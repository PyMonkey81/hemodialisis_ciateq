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


          
   