# gui/therapy/treatment_mode_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
import time

from gui.components.ui_components import ClickableLineEdit  # si lo usas en otro lado, sino quítalo
from core.variables_map import VARIABLES

class TreatmentModeScreen(QWidget):
    """
    Pantalla exclusiva para seleccionar el tipo de tratamiento:
    Hemodiálisis, Hemodiafiltración, Ultrafiltración, Limpieza
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.values = parent.current_values if parent else {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # self.setFixedSize(1536, 726)  # mismo tamaño que la otra para consistencia
        self.pending_mode_change_deadline = None
        self.commanded_mode_value = None

        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #1a2a4a, stop:1 #0f172a);
            color: #f8fafc;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Título
        title = QLabel("Tipo de Terapia")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep)

        # Frame de botones
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 30px;")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(20)

        lbl_mode = QLabel("Seleccione Tipo de Tratamiento:")
        lbl_mode.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000;")
        mode_layout.addWidget(lbl_mode)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Botones de modo
        self.btn_hemodialysis    = QPushButton("Hemodiálisis")
        self.btn_hemodiafiltration = QPushButton("Hemodiafiltración")
        self.btn_ultrafiltration = QPushButton("Ultrafiltración")
        self.btn_cleaning       = QPushButton("Limpieza")          # ← nuevo

        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)

        mode_buttons_info = [
            (self.btn_hemodialysis,     "treatmentModeSelection", 0.0),
            (self.btn_hemodiafiltration, "treatmentModeSelection", 1.0),
            (self.btn_ultrafiltration,   "treatmentModeSelection", 2.0),
            (self.btn_cleaning,          "treatmentModeSelection", 3.0),   # ← valor 3 para limpieza
        ]

        self.style_mode_unchecked = """
            QPushButton {
                background: #3b82f6;
                color: white;
                font-size: 26px;
                font-weight: bold;
                border-radius: 12px;
                padding: 20px 30px;
                border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
        """
        self.style_mode_checked = """
            QPushButton {
                background: #22c55e;
                color: white;
                font-size: 26px;
                font-weight: bold;
                border-radius: 12px;
                padding: 20px 30px;
                border: 2px solid #16a34a;
            }
            QPushButton:hover { background: #22c55e; }
        """

        for btn, tag, value in mode_buttons_info:
            btn.setStyleSheet(self.style_mode_unchecked)
            btn.setCheckable(True)
            btn.toggled.connect(lambda checked, b=btn, t=tag, v=value:
                                self._on_mode_toggled(b, t, v, checked))
            buttons_layout.addWidget(btn)
            self.mode_button_group.addButton(btn)

        mode_layout.addLayout(buttons_layout)
        main_layout.addWidget(mode_frame)

        main_layout.addStretch(1)

        # Botón Volver
        btn_back = QPushButton("Volver a Diálisis")
        btn_back.setFixedSize(250, 60)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background: #b91c1c; }
        """)
        btn_back.clicked.connect(self.parent_window.show_dialysis_screen)
        main_layout.addWidget(btn_back, alignment=Qt.AlignRight)

    def _on_mode_toggled(self, button: QPushButton, tag: str, value: float, checked: bool):
        if checked:
            button.setStyleSheet(self.style_mode_checked)
            self._write_setpoint(tag, value)
            self.pending_mode_change_deadline = time.monotonic() + 0.7
            self.commanded_mode_value = value
        else:
            button.setStyleSheet(self.style_mode_unchecked)

    def _write_setpoint(self, tag: str, value: float):
        """Método simplificado para escribir setpoint (cópialo o herédalo si prefieres)"""
        try:
            print(f"[SETPOINT] Escribiendo {tag} = {value}")

            if not self.parent_window or not hasattr(self.parent_window, 'serial_comm'):
                print("[INFO] No hay serial_comm disponible")
                return

            found = False
            for group_key, vars_in_group in VARIABLES.items():
                for var_id, info in vars_in_group.items():
                    if info.get("tag") == tag:
                        if info.get("rw", False):
                            self.parent_window.serial_comm.write_double(group_key, var_id, value)
                            found = True
                        break
                if found:
                    break

            if not found:
                print(f"[ERROR] Tag '{tag}' no encontrado o no escribible")

        except Exception as e:
            print(f"[ERROR] Fallo al escribir setpoint: {e}")

    def update_values(self, new_values: dict):
        """Sincroniza botones con el valor real recibido"""
        self.values = new_values
        current_mode = self.values.get("treatmentModeSelection", -1.0)
        now = time.monotonic()

        if self.pending_mode_change_deadline is not None:
            if current_mode == self.commanded_mode_value:
                self.pending_mode_change_deadline = None
                self.commanded_mode_value = None
                return
            elif now > self.pending_mode_change_deadline:
                print("[WARNING] Timeout en confirmación de modo. Revirtiendo UI.")
                self.pending_mode_change_deadline = None
                self.commanded_mode_value = None
            else:
                return  # aún esperando confirmación

        mode_map = {
            0.0: self.btn_hemodialysis,
            1.0: self.btn_hemodiafiltration,
            2.0: self.btn_ultrafiltration,
            3.0: self.btn_cleaning,
        }

        for mode_value, btn in mode_map.items():
            should_be_checked = (current_mode == mode_value)
            if btn.isChecked() != should_be_checked:
                btn.blockSignals(True)
                btn.setChecked(should_be_checked)
                btn.setStyleSheet(self.style_mode_checked if should_be_checked else self.style_mode_unchecked)
                btn.blockSignals(False)
