# core/treatment_controller.py
import logging
from PySide6.QtCore import QDateTime
from core.state_manager import TreatmentPhase
from utilities.csv_logger import CsvLogger

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

        # Variables de tiempo de terapia
        self.accumulated_therapy_seconds = 0
        self.last_resume_time = None
        self.total_therapy_seconds = 0
        self._current_elapsed_therapy_min = 0.0

    # ====================== START TREATMENT ======================
    def start_treatment(self):
        """Inicia o reanuda tratamiento con toda la lógica robusta"""
        logger.info("=== INTENTO DE INICIO DE TRATAMIENTO ===")

        current_phase = self.state.current_phase
        is_resuming = (current_phase == TreatmentPhase.PAUSED)

        # ==================== VALIDACIONES ====================
        if current_phase == TreatmentPhase.RUNNING:
            logger.warning("Tratamiento ya está en ejecución")
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

        # Validación de duración
        hours = int(self.main.current_values.get("heparineTherapyHours", 0))
        minutes = int(self.main.current_values.get("heparineTherapyMinutes", 0))
        self.total_therapy_seconds = (hours * 3600) + (minutes * 60)

        if self.total_therapy_seconds <= 0:
            self.main.show_warning_message("Configure la duración de la terapia", 3000)
            self.main.show_therapy_config_screen()
            return False

        try:
            # ==================== INICIO / REANUDACIÓN ====================
            if not is_resuming:
                success = self.state.set_phase(TreatmentPhase.RUNNING, "Inicio de tratamiento")
                if not success:
                    return False
                
                self.accumulated_therapy_seconds = 0
                self.main.current_treatment_start_date_time = QDateTime.currentDateTime()
                self.main.current_treatment_start = QDateTime.currentDateTime()
                self.main.operation_start_time = QDateTime.currentDateTime()
                
                self.main.show_info_message("Iniciando tratamiento...", 1500)
            else:
                success = self.state.set_phase(TreatmentPhase.RUNNING, "Reanudación de tratamiento")
                if not success:
                    return False
                self.main.show_info_message("Reanudando tratamiento...", 2000)

            # Timer de terapia
            self.last_resume_time = QDateTime.currentDateTime()
            self.timer_manager.start_operation_timer()

            # ==================== COMANDOS HARDWARE ====================
            self.main._write_boolean_command("dialyModeOperationStart", True)
            self.main._write_boolean_command("dialyModeOperationStop", False)

            # BiozUrea
            if self.bioz_urea_controller:
                try:
                    self.bioz_urea_controller.send_command("SRTB")
                except Exception as e:
                    logger.warning(f"No se pudo iniciar BiozUrea: {e}")

            # Logger de sesión
            self._setup_treatment_logger(is_resuming)

            logger.info(f"✅ Tratamiento {'reanudado' if is_resuming else 'iniciado'} correctamente")
            return True

        except Exception as e:
            logger.error(f"Error al iniciar tratamiento: {e}")
            self.main.show_error_message("Error al iniciar tratamiento")
            return False

    def _setup_treatment_logger(self, is_resuming: bool):
        """Configura el logger CSV de tratamiento"""
        if not hasattr(self.main, 'treatment_logger') or self.main.treatment_logger is None:
            self.main.treatment_logger = CsvLogger(
                log_type="treatment",
                patient_id=self.main.current_values.get("patient_name", "unknown")
            )
        if not is_resuming:
            self.main.treatment_logger.start_new_session()

    # ====================== PAUSE TREATMENT ======================
    def pause_treatment(self):
        """Pausa el tratamiento"""
        if self.state.current_phase != TreatmentPhase.RUNNING:
            logger.warning("No se puede pausar: no hay tratamiento activo")
            return False

        try:
            self.main._write_boolean_command("dialyModeOperationPause", True)

            # Acumular tiempo transcurrido
            if self.last_resume_time:
                seconds_passed = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                self.accumulated_therapy_seconds += seconds_passed
                self.last_resume_time = None

            self.state.set_phase(TreatmentPhase.PAUSED, "Usuario pausó tratamiento")
            self.timer_manager.pause_operation_timer()

            logger.info("Tratamiento pausado correctamente")
            return True

        except Exception as e:
            logger.error(f"Error al pausar tratamiento: {e}")
            return False

    # ====================== STOP TREATMENT ======================
    def stop_treatment(self):
        """Detiene completamente el tratamiento"""
        try:
            self.main._write_boolean_command("dialyModeOperationStop", True)
            # self.main._write_boolean_command("dialyModeOperationStart", False)

            # Acumular tiempo final
            if self.last_resume_time:
                seconds_passed = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                self.accumulated_therapy_seconds += seconds_passed

            self.timer_manager.pause_operation_timer()

            # Guardar reporte KTV
            if hasattr(self.main, 'KTVScreen') and self.main.KTVScreen:
                try:
                    report = self.main.KTVScreen.save_final_report()
                    if report:
                        self.main.show_success_message("Reporte Kt/V guardado", 2000)
                    
                    # Limpiar registros para próxima sesión
                    if hasattr(self.KTVScreen, 'ktv_records'):
                        self.KTVScreen.ktv_records.clear()
                    if hasattr(self.KTVScreen, 'ktv_points'):
                        self.KTVScreen.ktv_points.clear()
                    if hasattr(self.KTVScreen, 'heit_points'):
                        self.KTVScreen.heit_points.clear()
                except Exception as e:
                    logger.warning(f"Error guardando reporte KTV: {e}")

            # Resetear estado
            self.state.reset_to_idle("Usuario detuvo tratamiento")

            # Limpiar variables
            self.accumulated_therapy_seconds = 0
            self.last_resume_time = None

            # Cerrar logger
            if hasattr(self.main, 'treatment_logger') and self.main.treatment_logger:
                self.main.treatment_logger.close()
                self.main.treatment_logger = None

            logger.info("Tratamiento detenido completamente")
            return True

        except Exception as e:
            logger.error(f"Error al detener tratamiento: {e}")
            self.main.show_error_message("Error al detener tratamiento")
            return False

    # ====================== HELPERS ======================
    def get_elapsed_seconds(self) -> int:
        current = self.accumulated_therapy_seconds
        if self.last_resume_time:
            current += self.last_resume_time.secsTo(QDateTime.currentDateTime())
        return int(current)

    def get_remaining_seconds(self) -> int:
        return max(0, self.total_therapy_seconds - self.get_elapsed_seconds())

    def update_therapy_times(self):
        """Actualiza displays de tiempo en la pantalla de diálisis"""
        if self.state.current_phase not in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
            return

        elapsed = self.get_elapsed_seconds()
        remaining = self.get_remaining_seconds()

        if hasattr(self.main, 'dialysis_screen') and self.main.dialysis_screen:
            elapsed_str = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"
            remaining_str = f"{remaining // 3600:02d}:{(remaining % 3600) // 60:02d}:{remaining % 60:02d}"
            
            self.main.dialysis_screen.update_therapy_times(elapsed_str, remaining_str)

        # Paro automático al terminar
        if remaining <= 0 and self.state.current_phase == TreatmentPhase.RUNNING:
            self.stop_treatment()