# connection/nibp_par_communication.py

"""
Comunicación serial con el baumanómetro PAR Medizintechnik NIBP2020 UP
(Combi Board con SpO2). Puerto y protocolo INDEPENDIENTES del controlador
principal (Mega/FTDI) manejado por connection/serial_communication.py.

Serial: 19200 8N1 (con SpO2 siempre 19200, nunca 4800).
"""

from __future__ import annotations

import logging
import platform
import threading
import time
from queue import PriorityQueue, Empty
from typing import Optional

import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, Signal

from connection.nibp_protocol import (
    ADULT_START_PRESSURE_TO_CMD,
    CMD_ADULT_MODE,
    CMD_MANUAL_MODE,
    CMD_METHOD1_DEFLATION,
    CMD_METHOD2_IMT,
    CMD_METHOD3_ADAPTIVE,
    CMD_NEONATAL_MODE,
    CMD_PLETH_OFF,
    CMD_REQUEST_DATA,
    CMD_SOFTWARE_RESET,
    CMD_SPO2_OFF,
    CMD_SPO2_ON,
    CMD_START_MEASUREMENT,
    CMD_VERSION_29,
    CR,
    CYCLE_MINUTES_TO_CMD,
    ETX,
    ETX_SPO2,
    SPO2_HDR,
    STATUS_TEXTS_ES,
    STX,
    STX_SPO2,
    build_command,
    parse_frame,
    parse_spo2_packet,
)
from utilities.platform_runtime import (
    get_runtime_config_path,
    safe_json_load,
    sanitize_port_for_platform,
)

logger = logging.getLogger(__name__)

NIBP_BAUDRATE = 19200
_RECONNECT_INTERVAL_S = 2.0
_READ_TIMEOUT_S = 0.2
_MAX_RX_BUFFER = 256
_SPO2_ACTIVATION_DELAY_S = 0.5
_NIBP_CONFIG_PATH = get_runtime_config_path("nibp_config.json")

# Prioridades de la cola de comandos: menor número = mayor prioridad.
_PRIORITY_HIGH = 0
_PRIORITY_NORMAL = 5


class NibpParCommunication(QObject):
    """
    Maneja la comunicación serial con el módulo NIBP2020 UP, en un hilo
    daemon separado, con su propia cola de comandos y su propio puerto.
    """

    connected_changed = Signal(bool, str)
    cuff_pressure = Signal(int, int, int)
    measurement_ready = Signal(int, int, int, int)
    status_changed = Signal(int, str)
    error_message = Signal(str, str)
    version_received = Signal(str)
    raw_frame_received = Signal(bytes)
    spo2_updated = Signal(object)
    spo2_status_text = Signal(str)

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self._running = False
        self.reader_thread: Optional[threading.Thread] = None
        self._command_queue: "PriorityQueue[tuple[int, int, bytes]]" = PriorityQueue()
        self._command_seq = 0
        self._rx_buffer = bytearray()

        self._user_selected_port: Optional[str] = None  # None -> "Auto"
        self._is_enabled: bool = False
        self.is_connected = False

        self._spo2_enabled: bool = False
        self._spo2_activation_deadline: Optional[float] = None

    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, value: bool):
        self._running = value

    # ------------------------------------------------------------------
    # Configuración / ciclo de vida
    # ------------------------------------------------------------------
    def update_config(self, port_name: str, is_enabled: bool):
        """Actualiza puerto/habilitación desde la configuración persistida o la UI."""
        sanitized_port = sanitize_port_for_platform(port_name)
        port_changed = (
            self._user_selected_port != sanitized_port
            and not (self._user_selected_port is None and sanitized_port == "Auto")
        )
        self._user_selected_port = sanitized_port if sanitized_port != "Auto" else None
        self._is_enabled = is_enabled

        was_spo2_enabled = self._spo2_enabled
        self._refresh_spo2_enabled_from_config()

        logger.info(
            "[NIBP] Configuración recibida: Puerto='%s', Habilitado=%s, SpO2=%s",
            sanitized_port,
            is_enabled,
            self._spo2_enabled,
        )

        if not self._is_enabled and self.running:
            logger.info("[NIBP] Comunicación deshabilitada. Deteniendo módulo NIBP.")
            self.stop()
            self._reset_spo2_ui_state()
        elif self._is_enabled and not self.running:
            logger.info("[NIBP] Comunicación habilitada. Iniciando módulo NIBP.")
            self.start_reading()
        elif self._is_enabled and port_changed and self.running:
            logger.info("[NIBP] Puerto cambiado a '%s'. Forzando reconexión.", sanitized_port)
            self._close_port_resource()
            self._reset_spo2_ui_state()
        elif self._is_enabled and self.is_connected and was_spo2_enabled and not self._spo2_enabled:
            # spo2_enabled pasó a False con el puerto ya abierto: apagar stream y limpiar UI.
            logger.info("[NIBP] SpO2 deshabilitado por configuración. Apagando stream.")
            self.spo2_off()
            self._reset_spo2_ui_state()

    def _refresh_spo2_enabled_from_config(self):
        """Relee spo2_enabled desde config/nibp_config.json (fuente única compartida con la UI)."""
        loaded = safe_json_load(_NIBP_CONFIG_PATH, {})
        if not isinstance(loaded, dict):
            loaded = {}
        self._spo2_enabled = bool(loaded.get("spo2_enabled", False))

    def _reset_spo2_ui_state(self):
        self.spo2_updated.emit(None)
        self.spo2_status_text.emit("")

    def start_reading(self):
        """Inicia el hilo de comunicación de fondo si está habilitado."""
        if not self._is_enabled:
            logger.warning("[NIBP] Intento de arranque bloqueado: módulo deshabilitado.")
            return
        if self.running:
            return

        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        logger.info("[NIBP] Hilo de comunicación NIBP iniciado.")

    def stop(self):
        """Detiene el hilo de comunicación y cierra el puerto de forma segura."""
        if not self.running:
            self._close_port_resource()
            return

        logger.info("[NIBP] Iniciando apagado del módulo NIBP...")
        self.running = False
        self._close_port_resource()

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.5)
            if self.reader_thread.is_alive():
                logger.warning("[NIBP] El hilo de comunicación no respondió al join a tiempo.")

        self.reader_thread = None
        logger.info("[NIBP] Comunicación NIBP detenida limpiamente.")

    # ------------------------------------------------------------------
    # Conexión física
    # ------------------------------------------------------------------
    def connect_port(self) -> bool:
        """Abre el puerto físico basándose en la configuración actual."""
        if self.serial_port and getattr(self.serial_port, "is_open", False):
            self._close_port_resource()

        if self._user_selected_port:
            logger.info("[NIBP] Intentando conectar a puerto específico: %s", self._user_selected_port)
            return self._execute_connection(self._user_selected_port)

        return self._find_and_connect_auto()

    def _execute_connection(self, port_name: str) -> bool:
        current_os = platform.system()
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=NIBP_BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=_READ_TIMEOUT_S,
            )

            # Evitar autorreseteos del módulo por DTR/RTS en Linux, igual que el driver principal.
            if current_os != "Windows":
                self.serial_port.dtr = False
                self.serial_port.rts = False

            self._rx_buffer.clear()
            self.is_connected = True
            self.connected_changed.emit(True, port_name)
            self._spo2_activation_deadline = (
                time.monotonic() + _SPO2_ACTIVATION_DELAY_S if self._spo2_enabled else None
            )
            logger.info(
                "[NIBP] Conectado. OS: %s | Puerto: %s | Baud: %s | NIBP2020 UP",
                current_os,
                port_name,
                NIBP_BAUDRATE,
            )
            return True
        except Exception as exc:
            logger.error("[NIBP] Error de conexión en %s: %s", port_name, exc)
            self.is_connected = False
            self.connected_changed.emit(False, port_name)
            return False

    def _find_and_connect_auto(self) -> bool:
        """
        Sin puerto explícito no se abre nada automáticamente: el módulo NIBP
        no tiene una firma de hardware distintiva (FTDI) como el controlador
        principal, así que abrir "el primero disponible" arriesga tomar el
        puerto de otro dispositivo. 'Auto' solo se usa cuando la UI elige un COM.
        """
        logger.warning("[NIBP] Modo Auto sin puerto explícito: no se abrirá ningún puerto.")
        self.is_connected = False
        self.connected_changed.emit(False, "")
        return False

    def _close_port_resource(self):
        self.is_connected = False
        self._spo2_activation_deadline = None
        port = self.serial_port
        if port is not None:
            try:
                if getattr(port, "is_open", False):
                    port.close()
                    logger.info("[NIBP] Puerto serial cerrado.")
            except Exception as exc:
                logger.error("[NIBP] Error cerrando el recurso serial: %s", exc)
            finally:
                self.serial_port = None
        else:
            self.serial_port = None

    # ------------------------------------------------------------------
    # Hilo de comunicación
    # ------------------------------------------------------------------
    def _communication_loop(self):
        while self.running:
            if not self._is_enabled:
                self._close_port_resource()
                time.sleep(1.0)
                continue

            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                self.is_connected = False
                if not self.connect_port():
                    time.sleep(_RECONNECT_INTERVAL_S)
                    continue

            try:
                self._maybe_activate_pending_spo2()
                self._flush_pending_commands()
                self._read_and_parse_frames()
            except Exception as exc:
                if self.running:
                    logger.error("[NIBP] Error en bucle principal: %s -> Reiniciando puerto.", exc)
                    self._close_port_resource()
                time.sleep(1.0)

        logger.info("[NIBP] Hilo de comunicación NIBP finalizado.")

    def _maybe_activate_pending_spo2(self):
        """Activa el stream SpO2 ~500 ms después de abrir el puerto (no en el mismo tick del open)."""
        if self._spo2_activation_deadline is None:
            return
        if time.monotonic() < self._spo2_activation_deadline:
            return
        self._spo2_activation_deadline = None
        if self._spo2_enabled and self.is_connected:
            logger.info("[NIBP] Activando stream SpO2 tras la conexión.")
            self.spo2_on()

    def _flush_pending_commands(self):
        """Envía todos los comandos encolados (mayor prioridad primero)."""
        while True:
            try:
                _, _, frame = self._command_queue.get_nowait()
            except Empty:
                break
            self._write_frame(frame)

    def _write_frame(self, frame: bytes) -> bool:
        if not self.serial_port or not getattr(self.serial_port, "is_open", False):
            return False
        try:
            self.serial_port.write(frame)
            logger.debug("[NIBP] Comando enviado: %s", frame.hex())
            return True
        except Exception as exc:
            logger.error("[NIBP] Falla al escribir comando: %s", exc)
            self._close_port_resource()
            return False

    def _read_and_parse_frames(self):
        if not self.serial_port or not getattr(self.serial_port, "is_open", False):
            return

        chunk = self.serial_port.read(64)
        if not chunk:
            return

        self._rx_buffer.extend(chunk)

        while True:
            candidates = []
            stx_index = self._rx_buffer.find(STX)
            if stx_index != -1:
                candidates.append((stx_index, "ascii", STX))
            stx_spo2_index = self._rx_buffer.find(STX_SPO2)
            if stx_spo2_index != -1:
                candidates.append((stx_spo2_index, "ascii", STX_SPO2))
            spo2_index = self._rx_buffer.find(SPO2_HDR)
            if spo2_index != -1:
                candidates.append((spo2_index, "spo2", None))

            if not candidates:
                # Sin SOH/header reconocible (p.ej. pleth SMARTsat crudo). No se
                # descarta el buffer solo por esto; se acota su crecimiento.
                if len(self._rx_buffer) > _MAX_RX_BUFFER:
                    stray = bytes(self._rx_buffer)
                    self._rx_buffer.clear()
                    self.raw_frame_received.emit(stray)
                return

            start_index, kind, which_stx = min(candidates, key=lambda item: item[0])
            if start_index > 0:
                stray = bytes(self._rx_buffer[:start_index])
                del self._rx_buffer[:start_index]
                self.raw_frame_received.emit(stray)

            if kind == "spo2":
                if not self._try_consume_spo2_packet():
                    return
                continue

            etx_byte = ETX if which_stx == STX else ETX_SPO2
            etx_index = self._rx_buffer.find(etx_byte, 1)
            if etx_index == -1:
                if len(self._rx_buffer) > _MAX_RX_BUFFER:
                    # Trama nunca cerrada o SOH espúrio dentro de datos pleth;
                    # se descarta solo el byte inicial, no todo el buffer.
                    del self._rx_buffer[:1]
                    continue
                return  # Trama incompleta; esperar más datos

            end_index = etx_index + 1
            # Incluir el CR final si ya llegó junto con el ETX.
            if len(self._rx_buffer) > end_index and self._rx_buffer[end_index] == CR:
                end_index += 1

            frame = bytes(self._rx_buffer[:end_index])
            del self._rx_buffer[:end_index]

            self._handle_frame(frame)

    def _try_consume_spo2_packet(self) -> bool:
        """Intenta consumir un paquete 55 AA completo del buffer.

        Devuelve True si el bucle de lectura debe continuar (se consumió un
        paquete o se descartó un byte espurio); False si hay que esperar más
        datos (paquete incompleto).
        """
        if len(self._rx_buffer) < 3:
            if len(self._rx_buffer) > _MAX_RX_BUFFER:
                del self._rx_buffer[:1]
                return True
            return False

        n_field = self._rx_buffer[2]
        total = 2 + n_field
        if len(self._rx_buffer) < total:
            if len(self._rx_buffer) > _MAX_RX_BUFFER:
                del self._rx_buffer[:1]
                return True
            return False

        frame = bytes(self._rx_buffer[:total])
        del self._rx_buffer[:total]
        self._handle_spo2_frame(frame)
        return True

    def _handle_frame(self, frame: bytes):
        try:
            parsed = parse_frame(frame)
        except Exception as exc:
            logger.debug("[NIBP] No se pudo parsear la trama %s: %s", frame.hex(), exc)
            self.raw_frame_received.emit(frame)
            return

        if parsed is None:
            self.raw_frame_received.emit(frame)
            return

        frame_type = parsed.get("type")

        if frame_type == "cuff":
            self.cuff_pressure.emit(parsed["pressure_mmhg"], parsed["caution"], parsed["status"])
        elif frame_type == "end":
            logger.debug("[NIBP] Fin de medición detectado. Solicitando status (cmd 18).")
            self.request_status()
        elif frame_type == "status":
            status_text = STATUS_TEXTS_ES.get(parsed["status_digit"], "desconocido")
            self.status_changed.emit(parsed["status_digit"], status_text)

            if not parsed["checksum_ok"]:
                logger.warning(
                    "[NIBP] Checksum inválido en trama de status (recibido=%s). No se emite measurement_ready.",
                    parsed["checksum_received"],
                )
            else:
                self.measurement_ready.emit(
                    parsed["sys"], parsed["dia"], parsed["map"], parsed["hr"]
                )

            if parsed.get("error_code"):
                error_text = parsed.get("error_text") or "código de error desconocido"
                logger.warning("[NIBP] Error M%s: %s", parsed["error_code"], error_text)
                self.error_message.emit(f"M{parsed['error_code']}", error_text)
        else:
            logger.debug("[NIBP] Trama desconocida recibida: %s", frame.hex())
            self.raw_frame_received.emit(frame)

    def _handle_spo2_frame(self, frame: bytes):
        try:
            parsed = parse_spo2_packet(frame)
        except Exception as exc:
            logger.debug("[NIBP] No se pudo parsear paquete SpO2 %s: %s", frame.hex(), exc)
            return

        if parsed is None:
            return

        ptype = parsed.get("type")
        if ptype == "spo2":
            self.spo2_updated.emit(parsed)
            self.spo2_status_text.emit(self._spo2_status_text_from(parsed))
        elif ptype == "spo2_bad_checksum":
            logger.warning("[NIBP] Checksum SpO2 inválido: %s", frame.hex())
        else:
            logger.debug("[NIBP] Paquete SpO2 ignorado (pleth/versión): %s", frame.hex())

    @staticmethod
    def _spo2_status_text_from(parsed: dict) -> str:
        if parsed.get("sensor_off"):
            return "Sensor desconectado"
        if parsed.get("no_finger"):
            return "Sin dedo"
        if parsed.get("no_pulse"):
            return "Sin pulso"
        if parsed.get("searching"):
            return "Buscando…"
        if parsed.get("signal_weak"):
            return "Señal débil"
        return ""

    # ------------------------------------------------------------------
    # Envío de comandos (API pública)
    # ------------------------------------------------------------------
    def _enqueue_command(self, code: str, priority: int = _PRIORITY_NORMAL):
        frame = build_command(code)
        self._command_seq += 1
        self._command_queue.put((priority, self._command_seq, frame))

    def start_measurement(self):
        self._enqueue_command(CMD_START_MEASUREMENT, _PRIORITY_HIGH)

    def set_manual_mode(self):
        self._enqueue_command(CMD_MANUAL_MODE)

    def set_adult_mode(self):
        self._enqueue_command(CMD_ADULT_MODE)

    def set_neonatal_mode(self):
        self._enqueue_command(CMD_NEONATAL_MODE)

    def set_method(self, method: int):
        """method: 1 (deflación), 2 (IMT, default) o 3 (deflación adaptativa)."""
        method_to_cmd = {
            1: CMD_METHOD1_DEFLATION,
            2: CMD_METHOD2_IMT,
            3: CMD_METHOD3_ADAPTIVE,
        }
        code = method_to_cmd.get(method)
        if code is None:
            logger.warning("[NIBP] Método inválido solicitado: %s", method)
            return
        self._enqueue_command(code)

    def set_start_pressure_mmhg(self, pressure_mmhg: int):
        """Mapea a la presión de arranque adulto soportada más cercana."""
        closest = min(ADULT_START_PRESSURE_TO_CMD, key=lambda p: abs(p - pressure_mmhg))
        self._enqueue_command(ADULT_START_PRESSURE_TO_CMD[closest])

    def set_cycle_minutes(self, minutes: Optional[int]):
        """minutes: None -> modo manual (cmd 03); si no, ciclo más cercano soportado."""
        if minutes is None:
            self.set_manual_mode()
            return
        closest = min(CYCLE_MINUTES_TO_CMD, key=lambda m: abs(m - minutes))
        self._enqueue_command(CYCLE_MINUTES_TO_CMD[closest])

    def request_status(self):
        self._enqueue_command(CMD_REQUEST_DATA, _PRIORITY_HIGH)

    def software_reset(self):
        self._enqueue_command(CMD_SOFTWARE_RESET)

    def request_version(self):
        self._enqueue_command(CMD_VERSION_29)

    def spo2_on(self):
        self._enqueue_command(CMD_PLETH_OFF)
        self._enqueue_command(CMD_SPO2_ON)

    def spo2_off(self):
        self._enqueue_command(CMD_SPO2_OFF)
        self._reset_spo2_ui_state()
