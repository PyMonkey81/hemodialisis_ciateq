"""Controlador de tratamiento orientado a acciones y reacciones del GRAFCET."""

import logging
from PySide6.QtCore import QDateTime
from Actualizacion.state_manager import TreatmentPhase
from utilities.csv_logger import CsvLogger

logger = logging.getLogger(__name__)


class TreatmentController:
    def __init__(self, main_window):
        self.main = main_window
        self.state = self.main.state
        self.therapy_start_time: QDateTime | None = None
        self.accumulated_therapy_seconds = 0
        self.total_therapy_seconds = 0
        self.treatment_logger = None
        self.previous_phase = self.state.current_phase

    def request_start_treatment(self) -> bool:
        try:
            self.main._write_boolean_command("dialyModeOperationStart", True)
            self.main._write_boolean_command("dialyModeOperationStop", False)
            if hasattr(self.main, "bioz_urea_controller") and self.main.bioz_urea_controller:
                self.main.bioz_urea_controller.send_command("SRTB")
            return True
        except Exception as exc:
            logger.error(f"Error solicitando inicio de tratamiento: {exc}")
            self.main.show_error_message("Error al iniciar tratamiento")
            return False

    def request_pause_treatment(self) -> bool:
        if self.state.current_phase != TreatmentPhase.RUNNING:
            return False
        try:
            self.main._write_boolean_command("dialyModeOperationPause", True)
            return True
        except Exception as exc:
            logger.error(f"Error solicitando pausa: {exc}")
            self.main.show_error_message("Error al pausar tratamiento")
            return False

    def request_stop_treatment(self) -> bool:
        try:
            self.main._write_boolean_command("dialyModeOperationStop", True)
            self.main._write_boolean_command("dialyModeOperationStart", False)
            self.main._write_boolean_command("dialyStopDialysisButt", True)
            self.main._write_boolean_command("dialyStartDialysisButt", False)
            if hasattr(self.main, "bioz_urea_controller") and self.main.bioz_urea_controller:
                self.main.bioz_urea_controller.send_command("STOP")
            return True
        except Exception as exc:
            logger.error(f"Error solicitando detención de tratamiento: {exc}")
            self.main.show_error_message("Error al detener tratamiento")
            return False

    def on_state_changed(self, phase: TreatmentPhase, reason: str = "") -> None:
        if phase == TreatmentPhase.RUNNING:
            self._setup_treatment_logger()
            self._start_therapy_timer()
        elif phase == TreatmentPhase.PAUSED:
            self._pause_therapy_timer()
        elif phase == TreatmentPhase.IDLE:
            if self.previous_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.READY):
                self._close_treatment_session()
            self._reset_therapy_timer()

        self.previous_phase = phase

    def _setup_treatment_logger(self) -> None:
        if self.treatment_logger is not None:
            logger.debug("Logger de tratamiento ya existe, reanudando.")
            return
        try:
            self.treatment_logger = CsvLogger(
                log_directory="logs/tratamiento_hemodialisis",
                parameter_key_map=self.main.parameter_mapping,
            )
            logger.info("Logger de tratamiento creado.")
        except Exception as exc:
            logger.error(f"Error creando logger de tratamiento: {exc}")

    def _start_therapy_timer(self) -> None:
        if self.therapy_start_time is None:
            self.therapy_start_time = QDateTime.currentDateTime()
            logger.info("Timer de terapia iniciado.")

    def _pause_therapy_timer(self) -> None:
        if self.therapy_start_time is not None:
            self.accumulated_therapy_seconds += self.therapy_start_time.secsTo(QDateTime.currentDateTime())
            self.therapy_start_time = None
            logger.info(f"Timer de terapia pausado. Total acumulado: {self.accumulated_therapy_seconds}s")

    def _reset_therapy_timer(self) -> None:
        self.accumulated_therapy_seconds = 0
        self.therapy_start_time = None
        self.total_therapy_seconds = 0

    def _close_treatment_session(self) -> None:
        try:
            if self.treatment_logger is not None:
                self.treatment_logger.close()
                self.treatment_logger = None
            logger.info("Sesión de tratamiento finalizada y logger cerrado.")
        except Exception as exc:
            logger.warning(f"Error cerrando logger de tratamiento: {exc}")

    def get_elapsed_seconds(self) -> int:
        if self.therapy_start_time is None:
            return self.accumulated_therapy_seconds
        return self.accumulated_therapy_seconds + self.therapy_start_time.secsTo(QDateTime.currentDateTime())

    def update_therapy_times(self) -> None:
        phase = self.state.current_phase
        if phase not in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
            hours = int(self.main.current_values.get("heparineTherapyHours", 0))
            minutes = int(self.main.current_values.get("heparineTherapyMinutes", 0))
            self.total_therapy_seconds = hours * 3600 + minutes * 60
            remaining_str = f"{hours:02d}:{minutes:02d}:00"
            if hasattr(self.main, "dialysis_screen") and self.main.dialysis_screen:
                self.main.dialysis_screen.update_therapy_times("00:00:00", remaining_str)
            return

        current_elapsed = self.get_elapsed_seconds()
        remaining = max(0, self.total_therapy_seconds - current_elapsed)

        if self.total_therapy_seconds > 0 and remaining <= 0 and phase == TreatmentPhase.RUNNING:
            logger.info("Tiempo de terapia completado.")
            self.request_stop_treatment()
            if hasattr(self.main, "stop_priming"):
                self.main.stop_priming()
            return

        if hasattr(self.main, "dialysis_screen") and self.main.dialysis_screen:
            elapsed_str = f"{current_elapsed // 3600:02d}:{(current_elapsed % 3600) // 60:02d}:{current_elapsed % 60:02d}"
            remaining_str = f"{remaining // 3600:02d}:{(remaining % 3600) // 60:02d}:{remaining % 60:02d}"
            self.main.dialysis_screen.update_therapy_times(elapsed_str, remaining_str)
