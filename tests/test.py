from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QFormLayout,
    QMessageBox, QDialogButtonBox, QPushButton
)
from PySide6.QtCore import Qt
from gui.components.ui_components import ClickableLineEdit
from gui.components.numpad_modal import NumpadDialog


class AlarmLimitsConfigDialog(QDialog):
    def __init__(self, parent=None, current_values=None, limits_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Límites de Alarma")
        self.setMinimumSize(680, 720)

        self.current_values = current_values or {}
        if limits_manager is None:
            raise ValueError("limits_manager requerido")
        self.limits_manager = limits_manager

        self.inputs = {}
        self.variables = [
            {"tag": "dialyCondVariableData", "name": "Conductividad", "unit": "mS/cm", "decimals": 2, "hint": "13.0 – 15.0"},
            {"tag": "dialyTempVariableData",  "name": "Temperatura",  "unit": "°C",    "decimals": 1, "hint": "35.5 – 38.0"},
            {"tag": "bloodFlowVariableData",  "name": "Flujo sangre", "unit": "ml/min","decimals": 0, "hint": "200 – 450"},
            {"tag": "arterPresProcessData",   "name": "P. arterial",  "unit": "mmHg",  "decimals": 0, "hint": "-100 a +300"},
            {"tag": "venouPresProcessData",   "name": "P. venosa",    "unit": "mmHg",  "decimals": 0, "hint": "0 – 350"},
        ]

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Título + descripción
        layout.addWidget(QLabel("Límites de alarma - Seguridad del paciente", alignment=Qt.AlignCenter).setStyleSheet("font-size:22px; font-weight:bold; color:#c0392b;"))
        layout.addWidget(QLabel("Toque campos para editar • Use 'Restaurar' para defecto", alignment=Qt.AlignCenter).setStyleSheet("font-size:14px; color:#555;"))

        group = QGroupBox("Parámetros")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(14)

        for v in self.variables:
            tag, name, unit, dec, hint = v["tag"], v["name"], v["unit"], v["decimals"], v["hint"]
            curr = self.current_values.get(tag)
            curr_str = f"{curr:.{dec}f}" if curr is not None else "—"
            min_v, max_v = self.limits_manager.get_limits(tag)

            row = QHBoxLayout().setSpacing(12)
            row.addWidget(QLabel(f"Actual: {curr_str}", style="color:#444; min-width:130px; font-size:14px;"))
            
            min_edit = ClickableLineEdit(f"{min_v:.{dec}f}")
            min_edit.setAlignment(Qt.AlignCenter)
            min_edit.setFixedWidth(120)
            min_edit.setStyleSheet("background:#f8fafc; border:2px solid #cbd5e1; border-radius:8px; font-size:18px; padding:8px;")
            min_edit.clicked.connect(lambda _, e=min_edit, d=dec, t=tag, f="min": self.open_numpad(e, d, t, f))

            max_edit = ClickableLineEdit(f"{max_v:.{dec}f}")
            max_edit.setAlignment(Qt.AlignCenter)
            max_edit.setFixedWidth(120)
            max_edit.setStyleSheet("background:#f8fafc; border:2px solid #cbd5e1; border-radius:8px; font-size:18px; padding:8px;")
            max_edit.clicked.connect(lambda _, e=max_edit, d=dec, t=tag, f="max": self.open_numpad(e, d, t, f))

            restore_btn = QPushButton("Restaurar")
            restore_btn.setFixedSize(100, 45)
            restore_btn.setStyleSheet("background:#f59e0b; color:white; font-size:14px; border-radius:8px;")
            restore_btn.clicked.connect(lambda _, t=tag, m=min_edit, M=max_edit, d=dec: self.restore_defaults(t, m, M, d))

            row.addWidget(min_edit)
            row.addWidget(QLabel("–", style="color:#64748b; font-size:16px;"))
            row.addWidget(max_edit)
            row.addWidget(restore_btn)
            row.addStretch()

            lbl = QLabel(f"{name} ({unit})", style="font-weight:bold; font-size:16px; min-width:280px;")
            form.addRow(lbl, row)
            form.addRow("", QLabel(hint, style="color:#64748b; font-size:13px;"))

            self.inputs[tag] = (min_edit, max_edit)

        layout.addWidget(group)
        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.validate_and_save)
        btn_box.rejected.connect(self.reject)

        save_btn = btn_box.button(QDialogButtonBox.Save)
        save_btn.setText("Guardar")
        save_btn.setStyleSheet("background:#22c55e; color:white; font-size:18px; padding:12px; min-width:180px; border-radius:8px;")

        cancel_btn = btn_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setStyleSheet("background:#ef4444; color:white; font-size:18px; padding:12px; min-width:140px; border-radius:8px;")

        layout.addWidget(btn_box, alignment=Qt.AlignRight)

    def open_numpad(self, edit: ClickableLineEdit, decimals: int, tag: str, field: str):
        dlg = NumpadDialog(self, edit.text(), f"Límite {field.upper()} - {tag}")
        if dlg.exec() == QDialog.Accepted:
            val = dlg.get_value()
            edit.setText(f"{val:.{decimals}f}" if isinstance(val, float) else str(val))

    def restore_defaults(self, tag: str, min_edit: ClickableLineEdit, max_edit: ClickableLineEdit, decimals: int):
        if hasattr(self.limits_manager, 'defaults') and tag in self.limits_manager.defaults:
            dmin, dmax = self.limits_manager.defaults[tag]
            min_edit.setText(f"{dmin:.{decimals}f}")
            max_edit.setText(f"{dmax:.{decimals}f}")
        else:
            QMessageBox.warning(self, "Sin defecto", f"No hay valor por defecto para {tag}")

    def validate_and_save(self):
        errors = []
        for v in self.variables:
            tag = v["tag"]
            min_e, max_e = self.inputs[tag]
            try:
                mn, mx = float(min_e.text()), float(max_e.text())
                if mn >= mx: errors.append(f"{v['name']}: min ≥ max")
                if mn < -1000 or mx > 1000: errors.append(f"{v['name']}: fuera de ±1000")
            except ValueError:
                errors.append(f"{v['name']}: valor inválido")

        if errors:
            QMessageBox.warning(self, "Errores", "\n".join(errors))
            return

        for v in self.variables:
            tag = v["tag"]
            min_v = float(self.inputs[tag][0].text())
            max_v = float(self.inputs[tag][1].text())
            self.limits_manager.set_limits(tag, min_v, max_v)

        QMessageBox.information(self, "Guardado", "Límites actualizados")
        self.accept()


          
import serial.tools.list_ports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox, QMessageBox
from PySide6.QtCore import Signal
import json
import os
import logging
from gui.components.ui_components import show_dark_message

logger = logging.getLogger(__name__)

CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "sensor_comm_config.json")

class CommPortScreen(QWidget):
    config_changed = Signal(str, str, bool)  # id_sensor, puerto, habilitado

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded_settings = self._load_settings()
        self.all_ports = self.get_filtered_ports()  # Lista base de puertos filtrados
        self.setup_ui()
        self._apply_loaded_settings_to_ui()
        
        # Conectar señales para actualización dinámica de puertos
        self.cmb_cond_port.currentIndexChanged.connect(lambda: self.update_other_port('cond'))
        self.cmb_bioz_port.currentIndexChanged.connect(lambda: self.update_other_port('bioz'))

    def get_filtered_ports(self):
        all_comports = serial.tools.list_ports.comports()
        filtered_ports = ["Auto"]  # Siempre incluye "Auto"
        for p in all_comports:
            if p.manufacturer and "FTDI" not in p.manufacturer.upper():
                filtered_ports.append(p.device)
            elif not p.manufacturer:
                filtered_ports.append(p.device)
        return filtered_ports

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Configuración de Puertos de Comunicación (Sensores Externos)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # Sensor de Conductividad Patrón
        self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
        self.grp_cond.setStyleSheet("font-size: 30px; color: #000000;")
        lyt_cond = QHBoxLayout(self.grp_cond)
        
        self.chk_cond = QCheckBox("Habilitar Comunicación")
        self.chk_cond.setStyleSheet("""
            QCheckBox { color: #000000; font-size: 26px; spacing: 15px; }
            QCheckBox::indicator { width: 35px; height: 35px; }
        """)
        self.cmb_cond_port = QComboBox()
        self.cmb_cond_port.setStyleSheet("color: #000000; font-size: 26px;")
        self.cmb_cond_port.addItems(self.all_ports)  # Usar la lista base
        
        label_cond_port = QLabel("Puerto:")
        label_cond_port.setStyleSheet("color: #000000; font-size: 26px;")
        lyt_cond.addWidget(self.chk_cond)
        lyt_cond.addWidget(label_cond_port)
        lyt_cond.addWidget(self.cmb_cond_port)
        layout.addWidget(self.grp_cond)

        # Sensor Bioimpedancia/Urea
        self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
        self.grp_bioz.setStyleSheet("font-size: 30px; color: #000000;")
        lyt_bioz = QHBoxLayout(self.grp_bioz)
        
        self.chk_bioz = QCheckBox("Habilitar Comunicación")
        self.chk_bioz.setStyleSheet("""
            QCheckBox { color: #000000; font-size: 26px; spacing: 15px; }
            QCheckBox::indicator { width: 35px; height: 35px; }
        """)
        self.cmb_bioz_port = QComboBox()
        self.cmb_bioz_port.setStyleSheet("color: #000000; font-size: 26px;")
        self.cmb_bioz_port.addItems(self.all_ports)  # Usar la lista base

        label_bioz_port = QLabel("Puerto:")
        label_bioz_port.setStyleSheet("color: #000000; font-size: 26px;")
        lyt_bioz.addWidget(self.chk_bioz)
        lyt_bioz.addWidget(label_bioz_port)
        lyt_bioz.addWidget(self.cmb_bioz_port)
        layout.addWidget(self.grp_bioz)

        self.btn_apply = QPushButton("Aplicar\n Cambios")
        self.btn_apply.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: #ffffff; font-size: 26px; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #60a5fa; }
            QPushButton:pressed { background-color: #1e40af; border: 2px solid #0056b3; padding: 8px 10px 10px 12px; }
        """)
        self.btn_apply.setFixedSize(200, 100)
        self.btn_apply.clicked.connect(self.apply_configurations)
        layout.addWidget(self.btn_apply)
        
        layout.addStretch()

    def update_other_port(self, changed_sensor):
        if changed_sensor == 'cond':
            selected_port = self.cmb_cond_port.currentText()
            if selected_port != "Auto":
                # Remover el puerto del combo box de BioZ, si está presente
                index_to_remove = self.cmb_bioz_port.findText(selected_port)
                if index_to_remove >= 0:
                    self.cmb_bioz_port.removeItem(index_to_remove)
                # Opcional: Restaurar puertos si se selecciona "Auto"
                elif self.cmb_cond_port.currentText() == "Auto":
                    self.cmb_bioz_port.addItems([port for port in self.all_ports if port not in [self.cmb_cond_port.currentText()]])
        elif changed_sensor == 'bioz':
            selected_port = self.cmb_bioz_port.currentText()
            if selected_port != "Auto":
                index_to_remove = self.cmb_cond_port.findText(selected_port)
                if index_to_remove >= 0:
                    self.cmb_cond_port.removeItem(index_to_remove)
                # Opcional: Restaurar puertos si se selecciona "Auto"
                elif self.cmb_bioz_port.currentText() == "Auto":
                    self.cmb_cond_port.addItems([port for port in self.all_ports if port not in [self.cmb_bioz_port.currentText()]])
    
    def _load_settings(self):
        # ... (código original sin cambios)
        pass

    def _save_settings(self, settings):
        # ... (código original sin cambios)
        pass


    def _apply_loaded_settings_to_ui(self):
        # ... (código original, pero con verificación para evitar errores)
        cond_settings = self._loaded_settings.get("conductivity_sensor", {})
        port_to_set_cond = cond_settings.get("port", "Auto")
        if port_to_set_cond in self.all_ports:
            self.cmb_cond_port.setCurrentText(port_to_set_cond)
        else:
            self.cmb_cond_port.setCurrentText("Auto")
        self.chk_cond.setChecked(cond_settings.get("enabled", False))

        bioz_settings = self._loaded_settings.get("bioz_urea_sensor", {})
        port_to_set_bioz = bioz_settings.get("port", "Auto")
        if port_to_set_bioz in self.all_ports:
            self.cmb_bioz_port.setCurrentText(port_to_set_bioz)
        else:
            self.cmb_bioz_port.setCurrentText("Auto")
        self.chk_bioz.setChecked(bioz_settings.get("enabled", False))


def refresh_alarms_label(self):
    if not self.active_alarms:  # Verifica si no hay alarmas activas
        self.active_alarms_label.setText("SIN ALARMAS")  # Texto predeterminado cuando no hay alarmas
        self.active_alarms_label.setStyleSheet("""
            QLabel {    
                color: #ffffff; 
                background: #10b981;   /* Verde cuando todo está bien */
                font-weight: bold; 
                font-size: 22px; 
                border-radius: 8px;
            }
            """)
        return  # Sale del método si no hay alarmas, lo cual es eficiente
    
    # Orden de prioridad (rojo > naranja > amarillo > cian)
    priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}  # Mapa de prioridades: bien definido y fácil de entender
    
    # Obtener la alarma de mayor prioridad
    top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))  # Usa max() con una lambda para seleccionar la alarma más grave
    # Aquí, x[2] asume que cada elemento en self.active_alarms es una tupla como (nombre, valor, nivel). Esto es correcto si se mantiene consistente.
    name, value, level = top_alarm  # Desempaquetado de la alarma seleccionada
    
    display_text = name.upper()  # Convierte el nombre a mayúsculas para resaltar
    if value is not None and isinstance(value, (int, float)):  # Verifica si value es un número antes de formatearlo
        display_text += f" {value:.1f}"  # Agrega el valor con un decimal, lo cual es una buena práctica para valores numéricos
    
    color_map = {  # Mapa de colores: bien organizado y reutilizable
        "rojo": "#dc2626",
        "naranja": "#f97316",
        "amarillo": "#eab308",
        "cian": "#06b6d4"
    }
    
    bg_color = color_map.get(level, "#1e293b")  # Obtiene el color basado en el nivel, con un fallback a "#1e293b" si no coincide
    
    self.active_alarms_label.setText(display_text)  # Actualiza el texto de la etiqueta
    self.active_alarms_label.setStyleSheet(f"""  # Usa f-string para inyectar el color dinámicamente, lo cual es moderno y flexible
        QLabel {{ 
            background: {bg_color}; 
            color: #ffffff;
            font-weight: bold; 
            font-size: 22px; 
            border-radius: 8px;
        }}
        """)



# gui/service/comm_port_screen.py

import serial.tools.list_ports
import json
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal

from gui.components.ui_components import show_dark_message

logger = logging.getLogger(__name__)

CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "sensor_comm_config.json")


class CommPortScreen(QWidget):
    config_changed = Signal(str, str, bool)   # sensor_id, port, enabled

    def __init__(self, parent=None):
        super().__init__(parent)

        self.all_ports = self._get_filtered_ports()
        self._loaded_settings = self._load_settings()

        self.setup_ui()
        self._apply_loaded_settings_to_ui()

        # Conexiones
        self.cmb_cond_port.currentIndexChanged.connect(lambda: self._on_port_changed('cond'))
        self.cmb_bioz_port.currentIndexChanged.connect(lambda: self._on_port_changed('bioz'))

    # ====================== PORTS ======================
    def _get_filtered_ports(self):
        """Obtiene lista de puertos filtrados + opción 'Auto'"""
        ports = ["Auto"]
        for port in serial.tools.list_ports.comports():
            # Excluir puertos FTDI (usados probablemente por el controlador principal)
            if port.manufacturer and "FTDI" in port.manufacturer.upper():
                logger.debug(f"Puerto FTDI excluido: {port.device}")
                continue
            ports.append(port.device)
        return ports

    def refresh_ports(self):
        """Llamar si quieres refrescar los puertos disponibles en runtime"""
        current_cond = self.cmb_cond_port.currentText()
        current_bioz = self.cmb_bioz_port.currentText()

        self.all_ports = self._get_filtered_ports()

        self.cmb_cond_port.clear()
        self.cmb_bioz_port.clear()

        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)

        # Intentar restaurar selección anterior
        if current_cond in self.all_ports:
            self.cmb_cond_port.setCurrentText(current_cond)
        if current_bioz in self.all_ports:
            self.cmb_bioz_port.setCurrentText(current_bioz)

        self._update_port_exclusion()

    # ====================== UI ======================
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title = QLabel("Configuración de Puertos de Comunicación")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e3a8a;")
        layout.addWidget(title)

        # === Conductividad ===
        self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
        self.grp_cond.setStyleSheet("font-size: 26px; font-weight: 600;")

        lyt_cond = QHBoxLayout()
        lyt_cond.setSpacing(15)

        self.chk_cond = QCheckBox("Habilitar Comunicación")
        self.chk_cond.setStyleSheet("font-size: 26px; spacing: 12px;")

        lbl_port_cond = QLabel("Puerto:")
        lbl_port_cond.setStyleSheet("font-size: 26px;")

        self.cmb_cond_port = QComboBox()
        self.cmb_cond_port.setStyleSheet("font-size: 26px; min-width: 180px;")

        lyt_cond.addWidget(self.chk_cond)
        lyt_cond.addWidget(lbl_port_cond)
        lyt_cond.addWidget(self.cmb_cond_port)
        lyt_cond.addStretch()
        self.grp_cond.setLayout(lyt_cond)
        layout.addWidget(self.grp_cond)

        # === Bioimpedancia / Urea ===
        self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
        self.grp_bioz.setStyleSheet("font-size: 26px; font-weight: 600;")

        lyt_bioz = QHBoxLayout()
        lyt_bioz.setSpacing(15)

        self.chk_bioz = QCheckBox("Habilitar Comunicación")
        self.chk_bioz.setStyleSheet("font-size: 26px; spacing: 12px;")

        lbl_port_bioz = QLabel("Puerto:")
        lbl_port_bioz.setStyleSheet("font-size: 26px;")

        self.cmb_bioz_port = QComboBox()
        self.cmb_bioz_port.setStyleSheet("font-size: 26px; min-width: 180px;")

        lyt_bioz.addWidget(self.chk_bioz)
        lyt_bioz.addWidget(lbl_port_bioz)
        lyt_bioz.addWidget(self.cmb_bioz_port)
        lyt_bioz.addStretch()
        self.grp_bioz.setLayout(lyt_bioz)
        layout.addWidget(self.grp_bioz)

        # Botón Aplicar
        self.btn_apply = QPushButton("Aplicar Cambios")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-size: 26px;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover { background-color: #60a5fa; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        self.btn_apply.clicked.connect(self.apply_configurations)
        layout.addWidget(self.btn_apply, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Inicializar combos
        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)

    # ====================== LÓGICA DE EXCLUSIÓN MUTUA ======================
    def _on_port_changed(self, changed_sensor: str):
        """Evita que ambos sensores usen el mismo puerto físico"""
        self._update_port_exclusion()

    def _update_port_exclusion(self):
        """Actualiza la disponibilidad de puertos entre ambos combos"""
        cond_port = self.cmb_cond_port.currentText()
        bioz_port = self.cmb_bioz_port.currentText()

        # Restaurar todos los ítems primero
        self._repopulate_combos()

        if cond_port != "Auto":
            self._remove_port_from_combo(self.cmb_bioz_port, cond_port)

        if bioz_port != "Auto":
            self._remove_port_from_combo(self.cmb_cond_port, bioz_port)

    def _repopulate_combos(self):
        """Vuelve a llenar ambos combos con todos los puertos disponibles"""
        current_cond = self.cmb_cond_port.currentText()
        current_bioz = self.cmb_bioz_port.currentText()

        self.cmb_cond_port.clear()
        self.cmb_bioz_port.clear()

        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)

        if current_cond in self.all_ports:
            self.cmb_cond_port.setCurrentText(current_cond)
        if current_bioz in self.all_ports:
            self.cmb_bioz_port.setCurrentText(current_bioz)

    def _remove_port_from_combo(self, combo: QComboBox, port_to_remove: str):
        index = combo.findText(port_to_remove)
        if index >= 0:
            combo.removeItem(index)

    # ====================== CONFIGURACIÓN ======================
    def _load_settings(self):
        default = {
            "conductivity_sensor": {"port": "Auto", "enabled": False},
            "bioz_urea_sensor": {"port": "Auto", "enabled": False},
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Configuración de puertos cargada desde {CONFIG_FILE}")
                return settings
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")

        logger.warning("Usando configuración por defecto de puertos")
        return default

    def _save_settings(self):
        settings = {
            "conductivity_sensor": {
                "port": self.cmb_cond_port.currentText(),
                "enabled": self.chk_cond.isChecked()
            },
            "bioz_urea_sensor": {
                "port": self.cmb_bioz_port.currentText(),
                "enabled": self.chk_bioz.isChecked()
            }
        }

        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuración guardada en {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")

    def _apply_loaded_settings_to_ui(self):
        cond = self._loaded_settings.get("conductivity_sensor", {})
        bioz = self._loaded_settings.get("bioz_urea_sensor", {})

        self.cmb_cond_port.setCurrentText(cond.get("port", "Auto"))
        self.cmb_bioz_port.setCurrentText(bioz.get("port", "Auto"))

        self.chk_cond.setChecked(cond.get("enabled", False))
        self.chk_bioz.setChecked(bioz.get("enabled", False))

        # Aplicar exclusión después de cargar
        self._update_port_exclusion()

    def apply_configurations(self):
        self._save_settings()
        self.emit_current_configurations()

        show_dark_message(
            self,
            "Éxito",
            "Configuración de puertos guardada y aplicada correctamente.",
            icon=QMessageBox.Information
        )

    def emit_current_configurations(self):
        """Emite la configuración actual hacia la clase principal"""
        self.config_changed.emit(
            "CONDUCTIVITY",
            self.cmb_cond_port.currentText(),
            self.chk_cond.isChecked()
        )
        self.config_changed.emit(
            "BIOZ",
            self.cmb_bioz_port.currentText(),
            self.chk_bioz.isChecked()
        )
