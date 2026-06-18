"""Temporizador central orientado a fases del GRAFCET."""

import json
import logging
import os
from PySide6.QtCore import QObject, QTimer, QDateTime, QElapsedTimer
from Actualizacion.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)


class TimerManager(QObject):
    def __init__(self, main_window=None):
        super().__init__()
        self.main = main_window
        self.power_on_hours = 0.0
        self.operation_hours = 0.0
        self.cleaning_hours = 0.0

        self.operation_start_time: QDateTime | None = None
        self.cleaning_elapsed_timer = QElapsedTimer()
        self.is_cleaning_counting_active = False

        self.last_power_tick = QDateTime.currentDateTime()
        self._load_all_hours()

        self._second_timer = QTimer(self)
        self._second_timer.setInterval(1000)
        self._second_timer.timeout.connect(self._on_second_tick)
        self._second_timer.start()

        logger.info("TimerManager actualizado iniciado.")

    def _on_second_tick(self):
        now = QDateTime.currentDateTime()
        elapsed = self.last_power_tick.msecsTo(now) / 3600000.0
        self.power_on_hours += elapsed
        self.last_power_tick = now
        self._update_maintenance_screen()

    def on_state_changed(self, phase: TreatmentPhase, reason: str = "") -> None:
        if phase == TreatmentPhase.RUNNING:
            self._start_operation_timer()
        elif phase in (TreatmentPhase.PAUSED, TreatmentPhase.READY, TreatmentPhase.FINISHING, TreatmentPhase.IDLE, TreatmentPhase.CLEANING):
            self._stop_operation_timer()

        if phase == TreatmentPhase.CLEANING:
            self.on_cleaning_started_counting()
        elif phase == TreatmentPhase.IDLE and self.is_cleaning_counting_active:
            self.on_cleaning_stopped_counting()

    def _start_operation_timer(self) -> None:
        if self.operation_start_time is None:
            self.operation_start_time = QDateTime.currentDateTime()
            logger.debug("Inicio de conteo de operation_hours.")

    def _stop_operation_timer(self) -> None:
        if self.operation_start_time is not None:
            now = QDateTime.currentDateTime()
            elapsed = self.operation_start_time.msecsTo(now) / 3600000.0
            self.operation_hours += elapsed
            self.operation_start_time = None
            self._save_operation_hours()
            logger.debug(f"Terminó conteo de operation_hours: +{elapsed:.6f}h, total={self.operation_hours:.6f}h")

    def on_cleaning_started_counting(self) -> None:
        if not self.is_cleaning_counting_active:
            self.is_cleaning_counting_active = True
            self.cleaning_elapsed_timer.restart()
            logger.debug("Inicio de conteo de cleaning_hours.")

    def on_cleaning_stopped_counting(self) -> None:
        if self.is_cleaning_counting_active and self.cleaning_elapsed_timer.isValid():
            elapsed = self.cleaning_elapsed_timer.elapsed() / 3600000.0
            self.cleaning_hours += elapsed
            logger.debug(f"Acumulado {elapsed:.6f}h a cleaning_hours, total={self.cleaning_hours:.6f}h")
            self.is_cleaning_counting_active = False
            self._save_cleaning_hours()
            self._update_maintenance_screen()

    def get_hours_info(self) -> dict[str, float]:
        cleaning_extra = 0.0
        if self.is_cleaning_counting_active and self.cleaning_elapsed_timer.isValid():
            cleaning_extra = self.cleaning_elapsed_timer.elapsed() / 3600000.0

        return {
            "power_on": round(self.power_on_hours, 6),
            "operation": round(self.operation_hours, 6),
            "cleaning": round(self.cleaning_hours + cleaning_extra, 6),
        }

    def _update_maintenance_screen(self) -> None:
        if not hasattr(self.main, "maintenance_screen") or not self.main.maintenance_screen:
            return

        try:
            hours_info = self.get_hours_info()
            self.main.maintenance_screen.update_hours_display(
                hours_info["power_on"],
                hours_info["operation"],
                hours_info["cleaning"],
            )
        except Exception as exc:
            logger.debug(f"Error actualizando pantalla de mantenimiento: {exc}")

    def _load_all_hours(self) -> None:
        self._load_hours("power_on_hours.json", "power_on_hours")
        self._load_hours("operation_hours.json", "operation_hours")
        self._load_hours("cleaning_hours.json", "cleaning_hours")

    def _save_all_hours(self) -> None:
        if self.is_cleaning_counting_active and self.cleaning_elapsed_timer.isValid():
            elapsed = self.cleaning_elapsed_timer.elapsed() / 3600000.0
            self.cleaning_hours += elapsed
            self.cleaning_elapsed_timer.restart()

        self._save_hours("power_on_hours.json", "power_on_hours", self.power_on_hours)
        self._save_hours("operation_hours.json", "operation_hours", self.operation_hours)
        self._save_hours("cleaning_hours.json", "cleaning_hours", self.cleaning_hours)

    def _load_hours(self, filename: str, key: str) -> None:
        path = os.path.join("config", filename)
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                setattr(self, key, float(data.get(key, 0.0)))
        except Exception as exc:
            logger.warning(f"Error cargando {key}: {exc}")

    def _save_hours(self, filename: str, key: str, value: float) -> None:
        try:
            os.makedirs("config", exist_ok=True)
            with open(os.path.join("config", filename), "w", encoding="utf-8") as f:
                json.dump({
                    key: round(value, 6),
                    "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
                }, f, indent=4)
        except Exception as exc:
            logger.warning(f"Error guardando {key}: {exc}")
