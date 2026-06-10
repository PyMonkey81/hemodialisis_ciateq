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
Esta clase se instancia desde archivo `main.py`:

    app = QApplication(sys.argv)
    window = HemodialysisHMI()
    window.showFullScreen()
    sys.exit(app.exec())

Author: Miguel de Jesus C. Espinoza Calderón
Version: 2.18.5
"""


import os
import sys
import time
import logging
import csv
import json
from typing import List, Tuple

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QDateTime, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QPixmap

# === MODULES ===
from core.alarms import AlarmSystem
from core.alarm_config_manager import AlarmConfigManager
from core.state_manager import AppStateManager, TreatmentPhase
from core.variables_map import TAG_TO_ADDRESS, VARIABLES

from connection.serial_communication import SerialCommunication
from connection.led_bar_controller import LedBarController
from connection.bioz_urea_controller import BiozUreaController
from connection.conductivity_sensor_comm import PatternConductivity

from gui.therapy.main_screen import MainScreen
from gui.therapy.alarms_screen import AlarmsScreen
from gui.therapy.dialysis_screen import DialysisScreen
from gui.therapy.treatment_mode_screen import TreatmentModeScreen
from gui.therapy.ktv_screen import KTVScreen
from gui.service.options_screen import OptionsScreen
from gui.service.history_screen import HistoryScreen
from gui.service.cleaning_screen import CleaningScreen
from gui.service.comm_port_screen import CommPortScreen
from gui.components.real_time_variables import RealTimeVariablesMonitor
from gui.components.tank_gauge import TankGauge
from gui.components.conductivity_bar import ConductivityBar
from gui.components.floating_message import FloatingMessage

from gui.configuration.alarm_limits import AlarmLimitsManager
from gui.configuration.alarm_screen_config import AlarmScreenConfig 
from gui.configuration.alarm_screen_service_config import AlarmScreenServiceConfig
from gui.configuration.cleanning_config_screen import CleanningConfigScreen

from gui.service.manual_mode_screen import ManualModeScreen
from gui.service.test_panel_screen import TestPanelScreen
from gui.service.calibration_screen import CalibrationScreen
from gui.service.network_config_screen import NetworkConfigScreen
from gui.service.maintenance_screen import MaintenanceScreen

from gui.therapy.patient_config_screen import PatientConfigScreen
from gui.therapy.therapy_config_screen import TherapyConfigScreen

from logic.ktv_calculator import CalculadoraKtV
from logic.heitmann import heitmann
from logic.calculos import (
    convertir_flujo_a_ciclos, convertir_ciclos_a_flujo,
    convertir_litros_h_a_ml_min, convertir_ml_min_a_litros_h,
    calculo_ptm
)
from utilities.csv_logger import CsvLogger

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
        self.cleaning_logger = None

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
            "CALC_PTM": "Presión Transmembrana",
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

        self.calculadora_ktv = CalculadoraKtV(parent=self)
        # # ====================== TIMER MAESTRO (ÚNICO) ======================
        # self.master_timer = QTimer(self)
        # self.master_timer.setInterval(500)          # 500ms = 2 actualizaciones por segundo
        # self.master_timer.timeout.connect(self._master_timer_tick)

        # # Variables de control para el timer maestro
        # self.last_second_update = QDateTime.currentDateTime()
        # self.last_minute_update = QDateTime.currentDateTime()


        #======================= GESTOR DE ESTADOS ==========================

        self.state = AppStateManager()
        
        # Conectar señales a métodos de la app
        self.state.state_changed.connect(self._on_state_changed)
        self.state.treatment_started.connect(self._on_treatment_started)
        self.state.treatment_paused.connect(self._on_treatment_paused)
        self.state.treatment_resumed.connect(self._on_treatment_resumed)
        self.state.treatment_finished.connect(self._on_treatment_finished)
        self.state.cleaning_started.connect(self._on_cleaning_started)
        self.state.cleaning_finished.connect(self._on_cleaning_finished)
        self.state.error_occurred.connect(self._on_state_error)

        # ====================== TIMER MAESTRO (ÚNICO) ======================
        self.master_timer = QTimer(self)
        self.master_timer.setInterval(500)
        self.master_timer.timeout.connect(self._master_timer_tick)

        # Variables de control para el timer maestro
        self.last_second_update = QDateTime.currentDateTime()
        self.last_minute_update = QDateTime.currentDateTime()
        self._timer_lock = False  # ← NUEVO: protección contra reentrancia


        # ====================== HISTORIAL DE TRATAMIENTOS Y LIMPIEZA ======================
        self.treatment_history = []   # Se cargará desde JSON
        self.cleaning_history = []
        
        self.current_treatment_start = None   # Para registrar cuando inicia un tratamiento

        # ====================== VARIABLES DE HORAS ======================
        self.total_operation_hours = 0.0   # Tratamiento activo
        self.power_on_hours = 0.0          # Máquina encendida
        self.cleaning_hours = 0.0          # Tiempo en limpieza

        # Timers de conteo
        self.operation_start_time = None
        self.cleaning_start_time = None
        self.last_resume_time = None
        
        self.is_treatment_running = False
        self.is_cleaning_in_progress = False

        self._current_elapsed_therapy_min = 0.0 # Variable para cálculo de Kt/V acumulado en tiempo real        
        self._original_conductivity_setpoint = None # Para almacenar el setpoint original de conductividad antes de cualquier ajuste por terapia o limpieza
    
        

        # Control de tiempo de terapia (global)
        self.therapy_start_time = None
        self.total_therapy_seconds = 0
        self.accumulated_therapy_seconds = 0
        
        

        self.current_treatment_start_date_time = None # Variable para reporte de inicio/tratamiento
        self.navigation_buttons = {} # nuevo
        self.setup_ui()           
        self._load_histories()     
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #FCFCFC;")

        # Serial communication
        self.current_values = {}
        for group_key, vars_group in VARIABLES.items():
            if isinstance(vars_group, dict):
                for var_id, info in vars_group.items():
                    if "tag" in info:
                        self.current_values[info["tag"]] = 0.0 # Inicializar todos a 0.0

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
     
        # ====================== CONFIGURACIÓN DE ALARMAS (Nueva Arquitectura) ======================
        
        self.config_manager = AlarmConfigManager()          # Gestor central con QSettings
        
        # Sistema de alarmas (solo monitorea lo que el técnico habilite)
        self.alarm_system = AlarmSystem(
            config_manager=self.config_manager
        )      


        self.alarm_system.alarm_changed.connect(self.handle_alarm)
        self.alarm_system.new_event.connect(self.log_event)
        self.alarm_system.start_monitoring()
        self.active_alarms: List[Tuple[str, float, str]] = [] # La lista activa que usa el header label
        self.buzzer_silenced_by_user = False   

        self.led_bar = LedBarController()     
        self.led_bar.start()
        # ====================== PANTALLAS ======================
        
        self.alarms_screen = AlarmsScreen(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )
        self.alarms_screen.request_boolean_change.connect(self._write_boolean_command) # Conexión: conecta la señal de pantalla con el método de escritura serial en main

        self.real_time_var = RealTimeVariablesMonitor(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        # Pantalla de configuración para Operador
        self.alarm_config_limits_screen = AlarmScreenConfig(
            config_manager=self.config_manager,
            parent=self
        )

        # Pantalla de configuración para Servicio Técnico
        self.alarm_service_screen_config = AlarmScreenServiceConfig(
            config_manager=self.config_manager,
            parent=self
        )
        # # Therapy & service screens        
        self.dialysis_screen = DialysisScreen(parent=self, values_dict=self.current_values)
        self.dialysis_screen.request_boolean_change.connect(self._write_boolean_command)

        self.treatment_mode_screen = TreatmentModeScreen(parent=self, values_dict=self.current_values)
        self.treatment_mode_screen.request_setpoint_change.connect(self._write_setpoint)  # Conexión: conecta la señal de pantalla con el método de escritura serial en main

        self.cleaning_screen = CleaningScreen(parent=self, values_dict=self.current_values)
        self.cleaning_screen.request_setpoint_change.connect(self._write_setpoint)
        self.cleaning_screen.request_boolean_change.connect(self._write_boolean_command)
        self.cleaning_screen.cleaning_active_changed.connect(self._handle_cleaning_status_change) 


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
        
        self.comm_port_screen = CommPortScreen(parent=self)
        self.comm_port_screen.config_changed.connect(self.handle_comm_config_change)

        self.maintenance_screen = MaintenanceScreen(parent=self)  # PANTALLA NUEVA DE MANTENIMIENTO 

        self._cleanning_config_screen = CleanningConfigScreen(parent=self)

        # # Therapy sub-screens
        self.patient_config_screen = PatientConfigScreen(parent=self)
        
        self.therapy_config_screen = TherapyConfigScreen(parent=self, values_dict=self.current_values) # intanciar pasando los valores actuales (values_dict)
        self.therapy_config_screen.request_setpoint_change.connect(self._write_setpoint) # Conexión: conecta la señal de pantalla con el método de escritura serial en main   
        self.therapy_config_screen.request_boolean_change.connect(self._write_boolean_command)     
        self.therapy_config_screen.valueChanged.connect(self.handleGlobalValueChange) # Actualizar UI localmente

        self.history_screen = HistoryScreen(parent=self)

        self.KTVScreen = KTVScreen(parent=self, values_dict=self.current_values) # Pantalla de cálculo de Kt/V en tiempo real, con gráficos y todo el rollo.

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
        self.screen_stack.addWidget(self.comm_port_screen)             # 13 
        self.screen_stack.addWidget(self.maintenance_screen)            # 14
        self.screen_stack.addWidget(self.alarm_config_limits_screen)          # 15  se accede desde el menu de alarmas para configurar los limites de cada variable y su severidad. Esta pantalla reemplaza a la antigua AlarmLimitsConfigDialog, integrando la configuración de alarmas dentro del flujo principal de la aplicación.
        self.screen_stack.addWidget(self.alarm_service_screen_config)          # 16  se accede desde el menu de servicio técnico para configurar los limites de cada variable y su severidad. Esta pantalla es similar a la de configuración de alarmas pero con un enfoque específico para el servicio técnico, permitiendo ajustes avanzados que no están disponibles para el operador.
        self.screen_stack.addWidget(self._cleanning_config_screen)             # 17 configuración de modos de limpieza/desinfeccion      
        self.screen_stack.addWidget(self.history_screen)              # 18 pantalla de historial de tratamientos y mantenimientos realizados, con opción de exportar a PDF o CSV.
        self.screen_stack.addWidget(self.KTVScreen)                   # 19 pantalla de cálculo de Kt/V en tiempo real, con gráficos y todo el rollo. Se accede desde el menú de Tipo de Tratamiento.


        self.master_timer.timeout.connect(self.KTVScreen.on_master_tick)

        self.comm_port_screen.emit_current_configurations() # carga la configuracion de las puertos COM

        self.calibration_screen.valueChanged.connect(self.handleGlobalValueChange)
        self.manual_mode_screen.valueChanged.connect(self.handleGlobalValueChange)

        self._update_priming_controls_state() 
        # Cargar horas persistentes
        self._load_operation_hours()
        self._load_power_on_hours()
        self._load_cleaning_hours()

        # Iniciar el Timer Maestro (único)
        self.master_timer.start()
        logger.info("Timer Maestro iniciado correctamente (intervalo 500ms)")

        # Header update timers
        self.refresh_alarms_label()
        self.refresh_treatment_selected()
        
        self.serial_comm.connect()
        self.serial_comm.start_reading()
        self._set_ui_connected_state(False)
        self.screen_stack.setCurrentIndex(self.INDEX_HOME)
        self.right_content.hide()
        self.left_content.hide()
        self.left_container.setStyleSheet("background: transparent")
        self.right_container.setStyleSheet("background: transparent")

    
    def _on_state_changed(self, phase: TreatmentPhase, reason: str):
        """Callback principal de cambio de estado"""
        logger.info(f"Estado global cambiado: {phase.name} | {reason}")
        self._update_buttons_state()
        self._update_screens_state(phase)

    def _on_treatment_started(self, start_time):
        logger.info("Tratamiento INICIADO")
        self.is_treatment_running = True
        self.therapy_start_time = start_time
        # Iniciar logger, bioz, etc. (ya lo tenés en start_treatment)

    def _on_treatment_paused(self):
        logger.info("Tratamiento PAUSADO")
        self.is_treatment_running = False

    def _on_treatment_resumed(self):
        logger.info("Tratamiento REANUDADO")
        self.is_treatment_running = True

    def _on_treatment_finished(self):
        logger.info("Tratamiento FINALIZADO")
        self.is_treatment_running = False
        self.therapy_start_time = None

    def _on_cleaning_started(self):
        logger.info("Limpieza INICIADA")
        self.is_cleaning_in_progress = True

    def _on_cleaning_finished(self):
        logger.info("Limpieza FINALIZADA")
        self.is_cleaning_in_progress = False

    def _on_state_error(self, message: str):
        logger.error(f"Error de estado: {message}")
        self.show_error_message(message, 4000)

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
        self.nav_bar = QWidget()
        self.nav_bar.setFixedSize(1560, 150)
        self.nav_bar.setStyleSheet("background: #FCFCFC;")

        nav_layout = QHBoxLayout(self.nav_bar)
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
            ("Historial",            "#0f172a", self.show_history_screen),
            ("Salir",               "#dc2626", self.close),
        ]

        for text, color, callback in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(110)           
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self.navigation_buttons[text] = btn

        self.main_layout.addWidget(self.nav_bar, 2, 1, 1, 4)

    # ────────────────────────────────────────────────
    #              Navigation Methods
    # ────────────────────────────────────────────────
    def start_treatment(self):
        logger.info("Iniciando tratamiento y mediciones externas: Bioimpedancia")
        status_code = int(self.current_values.get("primingProcessStatus", 0))
        hours = int(self.current_values.get("heparineTherapyHours", 0))
        minutes = int(self.current_values.get("heparineTherapyMinutes", 0))
        self.total_therapy_seconds = (hours * 3600) + (minutes * 60)

        if self.total_therapy_seconds <= 0:            
            self.show_warning_message("Configure duración de terapia", 3000)            
            self.show_therapy_config_screen()
            return
            
        current_status = int(self.current_values.get("primingProcessStatus", 0))        
        is_resuming = (current_status == 15)

        if not is_resuming:
            self.accumulated_therapy_seconds = 0
            self.current_treatment_start_date_time = QDateTime.currentDateTime()
            self.current_treatment_start = QDateTime.currentDateTime()
            self.operation_start_time = QDateTime.currentDateTime()   # ← Importante
            self.is_treatment_running = True
            self.show_info_message("Iniciando tratamiento...", 1000)
        else:
            self.show_info_message("Reanudando tratamiento...", 2000)
            self.last_resume_time = QDateTime.currentDateTime()

        self.last_resume_time = QDateTime.currentDateTime()

        try:        
            self._write_boolean_command("dialyModeOperationStart", True)            
            self._write_boolean_command("dialyModeOperationStop", False)
            logger.info("Comandos de terapia enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de terapia: {e}")           
            self.show_error_message(f"Error al iniciar terapia: {e}", 4000)

        # Iniciar bioimpedancia y Kt/V
        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("SRTB")
    
        # self.perform_ktv_measurement()

        if self.screen_stack.currentWidget() == self.dialysis_screen:
            self.dialysis_screen.update_values(self.current_values)        
        # =====================================================================
        # SOLUCIÓN AL BUG DEL LOGGER (MÚLTIPLES ARCHIVOS)
        # =====================================================================
        if is_resuming and self.treatment_logger is not None:
            # Si estamos reanudando y el logger ya existe, no hacemos NADA.
            logger.info("Reanudando tratamiento: Continuando registro en el mismo archivo CSV.")
        else:
            # Si es un tratamiento nuevo (no venimos de pausa) o el logger no existe:
            if self.treatment_logger:
                logger.info("Cerrando logger anterior antes de nuevo tratamiento")
                self.treatment_logger.close()
                self.treatment_logger = None

            LOG_DIRECTORY = "logs/tratamiento_hemodialisis"

            try:
                self.treatment_logger = CsvLogger(
                    log_directory=LOG_DIRECTORY,
                    parameter_key_map=self.parameter_mapping
                )
                logger.info("Logger CSV iniciado correctamente para nuevo tratamiento")
            except Exception as e:
                logger.error(f"Error al crear logger CSV para tratamiento: {e}")                
                self.show_error_message(f"Error crítico:\nNo se pudo iniciar el registro de datos:\n{str(e)}", 4000)
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
            
            self.show_warning_message("No hay conexión serial.\nCebado no iniciado.", 3000)
            logger.warning("Intento de iniciar cebado sin conexión serial")
            return

        # 2. Cerrar logger anterior si ya existe (evita duplicados/corrupción)
        if self.csv_logger:
            logger.info("Cerrando logger anterior antes de nuevo cebado")
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
            logger.info("Logger CSV iniciado correctamente para cebado")
        except Exception as e:
            logger.error(f"Error al crear logger CSV para cebado: {e}")
            
            
            self.show_error_message(f"Error crítico:\nNo se pudo iniciar el registro de datos:\n{str(e)}", 4000)
            return

        # 5. Enviar comandos al controlador
        try:
            self._write_boolean_command("dialyStartDialysisButt", True)
            self._write_boolean_command("dialyStopDialysisButt",False)
           
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}") 
            self.show_error_message(f"Error al enviar comandos de cebado:\n{str(e)}", 4000)


        self.show_success_message("Cebado iniciado", 3000)

        self.show_dialysis_screen()

    def stop_priming(self):
        try:
            self._write_boolean_command("dialyStopDialysisButt",True)
            self._write_boolean_command("dialyStartDialysisButt", False)              
           
            logger.info("Comandos de cebado enviados: Start=True, Stop=False")
            self.show_info_message("Cebado detenido...", 3000)
        except Exception as e:
            logger.error(f"Error enviando comandos de cebado: {e}")
            self.show_warning_message("Cebado detenido, pero hubo problema al enviar comandos al controlador.", 4000)
            
        if self.csv_logger:
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")


    def stop_treatment(self):   
        try:            
            self._write_boolean_command("dialyModeOperationStop", True)
            self._write_boolean_command("dialyModeOperationStart", False)                   
            self.show_info_message("Fin de terapia...", 3000)
            self.register_treatment_session()   # Registrar sesión en el historial (JSON) y guardar resumen CSV de tratamientos
        except Exception as e:
            logger.error(f"Error enviando comandos de paro de terapia: {e}") 

        if self.bioz_urea_controller:
            self.bioz_urea_controller.send_command("STOP")

        # Resetear estado de tiempo       
        self._pause_operation_timer()

        self.is_treatment_running = False
        self.accumulated_therapy_seconds = 0  # Limpiar
        self.last_resume_time = None          # Limpiar

        # Actualizar displays inmediatamente
        self._update_therapy_time_displays()
        if hasattr(self, 'KTVScreen') and self.KTVScreen:
            report = self.KTVScreen.save_final_report()
            if report:
                self.show_success_message(f"Reporte Kt/V guardado correctamente", 2000)
            self.KTVScreen.ktv_records.clear()   # Limpiar para próxima terapia
        # Cerrar logger si existe
        if self.treatment_logger:
            self.treatment_logger.close()
            self.treatment_logger = None
            logger.info("Sesión detenida - logger cerrado")


    def pause_treatment(self):
        try:
            self._write_boolean_command("dialyModeOperationPause", True)
            self.show_info_message("Terapia en pausa...", 1500)
            self._pause_operation_timer()
            self.is_treatment_running = False
        except Exception as e:
            logger.error(f"[Error] Error al pausar terapia {e}")
        
    def _save_treatment_summary_csv(self):
        """Guarda un registro simple con Fecha, Hora de Inicio y Hora de Fin del tratamiento."""
        if not self.current_treatment_start_date_time:
            return  # No hay tratamiento registrado
 

        end_time = QDateTime.currentDateTime()
        date_str = self.current_treatment_start_date_time.toString("yyyy-MM-dd")
        start_str = self.current_treatment_start_date_time.toString("HH:mm:ss")
        end_str = end_time.toString("HH:mm:ss")

        os.makedirs("logs", exist_ok=True)
        filepath = "logs/historial_tratamientos.csv"
        file_exists = os.path.isfile(filepath)

        try:
            with open(filepath, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Si el archivo es nuevo, escribir encabezados
                if not file_exists:
                    writer.writerow(["Fecha", "Hora_Inicio", "Hora_Fin"])
                
                # Escribir los datos del tratamiento
                writer.writerow([date_str, start_str, end_str])
            logger.info(f"Resumen de tratamiento guardado: {date_str} de {start_str} a {end_str}")
        except Exception as e:
            logger.error(f"Error al guardar el historial de tratamientos CSV: {e}")

        # Limpiar la variable para el próximo tratamiento
        self.current_treatment_start_date_time = None


    def end_dialysis_session(self):
        if self.csv_logger:
            self.csv_logger.close()
            self.csv_logger = None
            logger.info("Sesión detenida - logger cerrado")

        if self.treatment_logger:
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
        if hasattr(self.cleaning_screen, "reset_cleaning_mode_selection"):
            self.cleaning_screen.reset_cleaning_mode_selection(reset_display=True)
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
        self._highlight_active_nav_button("Servicio")

    def show_test_panel_screen(self):
        self.screen_stack.setCurrentWidget(self.test_panel_screen)
        if hasattr(self.test_panel_screen, "update_values"):
            self.test_panel_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_calibration_screen(self):
        self.screen_stack.setCurrentWidget(self.calibration_screen)
        if hasattr(self.calibration_screen, "update_values"):
            self.calibration_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_network_config_screen(self):
        self.screen_stack.setCurrentWidget(self.network_config_screen)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_real_time_var_screen(self):
        self.screen_stack.setCurrentWidget(self.real_time_var)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_patient_config_screen(self):
        self.screen_stack.setCurrentWidget(self.patient_config_screen)
        if hasattr(self.patient_config_screen, "update_values"):
            self.patient_config_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Diálisis")

    def show_therapy_config_screen(self):
        self.screen_stack.setCurrentWidget(self.therapy_config_screen)
        if hasattr(self.therapy_config_screen, "update_values"):
            self.therapy_config_screen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Diálisis")
    
    def show_config_comm_screen(self):
        self.screen_stack.setCurrentWidget(self.comm_port_screen)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")

    def show_maintenance_screen(self):
        """Muestra la pantalla de mantenimiento y actualiza inmediatamente los valores"""
        self.screen_stack.setCurrentWidget(self.maintenance_screen)
        self.left_content.show()
        self.right_content.show()
        self._update_maintenance_screen_immediately()        
        self._highlight_active_nav_button("Servicio")

    def show_alarm_config_limits_screen(self):
        self.screen_stack.setCurrentWidget(self.alarm_config_limits_screen)
        self.alarm_config_limits_screen.refresh_ui() 
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Alarmas")

    def show_alarm_service_screen_config(self):
        self.screen_stack.setCurrentWidget(self.alarm_service_screen_config)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Servicio")
    
    def show_cleanning_config_screen(self):
        self.screen_stack.setCurrentWidget(self._cleanning_config_screen)
        self.left_content.show()
        self.right_content.show()
        if hasattr(self._cleanning_config_screen, '_load_config_for_display'):
            self._cleanning_config_screen._load_config_for_display()    
            self._highlight_active_nav_button("Servicio")

    def show_history_screen(self):
        self.screen_stack.setCurrentWidget(self.history_screen)
        self.history_screen.refresh_data()
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Historial")

    def show_ktv_screen(self):
        self.screen_stack.setCurrentWidget(self.KTVScreen)
        if hasattr(self.KTVScreen, "update_values"):
            self.KTVScreen.update_values(self.current_values)
        self.left_content.show()
        self.right_content.show()
        self._highlight_active_nav_button("Diálisis")



    # ────────────────────────────────────────────────
    #              Utility Methods
    # ────────────────────────────────────────────────


    def _master_timer_tick(self):
        """Timer Maestro - Se ejecuta cada 500ms. Actualizacion centralizada de estados, gauges, loggers y navegación."""
        if self._timer_lock:
            logger.warning("Timer tick saltado por lock")
            return
        self._timer_lock = True 
        # cambios nuevos - se agrego _timer_lock y Try, si no funcionan se quitan 
        try:
            now = QDateTime.currentDateTime()
            self.update_connection_status()

            if self.is_treatment_running:
                self._update_therapy_time_displays()

            # Actualizaciones cada 1 segundo
            delta_msecs = self.last_second_update.msecsTo(now)

            if delta_msecs >= 1000:            
                self.last_second_update = now
                self.update_date_time()
            
                hours_passed = delta_msecs / 3600000.0       
                # 1. Power On Hours → Siempre cuenta
                self.power_on_hours += hours_passed

                # 2. Operation Hours → Solo cuando el tratamiento está realmente activo
                if self.is_treatment_running and self.operation_start_time is not None:
                    self.total_operation_hours += hours_passed

                # 3. Cleaning Hours
                if self.is_cleaning_in_progress and self.cleaning_start_time is not None:
                    self.cleaning_hours += hours_passed

                # Logging
                if self.treatment_logger:
                    self._log_treatment_current_data()
                if self.csv_logger:           # cebado
                    self._log_current_data()
                if self.cleaning_logger:      # ← NUEVO: logger de limpieza
                    self._log_cleaning_current_data()

            # Cada minuto
            if self.last_minute_update.secsTo(now) >= 60:
                self.last_minute_update = now
            
                self._save_power_on_hours()
                self._save_operation_hours()
                self._save_cleaning_hours()

                if self.screen_stack.currentWidget() == self.maintenance_screen:
                    self._update_maintenance_screen_immediately()
        
            self._update_gauges()
            self._update_treatment_controls_state()
            self._update_priming_controls_state()
            self._refresh_navigation_bar()
        finally:
            self._timer_lock = False



    # ============================================================
    # MÉTODOS DE NAVEGACIÓN MEJORADOS
    # ============================================================

    def _get_current_screen_nav_text(self) -> str:
        """Devuelve el texto del botón de navegación correspondiente a la pantalla actual."""
        current = self.screen_stack.currentWidget()

        mapping = {
            self._main_screen: "Inicio",
            self.dialysis_screen: "Diálisis",
            self.treatment_mode_screen: "Tipo de\nTratamiento",
            self.cleaning_screen: "Limpieza",
            self.options_screen: "Servicio",
            self.alarms_screen: "Alarmas",
            self.history_screen: "Historial",
            self.KTVScreen: "Diálisis",                    # ← Importante
            self.patient_config_screen: "Diálisis",
            self.therapy_config_screen: "Diálisis",
        }

        # Pantallas de servicio
        service_screens = {
            self.manual_mode_screen, self.test_panel_screen,
            self.calibration_screen, self.network_config_screen,
            self.comm_port_screen, self.maintenance_screen,
            self._cleanning_config_screen, self.alarm_service_screen_config
        }

        if current in mapping:
            return mapping[current]
        if current in service_screens:
            return "Servicio"
    
        return ""


    def _highlight_active_nav_button(self, active_button_text: str):
        """Resalta el botón activo y restaura el resto."""
        if not active_button_text:
            return

        for text, btn in self.navigation_buttons.items():
            if text == active_button_text:
                btn.setStyleSheet(self.BTN_ACTIVE_STYLE)
            elif text in ["Inicio", "Diálisis", "Tipo de\nTratamiento", 
                          "Limpieza", "Servicio", "Alarmas", "Historial"]:
                # Solo restauramos estilo si el botón está habilitado
                if btn.isEnabled():
                    btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)

    # def _highlight_active_nav_button(self, active_button_text: str):
    #     """
    #     Resalta el botón de navegación correspondiente a la pantalla activa
    #     y restablece el estilo de los demás botones.
    #     """
    #     # Lista de textos de botones que representan pantallas navegables
    #     screen_buttons = ["Inicio", "Diálisis", "Tipo de\nTratamiento", "Limpieza", "Servicio", "Alarmas","Historial"]

    #     for btn_text, btn in self.navigation_buttons.items():
    #         # Solo procesamos botones de pantalla que estén habilitados
    #         if btn_text in screen_buttons and btn.isEnabled():
    #             if btn_text == active_button_text:
    #                 btn.setStyleSheet(self.BTN_ACTIVE_STYLE)
    #             else:
    #                 btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
    #         # Los botones "Iniciar Tratamiento" y "Salir" se mantienen con sus estilos
    #         # específicos definidos en _set_ui_connected_state o directamente.
    #         # Los botones deshabilitados mantienen su BTN_DISABLED_STYLE.

    def _refresh_navigation_bar(self):
        """
        Solo habilita/deshabilita botones.
        NO debe cambiar estilos de resaltado (eso lo hace _highlight_active_nav_button).
        """
        is_connected = self.serial_comm and self.serial_comm.is_connected

        if not is_connected:
            for text, btn in self.navigation_buttons.items():
                if text == "Salir":
                    btn.setEnabled(True)
                    btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE)
                elif text == "Servicio":
                    btn.setEnabled(True)
                    btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
                else:
                    btn.setEnabled(False)
                    btn.setStyleSheet(self.BTN_DISABLED_STYLE)
            return

        # Estados actuales
        status_code = int(self.current_values.get("primingProcessStatus", 0))
        treatment_mode = int(self.current_values.get("treatmentModeSelection", 0))

        is_cleaning_active = getattr(self, 'is_cleaning_in_progress', False)
        in_treatment = (status_code in (14, 15)) or getattr(self, 'is_treatment_running', False)

        for text, btn in self.navigation_buttons.items():
            if text == "Salir":
                enabled = not in_treatment and not is_cleaning_active
                btn.setEnabled(enabled)
                btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE if enabled else self.BTN_DISABLED_STYLE)
                continue

            if text == "Iniciar\nTratamiento":
                continue  # Se maneja en _update_treatment_controls_state()

            if text == "Alarmas":
                btn.setEnabled(True)
                continue

            if text == "Limpieza":
                enabled = (treatment_mode == 3)
            elif in_treatment:
                enabled = (text == "Diálisis")
            elif is_cleaning_active:
                enabled = (text in ["Limpieza", "Alarmas"])
            else:
                enabled = True

            btn.setEnabled(enabled)

            # Solo aplicamos estilo por defecto si NO está activo
            if enabled and text != self._get_current_screen_nav_text():
                btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
            elif not enabled:
                btn.setStyleSheet(self.BTN_DISABLED_STYLE)

    # def _refresh_navigation_bar(self):
    #     """
    #     Habilita o deshabilita los botones de navegación según el estado actual del sistema.
    #     - Si no hay conexión serial, solo "Salir" está habilitado.
    #     - Si hay conexión, se habilitan/deshabilitan botones según el modo de tratamiento y estado de limpieza.
    #     - "Alarmas" siempre está habilitado por seguridad.
    #     - "Iniciar Tratamiento" tiene reglas especiales basadas en temperatura, conductividad y modo de tratamiento.
    #     """

    #     is_conected = self.serial_comm and self.serial_comm.is_connected

    #     # =========================== SIN CONEXIÓN ===========================
    #     if not is_conected:
    #         for text, btn in self.navigation_buttons.items():
    #             if text == "Salir":
    #                 btn.setEnabled(True)
    #                 btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE)
    #             elif text == "Servicio":
    #                 btn.setEnabled(True)  # Permitir acceso a opciones de servicio incluso sin conexión
    #                 btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
    #             else:
    #                 btn.setEnabled(False)
    #                 btn.setStyleSheet(self.BTN_DISABLED_STYLE)
    #         return

    #     # =========================== ESTADOS ===========================  

    #     treatment_mode = int(self.current_values.get("treatmentModeSelection", 0))
    #     status_code = int(self.current_values.get("primingProcessStatus", 0))

    #     is_cleaning_mode = (treatment_mode == 3)
    #     is_cleaning_active = is_cleaning_mode and getattr(self, 'is_cleaning_in_progress', False)
    #     in_treatment_active = (status_code == 14 or getattr(self, 'is_treatment_running', False))

    #     active_screen_text = self._get_current_screen_nav_text()

    #     # =========================== PROCESAR CADA BOTÓN ===========================

    #     for text, btn in self.navigation_buttons.items():
    #         # ==================== SALIR ====================
    #         if text == "Salir":
    #             enabled = not in_treatment_active and not is_cleaning_active
    #             btn.setEnabled(enabled)
    #             btn.setStyleSheet(self.BTN_ENABLED_EXIT_STYLE if enabled else self.BTN_DISABLED_STYLE)
    #             continue
    #         # ==================== INICIAR TRATAMIENTO ====================
    #         if text == "Iniciar\nTratamiento":
    #             # DELEGAR COMPLETAMENTE a _update_treatment_controls_state()
    #             continue
            
    #         # ==================== LIMPIEZA ====================
    #         if text == "Limpieza":
    #             enabled = is_cleaning_mode  # Solo habilitado cuando modo == 3
    #             btn.setEnabled(enabled)                
    #             if enabled and text == active_screen_text:
    #                 btn.setStyleSheet(self.BTN_ACTIVE_STYLE)
    #             else:
    #                 btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE if enabled else self.BTN_DISABLED_STYLE)
    #             continue
    #         # ==================== ALARMAS (Siempre accesible) ====================
    #         if text == "Alarmas":
    #             btn.setEnabled(True)
    #             if text == active_screen_text:
    #                 btn.setStyleSheet(self.BTN_ACTIVE_STYLE)
    #             else:
    #                 btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
    #             continue
    #         # ==================== RESTO DE BOTONES ====================
    #         if is_cleaning_active:
    #             enabled = False  # Solo Alarmas + Limpieza están disponibles    
    #         elif in_treatment_active:
    #             enabled = (text == "Diálisis")  # Solo Diálisis + Alarmas   
    #         else:
    #             enabled = True  # Todos habilitados en estado normal

    #         btn.setEnabled(enabled)

    #         # Aplicar estilos
    #         if enabled and text == active_screen_text:
    #             btn.setStyleSheet(self.BTN_ACTIVE_STYLE)    
    #         elif enabled:
    #             btn.setStyleSheet(self.BTN_ENABLED_DEFAULT_STYLE)
    #         else:
    #             btn.setStyleSheet(self.BTN_DISABLED_STYLE)

    def _set_ui_connected_state(self, is_connected: bool):
        """
        Manages the overall UI state based on connection status.
        Protege al usuario si está en pantallas de configuración.
        """
        # --- NUEVA LÓGICA DE PROTECCIÓN ---
        current_widget = self.screen_stack.currentWidget()
        # Definimos las pantallas donde NO queremos que el sistema nos saque automáticamente
        service_screens = [self.comm_port_screen, self.options_screen, self.maintenance_screen, self.network_config_screen]
        is_in_service_area = current_widget in service_screens
        # ----------------------------------

        if is_connected:
            logger.info("Enabling UI elements for connected state.")
            
            if hasattr(self, 'alarm_system') and self.alarm_system:
                self.alarm_system.reset()
            self.active_alarms.clear()
            
            if hasattr(self, 'alarms_screen') and self.alarms_screen:
                self.alarms_screen.reset_ui_state() 
            
            self.current_process_status.setText("Máquina conectada") 
            self.refresh_treatment_selected()

            # Solo mandamos al Home si NO estamos en área de servicio
            if not is_in_service_area:
                self.show_home_screen() 
            else:
                logger.info("Manteniendo pantalla de servicio tras conexión.")

            
            

        else: # ESTADO DESCONECTADO
            logger.warning("Disabling UI elements for disconnected state.")
            
            if hasattr(self, 'alarm_system') and self.alarm_system:
                self.alarm_system.reset() 
            self.active_alarms.clear() 
            
            if hasattr(self, 'alarms_screen') and self.alarms_screen:
                self.alarms_screen.reset_ui_state() 

            self.current_process_status.setText("Esperando conexión")
            
            # --- CORRECCIÓN CRÍTICA AQUÍ ---
            # Antes esto no tenía protección y te mandaba a Home siempre al desconectarse
            if not is_in_service_area:
                self.show_home_screen()
            else:
                logger.info("Manteniendo pantalla de servicio tras desconexión (permitiendo configuración).")


    def _handle_cleaning_status_change(self, is_cleaning_active: bool):
        """Maneja el cambio de estado de limpieza"""
        logger.info(f"[CLEANING] Señal recibida → Activo: {is_cleaning_active}")

        if is_cleaning_active and not self.is_cleaning_in_progress:
            # === INICIO DE LIMPIEZA ===
            self.is_cleaning_in_progress = True
            self.cleaning_start_time = QDateTime.currentDateTime()   # Variable principal para conteo
            
            self._start_cleaning_logger()
            logger.info(f"🧼 Limpieza INICIADA a las {self.cleaning_start_time.toString('HH:mm:ss')}")

        elif not is_cleaning_active and self.is_cleaning_in_progress:
            # === FINAL DE LIMPIEZA ===
            self.is_cleaning_in_progress = False
            
            if self.cleaning_start_time is not None:
                elapsed_hours = self.cleaning_start_time.secsTo(QDateTime.currentDateTime()) / 3600.0
                logger.info(f"🧼 Limpieza finalizada - Duración: {elapsed_hours:.3f} horas")

            # Registrar en historial (importante)
            self.register_cleaning_session()     # ← Se mantiene intacto
            
            self._stop_cleaning_logger()
            self._save_cleaning_hours()
            
            logger.info("✅ Limpieza finalizada y registrada correctamente")

            # Limpiar variable
            self.cleaning_start_time = None

        # NO es necesario llamar _refresh_navigation_bar() aquí
    def handleGlobalValueChange(self, tag: str, value: float):
       
        self.current_values[tag] = value  # Actualiza el valor global
        print(f"[GLOBAL] Valor actualizado: {tag} = {value}")  # Log para depuración
        
        # Opcional: Notifica a las pantallas para que se actualicen
        # for screen in [self.therapy_config_screen, self.calibration_screen, self.test_panel_screen, self.manual_mode_screen,self.alarms_screen,self.real_time_var]:  # Agrega todas las pantallas
        for screen in [self.therapy_config_screen, self.calibration_screen, self.test_panel_screen, self.manual_mode_screen,self.alarms_screen,self.real_time_var, self.cleaning_screen, self._cleanning_config_screen,
                       self.patient_config_screen, self.therapy_config_screen, self.maintenance_screen, self.dialysis_screen, self.treatment_history,self.treatment_mode_screen]:  # Agrega todas las pantallas relevantes
            if hasattr(screen, 'update_values'):
                screen.update_values(self.current_values)  # Llama al update en cada pantalla

    def update_date_time(self):
        from datetime import datetime
        self.date_time_label.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))    

    def update_value(self, tag: str, value: float):        
        # 1. Pre-procesamiento y conversión de unidades ANTES de guardar o enviar a alarmas
        if tag == "dialyCondControlOutput":
            value = value / 5.0

        elif tag == "ultraFilterPumpSpeed":
            try:
                # Convertimos directamente el 'value' entrante (ml/min -> L/h)
                value = convertir_ml_min_a_litros_h(value)   
            except Exception as e:
                logger.error(f"Error converting UF flow: {e}")   

        elif tag == "balanceChamberSetTiming":            
            try:
                # Convertimos directamente el 'value' entrante (ciclos -> ml/min)
                value = convertir_ciclos_a_flujo(value)                                
            except Exception as e:
                logger.error(f"Error converting CB flow: {e}")

        # 2. Actualizar el valor centralizado (Ya convertido de manera segura)
        self.current_values[tag] = value
                
        # Actualizar sistema de alarmas si existe
        if self.alarm_system:
            self.alarm_system.update_value_by_tag(tag, value)

        # Manejo del tratamiento seleccionado
        if tag == "treatmentModeSelection":
            self.refresh_treatment_selected() # Llama al nuevo método para actualizar el label
        # ────────────────────────────────────────────────────────────────
        # Manejo de primingProcessStatus (estado del proceso + horas de operación)
        # ────────────────────────────────────────────────────────────────
        if tag == "primingProcessStatus":
            status_code = int(value)

            if status_code != self._last_priming_status:
                logger.info(f"Cambio de estado detectado: {self._last_priming_status} → {status_code}")
                self._last_priming_status = status_code

                # Mapa de estados
                status_map = {
                    1: "INICIO CEBADO", 2: "LLENADO DE TANQUE", 3: "LLENADO DE LINEA",
                    4: "LLENADO CÁMARA", 5: "CALENTAMIENTO", 6: "INFUSIÓN",
                    7: "COLOCACIÓN DE\nFILTRO", 8: "DIÁLISIS", 9: "BYPASS", 10: "CERRADO",
                    12: "ULTRAFILTRACIÓN OFF", 13: "LISTO PARA INICIAR\nTRATAMIENTO",
                    14: "TRATAMIENTO INICIADO", 15: "PAUSA", 16: "TRATAMIENTO\n DETENIDO"
                }
                status_text = status_map.get(status_code, f"Espera.. ({status_code})")
                self.current_process_status.setText(status_text)

                if status_code == 7: # indica al usuario que debe colocar el filtro antes de iniciar el tratamiento
                    self.show_info_message("Coloque el filtro y conecte las líneas", 10000)                  

                                # ====================== LÓGICA DE HORAS ======================
                if status_code == 14:  # TRATAMIENTO INICIADO / ACTIVO
                    if not self.is_treatment_running:
                        self.is_treatment_running = True
                        if self.operation_start_time is None:
                            self.operation_start_time = QDateTime.currentDateTime()
                            logger.info("▶️ Iniciando conteo de horas de operación (Tratamiento)")

                elif status_code in [15, 16]:  # PAUSA o DETENIDO
                    if self.is_treatment_running:
                        self.is_treatment_running = False
                        self._pause_operation_timer()  # Guarda y limpia timer
                        logger.info(f"⏸️ Tratamiento pausado/detenido. Horas op: {self.total_operation_hours:.3f}h")

                # Lógica de pausa de tiempo de terapia
                if status_code == 15 and self.last_resume_time is not None:
                    seconds_since_resume = self.last_resume_time.secsTo(QDateTime.currentDateTime())
                    self.accumulated_therapy_seconds += seconds_since_resume
                    self.last_resume_time = None

                elif status_code == 14 and self.last_resume_time is None:
                    self.last_resume_time = QDateTime.currentDateTime()

                # Colores según estado
                if status_code in [6, 7, 13, 14]:
                    color = "#25AD37"
                elif status_code in [1, 2, 3, 4, 5, 8]:
                    color = "#eab308"
                elif status_code in [15, 16]:
                    color = "#ef4444"
                else:
                    color = "#C6E3E6"

                self.current_process_status.setStyleSheet(f"""
                    QLabel {{
                        color: #ffffff;
                        background: {color};
                        font-weight: bold;
                        font-size: 25px;
                        border-radius: 10px;
                    }}
                """)
                

                # Actualizar inmediatamente la pantalla de mantenimiento si está visible
                if self.screen_stack.currentWidget() == self.maintenance_screen:
                    self._update_maintenance_screen_immediately()   

   
    def _update_gauges(self):
        
        gauge_mapping = {
            "bloodArteryPressureData":   self.arterial_pressure_gauge,
            "bloodVenousPressureData":   self.venous_pressure_gauge,
            "dialyTempIFProcessData":  self.dialysate_temp_gauge,
            "dialyCondVariableData":  self.conductivity_bar,
        }
        for tag, gauge in gauge_mapping.items():
            if gauge is not None:
                value = self.current_values.get(tag, 0.0)
                try:
                    gauge.setValue(value)
                except Exception as e:
                    logger.error(f"Error actualizando gauge {tag}: {e}")
   

    def _update_treatment_controls_state(self):
        """
        Calcula si se puede iniciar o detener tratamiento y actualiza
        TANTO la barra de navegación COMO la pantalla de diálisis.
        """
        # 1. Obtener valores necesarios  
        status_code = int(self.current_values.get("primingProcessStatus", 0))
        temp_actual = self.current_values.get("dialyTempIFProcessData", 0.0)     # dialyTempVariableData anterior
        temp_set    = self.current_values.get("dialyTempControlSetPoint", 0.0)   # Setpoint de temperatura
        cond_actual = self.current_values.get("dialyCondVariableData", 0.0)      # conductividad actual   
        cond_set    = self.current_values.get("dialyCondControlSetPoint", 0.0)   # Setpoint de conductividad
        treatment_mode_selection = self.current_values.get("treatmentModeSelection", 0.0)
        
        # 2. Lógica de validación (Tolerancias)
        temp_ok = (temp_actual - temp_set <= 2.0) and (temp_set - temp_actual <= 5.0)
        cond_ok = abs(cond_actual - cond_set) <= 2.0
        
        # 3. Determinar qué botones deben estar activos
        can_start = False
        can_stop = False
        can_pause = False

        if treatment_mode_selection == 3.0: # Si el modo seleccionado es "Limpieza"
            pass  # Para limpieza, no aplicamos esta lógica de habilitación de tratamiento. Se maneja por separado en _handle_cleaning_status_change.
        elif status_code == 13:  #13 LISTO PARA INICIAR
            can_start = temp_ok and cond_ok
            can_stop = False
            can_pause = False
        elif status_code == 14: # TRATAMIENTO CORRIENDO
            can_start = False
            can_stop = True
            can_pause = True
        elif status_code == 15:  # estado de pausa 
            if temp_ok and cond_ok:
                can_start = True      # Reanudar
                can_stop = True
                can_pause = False     # Ya estamos en pausa
            else:
                # Parámetros no óptimos → solo permitir detener
                can_start = False
                can_stop = True
                can_pause = False

        else: # CUALQUIER OTRO ESTADO (Cebado, Pausa, etc)
            can_start = False
            can_stop = False
            can_pause = False

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
                self.dialysis_screen.set_start_stop_buttons_state(can_start, can_stop, can_pause)

        
        


    def _update_priming_controls_state(self):
        """
        Calcula el estado de los botones de cebado ('INICIAR CEBADO', 'DETENER CEBADO')
        basándose en 'primingProcessStatus' y los actualiza en la DialysisScreen.
        """
        status_code = int(self.current_values.get("primingProcessStatus", 0))
        treatment_mode_selection = int(self.current_values.get("treatmentModeSelection", 0))

        enable_start_priming = False # Inicializa a False por defecto
        enable_stop_priming = False  # Inicializa a False por defecto

        if treatment_mode_selection != 3.0: 
            if status_code == 1: 
                enable_start_priming = True
            
            if 2 <= status_code <= 9:
                enable_stop_priming = True
            elif status_code == 13: 
                enable_stop_priming = True    
            elif status_code == 14: 
                enable_stop_priming = False 
            elif status_code in [15, 16]: 
                enable_stop_priming = True

            if status_code in [1, 10]: 
                 enable_stop_priming = False

        # Actualizar los botones en la pantalla de diálisis
        if hasattr(self, 'dialysis_screen') and self.dialysis_screen:
            if hasattr(self.dialysis_screen, 'set_priming_buttons_state'):
                self.dialysis_screen.set_priming_buttons_state(enable_start_priming, enable_stop_priming)

    def refresh_alarms_label(self):
        """
        Actualiza el QLabel del encabezado con la alarma de mayor prioridad.
        Si no hay conexión, muestra un estado adecuado.
        """      
        if not self.serial_comm or not self.serial_comm.is_connected:
            self.active_alarms_label.setText("SIN CONEXIÓN\n DE CONTROL")
            self.active_alarms_label.setStyleSheet("""
                QLabel { color: #ffffff; background: #f39c12; font-weight: bold; font-size: 20px; border-radius: 8px; }
            """)
            return

        if not self.active_alarms:
            self.active_alarms_label.setText("ESTADO: OK")
            self.active_alarms_label.setStyleSheet("""
                QLabel { color: #ffffff; background: #10b981; font-weight: bold; font-size: 22px; border-radius: 8px; }
            """)
            return

        # Orden de prioridad (rojo > naranja > amarillo > cian)
        priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
        top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
        name, value, level = top_alarm

        short_label = name 
        is_boolean = False

        for group in VARIABLES.values():
            if isinstance(group, dict):
                for info in group.values():
                    if info.get("name") == name:
                        short_label = info.get("label", name) 
                        if info.get("type") == "bool":
                            is_boolean = True
                        break

        display_text = short_label.upper()
        if not is_boolean and value is not None and isinstance(value, (int, float)):
            display_text += f" {value:.1f}"


        color_map = {"rojo": "#dc2626", "naranja": "#f97316", "amarillo": "#eab308", "cian": "#06b6d4"}
        bg_color = color_map.get(level, "#1e293b")

        self.active_alarms_label.setText(display_text)
        self.active_alarms_label.setStyleSheet(f"""
            QLabel {{ background: {bg_color}; color: #ffffff; font-weight: bold; font-size: 22px; border-radius: 8px; }}
        """)                                         


    def refresh_treatment_selected(self):
        mode_code = int(self.current_values.get("treatmentModeSelection", 0)) 
        mode_text = self._treatment_map.get(mode_code, "Desconocido") 
        self.treatment_mode_selected.setText(mode_text.upper()) 
        self.treatment_mode_selected.setStyleSheet("""
            QLabel { color: #ffffff; background: #1E4573; font-weight: bold; font-size: 25px; }
        """)

    def update_alarm_system_monitor_config(self):
        """
        Llamado al cambiar la configuración de monitoreo en la pantalla de servicio.
        """
        logger.info("Actualizando configuración del sistema de alarmas desde HMI (Recarga Solicitada).")        
        # 1. Limpieza forzada de la interfaz
        self.active_alarms.clear()
        if hasattr(self, 'alarms_screen') and self.alarms_screen:
            self.alarms_screen.reset_ui_state()
            
        # 2. Recargar motor de alarmas
        self.alarm_system.reload_configuration()
        
        # 3. Refrescar interfaz visual
        self.refresh_alarms_label()
        self.update_led_bar_state()

    
    def handle_alarm(self, idx, active, value, name, level, limits):
        found_idx = -1 # buscar si la alarma ya está en la lista de alarmas activas
        for i, (alarm_name, _, _) in enumerate(self.active_alarms):
            if alarm_name == name:
                found_idx = i
                break

        if active:
            if found_idx == -1:
                # Es una alarma NUEVA que se acaba de activar -> añadir
                self.active_alarms.append((name, value, level))
                self.buzzer_silenced_by_user = False # Resetear silencio por NUEVA alarma
            else:
                # La alarma ya estaba activa, solo actualizar su estado (valor/nivel)
                self.active_alarms[found_idx] = (name, value, level)
        else:
            if found_idx != -1:
                # La alarma se normalizó -> eliminar de la lista de activas
                self.active_alarms.pop(found_idx)
        
        # Si no quedan alarmas activas, resetear el silencio del buzzer
        if not self.active_alarms:
            self.buzzer_silenced_by_user = False

        self.refresh_alarms_label()
        self.update_led_bar_state()

    # ────────────────────────────────────────────────
    #              LED Bar Logic
    # ────────────────────────────────────────────────

    def update_led_bar_state(self):
        """Actualiza el estado de la barra LED según las alarmas activas"""
        if not hasattr(self, 'led_bar') or self.led_bar is None:
            return  # Evita error si aún no se ha creado o ya se cerró

        if not self.serial_comm or not self.serial_comm.is_connected:
            self.led_bar.send_state(self.led_bar.CMD_CYAN_SOLID, silence_buzzer=False)
            return

        if self.active_alarms:
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            level = top_alarm[2]

            if level == "rojo":
                cmd = self.led_bar.CMD_RED_SOLID
            elif level == "naranja":
                cmd = self.led_bar.CMD_YELLOW_FLASH
            elif level == "amarillo":
                cmd = self.led_bar.CMD_YELLOW_SOLID
            else:  # cian o default
                cmd = self.led_bar.CMD_CYAN_SOLID

            silence = self.buzzer_silenced_by_user
            self.led_bar.send_state(cmd, silence_buzzer=silence)
        else:
            self.led_bar.send_state(self.led_bar.CMD_GREEN_SOLID, silence_buzzer=False)

#==============================inicio de codigo de prueba========================

    def show_operator_message(self, text: str, level: str = "info", timeout_ms: int = 4000):
        """
        Muestra un mensaje al operador con:
        - Mensaje flotante
        - LED + Buzzer temporal
        - Restauración automática del estado de alarma (si existe)
        """
        # Guardar estado actual de alarmas antes de modificar
        had_active_alarms = len(self.active_alarms) > 0
        previous_cmd = None

        if had_active_alarms:
            # Guardamos el comando actual de alarma para restaurarlo después
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            level_alarm = top_alarm[2]

            if level_alarm == "rojo":
                previous_cmd = self.led_bar.CMD_RED_SOLID
            elif level_alarm == "naranja":
                previous_cmd = self.led_bar.CMD_YELLOW_FLASH
            elif level_alarm == "amarillo":
                previous_cmd = self.led_bar.CMD_YELLOW_SOLID
            else:
                previous_cmd = self.led_bar.CMD_CYAN_SOLID

        # Determinar comando y estilo según el nivel del mensaje
        if level == "success":
            self.show_success_message(text, timeout_ms)
            cmd = getattr(self.led_bar, 'CMD_GREEN_SOLID', None)
        elif level == "warning":
            self.show_warning_message(text, timeout_ms)
            cmd = getattr(self.led_bar, 'CMD_YELLOW_FLASH', None)
        elif level == "error":
            self.show_error_message(text, timeout_ms)
            cmd = getattr(self.led_bar, 'CMD_RED_SOLID', None)
        else:  # info
            self.show_info_message(text, timeout_ms)
            cmd = getattr(self.led_bar, 'CMD_CYAN_SOLID', None)

        # Enviar comando al LED Bar + Buzzer activo
        if hasattr(self, 'led_bar') and self.led_bar and cmd:
            self.led_bar.send_state(cmd, silence_buzzer=False)

        # Restaurar estado de alarma después del timeout
        def restore_alarm_state():
            if hasattr(self, 'led_bar') and self.led_bar:
                if had_active_alarms and previous_cmd:
                    self.led_bar.send_state(previous_cmd, 
                                          silence_buzzer=self.buzzer_silenced_by_user)
                else:
                    # No había alarma → volver a verde o estado normal
                    self.led_bar.send_state(self.led_bar.CMD_GREEN_SOLID, 
                                          silence_buzzer=False)
            self.update_led_bar_state()  # Forzar sincronización con sistema de alarmas

        QTimer.singleShot(timeout_ms, restore_alarm_state)   


# # En lugar de:
# self.show_info_message("Cebado iniciado", 3000)

# # Usa:
# self.show_operator_message("Cebado iniciado", level="info", timeout_ms=3000)


# # Ejemplos según tipo:
# self.show_operator_message("Tratamiento iniciado correctamente", "success", 2500)
# self.show_operator_message("Temperatura fuera de rango", "warning", 5000)
# self.show_operator_message("Error crítico en bomba", "error", 8000)

#===============================Fin de codigo de prueba======================
# ====================== MÉTODOS DE MENSAJES FLOTANTES ======================
    def _get_or_create_floating_msg(self) -> FloatingMessage:
        """Helper para evitar la duplicación de instanciación del widget de mensajes"""
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        return self._floating_msg

    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        self._get_or_create_floating_msg().show_floating_message(text, timeout_ms)

    def show_success_message(self, text: str, timeout_ms: int = 4000):
        self._get_or_create_floating_msg().show_success_message(text, timeout_ms)

    def show_info_message(self, text: str, timeout_ms: int = 3800):
        self._get_or_create_floating_msg().show_info_message(text, timeout_ms)

    def show_warning_message(self, text: str, timeout_ms: int = 4500):
        self._get_or_create_floating_msg().show_warning_message(text, timeout_ms)
    
    def show_error_message(self, text: str, timeout_ms: int = 5000):
        self._get_or_create_floating_msg().show_error_message(text, timeout_ms)
    
    def ktv_meassurement(self):
        """
        Secuencia completa para medir Kt/V:
        1. Leer Bioimpedancia (SRTB)
        2. Capturar conductividades t1
        3. Cambiar conductividad de la máquina
        4. Capturar conductividades t2
        5. Calcular Kt/V con fórmula de Heitmann
        """      
        if not hasattr(self, 'bioz_urea_controller') or not self.bioz_urea_controller:
            logger.warning("Controlador BioZ/Urea no disponible, omitiendo medición Kt/V")
            return
        if not self.bioz_urea_controller._is_enabled: # Usar la variable interna _is_enabled
            logger.warning("Controlador BioZ/Urea deshabilitado, omitiendo medición Kt/V")
            return

        logger.info("[Kt/V] Iniciando ciclo completo de medición...")
        self.current_values["ktv_projectado"] = 0.0
        self.calculadora_ktv.reset() # Limpiar cualquier dato de medición anterior

        # NO resetear ktv_acumulado si ya existe un valor (tratamiento en curso)
        if "ktv_acumulado" not in self.current_values or self.current_values["ktv_acumulado"] == 0.0:
            self.current_values["ktv_acumulado"] = 0.0

        # 0. Guardar la conductividad inicial actual de la máquina
        self._original_conductivity_setpoint = self.current_values.get("dialyCondControlSetPoint", 13.5)
        logger.info(f"[Kt/V] Conductividad inicial de la máquina guardada: {self._original_conductivity_setpoint:.2f} mS/cm")

        # 1. Enviar comando de Bioimpedancia
        self.bioz_urea_controller.send_command("SRTB")
        logger.info("[Kt/V] Comando 'SRTB' enviado. Esperando datos de Bioimpedancia...")

        
        self.show_info_message("iniciando medición de Kt/V...", timeout_ms=2000 )        
        # Programar el siguiente paso después de un tiempo para que BIA se complete
        QTimer.singleShot(5000, self._urea_measurement)


    def _urea_measurement(self):
        """Paso 1: Medición de Urea después de BIA."""
        logger.info("[Kt/V] Paso 1: Enviando comando 'SRTU' para Urea...")
        self.bioz_urea_controller.send_command("SRTU")        
        QTimer.singleShot(2000, self._measure_conductivity_t1) # Dar 2 segundos para Urea

    def _measure_conductivity_t1(self):
        """Paso 2: Capturar conductividades en tiempo 1 (Cd_inicial)."""
        logger.info("[Kt/V] Paso 2: Capturando conductividades T1 (iniciales)...")
        cd_in_t1 = self.current_values.get("dialyConductIFProcessData", 0.0) # Conductividad EF
        cd_out_t1 = self.current_values.get("dialyConductOFProcessData", 0.0) # Conductividad SF
        temp_t1 = self.current_values.get("dialyTempIFProcessData", 25.0) # Tempetura EF
        self.calculadora_ktv.store_conductivity_t1(cd_in_t1, cd_out_t1, temp_t1)

        # 3. Cambiar la conductividad del dializado
        self._original_conductivity_setpoint = self.current_values.get("dialyCondControlSetPoint", 13.5) # Guardar el valor original para restaurar después
        self._step_conductivity_value = 1.0
        new_conductivity_target =  self._original_conductivity_setpoint + self._step_conductivity_value
        self._write_setpoint("dialyCondControlSetPoint", new_conductivity_target)
        logger.info(f"[Kt/V] Conductividad de la máquina cambiada a {new_conductivity_target:.2f} mS/cm. Esperando estabilización...")
        self._conductivity_stabilization_time = 120000
        
        # Programar la segunda medición (t2) después de un tiempo de estabilización
        QTimer.singleShot(self._conductivity_stabilization_time, self._measure_conductivity_t2)


    def _measure_conductivity_t2(self):
        """Paso 3: Capturar conductividades en tiempo 2 (Cd_paso)."""
        logger.info("[Kt/V] Paso 3: Capturando conductividades T2 (con paso)...")
        cd_in_t2 = self.current_values.get("dialyConductIFProcessData", 0.0)
        cd_out_t2 = self.current_values.get("dialyConductOFProcessData", 0.0)
        temp_t2 = self.current_values.get("dialyTempIFProcessData", 25.0)
        self.calculadora_ktv.store_conductivity_t2(cd_in_t2, cd_out_t2, temp_t2)

        # CRUCIAL: 4. Restaurar la conductividad del dializado a su valor original
        self._write_setpoint("dialyCondControlSetPoint", self._original_conductivity_setpoint)
        logger.info(f"[Kt/V] Restaurando conductividad de la máquina a {self._original_conductivity_setpoint:.2f} mS/cm. Esperando estabilización...")
        self._conductivity_stabilization_time = 120000
        # Programar el cálculo final de Kt/V después de que el sistema se haya restaurado
        # El cálculo no necesita esperar, pero es buena práctica darle tiempo a la máquina.
        QTimer.singleShot(self._conductivity_stabilization_time, self._calculate_ktv)


    def _calculate_ktv(self):
        """Paso 4: Realizar el cálculo final de Kt/V y procesar resultados."""
        logger.info("[Kt/V] Paso 4: Realizando cálculo final de Kt/V...")

   
        # Obtener valores necesarios para la fórmula de Kt/V (Qd, Qf, Qb, t_min, etc.)
        qd = self.current_values.get("balanceChamberSetTiming", 500) # revisar las varaibles 
        qf = self.current_values.get("ultraFilterPumpSpeed", 10)
        qb = self.current_values.get("bloodFlowVariableData", 300) # flujo de sangre
        t_min = self.current_values.get("heparineTherapyHours", 4) * 60 + \
                self.current_values.get("heparineTherapyMinutes", 0) # Tiempo transcurrido en minutos
        # Obtener el volumen (V)
        z_resistencia = self.current_values.get("bioz_resistance", 0.0)
        print(f"Valor de resistencia (Z) para cálculo de V: {z_resistencia:.2f} Ohmios")
        
        # Por ahora, un placeholder. Deberías calcular V con z_resistencia.
        self.peso = self.current_values.get("patient_pre_weight_kg", 70)
        self.altura = self.current_values.get("patient_height_cm", 170)
        self.edad = self.current_values.get("patient_age", 40)
        self.genero = self.current_values.get("patient_gender", 1) # "M" o "F"

         # Variable temporal exclusiva para Heitmann (1 = Hombre, 0 = Mujer)
        genero_heitmann = 0 if self.genero == 2 else 1

        v_bis_litros = self._calculate_heitmann_volume(z_resistencia, self.altura, self.peso, genero_heitmann, self.edad) 
        self.current_values["heitmann_value"] = v_bis_litros

        if v_bis_litros and v_bis_litros > 0:
            self.calculadora_ktv.set_volumen_bioimpedancia(v_bis_litros)
        else:
            # Fallback a fórmula antropométrica (Watson) si la bioimpedancia falló o no dio un valor válido
            self.calculadora_ktv.config_paciente(self.peso, self.altura, self.edad, self.genero)

        print(f"peso={self.peso} kg, altura={self.altura} cm, edad={self.edad} años, genero={self.genero} → V = {self.calculadora_ktv.volumen_distribucion_v/1000:.2f} L")
        

        #tiempo total programado para calculo de kt/v proyectado
        t_programmed_min = (self.current_values.get("heparineTherapyHours", 0) * 60 + 
                            self.current_values.get("heparineTherapyMinutes", 0))
        t_elapsed_min = self._current_elapsed_therapy_min

        
        # Cálculo de Kt/V Proyectado (usando el tiempo total programado)
        ktv_projected = self.calculadora_ktv.calculate_ktv_ionic(qd, qf, qb, t_programmed_min)
        ktv_accumulated = self.calculadora_ktv.calculate_ktv_ionic(qd, qf, qb, t_elapsed_min)

        # Persistencia centralizada de datos calculados
        self.current_values["ktv_projectado"] = ktv_projected
        self.current_values["ktv_acumulado"] = ktv_accumulated

        logger.info(f"[Kt/V Finalizado] Proyectado: {ktv_projected:.2f} | Acumulado: {ktv_accumulated:.2f}")
        self.show_success_message(f"Kt/V Acumulado: {ktv_accumulated:.3f}", 2500)



    def _calculate_heitmann_volume(self, Z: float, H: float, W: float, G: int, E: int) -> float:
        """
        Calcula el Agua Corporal Total (TBW) usando fórmula de Heitmann.
        Retorna solo el volumen en LITROS (o None si Z es inválido).
          Parámetros:
        Z (float): Impedancia o resistencia en Ohmios.
        H (float): Altura del paciente en cm.
        W (float): Peso del paciente en kg.
        G (int): Género del paciente (1 = hombre, 0 = mujer).
        E (int): Edad del paciente en años.
        """
        a = 0.266
        b = 0.186
        c = 4.702
        d = 0.081
        k = 12.44

        if Z <= 0 or W <= 0 or H <= 0:
            logger.warning(f"[Heitmann] Datos inválidos para cálculo: Z={Z}")
            return None

        try:
            TBW = (a * (H ** 2) / Z) + b * W + c * G - d * E - k
            return round(TBW, 2)
        except Exception as e:
            logger.error(f"[Heitmann] Error en cálculo: {e}")
            return None

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
            text, color = "EN LINEA", "#10b981"

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
        """Detención de hilos de comunicación de hardware con logs corregidos."""
        logger.info("[INFO] Iniciando secuencia de apagado controlado de periféricos.")
        if hasattr(self, 'master_timer') and self.master_timer.isActive():
            self.master_timer.stop()
            logger.info("Timer Maestro detenido correctamente")

        # SOLO GUARDAR 
        self._save_power_on_hours()
        self._save_operation_hours()
        self._save_cleaning_hours()

        # Stop alarm system
        if hasattr(self, 'alarm_system') and self.alarm_system:
            try:
                self.alarm_system.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop alarm system cleanly: {e}")
            self.alarm_system = None

        # Stop serial communication
        if hasattr(self, 'serial_comm') and self.serial_comm:
            try:
                self.serial_comm.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop serial communication: {e}")
            self.serial_comm = None

        if hasattr(self, 'led_bar') and self.led_bar:
            try:
                self.led_bar.send_state(self.led_bar.CMD_OFF, silence_buzzer=True)
                # time.sleep(0.1)
                self.led_bar.stop()
            except Exception as e:
                logger.error(f"Error stopping LED bar: {e}")

        if hasattr(self, 'bioz_urea_controller') and self.bioz_urea_controller:
            try:
                self.bioz_urea_controller.stop()
            except Exception as e:
                logger.error(f"Error deteniendo el controlador de BioZ/Urea: {e}")
    
        if hasattr(self, 'pattern_sensor') and self.pattern_sensor:
            try:
                self.pattern_sensor.stop()
            except Exception as e:
                logger.error(f"Error deteniendo sensor patrón: {e}")
                
        logger.info("[INFO] Secuencia de apagado completo finalizada.")

    # ====================== MÉTODOS DE LOGGING ======================

    def _prepare_log_data(self, values_dict: dict) -> dict:
        """
        Prepara los datos para logging, aplicando formato especial 
        de 8 decimales para las variables del sensor patrón.
        """
        log_data = values_dict.copy()        
        high_precision_tags = ["patternCondSensor", "patternTempSensor", "patternCondRaw"]
        
        for tag in high_precision_tags:
            if tag in log_data:
                try:
                    value = float(log_data[tag])
                    log_data[tag] = round(value, 8)
                except (ValueError, TypeError):
                    log_data[tag] = 0.0
        return log_data

    def _log_current_data(self):
        if self.csv_logger:
            self.csv_logger.log_data(self._prepare_log_data(self.current_values))

    def _log_treatment_current_data(self):
        if self.treatment_logger:
            self.treatment_logger.log_data(self._prepare_log_data(self.current_values))

    def _start_cleaning_logger(self):
        """Inicia el logger CSV para sesión de limpieza"""
        if self.cleaning_logger:
            self.cleaning_logger.close()
        try:
            self.cleaning_logger = CsvLogger(
                log_directory="logs/limpieza",
                parameter_key_map=self.parameter_mapping
            )
            logger.info("Logger CSV de Limpieza iniciado")
        except Exception as e:
            logger.error(f"Error al inicializar sesión de logger para limpieza: {e}")
            self.cleaning_logger = None

    def _stop_cleaning_logger(self):
        if self.cleaning_logger:
            try:
                self.cleaning_logger.close()
                logger.info("Logger CSV de Limpieza cerrado exitosamente")
            except Exception as e:
                logger.error(f"Error al cerrar archivo logger de limpieza: {e}")
            self.cleaning_logger = None

    def _log_cleaning_current_data(self):
        if self.cleaning_logger:
            self.cleaning_logger.log_data(self._prepare_log_data(self.current_values))


    # ====================== ESCRITURA HACIA HARDWARE ======================

    def _write_setpoint(self, tag: str, value: float):
        if not self.serial_comm or not self.serial_comm.is_connected:
            logger.warning(f"No se puede escribir setpoint '{tag}': serial desconectado")
            return

        try:
            group, address = self._resolve_tag(tag)

            if group is None or address is None:
                logger.error(f"Tag double '{tag}' no encontrado en VARIABLES")
                return

            if not VARIABLES[group][address].get("rw", False):
                logger.warning(f"Tag '{tag}' es de solo lectura")
                return

            self.serial_comm.write_double(group, address, value)
            logger.info(f"SETPOINT [DBL]: {tag} = {value} (G:{hex(group)}, ID:{address})")

        except Exception as e:
            logger.error(f"Error escribiendo setpoint '{tag}': {e}")


    def _write_boolean_command(self, tag: str, state: bool):
        if not self.serial_comm or not self.serial_comm.is_connected:
            logger.warning(f"No serial connection for boolean command: {tag}")
            return

        try:
            _, address = self._resolve_tag(tag)  # group no se usa en boolean

            if address is None:
                logger.error(f"Tag booleano '{tag}' no encontrado")
                return

            self.serial_comm.write_boolean(address, state)
            logger.info(f"COMANDO [BOOL]: {tag} = {state} (Addr: {address})")

        except Exception as e:
            logger.error(f"Error en write_boolean_command '{tag}': {e}")


    def _resolve_tag(self, tag: str) -> tuple[int | None, int | None]:
        """
        Resuelve un tag a (group, address) usando el mapa inverso.
        Mucho más rápido y limpio.
        """
        if not hasattr(self, '_tags_cache'):
            self._tags_cache = {}

        if tag in self._tags_cache:
            return self._tags_cache[tag]
        result = TAG_TO_ADDRESS.get(tag, (None, None))
        self._tags_cache[tag] = result
        return result
    
    #===============================FIN ESCRITURA A HARDWARE===============================


    def on_pattern_data(self, tag: str, value: float):        
        """Mapeo directo de alta velocidad de los datos del sensor patrón hacia el diccionario global"""
        mapping = {
            "patternCondSensor": (0x09, 0x00),
            "patternTempSensor": (0x09, 0x01),
            "patternCondRaw": (0x09, 0x02)
        }
        
        if tag in mapping:
            g, id_ = mapping[tag]
            VARIABLES[g][id_]["value"] = value            

        self.current_values[tag] = value  
        current_widget = self.screen_stack.currentWidget()
        if hasattr(current_widget, "update_values"):
            current_widget.update_values(self.current_values)

    def _update_therapy_time_displays(self):
        # 1. Si no hay tratamiento, limpiar los displays y salir.   
        if not self.is_treatment_running:    
            if hasattr(self, 'dialysis_screen') and \
               hasattr(self.dialysis_screen, 'elapsed_time_display') and \
               hasattr(self.dialysis_screen, 'remaining_time_display'):
                self.dialysis_screen.elapsed_time_display.set_value("00:00:00")
                self.dialysis_screen.remaining_time_display.set_value("00:00:00")
            return

        # --- 2. CÁLCULO INTERNO DE TIEMPO (Siempre se ejecuta) ---
        current_elapsed_seconds = self.accumulated_therapy_seconds
        if self.last_resume_time is not None:
            current_segment_seconds = self.last_resume_time.secsTo(QDateTime.currentDateTime())
            current_elapsed_seconds += current_segment_seconds

        # Registro en minutos reales consumidos para el cálculo iónico de Kt/V
        self._current_elapsed_therapy_min = current_elapsed_seconds / 60.0

        # Calcular tiempo restante
        remaining_sec = max(0, self.total_therapy_seconds - current_elapsed_seconds)

        # Evaluar paro automático (INCLUSO SI ESTÁ EN OTRA PANTALLA)
        if remaining_sec <= 0:
            self.stop_treatment()
            self.stop_priming()
            # Ajustar para que los displays queden en cero exacto inmediatamente después del paro
            current_elapsed_seconds = self.total_therapy_seconds 
            remaining_sec = 0 # Asegurar que remaining_sec sea 0 para la actualización visual final

        # --- 3. ACTUALIZACIÓN VISUAL 
        if hasattr(self, 'dialysis_screen') and hasattr(self.dialysis_screen, 'elapsed_time_display') and \
           hasattr(self.dialysis_screen, 'remaining_time_display'):
            # self.dialysis_screen.remaining_time_display.set_value(remaining_str)
            elapsed_str = f"{current_elapsed_seconds // 3600:02d}:{(current_elapsed_seconds % 3600) // 60:02d}:{current_elapsed_seconds % 60:02d}"
            remaining_str = f"{remaining_sec // 3600:02d}:{(remaining_sec % 3600) // 60:02d}:{remaining_sec % 60:02d}"

            self.dialysis_screen.elapsed_time_display.set_value(elapsed_str)
            self.dialysis_screen.remaining_time_display.set_value(remaining_str)






    def handle_comm_config_change(self, sensor_id, port, is_enabled):
        if sensor_id == "MAIN_CONTROL":
            self.serial_comm.update_config(port, is_enabled)
            logger.info(f"Controlador Principal: Puerto={port}, Habilitado={is_enabled}")
            
        elif sensor_id == "CONDUCTIVITY":
            self.pattern_sensor.update_config(port, is_enabled)
            logger.info(f"Sensor Conductividad: Puerto={port}, Habilitado={is_enabled}")
            
        elif sensor_id == "BIOZ":
            self.bioz_urea_controller.update_config(port, is_enabled)
            logger.info(f"Sensor BioZ: Puerto={port}, Habilitado={is_enabled}")

    # ====================== PERSISTENCIA DE HORAS DE HARDWARE ======================
    def _helper_convert_hours_to_h_m(self, hours_float: float) -> tuple:
        """Helper matemático para uniformar el desglose de horas decimales a visualización H:M"""
        hours_int = int(hours_float)
        minutes_int = round((hours_float - hours_int) * 60)
        if minutes_int == 60:
            minutes_int = 0
            hours_int += 1
        return hours_int, minutes_int
    
    def _load_hours_from_file(self, file_path: str, key: str) -> float:
        """Carga genérica y segura de horas persistidas"""
        try:
            import json
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get(key, 0.0)
        except Exception as e:
            logger.error(f"Error al leer archivo {file_path}: {e}")
        return 0.0


    def _save_hours_to_file(self, file_path: str, data_dict: dict, log_msg: str):
        """Escritura genérica y segura de configuraciones operativas de horas"""
        try:
            import json
            os.makedirs("config", exist_ok=True)
            data_dict["last_update"] = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
            logger.info(log_msg)
        except Exception as e:
            logger.error(f"Error escribiendo configuración en {file_path}: {e}")


    def _load_operation_hours(self):
        self.total_operation_hours = self._load_hours_from_file("config/operation_hours.json", "total_operation_hours")
        logger.info(f"Horas de operación cargadas: {self.total_operation_hours:.2f} h")
        if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
            self._update_maintenance_screen_immediately()

    def _pause_operation_timer(self):
        """Detiene el conteo de horas de operación sin reiniciar el total acumulado."""
        if self.operation_start_time is not None:
            self.operation_start_time = None
            self._save_operation_hours()
            logger.info("Operación en pausa: contador de horas de operación detenido.")
            if hasattr(self, 'maintenance_screen'): # validar si esto genera error 
                self._update_maintenance_screen_immediately()


    def _save_operation_hours(self):
        self._save_hours_to_file(
            "config/operation_hours.json", 
            {"total_operation_hours": round(self.total_operation_hours, 4)},
            f"Horas de operación guardadas: {self.total_operation_hours:.2f}h"
        )

    def _load_power_on_hours(self):
        self.power_on_hours = self._load_hours_from_file("config/power_on_hours.json", "power_on_hours")
        logger.info(f"Power On Hours cargadas: {self.power_on_hours:.2f} h")
        if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
            self._update_maintenance_screen_immediately()
                
    def _save_power_on_hours(self):
        self._save_hours_to_file(
            "config/power_on_hours.json", 
            {"power_on_hours": round(self.power_on_hours, 4)},
            f"Power On Hours guardadas: {self.power_on_hours:.2f} h"
        )


    def _load_cleaning_hours(self):
        self.cleaning_hours = self._load_hours_from_file("config/cleaning_hours.json", "cleaning_hours")
        logger.info(f"Horas de limpieza cargadas: {self.cleaning_hours:.2f} h")
        if hasattr(self, 'maintenance_screen') and self.screen_stack.currentWidget() == self.maintenance_screen:
            self._update_maintenance_screen_immediately()

    def _save_cleaning_hours(self):
        self._save_hours_to_file(
            "config/cleaning_hours.json", 
            {"cleaning_hours": round(self.cleaning_hours, 4)},
            f"Horas de limpieza guardadas: {self.cleaning_hours:.2f} h"
        )



    def _update_maintenance_screen_immediately(self):
        """Actualiza la interfaz de mantenimiento utilizando la lógica matemática compactada"""
        if not hasattr(self, 'maintenance_screen'):
            return

        po_h, po_m = self._helper_convert_hours_to_h_m(self.power_on_hours)
        op_h, op_m = self._helper_convert_hours_to_h_m(self.total_operation_hours)
        cl_h, cl_m = self._helper_convert_hours_to_h_m(self.cleaning_hours)

        self.maintenance_screen.update_power_on_hours(po_h, po_m)
        self.maintenance_screen.update_operation_hours(op_h, op_m)
        self.maintenance_screen.update_cleaning_hours(cl_h, cl_m)

        logger.debug(f"Pantalla mantenimiento refrescada: PO={po_h}h {po_m}m | OP={op_h}h {op_m}m")

    # ====================== HISTORIAL JSON (CON VALIDACIÓN) ======================

    def _load_histories(self):
        """Carga los historiales desde JSON al iniciar"""
        os.makedirs("logs/Historiales", exist_ok=True)
        
        try:
            with open("logs/Historiales/historial_tratamientos.json", 'r', encoding='utf-8') as f:
                self.treatment_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.treatment_history = []
            
        try:
            with open("logs/Historiales/historial_limpieza.json", 'r', encoding='utf-8') as f:
                self.cleaning_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.cleaning_history = []

    def _save_history_to_file(self, file_path: str, history_data: list, label: str):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error escribiendo {label}: {e}")


    def _save_treatment_history(self):
        self._save_history_to_file("logs/Historiales/historial_tratamientos.json", self.treatment_history, "historial_tratamientos")

    def _save_cleaning_history(self):
        self._save_history_to_file("logs/Historiales/historial_limpieza.json", self.cleaning_history, "historial_limpieza")

    def _validate_session(self, start_time: QDateTime, end_time: QDateTime) -> bool:
        """Valida que la sesión sea lógica y no duplicada"""
        if start_time is None or end_time is None:
            logger.warning("Intento de registrar sesión sin tiempo de inicio o fin")
            return False

        if end_time < start_time:
            logger.error("Error: Hora de fin es anterior a hora de inicio")
            return False

        duration_seconds = start_time.secsTo(end_time)
        if duration_seconds < 60:  # Menos de 1 minuto
            logger.warning(f"Sesión muy corta ({duration_seconds} segundos). No se registrará.")
            return False

        return True

    def register_treatment_session(self):
        """Registra una sesión completa de tratamiento con validación"""
        if not self.current_treatment_start:
            return

        end_time = QDateTime.currentDateTime()
        
        # Validación de fechas
        if not self._validate_session(self.current_treatment_start, end_time):
            self.current_treatment_start = None
            return

        duration_seconds = self.current_treatment_start.secsTo(end_time)
        duration_minutes = round(duration_seconds / 60)
        
        record = {
            "fecha": self.current_treatment_start.toString("yyyy-MM-dd"),
            "hora_inicio": self.current_treatment_start.toString("HH:mm:ss"),
            "hora_fin": end_time.toString("HH:mm:ss"),
            "tipo_tratamiento": self._treatment_map.get(
                int(self.current_values.get("treatmentModeSelection", 0)), "Desconocido"
            ),
            "duracion_minutos": duration_minutes,
            "duracion_hhmm": f"{duration_minutes//60:02d}:{duration_minutes%60:02d}",
            "timestamp_registro": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        }
        
        # Evitar duplicados cercanos (últimos 5 minutos)
        if self.treatment_history:
            last = self.treatment_history[-1]
            if last["fecha"] == record["fecha"] and last["hora_inicio"] == record["hora_inicio"]:
                logger.info("Sesión de tratamiento ya guardada de forma síncrona.")
                self.current_treatment_start = None
                return

        self.treatment_history.append(record)
        self._save_treatment_history()
        
        logger.info(f"✅ Tratamiento registrado: {record['fecha']} {record['hora_inicio']} ({record['duracion_hhmm']})")
        self.current_treatment_start = None

    def register_cleaning_session(self):
        """Registra una sesión completa de limpieza"""
        if not self.cleaning_start_time:        # ← Cambiado a cleaning_start_time
            logger.warning("No hay sesión de limpieza activa para registrar.")
            return

        end_time = QDateTime.currentDateTime()
        
        if not self._validate_session(self.cleaning_start_time, end_time):
            self.cleaning_start_time = None
            return

        duration_seconds = self.cleaning_start_time.secsTo(end_time)
        duration_minutes = round(duration_seconds / 60)
        
        record = {
            "fecha": self.cleaning_start_time.toString("yyyy-MM-dd"),
            "hora_inicio": self.cleaning_start_time.toString("HH:mm:ss"),
            "hora_fin": end_time.toString("HH:mm:ss"),
            "tipo_tratamiento": "Limpieza",
            "duracion_minutos": duration_minutes,
            "duracion_hhmm": f"{duration_minutes//60:02d}:{duration_minutes%60:02d}",
            "timestamp_registro": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        }
        
        # Evitar duplicados
        if self.cleaning_history:
            last = self.cleaning_history[-1]
            if last["fecha"] == record["fecha"] and last["hora_inicio"] == record["hora_inicio"]:
                logger.info("Sesión de limpieza duplicada ignorada.")
                self.cleaning_start_time = None
                return
        self.cleaning_history.append(record)
        self._save_cleaning_history()
        
        logger.info(f"✅ Limpieza registrada: {record['fecha']} {record['hora_inicio']} ({record['duracion_hhmm']})")
        

    def closeEvent(self, event):
        
        # QApplication.processEvents()
        # time.sleep(0.8)   # Pequeña pausa visible

        self.end_dialysis_session() # Cierra los loggers
        logger.error("[INFO] closeEvent → performing shutdown...")
        self.shutdown() # shutdown ya guarda las horas
        # self.show_info_message("Cerrando aplicación...", 1000)
        time.sleep(1.0) 
        event.accept()
        QApplication.quit()



