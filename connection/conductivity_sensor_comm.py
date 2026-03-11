import serial
import serial.tools.list_ports
import threading
import time
import struct  # por si necesitas binario en el futuro
# import crcmod  # descomenta si agregas comandos con CRC
from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal


from core.variables_map import VARIABLES


READ_COMMAND = bytes.fromhex("5641 4C41 520D")  # b'VALAR\r'
EXPECTED_MINIMUM_SIZE = 30


class PatternConductivity(QObject):
    """
    Clase para manejar el sensor patrón de conductividad (HDM18/19).
    Emite señales con tag y valor para integración con VARIABLES y UI.
    """
    data_received = Signal(str, float)  # tag (ej: "patternCondSensor"), valor

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.command_queue = Queue()
        self.read_command = READ_COMMAND
        self.isConnected = False
        self.last_successful_comm = time.time()

    # def connect(self) -> bool:
    #     """Busca y conecta al puerto USB Serial Device"""
    #     target_port = "COM7"
    #     target_manufacturer = "MICROSOFT"
    #     available_ports = serial.tools.list_ports.comports()

    #     for port_info in available_ports:
    #         port_device = (port_info.device or "").upper()
    #         manufacturer = (port_info.manufacturer or "").upper()
    #         if target_port in port_device or target_manufacturer in manufacturer:  # amplía si sabes el driver exacto
    #             try:
    #                 self.serial_port = serial.Serial(
    #                     port=port_info.device,
    #                     baudrate=115200,
    #                     bytesize=serial.EIGHTBITS,
    #                     parity=serial.PARITY_NONE,
    #                     stopbits=serial.STOPBITS_ONE,
    #                     timeout=1.0,
    #                     write_timeout=0.5
    #                 )
    #                 time.sleep(1.5)  # tiempo para que el sensor se estabilice
    #                 print(f"[Connected Conductivity sensor] Port: {port_info.device}")
    #                 self.isConnected = True
    #                 self.last_successful_comm = time.time()
    #                 return True
    #             except Exception as e:
    #                 print(f"[ERROR] Failed to open {port_info.device}: {e}")
    #     print("[ERROR] No conductivity sensor detected on any USB serial port")
    #     self.isConnected = False
    #     return False
    
    def connect(self) -> bool:
        """Intenta conectar directamente al puerto COM7"""
        target_port = "COM7"  # Puerto fijo como especificaste
    
        try:
            # Intentar abrir el puerto directamente
            self.serial_port = serial.Serial(
                port=target_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=0.5
            )
        
            # Esperar un momento para que el sensor se estabilice
            time.sleep(1.5)
        
            print(f"[Connected Conductivity sensor] Port: {target_port}")
            self.isConnected = True
            self.last_successful_comm = time.time()
            return True  # Conexión exitosa
        except serial.SerialException as e:
            # Error específico de pySerial, como puerto no encontrado
            print(f"[ERROR] Failed to open {target_port}: {e}")
        except Exception as e:
            # Otro error inesperado
            print(f"[ERROR] An unexpected error occurred while connecting: {e}")
    
        self.isConnected = False  # Marca como no conectado
        return False  # Conexión fallida


    def start(self):
        """Inicia el hilo de comunicación si no está corriendo"""
        if self.running:
            return
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        # print("[PatternConductivity] Reading thread started")

    def stop(self):
        """Detiene el hilo y cierra el puerto"""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.isConnected = False
        print("[PatternConductivity] Stopped and port closed")

    def _send_command(self, command: bytes) -> bool:
        """Envía comando y retorna True si se envió correctamente"""
        if not self.serial_port or not self.serial_port.is_open:
            return False
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.serial_port.write(command)
            return True
        except Exception as e:
            # print(f"[ERROR] Send command failed: {e}")
            return False

    def _read_response(self) -> str:
        """Lee la respuesta completa con timeout"""
        if not self.serial_port or not self.serial_port.is_open:
            return ""
        try:
            response = self.serial_port.read(100).decode('ascii', errors='ignore').rstrip('\r\n \x00')
            # if response:
            #     print(f"[VALAR raw] '{response}' (len={len(response)})")
            return response
        except Exception as e:
            print(f"[ERROR] Read failed: {e}")
            return ""

    # En _parse_response: ahora devuelve los tres valores
    def _parse_response(self, raw: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Parsea: cond_raw, cond_compensada, temp"""
        if not raw or len(raw) < 20:  # mínimo razonable
            return None, None, None

        parts = [p.strip() for p in raw.split('/')]
        if len(parts) < 3:
            # print(f"[Parse error] Formato inesperado (menos de 3 partes): '{raw}'")
            return None, None, None

        try:
            cond_raw = float(parts[0])
            cond_comp = float(parts[1])
            temp = float(parts[2])
            return cond_raw, cond_comp, temp
        except ValueError as e:
            # print(f"[Parse error] No se pudo convertir a float: {e} → partes: {parts}")
            return None, None, None

    def _communication_loop(self):
        while self.running:
            if not self.isConnected or not self.serial_port or not self.serial_port.is_open:
                self.isConnected = False
                if self.connect():
                    pass  # ya imprime en connect
                else:
                    time.sleep(3.0)
                continue

            try:
                # Prioridad: comandos en cola (escrituras si las agregas después)
                try:
                    command = self.command_queue.get_nowait()
                    is_read = False
                except Empty:
                    command = self.read_command
                    is_read = True

                if not self._send_command(command):
                    raise serial.SerialException("Failed to send")

                time.sleep(0.08)  # respiro corto para respuesta
                raw_response = self._read_response()

                if raw_response:
                    self.last_successful_comm = time.time()

                    if is_read:
                        cond_raw, cond_comp, temp = self._parse_response(raw_response)
                        if cond_comp is not None:
                            self.data_received.emit("patternCondSensor", cond_comp)
                            # print(f"[Emit] patternCondSensor → {cond_comp:.4f} mS/cm")

                        if cond_raw is not None:
                            self.data_received.emit("patternCondRaw", cond_raw)
                            # print(f"[Emit] patternCondRaw → {cond_raw:.8f} mS/cm")  # más decimales para raw

                        if temp is not None:
                            self.data_received.emit("patternTempSensor", temp)
                            # print(f"[Emit] patternTempSensor → {temp:.3f} °C")

                # Chequeo de comunicación saludable (opcional: si >10s sin respuesta, reconectar)
                if time.time() - self.last_successful_comm > 10:
                    # print("[WARNING] No recent successful comm → forcing reconnect")
                    self.isConnected = False
                    continue

                time.sleep(0.4)  # ~2-3 lecturas por segundo, ajusta según necesites

            except serial.SerialException as e:
                print(f"[Serial error] {e} → Reintentando conexión")
                self.isConnected = False
                time.sleep(1.0)
            except Exception as e:
                # print(f"[Unexpected error in loop] {e}")
                time.sleep(1.0)

        print("[PatternConductivity] Communication loop ended")