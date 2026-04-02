# gui/service/comm_port_screen.py

import serial.tools.list_ports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox
from PySide6.QtCore import Signal
import json
import os
import logging

logger = logging.getLogger(__name__)

# Directorio para guardar la configuración (creará una carpeta 'config' en la raíz del proyecto)
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "sensor_comm_config.json")

class CommPortScreen(QWidget):
    # Señales para notificar a la app principal cuando cambie la configuración
    config_changed = Signal(str, str, bool) # id_sensor, puerto, habilitado

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded_settings = self._load_settings() # Cargar configuración al iniciar
        self.setup_ui()
        self._apply_loaded_settings_to_ui() # Aplicar la configuración cargada a la UI

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Configuración de Puertos de Comunicación (Sensores Externos)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # --- Detectar y filtrar puertos ---
        all_comports = serial.tools.list_ports.comports()
        
        # Siempre queremos la opción "Auto" al principio
        filtered_ports_devices = ["Auto"] 

        for p in all_comports:
            # Ahora verificamos 'manufacturer' en lugar de 'description'
            # y también consideraremos el caso en que 'manufacturer' sea None
            if p.manufacturer and "FTDI" not in p.manufacturer.upper():
                filtered_ports_devices.append(p.device)
            elif not p.manufacturer: # Si no tiene fabricante, lo incluimos por defecto
                 filtered_ports_devices.append(p.device)
            else: # El puerto tiene fabricante y contiene "FTDI"
                logger.info(f"Puerto '{p.device}' (Manuf: '{p.manufacturer}') excluido por contener 'FTDI'.")


        # Si después del filtrado no hay puertos adicionales, solo se mostrará "Auto"
        if len(filtered_ports_devices) == 1 and filtered_ports_devices[0] == "Auto":
            logger.warning("No se encontraron puertos COM disponibles para sensores externos después de filtrar.")
        else:
            logger.info(f"Puertos disponibles para sensores externos para selección: {filtered_ports_devices}")

        # --- Sensor de Conductividad Patrón ---
        self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
        # Estilo para el título del GroupBox
        self.grp_cond.setStyleSheet("font-size: 30px; color: #000000;") 
        lyt_cond = QHBoxLayout(self.grp_cond)
        
        self.chk_cond = QCheckBox("Habilitar Comunicación")
        self.chk_cond.setStyleSheet("""
            QCheckBox {
                color: #000000;
                font-size: 26px; /* Tamaño de la letra del texto de la etiqueta */
                spacing: 15px; /* Aumenta el espacio entre el indicador y el texto */
            }
            QCheckBox::indicator {
                width: 35px;   /* Ancho del recuadro del checkbox */
                height: 35px;  /* Alto del recuadro del checkbox */
            }
        """)
        self.cmb_cond_port = QComboBox()
        self.cmb_cond_port.setStyleSheet("color: #000000; font-size: 26px;")
        self.cmb_cond_port.addItems(filtered_ports_devices) # Usar la lista filtrada
        
        # --- CORRECCIÓN AQUÍ ---
        label_cond_port = QLabel("Puerto:")
        label_cond_port.setStyleSheet("color: #000000; font-size: 26px;")
        lyt_cond.addWidget(self.chk_cond)
        lyt_cond.addWidget(label_cond_port) # Añadir el QLabel ya estilizado
        lyt_cond.addWidget(self.cmb_cond_port)
        layout.addWidget(self.grp_cond)

        # --- Sensor Bioimpedancia/Urea ---
        self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
        # Estilo para el título del GroupBox
        self.grp_bioz.setStyleSheet("font-size: 30px; color: #000000;") 
        lyt_bioz = QHBoxLayout(self.grp_bioz)
        
        self.chk_bioz = QCheckBox("Habilitar Comunicación")
        self.chk_bioz.setStyleSheet("""
            QCheckBox {
                color: #000000;
                font-size: 26px; /* Tamaño de la letra del texto de la etiqueta */
                spacing: 15px; /* Aumenta el espacio entre el indicador y el texto */
            }
            QCheckBox::indicator {
                width: 35px;   /* Ancho del recuadro del checkbox */
                height: 35px;  /* Alto del recuadro del checkbox */
            }
        """)
        self.cmb_bioz_port = QComboBox()
        self.cmb_bioz_port.setStyleSheet("color: #000000; font-size: 26px;")
        self.cmb_bioz_port.addItems(filtered_ports_devices) # Usar la lista filtrada

        # --- CORRECCIÓN AQUÍ ---
        label_bioz_port = QLabel("Puerto:")
        label_bioz_port.setStyleSheet("color: #000000; font-size: 26px;")
        lyt_bioz.addWidget(self.chk_bioz)
        lyt_bioz.addWidget(label_bioz_port) # Añadir el QLabel ya estilizado
        lyt_bioz.addWidget(self.cmb_bioz_port)
        layout.addWidget(self.grp_bioz)

        # Botón de aplicar cambios
        self.btn_apply = QPushButton("Aplicar Cambios")
        self.btn_apply.setStyleSheet("""
            QPushButton { 
                background-color: #3b82f6; /* Color de fondo normal (azul) */
                color: white; 
                font-size: 18px; 
                padding: 10px;
                border-radius: 5px; /* Opcional: bordes redondeados para un look más moderno */
            }
            QPushButton:hover {
                background-color: #60a5fa; /* Color más claro al pasar el ratón por encima */
            }
            QPushButton:pressed {
                background-color: #1e40af; /* Color más oscuro o diferente al presionar */
                border: 2px solid #0056b3; /* Opcional: un borde visible al presionar */
                padding: 8px 10px 10px 12px; /* Opcional: un ligero "desplazamiento" para efecto 3D */
            }
        """)
        self.btn_apply.clicked.connect(self.apply_configurations)
        layout.addWidget(self.btn_apply)
        
        layout.addStretch()
    
    # ... (el resto del código de la clase CommPortScreen es el mismo) ...
    def _load_settings(self):
        """Carga la configuración desde el archivo JSON o retorna valores por defecto."""
        default_settings = {
            "conductivity_sensor": {"port": "Auto", "enabled": False},
            "bioz_urea_sensor": {"port": "Auto", "enabled": False},
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    settings = json.load(f)
                logger.info(f"Configuración de puertos cargada desde {CONFIG_FILE}")
                # Validar que las claves necesarias existen, si no, usar default
                for sensor_key in default_settings:
                    if sensor_key not in settings:
                        settings[sensor_key] = default_settings[sensor_key]
                    if "port" not in settings[sensor_key]:
                        settings[sensor_key]["port"] = default_settings[sensor_key]["port"]
                    if "enabled" not in settings[sensor_key]:
                        settings[sensor_key]["enabled"] = default_settings[sensor_key]["enabled"]
                return settings
            except json.JSONDecodeError as e:
                logger.error(f"Error al leer el archivo de configuración JSON {CONFIG_FILE}: {e}")
            except Exception as e:
                logger.error(f"Error inesperado al cargar la configuración desde {CONFIG_FILE}: {e}")
        logger.warning("Archivo de configuración no encontrado o inválido. Usando configuración por defecto.")
        return default_settings

    def _save_settings(self, settings):
        """Guarda la configuración actual en un archivo JSON."""
        os.makedirs(CONFIG_DIR, exist_ok=True) # Asegura que el directorio exista
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Configuración de puertos guardada en {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error al guardar la configuración en {CONFIG_FILE}: {e}")

    def _apply_loaded_settings_to_ui(self):
        """Aplica las configuraciones cargadas a los widgets de la UI."""
        # Sensor de Conductividad
        cond_settings = self._loaded_settings.get("conductivity_sensor", {})
        # Solo intentar establecer el texto si el puerto cargado está en la lista actual de opciones
        port_to_set_cond = cond_settings.get("port", "Auto")
        if port_to_set_cond in [self.cmb_cond_port.itemText(i) for i in range(self.cmb_cond_port.count())]:
            self.cmb_cond_port.setCurrentText(port_to_set_cond)
        else:
            self.cmb_cond_port.setCurrentText("Auto") # Fallback a Auto si el puerto guardado no es válido/visible
            logger.warning(f"Puerto de conductividad '{port_to_set_cond}' no válido o filtrado. Se estableció 'Auto'.")

        self.chk_cond.setChecked(cond_settings.get("enabled", False))

        # Sensor Bioimpedancia/Urea
        bioz_settings = self._loaded_settings.get("bioz_urea_sensor", {})
        # Solo intentar establecer el texto si el puerto cargado está en la lista actual de opciones
        port_to_set_bioz = bioz_settings.get("port", "Auto")
        if port_to_set_bioz in [self.cmb_bioz_port.itemText(i) for i in range(self.cmb_bioz_port.count())]:
            self.cmb_bioz_port.setCurrentText(port_to_set_bioz)
        else:
            self.cmb_bioz_port.setCurrentText("Auto") # Fallback a Auto si el puerto guardado no es válido/visible
            logger.warning(f"Puerto de BioZ '{port_to_set_bioz}' no válido o filtrado. Se estableció 'Auto'.")
            
        self.chk_bioz.setChecked(bioz_settings.get("enabled", False))
        
        logger.debug("Configuración cargada aplicada a la UI.")


    def apply_configurations(self):
        """
        Guarda la configuración actual de la UI en el archivo JSON
        y emite las señales para actualizar los controladores.
        """
        current_settings = {
            "conductivity_sensor": {
                "port": self.cmb_cond_port.currentText(),
                "enabled": self.chk_cond.isChecked()
            },
            "bioz_urea_sensor": {
                "port": self.cmb_bioz_port.currentText(),
                "enabled": self.chk_bioz.isChecked()
            },
        }
        self._save_settings(current_settings) # Guardar la configuración actual

        # Emitir señales con la nueva configuración para que los controladores la tomen
        self.emit_current_configurations()
        
        # Opcional: mostrar un mensaje de confirmación al usuario
        # from gui.components.ui_components import show_dark_message
        # show_dark_message(self, "Configuración Guardada", "La configuración de puertos ha sido guardada y aplicada.", icon=QMessageBox.Information)

    def emit_current_configurations(self):
        """
        Emite la configuración actual de la UI (ya sea cargada o modificada por el usuario).
        Esto es útil para que HemodialysisHMI la recoja al inicio.
        """
        self.config_changed.emit("CONDUCTIVITY", self.cmb_cond_port.currentText(), self.chk_cond.isChecked())
        self.config_changed.emit("BIOZ", self.cmb_bioz_port.currentText(), self.chk_bioz.isChecked())

# import serial.tools.list_ports
# from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox
# from PySide6.QtCore import Signal
# import json
# import os
# import logging

# logger = logging.getLogger(__name__)

# # Directorio para guardar la configuración (creará una carpeta 'config' en la raíz del proyecto)
# CONFIG_DIR = "config"
# CONFIG_FILE = os.path.join(CONFIG_DIR, "sensor_comm_config.json")

# class CommPortScreen(QWidget):
#     # Señales para notificar a la app principal cuando cambie la configuración
#     config_changed = Signal(str, str, bool) # id_sensor, puerto, habilitado

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._loaded_settings = self._load_settings() # Cargar configuración al iniciar
#         self.setup_ui()
#         self._apply_loaded_settings_to_ui() # Aplicar la configuración cargada a la UI

#     def setup_ui(self):
#         layout = QVBoxLayout(self)
        
#         title = QLabel("Configuración de Puertos de Comunicación (Sensores Externos)")
#         title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
#         layout.addWidget(title)

#         # --- Detectar y filtrar puertos ---
#         all_comports = serial.tools.list_ports.comports()
        
#         filtered_ports_devices = ["Auto"] 

#         for p in all_comports:
#             # Ahora verificamos 'manufacturer' en lugar de 'description'
#             # y también consideraremos el caso en que 'manufacturer' sea None
#             if p.manufacturer and "FTDI" not in p.manufacturer.upper():
#                 filtered_ports_devices.append(p.device)
#             elif not p.manufacturer: # Si no tiene fabricante, lo incluimos por defecto
#                  filtered_ports_devices.append(p.device)
#             else: # El puerto tiene fabricante y contiene "FTDI"
#                 logger.info(f"Puerto '{p.device}' (Manuf: '{p.manufacturer}') excluido por contener 'FTDI'.")

#         # Si después del filtrado no hay puertos adicionales, solo se mostrará "Auto"
#         if len(filtered_ports_devices) == 1 and filtered_ports_devices[0] == "Auto":
#             logger.warning("No se encontraron puertos COM disponibles para sensores externos después de filtrar los puertos FTDI.")
#         else:
#             logger.info(f"Puertos disponibles para sensores externos: {filtered_ports_devices}")

#         # --- Sensor de Conductividad Patrón ---
#         self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
#         # El estilo del QGroupBox afecta también a los QCheckBox dentro si no se especifican.
#         # Es mejor aplicar los estilos directamente a cada widget para más control.
#         # self.grp_cond.setStyleSheet("color: #000000; font-size: 30px;") # Esto afecta el título del GroupBox

#         lyt_cond = QHBoxLayout(self.grp_cond)
        
#         self.chk_cond = QCheckBox("Habilitar Comunicación")
#         self.chk_cond.setStyleSheet("""
#             QCheckBox {
#                 color: #000000;
#                 font-size: 26px; /* Tamaño de la letra del texto de la etiqueta */
#                 spacing: 15px; /* Aumenta el espacio entre el indicador y el texto */
#             }
#             QCheckBox::indicator {
#                 width: 35px;   /* Ancho del recuadro del checkbox */
#                 height: 35px;  /* Alto del recuadro del checkbox */
#                 /* Opcional: puedes personalizar aún más el indicador */
#                 /* background-color: lightgray; */
#                 /* border: 2px solid gray; */
#                 /* border-radius: 5px; */
#             }
#             QCheckBox::indicator:checked {
#                 /* Puedes usar un color diferente para el fondo del recuadro cuando está marcado */
#                 /* background-color: #3b82f6; */
#                 /* O un borde diferente */
#                 /* border: 2px solid #1e40af; */
#             }
#         """)
#         self.cmb_cond_port = QComboBox()
#         self.cmb_cond_port.setStyleSheet("color: #000000; font-size: 26px;")
#         self.cmb_cond_port.addItems(filtered_ports_devices) # Usar la lista filtrada
        
#         lyt_cond.addWidget(self.chk_cond)
#         lyt_cond.addWidget(QLabel("Puerto:").setStyleSheet("color: #000000; font-size: 26px;")) # Asegura que la etiqueta "Puerto:" también sea grande
#         lyt_cond.addWidget(self.cmb_cond_port)
#         layout.addWidget(self.grp_cond)

#         # --- Sensor Bioimpedancia/Urea ---
#         self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
#         # Estilo para el título del GroupBox si quieres que sea más grande
#         self.grp_bioz.setStyleSheet("font-size: 30px; color: #000000;") 
#         lyt_bioz = QHBoxLayout(self.grp_bioz)
        
#         self.chk_bioz = QCheckBox("Habilitar Comunicación")
#         self.chk_bioz.setStyleSheet("""
#             QCheckBox {
#                 color: #000000;
#                 font-size: 26px; /* Tamaño de la letra del texto de la etiqueta */
#                 spacing: 15px; /* Aumenta el espacio entre el indicador y el texto */
#             }
#             QCheckBox::indicator {
#                 width: 35px;   /* Ancho del recuadro del checkbox */
#                 height: 35px;  /* Alto del recuadro del checkbox */
#                 /* Opcional: puedes personalizar aún más el indicador */
#             }
#         """)
#         self.cmb_bioz_port = QComboBox()
#         self.cmb_bioz_port.setStyleSheet("color: #000000; font-size: 26px;")
#         self.cmb_bioz_port.addItems(filtered_ports_devices) # Usar la lista filtrada

#         lyt_bioz.addWidget(self.chk_bioz)
#         lyt_bioz.addWidget(QLabel("Puerto:").setStyleSheet("color: #000000; font-size: 26px;")) # Asegura que la etiqueta "Puerto:" también sea grande
#         lyt_bioz.addWidget(self.cmb_bioz_port)
#         layout.addWidget(self.grp_bioz)


#         # Botón de aplicar cambios
#         self.btn_apply = QPushButton("Aplicar Cambios")
#         self.btn_apply.setStyleSheet("""
#             QPushButton { 
#                 background-color: #3b82f6; /* Color de fondo normal (azul) */
#                 color: #ffffff; 
#                 font-size: 18px; 
#                 padding: 10px;
#                 border-radius: 5px; /* Opcional: bordes redondeados para un look más moderno */
#             }
#             QPushButton:hover {
#                 background-color: #60a5fa; /* Color más claro al pasar el ratón por encima */
#             }
#             QPushButton:pressed {
#                 background-color: #1e40af; /* Color más oscuro o diferente al presionar */
#                 border: 2px solid #0056b3; /* Opcional: un borde visible al presionar */
#                 padding: 8px 10px 10px 12px; /* Opcional: un ligero "desplazamiento" para efecto 3D */
#             }
#         """)
#         self.btn_apply.clicked.connect(self.apply_configurations)
#         layout.addWidget(self.btn_apply)        
#         layout.addStretch()
    
#     def _load_settings(self):
#         """Carga la configuración desde el archivo JSON o retorna valores por defecto."""
#         default_settings = {
#             "conductivity_sensor": {"port": "Auto", "enabled": False},
#             "bioz_urea_sensor": {"port": "Auto", "enabled": False},
#         }
#         if os.path.exists(CONFIG_FILE):
#             try:
#                 with open(CONFIG_FILE, 'r') as f:
#                     settings = json.load(f)
#                 logger.info(f"Configuración de puertos cargada desde {CONFIG_FILE}")
#                 # Validar que las claves necesarias existen, si no, usar default
#                 for sensor_key in default_settings:
#                     if sensor_key not in settings:
#                         settings[sensor_key] = default_settings[sensor_key]
#                     if "port" not in settings[sensor_key]:
#                         settings[sensor_key]["port"] = default_settings[sensor_key]["port"]
#                     if "enabled" not in settings[sensor_key]:
#                         settings[sensor_key]["enabled"] = default_settings[sensor_key]["enabled"]
#                 return settings
#             except json.JSONDecodeError as e:
#                 logger.error(f"Error al leer el archivo de configuración JSON {CONFIG_FILE}: {e}")
#             except Exception as e:
#                 logger.error(f"Error inesperado al cargar la configuración desde {CONFIG_FILE}: {e}")
#         logger.warning("Archivo de configuración no encontrado o inválido. Usando configuración por defecto.")
#         return default_settings

#     def _save_settings(self, settings):
#         """Guarda la configuración actual en un archivo JSON."""
#         os.makedirs(CONFIG_DIR, exist_ok=True) # Asegura que el directorio exista
#         try:
#             with open(CONFIG_FILE, 'w') as f:
#                 json.dump(settings, f, indent=4)
#             logger.info(f"Configuración de puertos guardada en {CONFIG_FILE}")
#         except Exception as e:
#             logger.error(f"Error al guardar la configuración en {CONFIG_FILE}: {e}")

#     def _apply_loaded_settings_to_ui(self):
#         """Aplica las configuraciones cargadas a los widgets de la UI."""
#         # Sensor de Conductividad
#         cond_settings = self._loaded_settings.get("conductivity_sensor", {})
#         self.cmb_cond_port.setCurrentText(cond_settings.get("port", "Auto"))
#         self.chk_cond.setChecked(cond_settings.get("enabled", False))

#         # Sensor Bioimpedancia/Urea
#         bioz_settings = self._loaded_settings.get("bioz_urea_sensor", {})
#         self.cmb_bioz_port.setCurrentText(bioz_settings.get("port", "Auto"))
#         self.chk_bioz.setChecked(bioz_settings.get("enabled", False))
        
#         logger.debug("Configuración cargada aplicada a la UI.")


#     def apply_configurations(self):
#         """
#         Guarda la configuración actual de la UI en el archivo JSON
#         y emite las señales para actualizar los controladores.
#         """
#         current_settings = {
#             "conductivity_sensor": {
#                 "port": self.cmb_cond_port.currentText(),
#                 "enabled": self.chk_cond.isChecked()
#             },
#             "bioz_urea_sensor": {
#                 "port": self.cmb_bioz_port.currentText(),
#                 "enabled": self.chk_bioz.isChecked()
#             },
#         }
#         self._save_settings(current_settings) # Guardar la configuración actual

#         # Emitir señales con la nueva configuración para que los controladores la tomen
#         self.emit_current_configurations()
        
#         # Opcional: mostrar un mensaje de confirmación al usuario
#         # from gui.components.ui_components import show_dark_message
#         # show_dark_message(self, "Configuración Guardada", "La configuración de puertos ha sido guardada y aplicada.", icon=QMessageBox.Information)

#     def emit_current_configurations(self):
#         """
#         Emite la configuración actual de la UI (ya sea cargada o modificada por el usuario).
#         Esto es útil para que HemodialysisHMI la recoja al inicio.
#         """
#         self.config_changed.emit("CONDUCTIVITY", self.cmb_cond_port.currentText(), self.chk_cond.isChecked())
#         self.config_changed.emit("BIOZ", self.cmb_bioz_port.currentText(), self.chk_bioz.isChecked())