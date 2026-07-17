# gui/theme_manager.py
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import QSettings, Signal, QObject
import logging

logger = logging.getLogger(__name__)

# Marca / Modelo,Tipo de letra principal,Características
# Fresenius 5008 / 6008,Segoe UI o Arial,"Negrita, sans-serif"
# Baxter / Gambro,Helvetica Neue o Arial,Muy limpia
# Braun Dialog+ / Adimea,Tahoma / Verdana,Buena legibilidad
# Nikkiso / Bellco,Arial Bold,Estilo industrial
# Estándar recomendado,Segoe UI / Arial / Helvetica,Mejor opción actual

class ThemeManager(QObject):
    theme_changed = Signal(str)  # Señal para notificar cuando el tema ha cambiado
    font_changed = Signal(str)   # Señal para notificar cuando cambia la fuente global

    DEFAULT_FONT_FAMILY = "Arial Narrow"
    DEFAULT_FALLBACK_FONTS = '"Helvetica Condensed", Arial, sans-serif'
    DEFAULT_MONOSPACE_FONTS = 'Consolas, "Courier New", monospace'
    DEFAULT_FONT_SIZE = 12
    DEFAULT_FONT_WEIGHT = QFont.Bold

    SETTINGS_THEME_KEY = "AppTheme/CurrentTheme"
    SETTINGS_FONT_FAMILY_KEY = "AppTheme/FontFamily"
    SETTINGS_FONT_SIZE_KEY = "AppTheme/FontSize"

    # Baseline de estilos por pantalla para migracion gradual.
    # Esta seccion documenta el estado visual actual sin alterar la UI.
    SCREEN_BASELINES = {
        "therapy_config_screen": {
            "meta": {
                "version": "baseline-v1",
                "description": "Registro visual actual de TherapyConfigScreen para homologacion",
            },
            "layout": {
                "main_margins": [40, 30, 40, 30],
                "main_spacing": 20,
                "columns_spacing": 30,
                "col1_spacing": 120,
                "params_grid_spacing": 20,
            },
            "typography": {
                "title": {"size": 42, "weight": "bold"},
                "section_label": {"size": 22, "weight": "bold", "min_height": 50},
                "frame_label": {"size": 18, "weight": "bold"},
                "input": {"size": 24, "family": 'Consolas, "Courier New", monospace'},
                "button": {"size": 20, "weight": "bold"},
            },
            "colors": {
                "title": "#60a5fa",
                "separator": "#fcfcfc",
                "label_text": "#000000",
                "frame_border": "#5c5c5c",
                "frame_label_text": "#2b2b2b",
                "input_bg": "#e2e8f0",
                "input_border": "#64748b",
                "input_focus_border": "#3b82f6",
                "input_focus_bg": "#ffffff",
                "button_enabled_bg": "#39ec21",
                "button_stop_bg": "#DD2911",
                "button_disabled_bg": "#334155",
                "button_disabled_text": "#94a3b8",
                "button_text": "#ffffff",
                "button_border": "#1e293b",
                "button_pressed_bg": "#334155",
            },
            "dimensions": {
                "pump_button": [120, 80],
                "input_field": [120, 50],
            },
            "labels": {
                "title": "Configuracion de Terapia",
                "frames": ["Bomba de Sangre", "Llenado de filtro"],
                "buttons": ["START", "STOP", "START"],
                "parameter_labels": [
                    "Flujo de Sangre (Qb, mL/min):",
                    "Flujo Dializante (Qd, mL/min):",
                    "Flujo UF (L/h):",
                    "Temperatura (C):",
                    "Conductividad (mS/cm):",
                    "T. Terapia (hh:mm)",
                ],
            },
        }
    }

    # Definiciones de estilos QSS para cada tema
    # Puedes externalizar estos a archivos .qss y cargarlos
    LIGHT_THEME_QSS = """
        /* Estilo general para el tema claro */
        * {
            font-family: {font_family};
            font-weight: bold;
            color: #0f172a;
        }
        QMainWindow { background-color: #FCFCFC; }
        QWidget { background-color: #FCFCFC; }
        QLabel { font-size: 18px; color: #0f172a; }
        QLineEdit, ClickableLineEdit {
            font-family: {monospace_family};
            font-size: 20px;
            color: #0f172a;
            border: 2px solid #0f172a;
            border-radius: 6px;
            padding: 4px;
            min-width: 80px;
            background: #FFFFE5;
        }
        QLineEdit:!read-only, ClickableLineEdit:!read-only {
            background: #FFFFE5;
        }
        QLineEdit:read-only, ClickableLineEdit[readOnly="true"] {
            background: #FFFFE5;
            color: #0f172a;
            border: 2px solid #0f172a;
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

        QFrame#dialysisValueFrame {
            background-color: #ffffff;
            border: 2px solid #000000;
            border-radius: 10px;
        }
        QLabel#dialysisValueTag {
            border: none;
            color: #333333;
            font-weight: bold;
            font-size: 20px;
        }
        QLabel#dialysisValueValue {
            border: none;
            color: #0078d7;
            font-weight: bold;
            font-size: 36px;
        }
        QFrame#dialysisButtonsContainer {
            background: #FCFCFC;
            border-radius: 10px;
            border: 4px solid #1e293b;
        }
        QPushButton#dialysisActionButton {
            background-color: #3b82f6;
            font-size: 30px;
            font-weight: bold;
            border-radius: 15px;
            border: 3px solid #1e293b;
            color: #ffffff;
            padding: 6px 12px;
        }
        QPushButton#dialysisActionButton[role="start"] { background-color: #39ec21; color: #ffffff; }
        QPushButton#dialysisActionButton[role="pause"] { background-color: #FFC400; color: #000000; }
        QPushButton#dialysisActionButton[role="stop"] { background-color: #DD2911; color: #ffffff; }
        QPushButton#dialysisActionButton[role="menu"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="apply"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="priming"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="priming_stop"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="ktv"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton:disabled { background-color: #334155; color: #94a3b8; }

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
            font-family: {font_family};
            font-weight: bold;
            color: #f0f0f0; /* Texto claro */
        }
        QMainWindow { background-color: #1a1a1a; } /* Fondo oscuro principal */
        QWidget { background-color: #2b2b2b; } /* Fondo oscuro de widgets */
        QLabel { font-size: 18px; color: #f0f0f0; } /* Texto claro */
        
        QLineEdit, ClickableLineEdit {
            font-family: {monospace_family};
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
        QLineEdit:read-only, ClickableLineEdit[readOnly="true"] {
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
        QPushButton:hover { background-color: #5a5a5a; }
        QPushButton:pressed { background-color: #3a3a3a; }

        QFrame#dialysisValueFrame {
            background-color: #3a3a3a;
            border: 2px solid #666666;
            border-radius: 10px;
        }
        QLabel#dialysisValueTag {
            border: none;
            color: #f0f0f0;
            font-weight: bold;
            font-size: 20px;
        }
        QLabel#dialysisValueValue {
            border: none;
            color: #7fbfff;
            font-weight: bold;
            font-size: 36px;
        }
        QFrame#dialysisButtonsContainer {
            background: #1e293b;
            border-radius: 10px;
            border: 4px solid #94a3b8;
        }
        QPushButton#dialysisActionButton {
            background-color: #4a4a4a;
            font-size: 30px;
            font-weight: bold;
            border-radius: 15px;
            border: 3px solid #1e293b;
            color: #ffffff;
            padding: 6px 12px;
        }
        QPushButton#dialysisActionButton[role="start"] { background-color: #39ec21; color: #ffffff; }
        QPushButton#dialysisActionButton[role="pause"] { background-color: #FFC400; color: #000000; }
        QPushButton#dialysisActionButton[role="stop"] { background-color: #DD2911; color: #ffffff; }
        QPushButton#dialysisActionButton[role="menu"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="apply"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="priming"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="priming_stop"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton[role="ktv"] { background-color: #0f172a; color: #ffffff; }
        QPushButton#dialysisActionButton:disabled { background-color: #334155; color: #94a3b8; }

        /* Estilo para QMessageBox en tema oscuro */
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMessageBox QLabel {
            color: #ffffff;
            background-color: #2b2b2b;
            padding: 5px;
        }
        QMessageBox QPushButton {
            background-color: #4CAF50;
            color: #ffffff;
            border-radius: 5px;
            padding: 5px 15px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover { background-color: #45a049; }
        QMessageBox QPushButton:pressed { background-color: #3e8e41; }
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
        self._current_font_family = self.DEFAULT_FONT_FAMILY
        self._current_font_size = self.DEFAULT_FONT_SIZE
        self._settings = QSettings("CIATEQ", "HemodialysisHMI")

        self._load_saved_settings()

    def _load_saved_settings(self):
        saved_theme = self._settings.value(self.SETTINGS_KEY, self.DEFAULT_THEME)
        saved_font_family = self._settings.value(self.SETTINGS_FONT_FAMILY_KEY, self.DEFAULT_FONT_FAMILY)
        saved_font_size = self._settings.value(self.SETTINGS_FONT_SIZE_KEY, self.DEFAULT_FONT_SIZE)

        if saved_theme in self.THEMES:
            self._current_theme_name = saved_theme
        else:
            logger.warning(f"Tema guardado '{saved_theme}' no encontrado. Usando tema por defecto '{self.DEFAULT_THEME}'.")
            self._current_theme_name = self.DEFAULT_THEME

        self._current_font_family = str(saved_font_family)
        try:
            self._current_font_size = int(saved_font_size)
        except (TypeError, ValueError):
            self._current_font_size = self.DEFAULT_FONT_SIZE
            logger.warning(f"Tamaño de fuente inválido '{saved_font_size}'. Usando {self.DEFAULT_FONT_SIZE}.")

        self.apply_theme(self._current_theme_name)

    def _apply_app_font(self):
        font = QFont(self._current_font_family, self._current_font_size)
        font.setWeight(self.DEFAULT_FONT_WEIGHT)
        self.app.setFont(font)

    def _build_qss(self, theme_name: str) -> str:
        template = self.THEMES.get(theme_name, self.THEMES[self.DEFAULT_THEME])
        return template.replace("{font_family}", self._current_font_family).replace(
            "{monospace_family}", self.DEFAULT_MONOSPACE_FONTS
        )

    def apply_theme(self, theme_name: str):
        if theme_name not in self.THEMES:
            logger.error(f"Tema '{theme_name}' no existe.")
            return

        self._current_theme_name = theme_name
        self._apply_app_font()
        qss = self._build_qss(theme_name)
        self.app.setStyleSheet(qss)
        self._settings.setValue(self.SETTINGS_KEY, theme_name)
        logger.info(f"Tema aplicado: {theme_name}")
        self.theme_changed.emit(theme_name)

    @classmethod
    def get_screen_baseline(cls, screen_key: str) -> dict:
        """Devuelve el baseline visual registrado para una pantalla."""
        return cls.SCREEN_BASELINES.get(screen_key, {})

    @classmethod
    def get_therapy_config_baseline(cls) -> dict:
        """Atajo para baseline de la pantalla de configuracion de terapia."""
        return cls.get_screen_baseline("therapy_config_screen")

    def apply_font(self, font_family: str, font_size: int | None = None):
        self._current_font_family = font_family
        if font_size is not None:
            self._current_font_size = font_size

        self._apply_app_font()
        qss = self._build_qss(self._current_theme_name)
        self.app.setStyleSheet(qss)

        self._settings.setValue(self.SETTINGS_FONT_FAMILY_KEY, self._current_font_family)
        self._settings.setValue(self.SETTINGS_FONT_SIZE_KEY, self._current_font_size)
        logger.info(f"Fuente aplicada: {self._current_font_family} ({self._current_font_size} pt)")
        self.font_changed.emit(self._current_font_family)

    def get_available_themes(self) -> list[str]:
        return list(self.THEMES.keys())

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name

    @property
    def current_font_family(self) -> str:
        return self._current_font_family

    @property
    def current_font_size(self) -> int:
        return self._current_font_size


