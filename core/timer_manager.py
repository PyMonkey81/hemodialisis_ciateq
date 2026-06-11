# core/timer_manager.py
import logging
from datetime import datetime
from PySide6.QtCore import QObject, QDateTime, QTimer
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)

class TimerManager(QObject):
    """Gestor centralizado de todos los timers y conteos de horas"""

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window  # Referencia a HemodialysisHMI

        self.power_on_hours = 0.0
        self.total_operation_hours = 0.0
        self.cleaning_hours = 0.0

        self.operation_start_time = None
        self.cleaning_start_time = None
        self.last_resume_time = None

        # Timer interno para conteos precisos
        self._second_timer = QTimer(self)
        self._second_timer.setInterval(1000)  # Cada segundo
        self._second_timer.timeout.connect(self._on_second_tick)
        self._second_timer.start()

    def _on_second_tick(self):
        """Se ejecuta cada segundo"""
        hours_passed = 1 / 3600.0

        # Power On Hours - Siempre cuenta
        self.power_on_hours += hours_passed

        # Operation Hours
        if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
            self.total_operation_hours += hours_passed

        # Cleaning Hours
        if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
            self.cleaning_hours += hours_passed

        # Logging (delegamos al main por ahora)
        if hasattr(self.main, '_log_treatment_current_data') and self.main.treatment_logger:
            self.main._log_treatment_current_data()
        if hasattr(self.main, '_log_current_data') and self.main.csv_logger:
            self.main._log_current_data()
        if hasattr(self.main, '_log_cleaning_current_data') and self.main.cleaning_logger:
            self.main._log_cleaning_current_data()

    # ====================== MÉTODOS PÚBLICOS ======================

    def start_operation_timer(self):
        """Inicia conteo de horas de operación"""
        if not self.operation_start_time:
            self.operation_start_time = QDateTime.currentDateTime()
            logger.info("Operation timer iniciado")

    def pause_operation_timer(self):
        """Pausa el conteo de horas de operación"""
        self.operation_start_time = None
        self._save_operation_hours()

    def start_cleaning_timer(self):
        if not self.cleaning_start_time:
            self.cleaning_start_time = QDateTime.currentDateTime()

    def stop_cleaning_timer(self):
        self.cleaning_start_time = None
        self._save_cleaning_hours()

    def reset_therapy_accumulated(self):
        self.last_resume_time = None

    # ====================== PERSISTENCIA ======================

    def _save_operation_hours(self):
        self.main._save_operation_hours()   # Temporal, luego moveremos la lógica aquí

    def _save_cleaning_hours(self):
        self.main._save_cleaning_hours()

    def _save_power_on_hours(self):
        self.main._save_power_on_hours()

    def get_state_info(self):
        """Retorna información de tiempos para UI"""
        return {
            "power_on_hours": self.power_on_hours,
            "operation_hours": self.total_operation_hours,
            "cleaning_hours": self.cleaning_hours,
        }