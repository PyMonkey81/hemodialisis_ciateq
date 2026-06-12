# core/timer_manager.py
import logging
import json
import os
from PySide6.QtCore import QObject, QTimer, QDateTime
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)

class TimerManager(QObject):
    """Gestor centralizado de timers y conteos de horas"""

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

        self.power_on_hours = 0.0
        self.total_operation_hours = 0.0
        self.cleaning_hours = 0.0

        self.operation_start_time = None
        self.cleaning_start_time = None
        self.last_resume_time = None

        self._second_timer = QTimer(self)
        self._second_timer.setInterval(1000)
        self._second_timer.timeout.connect(self._on_second_tick)
        self._second_timer.start()

        self._load_all_hours()

    def _on_second_tick(self):
        hours_passed = 1 / 3600.0

        self.power_on_hours += hours_passed

        if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
            self.total_operation_hours += hours_passed

        if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
            self.cleaning_hours += hours_passed

    # ====================== CONTROL DE TIMERS ======================

    def start_operation_timer(self):
        if not self.operation_start_time:
            self.operation_start_time = QDateTime.currentDateTime()
            logger.info("Operation timer iniciado")

    def pause_operation_timer(self):
        self.operation_start_time = None
        self._save_operation_hours()

    def start_cleaning_timer(self):
        if not self.cleaning_start_time:
            self.cleaning_start_time = QDateTime.currentDateTime()

    def stop_cleaning_timer(self):
        self.cleaning_start_time = None
        self._save_cleaning_hours()

    def get_hours_info(self):
        return {
            "power_on": self.power_on_hours,
            "operation": self.total_operation_hours,
            "cleaning": self.cleaning_hours,
        }
    # ====================== PERSISTENCIA ======================

    def _load_all_hours(self):
        self.power_on_hours = self._load_hours("config/power_on_hours.json", "power_on_hours")
        self.total_operation_hours = self._load_hours("config/operation_hours.json", "total_operation_hours")
        self.cleaning_hours = self._load_hours("config/cleaning_hours.json", "cleaning_hours")

    def _load_hours(self, file_path: str, key: str) -> float:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get(key, 0.0)
        except Exception as e:
            logger.error(f"Error cargando {file_path}: {e}")
        return 0.0

    def _save_hours(self, file_path: str, key: str, value: float):
        try:
            os.makedirs("config", exist_ok=True)
            data = {key: round(value, 4), "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando {file_path}: {e}")

    def _save_operation_hours(self):
        self._save_hours("config/operation_hours.json", "total_operation_hours", self.total_operation_hours)

    def _save_cleaning_hours(self):
        self._save_hours("config/cleaning_hours.json", "cleaning_hours", self.cleaning_hours)

    def _save_power_on_hours(self):
        self._save_hours("config/power_on_hours.json", "power_on_hours", self.power_on_hours)


