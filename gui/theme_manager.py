# gui/theme_manager.py
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Signal, QObject
import logging

logger = logging.getLogger(__name__)

class ThemeManager(QObject):
    theme_changed = Signal(str) # Señal para notificar cuando el tema ha cambiado

    # Definiciones de estilos QSS para cada tema
    # Puedes externalizar estos a archivos .qss y cargarlos
    LIGHT_THEME_QSS = """
        /* Estilo general para el tema claro */
        * {
            font-family: "Arial Narrow", "Helvetica Condensed", Arial, sans-serif;
            font-weight: bold;
            color: #000000;
        }
        QMainWindow { background-color: #FCFCFC; }
        QWidget { background-color: #FCFCFC; }
        QLabel { font-size: 18px; color: #000000; }
        QLineEdit, ClickableLineEdit {
            font-family: Consolas, "Courier New", monospace;
            font-size: 20px;
            color: #000000;
            border: 2px solid #000000;
            border-radius: 6px;
            padding: 4px;
            min-width: 80px;
            background: #FFFFE5;
        }
        QLineEdit:!read-only, ClickableLineEdit:!read-only {
            background: #FFFFE5;
        }
        QLineEdit:read-only, ClickableLineEdit:readOnly="true" {
            background: #FFFFE5;
            color: #000000;
            border: 2px solid #000000;
        }
        QLineEdit:focus, ClickableLineEdit:focus {
            border: 2px solid #3b82f6;
        }
        QPushButton {
            background: #3b82f6;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            padding: 6px;
            font-weight: bold;
        }
        QPushButton:pressed { background: #1e40af; }

        /* Estilo para QMessageBox en tema claro */
        QMessageBox {
            background-color: #FCFCFC;
            color: #000000;
        }
        QMessageBox QLabel {
            color: #000000;
            background-color: transparent;
            padding: 5px;
        }
        QMessageBox QPushButton {
            background-color: #3b82f6; /* Azul default para botones de mensaje */
            color: #ffffff;
            border-radius: 5px;
            padding: 5px 15px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #1e40af;
        }
        QMessageBox QPushButton:pressed {
            background-color: #0a1733;
        }
    """

    DARK_THEME_QSS = """
        /* Estilo general para el tema oscuro */
        * {
            font-family: "Arial Narrow", "Helvetica Condensed", Arial, sans-serif;
            font-weight: bold;
            color: #f0f0f0; /* Texto claro */
        }
        QMainWindow { background-color: #1a1a1a; } /* Fondo oscuro principal */
        QWidget { background-color: #2b2b2b; } /* Fondo oscuro de widgets */
        QLabel { font-size: 18px; color: #f0f0f0; } /* Texto claro */
        
        QLineEdit, ClickableLineEdit {
            font-family: Consolas, "Courier New", monospace;
            font-size: 20px;
            color: #f0f0f0;
            border: 2px solid #555555;
            border-radius: 6px;
            padding: 4px;
            min-width: 80px;
            background: #3a3a3a; /* Fondo oscuro de campos de texto */
        }
        QLineEdit:!read-only, ClickableLineEdit:!read-only {
            background: #3a3a3a;
        }
        QLineEdit:read-only, ClickableLineEdit:readOnly="true" {
            background: #3a3a3a;
            color: #f0f0f0;
            border: 2px solid #555555;
        }
        QLineEdit:focus, ClickableLineEdit:focus {
            border: 2px solid #4a90d9; /* Borde azul para focus */
        }
        QPushButton {
            background: #4a4a4a; /* Fondo oscuro de botones */
            color: #f0f0f0;
            border-radius: 8px;
            font-size: 16px;
            padding: 6px;
            font-weight: bold;
            border: 1px solid #666666;
        }
        QPushButton:hover { background: #5a5a5a; }
        QPushButton:pressed { background: #3a3a3a; }

        /* Estilo para QMessageBox en tema oscuro (tu estilo original) */
        QMessageBox {
            background-color: #2b2b2b; /* Fondo de la ventana oscuro */
            color: #ffffff;            /* Texto del QMessageBox (principal) */
        }
        QMessageBox QLabel {
            color: #ffffff;            /* Asegura que el texto del mensaje sea blanco */
            background-color: #2b2b2b; /* Fondo del QLabel explícitamente oscuro */
            padding: 5px;
        }
        QMessageBox QPushButton {
            background-color: #4CAF50; /* Color de fondo del botón (Verde ejemplo) */
            color: #ffffff;
            border-radius: 5px;
            padding: 5px 15px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #45a049;
        }
        QMessageBox QPushButton:pressed {
            background-color: #3e8e41;
        }
        
        /* Ajustes específicos para elementos del header para el tema oscuro */
        #header_container { background: #1a1a1a; } /* Asegúrate de que tu header_container tenga un objectName="header_container" */
        QLabel#status_label { background: #333333; color: #f0f0f0; border: 1px solid #555555; }
        QLabel#active_alarms_label { background: #333333; color: #f0f0f0; border: 1px solid #555555; }
        QLabel#current_screen_label { color: #f0f0f0; }
        QLabel#current_process_status { color: #f0f0f0; }
        QLabel#date_time_label { color: #f0f0f0; }

        /* También puedes ajustar el estilo de los botones de navegación para el tema oscuro */
        QPushButton { /* Estilos generales de QPushButton ya definidos arriba */ }
        /* Si tus botones de navegación tienen un objectName o clase CSS específica */
        #nav_button_Inicio { background: #333333; color: #f0f0f0; }
        #nav_button_Diálisis { background: #333333; color: #f0f0f0; }
        /* etc. */
        /* Alternativamente, si tienen los estilos BTN_..._STYLE, estos se pueden ajustar directamente */
    """

    # Diccionario de temas disponibles
    THEMES = {
        "Light": LIGHT_THEME_QSS,
        "Dark": DARK_THEME_QSS,
        # Puedes añadir más temas aquí
    }

    DEFAULT_THEME = "Light"
    SETTINGS_KEY = "AppTheme/CurrentTheme"

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._current_theme_name = self.DEFAULT_THEME
        self._settings = QSettings("CIATEQ", "HemodialysisHMI") # Cambia a tu nombre de organización/aplicación

        self._load_saved_theme()

    def _load_saved_theme(self):
        saved_theme = self._settings.value(self.SETTINGS_KEY, self.DEFAULT_THEME)
        if saved_theme in self.THEMES:
            self._current_theme_name = saved_theme
        else:
            logger.warning(f"Tema guardado '{saved_theme}' no encontrado. Usando tema por defecto '{self.DEFAULT_THEME}'.")
            self._current_theme_name = self.DEFAULT_THEME
        self.apply_theme(self._current_theme_name)

    def apply_theme(self, theme_name: str):
        if theme_name not in self.THEMES:
            logger.error(f"Tema '{theme_name}' no existe.")
            return

        qss = self.THEMES[theme_name]
        self.app.setStyleSheet(qss)
        self._current_theme_name = theme_name
        self._settings.setValue(self.SETTINGS_KEY, theme_name)
        logger.info(f"Tema aplicado: {theme_name}")
        self.theme_changed.emit(theme_name) # Emitir señal de cambio de tema

    def get_available_themes(self) -> list[str]:
        return list(self.THEMES.keys())

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name
