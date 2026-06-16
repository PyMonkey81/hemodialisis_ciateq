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
        self.current_elapsed = 0
        self.remaining = 0
        self.accumulated_therapy_seconds = 0
        self.last_resume_time = None
        self.total_therapy_seconds = 0

    # ====================== START TREATMENT ======================

    def start_treatment(self):
        """Inicia o reanuda tratamiento con mensaje correcto"""
        logger.info("=== INTENTO DE INICIO DE TRATAMIENTO ===")

        current_phase = self.state.current_phase

        if current_phase == TreatmentPhase.RUNNING:
            logger.warning("Ya está en RUNNING - ignorando comando repetido")
            return False

        if current_phase == TreatmentPhase.CLEANING:
            self.main.show_error_message("Finalice primero la limpieza", 3000)
            return False

        try:
            # Comandos al hardware
            self.main._write_boolean_command("dialyModeOperationStart", True)
            self.main._write_boolean_command("dialyModeOperationStop", False)

            # BiozUrea
            if self.bioz_urea_controller:
                try:
                    self.bioz_urea_controller.send_command("SRTB")
                    print("enviando comando a bio")
                except Exception as e:
                    logger.warning(f"BiozUrea no respondió: {e}")
                    print("no hay controlador bio")
            return True

        except Exception as e:
            logger.error(f"Error al iniciar tratamiento: {e}")
            self.main.show_error_message("Error al iniciar tratamiento")
            return False
        
    def _setup_treatment_logger(self, is_resuming: bool):
        """Configura o reinicia el logger de sesión"""
        if is_resuming and self.main.treatment_logger is not None:
            logger.info("Reanudando logger existente")
        else: 
            if self.main.treatment_logger:
                self.main.treatment_logger.close()
                self.main.treatment_logger = None

            try:
                LOG_DIRECTORY = "logs/tratamiento_hemodialisis"
                self.main.treatment_logger = CsvLogger(
                    log_directory=LOG_DIRECTORY,
                    parameter_key_map=self.main.parameter_mapping
                )
                logger.info("Nuevo logger CSV creado por el tratamiento")
            except Exception as e:
                logger.error(f"Error creando logger CSV: {e}")
                return 
      

    # ====================== PAUSE / STOP (mantengo limpios) ======================

    def pause_treatment(self):
        if self.state.current_phase != TreatmentPhase.RUNNING:
            return False
        try:
            self.main._write_boolean_command("dialyModeOperationPause", True)
            return True
        except Exception as e:
            logger.error(f"Error al pausar: {e}")
            return False


        
    def stop_treatment(self):
        """Detiene completamente el tratamiento"""
        try:
            # Comandos al hardware
            self.main._write_boolean_command("dialyModeOperationStop", True)
            self.main._write_boolean_command("dialyModeOperationStart", False)
            self.main._write_boolean_command("dialyStopDialysisButt",True) # detiene secuencia de cebado tambien 
            self.main._write_boolean_command("dialyStartDialysisButt", False)              
            return True

        except Exception as e:
            logger.error(f"Error al detener tratamiento: {e}")
            self.main.show_error_message("Error al detener tratamiento")
            return False

    # ====================== SINCRONIZACIÓN DE RELOJES ======================

    def get_elapsed_seconds(self) -> int:
        """Obtiene elapsed usando TimerManager (más confiable)"""
        if hasattr(self.main, 'timer_manager') and self.main.timer_manager:
            # Calculamos elapsed a partir de horas totales guardadas
            hours = self.main.timer_manager.total_operation_hours
            return int(hours * 3600)
        return 0

    def update_therapy_times(self):
        """Actualiza tiempos con lógica limpia y sincronizada"""
        phase = self.state.current_phase
        status_code = int(self.main.current_values.get("primingProcessStatus", 0))
        treatment_mode = int(self.main.current_values.get("treatmentModeSelection", 0))

        # Fuera de terapia activa
        if phase not in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
            hours = int(self.main.current_values.get("heparineTherapyHours", 0))
            minutes = int(self.main.current_values.get("heparineTherapyMinutes", 0))
            self.total_therapy_seconds = (hours * 3600) + (minutes * 60)
            
            remaining_str = f"{hours:02d}:{minutes:02d}:00"
            
            if hasattr(self.main, 'dialysis_screen') and self.main.dialysis_screen:
                self.main.dialysis_screen.update_therapy_times(remaining_str, "00:00:00")
            return

        # ==================== TERAPIA ACTIVA ====================
        current_elapsed = self.get_elapsed_seconds()
        remaining = max(0, self.total_therapy_seconds - current_elapsed)

        # Paro automático cuando se termina el tiempo
        if remaining <= 0 and phase == TreatmentPhase.RUNNING and status_code == 14:
            logger.info(f"Tiempo completado (elapsed={current_elapsed}s) → Paro automático")
            self.stop_treatment()
            return

        # Actualizar pantalla
        if hasattr(self.main, 'dialysis_screen') and self.main.dialysis_screen:
            elapsed_str = f"{current_elapsed // 3600:02d}:{(current_elapsed % 3600) // 60:02d}:{current_elapsed % 60:02d}"
            remaining_str = f"{remaining // 3600:02d}:{(remaining % 3600) // 60:02d}:{remaining % 60:02d}"
            
            self.main.dialysis_screen.update_therapy_times(elapsed_str, remaining_str)

