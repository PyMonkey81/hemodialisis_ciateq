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

    # def _on_second_tick(self):
    #     hours_passed = 1 / 3600.0

    #     self.power_on_hours += hours_passed

    #     # Contar operación solo si el timer fue iniciado y no ha sido pausado/detenido
    #     if self.operation_start_time is not None:
    #         self.total_operation_hours += hours_passed

    #     # Contar limpieza solo si el timer de limpieza fue iniciado y no ha sido detenido
    #     if self.cleaning_start_time is not None:
    #         self.cleaning_hours += hours_passed


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



  # def _load_operation_hours(self):
    #     self.total_operation_hours = self._load_hours_from_file("config/operation_hours.json", "total_operation_hours")
    #     logger.info(f"Horas de operación cargadas: {self.total_operation_hours:.2f} h")
    #     if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
    #         self._update_maintenance_screen_immediately()

    # def _pause_operation_timer(self):
    #     """Detiene el conteo de horas de operación sin reiniciar el total acumulado."""
    #     if self.operation_start_time is not None:
    #         self.operation_start_time = None
    #         self._save_operation_hours()
    #         logger.info("Operación en pausa: contador de horas de operación detenido.")
    #         if hasattr(self, 'maintenance_screen'): # validar si esto genera error 
    #             self._update_maintenance_screen_immediately()


    # def _save_operation_hours(self):
    #     self._save_hours_to_file(
    #         "config/operation_hours.json", 
    #         {"total_operation_hours": round(self.total_operation_hours, 4)},
    #         f"Horas de operación guardadas: {self.total_operation_hours:.2f}h"
    #     )

    # def _load_power_on_hours(self):
    #     self.power_on_hours = self._load_hours_from_file("config/power_on_hours.json", "power_on_hours")
    #     logger.info(f"Power On Hours cargadas: {self.power_on_hours:.2f} h")
    #     if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
    #         self._update_maintenance_screen_immediately()
                
    # def _save_power_on_hours(self):
    #     self._save_hours_to_file(
    #         "config/power_on_hours.json", 
    #         {"power_on_hours": round(self.power_on_hours, 4)},
    #         f"Power On Hours guardadas: {self.power_on_hours:.2f} h"
    #     )


    # def _load_cleaning_hours(self):
    #     self.cleaning_hours = self._load_hours_from_file("config/cleaning_hours.json", "cleaning_hours")
    #     logger.info(f"Horas de limpieza cargadas: {self.cleaning_hours:.2f} h")
    #     if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
    #         self._update_maintenance_screen_immediately()

    # def _save_cleaning_hours(self):
    #     self._save_hours_to_file(
    #         "config/cleaning_hours.json", 
    #         {"cleaning_hours": round(self.cleaning_hours, 4)},
    #         f"Horas de limpieza guardadas: {self.cleaning_hours:.2f} h"
    #     )
