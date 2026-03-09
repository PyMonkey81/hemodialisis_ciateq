# gui/service/test_panel_screen.py
# Test / Diagnostic panel screen for hemodialysis machine verification and manual control

import logging
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque

from core.variables_map import VARIABLES
from gui.components.LED import LED
from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit, DoubleToggleBox, LabeledParameterWidget

from logic.calculos import (
    convertir_flujo_a_ciclos,
    convertir_ciclos_a_flujo,
    convertir_litros_h_a_ml_min,
    convertir_ml_min_a_litros_h,
    calculo_ptm
)

logger = logging.getLogger(__name__)


class TestPanelScreen(QWidget):
    """
    Diagnostic and test panel for hemodialysis machine.
    Allows manual control of key parameters, real-time monitoring of sensors,
    pressure/temperature/conductivity trends, and LED status indicators.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = parent.current_values if parent else {}

        # Hold-off timers to prevent rapid setpoint writes (tag → timestamp ms)
        self.write_hold_off = {}

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#0f172a")) # Main background is dark blue
        self.setPalette(palette)

        # History buffers for plots (600 points)
        self.history_length = 600
        nan_array = [np.nan] * self.history_length
        self.temp_dialysate_ef_history = deque(nan_array, maxlen=self.history_length)
        self.temp_dialysate_sf_history = deque(nan_array, maxlen=self.history_length)
        self.temp_tank_history = deque(nan_array, maxlen=self.history_length)
        self.cond_ef_history = deque(nan_array, maxlen=self.history_length)
        self.cond_sf_history = deque(nan_array, maxlen=self.history_length)
        self.time_axis = np.arange(-self.history_length + 1, 1, dtype=np.float32)

        self.setup_ui()
        logger.info("Test panel module initialized (v1.0.0)")

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Labels will be on white backgrounds within their own widgets,
        # but the general labels like these need adjustment if parent is dark.
        label_style = "color: #000000; font-size: 18px; font-weight: bold;"
        indicator_style = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px; background: #e0e0e0;" # Added background for visibility
        button_style = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """
        unit_style = "color: #94a3b8; font-size: 16px;"
        input_style = """
            background: #FFFFE5; color: #000000; font-size: 18px; font-weight: bold;
            border: 2px solid #000000; border-radius: 5px; padding: 4px;
        """

        # ── Top Control Area (Input Setpoints & Readings)──────────────────────────
        control_area = QFrame() # Changed to QFrame for styling ease
        control_area.setStyleSheet("background: #fcfcfc; border-radius: 10px; border: 2px solid #1e293b;") # White background
        control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid_top = QGridLayout(control_area)
        grid_top.setSpacing(15)
        grid_top.setContentsMargins(10, 10, 10, 10)

        self.input_cb_flow = LabeledParameterWidget(
            label_text="Flujo CB", 
            tag="balanceChamberSetTiming", # Opcional, referencia
            value="0.0", 
            units="ml/min", # mostrar unidades 
            is_editable=True, 
            # parent=self.control_area
        )
        self.input_cb_flow.request_numpad.connect(lambda tag, wid, tit: self._handle_cb_flow_input())
        grid_top.addWidget(self.input_cb_flow, 0, 0, 1, 2)

        self.input_blood_flow = LabeledParameterWidget(
            label_text="Qb", tag= "bloodFlowControlSetPoint",
            value="0.0",units="ml/min",numpad_title="Flujo de sangre",
            is_editable=True,
        )
        self.input_blood_flow.request_numpad.connect(self.open_numpad)
        grid_top.addWidget(self.input_blood_flow, 1, 0, 1, 2)

        self.input_uf_flow = LabeledParameterWidget(
            label_text="UF", tag="",
            value="0.0", units="L/h", numpad_title="Flujo UF",
            is_editable=True
        )
        self.input_uf_flow.request_numpad.connect(lambda tag, wid, tit: self._handle_uf_flow_input())
        grid_top.addWidget(self.input_uf_flow, 2, 0, 1, 2)

        self.input_cond_setpoint = LabeledParameterWidget(
            label_text="Cond.", tag="dialyCondControlSetPoint",
            value="0.0", units="mS/cm", numpad_title="Condutividad (mS/cm)",
            is_editable=True
        )
        self.input_cond_setpoint.request_numpad.connect(self.open_numpad)
        grid_top.addWidget(self.input_cond_setpoint, 3, 0, 1, 2)

        self.input_temp_setpoint = LabeledParameterWidget(
            label_text="Temp. Dial.", tag="dialyTempControlSetPoint",
            value="0.0", units="°C", numpad_title="Temperatura Dializante",
            is_editable=True,
        )
        self.input_temp_setpoint.request_numpad.connect(self.open_numpad)
        grid_top.addWidget(self.input_temp_setpoint, 4, 0, 1, 2)

        self.label_cycles = LabeledParameterWidget(
            label_text="No. Ciclos CB", tag="balanceChamberCycleCount",
            value="0.0", units="", numpad_title="",
            is_editable=False,
        )
        grid_top.addWidget(self.label_cycles, 0, 3, 1, 2)

        # ── Sensor Readings ──────────────────────────────────────────────────────

        self.label_temp_ef = LabeledParameterWidget(
            label_text="T. Dial. EF", tag="dialyTempIFProcessData",
            value="0.0", units="°C", numpad_title="",
            is_editable=False,
        )
        grid_top.addWidget(self.label_temp_ef, 0, 6, 1, 2)

        self.label_temp_sf = LabeledParameterWidget(
            label_text="T. Dial. SF", tag="dialyTempOFProcessData",
            value="0.0", units="°C",
            is_editable=False
        )
        grid_top.addWidget(self.label_temp_sf, 1, 6, 1, 2)

        self.label_temp_tank = LabeledParameterWidget(
            label_text="T. Tanque", tag="dialyTempControlOutput",
            value="0.0", units="°C",
            is_editable=False
        )
        grid_top.addWidget(self.label_temp_tank, 2, 6, 1, 2)

        self.label_cond_ef = LabeledParameterWidget(
            label_text="Cond. EF", tag="dialyConductIFProcessData",
            value="0.0", units="mS/cm", # Asumo mS/cm, puedes quitarlo si prefieres
            is_editable=False
        )
        grid_top.addWidget(self.label_cond_ef, 3, 6, 1, 2)


        self.label_cond_sf = LabeledParameterWidget(
            label_text="Cond. SF", tag="dialyConductOFProcessData",
            value="0.0", units="mS/cm", # Asumo mS/cm
            is_editable=False
        )
        grid_top.addWidget(self.label_cond_sf, 4, 6, 1, 2)


        # ── Bottom Control Area (Pressures & Navigation) ─────────────────────────
        bottom_control = QFrame() # Changed to QFrame for styling ease
        bottom_control.setStyleSheet("background: #fcfcfc; border-radius: 10px; border: 2px solid #1e293b;") # White background
        bottom_control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid_bottom = QGridLayout(bottom_control)
        grid_bottom.setSpacing(15)
        grid_bottom.setContentsMargins(5, 5, 5, 5) # Adjusted margins for consistency

        # Styles for labels in this area
        
       

        row = 0
        col = 0
        self.label_ptm = self._add_output_row(grid_bottom, row, col, "PTM", "mmHg", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_peristaltic_flow = self._add_output_row(grid_bottom, row, col, "Qb", "ml/min", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt3 = self._add_output_row(grid_bottom, row, col, "PT-3", "psi", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt4 = self._add_output_row(grid_bottom, row, col, "PT-4", "psi", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt5 = self._add_output_row(grid_bottom, row, col, "PT-5", "psi", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt7 = self._add_output_row(grid_bottom, row, col, "PT-7", "psi", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt8 = self._add_output_row(grid_bottom, row, col, "PT-8", "mmHg", label_style=label_style, indicator_style=indicator_style)

        row = 1
        col = 0
        self.label_pt1 = self._add_output_row(grid_bottom, row, col, "PT-1", "mmHg", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt2 = self._add_output_row(grid_bottom, row, col, "PT-2", "mmHg", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt9 = self._add_output_row(grid_bottom, row, col, "PT-9", "mmHg", label_style=label_style, indicator_style=indicator_style)
        col += 3
        self.label_pt10 = self._add_output_row(grid_bottom, row, col, "PT-10", "mmHg", label_style=label_style, indicator_style=indicator_style)
        col += 3

        btn_controller = QPushButton("Controlador")
        btn_controller.setStyleSheet(button_style)
        btn_controller.setFixedSize(200, 70)
        btn_controller.clicked.connect(self.parent_window.show_calibration_screen)
        grid_bottom.addWidget(btn_controller, row, col)

        col += 3
        btn_manual = QPushButton("Op. Manual")
        btn_manual.setStyleSheet(button_style)
        btn_manual.setFixedSize(200, 70)
        btn_manual.clicked.connect(self.parent_window.show_manual_mode_screen)
        grid_bottom.addWidget(btn_manual, row, col)

        

        # ── Plots Area ───────────────────────────────────────────────────────────
        graphics_area = QFrame() # Changed to QFrame for styling ease
        graphics_area.setStyleSheet("background: #fcfcfc;") # White background
        graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid_plots = QGridLayout(graphics_area)
        grid_plots.setSpacing(15)
        grid_plots.setContentsMargins(5, 5, 5, 5)

        tick_font = QFont()
        tick_font.setPixelSize(12)

        # Temperature plot
        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground("#e0e0e0")
        self.temp_plot.setTitle('<span style="font-size: 11pt; color: black;">Temperatura</span>')
        self.temp_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Temperatura (°C)</span>')
        self.temp_plot.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.temp_plot.addLegend()

        self.curve_temp_ef = self.temp_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Temp. Dializante EF")
        self.curve_temp_sf = self.temp_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Temp. Dializante SF")
        self.curve_temp_tank = self.temp_plot.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), name="Temp. Tanque")

        grid_plots.addWidget(self.temp_plot, 0, 0)

        # Conductivity plot
        self.cond_plot = pg.PlotWidget()
        self.cond_plot.setBackground("#e0e0e0")
        self.cond_plot.setTitle('<span style="font-size: 11pt; color: black;">Conductividad</span>')
        self.cond_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Conductividad (mS/cm)</span>')
        self.cond_plot.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.cond_plot.addLegend()

        self.curve_cond_ef = self.cond_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Conductividad EF")
        self.curve_cond_sf = self.cond_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Conductividad SF")

        grid_plots.addWidget(self.cond_plot, 1, 0)

        for plot in [self.temp_plot, self.cond_plot]:
            plot.getAxis('bottom').setStyle(tickFont=tick_font)
            plot.getAxis('left').setStyle(tickFont=tick_font)
            plot.getAxis('bottom').setStyle(tickTextOffset=5)
            plot.getAxis('left').setStyle(tickTextOffset=5)

        

        # ── LED Indicators Area ──────────────────────────────────────────────────
        led_area = QFrame() # Changed to QFrame for styling ease
        led_area.setStyleSheet("background: #fcfcfc;") # White background
        led_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding) #
        grid_led = QGridLayout(led_area)
        grid_led.setSpacing(10)
        grid_led.setContentsMargins(10, 10, 10, 10) # Adjusted margins for consistency

        led_info = [
            ("LS Tanque",           "dialyTankHiLevelSwitch"),
            ("C. Deareación",       "dialyDeaerChamLevSwitch"),
            ("Aire en S.",          "airBubbleInBloodDetected"),
            ("P. Aire",             "dialyPurgePumpStartButt"),
            ("S. Dial.",            "bloodInDialyCircDetected")
        ]

        self.led_widgets = []

        for i, (name, tag) in enumerate(led_info):
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #000000; font-size: 20px; font-weight: bold;") # Black labels on white background
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid_led.addWidget(lbl, i, 0)

            led = LED(led_area)
            led.setFixedSize(45, 45)
            grid_led.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.led_widgets.append((led, tag))

        layout.addWidget(control_area, 0, 0, 1, 2) # control_area now takes col 0 and 1
        layout.addWidget(graphics_area, 0, 2, 1, 1) # graphics_area now takes col 2
        layout.addWidget(led_area, 0, 3, 1, 1) # led_area now takes col 3
        layout.addWidget(bottom_control, 1, 0, 1, 4) # bottom_control now takes col 0, 1, 2, 3


    def _add_output_row(self, grid, row, col, label_text, unit_text, label_style="", indicator_style=""):
        """Helper to add a labeled output row (label + value + unit)."""
        label_style = "color: #000000; font-size: 18px; font-weight: bold;"
        unit_style = "color: #94a3b8; font-size: 16px; border: none;"

        lbl = QLabel(label_text)
        lbl.setStyleSheet(label_style + "border: none;")
        lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        grid.addWidget(lbl, row, col)

        value_label = QLabel("0.0")
        value_label.setStyleSheet(indicator_style)
        value_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        value_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(value_label, row, col + 1)

        unit_lbl = QLabel(unit_text)
        unit_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        unit_lbl.setStyleSheet(unit_style)
        grid.addWidget(unit_lbl, row, col + 2)

        return value_label

    def update_values(self, new_values: dict):
        """Update all displayed values, plots, LEDs, and calculated parameters."""
        self.current_values = new_values
        current_ms = QDateTime.currentMSecsSinceEpoch()

        # ── LEDs ────────────────────────────────────────────────────────────────
        for led, tag in self.led_widgets:
            value = self.current_values.get(tag, 0.0)
            if tag == "dialyDeaerChamLevSwitch":                
                led.set_state("off" if value > 0 else "on") 
            else:
                led.set_state("on" if value > 0 else "off")

        # Removed the self.valve_cards sync loop as it's not applicable to TestPanelScreen UI structure.
        # This section was likely copied mistakenly from ManualModeScreen.

        # ── Balance Chamber Flow (cycles ↔ ml/min) ──────────────────────────────
        if "balanceChamberSetTiming" not in self.write_hold_off or \
           current_ms >= self.write_hold_off["balanceChamberSetTiming"]:
            cycles = self.current_values.get("balanceChamberSetTiming", 0.0)
            try:
                flow_ml_min = convertir_ciclos_a_flujo(cycles)                                
                self._update_input_display(self.input_cb_flow, flow_ml_min, precision=1) 
            except Exception as e:
                logger.error(f"Error converting CB flow: {e}")
                self._update_input_display(self.input_cb_flow, 0.0, precision=1)


        # ── UF Flow (ml/min → L/h) ──────────────────────────────────────────────
        if "ultraFilterPumpSpeed" not in self.write_hold_off or \
           current_ms >= self.write_hold_off["ultraFilterPumpSpeed"]:
            uf_ml_min = self.current_values.get("ultraFilterPumpSpeed", 0.0)
            try:
                uf_lh = convertir_ml_min_a_litros_h(uf_ml_min)   
                self._update_input_display(self.input_uf_flow, uf_lh, precision=1) 
            except Exception as e:
                logger.error(f"Error converting UF flow: {e}")
                self._update_input_display(self.input_uf_flow, 0.0, precision=1)

        # ── Other Inputs & Labels ───────────────────────────────────────────────
        self._update_input_display(self.input_blood_flow, self.current_values.get("bloodFlowControlSetPoint", 0.0))
        self._update_input_display(self.input_temp_setpoint, self.current_values.get("dialyTempControlSetPoint", 0.0))
        self._update_input_display(self.input_cond_setpoint, self.current_values.get("dialyCondControlSetPoint", 0.0))

        self._update_label_display(self.label_cycles, self.current_values.get("balanceChamberCycleCount", 0))
        self._update_label_display(self.label_cond_ef, self.current_values.get("dialyConductIFProcessData", 0.0))
        self._update_label_display(self.label_cond_sf, self.current_values.get("dialyConductOFProcessData", 0.0))
        self._update_label_display(self.label_temp_ef, self.current_values.get("dialyTempIFProcessData",0.0))
        self._update_label_display(self.label_cond_sf, self.current_values.get("dialyTempOFProcessData",0.0))

        # ── Calculated PTM ──────────────────────────────────────────────────────
        pd_ef = self.current_values.get("dialyPresIFProcessData", 0.0)
        pd_sf = self.current_values.get("dialyPresOFProcessData", 0.0)
        pa = self.current_values.get("bloodArteryPressureData", 0.0)
        pv = self.current_values.get("bloodVenousPressureData", 0.0)

        try:
            ptm = calculo_ptm(pd_ef, pd_sf, pa, pv)
        except Exception:
            ptm = 0.0

        self.current_values["CALC_PTM"] = ptm
        self._update_label_display(self.label_ptm, ptm)

        # ── Pressure Outputs ────────────────────────────────────────────────────
        self._update_label_display(self.label_peristaltic_flow, self.current_values.get("bloodFlowVariableData", 0.0))
        self._update_label_display(self.label_pt1, self.current_values.get("dialyLineWaterPresData", 0.0))
        self._update_label_display(self.label_pt2, self.current_values.get("dialyTankPresProcessData", 0.0))
        self._update_label_display(self.label_pt3, self.current_values.get("dialyLinePresProcessData", 0.0))
        self._update_label_display(self.label_pt4, self.current_values.get("dialyPresIFProcessData", 0.0))
        self._update_label_display(self.label_pt5, self.current_values.get("dialyPresOFProcessData", 0.0))
        self._update_label_display(self.label_pt7, self.current_values.get("dialyBChamPresProcessData", 0.0))
        self._update_label_display(self.label_pt8, self.current_values.get("bloodArteryPressureData", 0.0))
        self._update_label_display(self.label_pt9, self.current_values.get("bloodVenousPressureData", 0.0))
        self._update_label_display(self.label_pt10, self.current_values.get("dialyPFilPmpPresProcessData", 0.0))
        self._update_label_display(self.label_temp_tank, self.current_values.get("dialyTempControlOutput",0.0))

        # ── Temperature & Conductivity Plots ─────────────────────────────────────
        temp_ef = self.current_values.get("dialyTempIFProcessData", 0.0)
        temp_sf = self.current_values.get("dialyTempOFProcessData", 0.0)
        temp_tank = self.current_values.get("dialyTempControlOutput", 0.0) # Check if this should be VariableData
        cond_ef = self.current_values.get("dialyConductIFProcessData", 0.0)
        cond_sf = self.current_values.get("dialyConductOFProcessData", 0.0)

        self.temp_dialysate_ef_history.append(temp_ef)
        self.temp_dialysate_sf_history.append(temp_sf)
        self.temp_tank_history.append(temp_tank)
        self.cond_ef_history.append(cond_ef)
        self.cond_sf_history.append(cond_sf)

        self.curve_temp_ef.setData(self.time_axis, list(self.temp_dialysate_ef_history))
        self.curve_temp_sf.setData(self.time_axis, list(self.temp_dialysate_sf_history))
        self.curve_temp_tank.setData(self.time_axis, list(self.temp_tank_history))

        self.curve_cond_ef.setData(self.time_axis, list(self.cond_ef_history))
        self.curve_cond_sf.setData(self.time_axis, list(self.cond_sf_history))

        self.temp_plot.setXRange(-self.history_length + 1, 0)
        self.cond_plot.setXRange(-self.history_length + 1, 0)


    def _update_input_display(self, widget, value, precision=1):
        if not widget.hasFocus():
            if isinstance(widget, LabeledParameterWidget):
                widget.set_value(value)
            elif hasattr(widget, 'setText'):
                widget.setText(f"{value:.{precision}f}")

    def _update_label_display(self, label, value, precision=1):
        if isinstance(label, LabeledParameterWidget):
            label.set_value(value)
        elif hasattr(label, 'setText'):
            label.setText(f"{value:.{precision}f}")


    def _handle_cb_flow_input(self):
        """Handle balance chamber flow input (ml/min → cycles)."""        
        try:
            current_text = self.input_cb_flow.get_value()
            # ANTES: current_text = self.input_flow_cb.text()
        except AttributeError:
            current_text = "0.0"

        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo CB (ml/min)")
        if dialog.exec():
            new_value = dialog.get_value()
            if hasattr(self.input_cb_flow, 'setText'):
                self.input_cb_flow.setText(str(new_value))            
            try:
                cycles = convertir_flujo_a_ciclos(new_value)
                self._write_setpoint("balanceChamberSetTiming", cycles)
                self.write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error converting CB flow: {e}")

    def _handle_uf_flow_input(self):
        """Handle UF flow input (L/h → ml/min)."""
        try:
            # current_text = self.input_uf_flow.text()
            current_text = self.input_uf_flow.get_value()
        except AttributeError:
            current_text = "0.0"

        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo UF (L/h)")
        if dialog.exec():
            new_value = dialog.get_value()
            # self.input_uf_flow.setText(str(new_value))
            self.input_uf_flow.set_value(new_value)
            try:
                ml_min = convertir_litros_h_a_ml_min(new_value)
                self._write_setpoint("ultraFilterPumpSpeed", ml_min)
                self.write_hold_off["ultraFilterPumpSpeed"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error converting UF flow: {e}")

    def open_numpad(self, tag: str, input_widget, title: str = "Ingrese valor"):
        """Open numeric keypad for setpoint entry."""    
    # 1. Obtener el valor actual de forma segura
        if hasattr(input_widget, 'get_value'):
        # Es un LabeledParameterWidget
            current_text = input_widget.get_value()
        else:
            # Es un QLineEdit estándar
            current_text = input_widget.text()

        dialog = NumpadDialog(self, initial_value=current_text, title=title)
    
        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:            
                # 2. Establecer el nuevo valor de forma segura
                if hasattr(input_widget, 'set_value'):
                     # Es un LabeledParameterWidget
                    input_widget.set_value(new_value)
                else:
                    # Es un QLineEdit estándar
                    input_widget.setText(str(new_value))
            
                self._write_setpoint(tag, new_value)
                self.write_hold_off[tag] = QDateTime.currentMSecsSinceEpoch() + 3000


    def _write_setpoint(self, tag: str, value: float):
        """Write setpoint value to controller safely."""
        try:
            logger.info(f"Writing setpoint {tag} = {value}")

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
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                        if self.parent_window.serial_comm.is_connected:
                            self.parent_window.serial_comm.write_double(target_group, target_id, value)
                            logger.info(f"Setpoint written: {tag} = {value}")
                        else:
                            logger.warning("Serial not connected")
                            QMessageBox.warning(self, "Comunicación", "Serial no conectado")
                    else:
                        logger.warning("Serial communication not available")
                else:
                    logger.warning(f"Tag '{tag}' is read-only")
                    QMessageBox.warning(self, "Error", f"'{tag}' es de solo lectura")
            else:
                logger.error(f"Tag '{tag}' not found in variables map")
                QMessageBox.critical(self, "Error", f"Tag '{tag}' no encontrado")

        except Exception as e:
            logger.error(f"Critical error writing setpoint '{tag}': {e}")
            QMessageBox.critical(self, "Error Crítico", f"Error al escribir {tag}: {e}")
