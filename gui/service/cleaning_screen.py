# gui/service/cleaning_screen.py
# Cleaning / Disinfection screen (stacked index 3)
# Controls chemical disinfection cycle with progress tracking and safety checks

"""
Módulo para la pantalla de control del ciclo de limpieza y desinfección.

Este módulo define la clase `CleaningScreen`, que proporciona la interfaz
de usuario para gestionar los procesos automatizados de limpieza y
desinfección química de la máquina de hemodiálisis. Es una pantalla crucial
para asegurar la higiene y esterilidad del equipo entre pacientes o al final
de la jornada.

Características principales:
-----------------------------
- **Control del Ciclo:** Gestiona el inicio, el progreso y la finalización
  de un ciclo predefinido de limpieza química.
- **Barra de Progreso Visual:** Muestra una `QProgressBar` para indicar el
  avance del ciclo de forma clara, incluyendo el porcentaje y el tiempo
  transcurrido/total.
- **Temporizador de Cuenta Regresiva:** Muestra el tiempo restante del ciclo
  de limpieza, proporcionando al operador una estimación del tiempo de espera.
- **Estados del Ciclo:** Actualiza dinámicamente la fase actual del proceso
  (ej. "Esperando condiciones...", "Desinfección en curso...", "Limpieza completada").
- **Habilitación Condicional:** El botón de "Iniciar limpieza" se habilita
  únicamente cuando la máquina reporta un estado que permite el inicio seguro
  del ciclo de limpieza (ej. "INFUSION").
- **Comunicación con el Controlador:** Emite señales (`request_setpoint_change`
  y `request_boolean_change`) para instruir al controlador principal de la HMI
  a iniciar o detener el proceso de limpieza y para establecer el modo de
  operación adecuado.
- **Reinicio del Proceso:** Al finalizar un ciclo, el botón "Iniciar" se
  transforma en "Reiniciar", permitiendo volver al estado inicial o repetir
  el ciclo.

Clase principal:
----------------
- `CleaningScreen`: Widget que encapsula toda la lógica y la interfaz
  para la gestión del ciclo de limpieza.

Dependencias:
-------------
- `PySide6`: Para la construcción de la interfaz gráfica de usuario y señales/slots.
- `logging`: Para registrar eventos y posibles errores.


Uso:
----
La clase `CleaningScreen` se instancia en el `HemodialysisHMI` principal
y se añade a su `QStackedWidget` como una pantalla de servicio. Se espera
que el `HemodialysisHMI` conecte sus señales a métodos que envíen los comandos
al controlador serial y que se encargue de actualizar los `current_values`
para que esta pantalla pueda sincronizar su estado.
"""


# from PySide6.QtWidgets import (
#     QWidget, QGridLayout, QLabel, QPushButton,
#     QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame, QButtonGroup
# )
# from PySide6.QtCore import Qt, QTimer, Signal
# from PySide6.QtGui import QColor, QFont
# import logging
# import json
# import os
# logger = logging.getLogger(__name__)

# try:
#     from core.variables_map import VARIABLES
# except ImportError:
#     VARIABLES = {0x01: {}, 0x02: {}}

# CONFIG_FILE_PATH = "cleaning_config.json"

# gui/service/cleaning_screen.py

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
import logging
import json
import os

logger = logging.getLogger(__name__)

# Definimos la ruta del archivo de configuración (igual que en la otra pantalla)
CONFIG_FILE_PATH = "config/cleaning_config.json"

class CleaningScreen(QWidget):
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}

        self.cleaning_in_progress = False
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #0f172a;")

        self.current_phase = "Esperando condiciones..."
        self.total_time_seconds = 0
        self.remaining_time_seconds = 0
        
        self.selected_mode = None # Almacena el modo seleccionado (0.0 o 1.0)

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)

        self.setup_ui() # Construye la UI

        self._load_initial_config_on_startup() 
        

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(30)

        title_label = QLabel("Limpieza / Desinfección")
        title_label.setStyleSheet("color: #cbd5e1; font-size: 52px; font-weight: bold; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # ── Frame para Selección de Modo ─────────────────────────────────────────
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setSpacing(20)

        self.btn_mode_group = QButtonGroup(self)
        self.btn_mode_group.setExclusive(True)

        self.btn_short = QPushButton("Desinfección Química Corta")
        self.btn_long = QPushButton("Desinfección Química Larga")
#
        self.style_unchecked = """
            QPushButton {
                background: #3b82f6; color: white; font-size: 24px; font-weight: bold;
                border-radius: 12px; padding: 15px; border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
        """
        self.style_checked = """
            QPushButton {
                background: #22c55e; color: white; font-size: 24px; font-weight: bold;
                border-radius: 12px; padding: 15px; border: 2px solid #16a34a;
            }
        """

        for btn, mode_val in [(self.btn_short, 0.0), (self.btn_long, 1.0)]:
            btn.setStyleSheet(self.style_unchecked)
            btn.setCheckable(True)
            btn.toggled.connect(lambda checked, b=btn, val=mode_val: self._on_mode_toggled(b, val, checked))
            mode_layout.addWidget(btn)
            self.btn_mode_group.addButton(btn)

        main_layout.addWidget(mode_frame)

        # ── Current Phase / Status ───────────────────────────────────────────────
        self.phase_label = QLabel(self.current_phase)
        self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold; background: transparent; min-height: 60px;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.phase_label)

        # ── Progress Bar ─────────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m seg")
        self.progress_bar.setFixedHeight(60)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b; border: 2px solid #475569; border-radius: 10px;
                text-align: center; color: #ffffff; font-size: 24px; font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # ── Remaining Time ───────────────────────────────────────────────────────
        self.time_label = QLabel("Tiempo configurado: --:--")
        self.time_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
        self.time_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.time_label)
    
        main_layout.addStretch()

        # ── Start / Restart Button ───────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Iniciar limpieza")
        self.start_button.setFixedSize(300, 100)
        self.start_button.setEnabled(False)  
        self.start_button.setProperty("base_color", "#047857")         
        self.start_button.setStyleSheet("""
            QPushButton {
                background: #047857; color: white; font-size: 38px; font-weight: bold;
                border: none; border-radius: 16px; padding: 10px;
            }
            QPushButton:hover { background: #065f46; }
            QPushButton:pressed { background: #064e3b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        self.start_button.clicked.connect(self._start_cleaning)
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Initial UI state
        self.phase_label.setText("Esperando estado listo...")
        self.progress_bar.setValue(0)
        self.progress_timer.stop()


    def _load_initial_config_on_startup(self):
        """
        Carga la última configuración guardada al iniciar la pantalla
        y simula la selección del botón correspondiente.
        """
        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar configuración inicial desde JSON: {e}")
        
        saved_mode_value = config_data.get("last_active_mode_value", 0.0) # Por defecto, modo corto

        # Simular el clic en el botón correcto para cargar el tiempo
        if saved_mode_value == 0.0:
            self.btn_short.setChecked(True) # Esto activará _on_mode_toggled
        elif saved_mode_value == 1.0:
            self.btn_long.setChecked(True) # Esto activará _on_mode_toggled
        else:
             self.btn_short.setChecked(True) # Si el valor no es válido, por defecto el corto


    def _on_mode_toggled(self, button, mode_value, checked):
        """Maneja la selección del modo, carga el JSON y envía los tags"""
        if checked:
            button.setStyleSheet(self.style_checked)
            self.selected_mode = mode_value
            self._load_mode_specific_configuration(mode_value) # Carga la configuración específica del modo
        else:
            button.setStyleSheet(self.style_unchecked)

    def _load_mode_specific_configuration(self, mode_value: float):
        """
        Carga el tiempo desde JSON para el modo específico,
        actualiza la UI y envía los tags al controlador.
        """
        hours, minutes = 0, 15 # Valores por defecto (15 min)
        
        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.error(f"Error al leer JSON de limpieza para modo {mode_value}: {e}")

        # Intentar obtener la configuración para el modo específico
        mode_config = config_data.get("modes", {}).get(str(mode_value))
        if mode_config:
            hours = mode_config.get("time_hours", 0)
            minutes = mode_config.get("time_minutes", 15)
        
        # Calcular total en segundos
        self.total_time_seconds = (hours * 3600) + (minutes * 60)
        self.remaining_time_seconds = self.total_time_seconds
        
        # Escribir los valores solicitados al controlador
        self.on_user_input_setpoint("heparineTherapyHours", float(hours))
        self.on_user_input_setpoint("heparineTherapyMinutes", float(minutes))

        # Actualizar UI
        self.time_label.setText(f"Tiempo configurado: {hours:02d}:{minutes:02d}")
        self.progress_bar.setMaximum(self.total_time_seconds)
        self.progress_bar.setValue(0)
        logger.info(f"Modo {mode_value} cargado. Tiempo: {hours}h {minutes}m. Escrito a controlador.")


    def reset_ui(self):
        """Reset UI to initial waiting state."""
        self.cleaning_in_progress = False
        self.current_phase = "Esperando condiciones..."
        self.phase_label.setText(self.current_phase)
        self.progress_bar.setValue(0)
        self.time_label.setText("Tiempo restante: --:--")

        self.start_button.setEnabled(False)
        self.start_button.setText("Iniciar limpieza")

        try: self.start_button.clicked.disconnect()
        except TypeError: pass
        self.start_button.clicked.connect(self._start_cleaning)

        self.progress_timer.stop()
        # Al reiniciar, volver a cargar la última configuración guardada
        self._load_initial_config_on_startup()


    def _start_cleaning(self):
        """Initiate the disinfection cycle."""
        if self.selected_mode is None:
            logger.warning("No se seleccionó modo de desinfección antes de iniciar.")
            # Aquí podrías mostrar un QMessageBox al usuario avisando que seleccione un modo primero
            return

        self.cleaning_in_progress = True

        try:
            self.on_user_input_setpoint("treatmentModeSelection", 3.0) 
            self.on_user_boolean_command("dialyStartDialysisButt", True)
            self.on_user_boolean_command("dialyStopDialysisButt",False)

        except Exception as e:
            logger.error(f"Error al iniciar ciclo de limpieza: {e}")

        self.remaining_time_seconds = self.total_time_seconds

        self.current_phase = "Desinfección química en curso..."
        self.phase_label.setText(self.current_phase)
        self.start_button.setEnabled(False)
        self.start_button.setText("En proceso...")

        self.progress_bar.setMaximum(self.total_time_seconds)
        self.progress_bar.setValue(0)

        self.progress_timer.start(1000)
        self._update_time_display()

    def _update_progress(self):
        """Update progress every second."""
        if self.remaining_time_seconds > 0:
            self.remaining_time_seconds -= 1
            self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
            self._update_time_display()
        else:
            self.progress_timer.stop()
            self._finish_cleaning()

    def _update_time_display(self):
        """Format and display remaining time."""
        minutes = self.remaining_time_seconds // 60
        seconds = self.remaining_time_seconds % 60
        self.time_label.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

    def _finish_cleaning(self):
        """Handle cycle completion."""
        self.cleaning_in_progress = False
        self.current_phase = "Limpieza completada"
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
        self.time_label.setText("Tiempo restante: 00:00")
        self.progress_bar.setValue(self.total_time_seconds)
        
        try:            
            self.on_user_input_setpoint("dialyStartDialysisButt", False)
            self.on_user_boolean_command("dialyStopDialysisButt", True)
        except Exception as e:
            logger.error(f"Error al finalizar ciclo de limpieza: {e}")

        self.start_button.setText("Reiniciar")
        self.start_button.setEnabled(True)

        try:
            self.start_button.clicked.disconnect()
        except TypeError:
            pass
        self.start_button.clicked.connect(self.reset_ui)

    def update_values(self, new_values: dict):
        """Receive and process updated values from main window."""
        self.current_values = new_values
        pass

    def update_buttons_state(self, status_code):
        """
        Habilita o deshabilita el botón de limpieza basado en el estado.
        Estandarizado con DialysisScreen.
        """
        if self.cleaning_in_progress:
            return

        style_disabled = """
            QPushButton {
                background: #334155; color: #64748b;
                font-size: 38px; font-weight: bold; border: none;
                border-radius: 16px; padding: 10px;
            }
        """
        def set_enabled_style(btn):
            color = btn.property("base_color")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: white;
                    font-size: 38px; font-weight: bold; border: none;
                    border-radius: 16px; padding: 10px;
                }}
                QPushButton:hover {{ background: #065f46; }}
                QPushButton:pressed {{ background: #064e3b; }}
            """)

        if status_code == 7:
            if not self.start_button.isEnabled():
                self.start_button.setEnabled(True)
                set_enabled_style(self.start_button)
                
                self.current_phase = "Sistema listo para limpieza"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
        else:
            if self.start_button.isEnabled() and self.start_button.text() != "Reiniciar":
                self.start_button.setEnabled(False)
                self.start_button.setStyleSheet(style_disabled)
                
                self.current_phase = f"Esperando estado (Actual: {status_code})"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)

# class CleaningScreen(QWidget):
#     request_setpoint_change = Signal(str, float)
#     request_boolean_change = Signal(str, bool)

#     def __init__(self, parent=None, values_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.current_values = values_dict if values_dict is not None else {}

#         self.cleaning_in_progress = False
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setStyleSheet("background: #0f172a;") # Industrial dark blue

#         self.current_phase = "Esperando condiciones..."
#         self.total_time_seconds = 0
#         self.remaining_time_seconds = 0
        
#         self.selected_mode = None # Almacena el modo seleccionado (0.0 o 1.0)

#         self.progress_timer = QTimer(self)
#         self.progress_timer.timeout.connect(self._update_progress)

#         self.setup_ui() # Construye la UI

#         # --- NUEVO: Cargar configuración al iniciar la pantalla ---
#         self._load_initial_config_on_startup() 
#         # ---------------------------------------------------------


#     def setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(60, 40, 60, 40)
#         main_layout.setSpacing(30)

#         # ── Title ────────────────────────────────────────────────────────────────
#         title_label = QLabel("Limpieza / Desinfección")
#         title_label.setStyleSheet("color: #cbd5e1; font-size: 52px; font-weight: bold; background: transparent;")
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)

#         # ── Frame para Selección de Modo ─────────────────────────────────────────
#         mode_frame = QFrame()
#         mode_frame.setStyleSheet("background: #1e293b; border-radius: 10px; padding: 15px;")
#         mode_layout = QHBoxLayout(mode_frame)
#         mode_layout.setSpacing(20)

#         self.btn_mode_group = QButtonGroup(self)
#         self.btn_mode_group.setExclusive(True)

#         self.btn_short = QPushButton("Desinfección Química Corta")
#         self.btn_long = QPushButton("Desinfección Química Larga")

#         self.style_unchecked = """
#             QPushButton {
#                 background: #3b82f6; color: white; font-size: 24px; font-weight: bold;
#                 border-radius: 12px; padding: 15px; border: 2px solid #2563eb;
#             }
#             QPushButton:hover { background: #60a5fa; }
#         """
#         self.style_checked = """
#             QPushButton {
#                 background: #22c55e; color: white; font-size: 24px; font-weight: bold;
#                 border-radius: 12px; padding: 15px; border: 2px solid #16a34a;
#             }
#         """

#         for btn, mode_val in [(self.btn_short, 0.0), (self.btn_long, 1.0)]:
#             btn.setStyleSheet(self.style_unchecked)
#             btn.setCheckable(True)
#             # Conexión para manejar el clic del usuario Y la carga programática
#             btn.toggled.connect(lambda checked, b=btn, val=mode_val: self._on_mode_toggled(b, val, checked))
#             mode_layout.addWidget(btn)
#             self.btn_mode_group.addButton(btn)

#         main_layout.addWidget(mode_frame)

#         # ── Current Phase / Status ───────────────────────────────────────────────
#         self.phase_label = QLabel(self.current_phase)
#         self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold; background: transparent; min-height: 60px;")
#         self.phase_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.phase_label)

#         # ── Progress Bar ─────────────────────────────────────────────────────────
#         self.progress_bar = QProgressBar()
#         self.progress_bar.setMinimum(0)
#         self.progress_bar.setMaximum(100)
#         self.progress_bar.setValue(0)
#         self.progress_bar.setTextVisible(True)
#         self.progress_bar.setFormat("%p% - %v/%m seg")
#         self.progress_bar.setFixedHeight(60)
#         self.progress_bar.setStyleSheet("""
#             QProgressBar {
#                 background: #1e293b; border: 2px solid #475569; border-radius: 10px;
#                 text-align: center; color: #ffffff; font-size: 24px; font-weight: bold;
#             }
#             QProgressBar::chunk {
#                 background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
#                 border-radius: 8px;
#             }
#         """)
#         main_layout.addWidget(self.progress_bar)

#         # ── Remaining Time ───────────────────────────────────────────────────────
#         self.time_label = QLabel("Tiempo configurado: --:--")
#         self.time_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
#         self.time_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.time_label)
    
#         main_layout.addStretch()

#         # ── Start / Restart Button ───────────────────────────────────────────────
#         button_layout = QHBoxLayout()
#         button_layout.addStretch()

#         self.start_button = QPushButton("Iniciar limpieza")
#         self.start_button.setFixedSize(300, 100)
#         self.start_button.setEnabled(False)  
#         self.start_button.setProperty("base_color", "#047857")         
#         self.start_button.setStyleSheet("""
#             QPushButton {
#                 background: #047857; color: white; font-size: 38px; font-weight: bold;
#                 border: none; border-radius: 16px; padding: 10px;
#             }
#             QPushButton:hover { background: #065f46; }
#             QPushButton:pressed { background: #064e3b; }
#             QPushButton:disabled { background: #334155; color: #64748b; }
#         """)
#         self.start_button.clicked.connect(self._start_cleaning)
#         button_layout.addWidget(self.start_button)
#         button_layout.addStretch()
#         main_layout.addLayout(button_layout)

#         # Initial UI state
#         self.phase_label.setText("Esperando estado listo...")
#         self.progress_bar.setValue(0)
#         self.progress_timer.stop()


#     def _load_initial_config_on_startup(self):
#         """
#         Carga la última configuración guardada al iniciar la pantalla
#         y simula la selección del botón correspondiente.
#         """
#         if os.path.exists(CONFIG_FILE_PATH):
#             try:
#                 with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
#                     config_data = json.load(f)
                
#                 saved_mode_value = config_data.get("mode_value")
                
#                 # Simular el clic en el botón correcto para cargar el tiempo
#                 if saved_mode_value == 0.0:
#                     self.btn_short.setChecked(True) # Esto activará _on_mode_toggled
#                 elif saved_mode_value == 1.0:
#                     self.btn_long.setChecked(True) # Esto activará _on_mode_toggled
#                 else:
#                     logger.warning("Modo guardado no reconocido, usando modo corto por defecto.")
#                     self.btn_short.setChecked(True) # Default a corto si no hay o es inválido

#             except Exception as e:
#                 logger.error(f"Error al cargar configuración inicial desde JSON: {e}")
#                 self.btn_short.setChecked(True) # Si hay error, default a corto
#         else:
#             logger.info("No se encontró archivo de configuración, usando modo corto por defecto.")
#             self.btn_short.setChecked(True) # Si no hay archivo, default a corto


#     def _on_mode_toggled(self, button, mode_value, checked):
#         """Maneja la selección del modo, carga el JSON y envía los tags"""
#         if checked:
#             button.setStyleSheet(self.style_checked)
#             self.selected_mode = mode_value
#             self._load_configuration(mode_value)
#         else:
#             button.setStyleSheet(self.style_unchecked)

#     def _load_configuration(self, mode_value):
#         """Carga el tiempo desde JSON si existe, y configura las variables"""
#         hours, minutes = 0, 15 # Valores por defecto (15 min) si no hay JSON
        
#         if os.path.exists(CONFIG_FILE_PATH):
#             try:
#                 with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
#                     config_data = json.load(f)
#                     # Comprobamos si el JSON guardado corresponde al modo seleccionado
#                     # Esto es importante para que si tengo guardado el modo "largo" con 30min,
#                     # al seleccionar el botón "corto", se cargue el tiempo del modo "corto"
#                     # o el default si el archivo no contiene esa configuración.
#                     # SIN EMBARGO, para esta pantalla (CleaningScreen) la idea es que refleje
#                     # LA ÚLTIMA configuración guardada, independientemente del modo.
#                     # Si el objetivo es que CADA BOTÓN DE LIMPIEZA tenga su PROPIA configuración persistente,
#                     # entonces el JSON debería guardar un diccionario de modos, ej:
#                     # { "0.0": { "hours": 0, "minutes": 15 }, "1.0": { "hours": 1, "minutes": 0 } }
#                     # Pero basado en tu requerimiento actual ("si hago un cambio en la otra pantalla
#                     # que se refleje cuando entro nuevamente a esta"), el JSON solo guarda UN estado,
#                     # y este estado es el que se reflejará.
                    
#                     # Para mantener la lógica de "última configuración guardada",
#                     # no necesitamos verificar config_data.get("mode_value") == mode_value aquí,
#                     # ya que el _load_initial_config_on_startup ya forzó la selección del botón
#                     # del último modo guardado.
#                     # Entonces, simplemente cargamos el tiempo guardado.
                    
#                     hours = config_data.get("time_hours", 0)
#                     minutes = config_data.get("time_minutes", 15)
#             except Exception as e:
#                 logger.error(f"Error al leer JSON de limpieza: {e}")

#         # Calcular total en segundos
#         self.total_time_seconds = (hours * 3600) + (minutes * 60)
#         self.remaining_time_seconds = self.total_time_seconds
        
#         # Escribir los valores solicitados al controlador
#         self.on_user_input_setpoint("heparineTherapyHours", float(hours))
#         self.on_user_input_setpoint("heparineTherapyMinutes", float(minutes))

#         # Actualizar UI
#         self.time_label.setText(f"Tiempo configurado: {hours:02d}:{minutes:02d}")
#         self.progress_bar.setMaximum(self.total_time_seconds)
#         self.progress_bar.setValue(0)
#         logger.info(f"Modo {mode_value} cargado. Tiempo: {hours}h {minutes}m. Escrito a controlador.")

#     def reset_ui(self):
#         """Reset UI to initial waiting state."""
#         self.cleaning_in_progress = False
#         self.current_phase = "Esperando condiciones..."
#         self.phase_label.setText(self.current_phase)
#         self.progress_bar.setValue(0)
#         self.time_label.setText("Tiempo restante: --:--")

#         self.start_button.setEnabled(False)
#         self.start_button.setText("Iniciar limpieza")

#         try: self.start_button.clicked.disconnect()
#         except TypeError: pass
#         self.start_button.clicked.connect(self._start_cleaning)

#         self.progress_timer.stop()
#         # Al reiniciar, deberíamos volver a cargar la configuración para que los botones reflejen
#         # la última configuración guardada (o el default si no hay).
#         self._load_initial_config_on_startup()


#     def _start_cleaning(self):
#         """Initiate the disinfection cycle."""
#         if self.selected_mode is None:
#             # Aquí podrías mostrar un QMessageBox al usuario avisando que seleccione un modo primero
#             logger.warning("No se seleccionó modo de desinfección antes de iniciar.")
#             return

#         self.cleaning_in_progress = True

#         try:
            
#             self.on_user_input_setpoint("treatmentModeSelection", 3.0) 
            
#             self._write_boolean_command("dialyStartDialysisButt", True)
#             self._write_boolean_command("dialyStopDialysisButt",False)

#         except Exception as e:
#             logger.error(f"Error al iniciar ciclo de limpieza: {e}")

#         # Configura la duración del ciclo basada en el tiempo cargado
#         # (self.total_time_seconds ya está configurado por _load_configuration)
#         self.remaining_time_seconds = self.total_time_seconds

#         self.current_phase = "Desinfección química en curso..."
#         self.phase_label.setText(self.current_phase)
#         self.start_button.setEnabled(False)
#         self.start_button.setText("En proceso...")

#         self.progress_bar.setMaximum(self.total_time_seconds)
#         self.progress_bar.setValue(0)

#         # Start 1-second update timer
#         self.progress_timer.start(1000)

#         self._update_time_display()

#     def _update_progress(self):
#         """Update progress every second."""
#         if self.remaining_time_seconds > 0:
#             self.remaining_time_seconds -= 1
#             self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
#             self._update_time_display()
#         else:
#             self.progress_timer.stop()
#             self._finish_cleaning()

#     def _update_time_display(self):
#         """Format and display remaining time."""
#         minutes = self.remaining_time_seconds // 60
#         seconds = self.remaining_time_seconds % 60
#         self.time_label.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

#     def _finish_cleaning(self):
#         """Handle cycle completion."""
#         self.cleaning_in_progress = False
#         self.current_phase = "Limpieza completada"
#         self.phase_label.setText(self.current_phase)
#         self.phase_label.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
#         self.time_label.setText("Tiempo restante: 00:00")
#         self.progress_bar.setValue(self.total_time_seconds)
        
#         try:            
#             # Detiene la operación de desinfección/diálisis
#             self._write_boolean_command("dialyStartDialysisButt", False)
#             self._write_boolean_command("dialyStopDialysisButt",True)
#         except Exception as e:
#             logger.error(f"Error al finalizar ciclo de limpieza: {e}")

#         self.start_button.setText("Reiniciar")
#         self.start_button.setEnabled(True)

#         try:
#             self.start_button.clicked.disconnect()
#         except TypeError:
#             pass
#         self.start_button.clicked.connect(self.reset_ui) # Al hacer click en reiniciar, llama a reset_ui

#     def update_values(self, new_values: dict):
#         """Receive and process updated values from main window."""
#         self.current_values = new_values
#         pass # No se necesita hacer nada aquí si update_buttons_state se encarga de la lógica

#     def update_buttons_state(self, status_code):
#         """
#         Habilita o deshabilita el botón de limpieza basado en el estado.
#         Estandarizado con DialysisScreen.
#         """
#         if self.cleaning_in_progress:
#             return # Si está en proceso, no cambiamos el estado del botón "Iniciar/Reiniciar"

#         style_disabled = """
#             QPushButton {
#                 background: #334155; color: #64748b;
#                 font-size: 38px; font-weight: bold; border: none;
#                 border-radius: 16px; padding: 10px;
#             }
#         """
#         # Función para aplicar estilo habilitado (Verde original)
#         def set_enabled_style(btn):
#             color = btn.property("base_color")
#             btn.setStyleSheet(f"""
#                 QPushButton {{
#                     background: {color}; color: white;
#                     font-size: 38px; font-weight: bold; border: none;
#                     border-radius: 16px; padding: 10px;
#                 }}
#                 QPushButton:hover {{ background: #065f46; }}
#                 QPushButton:pressed {{ background: #064e3b; }}
#             """)

#         # Lógica de Estados
#         # Asumiendo que 7 es el código de estado "Listo para limpieza"
#         if status_code == 7:
#             if not self.start_button.isEnabled():
#                 self.start_button.setEnabled(True)
#                 set_enabled_style(self.start_button)
                
#                 # Feedback visual en etiquetas
#                 self.current_phase = "Sistema listo para limpieza"
#                 self.phase_label.setText(self.current_phase)
#                 self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
#         else:
#             # Cualquier otro estado deshabilita el botón
#             if self.start_button.isEnabled() and self.start_button.text() != "Reiniciar":
#                 # Solo deshabilitamos si no está en "Reiniciar" (porque ya terminó un ciclo)
#                 self.start_button.setEnabled(False)
#                 self.start_button.setStyleSheet(style_disabled)
                
#                 # Feedback visual
#                 self.current_phase = f"Esperando estado (Actual: {status_code})"
#                 self.phase_label.setText(self.current_phase)
#                 self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")


#     def on_user_boolean_command(self, tag, state):
#         self.request_boolean_change.emit(tag, state)

#     def on_user_input_setpoint(self, tag, value):
#         self.request_setpoint_change.emit(tag, value)


# CONFIG_FILE_PATH = "cleaning_config.json"

# class CleaningScreen(QWidget):
#     request_setpoint_change = Signal(str, float)
#     request_boolean_change = Signal(str, bool)

#     def __init__(self, parent=None, values_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.current_values = values_dict if values_dict is not None else {}

#         self.cleaning_in_progress = False
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setStyleSheet("background: #0f172a;")

#         self.current_phase = "Esperando condiciones..."
#         self.total_time_seconds = 0
#         self.remaining_time_seconds = 0
        
#         self.selected_mode = None

#         self.progress_timer = QTimer(self)
#         self.progress_timer.timeout.connect(self._update_progress)

#         self.setup_ui()
#         self._load_initial_config_on_startup() 

#     def setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(60, 40, 60, 40)
#         main_layout.setSpacing(30)

#         title_label = QLabel("Limpieza / Desinfección")
#         title_label.setStyleSheet("color: #cbd5e1; font-size: 52px; font-weight: bold; background: transparent;")
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)

#         # ── Frame para Selección de Modo ─────────────────────────────────────────
#         mode_frame = QFrame()
#         mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
#         mode_layout = QHBoxLayout(mode_frame)
#         mode_layout.setSpacing(20)

#         self.btn_mode_group = QButtonGroup(self)
#         self.btn_mode_group.setExclusive(True)

#         self.btn_short = QPushButton("Desinfección Química Corta")
#         self.btn_long = QPushButton("Desinfección Química Larga")

#         self.style_unchecked = """
#             QPushButton {
#                 background: #3b82f6; color: #ffffff; font-size: 24px; font-weight: bold;
#                 border-radius: 12px; padding: 15px; border: 2px solid #2563eb;
#             }
#             QPushButton:hover { background: #60a5fa; }
#         """
#         self.style_checked = """
#             QPushButton {
#                 background: #22c55e; color: #ffffff; font-size: 24px; font-weight: bold;
#                 border-radius: 12px; padding: 15px; border: 2px solid #16a34a;
#             }
#         """

#         for btn, mode_val in [(self.btn_short, 0.0), (self.btn_long, 1.0)]:
#             btn.setStyleSheet(self.style_unchecked)
#             btn.setCheckable(True)
#             btn.toggled.connect(lambda checked, b=btn, val=mode_val: self._on_mode_toggled(b, val, checked))
#             mode_layout.addWidget(btn)
#             self.btn_mode_group.addButton(btn)

#         main_layout.addWidget(mode_frame)

#         # ── Fase actual ───────────────────────────────────────────────
#         self.phase_label = QLabel(self.current_phase)
#         self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold; background: transparent; min-height: 60px;")
#         self.phase_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.phase_label)

#         # ── Progress Bar ─────────────────────────────────────────────────────────
#         self.progress_bar = QProgressBar()
#         self.progress_bar.setMinimum(0)
#         self.progress_bar.setMaximum(100)
#         self.progress_bar.setValue(0)
#         self.progress_bar.setTextVisible(True)
#         self.progress_bar.setFormat("%p% - %v/%m seg")
#         self.progress_bar.setFixedHeight(60)
#         self.progress_bar.setStyleSheet("""
#             QProgressBar {
#                 background: #1e293b; border: 2px solid #475569; border-radius: 10px;
#                 text-align: center; color: #ffffff; font-size: 24px; font-weight: bold;
#             }
#             QProgressBar::chunk {
#                 background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
#                 border-radius: 8px;
#             }
#         """)
#         main_layout.addWidget(self.progress_bar)

#         # ── Remaining Time ───────────────────────────────────────────────────────
#         self.time_label = QLabel("Tiempo configurado: --:--")
#         self.time_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
#         self.time_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.time_label)
    
#         main_layout.addStretch()

#         # ── Start Button ───────────────────────────────────────────────
#         button_layout = QHBoxLayout()
#         button_layout.addStretch()

#         self.start_button = QPushButton("Iniciar limpieza")
#         self.start_button.setFixedSize(300, 100)
#         self.start_button.setEnabled(False)  
#         self.start_button.setProperty("base_color", "#047857")         
#         self.start_button.setStyleSheet("""
#             QPushButton {
#                 background: #047857; color: white; font-size: 38px; font-weight: bold;
#                 border: none; border-radius: 16px; padding: 10px;
#             }
#             QPushButton:hover { background: #065f46; }
#             QPushButton:pressed { background: #064e3b; }
#             QPushButton:disabled { background: #334155; color: #64748b; }
#         """)
#         self.start_button.clicked.connect(self._start_cleaning)
#         button_layout.addWidget(self.start_button)
#         button_layout.addStretch()
#         main_layout.addLayout(button_layout)

#     def _on_mode_toggled(self, button, mode_value, checked):
#         """Maneja la selección del modo, carga el JSON y envía los tags"""
#         if checked:
#             button.setStyleSheet(self.style_checked)
#             self.selected_mode = mode_value
#             self._load_configuration(mode_value)
#         else:
#             button.setStyleSheet(self.style_unchecked)

#     def _load_configuration(self, mode_value):
#         """Carga el tiempo desde JSON si existe, y configura las variables"""
#         hours, minutes = 0, 15 # Valores por defecto (15 min) si no hay JSON
        
#         if os.path.exists(CONFIG_FILE_PATH):
#             try:
#                 with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
#                     config_data = json.load(f)
#                     # Comprobamos si el JSON guardado corresponde al modo seleccionado
#                     if config_data.get("mode_value") == mode_value:
#                         hours = config_data.get("time_hours", 0)
#                         minutes = config_data.get("time_minutes", 15)
#             except Exception as e:
#                 logger.error(f"Error al leer JSON de limpieza: {e}")

#         # Calcular total en segundos
#         self.total_time_seconds = (hours * 3600) + (minutes * 60)
#         self.remaining_time_seconds = self.total_time_seconds
        
#         # Escribir los valores solicitados al controlador
#         self.on_user_input_setpoint("heparineTherapyHours", float(hours))
#         self.on_user_input_setpoint("heparineTherapyMinutes", float(minutes))

#         # Actualizar UI
#         self.time_label.setText(f"Tiempo configurado: {hours:02d}:{minutes:02d}")
#         self.progress_bar.setMaximum(self.total_time_seconds)
#         self.progress_bar.setValue(0)
#         logger.info(f"Modo {mode_value} cargado. Tiempo: {hours}h {minutes}m. Escrito a controlador.")

#     def reset_ui(self):
#         self.cleaning_in_progress = False
#         self.current_phase = "Esperando condiciones..."
#         self.phase_label.setText(self.current_phase)
#         self.progress_bar.setValue(0)
#         self.time_label.setText("Tiempo restante: --:--")
#         self.start_button.setEnabled(False)
#         self.start_button.setText("Iniciar limpieza")
        
#         try: self.start_button.clicked.disconnect()
#         except TypeError: pass
#         self.start_button.clicked.connect(self._start_cleaning)
#         self.progress_timer.stop()

#     def _start_cleaning(self):
#         if self.selected_mode is None:
#             # Puedes mostrar un mensaje aquí para que seleccionen un modo primero
#             logger.warning("No se seleccionó modo de desinfección")
#             return

#         self.cleaning_in_progress = True
#         try:
#             self.on_user_input_setpoint("treatmentModeSelection", 3.0)
#             self._write_boolean_command("dialyStartDialysisButt", True)
#             self._write_boolean_command("dialyStopDialysisButt",False)


#         except Exception as e:
#             logger.error(f"Error {e}")

#         self.current_phase = "Desinfección química en curso..."
#         self.phase_label.setText(self.current_phase)
#         self.start_button.setEnabled(False)
#         self.start_button.setText("En proceso...")

#         self.progress_bar.setValue(0)
#         self.progress_timer.start(1000)
#         self._update_time_display()



#     def _update_progress(self):
#         """Update progress every second."""
#         if self.remaining_time_seconds > 0:
#             self.remaining_time_seconds -= 1
#             self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
#             self._update_time_display()
#         else:
#             self.progress_timer.stop()
#             self._finish_cleaning()

#     def _update_time_display(self):
#         """Format and display remaining time."""
#         minutes = self.remaining_time_seconds // 60
#         seconds = self.remaining_time_seconds % 60
#         self.time_label.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

#     def _finish_cleaning(self):
#         """Handle cycle completion."""
#         self.cleaning_in_progress = False
#         self.current_phase = "Limpieza completada"
#         self.phase_label.setText(self.current_phase)
#         self.phase_label.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
#         self.time_label.setText("Tiempo restante: 00:00")
#         self.progress_bar.setValue(self.total_time_seconds)
#         try:            
#             self._write_boolean_command("dialyStartDialysisButt", False)
#             self._write_boolean_command("dialyStopDialysisButt",True)
#         except Exception as e:
#             logger.error(f"Error {e}")

#         self.start_button.setText("Reiniciar")
#         self.start_button.setEnabled(True)

        
#         try:
#             self.start_button.clicked.disconnect()
#         except TypeError:
#             pass
#         self.start_button.clicked.connect(self.reset_ui)

#     def update_values(self, new_values: dict):
#         """Receive and process updated values from main window."""
#         self.current_values = new_values
#         pass


#     def update_buttons_state(self, status_code):
#         """
#         Habilita o deshabilita el botón de limpieza basado en el estado.
#         Estandarizado con DialysisScreen.
#         """
#         if self.cleaning_in_progress:
#             return

        
#         style_disabled = """
#             QPushButton {
#                 background: #334155; color: #64748b;
#                 font-size: 38px; font-weight: bold; border: none;
#                 border-radius: 16px; padding: 10px;
#             }
#         """
#         # Función para aplicar estilo habilitado (Verde original)
#         def set_enabled_style(btn):
#             color = btn.property("base_color")
#             btn.setStyleSheet(f"""
#                 QPushButton {{
#                     background: {color}; color: white;
#                     font-size: 38px; font-weight: bold; border: none;
#                     border-radius: 16px; padding: 10px;
#                 }}
#                 QPushButton:hover {{ background: #065f46; }}
#                 QPushButton:pressed {{ background: #064e3b; }}
#             """)

#         # Lógica de Estados
#         # 6 = INFUSION (Listo para limpieza)
#         if status_code == 7:
#             if not self.start_button.isEnabled():
#                 self.start_button.setEnabled(True)
#                 set_enabled_style(self.start_button)
                
#                 # Feedback visual en etiquetas
#                 self.current_phase = "Sistema listo para limpieza"
#                 self.phase_label.setText(self.current_phase)
#                 self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
        
#         else:
#             # Cualquier otro estado deshabilita el botón
#             if self.start_button.isEnabled():
#                 self.start_button.setEnabled(False)
#                 self.start_button.setStyleSheet(style_disabled)
                
#                 # Feedback visual
#                 self.current_phase = f"Esperando estado (Actual: {status_code})"
#                 self.phase_label.setText(self.current_phase)
#                 self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")


#     def on_user_boolean_command(self, tag, state):
#         self.request_boolean_change.emit(tag, state)

#     def on_user_input_setpoint(self, tag, value):
#         self.request_setpoint_change.emit(tag, value)       



# class CleaningScreen(QWidget):
#     """
#     Cleaning and disinfection screen.
#     Manages the chemical disinfection cycle with progress bar,
#     remaining time display, and conditional start button.
#     """
#     request_setpoint_change = Signal(str, float)
#     request_boolean_change = Signal(str, bool)

#     def __init__(self, parent=None, values_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.current_values = values_dict if values_dict is not None else {}

#         # Internal state
#         self.cleaning_in_progress = False

#         # Fixed size matching stacked widget
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setStyleSheet("background: #0f172a;")  # Industrial dark blue

#         # Cycle tracking
#         self.current_phase = "Esperando condiciones..."
#         self.total_time_seconds = 0
#         self.remaining_time_seconds = 0

#         # Timer for progress updates (1 second interval)
#         self.progress_timer = QTimer(self)
#         self.progress_timer.timeout.connect(self._update_progress)

#         self.setup_ui()

#     def setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(60, 40, 60, 40)
#         main_layout.setSpacing(30)

#         # ── Title ────────────────────────────────────────────────────────────────
#         title_label = QLabel("Limpieza / Desinfección")
#         title_label.setStyleSheet("""
#             color: #3d3d3d;
#             font-size: 52px;
#             font-weight: bold;
#             background: transparent;
#         """)
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)

#         # ── Current Phase / Status ───────────────────────────────────────────────
#         self.phase_label = QLabel(self.current_phase)
#         self.phase_label.setStyleSheet("""
#             color: #94a3b8;
#             font-size: 32px;
#             font-weight: bold;
#             background: transparent;
#             min-height: 60px;
#         """)
#         self.phase_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.phase_label)

#         # ── Progress Bar ─────────────────────────────────────────────────────────
#         self.progress_bar = QProgressBar()
#         self.progress_bar.setMinimum(0)
#         self.progress_bar.setMaximum(100)
#         self.progress_bar.setValue(0)
#         self.progress_bar.setTextVisible(True)
#         self.progress_bar.setFormat("%p% - %v/%m seg")
#         self.progress_bar.setFixedHeight(60)
#         self.progress_bar.setStyleSheet("""
#             QProgressBar {
#                 background: #1e293b;
#                 border: 2px solid #475569;
#                 border-radius: 10px;
#                 text-align: center;
#                 color: #ffffff;
#                 font-size: 24px;
#                 font-weight: bold;
#             }
#             QProgressBar::chunk {
#                 background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
#                                             stop:0 #3b82f6, stop:1 #60a5fa);
#                 border-radius: 8px;
#             }
#         """)
#         main_layout.addWidget(self.progress_bar)

#         # ── Remaining Time ───────────────────────────────────────────────────────
#         self.time_label = QLabel("Tiempo restante: --:--")
#         self.time_label.setStyleSheet("""
#             color: #cbd5e1;
#             font-size: 28px;
#             font-weight: bold;
#             background: transparent;
#         """)
#         self.time_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(self.time_label)

    
#         main_layout.addStretch()

#         # ── Start / Restart Button ───────────────────────────────────────────────

        
#         button_layout = QHBoxLayout()
#         button_layout.addStretch()

#         self.start_button = QPushButton("Iniciar limpieza")
#         self.start_button.setFixedSize(300, 100)
#         self.start_button.setEnabled(False)  
#         self.start_button.setProperty("base_color", "#047857")         
#         self.start_button.setStyleSheet("""
#             QPushButton {
#                 background: #047857;
#                 color: white;
#                 font-size: 38px;
#                 font-weight: bold;
#                 border: none;
#                 border-radius: 16px;
#                 padding: 10px;
#             }
#             QPushButton:hover { background: #065f46; }
#             QPushButton:pressed { background: #064e3b; }
#             QPushButton:disabled { background: #334155; color: #64748b; }
#         """)
#         self.start_button.clicked.connect(self._start_cleaning)
#         button_layout.addWidget(self.start_button)

#         button_layout.addStretch()
#         main_layout.addLayout(button_layout)

#         # Initial UI state
#         self.phase_label.setText("Esperando estado listo...")
#         self.progress_bar.setValue(0)
#         self.progress_timer.stop()

#     def reset_ui(self):
#         """Reset UI to initial waiting state."""
#         self.cleaning_in_progress = False
#         self.current_phase = "Esperando condiciones..."
#         self.phase_label.setText(self.current_phase)
#         self.progress_bar.setValue(0)
#         self.time_label.setText("Tiempo restante: --:--")

#         self.start_button.setEnabled(False)
#         self.start_button.setText("Iniciar limpieza")

        
#         try:
#             self.start_button.clicked.disconnect()
#         except TypeError:
#             pass
#         self.start_button.clicked.connect(self._start_cleaning)

#         self.progress_timer.stop()

#     def _start_cleaning(self):
#         """Initiate the disinfection cycle."""
#         self.cleaning_in_progress = True

        
#         try:
#             self.on_user_input_setpoint("treatmentModeSelection", 3.0)
#             self.on_user_boolean_command("dialyModeOperationStart",True)
#         except Exception as e:
#             logger.error(f"Error {e}")

#         # Configure cycle duration (900 seconds = 15 minutes)
#         self.total_time_seconds = 900
#         self.remaining_time_seconds = self.total_time_seconds

#         self.current_phase = "Desinfección química en curso..."
#         self.phase_label.setText(self.current_phase)
#         self.start_button.setEnabled(False)
#         self.start_button.setText("En proceso...")

#         self.progress_bar.setMaximum(self.total_time_seconds)
#         self.progress_bar.setValue(0)

#         # Start 1-second update timer
#         self.progress_timer.start(1000)

#         self._update_time_display()