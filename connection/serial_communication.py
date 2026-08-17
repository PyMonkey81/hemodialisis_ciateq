# connection/serial_communication.py

"""
Módulo para la comunicación serial con el controlador de la máquina de hemodiálisis.
Adaptado para control dinámico de puertos y estado desde la UI de configuración.
"""

import platform
import sys
import serial
import serial.tools.list_ports
import threading
import time
import struct
import crcmod
from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal
from core.variables_map import VARIABLES, ANALOG_MAP
from utilities.platform_runtime import sanitize_port_for_platform
import logging
logger = logging.getLogger(__name__)


# CRC-16 Modbus (polynomial 0x8005, reflected)
crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF, rev=True, xorOut=0x0000)

# Fixed read commands
READ_BOOLEAN_COMMAND    = bytes.fromhex("11 11 00 3C")
READ_ANALOG_COMMAND     = bytes.fromhex("12 AA 00 47")

# Expected response sizes (including 2-byte CRC)
EXPECTED_BOOLEAN_RESPONSE_SIZE = 65   # 3 header + 60 data + 2 CRC
EXPECTED_ANALOG_RESPONSE_SIZE  = 573  # 3 header + 71×8 bytes + 2 CRC
EXPECTED_WRITE_RESPONSE_SIZE   = 6    # 3 header + 1 response byte + 2 CRC


class SerialCommunication(QObject):
    """
    Handles serial communication with the hemodialysis machine controller.
    Emits data_received(tag: str, value: float) signal when new data is parsed.
    """
    data_received = Signal(str, float)

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self._running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.command_queue = Queue()
        self.next_read_command = READ_BOOLEAN_COMMAND
        self.is_connected = False
        self.last_successful_communication = time.time()

        # --- Nuevas variables para la configuración dinámica desde la UI ---
        self._user_selected_port: Optional[str] = None  # None significa "Auto" (Detección FTDI)
        self._is_enabled: bool = False                  # Deshabilitado por defecto para coincidir con la UI

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value: bool):
        self._running = value

    def update_config(self, port_name: str, is_enabled: bool):
        """
        Actualiza la configuración de comunicación desde la UI.
        
        Args:
            port_name (str): Nombre del puerto ("COMx", "/dev/ttyUSBx") o "Auto".
            is_enabled (bool): Flag de activación del controlador principal.
        """
        sanitized_port = sanitize_port_for_platform(port_name)
        port_changed = (self._user_selected_port != sanitized_port and not (self._user_selected_port is None and sanitized_port == "Auto"))
        enabled_changed = (self._is_enabled != is_enabled)
        
        # Guardar configuraciones mapeando "Auto" a None
        self._user_selected_port = sanitized_port if sanitized_port != "Auto" else None
        self._is_enabled = is_enabled
        
        logger.info(f"[CONTROLADOR PPAL] Configuración recibida: Puerto='{sanitized_port}', Habilitado={is_enabled}")

        # Lógica de estados del hilo basados en cambios de la UI
        if not self._is_enabled and self.running:
            logger.info("[CONTROLADOR PPAL] Se deshabilitó la comunicación. Deteniendo controlador.")
            self.stop()
        elif self._is_enabled and not self.running:
            logger.info("[CONTROLADOR PPAL] Se habilitó la comunicación. Iniciando controlador.")
            self.start_reading()
        elif self._is_enabled and port_changed and self.running:
            logger.info(f"[CONTROLADOR PPAL] Puerto cambiado a '{sanitized_port}'. Forzando reconexión física.")
            self._close_port_resource()

    def connect(self) -> bool:
        """Establece la conexión física basándose en la configuración de la UI."""
        if self.serial_port and getattr(self.serial_port, "is_open", False):
            self._close_port_resource()
        if self._user_selected_port:
            # Conexión directa a puerto específico dictado por el usuario
            logger.info(f"[CONTROLADOR PPAL] Intentando conectar a puerto ESPECÍFICO: {self._user_selected_port}")
            return self._execute_connection(self._user_selected_port)
        else:
            # Conexión en modo "Auto" buscando dispositivos FTDI por hardware
            return self._find_and_connect_auto()

    def _execute_connection(self, port_name: str) -> bool:
        """Realiza la apertura física del puerto serial."""
        current_os = platform.system()
        try:
            if self.serial_port and getattr(self.serial_port, "is_open", False):
                self._close_port_resource()
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=1.0,
                write_timeout=0.5
            )
            
            
            # Ajustes específicos para evitar autorreseteos de hardware en Linux
            if current_os != "Windows":
                self.serial_port.dtr = False
                self.serial_port.rts = False

            time.sleep(1.5)  # Estabilización del hardware tras el DTR/RTS bind
            self.is_connected = True
            #=========================Código de prueba======================
            # self.serial_port.reset_input_buffer()
            # self.serial_port.reset_output_buffer()
            # time.sleep(0.5)
            
            # # Enviar comando dummy para "despertar" y limpiar buffers del controlador
            # dummy = bytes([0x00, 0x00, 0x00])
            # self.serial_port.write(dummy + b'\x00\x00')  # CRC dummy
            # time.sleep(0.3)
            # self.serial_port.reset_input_buffer()
            # self.serial_port.reset_output_buffer()
            #===========================Fin================================

            self.last_successful_communication = time.time()
            logger.info(f"[CONNECTED PPAL] OS: {current_os} | Puerto: {port_name}")
            return True
        except Exception as e:
            self._log_linux_permission_hint(port_name, e)
            logger.error(f"[CONTROLADOR PPAL] Error de conexión en {port_name}: {e}")
            self.is_connected = False
            return False

    def _log_linux_permission_hint(self, port_name: str, error: Exception):
        """Muestra recomendación operativa cuando Linux rechaza acceso al puerto serial."""
        if platform.system() == "Windows":
            return

        error_text = str(error).lower()
        if "permission" in error_text or "denied" in error_text or "errno 13" in error_text:
            logger.warning(
                "[CONTROLADOR PPAL] Permiso denegado en %s. "
                "En Linux agrega el usuario al grupo de puertos seriales (dialout/uucp) "
                "y verifica reglas udev para el dispositivo.",
                port_name,
            )

    def _find_and_connect_auto(self) -> bool:
        """Algoritmo de detección automática original filtrando por fabricante FTDI."""
        current_os = platform.system()
        logger.debug("[CONTROLADOR PPAL] Ejecutando escaneo automático FTDI...")
        
        for port_info in serial.tools.list_ports.comports():
            is_ftdi = port_info.manufacturer and "FTDI" in port_info.manufacturer.upper()
            if is_ftdi:
                logger.info(f"[CONTROLADOR PPAL] Dispositivo FTDI detectado automáticamente en: {port_info.device}")
                return self._execute_connection(port_info.device)
                
        logger.warning("[CONTROLADOR PPAL] No se encontró ningún dispositivo FTDI en los puertos del sistema.")
        self.is_connected = False
        return False

    def start_reading(self):
        """Inicia el hilo de comunicación de fondo si está permitido."""
        if not self._is_enabled:
            logger.warning("[CONTROLADOR PPAL] Intento de arranque bloqueado: Comunicación deshabilitada.")
            return

        if self.running:
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        logger.info("[CONTROLADOR PPAL] Hilo de comunicación iniciado exitosamente.")

    def _communication_loop(self):
        """Main communication loop: handles reads and queued write commands."""
        while self.running:
            # Control preventivo si la UI apaga el switch a mitad de un ciclo largo
            if not self._is_enabled:
                self._close_port_resource()
                time.sleep(1.0)
                continue

            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                self.is_connected = False
                if self.connect():
                    self.last_successful_communication = time.time()
                else:
                    time.sleep(2.0)  # Frecuencia de reintento ante caídas de enlace o desconexión
                    continue

            try:
                # Write commands have priority
                try:
                    command = self.command_queue.get_nowait()
                    is_write = True
                    logger.debug("[CONTROLADOR PPAL] Enviando comando de ESCRITURA: %s", command.hex())
                except Empty:
                    command = self.next_read_command
                    is_write = False

                if not self._send_command(command):
                    raise serial.SerialException("Failed to send command")

                expected_size = (
                    EXPECTED_WRITE_RESPONSE_SIZE if is_write else
                    EXPECTED_BOOLEAN_RESPONSE_SIZE if command == READ_BOOLEAN_COMMAND else
                    EXPECTED_ANALOG_RESPONSE_SIZE
                )

                response = self._read_response(expected_size)
                if not response:
                    raise TimeoutError("Response timeout")

                # CRC validation
                received_crc = (response[-2] << 8) | response[-1]
                calculated_crc = crc16(response[:-2])
                if received_crc != calculated_crc:
                    raise ValueError(f"CRC mismatch (received: {received_crc:04X}, calculated: {calculated_crc:04X})")

                self.last_successful_communication = time.time()
                payload = response[:-2]

                if is_write:
                    if len(payload) >= 4 and payload[3] == 0xFF:
                        logger.debug("[WRITE OK] Command acknowledged")
                else:
                    self._parse_read_payload(payload)

                # Toggle between boolean and analog reads
                if not is_write:
                    self.next_read_command = (
                        READ_ANALOG_COMMAND if command == READ_BOOLEAN_COMMAND
                        else READ_BOOLEAN_COMMAND
                    )

                # Chequeo de salud del enlace (Watchdog de comunicación)
                if time.time() - self.last_successful_communication > 10.0:
                    logger.warning("[CONTROLADOR PPAL] Watchdog superado (>10s sin tramas válidas). Forzando reconexión.")
                    self._close_port_resource()
                    continue

                time.sleep(0.25)  # Prevent CPU overload

            except Exception as e:
                if self.running:
                    logger.error(f"[CONTROLADOR PPAL] Error en bucle principal: {e} -> Reiniciando interfaz serial.")
                    self._close_port_resource()
                time.sleep(1.0)

        logger.info("[CONTROLADOR PPAL] Hilo de comunicación finalizado.")

    def _send_command(self, command: bytes) -> bool:
        """Send command with CRC appended."""
        if not self.serial_port or not getattr(self.serial_port, "is_open", False):
            return False
        try:
            crc = crc16(command)
            frame = command + bytes([crc >> 8, crc & 0xFF])
            if hasattr(self.serial_port, "reset_input_buffer"):
                self.serial_port.reset_input_buffer()
            self.serial_port.write(frame)
            return True
        except Exception:
            self._close_port_resource()
            return False

    def _read_response(self, size: int) -> Optional[bytes]:
        """Read exactly 'size' bytes from serial port."""
        if not self.serial_port or not getattr(self.serial_port, "is_open", False):
            return None
        try:
            data = self.serial_port.read(size)
            return data if len(data) == size else None
        except Exception:
            self._close_port_resource()
            return None

    def _parse_read_payload(self, payload: bytes):
        """Parse incoming data and emit signals for each variable."""
        # ── Boolean values ───────────────────────────────────────
        if payload.startswith(b'\x11\x11\x00') and len(payload) >= 63:
            if 0x01 in VARIABLES:
                for i in range(60):
                    byte_value = payload[3 + i]
                    value = 1.0 if byte_value else 0.0
                    if i in VARIABLES[0x01]:
                        tag = VARIABLES[0x01][i]["tag"]
                        self.data_received.emit(tag, value)

        # ── Analog (double) values ───────────────────────────────
        elif payload.startswith(b'\x12\xAA\x00') and len(payload) >= 571:
            for idx in range(71):
                group, address = ANALOG_MAP[idx]
                if group in VARIABLES and address in VARIABLES[group]:
                    offset = 3 + idx * 8
                    try:
                        value = struct.unpack_from('<d', payload, offset)[0]
                        tag = VARIABLES[group][address]["tag"]
                        self.data_received.emit(tag, value)
                    except:
                        pass

    def write_boolean(self, address: int, value: bool):
        """Queue a boolean write command."""
        cmd = bytes([0x21, 0x11, address, 0x01 if value else 0x00])
        self.command_queue.put(cmd)

    def write_double(self, group_code: int, var_id_in_group: int, value: float):
        """
        Queue an analog (double) write command.
        group_code is OR-ed with 0x20 to form the command byte.
        """
        command_byte = 0x20 | group_code
        cmd = bytes([command_byte, 0xAA, var_id_in_group]) + struct.pack('<d', value)
        self.command_queue.put(cmd)

    def _close_port_resource(self):
        """Libera de forma segura el puerto serial y resetea variables de estado."""
        self.is_connected = False
        port = self.serial_port
        if port is not None:
            try:
                if getattr(port, "is_open", False):
                    if hasattr(port, "reset_input_buffer"):
                        port.reset_input_buffer()
                    if hasattr(port, "reset_output_buffer"):
                        port.reset_output_buffer()
                    port.close()
                    logger.info("[CONTROLADOR PPAL] Puerto serial cerrado.")
            except Exception as e:
                logger.error(f"[CONTROLADOR PPAL] Error cerrando el recurso serial: {e}")
            finally:
                self.serial_port = None
        else:
            self.serial_port = None

    def stop(self):
        """Gracefully stop communication thread and close port without triggering exceptions."""
        if not self.running:
            self._close_port_resource()
            return

        logger.info("Iniciando apagado síncrono del módulo de comunicación serial...")
        self.running = False
        self._close_port_resource()

        if self.reader_thread and self.reader_thread.is_alive():
            logger.debug("Esperando la finalización del hilo de lectura (_communication_loop)...")
            self.reader_thread.join(timeout=1.5)
            if self.reader_thread.is_alive():
                logger.warning("El hilo serial no respondió al join a tiempo.")

        self.reader_thread = None
        logger.info("[CONTROLADOR PPAL] Comunicación serial detenida limpiamente.")
