# gui/configuration/alarm_screen_config.py
# pantalla de configuracion de alarmas para usuario
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, 
    QPushButton, QHBoxLayout, QComboBox, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from gui.components.ui_components import ClickableLineEdit
from gui.components.numpad_modal import NumpadDialog
from gui.components.floating_message import FloatingMessage
from gui.components.floating_confirm import FloatingConfirmDialog
from core.alarm_config_manager import AlarmConfigManager
from typing import Dict
import logging
logger = logging.getLogger(__name__)


try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class AlarmScreenConfig(QWidget):
    """
    Pantalla de configuración de alarmas para el Operador.
    Muestra tanto variables numéricas (con límites) como booleanas (solo severidad).
    """

    def __init__(self, config_manager: AlarmConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.inputs: Dict[str, dict] = {}   # tag -> {'min': widget, 'max': widget, 'level': widget, 'type': str}


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

        title = QLabel("Configuración de Alarmas")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #34495e;")
        main_layout.addWidget(title)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: #f8fafc; }
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
   
        v_layout = QVBoxLayout(scroll_content)
        v_layout.setContentsMargins(0, 0, 0, 0)

        grid_widget = QWidget() 
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(15)

        v_layout.addWidget(grid_widget)
        v_layout.addStretch() 

        # Encabezados dinámicos
        headers = ["Parámetro", "Límite Inferior", "Límite Superior", "Nivel de Alarma"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; font-size: 24px; color: #7f8c8d;")
            self.grid_layout.addWidget(lbl, 0, col)

        self.populate_variables()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Botones
        btn_layout = QHBoxLayout()
        btn_restore = QPushButton("Restaurar Todo")
        btn_restore.setFixedSize(180, 55)
        btn_restore.setStyleSheet("background: #0f172a; color: #ffffff; font-size: 16px; font-weight: bold; border-radius: 8px;")
        btn_restore.clicked.connect(self.restore_all_defaults)

        btn_save = QPushButton("Guardar Cambios")
        btn_save.setFixedSize(180, 55)
        btn_save.setStyleSheet("background: #0f172a; color: #ffffff; font-size: 16px; font-weight: bold; border-radius: 8px;")
        btn_save.clicked.connect(self.save_configuration)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_restore)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)


    def populate_variables(self):
        row = 1

        enabled_tags = set(self.config_manager.get_enabled_tags())
        label_short = ""
        for group in VARIABLES.values():
            for info in group.values():
                if "tag" not in info:
                    continue
                
                tag = info["tag"]                
                if tag not in enabled_tags:
                    continue

                name = info.get("name", info.get("label", tag))
                label_short = info.get("label",tag)
                unit = info.get("unit", "")
                var_type = info.get("type", "numeric")

                current_level = self.config_manager.get_severity(tag)

                lbl_name = QLabel(f"{name} {f'({unit})' if unit else ''}")
                lbl_name.setStyleSheet("font-size: 23px; font-weight: bold;")

                combo_level = QComboBox()
                combo_level.addItems(["cian", "naranja", "amarillo", "rojo"])
                combo_level.setStyleSheet("font-size: 23px;")
                combo_level.setCurrentText(current_level)
                combo_level.setFixedWidth(130)

                # Guardamos la información del tipo
                widget_dict = {'level': combo_level, 'type': var_type}

                if var_type == "double":
                    # Variables numéricas → mostrar límites
                    min_val, max_val = self.config_manager.get_limits(tag)

                    min_edit = ClickableLineEdit(f"{min_val:.1f}")
                    max_edit = ClickableLineEdit(f"{max_val:.1f}")
                    min_edit.setFixedWidth(100)
                    max_edit.setFixedWidth(100)

                    min_edit.clicked.connect(lambda c=False, e=min_edit, t=label_short, f="min": self.open_numpad(e, t, f))
                    max_edit.clicked.connect(lambda c=False, e=max_edit, t=label_short, f="max": self.open_numpad(e, t, f))

                    self.grid_layout.addWidget(lbl_name, row, 0)
                    self.grid_layout.addWidget(min_edit, row, 1)
                    self.grid_layout.addWidget(max_edit, row, 2)
                    self.grid_layout.addWidget(combo_level, row, 3)

                    widget_dict.update({'min': min_edit, 'max': max_edit})

                else:
                    # Variables booleanas → solo mostrar nombre y nivel de alarma
                    # Dejar columnas de límites vacías
                    self.grid_layout.addWidget(lbl_name, row, 0)
                    self.grid_layout.addWidget(QLabel("—"), row, 1)   # placeholder
                    self.grid_layout.addWidget(QLabel("—"), row, 2)   # placeholder
                    self.grid_layout.addWidget(combo_level, row, 3)

                self.inputs[tag] = widget_dict
                row += 1

    def open_numpad(self, line_edit, tag, field):
        # dialog = NumpadDialog(self, initial_value=line_edit.text(), 
                            #  title=f"Límite {field.upper()} \n {tag}")
        dialog = NumpadDialog(self, initial_value="", 
                             title=f"Límite {field.upper()} \n {tag}")
        
        if dialog.exec():
            val = dialog.get_value()
            line_edit.setText(f"{val:.1f}")
            # line_edit.setText(" ")

    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        """Método genérico (recomendado)"""
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        
        self._floating_msg.show_floating_message(text, timeout_ms)

    # Métodos específicos (más semánticos)
    def show_success_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_success_message(text, timeout_ms)

    def show_info_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_info_message(text, timeout_ms)

    def show_warning_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_warning_message(text, timeout_ms)

    def show_error_message(self, text: str, timeout_ms: int = 3000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_error_message(text, timeout_ms)
        
    def save_configuration(self):
        for tag, widgets in self.inputs.items():
            try:
                level = widgets['level'].currentText()
                self.config_manager.set_severity(tag, level)

                # Solo guardar límites si es variable numérica
                if widgets.get('type') == "double":
                    min_v = float(widgets['min'].text())
                    max_v = float(widgets['max'].text())

                    if min_v >= max_v:
                        
                        self.show_warning_message("Límite inferior debe ser menor que el superior.", timeout_ms=2000)
                        return

                    self.config_manager.set_limits(tag, min_v, max_v)

            except ValueError:
                self.show_error_message(f"Valor inválido en {tag}.", timeout_ms=3000)
                return
        self.config_manager.save_config()
        self.show_success_message("Configuración de alarmas guardada correctamente.", timeout_ms=2000)

    def restore_all_defaults(self):
        dialog = FloatingConfirmDialog(self)
      
        mensaje = "Confirmar Restauración\n\n¿Está seguro de que desea restaurar TODOS los límites y niveles de alarma a sus valores por defecto?\nEsta acción no se puede deshacer."
        
        reply = dialog.show_confirm(mensaje, accept_text="Sí, Restaurar", cancel_text="Cancelar")

        if reply == False:
            return

        for tag, widgets in self.inputs.items():
            # Restaurar severidad
            default_severity = self.config_manager.get_default_severity_from_variables_map(tag)
            widgets['level'].setCurrentText(default_severity)
            self.config_manager.set_severity(tag, default_severity)

            # Restaurar límites si es numérica
            if widgets.get('type') == "double":
                default_min, default_max = self.config_manager.get_default_limits_from_variables_map(tag)
                widgets['min'].setText(f"{default_min:.1f}")
                widgets['max'].setText(f"{default_max:.1f}")
                self.config_manager.set_limits(tag, default_min, default_max)
        
        # Guardar todos los cambios al archivo JSON
        self.config_manager.save_config()
        
        self.show_info_message("Todos los límites y niveles han sido restaurados a sus valores por defecto.", timeout_ms=2000)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    
    def refresh_ui(self):
        # 1. Limpiar el layout actual
        self.clear_layout(self.grid_layout)

        # 2. Re-crear los encabezados (ya que clear_layout borra todo)
        headers = ["Parámetro", "Límite Inferior", "Límite Superior", "Nivel de Alarma"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; font-size: 24px; color: #7f8c8d;")
            self.grid_layout.addWidget(lbl, 0, col) # row 0 para los encabezados

        # 3. Limpiar el diccionario de inputs y volver a poblar
        self.inputs.clear()
        self.populate_variables()

 
    
    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()
