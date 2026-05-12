# # gui/configuration/cleanning_config_screen.py
# gui/configuration/cleanning_config_screen.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QButtonGroup, QPushButton, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal
import time
import logging
import json
import os

from gui.components.floating_message import FloatingMessage # Asumo que esta clase está disponible
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit

logger = logging.getLogger(__name__)

# Definimos la ruta del archivo de configuración
CONFIG_FILE_PATH = "config/cleaning_config.json"

class CleanningConfigScreen(QWidget):
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool) 

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(True)
        
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#f8f8f8"))
        self.setPalette(palette)

        self.pending_mode_change_deadline = None
        self.command_mode_value = 0.0 # Guardará el modo actual (0.0 o 1.0)
        self.current_mode_tag = "DesinftectionMode" # Valor por defecto

        self.init_ui()
        self._load_config_for_display() # Cargar configuración al iniciar la pantalla de configuración

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Configuración de Desinfección")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        _line = QFrame()
        _line.setFrameShape(QFrame.HLine)
        _line.setStyleSheet("background: #d3d3d3; max-height: 2px;")
        main_layout.addWidget(_line)

        # === Frame para modos ===
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 20px; border: 1px solid #e5e5e5;")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(20)

        lbl_mode = QLabel("Seleccione tipo de desinfección predeterminado")
        lbl_mode.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000; border: none;")
        mode_layout.addWidget(lbl_mode)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        self._short_chemical_desinfection = QPushButton("Desinfección Química Corta")
        self._long_chemical_desinfection = QPushButton("Desinfección Química Larga")

        self.btn_mode_group = QButtonGroup(self)
        self.btn_mode_group.setExclusive(True)

        btn_mode_info = [
            (self._short_chemical_desinfection, "DesinftectionMode", 0.0),
            (self._long_chemical_desinfection, "DesinftectionMode", 1.0),
        ]

        self.style_mode_unchecked = """
            QPushButton {
                background: #3b82f6; color: #ffffff; font-size: 22px; font-weight: bold;
                border-radius: 12px; padding: 15px 25px; border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
        """
        self.style_mode_checked = """
            QPushButton {
                background: #22c55e; color: #ffffff; font-size: 22px; font-weight: bold;
                border-radius: 12px; padding: 15px 25px; border: 2px solid #16a34a;
            }
        """

        for btn, tag, value in btn_mode_info:
            btn.setStyleSheet(self.style_mode_unchecked) 
            btn.setCheckable(True)
            btn.toggled.connect(lambda checked, b=btn, t=tag, v=value:
                                self._on_mode_toggled(b, t, v, checked))
            buttons_layout.addWidget(btn)
            self.btn_mode_group.addButton(btn)

        mode_layout.addLayout(buttons_layout)
        main_layout.addWidget(mode_frame)

        # === Input de Tiempo ===
        lbl_time = QLabel("Tiempo de desinfección (hh:mm):") 
        lbl_time.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(lbl_time)

        # ClickableLineEdit para el tiempo
        self.desinfection_time_input = ClickableLineEdit("00:00")
        self.desinfection_time_input.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #FFFFFF;")
        self.desinfection_time_input.setAlignment(Qt.AlignCenter)
        self.desinfection_time_input.setReadOnly(True)
        self.desinfection_time_input.clicked.connect(
            lambda: self.open_time_numpad(
                self.desinfection_time_input,
                title="Tiempo de Desinfección"
            )
         )
        main_layout.addWidget(self.desinfection_time_input)

        main_layout.addStretch(1)

        # === Botón Guardar ===
        save_button = QPushButton("Guardar Configuración")
        save_button.setStyleSheet("""
            QPushButton { background: #475569; color: #ffffff; font-size: 24px; padding: 15px; border-radius: 8px;}
            QPushButton:hover { background: #334155; }
        """)
        save_button.clicked.connect(self.save_configuration)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)

    def _load_config_for_display(self):
        """
        Carga la configuración de los modos desde el JSON y actualiza la UI.
        Se llama al iniciar la pantalla de configuración.
        """
        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.error(f"Error al leer configuración del JSON: {e}")

        # Obtener el último modo activo o usar uno por defecto
        last_active_mode_value = config_data.get("last_active_mode_value", 0.0) # Por defecto, modo corto

        # Simular el clic en el botón correspondiente para cargar sus valores
        if last_active_mode_value == 0.0:
            self._short_chemical_desinfection.setChecked(True)
        elif last_active_mode_value == 1.0:
            self._long_chemical_desinfection.setChecked(True)
        else: # Si el valor no es válido, por defecto el corto
             self._short_chemical_desinfection.setChecked(True)

    def _on_mode_toggled(self, button: QPushButton, tag: str, value: float, checked: bool):
        if checked:
            button.setStyleSheet(self.style_mode_checked)
            self.command_mode_value = value
            self.current_mode_tag = tag 
            # Cargar el tiempo específico para el modo seleccionado en el ClickableLineEdit
            self._display_mode_time(value)
        else:
            button.setStyleSheet(self.style_mode_unchecked)

    def _display_mode_time(self, mode_value: float):
        """Carga el tiempo guardado para el mode_value y lo muestra en el ClickableLineEdit."""
        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.error(f"Error al leer configuración para display: {e}")
        
        # Obtener la configuración específica para el modo
        mode_config = config_data.get("modes", {}).get(str(mode_value), {"time_hours": 0, "time_minutes": 15})
        hours = mode_config.get("time_hours", 0)
        minutes = mode_config.get("time_minutes", 15)
        
        self.desinfection_time_input.setText(f"{hours:02d}:{minutes:02d}")


    def save_configuration(self):
        # 1. Validar si se seleccionó un modo
        if not hasattr(self, 'current_mode_tag'):
            logger.warning("No se ha seleccionado ningún modo para guardar.")
            self.show_warning_message("Seleccione un modo de desinfección", 3000)
            return

        # 2. Obtener horas y minutos del ClickableLineEdit
        time_str = self.desinfection_time_input.text() 
        try:
            hours, minutes = map(int, time_str.split(':'))
        except ValueError:
            hours, minutes = 0, 0
            logger.error("Error al parsear el tiempo del ClickableLineEdit")
            self.show_error_message("Error al leer el tiempo, revise formato", 3000)
            return

        # 3. Leer la configuración existente (o inicializar con valores por defecto si no existe o está incompleta)
        current_config = {
            "modes": {}, # Aseguramos que 'modes' siempre sea un diccionario vacío por defecto
            "last_active_mode_value": 0.0,
            "last_active_mode_tag": "DesinftectionMode"
        }
        
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Fusionar los datos cargados con la configuración por defecto
                    # Esto asegura que si el archivo tiene keys viejas, se mantengan,
                    # y si le faltan las nuevas (como 'modes'), se añadan del default.
                    current_config.update(loaded_data)
                    
                    # Además, asegurarnos de que 'modes' sea un diccionario, por si el JSON lo cargó de otra forma (o no existía)
                    if not isinstance(current_config.get("modes"), dict):
                        current_config["modes"] = {}

            except json.JSONDecodeError:
                logger.error(f"El archivo JSON de configuración está corrupto. Se recreará con los valores actuales.")
                self.show_warning_message("Archivo de configuración corrupto, se recreará.", 4000)
                # Si el JSON está corrupto, current_config ya tiene los valores por defecto que queremos.
            except Exception as e:
                logger.error(f"Error inesperado al leer JSON existente: {e}")
                self.show_error_message(f"Error al leer configuración: {e}", 4000)
        
        # 4. Actualizar la configuración del modo actual
        mode_name = "Corta" if self.command_mode_value == 0.0 else "Larga"
        current_config["modes"][str(self.command_mode_value)] = {
            "time_hours": hours,
            "time_minutes": minutes,
            "mode_name": mode_name
        }
        
        # 5. Actualizar cuál fue el último modo activo
        current_config["last_active_mode_value"] = self.command_mode_value
        current_config["last_active_mode_tag"] = self.current_mode_tag

        # 6. Guardar la configuración completa en el archivo JSON
        try:
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as json_file:
                json.dump(current_config, json_file, indent=4, ensure_ascii=False)
            logger.info(f"Configuración guardada en JSON: {current_config}")
            self.show_success_message("Configuración guardada exitosamente", 2000)
        except Exception as e:
            logger.error(f"Error al guardar la configuración en JSON: {e}")
            self.show_error_message(f"Error al guardar: {e}", 3000)


    def open_time_numpad(self, time_widget, tag_hours: str = None, tag_minutes: str = None,
                         timer_id: str = None, title: str = "Config. Tiempo"):
        
        current_text = time_widget.text() if time_widget.text() else "00:00"

        dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title) # Pasa el tiempo actual

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            time_widget.setText(f"{hours:02d}:{minutes:02d}")
            logger.debug(f"Tiempo actualizado en la pantalla: {hours:02d}:{minutes:02d}")

    # Métodos show_floating_message, show_success_message, etc. (se mantienen igual)
    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        """Método genérico (recomendado)"""
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        
        self._floating_msg.show_floating_message(text, timeout_ms)

    # Métodos específicos (más semánticos)
    def show_success_message(self, text: str, timeout_ms: int = 4000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_success_message(text, timeout_ms)

    def show_info_message(self, text: str, timeout_ms: int = 3800):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_info_message(text, timeout_ms)

    def show_warning_message(self, text: str, timeout_ms: int = 4500):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_warning_message(text, timeout_ms)
    
    def show_error_message(self, text: str, timeout_ms: int = 5000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_error_message(text, timeout_ms)

# from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QButtonGroup, QPushButton, QFrame
# from PySide6.QtGui import QColor
# from PySide6.QtCore import Qt, Signal
# import time
# import logging
# import json
# import os

# from gui.components.floating_message import FloatingMessage
# from gui.components.time_numpad_modal import TimeNumpadDialog
# from gui.components.ui_components import ClickableLineEdit

# logger = logging.getLogger(__name__)

# # Definimos la ruta del archivo de configuración
# CONFIG_FILE_PATH = "cleaning_config.json"

# class CleanningConfigScreen(QWidget):
#     # Definición de señales (puedes dejarlas si las usas en otra parte de la UI)
#     request_setpoint_change = Signal(str, float)
#     request_boolean_change = Signal(str, bool) 

#     def __init__(self, parent=None, values_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.current_values = values_dict if values_dict is not None else {}
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setAutoFillBackground(True)
        
#         palette = self.palette()
#         palette.setColor(self.backgroundRole(), QColor("#f8f8f8"))
#         self.setPalette(palette)

#         self.pending_mode_change_deadline = None
#         self.command_mode_value = 0.0 # Guardará el modo actual (0.0 o 1.0)

#         self.init_ui()

#     def init_ui(self):
#         main_layout = QVBoxLayout()
#         main_layout.setContentsMargins(20, 20, 20, 20)
#         main_layout.setSpacing(15)

#         title_label = QLabel("Configuración de Desinfección")
#         title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)

#         _line = QFrame()
#         _line.setFrameShape(QFrame.HLine)
#         _line.setStyleSheet("background: #d3d3d3; max-height: 2px;")
#         main_layout.addWidget(_line)

#         # === Frame para modos ===
#         mode_frame = QFrame()
#         mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 20px; border: 1px solid #e5e5e5;")
#         mode_layout = QVBoxLayout(mode_frame)
#         mode_layout.setSpacing(20)

#         lbl_mode = QLabel("Seleccione tipo de desinfección predeterminado")
#         lbl_mode.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000; border: none;")
#         mode_layout.addWidget(lbl_mode)

#         buttons_layout = QHBoxLayout()
#         buttons_layout.setSpacing(20)

#         self._short_chemical_desinfection = QPushButton("Desinfección Química Corta")
#         self._long_chemical_desinfection = QPushButton("Desinfección Química Larga")

#         self.btn_mode_group = QButtonGroup(self)
#         self.btn_mode_group.setExclusive(True)

#         btn_mode_info = [
#             (self._short_chemical_desinfection, "DesinftectionMode", 0.0),
#             (self._long_chemical_desinfection, "DesinftectionMode", 1.0),
#         ]

#         self.style_mode_unchecked = """
#             QPushButton {
#                 background: #3b82f6; color: #ffffff; font-size: 22px; font-weight: bold;
#                 border-radius: 12px; padding: 15px 25px; border: 2px solid #2563eb;
#             }
#             QPushButton:hover { background: #60a5fa; }
#         """
#         self.style_mode_checked = """
#             QPushButton {
#                 background: #22c55e; color: #ffffff; font-size: 22px; font-weight: bold;
#                 border-radius: 12px; padding: 15px 25px; border: 2px solid #16a34a;
#             }
#         """

#         for btn, tag, value in btn_mode_info:
#             btn.setStyleSheet(self.style_mode_unchecked) 
#             btn.setCheckable(True)
#             btn.toggled.connect(lambda checked, b=btn, t=tag, v=value:
#                                 self._on_mode_toggled(b, t, v, checked))
#             buttons_layout.addWidget(btn)
#             self.btn_mode_group.addButton(btn)

#         mode_layout.addLayout(buttons_layout)
#         main_layout.addWidget(mode_frame)

#         # === Input de Tiempo ===
#         lbl_time = QLabel("Tiempo de desinfección (hh:mm):") 
#         lbl_time.setStyleSheet("font-size: 20px; font-weight: bold;")
#         main_layout.addWidget(lbl_time)

#         # ClickableLineEdit para el tiempo
#         self.desinfection_time_input = ClickableLineEdit("00:00")
#         self.desinfection_time_input.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #FFFFFF;")
#         self.desinfection_time_input.setAlignment(Qt.AlignCenter)
#         self.desinfection_time_input.setReadOnly(True)
#         self.desinfection_time_input.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.desinfection_time_input,
#                 title="Tiempo de Desinfección"
#             )
#          )
#         main_layout.addWidget(self.desinfection_time_input)

#         main_layout.addStretch(1)

#         # === Botón Guardar ===
#         save_button = QPushButton("Guardar Configuración")
#         save_button.setStyleSheet("""
#             QPushButton { background: #475569; color: #ffffff; font-size: 24px; padding: 15px; border-radius: 8px;}
#             QPushButton:hover { background: #334155; }
#         """)
#         save_button.clicked.connect(self.save_configuration)
#         main_layout.addWidget(save_button)

#         self.setLayout(main_layout)

#     def _on_mode_toggled(self, button: QPushButton, tag: str, value: float, checked: bool):
#         if checked:
#             button.setStyleSheet(self.style_mode_checked)
#             self.command_mode_value = value
#             self.current_mode_tag = tag 
#         else:
#             button.setStyleSheet(self.style_mode_unchecked)

#     def save_configuration(self):
#         # 1. Validar si se seleccionó un modo
#         if not hasattr(self, 'current_mode_tag'):
#             logger.warning("No se ha seleccionado ningún modo.")
#             return

#         # 2. Obtener horas y minutos del ClickableLineEdit
#         time_str = self.desinfection_time_input.text() 
#         try:
#             hours, minutes = map(int, time_str.split(':'))
#         except ValueError:
#             hours, minutes = 0, 0
#             logger.error("Error al parsear el tiempo")

#         # 3. Determinar el nombre del modo para guardarlo en JSON de forma más legible
#         mode_name = "Corta" if self.command_mode_value == 0.0 else "Larga"

#         # 4. Crear el diccionario con la configuración
#         config_data = {
#             "mode_value": self.command_mode_value,
#             "mode_name": mode_name,
#             "mode_tag": self.current_mode_tag,
#             "time_hours": hours,
#             "time_minutes": minutes
#         }

#         # 5. Guardar en el archivo JSON
#         try:
#             with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as json_file:
#                 json.dump(config_data, json_file, indent=4, ensure_ascii=False)
#             logger.info(f"Configuración guardada en JSON: {config_data}")
#             self.show_info_message("Configuración guardada", 2000)
#             # Opcional: Emitir alguna señal de éxito a la ventana padre
#         except Exception as e:
#             logger.error(f"Error al guardar la configuración en JSON: {e}")

#     def open_time_numpad(self, time_widget, tag_hours: str = None, tag_minutes: str = None,
#                          timer_id: str = None, title: str = "Config. Tiempo"):
        
#         # Obtener el texto actual del widget
#         current_text = time_widget.text() if time_widget.text() else "00:00"

#         dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title)
        
#         if dialog.exec():
#             hours, minutes = dialog.get_hours_minutes()
#             # Actualizar el widget de texto con el resultado
#             time_widget.setText(f"{hours:02d}:{minutes:02d}")
#             logger.debug(f"Tiempo actualizado en la pantalla: {hours:02d}:{minutes:02d}")



