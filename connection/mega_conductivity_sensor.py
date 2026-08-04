# connection/mega_conductivity_sensor.py
"""
Comunicación con el sensor de conductividad patrón (DFRobot EC)
conectado a través de Arduino Mega.
La Mega calcula la conductividad con la librería DFRobot_EC y envía
el resultado por Serial en formato texto.
"""

import platform
import serial
import serial.tools.list_ports
import threading
import time
import re
from typing import Optional

from PySide6.QtCore import QObject, Signal
from utilities.platform_runtime import sanitize_port_for_platform
import logging
logger = logging.getLogger(__name__)


class MegaConductivitySensor(QObject):
    """
    Sensor de conductividad patrón vía Arduino Mega + DFRobot EC.
    Emite:
        - "megaCondSensor" / "patternCondSensor" → conductividad en mS/cm
        - "megaTempSensor" / "patternTempSensor" → temperatura en °C
    """
    data_received = Signal(str, float)

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self._running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.is_connected = False
        self.last_successful_communication = time.time()
        self._rx_buffer = ""

        self._user_selected_port: Optional[str] = None
        self._is_enabled: bool = False

        # Expresión regular para parsear la línea de DFRobot
        # Ejemplo: temperature:25.0^C  EC:1.41ms/cm
        self._line_pattern = re.compile(
            r"temperature\s*:\s*([\d.]+).*?EC\s*:\s*([\d.]+)",
            re.IGNORECASE
        )

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

        logger.info(f"[MEGA_COND] Config: Puerto='{sanitized_port}', Habilitado={is_enabled}")

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
                timeout=0.3,
                write_timeout=0.5
            )
            if platform.system() != "Windows":
                self.serial_port.dtr = False
                self.serial_port.rts = False

            time.sleep(1.5)  # La Mega tarda un poco más en reiniciar
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.is_connected = True
            self.last_successful_communication = time.time()
            logger.info(f"[MEGA_COND] Conectado en {port_name}")
            return True
        except Exception as e:
            logger.error(f"[MEGA_COND] Error de conexión en {port_name}: {e}")
            self.is_connected = False
            return False

    def _find_and_connect_auto(self) -> bool:
        """Busca Arduino Mega (oficial o clones comunes)."""
        for port_info in serial.tools.list_ports.comports():
            desc = (port_info.description or "").upper()
            manuf = (port_info.manufacturer or "").upper()

            # Arduino Mega 2560 oficial
            if port_info.vid == 0x2341 and port_info.pid in (0x0010, 0x0042):
                logger.info(f"[MEGA_COND] Arduino Mega detectado en {port_info.device}")
                return self._execute_connection(port_info.device)

            # Clones / descripciones comunes
            if "MEGA" in desc or "MEGA" in manuf:
                logger.info(f"[MEGA_COND] Posible Mega detectada en {port_info.device} ({port_info.description})")
                return self._execute_connection(port_info.device)

        logger.warning("[MEGA_COND] No se encontró Arduino Mega")
        return False

    def start_reading(self):
        if not self._is_enabled or self.running:
            return
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        logger.info("[MEGA_COND] Hilo iniciado")

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
                # Leer datos disponibles
                data = self.serial_port.read(self.serial_port.in_waiting or 1)
                if data:
                    try:
                        text = data.decode("ascii", errors="ignore")
                        self._rx_buffer += text
                        self._parse_lines()
                    except Exception as e:
                        logger.debug(f"[MEGA_COND] Error decodificando: {e}")

                # Watchdog
                if time.time() - self.last_successful_communication > 10.0:
                    logger.warning("[MEGA_COND] Watchdog → reconectando")
                    self._close_port_resource()
                    continue

                time.sleep(0.05)

            except Exception as e:
                logger.error(f"[MEGA_COND] Error en bucle: {e}")
                self._close_port_resource()
                time.sleep(1.0)

    def _parse_lines(self):
        """Procesa líneas completas del buffer."""
        while "\n" in self._rx_buffer:
            line, self._rx_buffer = self._rx_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            match = self._line_pattern.search(line)
            if match:
                try:
                    temperature = float(match.group(1))
                    ec_value = float(match.group(2))

                    # Tags principales + aliases para compatibilidad
                    self.data_received.emit("megaCondSensor", ec_value)
                    self.data_received.emit("megaTempSensor", temperature)

                    self.data_received.emit("patternCondSensor", ec_value)
                    self.data_received.emit("patternTempSensor", temperature)

                    self.last_successful_communication = time.time()
                    logger.debug(f"[MEGA_COND] EC={ec_value:.3f} mS/cm | Temp={temperature:.1f} °C")
                except ValueError:
                    logger.warning(f"[MEGA_COND] No se pudo convertir valores de la línea: {line}")
            else:
                # Puede ser un mensaje de calibración, lo ignoramos en operación normal
                if "CALIBRATION" in line.upper() or "ENTEREC" in line.upper() or "EXITEC" in line.upper():
                    logger.info(f"[MEGA_COND] Mensaje de calibración: {line}")
                else:
                    logger.debug(f"[MEGA_COND] Línea no reconocida: {line}")

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
        self._rx_buffer = ""

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._close_port_resource()
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.5)
        logger.info("[MEGA_COND] Detenido")