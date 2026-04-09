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
from gui.components.ui_components import show_dark_message
from core.alarm_config_manager import AlarmConfigManager
from typing import Dict

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
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(15)

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

        for group in VARIABLES.values():
            for info in group.values():
                if "tag" not in info:
                    continue

                tag = info["tag"]
                if tag not in enabled_tags:
                    continue

                name = info.get("name", info.get("label", tag))
                unit = info.get("unit", "")
                var_type = info.get("type", "numeric")

                current_level = self.config_manager.get_severity(tag)

                lbl_name = QLabel(f"{name} {f'({unit})' if unit else ''}")
                lbl_name.setStyleSheet("font-size: 23px; font-weight: bold;")

                combo_level = QComboBox()
                combo_level.addItems(["cian", "naranja", "amarillo", "rojo"])
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

                    min_edit.clicked.connect(lambda c=False, e=min_edit, t=tag, f="min": self.open_numpad(e, t, f))
                    max_edit.clicked.connect(lambda c=False, e=max_edit, t=tag, f="max": self.open_numpad(e, t, f))

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
        dialog = NumpadDialog(self, initial_value=line_edit.text(), 
                             title=f"Límite {field.upper()} para {tag}")
        if dialog.exec():
            val = dialog.get_value()
            line_edit.setText(f"{val:.1f}")

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
                        show_dark_message(self, "Error", 
                                        f"Límite inferior debe ser menor que el superior para {tag}.", 
                                        icon=QMessageBox.Warning)
                        return

                    self.config_manager.set_limits(tag, min_v, max_v)

            except ValueError:
                show_dark_message(self, "Error", 
                                f"Valor inválido en {tag}.", 
                                icon=QMessageBox.Warning)
                return
        self.config_manager.save_config()
        show_dark_message(self, "Éxito", 
                         "Configuración de alarmas guardada correctamente.", 
                         icon=QMessageBox.Information)

    def restore_all_defaults(self):
        reply = show_dark_message(
            self,
            "Confirmar Restauración",
            "¿Está seguro de que desea restaurar TODOS los límites y niveles de alarma a sus valores por defecto?\n"
            "Esta acción no se puede deshacer.",
            icon=QMessageBox.Question,
            buttons=QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
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
        
        show_dark_message(self, "Restaurado", 
                         "Todos los límites y niveles han sido restaurados a sus valores por defecto.", 
                         icon=QMessageBox.Information)
        
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


# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, 
#     QPushButton, QHBoxLayout, QComboBox, QMessageBox
# )
# from PySide6.QtCore import Qt
# from gui.components.ui_components import ClickableLineEdit
# from gui.components.numpad_modal import NumpadDialog
# from gui.components.ui_components import show_dark_message
# from core.alarm_config_manager import AlarmConfigManager
# from typing import Dict 

# try:
#     from core.variables_map import VARIABLES
# except ImportError:
#     VARIABLES = {0x01: {}, 0x02: {}}

# class AlarmScreenConfig(QWidget):
#     """
#     Pantalla de configuración de límites y severidad de alarmas para el Operador.
    
#     """
#     def __init__(self, config_manager: AlarmConfigManager, parent=None):
#         super().__init__(parent)
#         self.config_manager = config_manager          # ← Cambiado
#         self.inputs: Dict[str, dict] = {}             # Guardará las referencias a los widgets
#         self.setup_ui()

#     def setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(20, 20, 20, 20)
#         main_layout.setSpacing(15)

#         # Título
#         title = QLabel("Configuración de Límites de Alarma")
#         title.setStyleSheet("font-size: 28px; font-weight: bold; color: #34495e;")
#         main_layout.addWidget(title)

#         # Área con scroll para las variables
#         scroll_area = QScrollArea()
#         scroll_area.setWidgetResizable(True)
#         scroll_area.setStyleSheet("""
#             QScrollArea { border: none; background: transparent; }
#             QScrollBar:vertical {
#                 border: none;
#                 background: #e0e0e5;
#                 width: 34px;               /* <--- aquí cambias el ancho */
#                 margin: 0px 0px 0px 0px;
#                 border-radius: 14px;
#             }
#             QScrollBar::handle:vertical {
#                 background: #8a8a9c;
#                 min-height: 60px;
#                 border-radius: 14px;
#             }
#             QScrollBar::handle:vertical:hover {
#                 background: #6b6b7a;
#             }
#             QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
#                 height: 0px;
#             }
#             QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
#                 background: none;
#             }
#         """)
        
#         scroll_content = QWidget()
#         self.grid_layout = QGridLayout(scroll_content)
#         self.grid_layout.setSpacing(15)
        
#         # Encabezados de las columnas
#         headers = ["Parámetro", "Límite Inferior", "Límite Superior", "Nivel de Alarma"]
#         for col, text in enumerate(headers):
#             lbl = QLabel(text)
#             lbl.setStyleSheet("font-weight: bold; font-size: 24px; color: #7f8c8d;")
#             self.grid_layout.addWidget(lbl, 0, col)

#         self.populate_variables()
        
#         scroll_area.setWidget(scroll_content)
#         main_layout.addWidget(scroll_area)

#         # Botones de Acción
#         btn_layout = QHBoxLayout()
        
#         btn_restore = QPushButton("Restaurar Todo")
#         btn_restore.setFixedSize(160, 50)
#         btn_restore.setStyleSheet("background: #0f172a; color: #ffffff; font-size: 16px; font-weight: bold; border-radius: 8px;")
#         btn_restore.clicked.connect(self.restore_all_defaults)
        
#         btn_save = QPushButton("Guardar Cambios")
#         btn_save.setFixedSize(160, 50)
#         btn_save.setStyleSheet("background: #0f172a; color: #ffffff; font-size: 16px; font-weight: bold; border-radius: 8px;")
#         btn_save.clicked.connect(self.save_configuration)

#         btn_layout.addStretch()
#         btn_layout.addWidget(btn_restore)
#         btn_layout.addWidget(btn_save)
        
#         main_layout.addLayout(btn_layout)

#     def populate_variables(self):
#         row = 1
#         enabled_tags = set(self.config_manager.get_enabled_tags())   # ← solo las habilitadas

#         for group in VARIABLES.values():
#             for info in group.values():
#                 # En tu diseño real, aquí filtrarías por las que el Técnico habilitó desde un JSON de estado.
#                 # Por ahora, mostraremos las que tienen tipo 'double' (numéricas)
#                 if info.get("type") == "double" and "tag" in info:
#                     tag = info["tag"]
#                     if tag not in enabled_tags:
#                         continue
#                     name = info.get("name", "Desconocido")
#                     unit = info.get("unit", "")
                    
#                     min_val, max_val = self.config_manager.get_limits(tag)
#                     current_level = self.config_manager.get_severity(tag)

#                     # Nombre
#                     lbl_name = QLabel(f"{name} {f'({unit})' if unit else ''}")
#                     lbl_name.setStyleSheet("font-size: 24px; font-weight: bold;")
                    
#                     # Editores Numéricos
#                     min_edit = ClickableLineEdit(f"{min_val:.1f}")
#                     min_edit.setFixedWidth(100)
#                     min_edit.clicked.connect(lambda checked=False, e=min_edit, t=tag, f="min": self.open_numpad(e, t, f))
                    
#                     max_edit = ClickableLineEdit(f"{max_val:.1f}")
#                     max_edit.setFixedWidth(100)
#                     max_edit.clicked.connect(lambda checked=False, e=max_edit, t=tag, f="max": self.open_numpad(e, t, f))

#                     # Combo de Severidad
#                     combo_level = QComboBox()
#                     combo_level.addItems(["cian","naranja", "amarillo","rojo"])
#                     combo_level.setCurrentText(current_level)
#                     combo_level.setFixedWidth(120)

#                     # Agregar al Grid
#                     self.grid_layout.addWidget(lbl_name, row, 0)
#                     self.grid_layout.addWidget(min_edit, row, 1)
#                     self.grid_layout.addWidget(max_edit, row, 2)
#                     self.grid_layout.addWidget(combo_level, row, 3)

#                     self.inputs[tag] = {'min': min_edit, 'max': max_edit, 'level': combo_level}
#                     row += 1

#     def open_numpad(self, line_edit, tag, field):
#         dialog = NumpadDialog(self, initial_value=line_edit.text(), title=f"Límite {field.upper()} para {tag}")
#         if dialog.exec():
#             val = dialog.get_value()
#             line_edit.setText(f"{val:.1f}")

#     def restore_all_defaults(self):
#         if self.limits_manager:
#             for tag, widgets in self.inputs.items():
#                 if tag in self.limits_manager.defaults:
#                     def_min, def_max = self.limits_manager.defaults[tag]
#                     widgets['min'].setText(f"{def_min:.1f}")
#                     widgets['max'].setText(f"{def_max:.1f}")

#     def save_configuration(self):
#         if not self.config_manager:
#             return

#         for tag, widgets in self.inputs.items():
#             try:
#                 min_v = float(widgets['min'].text())
#                 max_v = float(widgets['max'].text())

#                 if min_v >= max_v:
#                     show_dark_message(self, "Error", f"Límite inferior debe ser menor que el superior para {tag}.", 
#                                     icon=QMessageBox.Warning)
#                     return

#                 self.config_manager.set_limits(tag, min_v, max_v)
#                 level = widgets['level'].currentText()
#                 self.config_manager.set_severity(tag, level)

#             except ValueError:
#                 show_dark_message(self, "Error", f"Valor inválido en {tag}.", icon=QMessageBox.Warning)
#                 return

#         show_dark_message(self, "Información", "Configuración de límites y severidad guardada exitosamente.", 
#                          icon=QMessageBox.Information)
