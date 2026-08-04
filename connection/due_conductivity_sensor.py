# connection/due_conductivity_sensor.py
"""
Comunicación con el sensor de conductividad patrón conectado a través de Arduino Due.
La Due lee dos canales analógicos (A0, A1) y envía una trama binaria.
"""

import platform
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal
from utilities.platform_runtime import sanitize_port_for_platform
import logging
logger = logging.getLogger(__name__)


class DueConductivitySensor(QObject):
    """
    Sensor de conductividad patrón vía Arduino Due (2 canales analógicos).
    Emite:
        - "dueCondSensor" / "dueCondRef" → valor del canal A0 (0-4095)
        - "dueTempSensor" / "dueTempRef" → valor del canal A1 (0-4095)
    """
    data_received = Signal(str, float)

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self._running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.is_connected = False
        self.last_successful_communication = time.time()
        self._rx_buffer = bytearray()

        self._user_selected_port: Optional[str] = None
        self._is_enabled: bool = False

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value: bool):
        self._running = value

    def update_config(self, port_name: str, is_enabled: bool):
        sanitized_port = sanitize_port_for_platform(port_name)
        port_changed = (
            self._user_selected_port != sanitized_port
            and not (self._user_selected_port is None and sanitized_port == "Auto")
        )

        self._user_selected_port = sanitized_port if sanitized_port != "Auto" else None
        self._is_enabled = is_enabled

        logger.info(f"[DUE_COND] Config: Puerto='{sanitized_port}', Habilitado={is_enabled}")

        if not self._is_enabled and self.running:
            self.stop()
        elif self._is_enabled and not self.running:
            self.start_reading()
        elif self._is_enabled and port_changed and self.running:
            self._close_port_resource()

    def connect(self) -> bool:
        if self._user_selected_port:
            return self._execute_connection(self._user_selected_port)
        return self._find_and_connect_auto()

    def _execute_connection(self, port_name: str) -> bool:
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=0.2,
                write_timeout=0.5
            )
            if platform.system() != "Windows":
                self.serial_port.dtr = False
                self.serial_port.rts = False

            time.sleep(1.2)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.is_connected = True
            self.last_successful_communication = time.time()
            logger.info(f"[DUE_COND] Conectado en {port_name}")
            return True
        except Exception as e:
            logger.error(f"[DUE_COND] Error de conexión en {port_name}: {e}")
            self.is_connected = False
            return False

    def _find_and_connect_auto(self) -> bool:
        for port_info in serial.tools.list_ports.comports():
            # Arduino Due típico
            if port_info.vid == 0x2341 and port_info.pid in (0x003d, 0x003e, 0x003f):
                logger.info(f"[DUE_COND] Arduino Due detectado en {port_info.device}")
                return self._execute_connection(port_info.device)
            if port_info.description and "Arduino Due" in port_info.description:
                return self._execute_connection(port_info.device)
        logger.warning("[DUE_COND] No se encontró Arduino Due")
        return False

    def start_reading(self):
        if not self._is_enabled or self.running:
            return
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        logger.info("[DUE_COND] Hilo iniciado")

    def _communication_loop(self):
        while self.running:
            if not self._is_enabled:
                self._close_port_resource()
                time.sleep(1.0)
                continue

            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                self.is_connected = False
                if not self.connect():
                    time.sleep(2.0)
                    continue

            try:
                data = self.serial_port.read(self.serial_port.in_waiting or 1)
                if data:
                    self._rx_buffer.extend(data)
                    self._parse_buffer()

                if time.time() - self.last_successful_communication > 8.0:
                    logger.warning("[DUE_COND] Watchdog → reconectando")
                    self._close_port_resource()
                    continue

                time.sleep(0.01)
            except Exception as e:
                logger.error(f"[DUE_COND] Error en bucle: {e}")
                self._close_port_resource()
                time.sleep(1.0)

    def _parse_buffer(self):
        while len(self._rx_buffer) >= 7:
            try:
                idx = self._rx_buffer.index(0xAA)
            except ValueError:
                self._rx_buffer.clear()
                return

            if idx > 0:
                del self._rx_buffer[:idx]

            if len(self._rx_buffer) < 7:
                return

            if self._rx_buffer[1] != 0x55:
                del self._rx_buffer[0]
                continue

            chk = self._rx_buffer[2] ^ self._rx_buffer[3] ^ self._rx_buffer[4] ^ self._rx_buffer[5]
            if chk != self._rx_buffer[6]:
                del self._rx_buffer[0]
                continue

            adc0 = (self._rx_buffer[2] << 8) | self._rx_buffer[3]
            adc1 = (self._rx_buffer[4] << 8) | self._rx_buffer[5]

            # Tags canonicos del proyecto + aliases retrocompatibles.
            self.data_received.emit("dueCondSensor", float(adc0))
            self.data_received.emit("dueTempSensor", float(adc1))
            self.data_received.emit("dueCondRef", float(adc0))
            self.data_received.emit("dueTempRef", float(adc1))

            self.last_successful_communication = time.time()
            del self._rx_buffer[:7]

    def _close_port_resource(self):
        self.is_connected = False
        if self.serial_port:
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
            except Exception:
                pass
            finally:
                self.serial_port = None
        self._rx_buffer.clear()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._close_port_resource()
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.5)
        logger.info("[DUE_COND] Detenido")