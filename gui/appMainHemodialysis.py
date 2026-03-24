# gui/appMainHemodialysis.py

"""
Módulo principal de la Interfaz Hombre-Máquina (HMI) para el dispositivo de Hemodiálisis.

Este módulo define la clase `HemodialysisHMI`, que actúa como el punto de entrada
y el controlador central de la interfaz gráfica de usuario (GUI). Gestiona la navegación
entre pantallas, la comunicación con el hardware (controladores, sensores), el sistema
de alarmas y el registro de datos (logging).

Responsabilidades principales:
------------------------------
1. **Gestión de Ventanas (Stack):** Administra un `QStackedWidget` para navegar entre
   diferentes pantallas (Inicio, Diálisis, Limpieza, Servicio, Alarmas, etc.).
2. **Comunicación Serial:** Inicializa y maneja `SerialCommunication` para el intercambio
   de datos con el hardware de control en tiempo real.
3. **Monitoreo de Sensores:** Integra controladores específicos para Bioimpedancia/Urea
   (`BiozUreaController`) y Conductividad (`PatternConductivity`).
4. **Sistema de Alarmas:** Centraliza la lógica de alarmas (`AlarmSystem`), monitoreando
   variables críticas y controlando la retroalimentación visual (GUI) y física (Barra LED/Buzzer).
5. **Registro de Datos (Logging):** Gestiona la escritura de datos de telemetría en archivos CSV
   tanto para procesos de cebado como de tratamiento.
6. **Lógica de Tratamiento:** Controla el flujo de estados del tratamiento (Inicio, Pausa,
   Parada), incluyendo el cálculo de tiempo de terapia y métricas como Kt/V.
7. **Interfaz Visual:** Construye el layout principal, incluyendo encabezados de estado,
   paneles laterales de indicadores (gauges) y la barra de navegación inferior.

Dependencias Externas:
----------------------
- PySide6 (Qt for Python): Framework gráfico.
- Core Modules: `alarms`, `variables_map`.
- Connection Modules: `serial_communication`, `led_bar_controller`, `bioz_urea_controller`.
- GUI Components: Pantallas específicas (`DialysisScreen`, `MainScreen`, etc.) y widgets personalizados.

Uso:
----
Esta clase se instancia típicamente desde un archivo `main.py`:

    app = QApplication(sys.argv)
    window = HemodialysisHMI()
    window.showFullScreen()
    sys.exit(app.exec())

Author: Miguel de Jesus C. Espinoza Calderón
Version: 2.11
"""


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
from connection.conductivity_sensor_comm import PatternConductivity
from gui.therapy.main_screen import MainScreen
from gui.therapy.alarms_screen import AlarmsScreen
from gui.therapy.dialysis_screen import DialysisScreen
from gui.therapy.treatment_mode_screen import TreatmentModeScreen
from gui.service.options_screen import OptionsScreen
from gui.service.cleaning_screen import CleaningScreen
from gui.components.real_time_variables import RealTimeVariablesMonitor
from gui.components.tank_gauge import TankGauge
from gui.components.conductivity_bar import ConductivityBar
from gui.components.ui_components import show_dark_message
from gui.configuration.alarm_limits import AlarmLimitsManager
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

    BTN_ENABLED_DEFAULT_STYLE = """
        QPushButton { background: #0f172a; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 10px; }
        QPushButton:pressed { background: #334155; }
    """
    BTN_ENABLED_START_TREATMENT_STYLE = """
        QPushButton { background: #39ec21; color: #ffffff; border-radius: 8px; font-weight: bold; font-size: 30px;}
        QPushButton:pressed { background: #1e40af; }
    """
    BTN_ENABLED_EXIT_STYLE = """
        QPushButton { background: #dc2626; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 10px; }
        QPushButton:pressed { background: #b91c1c; }
    """
    BTN_DISABLED_STYLE = """
        QPushButton { background: #334155; color: #94a3b8; font-weight: bold; font-size: 30px; border-radius: 10px; }
    """
    BTN_ACTIVE_STYLE = """
        QPushButton { background: #3b82f6; color: white; font-weight: bold; font-size: 30px; border-radius: 10px; border: 2px solid #60a5fa;}
        QPushButton:pressed { background: #1e40af; }
    """
    QMESSAGEBOX_GLOBAL_STYLE = """
        QMessageBox {
            background-color: #2b2b2b; /* Fondo de la ventana oscuro */
            color: #ffffff;            /* Texto del QMessageBox (principal) */
        }
        QMessageBox QLabel { /* Reglas para QLabel DENTRO de un QMessageBox */
            color: #ffffff;            /* Asegura que el texto del mensaje sea blanco */
            background-color: #2b2b2b; /* <-- ¡Añadido! Fondo del QLabel explícitamente oscuro */
            padding: 5px;              /* Opcional: un pequeño padding para que el texto no se pegue al borde */
        }
        QMessageBox QPushButton { /* Reglas para QPushButton DENTRO de un QMessageBox */
            background-color: #4CAF50; /* Color de fondo del botón (Verde ejemplo) */
            color: #ffffff;              /* Color del texto del botón */
            border-radius: 5px;        /* Bordes redondeados */
            padding: 5px 15px;         /* Relleno para hacerlo más grande */
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #45a049; /* Color al pasar el mouse por encima */
        }
        QMessageBox QPushButton:pressed {
            background-color: #3e8e41; /* Color al presionar */
        }
    """


    def __init__(self):
        super().__init__()
        self.csv_logger = None
        self.treatment_logger = None
        self.parameter_mapping = {  
            "dialyLinePresProcessData": "PT-3",
            "dialyPresIFProcessData": "PT-4",
            "dialyPresOFProcessData": "PT-5",
            "dialyLineWaterPresData": "PT-6",
            "dialyBChamPresProcessData": "PT-7",
            "bloodArteryPressureData": "PT-8",
            "bloodVenousPressureData": "PT-9",
            "dialyPFilPmpPresProcessData": "PT-10",
            "dialyTempIFProcessData": "Temperatura EF",
            "dialyTempIOFProcessData": "Temperatura SF",
            "dialyTempVariableData": "Temperatura Tanque",
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
            "patternCondSensor": "Cond. Sensor patrón",
            "patternTempSensor": "Temp. Sensor patrón",
            "patternCondRaw": "Cond. Sensor raw", 
        }


        self._last_priming_status = -1
        self._treatment_map = {
            0: "Hemodiálisis",
            1: "Hemodiafiltración",
            2: "Ultrafiltración",
            3: "Limpieza"
        }

        # Control de tiempo de terapia (global)
        self.therapy_start_time = None
        self.total_therapy_seconds = 0
        self.is_treatment_running = False

        self.accumulated_therapy_seconds = 0  
        self.last_resume_time = None          

        # Timer para actualizar tiempo cada segundo (en toda la app)
        self.therapy_time_timer = QTimer(self)
        self.therapy_time_timer.setInterval(1000)  # 1 segundo
        self.therapy_time_timer.timeout.connect(self._update_therapy_time_displays)

        # Timer para mediciones Kt/V cada 30 min
        self.ktv_timer = QTimer(self)
        self.ktv_timer.setInterval(30 * 60 * 1000)  # 30 minutos en ms
        self.ktv_timer.timeout.connect(self.perform_ktv_measurement)

        self.setup_ui()                
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #FCFCFC;")

        self.log_timer = QTimer(self)
        self.log_timer.setInterval(1000) # Registrar cada 5 segundos (5000 ms)
        self.log_timer.timeout.connect(self._log_current_data)

        self.log_treatment_timer = QTimer(self)
        self.log_treatment_timer.setInterval(1000) # Registrar cada segundo
        self.log_treatment_timer.timeout.connect(self._log_treatment_current_data)

        # Serial communication
        self.current_values = {}
        self.serial_comm = SerialCommunication()
        self.serial_comm.data_received.connect(self.update_value)
        self._is_connected_prev_state = False # Rastrea estado de conexción

        # lectura de sensores de bioimpedancia
        self.bioz_urea_controller = BiozUreaController()
        self.bioz_urea_controller.data_received.connect(self.update_value) 
        self.bioz_urea_controller.start()

        # Sensor de conductividad patrón
        self.pattern_sensor = PatternConductivity()
        self.pattern_sensor.data_received.connect(self.on_pattern_data)
        self.pattern_sensor.start()
     
        self.active_alarms = []
        display_names = [info["label"] for g in VARIABLES.values() for info in g.values()]
        tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]
        
        all_tags = []
        for group_key, vars_group in VARIABLES.items():
             if isinstance(vars_group, dict):
                for var_id, info in vars_group.items():
                    if "tag" in info:
                        all_tags.append(info["tag"])
        
        display_names = [self.parameter_mapping.get(tag, tag) for tag in all_tags]
        tags = all_tags # Ahora `tags` es una lista de todos los tags únicos

        # Regenerar las listas para AlarmSystem
        alarm_limits_from_vars = []
        alarm_severity_from_vars = []
        alarm_types_from_vars = []
        boolean_triggers_from_vars = []

        for group_key, vars_group in VARIABLES.items():
            if isinstance(vars_group, dict):
                for var_id, info in vars_group.items():
                    if "tag" in info and info["tag"] in all_tags: # Asegurarse de que el tag esté en la lista
                        alarm_limits_from_vars.append(info.get("limites", (0.0, 100.0)))
                        alarm_severity_from_vars.append(info.get("nivel", "cian"))
                        alarm_types_from_vars.append("numeric" if info["type"] == "double" else "boolean")
                        boolean_triggers_from_vars.append(True if info["type"] == "boolean" else False) # Ajuste para boolean_triggers
        
        self.alarm_limits = AlarmLimitsManager() 
        self.alarm_system = AlarmSystem(
            display_names=display_names,                 
            tags=tags,
            limits=alarm_limits_from_vars,
            severity_levels=alarm_severity_from_vars,
            types=alarm_types_from_vars,
            boolean_triggers=boolean_triggers_from_vars,
            limits_manager=self.alarm_limits
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
        
        self.alarms_screen.limits_manager = self. alarm_limits

        self.real_time_var = RealTimeVariablesMonitor(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        # # Therapy & service screens        
        self.dialysis_screen = DialysisScreen(parent=self, values_dict=self.current_values)
        self.dialysis_screen.request_boolean_change.connect(self._write_boolean_command)

        self.treatment_mode_screen = TreatmentModeScreen(parent=self, values_dict=self.current_values)
        self.treatment_mode_screen.request_setpoint_change.connect(self._write_setpoint)  # Conexión: conecta la señal de pantalla con el método de escritura serial en main

        self.cleaning_screen = CleaningScreen(parent=self, values_dict=self.current_values)
        self.cleaning_screen.request_setpoint_change.connect(self._write_setpoint)
        self.cleaning_screen.request_boolean_change.connect(self._write_boolean_command)

        self.options_screen = OptionsScreen(parent=self)
        
        # # Service sub-screens
        self.manual_mode_screen = ManualModeScreen(parent=self, values_dict=self.current_values)
        self.manual_mode_screen.request_setpoint_change.connect(self._write_setpoint)
        self.manual_mode_screen.request_boolean_change.connect(self._write_boolean_command)

        self.test_panel_screen = TestPanelScreen(parent=self, values_dict=self.current_values)
        self.test_panel_screen.request_setpoint_change.connect(self._write_setpoint) # Conexión: conecta la señal de pantalla con el método de escritura serial en main        

        self.calibration_screen = CalibrationScreen(parent=self, values_dict=self.current_values)
        self.calibration_screen.request_setpoint_change.connect(self._write_setpoint)
        self.calibration_screen.request_boolean_change.connect(self._write_boolean_command)

        self.network_config_screen = NetworkConfigScreen(parent=self)
        

        # # Therapy sub-screens
        self.patient_config_screen = PatientConfigScreen(parent=self)
        
        self.therapy_config_screen = TherapyConfigScreen(parent=self, values_dict=self.current_values) # intanciar pasando los valores actuales (values_dict)
        self.therapy_config_screen.request_setpoint_change.connect(self._write_setpoint) # Conexión: conecta la señal de pantalla con el método de escritura serial en main   
        self.therapy_config_screen.request_boolean_change.connect(self._write_boolean_command)     
        self.therapy_config_screen.valueChanged.connect(self.handleGlobalValueChange) # Actualizar UI localmente

        
        # Add all screens to stacked widget (order matters)
        self.screen_stack.addWidget(self._main_screen)                 # 0 - Home
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


        self.therapy_config_screen.valueChanged.connect(self.handleGlobalValueChange)
        self.calibration_screen.valueChanged.connect(self.handleGlobalValueChange)
        self.manual_mode_screen.valueChanged.connect(self.handleGlobalValueChange)

        self._update_priming_controls_state() 

        # Header update timers
        self.refresh_alarms_label()
        self.refresh_treatment_selected()
        

        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self.update_connection_status)
        self.main_timer.start(500)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_date_time)
        self.clock_timer.start(1000)
        self.update_date_time()

        self.serial_comm.connect()
        self.serial_comm.start_reading()

        self._set_ui_connected_state(False)
        self.screen_stack.setCurrentIndex(self.INDEX_HOME)

        self.right_content.hide()
        self.left_content.hide()
        self.left_container.setStyleSheet("background: transparent")
        self.right_container.setStyleSheet("background: transparent")
    

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
        header_layout.setSpacing(5)

        #logo 1
        
        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo1)

        # Connection / alarm status
        self.status_label = QLabel("Conectado")
        self.status_label.setFixedSize(260, 120)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
               QLabel { background: #10b981; color: #ffffff; 
                       font-weight: bold; font-size: 25px; }
        """)
        header_layout.addWidget(self.status_label)

        self.active_alarms_label = QLabel("") 
        self.treatment_mode_selected = QLabel("")
        self.current_process_status = QLabel("Esperando conexión")
        self.date_time_label = QLabel("25/12/2025  14:37:22")
        
        for lbl in [self.active_alarms_label,  self.current_process_status, self.treatment_mode_selected, self.date_time_label]:
            lbl.setFixedSize(330, 120)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                QLabel { color: #ffffff; background: #1E4573;
                         font-weight: bold; font-size: 25px; }
            """)
            header_layout.addWidget(lbl)

        
        header_layout.addStretch()

        # Logo 2

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
        nav_bar.setFixedSize(1560, 150)
        nav_bar.setStyleSheet("background: #FCFCFC;")

        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        nav_layout.setSpacing(10)

        self.navigation_buttons = {}

        nav_items = [
            ("Inicio",              "#0f172a", self.show_home_screen),
            ("Diálisis",            "#0f172a", self.show_dialysis_screen),
            ("Tipo de\nTratamiento","#0f172a", self.show_treatment_mode_screen), 
            ("Iniciar\nTratamiento", "#39ec21", self.start_treatment),
            ("Limpieza",            "#0f172a", self.show_cleaning_screen),
            ("Servicio", "#0f172a", self.show_options_screen),
            ("Alarmas",             "#0f172a", self.show_alarms_screen),
            ("Salir",               "#dc2626", self.close),
        ]

        for text, color, callback in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(110)           
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self.navigation_buttons[text] = btn

        self.main_layout.addWidget(nav_bar, 2, 1, 1, 4)

    # ────────────────────────────────────────────────
    #              Navigation Methods
    # ────────────────────────────────────────────────
    def start_treatment(self):
        logger.info("Iniciando tratamiento y mediciones externas: Bioimpedancia")

        hours = int(self.current_values.get("heparineTherapyHours", 0))
        minutes = int(self.current_values.get("heparineTherapyMinutes", 0))
        self.total_therapy_seconds = (hours * 3600) + (minutes * 60)

        if self.total_therapy_seconds <= 0:
            show_dark_message(self, "Configuración incompleta", 
                                "Configure la duración de la terapia primero.",
                                icon=QMessageBox.warning)
            self.show_therapy_config_screen()
            return
        current_status = int(self.current_values.get("primingProcessStatus", 0))
        
        if current_status != 14:             
            self.accumulated_therapy_seconds = 0
        else:
            logger.info("Reanudando tratamiento desde Pausa (manteniendo tiempo acumulado)")
                
        self.last_resume_time = QDateTime.currentDateTime()   
        self.is_treatment_running = True
        
        if not self.therapy_time_timer.isActive():
            self.therapy_time_timer.start()

        try:        
            self._write_boolean_command("dialyModeOperationStart", True)            
            self._write_boolean_command("dialyModeOperationStop", False)
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}")
            show_dark_message(self, "Advertencia", 
                                "Cebado iniciado, pero hubo problema al enviar comandos al controlador.",
                                icon=QMessageBox.Warning)


        # Iniciar bioimpedancia y Kt/V
        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("SRTB")
    
        
        self.perform_ktv_measurement()
        
        if not self.ktv_timer.isActive():
            self.ktv_timer.start()

        if self.screen_stack.currentWidget() == self.dialysis_screen:
            self.dialysis_screen.update_values(self.current_values)
        if self.treatment_logger:
            logger.info("Cerrando logger anterior antes de nuevo tratamiento")
            self.log_treatment_timer.stop()
            self.treatment_logger.close()
            self.treatment_logger = None

        LOG_DIRECTORY = "logs/tratamiento_hemodialisis"

        try:
            self.treatment_logger = CsvLogger(
                log_directory=LOG_DIRECTORY,
                parameter_key_map=self.parameter_mapping
            )
            self.log_treatment_timer.start() 
            logger.info("Logger CSV iniciado correctamente para tratamiento")
        except Exception as e:
            logger.error(f"Error al crear logger CSV para tratamiento: {e}")
            show_dark_message(self, "Error crítico", f"No se pudo iniciar el registro de datos:\n{str(e)}", 
                      icon=QMessageBox.Critical)
            return

    

    def start_priming(self):
        """
        Inicia el proceso de cebado (priming / enjuague).
        - Verifica conexión serial
        - Cierra logger anterior si existe
        - Inicia nuevo logging CSV
        - Envía comandos booleanos al controlador
        - Muestra feedback al usuario
        """
        # 1. Verificar conexión serial
        if not self.serial_comm or not self.serial_comm.is_connected:
            show_dark_message(self, "Error de conexión", 
                          "No hay conexión con el controlador.\n"
                          "No se puede iniciar el cebado.",
                          icon=QMessageBox.Warning)  
            logger.warning("Intento de iniciar cebado sin conexión serial")
            return

        # 2. Cerrar logger anterior si ya existe (evita duplicados/corrupción)
        if self.csv_logger:
            logger.info("Cerrando logger anterior antes de nuevo cebado")
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None

        # 3. Definir directorio de logs (puedes cambiar la ruta si quieres)
        LOG_DIRECTORY = "logs/hemodialysis_cebado"  # Se crea automáticamente si no existe

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
            show_dark_message(self, "Error crítico", 
                                 f"No se pudo iniciar el registro de datos:\n{str(e)}",
                                 icon=QMessageBox.Critical)
            return

        # 5. Enviar comandos al controlador
        try:
            self._write_boolean_command("dialyStartDialysisButt", True)
            self._write_boolean_command("dialyStopDialysisButt",False)
           
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}")
            
            
            show_dark_message(self, "Advertencia", 
                                "Cebado iniciado, pero hubo problema al enviar comandos al controlador.",
                                icon=QMessageBox.Warning)


   
    
        show_dark_message(self, "Cebado Iniciado",
                  "Proceso de cebado iniciado correctamente.\n\n"
                  "Presione 'DETENER' cuando finalice o espere condición automática.",
                  icon=QMessageBox.Information)

        self.show_dialysis_screen()

    def stop_priming(self):
        try:
            self._write_boolean_command("dialyStopDialysisButt",True)
            self._write_boolean_command("dialyStartDialysisButt", False)              
           
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}")
            show_dark_message(self, "Advertencia", 
                                "Cebado iniciado, pero hubo problema al enviar comandos al controlador.",
                                icon=QMessageBox.Warning)
        if self.csv_logger:
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")


    def stop_treatment(self):   

        try:            
            self._write_boolean_command("dialyModeOperationStop", True)
            self._write_boolean_command("dialyModeOperationStart", False)                   
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de paro de terapia: {e}")


        # if self.ktv_timer.isActive():
        #     self.ktv_timer.stop()
        #     logger.info("[kt/V] Medición detenida")

        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("STOP")

        # Resetear estado de tiempo

        # self.is_treatment_running = False
        # self.therapy_start_time = None
        # self.total_therapy_seconds = 0

        self.is_treatment_running = False
        self.accumulated_therapy_seconds = 0  # Limpiar
        self.last_resume_time = None          # Limpiar


        # Detener timer de actualización si no hay tratamiento
        if hasattr(self, 'therapy_time_timer') and self.therapy_time_timer.isActive():
            self.therapy_time_timer.stop()

        # Actualizar displays inmediatamente
        self._update_therapy_time_displays()

        # Cerrar logger si existe
        if self.treatment_logger:
            self.log_treatment_timer.stop()
            self.treatment_logger.close()
            self.treatment_logger = None
            logger.info("Sesión detenida - logger cerrado")


    def pause_treatment(self):
        try:
            self._write_boolean_command("dialyModeOperationPause", True)
            self._write_boolean_command("dialyModeOperationPause", False)
        except Exception as e:
            logger.error(f"[Error] Error al pausar terapia {e}")
        

    def end_dialysis_session(self):
        if self.csv_logger:
            self.log_timer.stop()
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")

        if self.treatment_logger:
            self.log_treatment_timer.stop()
            self.treatment_logger.close()
            self.treatment_logger = None
            logger.info("Sesión detenida - logger cerrado")
        

    def show_home_screen(self):
        self.screen_stack.setCurrentIndex(self.INDEX_HOME)        
        self.right_content.hide()
        self.left_content.hide()
        self._highlight_active_nav_button("Inicio")


    def show_dialysis_screen(self):
        self.screen_stack.setCurrentWidget(self.dialysis_screen)
        if hasattr(self.dialysis_screen, "update_values"):
            self.dialysis_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self.navigation_buttons["Inicio"].setEnabled(True)        
        self.navigation_buttons["Inicio"].setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE) # NUEVO: usa el estilo de clase
        self._highlight_active_nav_button("Diálisis")

    def show_treatment_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.treatment_mode_screen)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Tipo de\nTratamiento") 

    def show_cleaning_screen(self):
        self.screen_stack.setCurrentWidget(self.cleaning_screen)
        if hasattr(self.cleaning_screen, "update_values"):
            self.cleaning_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Limpieza")

    def show_options_screen(self):
        self.screen_stack.setCurrentWidget(self.options_screen)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_alarms_screen(self):
        self.screen_stack.setCurrentWidget(self.alarms_screen)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Alarmas")

    def show_manual_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.manual_mode_screen)
        if hasattr(self.manual_mode_screen, "update_values"):
            self.manual_mode_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()

    def show_test_panel_screen(self):
        self.screen_stack.setCurrentWidget(self.test_panel_screen)
        if hasattr(self.test_panel_screen, "update_values"):
            self.test_panel_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()

    def show_calibration_screen(self):
        self.screen_stack.setCurrentWidget(self.calibration_screen)
        if hasattr(self.calibration_screen, "update_values"):
            self.calibration_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()

    def show_network_config_screen(self):
        self.screen_stack.setCurrentWidget(self.network_config_screen)
        self.left_content.show()
        self.right_content.show()

    def show_real_time_var_screen(self):
        self.screen_stack.setCurrentWidget(self.real_time_var)
        self.left_content.show()
        self.right_content.show()

    def show_patient_config_screen(self):
        self.screen_stack.setCurrentWidget(self.patient_config_screen)
        if hasattr(self.patient_config_screen, "update_values"):
            self.patient_config_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()

    def show_therapy_config_screen(self):
        self.screen_stack.setCurrentWidget(self.therapy_config_screen)
        if hasattr(self.therapy_config_screen, "update_values"):
            self.therapy_config_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()

        
        
        

    # ────────────────────────────────────────────────
    #              Utility Methods
    # ────────────────────────────────────────────────
    def _set_ui_connected_state(self, is_connected: bool):
        """
        Manages the overall UI state (buttons, header labels) based on connection status.
        """
        if is_connected:
            logger.info("Enabling UI elements for connected state.")
            for btn_text, btn in self.navigation_buttons.items():
                btn.setEnabled(True)
                if btn_text == "Salir":
                    btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE)
                elif btn_text == "Iniciar\nTratamiento":
                    btn.setStyleSheet(self.BTN_ENABLED_START_TREATMENT_STYLE)
                else:
                    btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
            
            # Restaurar etiquetas del encabezado a su estado por defecto
            self.refresh_alarms_label() # Mostrará alarmas reales o vacío
            self.refresh_treatment_selected() # Mostrar tratamiento seleccionado actualmente - default Hemodiálisis
            self.current_process_status.setText("Máquina conectada") 

            # Asegurar que se muestre la pantalla de inicio y se oculten los paneles laterales
            self.show_home_screen() 
            self._update_treatment_controls_state()
            self._update_priming_controls_state()

        else: # Desconectado
            logger.warning("Disabling UI elements for disconnected state.")
            for btn_text, btn in self.navigation_buttons.items():
                btn.setEnabled(False)
                if btn_text == "Salir": # 'Salir' siempre habilitado, incluso desconectado
                    btn.setEnabled(True) 
                    btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE)
                else:
                    btn.setStyleSheet(self.BTN_DISABLED_STYLE)
            
            # Actualizar etiquetas del encabezado para reflejar la desconexión
            self.active_alarms_label.setText("")             
            self.current_process_status.setText("Esperando conexión")

            # Siempre volver a la pantalla de inicio y ocultar paneles laterales cuando se desconecta
            self.show_home_screen() # Esto ocultará el contenido lateral y establecerá el índice de pantalla a inicio.

    
    def handleGlobalValueChange(self, tag: str, value: float):
        # Actualiza el diccionario compartido y propaga a todas las pantallas si es necesario
        self.current_values[tag] = value  # Actualiza el valor global
        print(f"[GLOBAL] Valor actualizado: {tag} = {value}")  # Log para depuración
        
        # Opcional: Notifica a todas las pantallas para que se actualicen
        for screen in [self.therapy_config_screen, self.calibration_screen, self.test_panel_screen, self.manual_mode_screen,self.alarms_screen,self.real_time_var]:  # Agrega todas las pantallas
            if hasattr(screen, 'update_values'):
                screen.update_values(self.current_values)  # Llama al update en cada pantalla

    def update_date_time(self):
        from datetime import datetime
        self.date_time_label.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))    

    def update_value(self, tag: str, value: float):
        # Actualizar valor centralizado
        self.current_values[tag] = value

        # Actualizar sistema de alarmas si existe
        if self.alarm_system:
            self.alarm_system.update_value_by_tag(tag, value)

        # Lógica específica de KTV/urea
        if tag == "urea_adc2":
            self.measurement_ktv()

        # Actualizar gauges
        gauge_mapping = {
            "arterPresProcessData":   self.arterial_pressure_gauge,
            "venouPresProcessData":   self.venous_pressure_gauge,
            "dialyTempVariableData":  self.dialysate_temp_gauge,
            "dialyCondVariableData":  self.conductivity_bar,
        }
        if tag in gauge_mapping:
            gauge_mapping[tag].setValue(value)

        # Manejo del tratamiento seleccionado
        if tag == "treatmentModeSelection":
            self.refresh_treatment_selected() # Llama al nuevo método para actualizar el label


        # ────────────────────────────────────────────────────────────────
        # Manejo de primingProcessStatus (estado del proceso)
        # ────────────────────────────────────────────────────────────────
        if tag == "primingProcessStatus":
            status_code = int(value)
            # Solo procesar si realmente cambió el estado
            if status_code != self._last_priming_status:
                self._last_priming_status = status_code

                # Mapa de estados
                status_map = {
                    1:  "INICIO CEBADO",
                    2:  "LLENADO DE TANQUE",
                    3:  "LLENADO DE LINEA",
                    4:  "LLENADO CÁMARA",
                    5:  "CALENTAMIENTO",
                    6:  "INFUSIÓN",
                    7:  "DIÁLISIS",
                    8:  "BYPASS",
                    9:  "CERRADO",
                    11: "ULTRAFILTRACIÓN OFF",
                    12: "LISTO PARA INICIAR\nTRATAMIENTO",
                    13: "TRATAMIENTO INICIADO",
                    14: "PAUSA",
                    15: "TRATAMIENTO DETENIDO"
                }

                status_text = status_map.get(status_code, f"Espera.. ({status_code})")
                self.current_process_status.setText(status_text)

                # --- LÓGICA DE PAUSA DE TIEMPO ---
                # Caso A: Estaba corriendo (o listo) y pasa a PAUSA (14)
                if status_code == 14 and self.last_resume_time is not None:
                    # Calculamos cuánto tiempo pasó desde el último inicio hasta ahora y lo guardamos
                    seconds_since_resume = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                    self.accumulated_therapy_seconds += seconds_since_resume
                    self.last_resume_time = None  # Ponemos en None para indicar que NO estamos contando tiempo
                    logger.info(f"Terapia PAUSADA. Tiempo acumulado: {self.accumulated_therapy_seconds}s")

                # Caso B: Estaba en Pausa (14) y vuelve a TRATAMIENTO (13)
                elif status_code == 13 and self.last_resume_time is None:
                    self.last_resume_time = QDateTime.currentDateTime()
                    logger.info("Terapia REANUDADA. Contador activo.")

                self._last_priming_status = status_code

                # Colores según estado
                if status_code in [6, 7, 12, 13]:      # Activos / listos / tratamiento
                    color = "#25AD37"  # Verde
                elif status_code in [1, 2, 3, 4, 5, 8]:  # Preparación / cebado
                    color = "#eab308"  # Amarillo
                elif status_code in [14, 15]:          # Pausa / detenido / error
                    color = "#ef4444"  # Rojo
                else:
                    color = "#C6E3E6"  # Gris neutro

                self.current_process_status.setStyleSheet(f"""
                    QLabel {{
                        color: #ffffff;
                        background: {color};
                        font-weight: bold;
                        font-size: 25px;
                        border-radius: 10px;
                    }}
                """)   
                self._update_priming_controls_state()

        # ────────────────────────────────────────────────────────────────
        # Reevaluar botón "Iniciar Tratamiento" cuando cambien status o temp
        # ────────────────────────────────────────────────────────────────
        if tag in ["primingProcessStatus", "dialyTempVariableData", 
                   "dialyTempControlSetPoint", "dialyCondVariableData", 
                   "dialyCondControlSetPoint"]:            
            self._update_treatment_controls_state()
        

    def _update_treatment_controls_state(self):
        """
        Calcula si se puede iniciar o detener tratamiento y actualiza
        TANTO la barra de navegación COMO la pantalla de diálisis.
        """
        # 1. Obtener valores necesarios
        status_code = int(self.current_values.get("primingProcessStatus", 0))
        temp_actual = self.current_values.get("dialyTempVariableData", 0.0)
        temp_set    = self.current_values.get("dialyTempControlSetPoint", 0.0)
        cond_actual = self.current_values.get("dialyCondVariableData", 0.0)
        cond_set    = self.current_values.get("dialyCondControlSetPoint", 0.0)

        # 2. Lógica de validación (Tolerancias)
        temp_ok = abs(temp_actual - temp_set) <= 2.0
        cond_ok = abs(cond_actual - cond_set) <= 2.0
        
        # 3. Determinar qué botones deben estar activos
        can_start = False
        can_stop = False

        if status_code == 12:  # LISTO PARA INICIAR
            if temp_ok and cond_ok:
                can_start = True
                can_stop = False
            else:
                # Listo por estado, pero temperaturas/cond mal
                can_start = False
                can_stop = False

        elif status_code == 13: # TRATAMIENTO CORRIENDO
            can_start = False
            can_stop = True
        elif status_code == 14:
            if temp_ok and cond_ok:
                can_start = True
                can_stop = True  #False se puede detener si se esta en pausa 
            else:                
                can_start = False
                can_stop = False

        else: # CUALQUIER OTRO ESTADO (Cebado, Pausa, etc)
            can_start = False
            can_stop = False

        # =========================================================
        # 4. APLICAR A LA BARRA DE NAVEGACIÓN (Botón Grande)
        # =========================================================
        nav_btn = self.navigation_buttons.get("Iniciar\nTratamiento")
        if nav_btn:                      
            if nav_btn.isEnabled() != can_start:
                nav_btn.setEnabled(can_start)                                  
                nav_btn.setStyleSheet(self.BTN_ENABLED_START_TREATMENT_STYLE if can_start else self.BTN_DISABLED_STYLE) 

        # =========================================================
        # 5. APLICAR A LA PANTALLA DE DIÁLISIS (Botones Chicos)
        # =========================================================
        # Verificamos si la pantalla ya fue creada y tiene el método
        if hasattr(self, 'dialysis_screen') and self.dialysis_screen:
            if hasattr(self.dialysis_screen, 'set_start_stop_buttons_state'):
                self.dialysis_screen.set_start_stop_buttons_state(can_start, can_stop)


    def _update_priming_controls_state(self):
        """
        Calcula el estado de los botones de cebado ('INICIAR CEBADO', 'DETENER CEBADO')
        basándose en 'primingProcessStatus' y los actualiza en la DialysisScreen.
        """
        status_code = int(self.current_values.get("primingProcessStatus", 0))

        enable_start_priming = False
        enable_stop_priming = False

        # --- Lógica para "INICIAR CEBADO" ---
        # Solo se puede iniciar cebado si la máquina está en el estado inicial de cebado (1).
        if status_code == 1: # "INICIO CEBADO"   
            enable_start_priming = True
        
        # --- Lógica para "DETENER CEBADO" ---
        # Este botón actua como un "Detener/Finalizar Proceso General".
        
        # Habilitar si el cebado está activo (estados 2 a 8)
        if status_code >= 2 and status_code <= 8:
            enable_stop_priming = True
        elif status_code == 12:
            enable_stop_priming = True    
        # Habilitar si el tratamiento está activo (estado 13)
        elif status_code == 13: # "TRATAMIENTO INICIADO"
            enable_stop_priming = False
        # Habilitar si el tratamiento está en pausa (estado 14)
        elif status_code == 14: # "PAUSA"
            enable_stop_priming = True
        # Habilitar si el tratamiento acaba de ser detenido (estado 15)
        elif status_code == 15: # "TRATAMIENTO DETENIDO" - ESTO RESPONDE A TU FEEDBACK
            enable_stop_priming = True

        # Deshabilitar en estados donde no hay nada que detener o ya está en un estado inactivo/listo
        if status_code in [1, 9]: # 1: INICIO CEBADO, 9: CERRADO, 12: LISTO PARA INICIAR TRATAMIENTO
             enable_stop_priming = False

        # Actualizar los botones en la pantalla de diálisis
        if hasattr(self, 'dialysis_screen') and self.dialysis_screen:
            if hasattr(self.dialysis_screen, 'set_priming_buttons_state'):
                self.dialysis_screen.set_priming_buttons_state(enable_start_priming, enable_stop_priming)


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
                QLabel {{ background: {bg_color}; color: #ffffff; 
                          font-weight: bold; font-size: 20px; }}
            """)

    def refresh_treatment_selected(self):
        # Obtener el valor actual del tag
        mode_code = int(self.current_values.get("treatmentModeSelection", 0)) # Por defecto 0 (Hemodiálisis)
        # Traducir el código a texto usando el mapa
        mode_text = self._treatment_map.get(mode_code, "Desconocido") # "Desconocido" si el código no está en el mapa
        # Actualizar el QLabel en el encabezado
        self.treatment_mode_selected.setText(mode_text.upper()) # Mostrar en mayúsculas para consistencia
        self.treatment_mode_selected.setStyleSheet(f"""
            QLabel {{ color: #ffffff; background: #1E4573;
                     font-weight: bold; font-size: 25px; }}
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
        """
        Actualiza el estado de la conexión en la UI y maneja la habilitación/deshabilitación
        de elementos según el estado de la conexión.
        """
        current_is_connected = self.serial_comm and self.serial_comm.is_connected
        if current_is_connected != self._is_connected_prev_state:
            self._set_ui_connected_state(current_is_connected)
         
        if not current_is_connected:
            text, color = "RECONECTANDO...", "#f97316" 
        elif self.active_alarms:
            text = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            text, color = "CONECTADO", "#10b981"

        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{ background: {color}; color: #ffffff; 
                      font-weight: bold; font-size: 22px; }}
        """)

        self._is_connected_prev_state = current_is_connected
        current_widget = self.screen_stack.currentWidget()
        if hasattr(current_widget, "update_values"):
            current_widget.update_values(self.current_values)
        
        self.refresh_alarms_label()
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
        
        self.pattern_sensor.stop()
        time.sleep(0.1)
        logger.error("[INFO] Controlled shutdown completed.")

    def _log_current_data(self):
        """
        Método slot llamado por el QTimer para registrar los datos actuales.
        """
        if self.csv_logger:
            self.csv_logger.log_data(self.current_values)

    def _log_treatment_current_data(self):
        if self.treatment_logger:
            self.treatment_logger.log_data(self.current_values)


    def _write_boolean_command(self, tag: str, state: bool):
        """
        Envía un comando booleano (True/False) al controlador vía serial.
        """
        if not self.serial_comm or not self.serial_comm.is_connected:
            logger.warning(f"No se puede enviar comando booleano '{tag} = {state}': serial no conectado")            
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
            return  # Opcional: mostrar QMessageBox para feedback visual

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

    def on_pattern_data(self, tag: str, value: float):
        
        if tag == "patternCondSensor":
            VARIABLES[0x09][0x00]["value"] = value
            

        elif tag == "patternCondRaw":
            VARIABLES[0x09][0x02]["value"] = value
            

        elif tag == "patternTempSensor":
            VARIABLES[0x09][0x01]["value"] = value
            

        self.current_values[tag] = value  
        current_widget = self.screen_stack.currentWidget()
        if hasattr(current_widget, "update_values"):
            current_widget.update_values(self.current_values)
    
    def _update_therapy_time_displays(self):
        if not hasattr(self, 'dialysis_screen') or self.screen_stack.currentWidget() != self.dialysis_screen:
            return
        
        if not self.is_treatment_running:
            self.dialysis_screen.elapsed_time_display.set_value("00:00:00")
            self.dialysis_screen.remaining_time_display.set_value("00:00:00")
            return

        # Calcular segundos transcurridos
        
        current_elapsed_seconds = self.accumulated_therapy_seconds
        if self.last_resume_time is not None:
            current_segment_seconds = self.last_resume_time.secsTo(QDateTime.currentDateTime())
            current_elapsed_seconds += current_segment_seconds


        # Transcurrido
        elapsed_h = current_elapsed_seconds // 3600
        elapsed_m = (current_elapsed_seconds % 3600) // 60
        elapsed_s = current_elapsed_seconds % 60
        elapsed_str = f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}"

        self.dialysis_screen.elapsed_time_display.set_value(elapsed_str)

        # Restante
        remaining_sec = max(0, self.total_therapy_seconds - current_elapsed_seconds)
        rem_h = remaining_sec // 3600
        rem_m = (remaining_sec % 3600) // 60
        rem_s = remaining_sec % 60
        remaining_str = f"{rem_h:02d}:{rem_m:02d}:{rem_s:02d}"

        self.dialysis_screen.remaining_time_display.set_value(remaining_str)

        # Detener al llegar a cero
        if remaining_sec <= 0:
            self.stop_treatment()
            self.stop_priming()
          


    def _highlight_active_nav_button(self, active_button_text: str):
        """
        Resalta el botón de navegación correspondiente a la pantalla activa
        y restablece el estilo de los demás botones.
        """
        # Lista de textos de botones que representan pantallas navegables
        screen_buttons = ["Inicio", "Diálisis", "Tipo de\nTratamiento", "Limpieza", "Servicio", "Alarmas"]

        for btn_text, btn in self.navigation_buttons.items():
            # Solo procesamos botones de pantalla que estén habilitados
            if btn_text in screen_buttons and btn.isEnabled():
                if btn_text == active_button_text:
                    btn.setStyleSheet(self.BTN_ACTIVE_STYLE)
                else:
                    btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
            # Los botones "Iniciar Tratamiento" y "Salir" se mantienen con sus estilos
            # específicos definidos en _set_ui_connected_state o directamente.
            # Los botones deshabilitados mantienen su BTN_DISABLED_STYLE.


    def closeEvent(self, event):
        self.end_dialysis_session() # Llama a la función que cierra el logger
        
        super().closeEvent(event)
        logger.error("[INFO] closeEvent → performing shutdown...")
        self.shutdown()
        time.sleep(1.0) 
        event.accept()
        QApplication.quit()



