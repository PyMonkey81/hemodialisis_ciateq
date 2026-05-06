# gui/configuration/alarm_screen_service_config.py
# pantalla de para configuracion de alarmas para servicio tecnico 
# gui/configuration/alarm_screen_service_config.py
from PySide6.QtWidgets import (
    QSizePolicy, QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, 
    QPushButton, QHBoxLayout, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from gui.components.floating_message import FloatingMessage

from core.alarm_config_manager import AlarmConfigManager
from typing import Dict
import logging
logger = logging.getLogger(__name__)

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class AlarmScreenServiceConfig(QWidget):
    """Pantalla para Servicio Técnico: Habilitar/Deshabilitar variables como alarmas"""

    def __init__(self, config_manager: AlarmConfigManager, parent=None):
        super().__init__(parent)
        self.parent_window = parent # parent_window es HemodialysisHMI
        self.config_manager = config_manager
        self.checkboxes: Dict[str, QCheckBox] = {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#f8f8f8"))
        self.setPalette(palette)


        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Título
        title = QLabel("Configuración de Alarmas - Servicio Técnico")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #34495e;")
        main_layout.addWidget(title)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                border: none;
                background: #e0e0e5;
                width: 34px;
                margin: 0px 0px 0px 0px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical {
                background: #8a8a9c;
                min-height: 60px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b6b7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setSpacing(18)
        grid.setColumnStretch(1, 1)   # Hace que la columna de nombre ocupe el espacio restante

        # Encabezados
        headers = ["Habilitar", "Variable"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; font-size: 24px; color: #7f8c8d; padding-bottom: 8px;")
            grid.addWidget(lbl, 0, col)

        row = 1
        for group in VARIABLES.values():
            for info in group.values():
                if info.get("tag") and info.get("type") in ("double", "bool"):
                    tag = info["tag"]
                    name = info.get("name", info.get("name", tag))
                    unit = info.get("unit", "")

                    # Checkbox más grande y visible
                    chk = QCheckBox()
                    chk.setChecked(self.config_manager.is_enabled(tag))
                    chk.setMinimumHeight(32)
                    chk.setStyleSheet("""
                        QCheckBox { color: #000000; font-size: 26px;  border: 2px solid #000000; border-radius: 6px; padding: 4px; }
                        QCheckBox::indicator { width: 35px; height: 35px; }
                    """)
                    self.checkboxes[tag] = chk

                    # Nombre de la variable
                    display_text = f"{name}"
                    if unit:
                        display_text += f" ({unit})"
                    # Indicador visual si es booleana
                    if info.get("type") == "boolean":
                        display_text += "  [Booleana]"

                    lbl_name = QLabel(display_text)
                    lbl_name.setStyleSheet("font-size: 22px; padding: 4px 0;")

                    # Agregar al grid
                    grid.addWidget(chk, row, 0, alignment=Qt.AlignCenter)
                    grid.addWidget(lbl_name, row, 1, alignment=Qt.AlignLeft)
                    row += 1

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Botones
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar Configuración de Alarmas")
        btn_save.setFixedSize(380, 60)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #0f172a; 
                color: #ffffff; 
                font-size: 18px; 
                font-weight: bold; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background: #1e2937;
            }
        """)
        btn_save.clicked.connect(self.save_enabled)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)


    def save_enabled(self):
        enabled_count = 0
        for tag, chk in self.checkboxes.items():
            self.config_manager.set_enabled(tag, chk.isChecked())
            if chk.isChecked():
                enabled_count += 1
    
        self.config_manager.save_config()
        logger.info(f"Configuración de alarmas guardada. {enabled_count} variables habilitadas como alarmas.")


        self.show_success_message(f"Configuración guardada. {enabled_count} alarmas habilitadas.", 3500)
        # 1. Recargar automáticamente la pantalla del Operador
        if self.parent_window is not None and hasattr(self.parent_window, 'alarm_config_limits_screen'):
            # Llamar al método refresh_ui en la instancia de la pantalla del operador
            self.parent_window.alarm_config_limits_screen.refresh_ui()

        # 2. Informar al AlarmSystem en HemodialysisHMI para que recargue su configuración de monitoreo
        if self.parent_window is not None and hasattr(self.parent_window, 'update_alarm_system_monitor_config'):
            self.parent_window.update_alarm_system_monitor_config()

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

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()