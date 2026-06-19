# connection/serial_communication.py

"""
Módulo para la comunicación serial con el controlador de la máquina de hemodiálisis.

Este módulo implementa la clase `SerialCommunication`, encargada de establecer
y mantener la conexión serial con el hardware de control de la máquina.
Gestiona el envío y recepción de datos, el parseo de tramas específicas del
protocolo y la emisión de señales de Qt para integrar los datos en tiempo
real con la interfaz gráfica de usuario (GUI).

Características clave:
--------------------
- **Conectividad Robusta**: Busca y se conecta automáticamente a dispositivos
  USB-serial de tipo FTDI, y maneja la reconexión en caso de pérdida de enlace.
- **Comunicación Asíncrona**: Opera en un hilo separado para realizar lecturas
  continuas y enviar comandos sin bloquear la aplicación principal ni la GUI.
- **Protocolo de Trama Personalizado**:
    - Implementa CRC-16 Modbus para la validación de la integridad de los datos.
    - Maneja comandos de lectura específicos para datos booleanos y analógicos (doble precisión).
    - Soporta comandos de escritura para actualizar variables booleanas y de punto flotante.
- **Parseo de Datos**: Interpreta los payloads recibidos basándose en los mapeos
  definidos en `core.variables_map` para extraer valores significativos.
- **Integración con GUI (Qt Signals)**: Emite la señal `data_received`
  (`tag: str, value: float`) cada vez que se procesa un nuevo valor del controlador,
  permitiendo que la GUI se actualice en tiempo real de forma segura.
- **Cola de Comandos**: Utiliza una cola (`queue.Queue`) para gestionar de forma
  eficiente los comandos de escritura enviados desde la GUI, dándoles prioridad
  sobre las lecturas cíclicas.
- **Monitoreo de Conexión**: Rastrea el estado de la conexión y el tiempo
  de la última comunicación exitosa para detectar problemas de forma proactiva.

Clase principal:
---------------
- `SerialCommunication`: Gestiona toda la lógica de bajo nivel para la
  interacción con el puerto serial, el protocolo de comunicación y la
  entrega de datos a la aplicación.

Dependencias:
-------------
- `serial`: Para el control del puerto serial.
- `serial.tools.list_ports`: Para la detección automática de puertos seriales.
- `threading`: Para la ejecución de la comunicación en un hilo separado.
- `time`: Para la gestión de tiempos y demoras.
- `struct`: Para la conversión de bytes a tipos de datos (ej. double).
- `crcmod`: Para la generación y verificación de sumas de control CRC-16.
- `queue`: Para la gestión de la cola de comandos de escritura.
- `PySide6.QtCore.QObject`, `PySide6.QtCore.Signal`: Para la integración con el sistema de señales/slots de Qt.
- `core.variables_map.VARIABLES`, `core.variables_map.ANALOG_MAP`: Mapeos de variables para el parseo de datos.

Uso:
----
1.  **Instanciación**: Crear una instancia de `SerialCommunication` en el
    componente principal de la aplicación (ej. `HemodialysisHMI`).
2.  **Conexión**: Llamar a `connect()` para intentar establecer la conexión
    con el hardware.
3.  **Inicio del Bucle de Lectura**: Llamar a `start_reading()` para que el
    sistema comience a leer datos en segundo plano.
4.  **Conexión de Señales**: Conectar la señal `data_received` a un slot
    de la GUI para procesar los datos entrantes.
5.  **Envío de Comandos**: Utilizar `write_boolean()` o `write_double()`
    para enviar setpoints o comandos de control al hardware.
6.  **Detención**: Al cerrar la aplicación, llamar a `stop()` para liberar
    el puerto serial y finalizar el hilo de comunicación de forma segura.
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
from hemodialisis_ciateq.core.variables_map import VARIABLES, ANALOG_MAP
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
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.command_queue = Queue()
        self.next_read_command = READ_BOOLEAN_COMMAND                                                    
        self.is_connected = False
        self.last_successful_communication = time.time()

    def connect(self) -> bool:
        """Attempt to connect to an FTDI USB-serial device, distinguishing between Windows and Linux."""
        current_os = platform.system()
        logger.info(f"Detecting OS: {current_os}")

        for port_info in serial.tools.list_ports.comports():
            is_ftdi = port_info.manufacturer and "FTDI" in port_info.manufacturer.upper()
            # is_ftdi = True
            # if port_info.manufacturer and "FTDI" in port_info.manufacturer.upper():
            if is_ftdi:
                try:

                    if current_os == "Windows":
                        logger.info(f"Attempting to connect to FTDI device on Windows: {port_info.device}")
                        port_name = port_info.device
                    else:  # Linux
                        logger.info(f"Attempting to connect to FTDI device on Linux: {port_info.device}")
                        port_name = port_info.device

                    self.serial_port = serial.Serial(
                        port=port_name,
                        # port="COM13",
                        
                        baudrate=115200,
                        timeout=1.0,
                        write_timeout=0.5
                    )
                    #Ajustes para evitar resets automáticos en Linux con FTDI
                    if current_os != "Windows":
                        self.serial_port.dtr = False  # Ensure DTR is low to prevent auto-reset on some FTDI devices
                        self.serial_port.rts = False  # Ensure RTS is low as well

                    time.sleep(1.5)  # Allow time for device stabilization
                    self.is_connected = True
                    logger.info(f"[CONNECTED] OS: {current_os} | Port: {port_info.device}")
                    print(f"[CONNECTED] OS: {current_os} | Port: {port_info.device}") 
                    return True
                except Exception as e:
                    logger.error(f"[ERROR] Failed to open port {port_info.device}: {e}")
        logger.error("[ERROR] No FTDI device found")
        self.is_connected = False
        return False

    def start_reading(self):
        """Start the background communication thread."""
        if self.running:
            return
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()

    def _communication_loop(self):
        """Main communication loop: handles reads and queued write commands."""
        while self.running:
            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                self.is_connected = False
                if self.connect():
                    self.last_successful_communication = time.time()
                time.sleep(2.0)
                continue

            try:
                # Write commands have priority
                try:
                    command = self.command_queue.get_nowait()
                    is_write = True
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
                        print("[WRITE OK] Command acknowledged")
                else:
                    self._parse_read_payload(payload)

                # Toggle between boolean and analog reads
                if not is_write:
                    self.next_read_command = (
                        READ_ANALOG_COMMAND if command == READ_BOOLEAN_COMMAND
                        else READ_BOOLEAN_COMMAND
                    )

                time.sleep(0.05)  # Prevent CPU overload

            except Exception as e:
                if self.running:
                    self.is_connected = False
                    if self.serial_port:
                        try:
                            self.serial_port.close()
                        except:
                            pass
                    self.serial_port = None
                time.sleep(1.0)

    def _send_command(self, command: bytes) -> bool:
        """Send command with CRC appended."""
        if not self.serial_port or not self.serial_port.is_open:
            return False
        try:
            crc = crc16(command)
            frame = command + bytes([crc >> 8, crc & 0xFF])
            self.serial_port.reset_input_buffer()
            self.serial_port.write(frame)
            return True
        except:
            return False

    def _read_response(self, size: int) -> Optional[bytes]:
        """Read exactly 'size' bytes from serial port."""
        if not self.serial_port or not self.serial_port.is_open:
            return None
        try:
            data = self.serial_port.read(size)
            return data if len(data) == size else None
        except:
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


    def stop(self):
        """Gracefully stop communication thread and close port without triggering exceptions."""
        if not self.running:
            return  # Evita doble ejecución si ya se llamó antes

        logger.info("Iniciando apagado síncrono del módulo de comunicación serial...")
        self.running = False
        self.is_connected = False

        # 1. Esperar a que el hilo muera de forma natural. 
        # Como read() tiene un timeout=1.0, el join debe esperar lo suficiente.
        if self.reader_thread and self.reader_thread.is_alive():
            logger.debug("Esperando la finalización del hilo de lectura (_communication_loop)...")
            self.reader_thread.join(timeout=1.5)
            
            if self.reader_thread.is_alive():
                logger.warning("El hilo serial no respondió al join a tiempo. Forzando cierre del puerto.")

        # 2. Ahora que el hilo terminó (o expiró el timeout), es seguro cerrar el recurso físico.
        if self.serial_port:
            try:
                if self.serial_port.is_open:
                    # Limpiamos buffers para liberar descriptores de comunicación del SO
                    self.serial_port.reset_input_buffer()
                    self.serial_port.reset_output_buffer()
                    self.serial_port.close()
                    logger.info("Puerto serial cerrado correctamente.")
            except Exception as e:
                logger.error(f"Error al cerrar el puerto serial durante el shutdown: {e}")
            finally:
                self.serial_port = None

        print("[INFO] Serial communication stopped clean")