# core/timer_manager.py
import logging
import json
import os
from PySide6.QtCore import QObject, QTimer, QDateTime
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)

class TimerManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

        # Cargar valores existentes (nunca resetear a 0)
        self.power_on_hours = 0.0
        self.total_operation_hours = 0.0
        self.cleaning_hours = 0.0

        self.operation_start_time = None
        self.cleaning_start_time = None
        self.last_power_on_tick = QDateTime.currentDateTime()

        # Cargar desde archivos
        self._load_all_hours()

        # Timer cada segundo
        self._second_timer = QTimer(self)
        self._second_timer.setInterval(1000)
        self._second_timer.timeout.connect(self._on_second_tick)
        self._second_timer.start()

        logger.info(f"TimerManager iniciado con datos existentes - "
                   f"PowerOn: {self.power_on_hours:.6f}h | "
                   f"Operation: {self.total_operation_hours:.6f}h | "
                   f"Cleaning: {self.cleaning_hours:.6f}h")

    def _on_second_tick(self):
        """Actualización precisa usando milisegundos para evitar pérdida de fracciones"""
        now = QDateTime.currentDateTime()

        # Power On (siempre activo) - Usando milisegundos para fraccionamiento exacto
        msecs_power = self.last_power_on_tick.msecsTo(now)
        self.power_on_hours += msecs_power / 3600000.0
        self.last_power_on_tick = now

        # Operación (tratamiento)
        if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
            msecs_op = self.operation_start_time.msecsTo(now)
            self.total_operation_hours += msecs_op / 3600000.0
            self.operation_start_time = now

        # Limpieza
        if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
            msecs_clean = self.cleaning_start_time.msecsTo(now)
            self.cleaning_hours += msecs_clean / 3600000.0
            self.cleaning_start_time = now

        # Actualizar pantalla
        self._update_maintenance_screen()

    def start_operation_timer(self):
        self.operation_start_time = QDateTime.currentDateTime()

    def pause_operation_timer(self):
        if self.operation_start_time:
            msecs = self.operation_start_time.msecsTo(QDateTime.currentDateTime())
            self.total_operation_hours += msecs / 3600000.0
            self.operation_start_time = None
        self._save_operation_hours()

    def start_cleaning_timer(self):
        self.cleaning_start_time = QDateTime.currentDateTime()

    def stop_cleaning_timer(self):
        if self.cleaning_start_time:
            msecs = self.cleaning_start_time.msecsTo(QDateTime.currentDateTime())
            self.cleaning_hours += msecs / 3600000.0
            self.cleaning_start_time = None
        self._save_cleaning_hours()

    def get_hours_info(self):
        return {
            "power_on": self.power_on_hours,
            "operation": self.total_operation_hours,
            "cleaning": self.cleaning_hours
        }

    def _update_maintenance_screen(self):
        try:
            if hasattr(self.main, 'maintenance_screen') and self.main.maintenance_screen:
                self.main.maintenance_screen.update_hours_display(
                    self.power_on_hours,
                    self.total_operation_hours,
                    self.cleaning_hours
                )
        except:
            pass

    # ====================== CARGA Y GUARDADO (PRESERVA DATOS) ======================
    def _load_all_hours(self):
        self._load_power_on_hours()
        self._load_operation_hours()
        self._load_cleaning_hours()

    def _save_all_hours(self):
        self._save_power_on_hours()
        self._save_operation_hours()
        self._save_cleaning_hours()

    # NOTA: Los guardados usan round(..., 6). Esto es correcto.
    # 6 decimales de hora equivale a 0.0036 segundos, preservando la fracción de forma perfecta.

    def _load_power_on_hours(self):
        try:
            path = "config/power_on_hours.json"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.power_on_hours = data.get("power_on_hours", data.get("hours", 0.0))
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
                    self.total_operation_hours = data.get("total_operation_hours", data.get("hours", 0.0))
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
                    self.cleaning_hours = data.get("cleaning_hours", data.get("hours", 0.0))
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


# # core/timer_manager.py
# import logging
# import json
# import os
# from PySide6.QtCore import QObject, QTimer, QDateTime
# from core.state_manager import TreatmentPhase

# logger = logging.getLogger(__name__)

# class TimerManager(QObject):
#     def __init__(self, main_window):
#         super().__init__()
#         self.main = main_window

#         # Cargar valores existentes (nunca resetear a 0)
#         self.power_on_hours = 0.0
#         self.total_operation_hours = 0.0
#         self.cleaning_hours = 0.0

#         self.operation_start_time = None
#         self.cleaning_start_time = None
#         self.last_power_on_tick = QDateTime.currentDateTime()

#         # Cargar desde archivos
#         self._load_all_hours()

#         # Timer cada segundo
#         self._second_timer = QTimer(self)
#         self._second_timer.setInterval(1000)
#         self._second_timer.timeout.connect(self._on_second_tick)
#         self._second_timer.start()

#         logger.info(f"TimerManager iniciado con datos existentes - "
#                    f"PowerOn: {self.power_on_hours:.4f}h | "
#                    f"Operation: {self.total_operation_hours:.4f}h | "
#                    f"Cleaning: {self.cleaning_hours:.4f}h")

#     def _on_second_tick(self):
#         """Actualización precisa cada segundo"""
#         now = QDateTime.currentDateTime()

#         # Power On (siempre activo)
#         seconds_power = self.last_power_on_tick.secsTo(now)
#         self.power_on_hours += seconds_power / 3600.0
#         self.last_power_on_tick = now

#         # Operación (tratamiento)
#         if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
#             seconds_op = self.operation_start_time.secsTo(now)
#             self.total_operation_hours += seconds_op / 3600.0
#             self.operation_start_time = now

#         # Limpieza
#         if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
#             seconds_clean = self.cleaning_start_time.secsTo(now)
#             self.cleaning_hours += seconds_clean / 3600.0
#             self.cleaning_start_time = now

#         # Actualizar pantalla
#         self._update_maintenance_screen()

#     def start_operation_timer(self):
#         self.operation_start_time = QDateTime.currentDateTime()

#     def pause_operation_timer(self):
#         if self.operation_start_time:
#             seconds = self.operation_start_time.secsTo(QDateTime.currentDateTime())
#             self.total_operation_hours += seconds / 3600.0
#             self.operation_start_time = None
#         self._save_operation_hours()

#     def start_cleaning_timer(self):
#         self.cleaning_start_time = QDateTime.currentDateTime()

#     def stop_cleaning_timer(self):
#         if self.cleaning_start_time:
#             seconds = self.cleaning_start_time.secsTo(QDateTime.currentDateTime())
#             self.cleaning_hours += seconds / 3600.0
#             self.cleaning_start_time = None
#         self._save_cleaning_hours()

#     def get_hours_info(self):
#         return {
#             "power_on": self.power_on_hours,
#             "operation": self.total_operation_hours,
#             "cleaning": self.cleaning_hours
#         }

#     def _update_maintenance_screen(self):
#         try:
#             if hasattr(self.main, 'maintenance_screen') and self.main.maintenance_screen:
#                 self.main.maintenance_screen.update_hours_display(
#                     self.power_on_hours,
#                     self.total_operation_hours,
#                     self.cleaning_hours
#                 )
#         except:
#             pass

#     # ====================== CARGA Y GUARDADO (PRESERVA DATOS) ======================
#     def _load_all_hours(self):
#         self._load_power_on_hours()
#         self._load_operation_hours()
#         self._load_cleaning_hours()

#     def _save_all_hours(self):
#         self._save_power_on_hours()
#         self._save_operation_hours()
#         self._save_cleaning_hours()

#     def _load_power_on_hours(self):
#         try:
#             path = "config/power_on_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.power_on_hours = data.get("power_on_hours", data.get("hours", 0.0))
#         except Exception as e:
#             logger.warning(f"Error cargando power_on_hours: {e}")

#     def _save_power_on_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/power_on_hours.json", 'w') as f:
#                 json.dump({
#                     "power_on_hours": round(self.power_on_hours, 6),
#                     "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
#                 }, f, indent=4)
#         except Exception as e:
#             logger.warning(f"Error guardando power_on_hours: {e}")

#     def _load_operation_hours(self):
#         try:
#             path = "config/operation_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.total_operation_hours = data.get("total_operation_hours", data.get("hours", 0.0))
#         except Exception as e:
#             logger.warning(f"Error cargando operation_hours: {e}")

#     def _save_operation_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/operation_hours.json", 'w') as f:
#                 json.dump({
#                     "total_operation_hours": round(self.total_operation_hours, 6),
#                     "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
#                 }, f, indent=4)
#         except Exception as e:
#             logger.warning(f"Error guardando operation_hours: {e}")

#     def _load_cleaning_hours(self):
#         try:
#             path = "config/cleaning_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.cleaning_hours = data.get("cleaning_hours", data.get("hours", 0.0))
#         except Exception as e:
#             logger.warning(f"Error cargando cleaning_hours: {e}")

#     def _save_cleaning_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/cleaning_hours.json", 'w') as f:
#                 json.dump({
#                     "cleaning_hours": round(self.cleaning_hours, 6),
#                     "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
#                 }, f, indent=4)
#         except Exception as e:
#             logger.warning(f"Error guardando cleaning_hours: {e}")


# # core/timer_manager.py
# import logging
# import json
# import os
# from PySide6.QtCore import QObject, QTimer, QDateTime
# from core.state_manager import TreatmentPhase

# logger = logging.getLogger(__name__)

# class TimerManager(QObject):
#     def __init__(self, main_window):
#         super().__init__()
#         self.main = main_window

#         # Horas persistentes
#         self.power_on_hours = 0.0
#         self.total_operation_hours = 0.0
#         self.cleaning_hours = 0.0

#         # Timers de referencia para medición precisa
#         self.last_power_on_tick = QDateTime.currentDateTime()
#         self.operation_start_time = None
#         self.cleaning_start_time = None

#         self._load_all_hours()
    
#         # Timer principal
#         self._second_timer = QTimer(self)
#         self._second_timer.setInterval(1000)
#         self._second_timer.timeout.connect(self._on_second_tick)
#         self._second_timer.start()

#         logger.info(f"TimerManager iniciado - PowerOn: {self.power_on_hours:.2f}h | "
#                    f"Operation: {self.total_operation_hours:.2f}h | "
#                    f"Cleaning: {self.cleaning_hours:.2f}h")

#     def _on_second_tick(self):
#         """Actualización cada segundo"""
#         # hours_passed = 1 / 3600.0
#         # self.power_on_hours += hours_passed
        
#         now = QDateTime.currentDateTime()
#         # Power On (siempre)
#         seconds_power = self.last_power_on_tick.secsTo(now)
#         self.power_on_hours += seconds_power / 3600.0
#         self.last_power_on_tick = now

#         # Operación (tratamiento)
#         if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
#             seconds_op = self.operation_start_time.secsTo(now)
#             self.total_operation_hours += seconds_op / 3600.0
#             self.operation_start_time = now

#         # if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
#         #     self.total_operation_hours += hours_passed

#         # Limpieza
#         if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
#             seconds_clean = self.cleaning_start_time.secsTo(now)
#             self.cleaning_hours += seconds_clean / 3600.0
#             self.cleaning_start_time = now

#         # if self.main.state.current_phase == TreatmentPhase.CLEANING:
#         #     self.cleaning_hours += hours_passed

#         # Actualizar pantalla de mantenimiento de forma segura
#         self._update_maintenance_screen()

#     def _update_maintenance_screen(self):
#         """Actualiza la pantalla de mantenimiento de forma segura"""
#         try:
#             if hasattr(self.main, 'maintenance_screen') and self.main.maintenance_screen:
#                 self.main.maintenance_screen.update_hours_display(
#                     self.power_on_hours,
#                     self.total_operation_hours,
#                     self.cleaning_hours
#                 )
#         except Exception as e:
#             logger.debug(f"MaintenanceScreen no disponible aún: {e}")

#     def start_operation_timer(self):
#         self.operation_start_time = QDateTime.currentDateTime()
#         self._save_operation_hours()

#     # def pause_operation_timer(self):
#     #     self.operation_start_time = None
#     #     self._save_operation_hours()
#     def pause_operation_timer(self):
#         if self.operation_start_time:
#             seconds = self.operation_start_time.secsTo(QDateTime.currentDateTime())
#             self.total_operation_hours += seconds / 3600.0
#             self.operation_start_time = None
#         self._save_operation_hours()


#     def start_cleaning_timer(self):
#         self.cleaning_start_time = QDateTime.currentDateTime()
#         self._save_cleaning_hours()

#     # def stop_cleaning_timer(self):
#     #     self.cleaning_start_time = None
#     #     self._save_cleaning_hours()
#     def stop_cleaning_timer(self):
#         if self.cleaning_start_time:
#             seconds = self.cleaning_start_time.secsTo(QDateTime.currentDateTime())
#             self.cleaning_hours += seconds / 3600.0
#             self.cleaning_start_time = None
#         self._save_cleaning_hours()


#     def get_hours_info(self):
#         return {
#             "power_on": round(self.power_on_hours, 6),
#             "operation": round(self.total_operation_hours, 6),
#             "cleaning": round(self.cleaning_hours, 6)
#         }

#     # ====================== PERSISTENCIA ======================
#     def _load_all_hours(self):
#         """Carga los valores existentes sin resetear"""
#         self._load_power_on_hours()
#         self._load_operation_hours()
#         self._load_cleaning_hours()

#     def _save_all_hours(self):
#         self._save_power_on_hours()
#         self._save_operation_hours()
#         self._save_cleaning_hours()

#     def _load_power_on_hours(self):
#         try:
#             path = "config/power_on_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.power_on_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando power_on_hours: {e}")

#     def _save_power_on_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/power_on_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.power_on_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando power_on_hours: {e}")

#     def _load_operation_hours(self):
#         try:
#             path = "config/operation_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.total_operation_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando operation_hours: {e}")

#     def _save_operation_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/operation_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.total_operation_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando operation_hours: {e}")

#     def _load_cleaning_hours(self):
#         try:
#             path = "config/cleaning_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.cleaning_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando cleaning_hours: {e}")

#     def _save_cleaning_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/cleaning_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.cleaning_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando cleaning_hours: {e}")

# import logging
# import json
# import os
# from PySide6.QtCore import QObject, QTimer, QDateTime
# from core.state_manager import TreatmentPhase

# logger = logging.getLogger(__name__)

# class TimerManager(QObject):
#     """Gestor centralizado de timers y conteos de horas"""

#     def __init__(self, main_window):
#         super().__init__()
#         self.main = main_window

#         self.power_on_hours = 0.0
#         self.total_operation_hours = 0.0
#         self.cleaning_hours = 0.0

#         self.operation_start_time = None
#         self.cleaning_start_time = None
#         self.last_resume_time = None

#         self._second_timer = QTimer(self)
#         self._second_timer.setInterval(1000)
#         self._second_timer.timeout.connect(self._on_second_tick)
#         self._second_timer.start()

#         self.operation_start_time = None
#         self.cleaning_start_time = None

#         self._load_all_hours()

#     def _on_second_tick(self):
#         hours_passed = 1 / 3600.0

#         self.power_on_hours += hours_passed

#         # if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED) and self.operation_start_time:
#         #     self.total_operation_hours += hours_passed

#         # if self.main.state.current_phase == TreatmentPhase.CLEANING and self.cleaning_start_time:
#         #     self.cleaning_hours += hours_passed

#         # Operación (tratamiento)
#         if self.main.state.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
#             self.total_operation_hours += hours_passed

#         # Limpieza
#         if self.main.state.current_phase == TreatmentPhase.CLEANING:
#             self.cleaning_hours += hours_passed

#         # Actualizar pantalla de mantenimiento
#         if hasattr(self.main, 'maintenance_screen') and self.main.maintenance_screen:
#             self.main.maintenance_screen.update_hours_display(
#                 self.power_on_hours,
#                 self.total_operation_hours,
#                 self.cleaning_hours
#             )

#     # ====================== CONTROL DE TIMERS ======================

#     def start_operation_timer(self):
#         if not self.operation_start_time:
#             self.operation_start_time = QDateTime.currentDateTime()
#             logger.info("Operation timer iniciado")
#             self._save_operation_hours()

#     def pause_operation_timer(self):
#         self.operation_start_time = None
#         self._save_operation_hours()

#     def start_cleaning_timer(self):
#         if not self.cleaning_start_time:
#             self.cleaning_start_time = QDateTime.currentDateTime()
#             self._save_operation_hours()

#     def stop_cleaning_timer(self):
#         self.cleaning_start_time = None
#         self._save_cleaning_hours()

#     def get_hours_info(self):
#         return {
#             "power_on": self.power_on_hours,
#             "operation": self.total_operation_hours,
#             "cleaning": self.cleaning_hours,
#         }
#     # ====================== PERSISTENCIA ======================

#     def _load_all_hours(self):
#         self._load_power_on_hours()
#         self._load_operation_hours()
#         self._load_cleaning_hours()

#     def _save_all_hours(self):
#         self._save_power_on_hours()
#         self._save_operation_hours()
#         self._save_cleaning_hours()

#     def _load_power_on_hours(self):
#         try:
#             path = "config/power_on_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.power_on_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando power_on_hours: {e}")

#     def _save_power_on_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/power_on_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.power_on_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando power_on_hours: {e}")

#     def _load_operation_hours(self):
#         try:
#             path = "config/operation_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.total_operation_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando operation_hours: {e}")

#     def _save_operation_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/operation_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.total_operation_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando operation_hours: {e}")

#     def _load_cleaning_hours(self):
#         try:
#             path = "config/cleaning_hours.json"
#             if os.path.exists(path):
#                 with open(path, 'r') as f:
#                     data = json.load(f)
#                     self.cleaning_hours = data.get("hours", 0.0)
#         except Exception as e:
#             logger.warning(f"Error cargando cleaning_hours: {e}")

#     def _save_cleaning_hours(self):
#         try:
#             os.makedirs("config", exist_ok=True)
#             with open("config/cleaning_hours.json", 'w') as f:
#                 json.dump({"hours": round(self.cleaning_hours, 4)}, f)
#         except Exception as e:
#             logger.warning(f"Error guardando cleaning_hours: {e}")


#     def _load_hours(self, file_path: str, key: str) -> float:
#         try:
#             if os.path.exists(file_path):
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     return json.load(f).get(key, 0.0)
#         except Exception as e:
#             logger.error(f"Error cargando {file_path}: {e}")
#         return 0.0

#     def _save_hours(self, file_path: str, key: str, value: float):
#         try:
#             os.makedirs("config", exist_ok=True)
#             data = {key: round(value, 4), "last_update": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")}
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
#         except Exception as e:
#             logger.error(f"Error guardando {file_path}: {e}")

#     def _save_operation_hours(self):
#         self._save_hours("config/operation_hours.json", "total_operation_hours", self.total_operation_hours)

#     def _save_cleaning_hours(self):
#         self._save_hours("config/cleaning_hours.json", "cleaning_hours", self.cleaning_hours)

#     def _save_power_on_hours(self):
#         self._save_hours("config/power_on_hours.json", "power_on_hours", self.power_on_hours)


