# gui/service/calibration_screen.py
# Low-level calibration and controller tuning screen
# Allows enabling control loops, adjusting PID gains, feedforward, and monitoring setpoints/variables/outputs

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import pyqtgraph as pg
import numpy as np
from collections import deque

from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit, DoubleToggleBox

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class CalibrationScreen(QWidget):
    """
    Calibration and low-level controller tuning screen.
    Enables/disables control loops, adjusts PID gains/feedforward,
    and displays real-time setpoint/variable/output trends for blood flow,
    conductivity, and temperature controllers.
    """

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.values = values_dict if values_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#fcfcfc"))
        self.setPalette(palette)

        # Toggle switches mapping (tag → ToggleSwitch widget)
        self.control_loop_toggles = {}

        # Plot history buffers (600 points ~5 min at 500 ms update)
        self.history_length = 600
        nan_array = [np.nan] * self.history_length

        # Blood flow control
        self.blood_flow_setpoint_history = deque(nan_array, maxlen=self.history_length)
        self.blood_flow_variable_history = deque(nan_array, maxlen=self.history_length)
        self.blood_flow_output_history   = deque(nan_array, maxlen=self.history_length)

        # Conductivity control
        self.cond_setpoint_history = deque(nan_array, maxlen=self.history_length)
        self.cond_variable_history = deque(nan_array, maxlen=self.history_length)
        self.cond_output_history   = deque(nan_array, maxlen=self.history_length)

        # Temperature control
        self.temp_setpoint_history = deque(nan_array, maxlen=self.history_length)
        self.temp_variable_history = deque(nan_array, maxlen=self.history_length)
        self.temp_output_history   = deque(nan_array, maxlen=self.history_length)

        self.time_axis = np.arange(-self.history_length + 1, 1, dtype=np.float32)

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── Plots Area ───────────────────────────────────────────────────────────
        graphics_area = QWidget()
        graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid_graphics = QGridLayout(graphics_area)
        grid_graphics.setSpacing(15)
        grid_graphics.setContentsMargins(5, 5, 5, 5)

        tick_font = QFont()
        tick_font.setPixelSize(12)

        # Blood Flow Control Plot
        self.blood_flow_control_plot = pg.PlotWidget()
        self.blood_flow_control_plot.setBackground("#e0e0e0")
        self.blood_flow_control_plot.setTitle('<span style="font-size: 11pt; color: black;">Control de Flujo de Sangre</span>')
        self.blood_flow_control_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Flujo Qb / Salida (%)</span>')
        self.blood_flow_control_plot.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.blood_flow_control_plot.addLegend()

        self.curve_bf_setpoint = self.blood_flow_control_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint CFS")
        self.curve_bf_variable = self.blood_flow_control_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable CFS")
        self.curve_bf_output   = self.blood_flow_control_plot.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida CFS (%)")

        grid_graphics.addWidget(self.blood_flow_control_plot, 0, 0)

        # Conductivity Control Plot
        self.cond_control_plot = pg.PlotWidget()
        self.cond_control_plot.setBackground("#e0e0e0")
        self.cond_control_plot.setTitle('<span style="font-size: 11pt; color: black;">Control de Conductividad</span>')
        self.cond_control_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Conductividad (mS/cm)</span>')
        self.cond_control_plot.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.cond_control_plot.addLegend()

        self.curve_cond_setpoint = self.cond_control_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Cond.")
        self.curve_cond_variable = self.cond_control_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Cond.")
        self.curve_cond_output   = self.cond_control_plot.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida Cond. (%)")

        grid_graphics.addWidget(self.cond_control_plot, 1, 0)

        # Temperature Control Plot
        self.temp_control_plot = pg.PlotWidget()
        self.temp_control_plot.setBackground("#e0e0e0")
        self.temp_control_plot.setTitle('<span style="font-size: 11pt; color: black;">Control de Temperatura</span>')
        self.temp_control_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Temperatura Dializante (°C)</span>')
        self.temp_control_plot.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.temp_control_plot.addLegend()

        self.curve_temp_setpoint = self.temp_control_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Temp.")
        self.curve_temp_variable = self.temp_control_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Temp.")
        self.curve_temp_output   = self.temp_control_plot.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida Temp. (%)")

        grid_graphics.addWidget(self.temp_control_plot, 2, 0)

        for plot in [self.blood_flow_control_plot, self.cond_control_plot, self.temp_control_plot]:
            plot.getAxis('bottom').setStyle(tickFont=tick_font)
            plot.getAxis('left').setStyle(tickFont=tick_font)
            plot.getAxis('bottom').setStyle(tickTextOffset=5)
            plot.getAxis('left').setStyle(tickTextOffset=5)

        # layout.addWidget(graphics_area, 0, 5)

        # ── Control Area ─────────────────────────────────────────────────────────
        control_area = QWidget()
        control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout(control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)

        # ── Control Loop Enable / Mode Toggles ───────────────────────────────────
        control_loop_info = [
            (0, 0, "bloodControlLoopEnable",     "Hab. CFS"),
            (1, 0, "bloodControlLoopMode",       "Hab. Modo CFS"),
            (2, 0, "dialyCondCtrlLoopEnable",    "Hab. CC"),
            (3, 0, "dialyCondCtrlLoopMode",      "Hab. Modo CC"),
            (4, 0, "dialyTempCtrlLoopEnable",    "Hab. CTD"),
            (5, 0, "dialyTempCtrlLoopMode",      "Hab. Modo CTD"),
        ]

        current_row = 0
        for i in range(0, len(control_loop_info), 2):
            enable_tag = control_loop_info[i][2]
            enable_label = control_loop_info[i][3]
            mode_tag = control_loop_info[i+1][2]
            mode_label = control_loop_info[i+1][3]

            double_box = DoubleToggleBox(enable_label, mode_label)
            grid.addWidget(double_box, current_row, 0, 2, 2)

            # Conexiones
            double_box.toggle1.toggled.connect(lambda checked, t=enable_tag: self._toggle_control_loop(t, checked))
            double_box.toggle2.toggled.connect(lambda checked, t=mode_tag: self._toggle_control_loop(t, checked))

            self.control_loop_toggles[enable_tag] = double_box.toggle1
            self.control_loop_toggles[mode_tag] = double_box.toggle2

            current_row += 2

        # ── Setpoint / Output / Variable Rows ────────────────────────────────────
        current_row = 0
        target_col = 3

        # Blood Flow (CFS)
        self.blood_flow_setpoint_input = self._add_control_row(grid, current_row, target_col, "SetPoint CFS", "ml/min", tag="bloodFlowControlSetPoint", numpad_title="Setpoint CFS (ml/min)")
        current_row += 1
        self.blood_flow_output_input   = self._add_control_row(grid, current_row, target_col, "Salida CFS", "%", tag="bloodFlowControlOutput", numpad_title="Salida CFS (%)")
        current_row += 1
        self.blood_flow_variable_label = self._add_control_row(grid, current_row, target_col, "Variable CFS", "ml/min", is_input=False)
        current_row += 1

        # Conductivity (CC)
        self.cond_setpoint_input = self._add_control_row(grid, current_row, target_col, "SetPoint Cond.", "mS/cm", tag="dialyCondControlSetPoint", numpad_title="Setpoint Conductividad (mS/cm)")
        current_row += 1
        self.cond_output_input   = self._add_control_row(grid, current_row, target_col, "Salida Cond.", "%", tag="dialyCondControlOutput", numpad_title="Salida Conductividad (%)")
        current_row += 1
        self.cond_variable_label = self._add_control_row(grid, current_row, target_col, "Variable Cond.", "mS/cm", is_input=False)
        current_row += 1

        # Temperature (CTD)
        self.temp_setpoint_input = self._add_control_row(grid, current_row, target_col, "SetPoint Temp.", "°C", tag="dialyTempControlSetPoint", numpad_title="Setpoint Temperatura (°C)")
        current_row += 1
        self.temp_output_input   = self._add_control_row(grid, current_row, target_col, "Salida Temp.", "%", tag="dialyTempControlOutput", numpad_title="Salida Temperatura (%)")
        current_row += 1
        self.temp_variable_label = self._add_control_row(grid, current_row, target_col, "Variable Temp.", "°C", is_input=False)
        current_row += 1

        # ── Feedforward & PID Gains ──────────────────────────────────────────────
        ff_row = 0
        ff_col = 6

        self.blood_speed_rpm_label = self._add_control_row(grid, ff_row, ff_col, "Velocidad BS", "RPM", is_input=False)
        ff_row += 1
        self.feedforward_gain_input = self._add_control_row(grid, ff_row, ff_col, "FFWD", "", tag="bloodFlowFeedForwardGain", numpad_title="Ganancia FFWD")
        ff_row += 1
        self.feedforward_lead_input = self._add_control_row(grid, ff_row, ff_col, "Lead FFWD", "", tag="bloodFlowFeedForwardLead", numpad_title="Lead FFWD")

        pid_row = 0
        pid_col = 9

        # Blood Flow PID
        self.blood_flow_kp_input = self._add_control_row(grid, pid_row, pid_col, "CFS", "kp", tag="bloodFlowControlPropGain", numpad_title="CFS Kp Gain")
        pid_row += 1
        self.blood_flow_ki_input = self._add_control_row(grid, pid_row, pid_col, "CFS", "ki", tag="bloodFlowControlInteGain", numpad_title="CFS Ki Gain")
        pid_row += 1
        self.blood_flow_kd_input = self._add_control_row(grid, pid_row, pid_col, "CFS", "kd", tag="bloodFlowControlDeriGain", numpad_title="CFS Kd Gain")
        pid_row += 1

        # Conductivity PID
        self.cond_kp_input = self._add_control_row(grid, pid_row, pid_col, "Cond.", "kp", tag="dialyCondControlPropGain", numpad_title="Cond. Kp Gain")
        pid_row += 1
        self.cond_ki_input = self._add_control_row(grid, pid_row, pid_col, "Cond.", "ki", tag="dialyCondControlInteGain", numpad_title="Cond. Ki Gain")
        pid_row += 1
        self.cond_kd_input = self._add_control_row(grid, pid_row, pid_col, "Cond.", "kd", tag="dialyCondControlDeriGain", numpad_title="Cond. Kd Gain")
        pid_row += 1

        # Temperature PID
        self.temp_kp_input = self._add_control_row(grid, pid_row, pid_col, "Temp.", "kp", tag="dialyTempControlPropGain", numpad_title="Temp. Kp Gain")
        pid_row += 1
        self.temp_ki_input = self._add_control_row(grid, pid_row, pid_col, "Temp.", "ki", tag="dialyTempControlInteGain", numpad_title="Temp. Ki Gain")
        pid_row += 1
        self.temp_kd_input = self._add_control_row(grid, pid_row, pid_col, "Temp.", "kd", tag="dialyTempControlDeriGain", numpad_title="Temp. Kd Gain")

        layout.addWidget(control_area, 0, 0)
        layout.addWidget(graphics_area, 0, 5)

    def _add_control_row(self, grid, row, col, label_text, unit_text, tag=None, numpad_title="", is_input=True, initial_value="0.0"):
        """Helper to add a labeled control row (label + input/display + unit)."""
        label = QLabel(label_text)
        grid.addWidget(label, row, col)

        if is_input:
            widget = ClickableLineEdit(initial_value)
            widget.setReadOnly(True)
            widget.setStyleSheet("""
                background: #FFFFE5;
                color: #000000;
                border: 2px solid #000000;
                border-radius: 6px;
                padding: 4px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 20px;
                font-weight: bold;
            """)
            if tag and numpad_title:
                widget.clicked.connect(lambda: self.open_numpad(tag, widget, numpad_title))
        else:
            widget = QLabel(initial_value)
            widget.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;")
            widget.setProperty("class", "highlighted")

        widget.setFixedSize(80, 35)
        widget.setAlignment(Qt.AlignCenter)
        grid.addWidget(widget, row, col + 1)

        unit_label = QLabel(unit_text)
        unit_label.setStyleSheet("color: #94a3b8; font-size: 16px;")
        grid.addWidget(unit_label, row, col + 2)

        return widget

    def _toggle_control_loop(self, tag: str, enabled: bool):
        """Enable/disable a control loop."""
        if enabled:
            print(f"[CONTROL] Habilitado {tag}")
            self._write_boolean_command(tag, True)
        else:
            print(f"[CONTROL] Deshabilitado {tag}")
            self._write_boolean_command(tag, False)

    def _write_boolean_command(self, tag: str, state: bool):
        """Send boolean command to controller."""
        print(f"[COMMAND] Usuario cambió {tag} a {state}")

        address = -1
        if 0x01 in VARIABLES:
            for var_id, info in VARIABLES[0x01].items():
                if info.get("tag") == tag:
                    address = var_id
                    break

        if address != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                if self.parent_window.serial_comm.is_connected:
                    self.parent_window.serial_comm.write_boolean(address, state)
                    print(f" → Enviado: Addr {address} = {state}")
                else:
                    print(" → Serial no conectado")
            else:
                print("[INFO] Serial no disponible")
        else:
            print(f" → Tag '{tag}' no encontrado")

    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str = "Ingrese valor"):
        """Open numeric keypad for setpoint entry."""
        current_text = input_widget.text()
        dialog = NumpadDialog(self, initial_value=current_text, title=title)
        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                input_widget.setText(str(new_value))
                self._write_setpoint(tag, input_widget)

    def _write_setpoint(self, tag: str, input_widget: ClickableLineEdit):
        """Safe setpoint write from input widget."""
        try:
            text = input_widget.text().replace(',', '.')
            if not text:
                current_value = self.values.get(tag, 0.0)
                input_widget.setText(f"{current_value:.1f}")
                return

            value = float(text)
            print(f"[SETPOINT] Intentando escribir {tag} = {value}")

            target_group = target_id = -1
            found = False

            for group_key, vars_group in VARIABLES.items():
                if isinstance(vars_group, dict):
                    for var_id, info in vars_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found:
                    break

            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" → Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                        if self.parent_window.serial_comm.is_connected:
                            self.parent_window.serial_comm.write_double(target_group, target_id, value)
                        else:
                            print(f"[INFO] Serial no conectado. {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {value}")
                    else:
                        print(f"[INFO] No serial_comm disponible en parent. {tag}={value}")
                else:
                    print(f"[ADVERTENCIA] Variable '{tag}' no escribible (rw=False).")
            else:
                print(f"[ERROR] Tag '{tag}' no encontrado en variables_map.")

            input_widget.clearFocus()
            self.setFocus()

        except ValueError:
            print(f"[ERROR] Valor numérico inválido en input para {tag}: {input_widget.text()}")
            current_value = self.values.get(tag, 0.0)
            input_widget.setText(f"{current_value:.1f}")
            input_widget.clearFocus()
        except Exception as e:
            print(f"[ERROR] Error al escribir setpoint {tag}: {e}")

    def update_values(self, new_values: dict):
        """Update displayed values, plots, and inputs from shared dictionary."""
        self.values = new_values

        # ── Blood Flow ───────────────────────────────────────────────────────────
        bf_setpoint = self.values.get("bloodFlowControlSetPoint", 0.0)
        bf_variable = self.values.get("bloodFlowVariableData", 0.0)
        bf_output_raw = self.values.get("bloodFlowControlOutput", 0.0)
        bf_output_percent = bf_output_raw * 10  # Asumiendo escala 0-10 → %

        self.blood_flow_setpoint_history.append(bf_setpoint)
        self.blood_flow_variable_history.append(bf_variable)
        self.blood_flow_output_history.append(bf_output_percent)

        self.curve_bf_setpoint.setData(self.time_axis, list(self.blood_flow_setpoint_history))
        self.curve_bf_variable.setData(self.time_axis, list(self.blood_flow_variable_history))
        self.curve_bf_output.setData(self.time_axis, list(self.blood_flow_output_history))

        # ── Conductivity ─────────────────────────────────────────────────────────
        cond_setpoint = self.values.get("dialyCondControlSetPoint", 0.0)
        cond_variable = self.values.get("dialyCondVariableData", 0.0)
        cond_output_raw = self.values.get("dialyCondControlOutput", 0.0)
        cond_output_percent = cond_output_raw / 5  # Asumiendo escala

        self.cond_setpoint_history.append(cond_setpoint)
        self.cond_variable_history.append(cond_variable)
        self.cond_output_history.append(cond_output_percent)

        self.curve_cond_setpoint.setData(self.time_axis, list(self.cond_setpoint_history))
        self.curve_cond_variable.setData(self.time_axis, list(self.cond_variable_history))
        self.curve_cond_output.setData(self.time_axis, list(self.cond_output_history))

        # ── Temperature ──────────────────────────────────────────────────────────
        temp_setpoint = self.values.get("dialyTempControlSetPoint", 0.0)
        temp_variable = self.values.get("dialyTempVariableData", 0.0)
        temp_output_raw = self.values.get("dialyTempControlOutput", 0.0)
        temp_output_percent = temp_output_raw / 2  # Asumiendo escala

        self.temp_setpoint_history.append(temp_setpoint)
        self.temp_variable_history.append(temp_variable)
        self.temp_output_history.append(temp_output_percent)

        self.curve_temp_setpoint.setData(self.time_axis, list(self.temp_setpoint_history))
        self.curve_temp_variable.setData(self.time_axis, list(self.temp_variable_history))
        self.curve_temp_output.setData(self.time_axis, list(self.temp_output_history))

        # Fixed X range
        for plot in [self.blood_flow_control_plot, self.cond_control_plot, self.temp_control_plot]:
            plot.setXRange(-self.history_length + 1, 0)

        # ── Numeric Inputs & Labels ──────────────────────────────────────────────
        self._update_input_display(self.blood_flow_setpoint_input, "bloodFlowControlSetPoint")
        self._update_input_display(self.blood_flow_output_input, "bloodFlowControlOutput")
        self._update_label_display(self.blood_flow_variable_label, "bloodFlowVariableData")

        self._update_input_display(self.cond_setpoint_input, "dialyCondControlSetPoint")
        self._update_input_display(self.cond_output_input, "dialyCondControlOutput")
        self._update_label_display(self.cond_variable_label, "dialyCondVariableData")

        self._update_input_display(self.temp_setpoint_input, "dialyTempControlSetPoint")
        self._update_input_display(self.temp_output_input, "dialyTempControlOutput")
        self._update_label_display(self.temp_variable_label, "dialyTempVariableData")

        self._update_label_display(self.blood_speed_rpm_label, "bloodSpeedVariableData")

        self._update_input_display(self.feedforward_gain_input, "bloodFlowFeedForwardGain")
        self._update_input_display(self.feedforward_lead_input, "bloodFlowFeedForwardLead")

        # PID Gains
        self._update_input_display(self.blood_flow_kp_input, "bloodFlowControlPropGain")
        self._update_input_display(self.blood_flow_ki_input, "bloodFlowControlInteGain")
        self._update_input_display(self.blood_flow_kd_input, "bloodFlowControlDeriGain")

        self._update_input_display(self.cond_kp_input, "dialyCondControlPropGain")
        self._update_input_display(self.cond_ki_input, "dialyCondControlInteGain")
        self._update_input_display(self.cond_kd_input, "dialyCondControlDeriGain")

        self._update_input_display(self.temp_kp_input, "dialyTempControlPropGain")
        self._update_input_display(self.temp_ki_input, "dialyTempControlInteGain")
        self._update_input_display(self.temp_kd_input, "dialyTempControlDeriGain")

    def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        """Update input field if not focused."""
        value = self.values.get(tag, 0.0)
        if not widget.hasFocus():
            widget.setText(f"{value:.{precision}f}")

    def _update_label_display(self, label, tag: str, precision: int = 1):
        """Update read-only label."""
        value = self.values.get(tag, 0.0)
        label.setText(f"{value:.{precision}f}")

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()