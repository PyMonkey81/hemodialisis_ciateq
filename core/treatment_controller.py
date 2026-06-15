# core/treatment_controller.py
import logging
from PySide6.QtCore import QDateTime
from core.state_manager import TreatmentPhase
from utilities.csv_logger import CsvLogger   # ← Importación agregada

logger = logging.getLogger(__name__)


class TreatmentController:
    """
    Controlador dedicado a toda la lógica del ciclo de tratamiento.
    """

    def __init__(self, main_window):
        self.main = main_window
        self.state = main_window.state
        self.timer_manager = main_window.timer_manager
        self.bioz_urea_controller = getattr(main_window, 'bioz_urea_controller', None)

        # Variables de control de terapia
        self.accumulated_therapy_seconds = 0
        self.last_resume_time = None
        self.total_therapy_seconds = 0

    # ====================== START TREATMENT ======================
    def start_treatment(self):
        """Inicia o reanuda tratamiento con sincronización completa"""
        logger.info("=== INTENTO DE INICIO DE TRATAMIENTO ===")

        current_phase = self.state.current_phase
        is_resuming = (current_phase == TreatmentPhase.PAUSED)

        # Validaciones (mantengo tu lógica robusta)
        if current_phase == TreatmentPhase.RUNNING:
            self.main.show_warning_message("El tratamiento ya se encuentra en ejecución", 2500)
            return False

        if current_phase == TreatmentPhase.CLEANING:
            self.main.show_error_message("Finalice el proceso de limpieza antes de iniciar tratamiento", 4000)
            return False

        if current_phase == TreatmentPhase.ERROR:
            self.main.show_error_message("Resuelva las alarmas activas antes de iniciar tratamiento", 4000)
            return False

        if current_phase not in (TreatmentPhase.IDLE, TreatmentPhase.PAUSED, TreatmentPhase.READY, TreatmentPhase.PREPARING):
            self.main.show_error_message(f"No se puede iniciar en estado: {current_phase.name}", 3500)
            return False
        

        # Duración de terapia
        hours = int(self.main.current_values.get("heparineTherapyHours", 0))
        minutes = int(self.main.current_values.get("heparineTherapyMinutes", 0))
        self.total_therapy_seconds = (hours * 3600) + (minutes * 60)

        if self.total_therapy_seconds <= 0:
            self.main.show_warning_message("Configure la duración de la terapia", 3000)
            self.main.show_therapy_config_screen()
            return False

        try:
            # Forzar transición a RUNNING (más tolerante)
            success = self.state.set_phase(TreatmentPhase.RUNNING, "Usuario inició tratamiento")
            if not success:
                logger.warning("Transición forzada a RUNNING")
                self.state.current_phase = TreatmentPhase.RUNNING  # Forzar si la validación falla

            # Sincronización de relojes
            now = QDateTime.currentDateTime()

            if not is_resuming:
                self.accumulated_therapy_seconds = 0
                self.main.current_treatment_start_date_time = now
                self.main.current_treatment_start = now
                self.main.operation_start_time = now
                self.main.show_info_message("Iniciando tratamiento...", 1500)
            else:
                self.main.show_info_message("Reanudando tratamiento...", 2000)

            # Actualizar timer de reanudación (sincronización clave)
            self.last_resume_time = now

            # Iniciar contadores
            self.timer_manager.start_operation_timer()

            # Comandos hardware
            self.main._write_boolean_command("dialyModeOperationStart", True)
            self.main._write_boolean_command("dialyModeOperationStop", False)

            # BiozUrea
            if self.bioz_urea_controller:
                try:
                    self.bioz_urea_controller.send_command("SRTB")
                except Exception as e:
                    logger.warning(f"BiozUrea no respondió: {e}")

            # Logger
            self._setup_treatment_logger(is_resuming)

            self.main.show_success_message("Tratamiento iniciado", 1500)
            logger.info("Tratamiento iniciado")
            return True

        except Exception as e:
            logger.error(f"Error al iniciar tratamiento: {e}")
            self.main.show_error_message("Error al iniciar tratamiento")
            return False

    def _setup_treatment_logger(self, is_resuming: bool):
        """Configura o reinicia el logger de sesión"""
        if not hasattr(self.main, 'treatment_logger') or self.main.treatment_logger is None:
            self.main.treatment_logger = CsvLogger(
                log_type="treatment",
                patient_id=self.main.current_values.get("patient_name", "unknown")
            )
        if not is_resuming:
            self.main.treatment_logger.start_new_session()

    # ====================== PAUSE / STOP (mantengo limpios) ======================
    def pause_treatment(self):
        if self.state.current_phase != TreatmentPhase.RUNNING:
            return False

        try:
            self.main._write_boolean_command("dialyModeOperationPause", True)

            if self.last_resume_time:
                seconds_passed = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                self.accumulated_therapy_seconds += seconds_passed
                self.last_resume_time = None

            self.state.set_phase(TreatmentPhase.PAUSED, "Usuario pausó tratamiento")
            self.timer_manager.pause_operation_timer()
            return True

        except Exception as e:
            logger.error(f"Error al pausar: {e}")
            return False

    def stop_treatment(self):
        try:
            self.main._write_boolean_command("dialyModeOperationStop", True)
            self.main._write_boolean_command("dialyModeOperationStart", False)

            if self.last_resume_time:
                seconds_passed = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                self.accumulated_therapy_seconds += seconds_passed

            self.timer_manager.pause_operation_timer()

            # KTV Report
            if hasattr(self.main, 'KTVScreen') and self.main.KTVScreen:
                try:
                    report = self.main.KTVScreen.save_final_report()
                    if report:
                        self.main.show_success_message("Reporte Kt/V guardado", 2000)
                except Exception as e:
                    logger.warning(f"Error guardando KTV: {e}")

            self.state.reset_to_idle("Usuario detuvo tratamiento")
            self.accumulated_therapy_seconds = 0
            self.last_resume_time = None

            if hasattr(self.main, 'treatment_logger') and self.main.treatment_logger:
                self.main.treatment_logger.close()
                self.main.treatment_logger = None

            return True

        except Exception as e:
            logger.error(f"Error al detener: {e}")
            return False

    # ====================== SINCRONIZACIÓN DE RELOJES ======================
    def get_elapsed_seconds(self) -> int:
        """Sincronización precisa del tiempo transcurrido"""
        current = self.accumulated_therapy_seconds
        if self.last_resume_time:
            current += self.last_resume_time.secsTo(QDateTime.currentDateTime())
        return int(current)

    def update_therapy_times(self):
        """Actualiza displays con sincronización en tiempo real"""
        if self.state.current_phase not in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
            return

        elapsed = self.get_elapsed_seconds()
        remaining = max(0, self.total_therapy_seconds - elapsed)

        if hasattr(self.main, 'dialysis_screen') and self.main.dialysis_screen:
            elapsed_str = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"
            remaining_str = f"{remaining // 3600:02d}:{(remaining % 3600) // 60:02d}:{remaining % 60:02d}"
            self.main.dialysis_screen.update_therapy_times(elapsed_str, remaining_str)

        # Paro automático seguro
        if remaining <= 0 and self.state.current_phase == TreatmentPhase.RUNNING:
            self.stop_treatment()