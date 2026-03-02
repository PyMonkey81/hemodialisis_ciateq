
# # gui/appMainHemodialysis.py



import os
import sys
import time
import logging
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor, QPixmap
from utilities.csv_logger import CsvLogger

# === MODULES ===
from core.alarms import AlarmSystem
from core.variables_map import VARIABLES

from connection.serial_communication import SerialCommunication
from connection.led_bar_controller import LedBarController
from connection.bioz_urea_controller import BiozUreaController
from gui.therapy.main_screen import MainScreen
from gui.therapy.alarms_screen import AlarmsScreen
from gui.therapy.dialysis_screen import DialysisScreen
from gui.therapy.treatment_mode_screen import TreatmentModeScreen
from gui.service.options_screen import OptionsScreen
from gui.service.cleaning_screen import CleaningScreen
from gui.components.real_time_variables import RealTimeVariablesMonitor
from gui.components.tank_gauge import TankGauge
from gui.components.conductivity_bar import ConductivityBar

from gui.service.manual_mode_screen import ManualModeScreen
from gui.service.test_panel_screen import TestPanelScreen
from gui.service.calibration_screen import CalibrationScreen
from gui.service.network_config_screen import NetworkConfigScreen

from gui.therapy.patient_config_screen import PatientConfigScreen
from gui.therapy.therapy_config_screen import TherapyConfigScreen

logger = logging.getLogger(__name__)

#===============================================================================
#======================CODIGO PARA ADJUNTAR LOGOS EN EJECUTABLE=================
#===============================================================================
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)




   

class HemodialysisHMI(QMainWindow):
    # Screen indices
    INDEX_HOME = 0

    def __init__(self):
        super().__init__()
        self.csv_logger = None
        self.parameter_mapping = {            
            # "dialyLinePresProcessData":     "PT-3 (Presión Línea)",
            # "dialyPresIFProcessData":       "PT-4 (Presión IF)",
            # "dialyPresOFProcessData":       "PT-5 (Presión OF)",
            # "dialyLineWaterPresData":       "PT-6 (Presión Agua)",
            # "dialyBChamPresProcessData":    "PT-7 (Presión Cámara B)",
            # "bloodArteryPressureData":      "PT-8 (Presión Arteria Sanguínea)",
            # "bloodVenousPressureData":      "PT-9 (Presión Vena Sanguínea)",
            # "dialyPFilPmpPresProcessData":  "PT-10 (Presión Bomba Filtro)",
            # "CALC_PTM":                     "PTM", # Lo dejé como estaba, si es un valor calculado
            # "dialyCondVariableData":        "Conductividad",
            # "bloodSpeedVariableData":       "Flujo Sanguíneo",
            # "dialyFlowControlOutput":       "Flujo Dializado",
            # "dialyTempIFProcessData":       "Temperatura DI",
            # "dialyTempControlOutput":       "Temperatura Tanque",
            # "dialyTempControlSetPoint":     "Setpoint Temperatura",
            # "dialyCondControlSetPoint":     "Setpoint Conductividad",
            # "UF Total":                     "UF Total Acumulada",
            # "ultraFilterPumpSpeed":         "Tasa UF",
            # "heparineTherapyDosage":        "Dosis Heparina", # Ya tiene su propio display
            # "therapy_time":                 "Tiempo Terapia", # Corregido "theraphy"
            # "dialyTankHiLevelSwitch":       "Nivel Tanque Alto",
            # "dialyWaterInletValveButt":     "Válvula Entrada Agua",
            # "dialyDeaerChamLevSwitch":      "Cámara Desaireación",
            # "watterTankHeaterProtect":      "Protector Calefactor",
            # "airBubbleInBloodDetected":     "Burbuja en Sangre",
            # "bloodInDialyCircDetected":     "Sangre en Circuito Dial.",
            # "dialyPurgePumpStartButt":      "Purga Aire",
            "dialyLinePresProcessData": "PT-3",
            "dialyPresIFProcessData": "PT-4",
            "dialyPresOFProcessData": "PT-5",
            "dialyLineWaterPresData": "PT-6",
            "dialyBChamPresProcessData": "PT-7",
            "bloodArteryPressureData": "PT-8",
            "bloodVenousPressureData": "PT-9",
            "dialyPFilPmpPresProcessData": "PT-10",
            "dialyTempIFProcessData": "Temperatura EF",
            "dialyTempOFProcessData": "Temperatura SF",
            "dialyTempControlOutput": "Temperatura Tanque",
            "dialyCondControlSetPoint": "Setpoint Conductividad",
            "dialyCondControlOutput": "Salida Conductividad",
            "dialyTempControlSetPoint": "Setpoint Temperatura",
            "CAL_PTM": "Presión Transmembrana",
            "dialyTankHiLevelSwitch": "Nivel",
            "dialyWaterInletValveButt": "Valvula 27",
            "dialyDeaerChamLevSwitch": "C. Deareación",
            "watterTankHeaterProtect": "Protector Calefactor",
            "airBubbleInBloodDetected": "Aire en Sangre",
            "bloodInDialyCircDetected": "Sangre en dializante",
            "dialyPurgePumpStartButt": "Purga de aire",
        }
        # Control de tiempo de terapia (global)
        self.therapy_start_time = None
        self.total_therapy_seconds = 0
        self.is_treatment_running = False

        # Timer para actualizar tiempo cada segundo (en toda la app)
        self.therapy_time_timer = QTimer(self)
        self.therapy_time_timer.setInterval(1000)  # 1 segundo
        self.therapy_time_timer.timeout.connect(self._update_therapy_time_displays)

        # Timer para mediciones Kt/V cada 30 min
        self.ktv_timer = QTimer(self)
        self.ktv_timer.setInterval(30 * 60 * 1000)  # 30 minutos en ms
        self.ktv_timer.timeout.connect(self.perform_ktv_measurement)

        self.setup_ui()
        self.update_current_screen_label("Inicio", "#000000")
        self.setFixedSize(1920, 1080)
        self.setStyleSheet("background: #FCFCFC;")

        self.log_timer = QTimer(self)
        self.log_timer.setInterval(5000) # Registrar cada 5 segundos (5000 ms)
        self.log_timer.timeout.connect(self._log_current_data)

        # Serial communication
        self.current_values = {}
        self.serial_comm = SerialCommunication()
        self.serial_comm.data_received.connect(self.update_value)

        # lectura de sensores de bioimpedancia
        self.bioz_urea_controller = BiozUreaController()
        self.bioz_urea_controller.data_received.connect(self.update_value) 
        self.bioz_urea_controller.start()

        

        

        # Alarm system
        self.active_alarms = []
        display_names = [info["name"] for g in VARIABLES.values() for info in g.values()]
        tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]

        self.alarm_system = AlarmSystem(
            display_names=display_names,                     # ← cambiado de names=
            tags=tags,
            limits=[info.get("limites", (0.0, 100.0)) for g in VARIABLES.values() for info in g.values()],
            severity_levels=[info.get("nivel", "cyan") for g in VARIABLES.values() for info in g.values()],
            types=["numeric" if info["type"] == "double" else "boolean" for g in VARIABLES.values() for info in g.values()],
            boolean_triggers=[True] * len(tags)
        )
        self.buzzer_silenced_by_user = False

        # handle for alarms and start monitoring
        self.alarm_system.alarm_changed.connect(self.handle_alarm)
        self.alarm_system.new_event.connect(self.log_event)
        self.alarm_system.start_monitoring()

        self.current_values = {tag: 0.0 for tag in tags}

        # led bar 
        self.led_bar = LedBarController()
        self.led_bar.start()

        # Screens initialization
        self.alarms_screen = AlarmsScreen(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        self.real_time_var = RealTimeVariablesMonitor(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        # # Therapy & service screens        
        self.dialysis_screen = DialysisScreen(parent=self)
        self.treatment_mode_screen = TreatmentModeScreen(parent=self)  # ← revisar si debe ser distinta clase
        self.cleaning_screen = CleaningScreen(parent=self)
        self.options_screen = OptionsScreen(parent=self)
        
        # # Service sub-screens
        self.manual_mode_screen = ManualModeScreen(parent=self)
        self.test_panel_screen = TestPanelScreen(parent=self)
        self.calibration_screen = CalibrationScreen(parent=self)
        self.network_config_screen = NetworkConfigScreen(parent=self)
        

        # # Therapy sub-screens
        self.patient_config_screen = PatientConfigScreen(parent=self)
        self.therapy_config_screen = TherapyConfigScreen(parent=self)
     
        
        # Add all screens to stacked widget (order matters)
        self.screen_stack.addWidget(self._main_screen)                      # 0 - Home
        self.screen_stack.addWidget(self.dialysis_screen)              # 1   funciona
        self.screen_stack.addWidget(self.treatment_mode_screen)        # 2 funciona 
        self.screen_stack.addWidget(self.cleaning_screen)              # 3
        self.screen_stack.addWidget(self.options_screen)               # 4
        self.screen_stack.addWidget(self.alarms_screen)                # 5
        self.screen_stack.addWidget(self.manual_mode_screen)           # 6
        self.screen_stack.addWidget(self.test_panel_screen)            # 7
        self.screen_stack.addWidget(self.calibration_screen)           # 8
        self.screen_stack.addWidget(self.network_config_screen)        # 9
        self.screen_stack.addWidget(self.real_time_var)                # 10
        self.screen_stack.addWidget(self.patient_config_screen)        # 11
        self.screen_stack.addWidget(self.therapy_config_screen)        # 12

        # Header update timers
        self.refresh_alarms_label()
        self.update_connection_status()

        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self.update_connection_status)
        self.main_timer.start(500)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_date_time)
        self.clock_timer.start(1000)
        self.update_date_time()

        self.serial_comm.connect()
        self.serial_comm.start_reading()

        self.right_content.hide()
        self.left_content.hide()
        self.left_container.setStyleSheet("background: transparent")
        self.right_container.setStyleSheet("background: transparent")
    

        # Disable home buttons at startup
        if "Inicio" in self.navigation_buttons:
            self.navigation_buttons["Inicio"].setEnabled(False)
            self.navigation_buttons["Inicio"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
            self.navigation_buttons["Iniciar\nTratamiento"].setEnabled(False)
            self.navigation_buttons["Iniciar\nTratamiento"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")

   
    # ────────────────────────────────────────────────
    #                   UI Setup
    # ────────────────────────────────────────────────
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0) 

        self.main_layout.setColumnStretch(0,0) # COLUMNA 0 → IZQUIERDA
        self.main_layout.setColumnStretch(1,1) # COLUMNA 1 → STACKED + NAV (parte 1/4)
        self.main_layout.setColumnStretch(2,1) # COLUMNA 2 → STACKED + NAV (parte 2/4)
        self.main_layout.setColumnStretch(3,1) # COLUMNA 3 → STACKED + NAV (parte 3/4)
        self.main_layout.setColumnStretch(4,1) # COLUMNA 4 → STACKED + NAV (parte 4/4)
        self.main_layout.setColumnStretch(5,0) # COLUMNA 5 → DERECHA
        button_enabled_style ="""
            QPushButton { background: #39ec21; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """
        button_disabled_style = """background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px"""

        # =========================================================================================
        #                                    MAIN STACKED
        # =========================================================================================
        self.screen_stack = QStackedWidget()    
        self._main_screen = MainScreen()    
        self.screen_stack.addWidget(self._main_screen)
        self.main_layout.addWidget(self.screen_stack, 1, 1, 1, 4)
        #==========================================================================================
        # ============================ Header (1920 × 177) ========================================
        #==========================================================================================
        header_container = QWidget()
        header_container.setFixedHeight(150)
        header_container.setStyleSheet("background: #EBEBEB;")

        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(20)

        # Connection / alarm status
        self.status_label = QLabel("Conectado")
        self.status_label.setFixedSize(260, 80)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
               QLabel { background: #10b981; color: #ffffff; padding: 10px; border-radius: 12px;
                       font-weight: bold; font-size: 22px; }
        """)
        header_layout.addWidget(self.status_label)

        self.active_alarms_label = QLabel("Alarmas:")
        self.current_screen_label = QLabel("Inicio")
        self.current_process_status = QLabel("Iniciando máquina")
        self.date_time_label = QLabel("25/12/2025  14:37:22")

        for lbl in [self.active_alarms_label, self.current_screen_label, self.current_process_status, self.date_time_label]:
            lbl.setFixedSize(400, 80)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                QLabel { color: #0f172a; background: transparent;
                         font-weight: bold; font-size: 25px; }
            """)
            header_layout.addWidget(lbl)

        header_layout.addStretch()

        # Logos
        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo1)

        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("resources/images/Logo_secihti_.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo2)

        self.main_layout.addWidget(header_container, 0, 0, 1, 6)

        # ==================================================================== 
        #                  GAUGES IZQUIERDA (PA + PV) 
        # ====================================================================
        self.left_container = QWidget()  #CONTENEDOR FIJO SIEMPRE VISIBLE
        self.left_container.setFixedSize(180, 903)
        left_layout_outer = QVBoxLayout(self.left_container)
        left_layout_outer.setContentsMargins(0, 0, 0, 0)

        self.left_content = QWidget() # CONTENEDOR DE WIDGETS
        self.left_content.setFixedSize(180, 903)
        left_inner_layout = QVBoxLayout(self.left_content)
        left_inner_layout.setContentsMargins(0, 0, 0, 0)
        left_inner_layout.setSpacing(0)

        self.arterial_pressure_gauge = TankGauge("Art", -100, 400, "mmHg", "#dc2626")
        self.venous_pressure_gauge   = TankGauge("Ven",  -50, 400, "mmHg", "#1640f9")
        self.arterial_pressure_gauge.setFixedSize(180, 451)
        self.venous_pressure_gauge.setFixedSize(180, 452)
        left_inner_layout.addWidget(self.arterial_pressure_gauge)
        left_inner_layout.addWidget(self.venous_pressure_gauge)

        left_layout_outer.addWidget(self.left_content)
        self.main_layout.addWidget(self.left_container, 1, 0, 2, 1)
        #=========================================================================================
        # ===================== Right gauges (Temp + Conductivity) ===============================
        #=========================================================================================
        self.right_container = QWidget() # CONTENEDOR DERECHO FIJO 
        self.right_container.setFixedSize(180, 903)
        right_outer_layout = QVBoxLayout(self.right_container)
        right_outer_layout.setContentsMargins(0, 0, 0, 0)

        self.right_content = QWidget() # CONTENEDOR DE WIDGETS 
        self.right_content.setFixedSize(180, 903)
        right_inner_layout = QVBoxLayout(self.right_content)
        right_inner_layout.setContentsMargins(0, 0, 0, 0)
        right_inner_layout.setSpacing(0)

        self.dialysate_temp_gauge = TankGauge("Temp.\nDial", 0, 50, "°C", "#A31A1A")
        self.conductivity_bar = ConductivityBar()

        self.dialysate_temp_gauge.setFixedWidth(180)
        self.conductivity_bar.setFixedWidth(180)

        right_inner_layout.addWidget(self.dialysate_temp_gauge, 1)
        right_inner_layout.addWidget(self.conductivity_bar, 1)

        right_outer_layout.addWidget(self.right_content)
        self.main_layout.addWidget(self.right_container, 1, 5, 2, 1)

        # ── Bottom navigation bar ────────────────────────
        nav_bar = QWidget()
        # nav_bar.setFixedSize(1536, 177)
        nav_bar.setFixedSize(1560, 150)
        nav_bar.setStyleSheet("background: #FCFCFC;")

        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        nav_layout.setSpacing(10)

        self.navigation_buttons = {}

        nav_items = [
            ("Inicio",              "#0f172a", self.show_home_screen),
            ("Diálisis",            "#0f172a", self.show_dialysis_screen),
            ("Tipo de\nTratamiento","#0f172a", self.show_treatment_mode_screen),   # antes "Tipo de Tratamiento"
            ("Iniciar\nTratamiento", "#39ec21", self.start_treatment),
            ("Limpieza",            "#0f172a", self.show_cleaning_screen),
            ("Configuración", "#0f172a", self.show_options_screen),
            ("Alarmas",             "#0f172a", self.show_alarms_screen),
            ("Salir",               "#dc2626", self.close),
        ]

        for text, color, callback in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(110)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                               font-size: 24px; border-radius: 10px; }}
                QPushButton:pressed {{ background: #334155; }}
            """)            
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self.navigation_buttons[text] = btn

        self.main_layout.addWidget(nav_bar, 2, 1, 1, 4)

    # ────────────────────────────────────────────────
    #              Navigation Methods
    # ────────────────────────────────────────────────
    def start_treatment(self):
        logger.info("Iniciando tratamiento y mediciones externas: Bioimpedancia")
        # Verificar que haya duración configurada
        # Leer duración desde current_values (viene de therapy_config)
        hours = int(self.current_values.get("heparineTherapyHours", 0))
        minutes = int(self.current_values.get("heparineTherapyMinutes", 0))
        self.total_therapy_seconds = (hours * 3600) + (minutes * 60)

        if self.total_therapy_seconds <= 0:
            QMessageBox.warning(self, "Configuración incompleta", 
                                "Configure la duración de la terapia primero.")
            self.show_therapy_config_screen()
            return

        # Guardar inicio y activar estado
        self.therapy_start_time = QDateTime.currentDateTime()
        self.is_treatment_running = True

        # Iniciar timer de actualización (si no está corriendo)
        if not self.therapy_time_timer.isActive():
            self.therapy_time_timer.start()

        # Iniciar bioimpedancia y Kt/V
        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("SRTB")
    
        
        self.perform_ktv_measurement()  # Primera medición inmediata
        
        if not self.ktv_timer.isActive():
            self.ktv_timer.start()

        # Feedback
        QMessageBox.information(self, "Tratamiento Iniciado", 
                                f"Sesión iniciada por {hours:02d}:{minutes:02d}")

        # Actualizar pantalla de diálisis (si está visible)
        if self.screen_stack.currentWidget() == self.dialysis_screen:
            self.dialysis_screen.update_values(self.current_values)

    def start_priming(self):
        """
        Inicia el proceso de cebado (priming / enjuague).
        - Verifica conexión serial
        - Cierra logger anterior si existe
        - Inicia nuevo logging CSV
        - Envía comandos booleanos al controlador
        - Muestra feedback al usuario
        """
        # 1. Verificar conexión serial (obligatorio)
        if not self.serial_comm or not self.serial_comm.is_connected:
            QMessageBox.warning(self, "Error de conexión", 
                                "No hay conexión con el controlador.\n"
                                "No se puede iniciar el cebado.")
            logger.warning("Intento de iniciar cebado sin conexión serial")
            return

        # 2. Cerrar logger anterior si ya existe (evita duplicados/corrupción)
        if self.csv_logger:
            logger.info("Cerrando logger anterior antes de nuevo cebado")
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None

        # 3. Definir directorio de logs (puedes cambiar la ruta si quieres)
        LOG_DIRECTORY = "logs/hemodialysis"  # Se crea automáticamente si no existe

        # 4. Crear e iniciar el nuevo logger CSV
        try:
            self.csv_logger = CsvLogger(
                log_directory=LOG_DIRECTORY,
                parameter_key_map=self.parameter_mapping
            )
            self.log_timer.start()
            logger.info("Logger CSV iniciado correctamente para cebado")
        except Exception as e:
            logger.error(f"Error al crear logger CSV para cebado: {e}")
            QMessageBox.critical(self, "Error crítico", 
                                 f"No se pudo iniciar el registro de datos:\n{str(e)}")
            return

        # 5. Enviar comandos al controlador
        try:
            self._write_boolean_command("dialyStartDialysisButt", True)
            self._write_boolean_command("dialyStopDialysisButt", False)
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}")
            QMessageBox.warning(self, "Advertencia", 
                                "Cebado iniciado, pero hubo problema al enviar comandos al controlador.")

        # 6. Feedback claro al usuario (muy importante en equipo médico)
        QMessageBox.information(self, "Cebado Iniciado",
                                "Proceso de cebado iniciado correctamente.\n\n"
                                "• Registro de datos activo en logs/hemodialysis/\n"
                                "• Duración típica: 5–10 minutos\n"
                                "Presione 'DETENER' cuando finalice o espere condición automática.")

        # 7. Cambiar a pantalla de diálisis para monitorear presiones, etc.
        self.show_dialysis_screen()


    def stop_treatment(self):   
        self._write_boolean_command("dialyStartDialysisButt", False)
        self._write_boolean_command("dialyStopDialysisButt", True)

        # if self.ktv_timer.isActive():
        #     self.ktv_timer.stop()
        #     logger.info("[kt/V] Medición detenida")

        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("STOP")

        # Resetear estado de tiempo

        self.is_treatment_running = False
        self.therapy_start_time = None
        self.total_therapy_seconds = 0

        # Detener timer de actualización si no hay tratamiento
        if hasattr(self, 'therapy_time_timer') and self.therapy_time_timer.isActive():
            self.therapy_time_timer.stop()

        # Actualizar displays inmediatamente
        self._update_therapy_time_displays()

        # Cerrar logger si existe
        if self.csv_logger:
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")

    def end_dialysis_session(self):
        if self.csv_logger:
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")
        

    def show_home_screen(self):
        self.screen_stack.setCurrentIndex(self.INDEX_HOME)
        self.update_current_screen_label("Inicio", "#0A0A0A")
        self.right_content.hide()
        self.left_content.hide()


    def show_dialysis_screen(self):
        self.screen_stack.setCurrentWidget(self.dialysis_screen)
        if hasattr(self.dialysis_screen, "update_values"):
            self.dialysis_screen.update_values(self.current_values)
        self.update_current_screen_label("Diálisis", "#0f172a")
        self.left_content.show()
        self.right_content.show()
        self.navigation_buttons["Inicio"].setEnabled(True)
        self.navigation_buttons["Inicio"].setStyleSheet("""
            QPushButton { background: #1b10b9; color: #ffffff; font-weight: bold;
                          font-size: 24px; border-radius: 10px;}
            QPushButton:pressed { background: #334155;}
        """)

    def show_treatment_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.treatment_mode_screen)
        self.update_current_screen_label("Modo de\n Tratamiento", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_cleaning_screen(self):
        self.screen_stack.setCurrentWidget(self.cleaning_screen)
        if hasattr(self.cleaning_screen, "update_values"):
            self.cleaning_screen.update_values(self.current_values)
        self.update_current_screen_label("Limpieza", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_options_screen(self):
        self.screen_stack.setCurrentWidget(self.options_screen)
        self.update_current_screen_label("Configuración", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_alarms_screen(self):
        self.screen_stack.setCurrentWidget(self.alarms_screen)
        self.update_current_screen_label("Alarmas", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_manual_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.manual_mode_screen)
        if hasattr(self.manual_mode_screen, "update_values"):
            self.manual_mode_screen.update_values(self.current_values)
        self.update_current_screen_label("Modo Manual", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_test_panel_screen(self):
        self.screen_stack.setCurrentWidget(self.test_panel_screen)
        if hasattr(self.test_panel_screen, "update_values"):
            self.test_panel_screen.update_values(self.current_values)
        self.update_current_screen_label("Panel de Pruebas", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_calibration_screen(self):
        self.screen_stack.setCurrentWidget(self.calibration_screen)
        if hasattr(self.calibration_screen, "update_values"):
            self.calibration_screen.update_values(self.current_values)
        self.update_current_screen_label("Calibración", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_network_config_screen(self):
        self.screen_stack.setCurrentWidget(self.network_config_screen)
        self.update_current_screen_label("Configuración de Red", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_real_time_var_screen(self):
        self.screen_stack.setCurrentWidget(self.real_time_var)
        self.update_current_screen_label("Monitor de Variables", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_patient_config_screen(self):
        self.screen_stack.setCurrentWidget(self.patient_config_screen)
        if hasattr(self.patient_config_screen, "update_values"):
            self.patient_config_screen.update_values(self.current_values)
        self.update_current_screen_label("Paciente", "#0f172a")
        self.left_content.show()
        self.right_content.show()

    def show_therapy_config_screen(self):
        self.screen_stack.setCurrentWidget(self.therapy_config_screen)
        if hasattr(self.therapy_config_screen, "update_values"):
            self.therapy_config_screen.update_values(self.current_values)
        self.update_current_screen_label("Terapia", "#0f172a")
        self.left_content.show()
        self.right_content.show()


    
  
        
        
        

    # ────────────────────────────────────────────────
    #              Utility Methods
    # ────────────────────────────────────────────────
    def update_current_screen_label(self, text, text_color="#0f172a"):
        self.current_screen_label.setText(text)
        self.current_screen_label.setStyleSheet(
            f"color: {text_color}; background: transparent; font-weight: bold; font-size: 30px;"
        )

    def update_date_time(self):
        from datetime import datetime
        self.date_time_label.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

    def update_value(self, tag: str, value: float):
        button_enabled_style ="""
            QPushButton { background: #39ec21; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """
        button_disabled_style = """background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px"""

        self.current_values[tag] = value

        if self.alarm_system:
            self.alarm_system.update_value_by_tag(tag, value)


        if tag == "urea_adc2":
            self.measurement_ktv()

        gauge_mapping = {
            "arterPresProcessData":   self.arterial_pressure_gauge,
            "venouPresProcessData":   self.venous_pressure_gauge,
            "dialyTempVariableData":  self.dialysate_temp_gauge,
            "dialyCondVariableData":  self.conductivity_bar,
        }  

        if tag in gauge_mapping:
            gauge_mapping[tag].setValue(value)

        
        if tag == "primingProcessStatus":
            status_code = int (value)

            status_map = {
                1: "INICIO CEBADO",
                2: "LLENADO DE TANQUE",
                3: "LLENADO DE LINEA",
                4: "LLENADO CÁMARA",
                5: "CALENTAMIENTO",
                6: "INFUSIÓN",
                7: "DIÁLISIS",
                8: "BYPASS",
                9: "CERRADO",
                11: "ULTRAFILTRACIÓN OFF",
                12: "LISTO",
                13: "TRATAMIENTO INICIADO",
                14: "PAUSA",
                15: "TRATAMIENTO DETENIDO"
            }
        
            # Obtener texto, por defecto "DESCONOCIDO" si no está en la lista
            status_text = status_map.get(status_code, "ESTADO DESCONOCIDO")
            self.current_process_status.setText(status_text)
            if status_code == 7: # DIÁLISIS
                color = "#25AD37" # Verde
            elif status_code in [1, 2, 3, 4, 5]: # Preparación
                color = "#eab308" # Amarillo/Naranja
            else:
                color = "#0f172a" # Azul oscuro por defecto
                
            self.current_process_status.setStyleSheet(f"""
                QLabel {{ color: {color}; background: transparent;
                         font-weight: bold; font-size: 25px; }}
            """)

            if "Iniciar\nTratamiento" in self.navigation_buttons:
                self.navigation_buttons["Iniciar\nTratamiento"].setEnabled(True)
            else:
                self.navigation_buttons["Iniciar\nTratamiento"].setEnabled(False)
                self.navigation_buttons["Iniciar\nTratamiento"].setStyleSheet(button_disabled_style)

            if self.dialysis_screen:
                self.dialysis_screen.update_buttons_state(status_code)

            if self.cleaning_screen:
                self.cleaning_screen.update_buttons_state(status_code)


    def refresh_alarms_label(self):
        if not self.active_alarms:
            self.active_alarms_label.setText("")
            self.active_alarms_label.setStyleSheet("""
                QLabel { color: #ffffff; background: transparent;
                         font-weight: bold; font-size: 25px; }
            """)
        else:
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            name, value, level = top_alarm

            display_text = name.upper()
            if value is not None:
                display_text += f" {value:.1f}"

            color_map = {
                "rojo":    "#dc2626",
                "naranja": "#f97316",
                "amarillo":"#eab308",
                "cian":    "#06b6d4"
            }
            bg_color = color_map.get(level, "#1e293b")

            self.active_alarms_label.setText(display_text)
            self.active_alarms_label.setStyleSheet(f"""
                QLabel {{ background: {bg_color}; color: #ffffff; padding: 10px;
                          border-radius: 12px; font-weight: bold; font-size: 20px; }}
            """)

    def handle_alarm(self, idx, active, value, name, level, limit):
        was_active = name in [a[0] for a in self.active_alarms]
        if active:
            if name not in [a[0] for a in self.active_alarms]:
                self.active_alarms.append((name, value, level))
                self.buzzer_silenced_by_user = False
        else:
            self.active_alarms = [a for a in self.active_alarms if a[0] != name]
            self.active_alarms = [a for a in self.active_alarms if a[0] != name]
            if not self.active_alarms:
                self.buzzer_silenced_by_user = False

        self.refresh_alarms_label()
        self.update_connection_status()
        self.update_led_bar_state()

    # ────────────────────────────────────────────────
    #              LED Bar Logic
    # ────────────────────────────────────────────────

    def update_led_bar_state(self):
        """Determina LED + estado del buzzer según prioridad y si el usuario silenció."""
        if not self.serial_comm or not self.serial_comm.is_connected:
            self.led_bar.send_state(self.led_bar.CMD_CYAN_SOLID, silence_buzzer=False)
            return

        if self.active_alarms:
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            level = top_alarm[2]

            if level == "rojo":
                cmd = self.led_bar.CMD_RED_SOLID
            elif level == "naranja":
                cmd = self.led_bar.CMD_YELLOW_FLASH
            elif level == "amarillo":
                cmd = self.led_bar.CMD_YELLOW_SOLID
            elif level == "cian":
                cmd = self.led_bar.CMD_CYAN_SOLID
            else:
                cmd = self.led_bar.CMD_GREEN_SOLID

            # ← flag del usuario
            silence = self.buzzer_silenced_by_user
            self.led_bar.send_state(cmd, silence_buzzer=silence)
        else:
            self.led_bar.send_state(self.led_bar.CMD_GREEN_SOLID, silence_buzzer=False)

    
    def perform_ktv_measurement(self):
        """
        Ejecuta la secuencia de lectura para Bioimpedancia y Urea.
        Se llama al inicio del tratamiento y luego cada 30 minutos.
        """
        if not hasattr(self, 'bioz_urea_controller') or not self.bioz_urea_controller:
            logger.warning("Controlador BioZ/Urea no disponible, omitiendo medición Kt/V")
            return

        logger.info("[Kt/V] Iniciando ciclo de medición automático...")
        
        self.bioz_urea_controller.send_command("SRTB")# 1. Enviar comando de Bioimpedancia
        
        # 2. Programar la lectura de Urea unos segundos después
        # Damos 5 segundos para que la BioZ termine o se estabilice antes de pedir Urea
        
        QTimer.singleShot(5000, lambda: self.bioz_urea_controller.send_command("SRTU"))


    def measurement_ktv(self):
        urea = self.current_values.get("urea_adc1", 0) # O el algoritmo que usen para convertir ADC a concentración
        # bioz = self.current_values.get("bioz_resistance", 0)
        
        # ... Fórmula del Kt/V (Daugirdas u otra) ...
        # ktv = ...
        
        # Guardar/Mostrar resultado
        # self.current_values["ktv_calculado"] = ktv
        # logger.info(f"Nuevo cálculo Kt/V: {ktv}")


    def update_connection_status(self):
        if not hasattr(self, 'serial_comm') or not self.serial_comm or not self.serial_comm.is_connected:
            text, color = "RECONECTANDO...", "#f97316"            
        elif self.active_alarms:
            text = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            text, color = "CONECTADO", "#10b981"

        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{ background: {color}; color: #ffffff; padding: 10px;
                      border-radius: 12px; font-weight: bold; font-size: 22px; }}
        """)

        current_widget = self.screen_stack.currentWidget()
        if hasattr(current_widget, "update_values"):
            current_widget.update_values(self.current_values)

        self.update_led_bar_state()

    def log_event(self, event, value, timestamp):
        logger.error(f"[EVENT] {timestamp} → {event}")

    def __del__(self):
        logger.error("[INFO] Destructor called → stopping threads...")
        self.shutdown()

    def shutdown(self):
        logger.error("[INFO] Initiating controlled shutdown.")

        # Stop timers
        if hasattr(self, 'main_timer') and isinstance(self.main_timer, QTimer) and self.main_timer.isActive():
            self.main_timer.stop()
            logger.error("[INFO] Timer principal detenido.")
        if hasattr(self, 'clock_timer') and isinstance(self.clock_timer,QTimer) and self.clock_timer.isActive():
            self.clock_timer.stop()
            logger.error("[INFO] Timer reloj detenido")

        # Stop alarm system
        if hasattr(self, 'alarm_system') and self.alarm_system:
            try:
                self.alarm_system.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop alarm system cleanly: {e}")
            self.alarm_system = None

        # Stop serial communication (most critical I/O)
        if hasattr(self, 'serial_comm') and self.serial_comm:
            try:
                self.serial_comm.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop serial communication: {e}")
            self.serial_comm = None
        
        if hasattr(self, 'led_bar') and self.led_bar:
            try:
                # Enviar comando de apagado al Arduino modificado
                self.led_bar.send_state(self.led_bar.CMD_OFF, silence_buzzer=True) 
                time.sleep(0.1) # Breve espera para asegurar que el comando salga
                self.led_bar.stop()
            except Exception as e:
                logger.error(f"Error stopping LED bar: {e}")

        if hasattr(self, 'bioz_urea_controller') and self.bioz_urea_controller:
            try:
                self.bioz_urea_controller.stop()
            except Exception as e:
                logger.error(f"Error deteniendo el controlador de BioZ/Urea: {e}")
        

        if hasattr(self, 'ktv_timer') and self.ktv_timer.isActive():
            self.ktv_timer.stop()
        

        time.sleep(0.1)
        logger.error("[INFO] Controlled shutdown completed.")

    def _log_current_data(self):
        """
        Método slot llamado por el QTimer para registrar los datos actuales.
        """
        if self.csv_logger:
            self.csv_logger.log_data(self.current_values)


    def _write_boolean_command(self, tag: str, state: bool):
        """
        Envía un comando booleano (True/False) al controlador vía serial.
        """
        if not self.serial_comm or not self.serial_comm.is_connected:
            logger.warning(f"No se puede enviar comando booleano '{tag} = {state}': serial no conectado")
            # Opcional: QMessageBox.warning(self, "Error", "Serial no conectado")
            return

        try:
            logger.debug(f"Buscando tag booleano: {tag} = {state}")

            address = -1
            for group_key, vars_group in VARIABLES.items():
                if isinstance(vars_group, dict):
                    for var_id, info in vars_group.items():
                        if info.get("tag") == tag:
                            address = var_id
                            break
                if address != -1:
                    break

            if address == -1:
                logger.error(f"Tag booleano '{tag}' no encontrado en VARIABLES")
                return

            # Envío real
            self.serial_comm.write_boolean(address, state)
            logger.info(f"Comando booleano enviado: {tag} = {state} (Address {address})")

        except Exception as e:
            logger.error(f"Error al enviar comando booleano '{tag} = {state}': {e}")

    def _write_setpoint(self, tag: str, value: float):
        """
        Envía un setpoint (double) al controlador vía serial.
        """
        if not self.serial_comm or not self.serial_comm.is_connected:
            logger.warning(f"No se puede escribir setpoint '{tag} = {value}': serial no conectado")
            return  # Opcional: mostrar QMessageBox si quieres feedback visual

        try:
            logger.debug(f"Buscando tag para escritura: {tag} = {value}")

            target_group = target_id = -1
            found = False

            for group_key, vars_group in VARIABLES.items():
                if isinstance(vars_group, dict):
                    for var_id, info in vars_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found:
                    break

            if not found or target_group == -1 or target_id == -1:
                logger.error(f"Tag '{tag}' no encontrado en VARIABLES")
                return

            if not VARIABLES[target_group][target_id].get("rw", False):
                logger.warning(f"Tag '{tag}' es de solo lectura (rw=False)")
                return

            # Envío real
            self.serial_comm.write_double(target_group, target_id, value)
            logger.info(f"Setpoint escrito correctamente: {tag} = {value} (Grupo {hex(target_group)}, ID {target_id})")

        except Exception as e:
            logger.error(f"Error al escribir setpoint '{tag} = {value}': {e}")

    def closeEvent(self, event):
        self.end_dialysis_session() # Llama a la función que cierra el logger
        super().closeEvent(event)
        logger.error("[INFO] closeEvent → performing shutdown...")
        self.shutdown()
        time.sleep(1.0)  # Give OS time to release resources
        event.accept()
        QApplication.quit()


# gui/appMainHemodialisis.py

# import os
# import sys
# import time
# import logging
# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtGui import QColor, QPixmap

# # === MÓDULOS ===
# from core.alarmas import SistemaAlarmas
# from core.variables_map import VARIABLES

# from connection.comunicacion_serial import ComunicacionSerial
# from gui.therapy.main_screen import mainScr
# from gui.therapy.dialysis_screen import dialysisScr
# from gui.service.options_screen import optionScr
# from gui.service.cleaning_screen import cleanScr
# from gui.therapy.alarms_screen import alarmsScr
# from gui.components.real_time_variables import monitorVariables
# from gui.components.tank_gauge import TankGauge
# from gui.components.conductivity_bar import ConductivityBar


# from gui.service.manual_mode_screen import mManualScr #Pantalla modo manual 
# from gui.service.test_panel_screen import testScr #Pantalla panel de pruebas 
# from gui.service.calibration_screen import ctrlCfgScr #pantalla calibracion
# from gui.service.network_config_screen import cfgRedScr # pantalla configuracion de red

# from gui.therapy.patient_config_screen import patienCfgScr
# from gui.therapy.therapy_config_screen import therapyCfgScr

# logger = logging.getLogger(__name__)

# #===============================================================================
# #======================CODIGO PARA ADJUNTAR LOGOS EN EJECUTABLE=================
# #===============================================================================

# def resource_path(relative_path):
#     """Devuelve la ruta correcta tanto en desarrollo como en .exe"""
#     try:
#         # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)
# #===============================================================================


# class HemodialysisHMI(QMainWindow):
#     #INDEX DE PANTALLAS 
#     INDEX_INICIO = 0   

#     def __init__(self):
#         super().__init__()

#         # === DETECCIÓN DE ENTORNO DE PRUEBAS ===
#         # import os
#         # en_pruebas = os.getenv('PYTEST_VERSION') or 'pytest' in sys.modules
    
#         # if en_pruebas:
#         #     logger.error("[INFO] Modo pruebas detectado → puerto serial desactivado")
#         #     self.serial = None
#         #     self.conectado = False
#         # else:
#         #     self.serial = ComunicacionSerial(callback=self.actualizar_valor)
#         #     self.conectado = self.serial.conectar()
#         #     if self.conectado:
#         #         self.serial.iniciar_lectura()
       
#         # 1. Crear estructura visual (ventana, label y stacked)
#         self.setup_ui()
#         self.actualizar_label_pantalla("Inicio", "#000000")     # <-------------cambio de color para en un futuro hacer temas 
#         self.setFixedSize(1920, 1080) # Tamaño resolución de monitor
#         self.setStyleSheet("background: #FCFCFC ;") ##090c33          <--------------------------- para consideracion de temas de colores 

#         # 2. Iniciar comunicación serial
#         #  === COMUNICACIÓN SERIAL ===    
#         self.valores = {}           
#         self.serial = ComunicacionSerial()
#         self.serial.data_received.connect(self.actualizar_valor)
#         # self.serial.conectar()
        
       

#         # # 3. Crear pantallas 

#         self.alarmas_activas = []      
#         nombres = [info["name"] for g in VARIABLES.values() for info in g.values()]
#         tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]
#         self.sistema_alarmas = SistemaAlarmas(
#             nombres=nombres,
#             tags=tags,
#             limites=[info.get("limites", (0, 100)) for g in VARIABLES.values() for info in g.values()],
#             niveles=[info.get("nivel", "cian") for g in VARIABLES.values() for info in g.values()],
#             tipos=["numerico" if info["type"] == "double" else "booleano" for g in VARIABLES.values() for info in g.values()],
#             trigger_booleano=[True] * len(tags)
#         )
     
#         # conecta las señales de alarma   
#         self.sistema_alarmas.cambio_alarma.connect(self.manejar_alarma)
#         self.sistema_alarmas.nuevo_evento.connect(self.registrar_evento)
#         self.sistema_alarmas.iniciar_monitoreo()
#         self.valores = {n: 0.0 for n in tags}   

#         self.pantalla_alarmas     = alarmsScr(
#             parent=self,
#             valores_dict=self.valores,          # opcional, pero ya lo tienes
#             sistema_alarmas=self.sistema_alarmas
#         )        
#         # Monitor de variables (también necesita sistema_alarmas)
#         self.pantalla_monitor_variables = monitorVariables(
#             parent=self,
#             valores_dict=self.valores,
#             sistema_alarmas=self.sistema_alarmas
#         )        


#          # 4. Crear pantallas (en orden lógico)
#         self.dialysis_scr    = dialysisScr(parent=self)
#         self.pantalla_modo_       = dialysisScr(parent=self)  # ← considera renombrar esta clase
#         self.pantalla_limpieza    = cleanScr(parent=self)
#         self.pantalla_ajustes     = optionScr(parent=self)
#         # Submenús de ajustes
#         self.pantalla_modo_manual   = mManualScr(parent=self)
#         self.pantalla_panel_pruebas = testScr(parent=self)
#         self.pantalla_calibracion   = ctrlCfgScr(parent=self)
#         self.pantalla_config_red    = cfgRedScr(parent=self)

#         # Submenu de dialisis 
#         self.pantalla_paciente = patienCfgScr(parent=self)
#         self.pantalla_configuracion_terapia = therapyCfgScr(parent=self)

#         # 5. Añadir TODAS al stacked (en el orden deseado)
#         self.stacked.addWidget(mainScr())                    # 0
#         self.stacked.addWidget(self.dialysis_scr)       # 1
#         self.stacked.addWidget(self.pantalla_modo_)          # 2
#         self.stacked.addWidget(self.pantalla_limpieza)       # 3
#         self.stacked.addWidget(self.pantalla_ajustes)        # 4
#         self.stacked.addWidget(self.pantalla_alarmas)        # 5  ← ahora sí está la correcta
#         self.stacked.addWidget(self.pantalla_modo_manual)    # 6
#         self.stacked.addWidget(self.pantalla_panel_pruebas)  # 7
#         self.stacked.addWidget(self.pantalla_calibracion)    # 8
#         self.stacked.addWidget(self.pantalla_config_red)     # 9
       
#         self.stacked.addWidget(self.pantalla_monitor_variables) # 10
#         self.stacked.addWidget(self.pantalla_paciente)       # 11
#         self.stacked.addWidget(self.pantalla_configuracion_terapia) 
        

        
#         # 7. Iniciar timers y metodos de actualizacion de etiquedas en header
#         self.refrescar_etiqueta_alarmas()
#         self.actualizar_estado()
        
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.actualizar_estado)
#         self.timer.start(500)

#         self.timer_reloj = QTimer(self)
#         self.timer_reloj.timeout.connect(self.actualizar_fecha_hora)
#         self.timer_reloj.start(1000)
#         self.actualizar_fecha_hora()    

#         self.serial.conectar()
#         self.serial.iniciar_lectura()  

#         self.left.hide()
#         self.right.hide()
#         #contenedores vacios para el inicio de la app
#         self.container_right.setStyleSheet("background: transparent")
#         self.container_left.setStyleSheet("background: transparent")

#         if "Inicio" in self.botones_nav: # DESACTIVACION DE BOTONES AL UNICIO DE LA APLICACIÓN.
#             self.botones_nav["Inicio"].setEnabled(False)
#             self.botones_nav["Inicio"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
#             self.botones_nav["Inicio\nTratamiento"].setEnabled(False)
#             self.botones_nav["Inicio\nTratamiento"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
        
#     #  === PANTALLAS ===
#     def pantalla_principal(self):
#         return mainScr()
    
#     # === SETUP UI ===
#     def setup_ui(self):
#         central = QWidget()
#         self.setCentralWidget(central)
#         self.layout = QGridLayout(central)
#         self.layout.setSpacing(0)
#         self.layout.setContentsMargins(0, 0, 0, 0)

#         self.layout.setColumnStretch(0,0) # COLUMNA 0 → IZQUIERDA
#         self.layout.setColumnStretch(1,1) # COLUMNA 1 → STACKED + NAV (parte 1/4)
#         self.layout.setColumnStretch(2,1) # COLUMNA 2 → STACKED + NAV (parte 2/4)
#         self.layout.setColumnStretch(3,1) # COLUMNA 3 → STACKED + NAV (parte 3/4)
#         self.layout.setColumnStretch(4,1) # COLUMNA 4 → STACKED + NAV (parte 4/4)
#         self.layout.setColumnStretch(5,0) # COLUMNA 5 → DERECHA


#         # =========================================================================================
#         #                                    MAIN STACKED
#         # =========================================================================================
       
#         self.stacked = QStackedWidget()
#         # self.stacked.setFixedSize(1536, 726)
#         self.stacked.addWidget(self.pantalla_principal())
       
#         self.layout.addWidget(self.stacked, 1, 1, 1, 4)

#         #================================================================
#         # =========================== HEADER 1920x177 ===================
#         #================================================================       
#         header_container = QWidget()
#         header_container.setFixedHeight(177)
#         header_container.setStyleSheet("background: #EBEBEB;") 

#         header = QHBoxLayout(header_container)
#         header.setContentsMargins(30, 20, 30, 20)
#         header.setSpacing(20)

        

#         # ESTADO (la única con fondo)       
#         self.lbl_estado = QLabel("Conectado")
#         self.lbl_estado.setFixedSize(260, 80)
#         self.lbl_estado.setAlignment(Qt.AlignCenter)
#         self.lbl_estado.setStyleSheet("""
#               QLabel { background: #10b981; color: #ffffff; padding: 10px; border-radius: 12px;
#                       font-weight: bold; font-size: 22px; }
#         """)
#         header.addWidget(self.lbl_estado)
        
#         self.lbl_alarmas = QLabel("Alarmas:")
#         self.lbl_pantalla_actual = QLabel("Inicio")
#         self.lbl_fecha_hora = QLabel("25/12/2025  14:37:22")
#         # Especifica el tamaño de la etiqueta, alineacion, color de letra, etc. y lo agrega al widget
#         for lbl in [self.lbl_alarmas, self.lbl_pantalla_actual, self.lbl_fecha_hora]:
#             lbl.setFixedSize(400, 80)
#             lbl.setAlignment(Qt.AlignCenter)
#             lbl.setStyleSheet("""
#                 QLabel { color: #0f172a; background: transparent;
#                         font-weight: bold; font-size: 25px; }
#             """)
#             header.addWidget(lbl)

#         header.addStretch()    

#         logo1 = QLabel()
#         logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
#         header.addWidget(logo1)
#         logo2 = QLabel()
#         logo2.setPixmap(QPixmap(resource_path("resources/images/Logo_secihti_.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
#         header.addWidget(logo2)
#         self.layout.addWidget(header_container, 0, 0, 1, 6) #


#         # ==================================================================== 
#         #                  GAUGES IZQUIERDA (PA + PV) 
#         # ====================================================================
#         self.container_left = QWidget() # CONTENEDOR FIJO SIEMPRE VISIBLE
#         self.container_left.setFixedSize(192, 903)
#         layout_cont_left = QVBoxLayout(self.container_left)
#         layout_cont_left.setContentsMargins(0, 0, 0, 0)

#         self.left = QWidget() # CONTENEDOR DE WIDGETS 
#         self.left.setFixedSize(192, 903)
#         left_layout = QVBoxLayout(self.left)
#         left_layout.setContentsMargins(0, 0, 0, 0)
#         left_layout.setSpacing(0)

#         self.gauge_art = TankGauge("Art", -100, 400, "mmHg", "#dc2626")
#         self.gauge_ven = TankGauge("Ven", -50, 400, "mmHg", "#1640f9")

#         self.gauge_art.setFixedSize(192, 451)
#         self.gauge_ven.setFixedSize(192, 452)

#         left_layout.addWidget(self.gauge_art)
#         left_layout.addWidget(self.gauge_ven)

#         layout_cont_left.addWidget(self.left)

#         self.layout.addWidget(self.container_left, 1, 0, 2, 1)      

        
#         # ==================================================================================
#         #                            GAUGE DERECHA (TEMPERATURA + CONDUCTIVIDAD)
#         # ==================================================================================
#         self.container_right = QWidget() # contenedor fijo
#         self.container_right.setFixedSize(192,903)
#         layout_cont_right = QVBoxLayout(self.container_right)
#         layout_cont_right.setContentsMargins(0, 0, 0, 0)


#         self.right = QWidget()
#         self.right.setFixedSize(192, 903)
#         right_layout = QVBoxLayout(self.right)
#         right_layout.setContentsMargins(0, 0, 0, 0)
#         right_layout.setSpacing(0)

#         self.gauge_tempDial = TankGauge("Temp.\nDial", 0 ,50, "°C","#A31A1A")
#         self.powbar = ConductivityBar()

#         self.gauge_tempDial.setFixedWidth(192)        
#         self.powbar.setFixedWidth(192)

#         right_layout.addWidget(self.gauge_tempDial, 1)
#         right_layout.addWidget(self.powbar, 1)

#         layout_cont_right.addWidget(self.right)
#         self.layout.addWidget(self.container_right, 1, 5, 2, 1)      

#         # ==================================================================================
#         #                           === NAVEGACIÓN INFERIOR ===
#         # ==================================================================================
    
#         nav = QWidget()
#         nav.setFixedSize(1536, 177)
#         nav.setStyleSheet("background:  #FCFCFC;") # #090c33 <------------------- aqui tambien se cambiaria para hacer un tema diferente
#         nav_layout = QHBoxLayout(nav)
#         nav_layout.setContentsMargins(40, 20, 40, 20)
#         nav_layout.setSpacing(10)

#         self.botones_nav = {} 

#         botones = [
#             ("Inicio", "#0f172a", self.mostrar_pantalla_principal), # index 0 1b10b9
#             ("Diálisis", "#0f172a", self.show_daialysis_scr), # index 1
#             ("Tipo de\nTratamiento", "#0f172a", self.mostrar_pantalla_modo), # indes 2   ====================================modificar el nombre de esta pantalla para que coincida con el de labview, que es la seleccion del modo de operación
#             ("Inicio\nTratamiento","#25AD37",self.iniciar_tratamiento_),
#             ("Limpieza", "#0f172a", self.mostrar_pantalla_limpieza), # index 3
#             ("Parámetros\n de sistema", "#0f172a", self.mostrar_pantalla_ajustes), # index 4
#             ("Alarmas", "#0f172a", self.mostrar_pantalla_alarmas), # index 5           
#             ("Salir", "#dc2626", self.close),
#         ]
        

#         for texto, color, func in botones:
#             btn = QPushButton(texto)
#             btn.setFixedHeight(110)
#             btn.setStyleSheet(f"""
#                 QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
#                               font-size: 24px; border-radius: 10px; /*border: 4px solid #1b10b9;*/ }}
#                 QPushButton:pressed {{ background: #334155; }}
#             """)
#             btn.clicked.connect(func)
#             nav_layout.addWidget(btn)

#             self.botones_nav[texto] = btn 

#         self.layout.addWidget(nav, 2, 1, 1, 4)
    
#     # ==================================================================================
#     #                               === NAVEGACIÓN ===
#     # ==================================================================================
#     def iniciar_tratamiento_(self): #<------ el boton se debe activar cuando se cumplan las condiciones iniciales, inicia el tratamiento.
#         pass

#     def mostrar_pantalla_principal(self):
#         self.stacked.setCurrentIndex(self.INDEX_INICIO)
#         self.actualizar_label_pantalla("Inicio", "#0A0A0A")
#         self.left.hide()
#         self.right.hide()

#     def show_daialysis_scr(self):       
#         self.stacked.setCurrentWidget(self.dialysis_scr)
#         if hasattr(self.dialysis_scr, "actualizar_valores"): # value_update
#             self.dialysis_scr.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Diálisis", "#0f172a")
#         self.left.show()
#         self.right.show()
#         if "Inicio" in self.botones_nav:
#             self.botones_nav["Inicio"].setEnabled(True)
#             self.botones_nav["Inicio"].setStyleSheet("""
#                 QPushButton { background: #1b10b9; color: #ffffff; font-weight: bold;
#                               font-size: 24px; border-radius: 10px;}
#                 QPushButton:pressed { background: #334155;}
#             """)

#     def mostrar_pantalla_modo(self):
#         self.stacked.setCurrentWidget(self.pantalla_modo_)
#         self.actualizar_label_pantalla("Tipo de Tratamiento", "#0f172a")
#         self.left.show()
#         self.right.show()
    
#     def mostrar_pantalla_limpieza(self):    
#         self.stacked.setCurrentWidget(self.pantalla_limpieza)
#         if hasattr(self.pantalla_limpieza, "actualizar_valores"):
#             self.pantalla_limpieza.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Limpieza", "#0f172a") 
#         self.left.show()
#         self.right.show()   
    
#     def mostrar_pantalla_ajustes(self): 
#         self.stacked.setCurrentWidget(self.pantalla_ajustes)
#         self.actualizar_label_pantalla("Configuración", "#0f172a")     
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_alarmas(self):
#         self.stacked.setCurrentWidget(self.pantalla_alarmas)
#         self.actualizar_label_pantalla("Alarmas", "#0f172a")
#         self.left.show()
#         self.right.show()
    
#     def mostrar_modo_manual(self):
#         self.stacked.setCurrentWidget(self.pantalla_modo_manual)
#         if hasattr(self.pantalla_modo_manual, "actualizar_valores"):
#             self.pantalla_modo_manual.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Modo Manual","#0f172a")
#         self.left.show()
#         self.right.show()
        
    
#     def mostrar_panel_pruebas(self):
#         self.stacked.setCurrentWidget(self.pantalla_panel_pruebas)
#         if hasattr(self.pantalla_panel_pruebas, "actualizar_valores"):
#             self.pantalla_panel_pruebas.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Panel de pruebas", "#0f172a")
#         self.left.show()
#         self.right.show()
        

#     def mostrar_calibracion(self):
#         self.stacked.setCurrentWidget(self.pantalla_calibracion)
#         if hasattr(self.pantalla_calibracion,"actualizar_valores"):
#             self.pantalla_calibracion.actualizar_valores(self.valores)    
#         self.actualizar_label_pantalla("Calibración", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_config_red(self):
#         self.stacked.setCurrentWidget(self.pantalla_config_red)
#         self.actualizar_label_pantalla("Configuración de red", "#0f172a")

#     def mostrar_monitor_variables(self):
#         self.stacked.setCurrentWidget(self.pantalla_monitor_variables)
#         self.actualizar_label_pantalla("Monitor de variables", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_paciente(self):
#         self.stacked.setCurrentWidget(self.pantalla_paciente)
#         if hasattr(self.pantalla_paciente, "actualizar_valores"):
#             self.pantalla_paciente.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Paciente", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_cfg_terapia(self):
#         self.stacked.setCurrentWidget(self.pantalla_configuracion_terapia)
#         if hasattr(self.pantalla_configuracion_terapia, "actualizar_valores"):
#             self.pantalla_configuracion_terapia.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Terapia", "#0f172a")
#         self.left.show()
#         self.right.show()
 
  
#     def actualizar_label_pantalla(self, texto, color_texto="#0f172a"):
#         self.lbl_pantalla_actual.setText(texto)       
#         self.lbl_pantalla_actual.setStyleSheet(f"color: {color_texto}; background: transparent; font-weight: bold; font-size: 30px;")


#     def actualizar_fecha_hora(self):
#         from datetime import datetime
#         texto = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
#         self.lbl_fecha_hora.setText(texto)


#     def actualizar_valor(self, tag: str, valor: float):
#         self.valores[tag] = valor
#         mapeo = {
#             "arterPresProcessData": self.gauge_art,
#             "venouPresProcessData": self.gauge_ven,
#             "dialyTempVariableData": self.gauge_tempDial,
#             "dialyCondVariableData": self.powbar,
#         }
#         if tag in mapeo:
#             mapeo[tag].setValue(valor)

#     def refrescar_etiqueta_alarmas(self):
#         """Actualiza la etiqueta de alarmas con la alarma activa de mayor prioridad"""
#         if not self.alarmas_activas:
#             self.lbl_alarmas.setText("")
#             self.lbl_alarmas.setStyleSheet("""
#                 QLabel { color: #ffffff; background: transparent;
#                          font-weight: bold; font-size: 25px; }
#             """)
#         else:
#             prioridad = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
#             alarma_mayor = max(self.alarmas_activas, key=lambda x: prioridad.get(x[2], 0))
#             nombre, valor, nivel = alarma_mayor

#             texto = nombre.upper()
#             if valor is not None:
#                 texto += f" {valor:.1f}"

#             colores = {
#                 "rojo": "#dc2626",
#                 "naranja": "#f97316",
#                 "amarillo": "#eab308",
#                 "cian": "#06b6d4"
#             }
#             color_fondo = colores.get(nivel, "#1e293b")

#             self.lbl_alarmas.setText(texto)
#             self.lbl_alarmas.setStyleSheet(f"""
#                 QLabel {{ 
#                     background: {color_fondo}; 
#                     color: #ffffff; 
#                     padding: 10px;
#                     border-radius: 12px;
#                     font-weight: bold; 
#                     font-size: 20px; 
#                 }}
#             """)

#     def manejar_alarma(self, idx, activada, valor, nombre, nivel, limite):
#         if activada:
#             if nombre not in [a[0] for a in self.alarmas_activas]:
#                 self.alarmas_activas.append((nombre, valor, nivel))
#         else:
#             self.alarmas_activas = [a for a in self.alarmas_activas if a[0] != nombre]
#         # actualiza la etiqueta
#         self.refrescar_etiqueta_alarmas()
#         self.actualizar_estado()  # parpadeo rojo

#     def actualizar_estado(self):
#         if not hasattr(self,'serial') or not self.serial or not self.serial.conectado:
#             texto, color = "RECONECTANDO...", "#f97316"
#         elif self.alarmas_activas:
#             texto = "ALARMA ACTIVA"
#             color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
#         else:
#             texto, color = "CONECTADO", "#10b981"
    
#         self.lbl_estado.setText(texto)
#         self.lbl_estado.setStyleSheet(f"""
#             QLabel {{ background: {color}; color: #ffffff; padding: 10px;
#                       border-radius: 12px; font-weight: bold; font-size: 22px; }}
#         """)
#         if self.stacked.count() > 0:
#             widget_actual = self.stacked.currentWidget()
#             if hasattr(widget_actual, "actualizar_valores"):
#                 widget_actual.actualizar_valores(self.valores)
      

       
    
#     def registrar_evento(self, evento, valor, hora):
#         logger.error(f"[EVENTO] {hora} → {evento}")

#     def __del__(self):
#         """Destructor: se llama cuando Python destruye el objeto"""
#         logger.error("[INFO] Destructor llamado → deteniendo hilos...")
#         self.detener_todo()
     
#     def detener_todo(self):
#         """Detiene TODO de forma segura y limpia referencias."""
#         logger.error("[INFO] Iniciando detención controlada.")

#         # 1. Detener Timers (si existen)
#         if hasattr(self, 'timer') and isinstance(self.timer, QTimer) and self.timer.isActive():
#             self.timer.stop()
#             logger.error("[INFO] Timer principal detenido.")
#         if hasattr(self, 'timer_reloj') and isinstance(self.timer_reloj, QTimer) and self.timer_reloj.isActive():
#             self.timer_reloj.stop()
#             logger.error("[INFO] Timer reloj detenido.")
    
#         # 2. Detener Alarmas (Alto riesgo de fallo si no está bien implementado)
#         if hasattr(self, 'sistema_alarmas') and self.sistema_alarmas:
#             try:
#                 # La función detener() es responsable de su propio hilo.               
#                 self.sistema_alarmas.detener()
#             except Exception as e:
#                 # Este bloque de código ya no debería dar el error 'NoneType'
#                 logger.error(f"[ERROR] Fallo al detener alarmas de forma limpia: {e}")            
#             # Limpieza la referencia
#             self.sistema_alarmas = None 
#             logger.error("[INFO] Referencia a Sistema de Alarmas nulada.")
    
#         # 3. Detener Serial (Debe ser la última operación de I/O)
#         if hasattr(self, 'serial') and self.serial:
#             try:
#                 # La función detener() es responsable de su propio hilo.
#                 self.serial.detener() # Llama a la versión corregida que cierra el puerto primero
#             except Exception as e:
#                 logger.error(f"[ERROR] Fallo al detener serial: {e}")            
#             # Limpieza defensiva de la referencia
#             self.serial = None
#             logger.error("[INFO] Referencia a Comunicación Serial nulada.")

#         # 4. Pausa de seguridad final
#         # Espera un momento para que los hilos terminen sus joins finales
#         time.sleep(0.1) 
#         logger.error("[INFO] Detención controlada finalizada.")


#     def closeEvent(self, event):
#         logger.error("[INFO] closeEvent → deteniendo todo...")        
#         # Bloquea el hilo principal para terminar los procesos de los hilos
#         self.detener_todo() 
#         # Aumentamos la pausa a 1.0 segundo. Esto es fundamental para darle al sistema operativo
#         # tiempo de liberar correctamente la memoria de los hilos C/C++ subyacentes (Qt/Serial).
#         time.sleep(1.0) 
        
#         event.accept()
#         QApplication.quit()



#=========================================================================================================
    # def _update_therapy_time_displays(self):
    #     """
    #     Actualiza los displays de tiempo en DialysisScreen si está visible.
    #     También detiene automáticamente al finalizar.
    #     """
    #     # Solo si la pantalla de diálisis está activa
    #     if not hasattr(self, 'dialysis_screen') or self.screen_stack.currentWidget() != self.dialysis_screen:
    #         return

    #     if not self.is_treatment_running or self.therapy_start_time is None:
    #         self.dialysis_screen.elapsed_time_display.set_value("00:00")
    #         self.dialysis_screen.remaining_time_display.set_value("00:00")
    #         return

    #     # Tiempo transcurrido
    #     elapsed = self.therapy_start_time.secsTo(QDateTime.currentDateTime())
    #     elapsed_h = elapsed // 3600
    #     elapsed_m = (elapsed % 3600) // 60
    #     self.dialysis_screen.elapsed_time_display.set_value(f"{elapsed_h:02d}:{elapsed_m:02d}")

    #     # Tiempo restante
    #     remaining_sec = max(0, self.total_therapy_seconds - elapsed)
    #     rem_h = remaining_sec // 3600
    #     rem_m = (remaining_sec % 3600) // 60
    #     self.dialysis_screen.remaining_time_display.set_value(f"{rem_h:02d}:{rem_m:02d}")

    #     # Detener automáticamente al llegar a cero
    #     if remaining_sec <= 0:
    #         self.stop_treatment()
    #         QMessageBox.information(self, "Terapia Finalizada", "Tiempo programado completado.")

    def _update_therapy_time_displays(self):
        if not hasattr(self, 'dialysis_screen') or self.screen_stack.currentWidget() != self.dialysis_screen:
            return

        if not self.is_treatment_running or self.therapy_start_time is None:
            self.dialysis_screen.elapsed_time_display.set_value("00:00")
            self.dialysis_screen.remaining_time_display.set_value("00:00")
            return

        # Calcular segundos transcurridos
        elapsed_sec = self.therapy_start_time.secsTo(QDateTime.currentDateTime())

        # Transcurrido
        elapsed_h = elapsed_sec // 3600
        elapsed_m = (elapsed_sec % 3600) // 60
        elapsed_s = elapsed_sec % 60   # ← AGREGADO: segundos reales
        elapsed_str = f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}"  # Muestra segundos también

        self.dialysis_screen.elapsed_time_display.set_value(elapsed_str)

        # Restante
        remaining_sec = max(0, self.total_therapy_seconds - elapsed_sec)
        rem_h = remaining_sec // 3600
        rem_m = (remaining_sec % 3600) // 60
        rem_s = remaining_sec % 60
        remaining_str = f"{rem_h:02d}:{rem_m:02d}:{rem_s:02d}"

        self.dialysis_screen.remaining_time_display.set_value(remaining_str)

        # Detener al llegar a cero
        if remaining_sec <= 0:
            self.stop_treatment()
            QMessageBox.information(self, "Finalizado", "Tiempo de terapia completado.")


    # def start_dialysis_session(self, patient_id: str):
    #     # ... (Carga de datos del paciente, configuración de la máquina, etc.) ...

    #     # Inicializar el logger CSV cuando la sesión comienza
    #     log_dir = "dialysis_logs" # Directorio para guardar los logs
    #     self.csv_logger = CsvLogger(log_dir, patient_id, self.parameter_mapping)
        
    #     self.log_timer.start() # Iniciar el temporizador para el registro

  


