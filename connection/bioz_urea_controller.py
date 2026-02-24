# connection/bioz_urea_controller.py

import serial
import serial.tools.list_ports
import threading
import time
import re 

from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal

class BiozUreaController(QObject):
    """
    Controlador independiente para la medición de Bioimpedancia y Urea.
    Se comunica con un dispositivo ESP32-S3 a 115200 baudios.
    Emite señales cuando se reciben nuevos datos.
    """
    
    # Señal para enviar datos a la HMI (tag, valor)
    data_received = Signal(str, float)

    def __init__(self, port_whitelist=None, baudrate=115200):
        super().__init__()
        # Lista de palabras clave para identificar el puerto del ESP32-S3
        # Ajustar esto según cómo aparezca el puerto del sistema
        self.port_whitelist = port_whitelist if port_whitelist else ["ESP32", "CP210X", "UART Bridge"]
        self.baudrate = baudrate
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self.command_queue = Queue()
        self.read_thread: Optional[threading.Thread] = None

    def start(self):
        """Inicia el hilo de comunicación con el ESP32."""
        if self.running:
            return
        self.running = True
        self.read_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.read_thread.start()

    def stop(self):
        """Detiene el hilo de comunicación y cierra el puerto serial."""
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                print(f"[BIOZ/UREA] Error cerrando puerto serial: {e}")
        self.serial_port = None
        print("[BIOZ/UREA] Controlador detenido.")

    def send_command(self, command_str: str):
        """
        Comando para ser enviado al ESP32.
        Asegura que el comando termine con '\n' (nueva línea).
        """
        if self.serial_port and self.serial_port.is_open:
            full_command = command_str.encode('ascii') + b'\n'
            print(f"[BIOZ/UREA] Queued command: {full_command.decode().strip()}")
            self.command_queue.put(full_command)
        else:
            print("[BIOZ/UREA] Puerto serial no conectado. Comando no enviado.")

    def _find_and_connect(self) -> bool:
        """
        Intenta encontrar y conectar al puerto serial del ESP32.
        Excluye puertos que contengan "FTDI" (para evitar el controlador principal).
        """
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"

            # Excluir el puerto del controlador principal
            if "FTDI" in full_info:
                continue

            # Buscar palabras clave en la whitelist
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    try:
                        self.serial_port = serial.Serial(p.device, self.baudrate, timeout=1, write_timeout=1)
                        time.sleep(2) # Dar tiempo al ESP32 para que se reinicie
                        print(f"[BIOZ/UREA] Conectado en {p.device}")
                        return True
                    except Exception as e:
                        print(f"[BIOZ/UREA] Error al intentar conectar {p.device}: {e}")
        return False

    def _communication_loop(self):
        """
        Bucle principal del hilo de comunicación.
        Maneja la reconexión, el envío de comandos y la lectura/parsing de datos.
        """
        line_buffer = b''
        while self.running:
            if not self.serial_port or not self.serial_port.is_open:
                if not self._find_and_connect():
                    time.sleep(3) # Reintentar la conexión cada 3 segundos
                    continue
                else:
                    # Tras una conexión exitosa, limpiar comandos pendientes de sesiones anteriores
                    with self.command_queue.mutex:
                        self.command_queue.queue.clear()

            try:
                # 1. Enviar comandos en cola
                try:
                    cmd_to_send = self.command_queue.get_nowait()
                    self.serial_port.write(cmd_to_send)
                except Empty:
                    pass # No hay comandos pendientes

                # 2. Leer datos entrantes línea por línea
                if self.serial_port.in_waiting > 0:
                    char = self.serial_port.read(1)
                    if char == b'\n':
                        self._parse_line(line_buffer.decode('ascii', errors='ignore').strip())
                        line_buffer = b''
                    elif char != b'\r': # Ignorar el retorno de carro (CR)
                        line_buffer += char
                
                time.sleep(0.01) # Pequeño retardo para evitar consumo excesivo de CPU
            
            except serial.SerialException as e:
                print(f"[BIOZ/UREA] Error serial: {e}")
                if self.serial_port:
                    try:
                        self.serial_port.close()
                    except: pass
                self.serial_port = None # Forzar reconexión
                line_buffer = b'' # Limpiar buffer al perder conexión
                time.sleep(1)
            except Exception as e:
                print(f"[BIOZ/UREA] Error inesperado en el bucle de comunicación: {e}")
                time.sleep(1)

    def _parse_line(self, line: str):
        """
        Parsea una línea de texto recibida del ESP32 y emite señales.
        """
        # Expresión regular para Bioimpedancia: "R: <val> Ohm, Phase: <val> Deg"
        match_bia = re.match(r"R:\s*([\d.-]+)\s*Ohm,\s*Phase:\s*([\d.-]+)\s*Deg", line)
        if match_bia:
            try:
                resistance = float(match_bia.group(1))
                phase = float(match_bia.group(2))
                self.data_received.emit("bioz_resistance", resistance)
                self.data_received.emit("bioz_phase", phase)
                print(f"Parsed BIA: R={resistance}, Phase={phase}")
                return
            except (ValueError, IndexError) as e:
                print(f"[BIOZ/UREA] Error al parsear línea BIA '{line}': {e}")
                return

        # Expresión regular para Urea: "UREA ADC1: <val>, ADC2: <val>"
        match_urea = re.match(r"UREA ADC1:\s*([\d.-]+),\s*ADC2:\s*([\d.-]+)", line)
        if match_urea:
            try:
                adc1 = float(match_urea.group(1))
                adc2 = float(match_urea.group(2))
                self.data_received.emit("urea_adc1", adc1)
                self.data_received.emit("urea_adc2", adc2)
                print(f"Parsed UREA: ADC1={adc1}, ADC2={adc2}")
                return
            except (ValueError, IndexError) as e:
                print(f"[BIOZ/UREA] Error al parsear línea UREA '{line}': {e}")
                return
        
        # Si la línea no es reconocida y no está vacía, imprimirla (depuración)
        if line:
           print(f"[BIOZ/UREA] Línea no reconocida: {line}")
