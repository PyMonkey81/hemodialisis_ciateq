# core/timer_manager.py
import logging
import json
import os
from PySide6.QtCore import QObject, QTimer, QDateTime
from core.state_manager import TreatmentPhase
from core.hardware_state_mapper import HardwareStateMapper

logger = logging.getLogger(__name__)


class TimerManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.hardware_mapper = None  # Se inyecta desde appMainHemodialysis

        # Horas totales persistentes
        self.power_on_hours = 0.0
        self.total_operation_hours = 0.0
        self.cleaning_hours = 0.0

        self.operation_start_time = None
        self.cleaning_start_time = None
        self.is_cleaning_paused = False
        self.last_power_on_tick = QDateTime.currentDateTime()

        self._load_all_hours()

        # Timer principal
        self._second_timer = QTimer(self)
        self._second_timer.setInterval(1000)
        self._second_timer.timeout.connect(self._on_second_tick)
        self._second_timer.start()

        logger.info("TimerManager iniciado con mapper de hardware")

    def _on_second_tick(self):
        """Actualización precisa de todos los contadores"""
        now = QDateTime.currentDateTime()
        
        status_code = int(self.main.current_values.get("primingProcessStatus", 0))
        treatment_mode = int(self.main.current_values.get("treatmentModeSelection", 0))

        # ==================== POWER ON (siempre activo) ====================
        msecs_power = self.last_power_on_tick.msecsTo(now)
        self.power_on_hours += msecs_power / 3600000.0
        self.last_power_on_tick = now

        # ==================== OPERATION HOURS (solo tratamiento real) ====================
        if (self.hardware_mapper and 
            self.hardware_mapper.should_count_operation_time(status_code, treatment_mode)):
            
            if not self.operation_start_time:
                self.operation_start_time = now
            else:
                msecs_op = self.operation_start_time.msecsTo(now)
                self.total_operation_hours += msecs_op / 3600000.0
                self.operation_start_time = now
                
        elif self.operation_start_time:
            # Acumular antes de pausar (pausa, idle, limpieza, etc.)
            msecs_op = self.operation_start_time.msecsTo(now)
            self.total_operation_hours += msecs_op / 3600000.0
            self.operation_start_time = None

        # ==================== CLEANING HOURS ====================
        # if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
        #     msecs_clean = self.cleaning_start_time.msecsTo(now)
        #     self.cleaning_hours += msecs_clean / 3600000.0
        #     self.cleaning_start_time = now
        if (self.main.state.current_phase == TreatmentPhase.CLEANING and 
            self.cleaning_start_time and 
            not self.is_cleaning_paused):
            
            msecs_clean = self.cleaning_start_time.msecsTo(now)
            self.cleaning_hours += msecs_clean / 3600000.0
            self.cleaning_start_time = now   # reset para próximo tick
        self._update_maintenance_screen()

    def sync_with_hardware(self, status_code: int):
        """Sincronización llamada desde update_value cuando cambia primingProcessStatus"""
        if not self.hardware_mapper:
            return
            
        treatment_mode = int(self.main.current_values.get("treatmentModeSelection", 0))
        
        if self.hardware_mapper.should_count_operation_time(status_code, treatment_mode):
            if not self.operation_start_time:
                self.operation_start_time = QDateTime.currentDateTime()
        else:
            if self.operation_start_time:
                now = QDateTime.currentDateTime()
                msecs = self.operation_start_time.msecsTo(now)
                self.total_operation_hours += msecs / 3600000.0
                self.operation_start_time = None

    # =============== CLEANING ========================

    # def start_cleaning_timer(self):
    #     """Inicia conteo de limpieza"""
    #     self.cleaning_start_time = QDateTime.currentDateTime()

    # def stop_cleaning_timer(self):
    #     """Detiene y guarda conteo de limpieza"""
    #     if self.cleaning_start_time:
    #         now = QDateTime.currentDateTime()
    #         msecs = self.cleaning_start_time.msecsTo(now)
    #         self.cleaning_hours += msecs / 3600000.0
    #         self.cleaning_start_time = None
    #     self._save_cleaning_hours()    
    
    def start_cleaning_timer(self):
        self.cleaning_start_time = QDateTime.currentDateTime()
        self.is_cleaning_paused = False

    def pause_cleaning_timer(self):
        if self.cleaning_start_time:
            self._accumulate_cleaning_segment()
            self.is_cleaning_paused = True

    def resume_cleaning_timer(self):
        self.cleaning_start_time = QDateTime.currentDateTime()
        self.is_cleaning_paused = False

    def _accumulate_cleaning_segment(self):
        """Acumula el segmento actual"""
        if self.cleaning_start_time:
            msecs = self.cleaning_start_time.msecsTo(QDateTime.currentDateTime())
            self.cleaning_hours += msecs / 3600000.0
            self.cleaning_start_time = None

    def stop_cleaning_timer(self):
        if self.cleaning_start_time:
            self._accumulate_cleaning_segment()
        self.is_cleaning_paused = False
        self._save_cleaning_hours()
    
    
    # =======================================================================

    def get_hours_info(self):
        return {
            "power_on": round(self.power_on_hours, 6),
            "operation": round(self.total_operation_hours, 6),
            "cleaning": round(self.cleaning_hours, 6)
        }

    def _update_maintenance_screen(self):
        try:
            if hasattr(self.main, 'maintenance_screen') and self.main.maintenance_screen:
                self.main.maintenance_screen.update_hours_display(
                    self.power_on_hours,
                    self.total_operation_hours,
                    self.cleaning_hours
                )
        except Exception as e:
            logger.debug(f"Error actualizando pantalla de mantenimiento: {e}")

    # ====================== PERSISTENCIA ======================
    def _load_all_hours(self):
        self._load_power_on_hours()
        self._load_operation_hours()
        self._load_cleaning_hours()

    def _save_all_hours(self):
        self._save_power_on_hours()
        self._save_operation_hours()
        self._save_cleaning_hours()

    def _load_power_on_hours(self):
        try:
            path = "config/power_on_hours.json"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.power_on_hours = data.get("power_on_hours", 0.0)
        except Exception as e:
            logger.warning(f"Error cargando power_on_hours: {e}")

    def _save_power_on_hours(self):
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/power_on_hours.json", 'w') as f:
                json.dump({
                    "power_on_hours": round(self.power_on_hours, 6),
                    "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                }, f, indent=4)
        except Exception as e:
            logger.warning(f"Error guardando power_on_hours: {e}")

    def _load_operation_hours(self):
        try:
            path = "config/operation_hours.json"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.total_operation_hours = data.get("total_operation_hours", 0.0)
        except Exception as e:
            logger.warning(f"Error cargando operation_hours: {e}")

    def _save_operation_hours(self):
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/operation_hours.json", 'w') as f:
                json.dump({
                    "total_operation_hours": round(self.total_operation_hours, 6),
                    "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                }, f, indent=4)
        except Exception as e:
            logger.warning(f"Error guardando operation_hours: {e}")

    def _load_cleaning_hours(self):
        try:
            path = "config/cleaning_hours.json"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.cleaning_hours = data.get("cleaning_hours", 0.0)
        except Exception as e:
            logger.warning(f"Error cargando cleaning_hours: {e}")

    def _save_cleaning_hours(self):
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/cleaning_hours.json", 'w') as f:
                json.dump({
                    "cleaning_hours": round(self.cleaning_hours, 6),
                    "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                }, f, indent=4)
        except Exception as e:
            logger.warning(f"Error guardando cleaning_hours: {e}")