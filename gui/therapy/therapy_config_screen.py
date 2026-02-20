# gui/therapy/therapy_config_screen.py
# Therapy configuration screen for setting treatment parameters and mode

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QGridLayout, QFrame, QLineEdit, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import time


from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class TherapyConfigScreen(QWidget):
    """
    Configuration screen for dialysis therapy parameters.
    Allows selection of treatment mode and adjustment of key setpoints.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Reference to main HemodialysisHMI window
        self.values = parent.current_values if parent else {}  # Shared values dict

        self.setFixedSize(1536, 726)
        self.setStyleSheet("background: #0f172a;")

        # Pending mode change tracking (to detect confirmation timeout)
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

        # Title
        title = QLabel("Configuración de Terapia")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep1)

        # ── Treatment Mode Selection ─────────────────────────────────────────────
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(15)

        lbl_mode = QLabel("Seleccione Tipo de Tratamiento:")
        lbl_mode.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000;")
        mode_layout.addWidget(lbl_mode)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Treatment mode buttons
        self.btn_hemodialysis = QPushButton("Hemodiálisis")
        self.btn_hemodiafiltration = QPushButton("Hemodiafiltración")
        self.btn_ultrafiltration = QPushButton("Ultrafiltración")

        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)

        # Updated to use the buttons directly as keys if needed later, or simply for display.
        mode_buttons_info = [
            (self.btn_hemodialysis,     "treatmentModeSelection", 0.0),
            (self.btn_hemodiafiltration, "treatmentModeSelection", 1.0),
            (self.btn_ultrafiltration,   "treatmentModeSelection", 2.0)
        ]

        self.style_mode_unchecked = """
            QPushButton {
                background: #3b82f6;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px 25px;
                border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
            QPushButton:pressed { background: #1e40af; }
        """
        self.style_mode_checked = """
            QPushButton {
                background: #22c55e;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px 25px;
                border: 2px solid #16a34a;
            }
            QPushButton:hover { background: #22c55e; }
            QPushButton:pressed { background: #16a34a; }
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

        # ── Parameter Inputs ─────────────────────────────────────────────────────
        params_frame = QFrame()
        params_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        params_layout = QGridLayout(params_frame)
        params_layout.setSpacing(20)

        label_style = "color: #000000; font-size: 22px; font-weight: bold;"
        input_style = """
            ClickableLineEdit {
                font-family: Consolas, "Courier New", monospace;
                font-size: 24px;
                color: #000000;
                background: #e2e8f0;
                border: 2px solid #64748b;
                border-radius: 8px;
                padding: 5px;
                min-width: 100px;
            }
            ClickableLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
            }
        """

        # Heparin Dose
        lbl_heparin = QLabel("Dosis Heparina (UI):")
        lbl_heparin.setStyleSheet(label_style)
        self.input_heparin = ClickableLineEdit("0.0")
        self.input_heparin.setFixedSize(120, 50)
        self.input_heparin.setAlignment(Qt.AlignCenter)
        self.input_heparin.setStyleSheet(input_style)
        self.input_heparin.setReadOnly(True)
        self.input_heparin.clicked.connect(
            lambda: self.open_numpad("heparineTherapyDosage", self.input_heparin, "Dosis Heparina")
        )
        params_layout.addWidget(lbl_heparin, 0, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_heparin, 0, 1)

        # Blood Flow (Qb)
        lbl_blood_flow = QLabel("Flujo de Sangre (Qb, mL/min):")
        lbl_blood_flow.setStyleSheet(label_style)
        self.input_blood_flow = ClickableLineEdit("0.0")
        self.input_blood_flow.setFixedSize(120, 50)
        self.input_blood_flow.setAlignment(Qt.AlignCenter)
        self.input_blood_flow.setStyleSheet(input_style)
        self.input_blood_flow.setReadOnly(True)
        self.input_blood_flow.clicked.connect(
            lambda: self.open_numpad("bloodFlowControlSetPoint", self.input_blood_flow, "Flujo de Sangre (Qb)")
        )
        params_layout.addWidget(lbl_blood_flow, 1, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_blood_flow, 1, 1)

        # Dialysate Flow (Qd)
        lbl_dialysate_flow = QLabel("Flujo Dializante (Qd, mL/min):")
        lbl_dialysate_flow.setStyleSheet(label_style)
        self.input_dialysate_flow = ClickableLineEdit("0.0")
        self.input_dialysate_flow.setFixedSize(120, 50)
        self.input_dialysate_flow.setAlignment(Qt.AlignCenter)
        self.input_dialysate_flow.setStyleSheet(input_style)
        self.input_dialysate_flow.setReadOnly(True)
        self.input_dialysate_flow.clicked.connect(
            lambda: self.open_numpad("dialyFlowControlSetPoint", self.input_dialysate_flow, "Flujo Dializante (Qd)")
        )
        params_layout.addWidget(lbl_dialysate_flow, 2, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_dialysate_flow, 2, 1)

        # Temperature
        lbl_temperature = QLabel("Temperatura (°C):")
        lbl_temperature.setStyleSheet(label_style)
        self.input_temperature = ClickableLineEdit("0.0")
        self.input_temperature.setFixedSize(120, 50)
        self.input_temperature.setAlignment(Qt.AlignCenter)
        self.input_temperature.setStyleSheet(input_style)
        self.input_temperature.setReadOnly(True)
        self.input_temperature.clicked.connect(
            lambda: self.open_numpad("dialyTempControlSetPoint", self.input_temperature, "Temperatura")
        )
        params_layout.addWidget(lbl_temperature, 0, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_temperature, 0, 3)

        # Conductivity
        lbl_conductivity = QLabel("Conductividad (mS/cm):")
        lbl_conductivity.setStyleSheet(label_style)
        self.input_conductivity = ClickableLineEdit("0.0")
        self.input_conductivity.setFixedSize(120, 50)
        self.input_conductivity.setAlignment(Qt.AlignCenter)
        self.input_conductivity.setStyleSheet(input_style)
        self.input_conductivity.setReadOnly(True)
        self.input_conductivity.clicked.connect(
            lambda: self.open_numpad("dialyCondControlSetPoint", self.input_conductivity, "Conductividad")
        )
        params_layout.addWidget(lbl_conductivity, 1, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_conductivity, 1, 3)

        # Sodium (Na+)
        lbl_sodium = QLabel("Sodio (Na+, mmol/L):")
        lbl_sodium.setStyleSheet(label_style)
        self.input_sodium = ClickableLineEdit("0.0")
        self.input_sodium.setFixedSize(120, 50)
        self.input_sodium.setAlignment(Qt.AlignCenter)
        self.input_sodium.setStyleSheet(input_style)
        self.input_sodium.setReadOnly(True)
        self.input_sodium.clicked.connect(
            lambda: self.open_numpad("sodiumConcentrationSetPoint", self.input_sodium, "Sodio (Na+)")
        )
        params_layout.addWidget(lbl_sodium, 2, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_sodium, 2, 3)

        # Therapy Duration (hh:mm)
        lbl_duration = QLabel("T. Terapia (hh:mm)")
        lbl_duration.setStyleSheet(label_style)
        self.input_duration = ClickableLineEdit("00:00")
        self.input_duration.setFixedSize(120, 50)
        self.input_duration.setAlignment(Qt.AlignCenter)
        self.input_duration.setStyleSheet(input_style)
        self.input_duration.setReadOnly(True)
        self.input_duration.clicked.connect(
            lambda: self.open_time_numpad(
                self.input_duration,
                tag_hours="heparineTherapyHours",      # Ajustar tags reales
                tag_minutes="heparineTherapyMinutes",
                local_timer_id=None,
                title="Tiempo de terapia"
            )
        )
        params_layout.addWidget(lbl_duration, 3, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_duration, 3, 3)

        params_layout.setColumnStretch(0, 1)
        params_layout.setColumnStretch(1, 0)
        params_layout.setColumnStretch(2, 1)
        params_layout.setColumnStretch(3, 0)

        main_layout.addWidget(params_frame)
        main_layout.addStretch(1)

        # Back button
        btn_back = QPushButton("Volver a Diálisis")
        btn_back.setFixedSize(250, 60)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
        """)
        btn_back.clicked.connect(self.parent_window.show_dialysis_screen)
        main_layout.addWidget(btn_back, alignment=Qt.AlignRight)

    def _on_mode_toggled(self, button: QPushButton, tag: str, value: float, checked: bool):
        """Handle treatment mode button toggle and send setpoint."""
        if checked:
            button.setStyleSheet(self.style_mode_checked)
            self._write_setpoint(tag, value) # Pass value directly
            self.pending_mode_change_deadline = time.monotonic() + 0.7
            self.commanded_mode_value = value
        else:
            button.setStyleSheet(self.style_mode_unchecked)

    def update_values(self, new_values: dict):
        """Update displayed setpoints from shared values dictionary."""
        self.values = new_values

        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_blood_flow, "bloodFlowControlSetPoint")
        self._update_input_display(self.input_dialysate_flow, "dialyFlowControlSetPoint")
        self._update_input_display(self.input_temperature, "dialyTempControlSetPoint")
        self._update_input_display(self.input_conductivity, "dialyCondControlSetPoint")
        self._update_input_display(self.input_sodium, "sodiumConcentrationSetPoint")

        self._update_time_display(self.input_duration, "heparineTherapyHours", "heparineTherapyMinutes")

        # Sync mode buttons with current value
        current_mode = self.values.get("treatmentModeSelection", -1.0)
        now = time.monotonic()

        if self.pending_mode_change_deadline is not None:
            if current_mode == self.commanded_mode_value:
                self.pending_mode_change_deadline = None
                self.commanded_mode_value = None
                return
            elif now > self.pending_mode_change_deadline:
                print("[WARNING] Timeout waiting for treatment mode confirmation. Reverting UI.")
                self.pending_mode_change_deadline = None
                self.commanded_mode_value = None
            else:
                return

        mode_map = {
            0.0: self.btn_hemodialysis,
            1.0: self.btn_hemodiafiltration,
            2.0: self.btn_ultrafiltration
        }

        for mode_value, btn in mode_map.items():
            should_be_checked = (current_mode == mode_value)
            if btn.isChecked() != should_be_checked:
                # Block signals to prevent _on_mode_toggled from being called again
                # and potentially re-sending a setpoint if the toggle is just syncing UI
                btn.blockSignals(True) 
                btn.setChecked(should_be_checked)
                btn.setStyleSheet(self.style_mode_checked if should_be_checked else self.style_mode_unchecked)
                btn.blockSignals(False)

    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
        """Open numeric keypad dialog for setpoint entry."""
        current_text = input_widget.text()
        dialog = NumpadDialog(self, initial_value=current_text, title=title)

        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                input_widget.setText(str(new_value))
                self._write_setpoint(tag, float(new_value)) # Pass new_value directly as float

    def open_time_numpad(self, input_widget: ClickableLineEdit,
                         tag_hours: str = None, tag_minutes: str = None,
                         local_timer_id=None, title: str = "Config. Tiempo"):
        """
        Open time (hh:mm) keypad dialog.
        Updates widget display and sends values to controller if tags are provided.
        """
        current_text = input_widget.text()
        dialog = TimeNumpadDialog(self, initial_hh_mm=current_text, title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                input_widget.setText(f"{hours:02d}:{minutes:02d}")

                # Send to controller if tags are available
                if tag_hours and tag_minutes:
                    print(f"[WRITE] Sending hours ({hours}) to tag: {tag_hours}")
                    self._write_setpoint(tag_hours, float(hours))

                    print(f"[WRITE] Sending minutes ({minutes}) to tag: {tag_minutes}")
                    self._write_setpoint(tag_minutes, float(minutes))
                elif tag_hours or tag_minutes:
                    print("[WARNING] Only one time tag provided. Both hours and minutes tags required.")

                # Optional: local timer configuration (if implemented)
                # if local_timer_id and hasattr(self, '_local_timers_state'):
                #     state = self._local_timers_state[local_timer_id]
                #     total_ms = (hours * 3600 + minutes * 60) * 1000
                #     state["duration_ms"] = total_ms
                #     ...

    def _write_setpoint(self, tag: str, value_input):
        """
        Unified method to write a setpoint value to the controller.
        Accepts either a direct float/int or a ClickableLineEdit widget.
        """
        try:
            value = None
            source = ""
            widget_to_focus_clear = None

            if isinstance(value_input, (float, int)):
                value = float(value_input)
                source = f"direct value {value}"
            elif isinstance(value_input, (ClickableLineEdit, QLineEdit)):
                text = value_input.text().replace(',', '.')
                if not text:
                    print(f"[INFO] Empty input for {tag}, skipping write.")
                    return
                value = float(text)
                source = f"from widget '{text}'"
                widget_to_focus_clear = value_input
            else:
                print(f"[ERROR] Unexpected input type for {tag}: {type(value_input)}")
                return

            print(f"[SETPOINT] Writing {tag} = {value} ({source})")

            target_group = -1
            target_id = -1
            found = False

            for group_key, vars_in_group in VARIABLES.items():
                if isinstance(vars_in_group, dict):
                    for var_id, info in vars_in_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found:
                    break

            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" → Found: Group {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                        if self.parent_window.serial_comm.is_connected:
                            self.parent_window.serial_comm.write_double(target_group, target_id, value)
                        else:
                            print(f"[INFO] Serial not connected. Skipped write: {tag}={value}")
                    else:
                        print(f"[INFO] No serial_comm available in parent. Skipped write: {tag}={value}")
                else:
                    print(f"[WARNING] Variable '{tag}' is not writable (rw=False). Skipped.")
            else:
                print(f"[ERROR] Tag '{tag}' not found in variables map. Skipped write.")

            if widget_to_focus_clear:
                widget_to_focus_clear.clearFocus()
            else:
                self.setFocus() # Esto en un QWidget puede no tener el efecto deseado, si es un child widget.

        except ValueError:
            if isinstance(value_input, (ClickableLineEdit, QLineEdit)):
                print(f"[ERROR] Invalid numeric input for {tag}: '{value_input.text()}'. Reverting.")
                current_val = self.values.get(tag, 0.0)
                value_input.setText(f"{current_val:.1f}")
                value_input.clearFocus()
            else:
                print(f"[ERROR] Conversion error for tag '{tag}': {value_input}")
        except Exception as e:
            print(f"[ERROR] Unexpected error writing setpoint '{tag}': {e}")

    def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        """Update a numeric input field if it doesn't have focus."""
        if not widget.hasFocus():
            value = self.values.get(tag, 0.0)
            widget.setText(f"{value:.{precision}f}")

    def _update_time_display(self, widget: ClickableLineEdit, tag_hours: str, tag_minutes: str):
        """Update hh:mm display from separate hours/minutes tags."""
        if not widget.hasFocus():
            hours = int(self.values.get(tag_hours, 0))
            minutes = int(self.values.get(tag_minutes, 0))
            widget.setText(f"{hours:02d}:{minutes:02d}")
