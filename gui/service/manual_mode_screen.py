# gui/service/manual_mode_screen.py
# Manual mode screen for direct control of pumps, valves, and critical actuators
# Critical safety features: REQ-SW-005, REQ-SW-010, REQ-SW-012, REQ-SW-020

import logging
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

# Asumo que estas importaciones existen en tu proyecto
from gui.components.LED import LED
from gui.components.ToggleSwitch import ToggleSwitch
from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit, LabeledParameterWidget, LabeledTimeInput

from core.variables_map import VARIABLES
from logic.calculos import (
    convertir_flujo_a_ciclos,
    convertir_ciclos_a_flujo,
    convertir_litros_h_a_ml_min,
    convertir_ml_min_a_litros_h
)

logger = logging.getLogger(__name__)


class ValveCard(QFrame):
    """Reusable card component for valve control (REQ-SW-005)."""

    def __init__(self, code: str, description: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 2px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Aquí usamos HTML para el salto de línea y estilos
        info_label = QLabel(f"<b>{code}</b><br><span style='font-size:18px; color:#cbd5e1;'>{description}</span>")
        info_label.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
        info_label.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=70, height=30, parent=self)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(self.toggle)


class ManualModeScreen(QWidget):
    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.values = values_dict if values_dict is not None else {}

        self.write_hold_off = {}

        self._setup_timers()
        self.setup_ui()
        logger.info("Manual mode module initialized (v1.0.0)")

    def _setup_timers(self):
        self.blood_pump_timer = QTimer(self)
        self.blood_pump_timer.timeout.connect(self._stop_blood_pump_on_timeout)

        self.dialysate_pump_timer = QTimer(self)
        self.dialysate_pump_timer.timeout.connect(self._stop_dialysate_pump_on_timeout)

        self.uf_pump_timer = QTimer(self)
        self.uf_pump_timer.timeout.connect(self._stop_uf_pump_on_timeout)

        self.heparin_pump_timer = QTimer(self)
        self.heparin_pump_timer.timeout.connect(self._stop_heparin_pump_on_timeout)

        self.balance_chamber_timer = QTimer(self)
        self.balance_chamber_timer.timeout.connect(self._stop_balance_chamber_on_timeout)

        self.display_update_timer = QTimer(self)
        self.display_update_timer.timeout.connect(self._update_local_time_displays)
        self.display_update_timer.start(500)

        self.local_timer_states = {
            "blood_pump":     {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "dialysate_pump": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "uf_pump":        {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "heparin_pump":   {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "balance_chamber": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},          
        }

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        label_style = "color: #000000; font-size: 18px; font-weight: bold; border: none; background: transparent;"
        indicator_style = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        button_style = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 20px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """
        input_style = """
            background: #FFFFE5; color: #000000; font-size: 18px; font-weight: bold;
            border: 2px solid #000000; border-radius: 5px; padding: 4px;
        """

        self.control_area = QWidget(self)
        self.control_area.setStyleSheet("background: #fcfcfc; border: None;")
        self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout(self.control_area)
        grid.setSpacing(10)
        grid.setContentsMargins(5, 5, 5, 5)

        # Configuración del Grid (Espacio en el medio)
        # Izquierda: cols 0-3 | Espacio: col 4 | Derecha: cols 5-13
        grid.setColumnStretch(4, 1) 

        # ==============================================================================
        # --- FILA 0: Dosis Heparina(1), Bolo(2) | Sangre(3,4,5,6,7) ---
        # ==============================================================================
        
        # 1. Dosis de heparina (Izq)
        self.input_heparin = LabeledParameterWidget(
            label_text="Dosis Hep.", tag="heparineTherapyDosage",
            value="0.0", units="ml/h", numpad_title="Dosis Heparina",
            is_editable=True, parent=self.control_area
        )
        self.input_heparin.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_heparin, 0, 0, 1, 2)

        # 2. Bolus (Izq)
        self.input_bolus = LabeledParameterWidget(
            label_text="Bolo", tag="heparineBolusQuantity",
            value="0.0", units="ml", numpad_title="Dosis Bolo",
            is_editable=True, parent=self.control_area
        )
        self.input_bolus.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_bolus, 0, 2, 1, 2)

        # 3. Toggle b. sangre (Der)
        lbl_blood_pump = QLabel("B. S.")
        lbl_blood_pump.setStyleSheet(label_style)
        grid.addWidget(lbl_blood_pump, 0, 5, 1, 1)

        self.blood_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.blood_pump_toggle.toggled.connect(
            lambda checked: self._handle_dual_pump_toggle(
                "bloodPumpStartButton", "bloodPumpStopButton", checked, timer_id="blood_pump"
            )
        )
        grid.addWidget(self.blood_pump_toggle, 0, 6, 1, 1)

        # 4. Btn REV sangre (Der)
        self.btn_rev = QPushButton("REV")
        self.btn_rev.setFixedSize(80, 70) # Mantengo tu tamaño original
        self.btn_rev.setStyleSheet(button_style)        
        self.btn_rev.pressed.connect(lambda: self._write_boolean_command("bloodPumpREVButton", True))
        self.btn_rev.released.connect(lambda: self._write_boolean_command("bloodPumpREVButton", False))
        grid.addWidget(self.btn_rev, 0, 7, 1, 1)

        # 5. Btn FWD sangre (Der)
        btn_fwd = QPushButton("FWD")
        btn_fwd.setFixedSize(80, 70)
        btn_fwd.setStyleSheet(button_style)
        btn_fwd.pressed.connect(lambda: self._write_boolean_command("bloodPumpFWDButton", True))
        btn_fwd.released.connect(lambda: self._write_boolean_command("bloodPumpFWDButton", False))
        grid.addWidget(btn_fwd, 0, 8, 1, 1)

        # 6. Flujo Sangre (Der)
        self.blood_flow_input = LabeledParameterWidget(
            label_text="Flujo", tag="bloodFlowControlSetPoint",
            value="0", units="ml/min", numpad_title="Flujo de Sangre",
            is_editable=True, parent=self.control_area
        )
        self.blood_flow_input.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.blood_flow_input, 0, 9, 1, 2)

        # 7. Velocidad Sangre (Der)
        self.blood_speed_display = LabeledParameterWidget(
            label_text="Vel", tag="bloodSpeedVariableData",
            value="0.0", units="rpm", is_editable=False, parent=self.control_area
        )
        grid.addWidget(self.blood_speed_display, 0, 11, 1, 2)


        # ==============================================================================
        # --- FILA 1: Jeringa(8), Btn Bolo(9) | Tiempos Sangre(10, 11) ---
        # ==============================================================================

        # 8. Jeringa (Izq)
        self.input_syringe_size = LabeledParameterWidget(
            label_text="Jeringa", tag="heparineSyrinjeScaleSize",
            value="0.0", units="mm/ml", numpad_title="Tamaño de jeringa",
            is_editable=True, parent=self.control_area
        )
        self.input_syringe_size.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_syringe_size, 1, 0, 1, 2)

        # 9. Btn aplicar bolo (Izq)
        btn_bolus_apply = QPushButton("Aplicar\nbolo", self.control_area)
        btn_bolus_apply.setFixedSize(120, 70)
        btn_bolus_apply.setStyleSheet(button_style)
        btn_bolus_apply.pressed.connect(lambda: self.parent_window._write_boolean_command("heparinApplyBolusDose", True))
        btn_bolus_apply.released.connect(lambda: self.parent_window._write_boolean_command("heparinApplyBolusDose", False))
        grid.addWidget(btn_bolus_apply, 1, 2, 1, 2, alignment=Qt.AlignCenter)

        # 10. Tiempo operación b. sangre (Der)
        self.blood_pump_time_input = LabeledTimeInput(
            label_text="Tiempo Op.:", initial_hh_mm="00:00",
            tag_hours=None, tag_minutes=None, local_timer_id="blood_pump",
            numpad_title="Tiempo de operación de bomba de sangre",
            is_editable=True,
            parent=self.control_area
        )
        self.blood_pump_time_input.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.blood_pump_time_input, 1, 9, 1, 2)

        # 11. Rest b. sangre (Der)
        self.remaining_blood_time_label = LabeledTimeInput(
            label_text="Rest.:", 
            initial_hh_mm="00:00",
            is_editable=False,
            parent=self.control_area
        )        
        grid.addWidget(self.remaining_blood_time_label, 1, 11, 1, 2)
        self.local_timer_states["blood_pump"]["remaining_lbl"] = self.remaining_blood_time_label.time_display


        # ==============================================================================
        # --- FILA 2: Terapia(12, 43) | B. Heparina (13-18) ---
        # ==============================================================================

        # 12. Tiempo terapia (Izq)
        self.heparin_time_input = LabeledTimeInput(
            label_text="T. Terapia:", initial_hh_mm="00:00",
            tag_hours="heparineTherapyHours", tag_minutes="heparineTherapyMinutes",
            local_timer_id="heparin_pump", numpad_title="Tiempo de terapia",
            is_editable=True,
            parent=self.control_area
        )
        self.heparin_time_input.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.heparin_time_input, 2, 0, 1, 2) 

        # 43. Rest. Terapia (Izq)
        self.remaining_heparin_pump = LabeledTimeInput(
            label_text="Rest.:", 
            initial_hh_mm="00:00",
            is_editable=False,
            parent=self.control_area
        )        
        grid.addWidget(self.remaining_heparin_pump, 2, 2, 1, 2)       

        self.local_timer_states["heparin_pump"]["remaining_lbl"] = self.remaining_heparin_pump.time_display

        # 13. Toggle b. heparina (Der)
        lbl_heparin_pump = QLabel("B. Hep.", self.control_area)
        lbl_heparin_pump.setStyleSheet(label_style)
        grid.addWidget(lbl_heparin_pump, 2, 5, 1, 1)

        self.heparin_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.heparin_pump_toggle.toggled.connect(
            lambda checked: self._handle_dual_pump_toggle("heparinePumpsStartButton", "heparinePumpsStopButton", checked, timer_id="heparin_pump")
        )
        grid.addWidget(self.heparin_pump_toggle, 2, 6, 1, 1)

        # 14. Btn HOME heparina
        btn_heparin_home = QPushButton("HOME", self.control_area)
        btn_heparin_home.setFixedSize(80, 70)
        btn_heparin_home.setStyleSheet(button_style)
        btn_heparin_home.pressed.connect(lambda: self._write_boolean_command("heparinePumpHomePosition", True))
        btn_heparin_home.released.connect(lambda: self._write_boolean_command("heparinePumpHomePosition", False))
        grid.addWidget(btn_heparin_home, 2, 7, 1, 1)

        # 15. Btn REV heparina
        btn_rev_hep = QPushButton("REV", self.control_area)
        btn_rev_hep.setFixedSize(80, 70)
        btn_rev_hep.setStyleSheet(button_style)
        btn_rev_hep.pressed.connect(lambda: self._write_boolean_command("heparinePumpREVButton", True))
        btn_rev_hep.released.connect(lambda: self._write_boolean_command("heparinePumpREVButton", False))
        grid.addWidget(btn_rev_hep, 2, 8, 1, 1)

        # 16. Btn PAUSE heparina
        btn_pause_hep = QPushButton("PAUSE", self.control_area)
        btn_pause_hep.setFixedSize(80, 70)
        btn_pause_hep.setStyleSheet(button_style)
        btn_pause_hep.pressed.connect(lambda: self._write_boolean_command("heparineOperPauseResume", True))
        btn_pause_hep.released.connect(lambda: self._write_boolean_command("heparineOperPauseResume", False))
        grid.addWidget(btn_pause_hep, 2, 9, 1, 1)

        # 17. Btn FWD heparina
        btn_fwd_hep = QPushButton("FWD", self.control_area)
        btn_fwd_hep.setFixedSize(80, 70)
        btn_fwd_hep.setStyleSheet(button_style)
        btn_fwd_hep.pressed.connect(lambda: self._write_boolean_command("heparinePumpFWDButton", True))
        btn_fwd_hep.released.connect(lambda: self._write_boolean_command("heparinePumpFWDButton", False))
        grid.addWidget(btn_fwd_hep, 2, 10, 1, 1)

        # 18. Heparina (Acumulado)
        self.heparin_current_dosage_display = LabeledParameterWidget(
            label_text="Hep.", tag="heparineCurrentDosage",
            value="0.0", units="ml", is_editable=False, parent=self.control_area
        )
        grid.addWidget(self.heparin_current_dosage_display, 2, 11, 1, 2)


        # ==============================================================================
        # SEPARADOR CENTRAL (Usamos Frame HLine)
        # ==============================================================================
        # linea = QFrame(); linea.setFrameShape(QFrame.HLine); linea.setStyleSheet("color: #ccc;")
        # grid.addWidget(linea, 3, 0, 1, 13)


        # ==============================================================================
        # --- FILA 4: Camara Balance(19,20) | B. Dializante (21-24) ---
        # ==============================================================================

        # 19. Toggle camara balance (Izq)
        lbl_cb = QLabel("C. Balance", self.control_area)
        lbl_cb.setStyleSheet(label_style)
        grid.addWidget(lbl_cb, 4, 0, 1, 1)

        self.balance_chamber_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.balance_chamber_toggle.toggled.connect(
            lambda chk: self._handle_dual_pump_toggle("dialiserBalChambStrButt", "dialiserBalChambStpButt", chk, timer_id="balance_chamber")
        )
        grid.addWidget(self.balance_chamber_toggle, 4, 1, 1, 1)

        # 20. Flujo CB (Izq)
        self.input_flow_cb = LabeledParameterWidget(
            label_text="Flujo", 
            tag="balanceChamberSetTiming", # Opcional, referencia
            value="0.0", 
            units="ml/min", # mostrar unidades 
            is_editable=True, 
            parent=self.control_area
        )
        self.input_flow_cb.request_numpad.connect(lambda tag, wid, tit: self._handle_cb_flow_input())
        grid.addWidget(self.input_flow_cb, 4, 2, 1, 2)    

        # 21. Toggle dializante (Der)
        lbl_dialysate = QLabel("B. Dial.", self.control_area)
        lbl_dialysate.setStyleSheet(label_style)
        grid.addWidget(lbl_dialysate, 4, 5, 1, 1)
        self.dialysate_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.dialysate_pump_toggle.toggled.connect(            
            lambda chk: self._handle_dual_pump_toggle("dialyserPumpStartButton", "dialyserPumpStopButton", chk, timer_id="dialysate_pump")
        )
        grid.addWidget(self.dialysate_pump_toggle, 4, 6, 1, 1)

        # 22. Salida dializante (Der)
   
        self.dialysate_output_display = LabeledParameterWidget(
            label_text="Salida", tag="dialyFlowControlOutput",
            value="0.0", units="%", is_editable=True, parent=self.control_area
        )
        self.dialysate_output_display.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.dialysate_output_display, 4, 7, 1, 2)

        # 23. Tiempo op. b dializante (Der)

        self.dialysate_time_display = LabeledTimeInput(
            label_text="T. Terapia:", initial_hh_mm="00:00",
            tag_hours=None, tag_minutes=None,
            local_timer_id="dialysate_pump", numpad_title="tiempo de Operación",
            is_editable=True,
            parent=self.control_area
        )
        self.dialysate_time_display.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.dialysate_time_display, 4, 9, 1, 2)

        # 24. Tiempo rest dializante (Der)
        self.lbl_remaining_pd = LabeledTimeInput(
            label_text="Rest:",
            initial_hh_mm="00:00",
            is_editable=False,
            parent=self.control_area,
        )
        grid.addWidget(self.lbl_remaining_pd, 4, 11, 1, 2)

        self.local_timer_states["dialysate_pump"]["remaining_lbl"] = self.lbl_remaining_pd.time_display


        # ==============================================================================
        # --- FILA 5: Ciclos(25, 26) | B. Purga (27, 28) ---
        # ==============================================================================

        # 25. Set Ciclos CB (Izq)
        self.balance_cycles_set_input = LabeledParameterWidget(
            label_text="Ciclos CB", tag="balanceChamberCycleSet",
            value="0.0",numpad_title="Número de ciclos de cCB",is_editable=True,
            parent=self.control_area
        )
        self.balance_cycles_set_input.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.balance_cycles_set_input, 5, 0, 1, 2)

        # 26. Ciclos actuales (Izq)
        self.balance_cycles_actual_label = LabeledParameterWidget(
            label_text="Ciclos Act.", tag="balanceChamberCycleCount",
            value="0.0", units="",is_editable=False, parent=self.control_area
        )
        grid.addWidget(self.balance_cycles_actual_label, 5, 2, 1, 2)

        # 27. Bomba Purga (Der)
        lbl_purga = QLabel("B. Purga", self.control_area)
        lbl_purga.setStyleSheet(label_style)
        grid.addWidget(lbl_purga, 5, 5, 1, 1)

        self.purge_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.purge_pump_toggle.toggled.connect(            
            lambda chk: self._handle_dual_pump_toggle("dialyPurgePumpStartButt", "dialyPurgePumpStopButt", chk, timer_id=None)
        )
        grid.addWidget(self.purge_pump_toggle, 5, 6, 1, 1)

        # 28. Salida purga % (Der)
        self.purge_output_display = LabeledParameterWidget(
            label_text="Salida", tag="dialyDeaerControlOutput",
            value="0.0", units="%", is_editable=True, parent=self.control_area
        )
        self.purge_output_display.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.purge_output_display, 5, 7, 1, 2)

        # ==============================================================================
        # --- FILA 6: Tiempos CB (29, 30) | B. UF (31-34) ---
        # ==============================================================================

        # 29. Tiempo Op CB (Izq)
        self.balance_chamber_time_input = LabeledTimeInput(
            label_text="T. Operacion CB",
            initial_hh_mm="00:00", tag_hours=None, tag_minutes=None,
            local_timer_id="balance_chamber",numpad_title="Tiempo de operación CB",
            is_editable=True,
            parent=self.control_area
        )
        self.balance_chamber_time_input.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.balance_chamber_time_input, 6, 0, 1, 2)

        # 30. Tiempo Rest CB (Izq)
        self.lbl_remaining_cb = LabeledTimeInput(
            label_text="Rest:",
            initial_hh_mm="00:00",
            is_editable=False,
            parent=self.control_area,
        )
        grid.addWidget(self.lbl_remaining_cb, 6, 2, 1, 2)
        self.local_timer_states["balance_chamber"]["remaining_lbl"] = self.lbl_remaining_cb.time_display

        # 31. Bomba UF (Der)
        lbl_ultrafiltado = QLabel("B. UF", self.control_area)
        lbl_ultrafiltado.setStyleSheet(label_style)
        grid.addWidget(lbl_ultrafiltado, 6, 5, 1, 1)
        
        self.uf_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.uf_pump_toggle.toggled.connect(
            lambda chk: self._handle_dual_pump_toggle("dialyUltraFPumpStartButt", "dialyUltraFPumpStoptButt", chk, timer_id="uf_pump")
        )
        grid.addWidget(self.uf_pump_toggle, 6, 6, 1, 1)

        # 32. Salida UF (Der)        
        self.lbl_input_indUF = LabeledParameterWidget(
            label_text="Flujo", tag="ultraFilterPumpSpeed",
            value="0.0", units="L/h",
            numpad_title="Flujo UF",is_editable=True,
            parent=self.control_area
        )
        # self.lbl_input_indUF.request_numpad.connect(self._handle_uf_flow_input) 
        self.lbl_input_indUF.request_numpad.connect(lambda tag, wid, tit: self._handle_uf_flow_input())
        grid.addWidget(self.lbl_input_indUF, 6, 7, 1, 2)

        # 33. Tiempo Op B UF (Der) 
        self.uf_time_display = LabeledTimeInput(
            label_text="T. Operación:",initial_hh_mm="00:00",
            tag_hours=None, tag_minutes=None,
            local_timer_id="uf_pump", numpad_title="T. Operación B. UF",
            is_editable=True, parent=self.control_area
        )
        self.uf_time_display.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.uf_time_display, 6, 9, 1, 2)

        # 34. Tiempo Rest B UF (Der)
        self.lbl_remaining_puf = LabeledTimeInput(
            label_text="Rest:", initial_hh_mm="00:00",
            tag_hours=None, tag_minutes= None,
            local_timer_id="uf_pump", is_editable=False,
            parent=self.control_area
        )
        grid.addWidget(self.lbl_remaining_puf, 6, 11, 1, 2)

        self.local_timer_states["uf_pump"]["remaining_lbl"] = self.lbl_remaining_puf.time_display


        # ==============================================================================
        # SEPARADOR HORIZONTAL
        # ==============================================================================
        linea2 = QFrame(); linea2.setFrameShape(QFrame.HLine); linea2.setStyleSheet("color: #ccc;")
        grid.addWidget(linea2, 7, 0, 1, 13)


        # ==============================================================================
        # --- FILA 8: B. Na+ (35, 36) | B. Acido Citrico (39, 40) ---
        # ==============================================================================
        
        # 35. Toggle NA (Izq)
        lbl_bicarbonate = QLabel("B. Na+", self.control_area)
        lbl_bicarbonate.setStyleSheet(label_style)
        grid.addWidget(lbl_bicarbonate, 8, 0, 1, 1)

        self.bicarbonate_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.bicarbonate_pump_toggle.toggled.connect(
            lambda chk: self._handle_dual_pump_toggle("dialyBicarbonPumpStartButt", "dialyBicarbonPumpStopButt", chk, timer_id=None)
        )
        grid.addWidget(self.bicarbonate_pump_toggle, 8, 1, 1, 1)

        # 36. Salida NA (Izq)
        self.bicarbonate_output_display = LabeledParameterWidget(
            label_text="Salida", tag="bicarbonatePumpSpeed",
            value="0.0", units="%", is_editable=False, parent=self.control_area
        )
        grid.addWidget(self.bicarbonate_output_display, 8, 2, 1, 2)

        # 39. Toggle Acido Citrico (Der)
        lbl_acidocitrico = QLabel("B. A. Citrico", self.control_area)
        lbl_acidocitrico.setStyleSheet(label_style)
        grid.addWidget(lbl_acidocitrico, 8, 5, 1, 1)

        self.citric_acid_pump_toggle = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.citric_acid_pump_toggle.toggled.connect(
            lambda chk: self._handle_dual_pump_toggle("dialyCitricAcPumpStartButt", "dialyCitricAcPumpStopButt", chk, timer_id=None)
        )
        grid.addWidget(self.citric_acid_pump_toggle, 8, 6, 1, 1)

        # 40. Salida Acido Citrico (Der) citricAcidPumpSpeed
        self.citric_acid_output_display = LabeledParameterWidget(
            label_text="Salida", tag="citricAcidPumpSpeed",
            value="0.0", units="%", is_editable=False, parent=self.control_area
        )
        grid.addWidget(self.citric_acid_output_display, 8, 7, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(3, 70)
        grid.setColumnMinimumWidth(13, 110)

        

        # --- VALVULAS ---
        valves_container = QWidget()
        # valves_container.setFixedSize(1300, 180)
        valves_layout = QHBoxLayout(valves_container)
        valves_layout.setContentsMargins(0, 0, 0, 0)
        valves_layout.setSpacing(5)

        mode_frame = QFrame()
        mode_frame.setFixedSize(100, 180)
        mode_frame.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
        mode_layout = QVBoxLayout(mode_frame)

        mode_label = QLabel("Modo de<br>Op.")
        mode_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
        mode_label.setAlignment(Qt.AlignCenter)

        self.operation_mode_toggle = ToggleSwitch(width=70, height=30, active_color="#facc15", parent=mode_frame)
        self.operation_mode_toggle.toggled.connect(
            lambda checked: self._write_boolean_command("dialyCircuitElementsOpSel", checked)
        )

        mode_layout.addStretch()
        mode_layout.addWidget(mode_label)
        mode_layout.addSpacing(10)
        mode_layout.addWidget(self.operation_mode_toggle, 0, Qt.AlignCenter)
        mode_layout.addStretch()

        valves_layout.addWidget(mode_frame)

        valves_grid_widget = QWidget()
        valves_grid = QGridLayout(valves_grid_widget)
        valves_grid.setContentsMargins(0, 0, 0, 0)
        valves_grid.setSpacing(10)

        valve_info = [
            (0, 0, "SV_24", "E. Filtro UF", "dialyInputFilterCutButt"),
            (0, 1, "SV_25", "S. Filtro UF", "dialyOutputFilterCutButt"),
            (1, 0, "SV_26", "Bypass UF",    "dialyBypassFilterButt"),
            (1, 1, "SV_27", "E. Agua",      "dialyWaterInletValveButt"),
            (2, 0, "SV_39", "Recirculación","dialyRecirculatValveButt"),
            (2, 1, "SV_43", "Venteo CS Aire","dialyAirVentSepChambButt"),
            (3, 0, "SV_50", "C. Caliente",  "dialyHotChambValveButt"),
            (3, 1, "SV_30", "Drenaje",      "dialyWaterDrainValveButt"),
        ]
        self.valve_cards = {}

        for r, c, code, desc, tag in valve_info:
            card = ValveCard(code, desc, parent=valves_grid_widget)
            self.valve_cards[tag] = card
            valves_grid.addWidget(card, r, c)
            card.toggle.toggled.connect(lambda checked, t=tag: self._write_boolean_command(t, checked))
        valves_layout.addWidget(valves_grid_widget)
        
        #======================================================================================
        #                           --- LEDS ---
        #======================================================================================
        indicators_area = QWidget()
        # indicators_area.setFixedSize(180, 780)
        indicators_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        indicators_area.setStyleSheet("background: #fcfcfc;")
        led_grid = QGridLayout(indicators_area)
        led_grid.setSpacing(10)
        led_grid.setContentsMargins(10, 10, 10, 10)

        led_info = [
            (0, 0, 0, 1,"B. Sangre",     "bloodPumpStartButton"),
            (1, 0, 1, 1,"B. Dialante", "dialyserPumpStartButton"),
            (2, 0, 2, 1,"B.Heparina.",   "heparinePumpsStartButton"),
            (3, 0, 3, 1,"B. UF",     "dialyUltraFPumpStartButt"),
            (4, 0, 4, 1,"Purga de aire", "dialyPurgePumpStartButt"),
            (5, 0, 5, 1,"C.Balance",     "dialiserBalChambStrButt"),
            (0, 2, 0, 3,"Aire en sangre",     "airBubbleInBloodDetected"),
            (1, 2, 1, 3,"C.Deaereación", "dialyDeaerChamLevSwitch"),
            (2, 2, 2, 3,"Fin de ciclos", "dialyBalanceChambCycleEnd"),
            (3, 2, 3, 3,"Protec. R.","watterTankHeaterProtect"),
            (4, 2, 4, 3,"Sangre en Dial.",  "bloodInDialyCircDetected"),
            (5, 2, 5, 3,"Nivel Tanque","dialyTankHiLevelSwitch"),        ]

        self.led_indicators = []
        for rowl,coll, rled,cled, name, tag in led_info:
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;") 
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            led_grid.addWidget(lbl, rowl, coll)

            led = LED(indicators_area)
            led.setFixedSize(45, 45)
            led_grid.addWidget(led, rled, cled, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.led_indicators.append((led, tag))

        layout.addWidget(self.control_area, 0, 0, 2, 2) 
        layout.addWidget(valves_container, 0, 2, 1, 1) 
        layout.addWidget(indicators_area, 1, 2, 1, 1)

    # ────────────────────────────────────────────────
    # Métodos Lógicos (Sin cambios, solo corrección en llamadas auxiliares)
    # ────────────────────────────────────────────────

    def update_values(self, new_values: dict):
        self.values = new_values
        current_ms = QDateTime.currentMSecsSinceEpoch()

        for led, tag in self.led_indicators:
            value = self.values.get(tag, 0.0)
            if tag == "dialyTankHiLevelSwitch":
                led.set_state("off" if value > 0 else "in")
            else:
                led.set_state("on" if value > 0 else "off")

        for tag, card in self.valve_cards.items():
            value = self.values.get(tag, 0.0)
            new_state = value > 0
            if card.toggle.is_checked() != new_state:
                card.toggle.blockSignals(True)
                card.toggle.setChecked(new_state)
                card.toggle.blockSignals(False)

        if "balanceChamberSetTiming" not in self.write_hold_off or \
           current_ms >= self.write_hold_off["balanceChamberSetTiming"]:
            cycles = self.values.get("balanceChamberSetTiming", 0.0)
            try:
                flow_ml_min = convertir_ciclos_a_flujo(cycles)
                self._update_input_display(self.input_flow_cb, flow_ml_min, precision=1) 
            except Exception as e:
                logger.error(f"Error converting CB flow: {e}")
                self._update_input_display(self.input_flow_cb, 0.0, precision=1)

        if "ultraFilterPumpSpeed" not in self.write_hold_off or \
           current_ms >= self.write_hold_off["ultraFilterPumpSpeed"]:
            uf_ml_min = self.values.get("ultraFilterPumpSpeed", 0.0)
            try:
                uf_lh = convertir_ml_min_a_litros_h(uf_ml_min)
                self._update_input_display(self.lbl_input_indUF, uf_lh, precision=1) 
            except Exception as e:
                logger.error(f"Error converting UF flow: {e}")
                self._update_input_display(self.lbl_input_indUF, 0.0, precision=1)

        self._update_input_display(self.blood_flow_input, self.values.get("bloodFlowControlSetPoint", 0.0))
        self._update_input_display(self.input_heparin, self.values.get("heparineTherapyDosage", 0.0))
        self._update_input_display(self.input_bolus, self.values.get("heparineBolusQuantity", 0.0))
        self._update_input_display(self.input_syringe_size, self.values.get("heparineSyrinjeScaleSize", 0.0))
        self._update_input_display(self.dialysate_output_display, self.values.get("dialyFlowControlOutput", 0.0))
        self._update_input_display(self.purge_output_display, self.values.get("dialyDeaerControlOutput", 0.0))
        self._update_input_display(self.balance_cycles_set_input, self.values.get("balanceChamberCycleSet", 0))
        self._update_label_display(self.balance_cycles_actual_label, self.values.get("balanceChamberCycleCount", 0))

        self._update_label_display(self.blood_speed_display, self.values.get("bloodSpeedVariableData", 0.0))
        self._update_label_display(self.bicarbonate_output_display, self.values.get("bicarbonatePumpSpeed", 0.0))
        self._update_label_display(self.citric_acid_output_display, self.values.get("citricAcidPumpSpeed", 0.0))
        self._update_label_display(self.heparin_current_dosage_display, self.values.get("heparineCurrentDosage", 0.0))

        self._update_time_display(self.blood_pump_time_input, None, None, "blood_pump")
        self._update_time_display(self.heparin_time_input, "heparineTherapyHours", "heparineTherapyMinutes", "heparin_pump")
        self._update_time_display(self.dialysate_time_display, None, None, "dialysate_pump")
        self._update_time_display(self.uf_time_display, None, None, "uf_pump")
        self._update_time_display(self.balance_chamber_time_input, None, None, "balance_chamber")

        self._sync_toggle(self.blood_pump_toggle, self.values.get("bloodPumpStartButton", 0.0))
        self._sync_toggle(self.heparin_pump_toggle, self.values.get("heparinePumpsStartButton", 0.0))
        self._sync_toggle(self.dialysate_pump_toggle, self.values.get("dialyserPumpStartButton", 0.0))
        self._sync_toggle(self.citric_acid_pump_toggle, self.values.get("dialyCitricAcPumpStartButt", 0.0))
        self._sync_toggle(self.bicarbonate_pump_toggle, self.values.get("dialyBicarbonPumpStartButt", 0.0))
        self._sync_toggle(self.purge_pump_toggle, self.values.get("dialyPurgePumpStartButt", 0.0))
        self._sync_toggle(self.uf_pump_toggle, self.values.get("dialyUltraFPumpStartButt", 0.0))
        self._sync_toggle(self.operation_mode_toggle, self.values.get("dialyCircuitElementsOpSel", 0.0))
        self._sync_toggle(self.balance_chamber_toggle, self.values.get("dialiserBalChambStrButt", 0.0))

        logger.debug("Manual mode values updated from machine")

    def _sync_toggle(self, toggle_widget, value: float):
        new_state = value > 0
        if toggle_widget.is_checked() != new_state:
            toggle_widget.blockSignals(True)
            toggle_widget.setChecked(new_state)
            toggle_widget.blockSignals(False)

    def _update_time_display(self, time_widget, tag_hours: str, tag_minutes: str, timer_id: str):
        if not tag_hours and not tag_minutes:
            return
        
        current_ms = QDateTime.currentMSecsSinceEpoch()
        hold_hours = self.write_hold_off.get(tag_hours, 0) if tag_hours else 0
        hold_minutes = self.write_hold_off.get(tag_minutes, 0) if tag_minutes else 0

        if current_ms < hold_hours or current_ms < hold_minutes:
            return

        hours = int(self.values.get(tag_hours, 0)) if tag_hours else 0
        minutes = int(self.values.get(tag_minutes, 0)) if tag_minutes else 0

        if isinstance(time_widget, LabeledTimeInput):
            time_widget.set_time_value(hours, minutes)
        elif hasattr(time_widget, 'setText'):
            if not time_widget.hasFocus():
                time_widget.setText(f"{hours:02d}:{minutes:02d}")

        if timer_id and timer_id in self.local_timer_states:
            if not self.local_timer_states[timer_id]["active"]:
                total_ms = (hours * 3600 + minutes * 60) * 1000
                self.local_timer_states[timer_id]["duration_ms"] = total_ms

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

    def _handle_dual_pump_toggle(self, start_tag: str, stop_tag: str, enabled: bool, timer_id: str = None):
        """Handle dual start/stop pump control (REQ-SW-005)."""
        if enabled:
            logger.info(f"Starting pump: {start_tag}")
            self._write_boolean_command(start_tag, True)
            self._write_boolean_command(stop_tag, False)

            if timer_id and timer_id in self.local_timer_states:
                state = self.local_timer_states[timer_id]
                total_ms = state["duration_ms"]
                if total_ms > 0:
                    state["active"] = True
                    state["start_ms"] = QDateTime.currentMSecsSinceEpoch()
                    timer = getattr(self, f"{timer_id}_timer", None)
                    if timer: timer.start(total_ms)
                    logger.info(f"Timer '{timer_id}' started for {total_ms} ms")
        else:
            logger.info(f"Stopping pump: {start_tag}")
            self._write_boolean_command(stop_tag, True)
            self._write_boolean_command(start_tag, False)

            if timer_id and timer_id in self.local_timer_states:
                state = self.local_timer_states[timer_id]
                if state["active"]:
                    state["active"] = False
                    timer = getattr(self, f"{timer_id}_timer", None)
                    if timer and timer.isActive():
                        timer.stop()
                    if state["elapsed_lbl"]:
                        state["elapsed_lbl"].setText("00:00")
                    if state["remaining_lbl"]:
                        h = state["duration_ms"] // 3600000
                        m = (state["duration_ms"] % 3600000) // 60000
                        state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")
                    logger.info(f"Timer '{timer_id}' stopped")

    def _write_boolean_command(self, tag: str, state: bool):
        logger.info(f"Command: {tag} → {state}")
        address = -1
        for group_key, vars_group in VARIABLES.items():
            if isinstance(vars_group, dict):
                for var_id, info in vars_group.items():
                    if info.get("tag") == tag:
                        address = var_id
                        break
            if address != -1:
                break

        if address != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                if self.parent_window.serial_comm.is_connected:
                    self.parent_window.serial_comm.write_boolean(address, state)
                    logger.info(f"Boolean command sent: Addr {address} = {state}")
                else:
                    logger.warning("Serial not connected")
                    QMessageBox.warning(self, "Error", "Serial no conectado")
            else:
                logger.warning("Serial communication not available")
        else:
            logger.error(f"Tag '{tag}' not found in VARIABLES map")

    def _write_setpoint(self, tag: str, value: float):
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
                    else:
                        logger.warning("Serial communication not available")
                else:
                    logger.warning(f"Tag '{tag}' is read-only")
            else:
                logger.error(f"Tag '{tag}' not found in variables map")

        except Exception as e:
            logger.error(f"Critical error writing setpoint '{tag}': {e}")

    def open_numpad(self, tag: str, input_widget, title: str = "Ingrese valor"):
        if isinstance(input_widget, LabeledParameterWidget):
            current_text = str(input_widget.get_value())
        elif hasattr(input_widget, 'text'):
            current_text = input_widget.text()
        else:
            current_text = "0.0"

        dialog = NumpadDialog(self, initial_value=current_text, title=title)

        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                if isinstance(input_widget, LabeledParameterWidget):
                    input_widget.set_value(new_value)
                elif hasattr(input_widget, 'setText'):
                    input_widget.setText(str(new_value))
                
                self._write_setpoint(tag, new_value)
                self.write_hold_off[tag] = QDateTime.currentMSecsSinceEpoch() + 3000

    def open_time_numpad(self, time_widget, tag_hours: str = None, tag_minutes: str = None,
                         timer_id: str = None, title: str = "Config. Tiempo"):
        if isinstance(time_widget, LabeledTimeInput):
            current_text = time_widget.get_time_value()
        elif hasattr(time_widget, 'text'):
            current_text = time_widget.text()
        else:
            current_text = "00:00"

        dialog = TimeNumpadDialog(self, initial_hh_mm=current_text, title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                if isinstance(time_widget, LabeledTimeInput):
                    time_widget.set_time_value(hours, minutes)
                elif hasattr(time_widget, 'setText'):
                    time_widget.setText(f"{hours:02d}:{minutes:02d}")

                total_ms = (hours * 3600 + minutes * 60) * 1000
                current_ms = QDateTime.currentMSecsSinceEpoch()
                hold_duration = 3000

                if tag_hours and tag_minutes:
                    self._write_setpoint(tag_hours, float(hours))
                    self.write_hold_off[tag_hours] = current_ms + hold_duration
                    self._write_setpoint(tag_minutes, float(minutes))
                    self.write_hold_off[tag_minutes] = current_ms + hold_duration

                if timer_id and timer_id in self.local_timer_states:
                    state = self.local_timer_states[timer_id]
                    state["duration_ms"] = total_ms
                    if state["elapsed_lbl"]:
                        state["elapsed_lbl"].setText("00:00")
                    if state["remaining_lbl"]:
                        state["remaining_lbl"].setText(f"{hours:02d}:{minutes:02d}")

    def _stop_pump_generic(self, timer_key: str, stop_tag: str, start_tag: str, toggle_widget):
        logger.warning(f"Timeout: {timer_key} - Automatic pump stop")
        timer = getattr(self, f"{timer_key}_timer")
        if timer:
            timer.stop()

        self.local_timer_states[timer_key]["active"] = False
        self._write_boolean_command(stop_tag, True)
        self._write_boolean_command(start_tag, False)

        toggle_widget.blockSignals(True)
        toggle_widget.setChecked(False)
        toggle_widget.blockSignals(False)

        state = self.local_timer_states[timer_key]
        if state["elapsed_lbl"]:
            state["elapsed_lbl"].setText("00:00")
        if state["remaining_lbl"]:
            h = state["duration_ms"] // 3600000
            m = (state["duration_ms"] % 3600000) // 60000
            state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

    def _stop_blood_pump_on_timeout(self):
        self._stop_pump_generic("blood_pump", "bloodPumpStopButton", "bloodPumpStartButton", self.blood_pump_toggle)

    def _stop_dialysate_pump_on_timeout(self):
        self._stop_pump_generic("dialysate_pump", "dialyserPumpStopButton", "dialyserPumpStartButton", self.dialysate_pump_toggle)

    def _stop_uf_pump_on_timeout(self):
        self._stop_pump_generic("uf_pump", "dialyUltraFPumpStoptButt", "dialyUltraFPumpStartButt", self.uf_pump_toggle)

    def _stop_heparin_pump_on_timeout(self):
        self._stop_pump_generic("heparin_pump", "heparinePumpsStopButton", "heparinePumpsStartButton", self.heparin_pump_toggle)

    def _stop_balance_chamber_on_timeout(self):
        self._stop_pump_generic("balance_chamber", "dialiserBalChambStpButt", "dialiserBalChambStrButt", self.balance_chamber_toggle)

    def _update_local_time_displays(self):
        current_ms = QDateTime.currentMSecsSinceEpoch()
        for timer_id, state in self.local_timer_states.items():
            if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
                elapsed_ms = current_ms - state["start_ms"]
                # remaining_ms = max(0, state["duration_ms"] - elapsed_ms)
                remaining_ms = state["duration_ms"] - elapsed_ms

                if remaining_ms <= 0:
                    remaining_ms = 0
                    # elapsed_ms = state["duration_ms"]

                if state["elapsed_lbl"]:
                    state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
                if state["remaining_lbl"]:
                    state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))
            
            else:
                if state["elapsed_lbl"] and state["elapsed_lbl"].text() != "00:00":
                    state["elapsed_lbl"].setText("00:00")

                if state["remaining_lbl"]:
                    state["remaining_lbl"].setText(self._format_ms_to_hh_mm(state["duration_ms"]))
                    # h = state["duration_ms"] // 3600000
                    # m = (state["duration_ms"] % 3600000) // 60000
                    # state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")
    
    def _format_ms_to_label(self, label_widget, ms):
        total_seconds = max(0, int(ms//1000))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        label_widget.setText(f"{hours:02d}:{minutes:02d}")

    def _format_ms_to_hh_mm(self, ms: int) -> str:
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def _handle_cb_flow_input(self):
        """Handle balance chamber flow input (ml/min → cycles)."""        
        try:
            current_text = self.input_flow_cb.get_value()
            # ANTES: current_text = self.input_flow_cb.text()
        except AttributeError:
            current_text = "0.0"

        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo CB (ml/min)")
        if dialog.exec():
            new_value = dialog.get_value()
            if hasattr(self.input_flow_cb, 'setText'):
                self.input_flow_cb.setText(str(new_value))
            
            try:
                cycles = convertir_flujo_a_ciclos(new_value)
                self._write_setpoint("balanceChamberSetTiming", cycles)
                self.write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error converting CB flow: {e}")

    def _handle_uf_flow_input(self):
        """Handle UF flow input (L/h → ml/min)."""
        # CORREGIDO: Usar text() 
        try:
            current_text = self.lbl_input_indUF.text()
        except AttributeError:
            current_text = "0.0"
            
        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo UF (L/h)")
        if dialog.exec():
            new_value = dialog.get_value()
            if hasattr(self.lbl_input_indUF, 'setText'):
                self.lbl_input_indUF.setText(str(new_value))

            try:
                ml_min = convertir_litros_h_a_ml_min(new_value)
                self._write_setpoint("ultraFilterPumpSpeed", ml_min)
                self.write_hold_off["ultraFilterPumpSpeed"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error converting UF flow: {e}")
















# gui/service/manual_mode_screem.py
# CIATEQ A.C. - Módulo de control manual para máquina de hemodiálisis
# Software Version: 1.0.0
# Safety Class: Class C (IEC 62304:2006 + A1:2015)
# Risk References: 
#   - RM-HEMO-SW-005: Control de bombas y tiempos de operación
#   - RM-HEMO-SW-010: Prevención de sobreescritura de setpoints (hold-off)
#   - RM-HEMO-SW-012: Paro automático por timeout de seguridad
# Last Reviewed: 2026-02-XX
# Criticality: High (controla actuadores críticos y seguridad del paciente)

# import logging
# from PySide6.QtWidgets import QWidget, QFrame,QVBoxLayout, QGridLayout,QHBoxLayout, QLabel, QPushButton, QMessageBox,QSizePolicy
# from PySide6.QtCore import Qt, QTimer, QDateTime
# from PySide6.QtGui import QColor

# from gui.components.LED import LED
# from gui.components.ToggleSwitch import ToggleSwitch
# from gui.components.numpad_modal import NumpadDialog
# from gui.components.time_numpad_modal import TimeNumpadDialog
# from gui.components.ui_components import ClickableLineEdit, LabeledParameterWidget, LabeledTimeInput

# from core.variables_map import VARIABLES
# from logic.calculos import (
#     convertir_flujo_a_ciclos,
#     convertir_ciclos_a_flujo,
#     convertir_litros_h_a_ml_min,
#     convertir_ml_min_a_litros_h
# )

# logger = logging.getLogger(__name__)

# class ValveCard(QFrame):
#     """Componente para control de válvulas (REQ-SW-005)."""
#     def __init__(self, codigo, descripcion, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: #1e293b;
#                 border-radius: 8px;
#                 border: 1px solid #334155;
#             }
#         """)
#         self.setFixedHeight(80)
#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(10)

#         lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>", self)
#         lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
#         lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

#         self.toggle = ToggleSwitch(width=70, height=30, parent=self)
#         layout.addWidget(lbl_info)
#         layout.addStretch()
#         layout.addWidget(self.toggle)


# class mManualScr(QWidget):
#     """
#     Pantalla de control manual de actuadores, bombas y válvulas.
#     REQ-SW-005: Permite operación manual segura de componentes críticos.
#     REQ-SW-010: Implementa hold-off de 3 segundos en escritura de setpoints.
#     REQ-SW-012: Paro automático por timeout de seguridad en bombas.
#     REQ-SW-020: Actualización consistente de valores.
#     """

#     def __init__(self, parent=None, valores_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.valores = valores_dict or {}

#         self._write_hold_off = {}

#         self._setup_timers()
#         self.setup_ui()
#         logger.info("Módulo de control manual inicializado (v1.0.0)")

#     def _setup_timers(self):
#         """Inicializa timers de operación y actualización visual.
#         REQ-SW-012: Timeout de seguridad para evitar operación indefinida."""
#         self.timer_op_pb = QTimer(self)
#         self.timer_op_pb.timeout.connect(self._stop_blood_pump_on_timeout)

#         self.timer_op_pd = QTimer(self)
#         self.timer_op_pd.timeout.connect(self._stop_dialysate_pump_on_timeout)

#         self.timer_op_puf = QTimer(self)
#         self.timer_op_puf.timeout.connect(self._stop_uf_pump_on_timeout)

#         self.timer_op_ph = QTimer(self)
#         self.timer_op_ph.timeout.connect(self._stop_heparin_pump_on_timeout)

#         self.timer_op_cb = QTimer(self)
#         self.timer_op_cb.timeout.connect(self._stop_balance_chamber_on_timeout)

#         self._display_update_timer = QTimer(self)
#         self._display_update_timer.timeout.connect(self._update_local_time_displays)
#         self._display_update_timer.start(500)

#         self._local_timers_state = {
#             "op_pb": {"duration_ms": 0, "start_ms": 0, "active": False,"elapsed_lbl": None, "remaining_lbl": None},
#             "op_pd": {"duration_ms": 0, "start_ms": 0, "active": False,"elapsed_lbl": None, "remaining_lbl": None},
#             "op_puf": {"duration_ms": 0, "start_ms": 0, "active": False,"elapsed_lbl": None, "remaining_lbl": None},
#             "op_ph": {"duration_ms": 0, "start_ms": 0, "active": False,
#                       "elapsed_lbl": None, "remaining_lbl": None},
#             "op_cb": {"duration_ms": 0, "start_ms": 0, "active": False,
#                       "elapsed_lbl": None, "remaining_lbl": None},
#         }

#     def setup_ui(self):
#         """Construye interfaz según SRS-UI-001 (layout táctil optimizado)."""
#         layout = QGridLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(15)

#         style_lbl = "color: #000000; font-size: 18px; font-weight: bold;"
#         style_lbl_indicator = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
#         style_btn = """
#             QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
#             QPushButton:pressed { background: #1e40af; }
#         """
#         style_unit = "color: #94a3b8; font-size: 16px;"
#         style_input = """
#             background: #FFFFE5; color: #000000; font-size: 18px; font-weight: bold;
#             border: 2px solid #000000; border-radius: 5px; padding: 4px;
#         """
#         self.control_area = QWidget(self)
#         self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         grid = QGridLayout(self.control_area)
#         grid.setSpacing(15)
#         grid.setContentsMargins(5, 5, 5, 5)
  


#         # FILA 0: Bomba de Sangre (REQ-SW-005)
#         lbl_sangre = QLabel("B. Sangre", self.control_area)
#         lbl_sangre.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_sangre, 0, 0, 2, 2)

#         self.toggle_sangre = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_sangre.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk, timer_id="op_pb")
#         )
#         grid.addWidget(self.toggle_sangre, 0, 2, 2, 1)

#         btn_rev = QPushButton("REV", self.control_area)
#         btn_rev.setFixedSize(80, 70)
#         btn_rev.setStyleSheet(style_btn)
#         btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
#         btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
#         grid.addWidget(btn_rev, 0, 3, 2, 2)

#         btn_fwd = QPushButton("FWD", self.control_area)
#         btn_fwd.setFixedSize(80, 70)
#         btn_fwd.setStyleSheet(style_btn)
#         btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
#         btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))
#         grid.addWidget(btn_fwd, 0, 5, 2, 2)

#         self.input_flujo_sangre = LabeledParameterWidget(
#             label_text="Flujo", tag="bloodFlowControlSetPoint",
#             value="0", units="ml/min", numpad_title="Flujo de Sangre",
#             is_editable=True, parent=self.control_area
#         )
#         self.input_flujo_sangre.request_numpad.connect(self.open_numpad)
#         grid.addWidget(self.input_flujo_sangre, 0, 7, 2, 2)

#         self.lbl_velocidad_val = LabeledParameterWidget(
#             label_text="Vel", tag="bloodSpeedVariableData",
#             value="0.0", units="rpm", is_editable=False, parent=self.control_area
#         )
#         grid.addWidget(self.lbl_velocidad_val, 0, 9, 2, 2)

#         self.input_t_BloodPump = LabeledTimeInput(
#             label_text="Tiempo Op.:", initial_hh_mm="00:00",
#             tag_hours=None, tag_minutes=None, local_timer_id="op_pb",
#             numpad_title="Tiempo de operación de bomba de sangre",
#             parent=self.control_area
#         )
#         self.input_t_BloodPump.request_time_numpad.connect(self.open_time_numpad)
#         grid.addWidget(self.input_t_BloodPump, 0, 11, 2, 2)

#         lbl_remaining_pb_title = QLabel("Rest.:", self.control_area)
#         lbl_remaining_pb_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_pb_title, 0, 13, 2, 1, alignment=Qt.AlignRight)

#         self.lbl_remaining_pb = QLabel("00:00", self.control_area)
#         self.lbl_remaining_pb.setStyleSheet(style_lbl_indicator)
#         self.lbl_remaining_pb.setFixedSize(100, 35)
#         self.lbl_remaining_pb.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_pb, 0, 14, 2, 2, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_pb"]["remaining_lbl"] = self.lbl_remaining_pb

#         # FILA 2: Bomba de Heparina (REQ-SW-005)
#         lbl_bHeparina = QLabel("B. Hep.", self.control_area)
#         lbl_bHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_bHeparina, 2, 0, 2, 2)

#         self.toggle_heparina = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_heparina.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton", chk, timer_id="op_ph")
#         )
#         grid.addWidget(self.toggle_heparina, 2, 2, 2, 1)

#         btn_homeHep = QPushButton("HOME", self.control_area)
#         btn_homeHep.setFixedSize(80, 70)
#         btn_homeHep.setStyleSheet(style_btn)
#         btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
#         btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False))
#         grid.addWidget(btn_homeHep, 2, 3, 2, 2)

#         btn_rev_hep = QPushButton("REV", self.control_area)
#         btn_rev_hep.setFixedSize(80, 70)
#         btn_rev_hep.setStyleSheet(style_btn)
#         btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton", True))
#         btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))
#         grid.addWidget(btn_rev_hep, 2, 5, 2, 2)

#         btn_pause_hep = QPushButton("PAUSE", self.control_area)
#         btn_pause_hep.setFixedSize(80, 70)
#         btn_pause_hep.setStyleSheet(style_btn)
#         btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume", True))
#         btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))
#         grid.addWidget(btn_pause_hep, 2, 7, 2, 2)

#         btn_fwd_hep = QPushButton("FWD", self.control_area)
#         btn_fwd_hep.setFixedSize(80, 70)
#         btn_fwd_hep.setStyleSheet(style_btn)
#         btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton", True))
#         btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))
#         grid.addWidget(btn_fwd_hep, 2, 9, 2, 2)

#         self.indHeparinCurrentDosage = LabeledParameterWidget(
#             label_text="Heparina", tag="heparineCurrentDosage",
#             value="0.0", units="ml", is_editable=False, parent=self.control_area
#         )
#         grid.addWidget(self.indHeparinCurrentDosage, 2, 11, 2, 2)

#         self.input_dosis_hep = LabeledParameterWidget(
#             label_text="Dosis Hep.", tag="heparineTherapyDosage",
#             value="0.0", units="ml/h", numpad_title="Dosis Heparina",
#             is_editable=True, parent=self.control_area
#         )
#         self.input_dosis_hep.request_numpad.connect(self.open_numpad)
#         grid.addWidget(self.input_dosis_hep, 2, 13, 2, 3)

#         self.input_dosis_bolo = LabeledParameterWidget(
#             label_text="Bolo", tag="heparineBolusQuantity",
#             value="0.0", units="ml", numpad_title="Dosis Bolo",
#             is_editable=True, parent=self.control_area
#         )
#         self.input_dosis_bolo.request_numpad.connect(self.open_numpad)
#         grid.addWidget(self.input_dosis_bolo, 4, 0, 2, 3)

#         self.input_size_syringe = LabeledParameterWidget(
#             label_text="Jeringa", tag="heparineSyrinjeScaleSize",
#             value="0.0", units="mm/ml", numpad_title="Tamaño de jeringa",
#             is_editable=True, parent=self.control_area
#         )
#         self.input_size_syringe.request_numpad.connect(self.open_numpad)
#         grid.addWidget(self.input_size_syringe, 4, 3, 2, 2)

#         self.input_t_therapy = LabeledTimeInput(
#             label_text="T. Terapia:", initial_hh_mm="00:00",
#             tag_hours="heparineTherapyHours", tag_minutes="heparineTherapyMinutes",
#             local_timer_id="op_ph", numpad_title="Tiempo de terapia",
#             parent=self.control_area
#         )
#         self.input_t_therapy.request_time_numpad.connect(self.open_time_numpad)
#         grid.addWidget(self.input_t_therapy, 4, 5, 2, 2)

#         lbl_remaining_ph_title = QLabel("Rest.:", self.control_area)
#         lbl_remaining_ph_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_ph_title, 4, 7, 2, 1, alignment=Qt.AlignLeft)

#         self.lbl_remaining_ph = QLabel("00:00", self.control_area)
#         self.lbl_remaining_ph.setStyleSheet(style_lbl_indicator)
#         self.lbl_remaining_ph.setFixedSize(100, 35)
#         self.lbl_remaining_ph.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_ph, 4, 8, 2, 1, alignment=Qt.AlignCenter)

#         self._local_timers_state["op_ph"]["remaining_lbl"] = self.lbl_remaining_ph

#         # FILA 4: Bicarbonato (B. Na+)
#         lbl_bicarbonato = QLabel("B. Na+", self.control_area)
#         lbl_bicarbonato.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_bicarbonato, 4, 9, 2, 2)

#         self.toggle_Na = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_Na.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt", "dialyBicarbonPumpStopButt", chk, timer_id=None)
#         )
#         grid.addWidget(self.toggle_Na, 4, 11, 2, 2)

#         self.lbl_indBNa = LabeledParameterWidget(
#             label_text="Salida", tag="bicarbonatePumpSpeed",
#             value="0.0", units="%", is_editable=False, parent=self.control_area
#         )
#         grid.addWidget(self.lbl_indBNa, 4, 13, 2, 3)

#         # FILA 6: Bomba de Dializante
#         lbl_dializante = QLabel("B. Dializante", self.control_area)
#         lbl_dializante.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dializante, 6, 0, 1, 2)

#         self.toggle_dializante = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_dializante.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton", "dialyserPumpStopButton", chk, timer_id="op_pd")
#         )
#         grid.addWidget(self.toggle_dializante, 6, 2, 1, 1)

#         self.lbl_io_dial = ClickableLineEdit("0.0")
#         self.lbl_io_dial.setStyleSheet(style_input)
#         self.lbl_io_dial.setAlignment(Qt.AlignCenter)
#         self.lbl_io_dial.setReadOnly(True)
#         self.lbl_io_dial.clicked.connect(
#             lambda: self.open_numpad("dialyFlowControlOutput", self.lbl_io_dial, "Salida Dializante (%)")
#         )
#         grid.addWidget(self.lbl_io_dial, 6, 3, 1, 2)

#         lbl_e_tOpBD = QLabel("Tiempo Op.:", self.control_area)
#         lbl_e_tOpBD.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_e_tOpBD, 6, 7, 1, 2)

#         self.lbl_tiempo_OpBD = ClickableLineEdit("00:00")
#         self.lbl_tiempo_OpBD.setStyleSheet(style_input)
#         self.lbl_tiempo_OpBD.setFixedSize(100, 35)
#         self.lbl_tiempo_OpBD.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_OpBD.setReadOnly(True)
#         self.lbl_tiempo_OpBD.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.lbl_tiempo_OpBD, None, None, "op_pd", "Tiempo Op. Dializante"
#             )
#         )
#         grid.addWidget(self.lbl_tiempo_OpBD, 6, 9, 1, 2)

#         lbl_remaining_pd_title = QLabel("Rest.:", self.control_area)
#         lbl_remaining_pd_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_pd_title, 6, 11, 1, 2, alignment=Qt.AlignRight)

#         self.lbl_remaining_pd = QLabel("00:00", self.control_area)
#         self.lbl_remaining_pd.setStyleSheet(style_lbl_indicator)
#         self.lbl_remaining_pd.setFixedSize(100, 35)
#         self.lbl_remaining_pd.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_pd, 6, 13, 1, 3, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_pd"]["remaining_lbl"] = self.lbl_remaining_pd

#         # FILA 7: Cámara de Balance
#         lbl_cb = QLabel("C. Balance", self.control_area)
#         lbl_cb.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_cb, 7, 0, 1, 2)

#         self.toggle_cb = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_cb.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialiserBalChambStrButt", "dialiserBalChambStpButt", chk, timer_id="op_cb")
#         )
#         grid.addWidget(self.toggle_cb, 7, 2, 1, 1)

#         lbl_flow = QLabel("Flujo", self.control_area)
#         lbl_flow.setStyleSheet(style_lbl)
#         lbl_flow.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         grid.addWidget(lbl_flow, 7, 3)

#         self.input_flow_cb = ClickableLineEdit("0.0")
#         self.input_flow_cb.setStyleSheet(style_input)
#         self.input_flow_cb.setAlignment(Qt.AlignCenter)
#         self.input_flow_cb.setReadOnly(True)
#         self.input_flow_cb.clicked.connect(self._handle_flow_cb_input)
#         grid.addWidget(self.input_flow_cb, 7, 4)

#         lbl_cycles_set = QLabel("Ciclos cb", self.control_area)
#         lbl_cycles_set.setStyleSheet(style_lbl)
#         lbl_cycles_set.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         grid.addWidget(lbl_cycles_set, 7, 5)

#         self.input_cycles_chamber = ClickableLineEdit("0")
#         self.input_cycles_chamber.setStyleSheet(style_input)
#         self.input_cycles_chamber.setAlignment(Qt.AlignCenter)
#         self.input_cycles_chamber.setReadOnly(True)
#         self.input_cycles_chamber.clicked.connect(
#             lambda: self.open_numpad("balanceChamberCycleSet", self.input_cycles_chamber, "Ciclos CB (Set)")
#         )
#         grid.addWidget(self.input_cycles_chamber, 7, 6)

#         lbl_cycles_act = QLabel("Act.:", self.control_area)
#         lbl_cycles_act.setStyleSheet(style_lbl)
#         lbl_cycles_act.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         grid.addWidget(lbl_cycles_act, 7, 7)

#         self.ind_cycles_chamber = QLabel("0")
#         self.ind_cycles_chamber.setStyleSheet(style_lbl_indicator)
#         self.ind_cycles_chamber.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.ind_cycles_chamber, 7, 8)

#         lbl_t_op_cb = QLabel("T. Op.:", self.control_area)
#         lbl_t_op_cb.setStyleSheet(style_lbl)
#         lbl_t_op_cb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         grid.addWidget(lbl_t_op_cb, 7, 9)

#         self.input_t_BalanceChamber = ClickableLineEdit("00:00")
#         self.input_t_BalanceChamber.setStyleSheet(style_input)
#         self.input_t_BalanceChamber.setAlignment(Qt.AlignCenter)
#         self.input_t_BalanceChamber.setReadOnly(True)
#         self.input_t_BalanceChamber.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_BalanceChamber, None, None, "op_cb", "Tiempo Op. CB"
#             )
#         )
#         grid.addWidget(self.input_t_BalanceChamber, 7, 10)

#         lbl_remaining_cb_title = QLabel("Rest.:", self.control_area)
#         lbl_remaining_cb_title.setStyleSheet(style_lbl)
#         lbl_remaining_cb_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         grid.addWidget(lbl_remaining_cb_title, 7, 11)

#         self.lbl_remaining_cb = QLabel("00:00", self.control_area)
#         self.lbl_remaining_cb.setStyleSheet(style_lbl_indicator)
#         self.lbl_remaining_cb.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_cb, 7, 12, 1, 2)

#         self._local_timers_state["op_cb"]["remaining_lbl"] = self.lbl_remaining_cb

#         # FILA 8: Bomba de Purga y Ácido Cítrico
#         lbl_purga = QLabel("B. Purga", self.control_area)
#         lbl_purga.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_purga, 8, 0, 1, 2)

#         self.toggle_purga = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_purga.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt", "dialyPurgePumpStopButt", chk, timer_id=None)
#         )
#         grid.addWidget(self.toggle_purga, 8, 2, 1, 1)

#         self.lbl_indPurga = ClickableLineEdit("0.0")
#         self.lbl_indPurga.setStyleSheet(style_input)
#         self.lbl_indPurga.setAlignment(Qt.AlignCenter)
#         self.lbl_indPurga.setReadOnly(True)
#         self.lbl_indPurga.clicked.connect(
#             lambda: self.open_numpad("dialyDeaerControlOutput", self.lbl_indPurga, "Salida b. Purga (%)")
#         )
#         grid.addWidget(self.lbl_indPurga, 8, 3, 1, 2)

#         lbl_unit_indPurga = QLabel("%", self.control_area)
#         lbl_unit_indPurga.setStyleSheet(style_unit)
#         grid.addWidget(lbl_unit_indPurga, 8, 5, 1, 2)

#         lbl_acidocitrico = QLabel("B. A. Citrico", self.control_area)
#         lbl_acidocitrico.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_acidocitrico, 8, 9, 1, 2)

#         self.toggle_acidocitrico = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_acidocitrico.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt", "dialyCitricAcPumpStopButt", chk, timer_id=None)
#         )
#         grid.addWidget(self.toggle_acidocitrico, 8, 11, 1, 2)

#         lbl_output_BAC = QLabel("Salida (%)", self.control_area)
#         lbl_output_BAC.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_output_BAC, 8, 13, 1, 1)

#         self.lbl_indBAC = QLabel("0.0", self.control_area)
#         self.lbl_indBAC.setStyleSheet(style_lbl_indicator)
#         self.lbl_indBAC.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_indBAC, 8, 14, 1, 2)

#         # FILA 9: Bomba de Ultra Filtrado
#         lbl_ultrafiltado = QLabel("B. UF", self.control_area)
#         lbl_ultrafiltado.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_ultrafiltado, 9, 0, 1, 2)

#         self.toggle_uf = ToggleSwitch(width=70, height=35, parent=self.control_area)
#         self.toggle_uf.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt", "dialyUltraFPumpStoptButt", chk, timer_id="op_puf")
#         )
#         grid.addWidget(self.toggle_uf, 9, 2, 1, 1)

#         lbl_uf = QLabel("Flujo (L/h)", self.control_area)
#         lbl_uf.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_uf, 9, 3, 1, 2)

#         self.lbl_input_indUF = ClickableLineEdit("0.0")
#         self.lbl_input_indUF.setStyleSheet(style_input)
#         self.lbl_input_indUF.setAlignment(Qt.AlignCenter)
#         self.lbl_input_indUF.setReadOnly(True)
#         self.lbl_input_indUF.clicked.connect(self._handle_flow_uf_input)
#         grid.addWidget(self.lbl_input_indUF, 9, 5, 1, 2)

#         lbl_e_tOpBUF = QLabel("Tiempo Op.:", self.control_area)
#         lbl_e_tOpBUF.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_e_tOpBUF, 9, 7, 1, 2)

#         self.lbl_tiempo_opBUF = ClickableLineEdit("00:00")
#         self.lbl_tiempo_opBUF.setStyleSheet(style_input)
#         self.lbl_tiempo_opBUF.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_opBUF.setReadOnly(True)
#         self.lbl_tiempo_opBUF.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.lbl_tiempo_opBUF, None, None, "op_puf", "Tiempo Op. Ultra Filtrado"
#             )
#         )
#         grid.addWidget(self.lbl_tiempo_opBUF, 9, 9, 1, 2)

#         lbl_remaining_puf_title = QLabel("Rest.:", self.control_area)
#         lbl_remaining_puf_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_puf_title, 9, 11, 1, 2, alignment=Qt.AlignRight)

#         self.lbl_remaining_puf = QLabel("00:00", self.control_area)
#         self.lbl_remaining_puf.setStyleSheet(style_lbl_indicator)
#         self.lbl_remaining_puf.setFixedSize(100, 35)
#         self.lbl_remaining_puf.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_puf, 9, 13, 1, 3, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_puf"]["remaining_lbl"] = self.lbl_remaining_puf

#         # Ajustes finales del grid
#         grid.setColumnStretch(0, 1)
#         grid.setColumnMinimumWidth(3, 70)
#         grid.setColumnMinimumWidth(13, 110)

#         layout.addWidget(self.control_area, 0, 0)

#         # Área de LEDs (solo lectura, REQ-SW-015)
#         self.ind_area = QWidget(self)
#         self.ind_area.setFixedSize(180, 726)
#         grid_ind_area = QGridLayout(self.ind_area)
#         grid_ind_area.setSpacing(10)
#         grid_ind_area.setContentsMargins(10, 10, 10, 10)

#         led_nombres = [
#             "B. Sangre", "B. Dializante", "B. Heparina", "B. UltraF",
#             "Purga de aire", "C.Balance", "A. sangre", "C.Deaereación",
#             "Fin de ciclos", "Protec. Resist.", "S.Dializante", "Nivel de tanque"
#         ]
#         led_tags = [
#             "bloodPumpStartButton", "dialyserPumpStartButton", "heparinePumpsStartButton",
#             "dialyUltraFPumpStartButt", "dialyPurgePumpStartButt", "dialiserBalChambStrButt",
#             "airBubbleInBloodDetected", "dialyDeaerChamLevSwitch", "dialyBalanceChambCycleEnd",
#             "watterTankHeaterProtect", "bloodInDialyCircDetected", "dialyTankHiLevelSwitch"
#         ]
#         self.leds = []
#         for i, nombre in enumerate(led_nombres):
#             lbl = QLabel(nombre, self.ind_area)
#             lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
#             lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#             grid_ind_area.addWidget(lbl, i, 0)
#             led = LED(self.ind_area)
#             led.setFixedSize(45, 45)
#             grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
#             self.leds.append((led, led_tags[i]))

#         layout.addWidget(self.ind_area, 0, 1, 2, 1)

#         # Área de válvulas (REQ-SW-005)
#         self.ctrl_valvulas = QWidget(self)
#         self.ctrl_valvulas.setFixedSize(1300, 180)
#         layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas)
#         layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
#         layout_ctrl_valvulas.setSpacing(5)

#         self.container_mop = QFrame(self.ctrl_valvulas)
#         self.container_mop.setFixedSize(100, 180)
#         self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
#         layout_mop = QVBoxLayout(self.container_mop)

#         lbl_modo = QLabel("Modo de \n Op.", self.container_mop)
#         lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
#         lbl_modo.setAlignment(Qt.AlignCenter)

#         self.toggle_modo = ToggleSwitch(width=70, height=30, active_color="#facc15", parent=self.container_mop)
#         self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))
#         layout_mop.addStretch()
#         layout_mop.addWidget(lbl_modo)
#         layout_mop.setSpacing(10)
#         layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
#         layout_mop.addStretch()

#         layout_ctrl_valvulas.addWidget(self.container_mop)

#         self.container_val = QWidget(self.ctrl_valvulas)
#         grid_valvulas_area = QGridLayout(self.container_val)
#         grid_valvulas_area.setContentsMargins(0, 0, 0, 0)
#         grid_valvulas_area.setSpacing(10)

#         valvulas_tag = [
#             (0, 0, "dialyInputFilterCutButt", "SV_24 E. Filtro UF"),
#             (0, 1, "dialyOutputFilterCutButt", "SV_25 S. Filtro UF"),
#             (0, 2, "dialyBypassFilterButt", "SV_26 Bypass UF"),
#             (0, 3, "dialyWaterInletValveButt", "SV_27 E. Agua"),
#             (1, 0, "dialyRecirculatValveButt", "SV_39 Recirculación"),
#             (1, 1, "dialyAirVentSepChambButt", "SV_43 Venteo CS Aire"),
#             (1, 2, "dialyHotChambValveButt", "SV_50 C. Caliente"),
#             (1, 3, "dialyWaterDrainValveButt", "SV_30 Drenaje"),
#         ]
#         self.valvulas_map = {}
#         for r, c, tag, desc in valvulas_tag:
#             parts = desc.split(" ", 1)
#             codigo = parts[0]
#             texto = parts[1] if len(parts) > 1 else ""
#             card = ValveCard(codigo, texto, parent=self.container_val)
#             self.valvulas_map[tag] = card
#             grid_valvulas_area.addWidget(card, r, c)
#             card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

#         layout_ctrl_valvulas.addWidget(self.container_val)
#         layout.addWidget(self.ctrl_valvulas, 10, 0, 1, 1)

#     # ────────────────────────────────────────────────
#     # Métodos críticos con trazabilidad regulatoria
#     # ────────────────────────────────────────────────

#     def actualizar_valores(self, nuevos_valores):
#         """
#         REQ-SW-020: Actualización segura de valores.
#         Riesgo RM-HEMO-SW-020: Datos inconsistentes por sobreescritura rápida.
#         Mitigación: Hold-off por tag y actualización condicional.
#         """
#         self.valores = nuevos_valores
#         current_time = QDateTime.currentMSecsSinceEpoch()

#         # LEDs
#         for led, tag in self.leds:
#             valor = self.valores.get(tag, 0.0)
#             if tag == "dialyTankHiLevelSwitch":
#                 led.set_state("off" if valor > 0 else 'in')
#             else:
#                 led.set_state('on' if valor > 0 else 'off')

#         # Válvulas
#         for tag, card in self.valvulas_map.items():
#             val = self.valores.get(tag, 0.0)
#             nuevo_estado = val > 0
#             if card.toggle.is_checked() != nuevo_estado:
#                 card.toggle.blockSignals(True)
#                 card.toggle.setChecked(nuevo_estado)
#                 card.toggle.blockSignals(False)

#         # Cámara Balance: ciclos → ml/min
#         if "balanceChamberSetTiming" not in self._write_hold_off or \
#            current_time >= self._write_hold_off["balanceChamberSetTiming"]:
#             cycle_val = self.valores.get("balanceChamberSetTiming", 0.0)
#             try:
#                 calc_flow = convertir_ciclos_a_flujo(cycle_val)
#                 self.update_input_val(self.input_flow_cb, "balanceChamberSetTiming",
#                                      precision=1, display_value=calc_flow)
#             except Exception as e:
#                 logger.error(f"Error conversión flujo CB: {e}")
#                 self.update_input_val(self.input_flow_cb, "balanceChamberSetTiming",
#                                      precision=1, display_value=0.0)

#         # Ultra Filtración: ml/min → L/h
#         if "ultraFilterPumpSpeed" not in self._write_hold_off or \
#            current_time >= self._write_hold_off["ultraFilterPumpSpeed"]:
#             uf_ml_min = self.valores.get("ultraFilterPumpSpeed", 0.0)
#             try:
#                 calc_lh = convertir_ml_min_a_litros_h(uf_ml_min)
#                 self.update_input_val(self.lbl_input_indUF, "ultraFilterPumpSpeed",
#                                      precision=1, display_value=calc_lh)
#             except Exception as e:
#                 logger.error(f"Error conversión flujo UF: {e}")
#                 self.update_input_val(self.lbl_input_indUF, "ultraFilterPumpSpeed",
#                                      precision=1, display_value=0.0)

#         # Campos numéricos
#         self.update_input_val(self.input_flujo_sangre, "bloodFlowControlSetPoint")
#         self.update_input_val(self.input_dosis_hep, "heparineTherapyDosage")
#         self.update_input_val(self.input_dosis_bolo, "heparineBolusQuantity")
#         self.update_input_val(self.input_size_syringe, "heparineSyrinjeScaleSize")
#         self.update_input_val(self.lbl_io_dial, "dialyFlowControlOutput")
#         self.update_input_val(self.lbl_indPurga, "dialyDeaerControlOutput")
#         self.update_input_val(self.input_cycles_chamber, "balanceChamberCycleSet")
#         self.update_label_val(self.ind_cycles_chamber, "balanceChamberCycleCount")

#         # Indicadores
#         self.update_label_val(self.lbl_velocidad_val, "bloodSpeedVariableData")
#         self.update_label_val(self.lbl_indBNa, "bicarbonatePumpSpeed")
#         self.update_label_val(self.lbl_indBAC, "citricAcidPumpSpeed")
#         self.update_label_val(self.indHeparinCurrentDosage, "heparineCurrentDosage")

#         # Tiempos
#         self.update_time_input_val(self.input_t_BloodPump, None, None, "op_pb")
#         self.update_time_input_val(self.input_t_therapy, "heparineTherapyHours", "heparineTherapyMinutes", "op_ph")
#         self.update_time_input_val(self.lbl_tiempo_OpBD, None, None, "op_pd")
#         self.update_time_input_val(self.lbl_tiempo_opBUF, None, None, "op_puf")
#         self.update_time_input_val(self.input_t_BalanceChamber, None, None, "op_cb")

#         # Toggles
#         self._actualizar_toggle(self.toggle_sangre, self.valores.get("bloodPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_heparina, self.valores.get("heparinePumpsStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_dializante, self.valores.get("dialyserPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_acidocitrico, self.valores.get("dialyCitricAcPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_Na, self.valores.get("dialyBicarbonPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_purga, self.valores.get("dialyPurgePumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_uf, self.valores.get("dialyUltraFPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_modo, self.valores.get("dialyCircuitElementsOpSel", 0.0))
#         self._actualizar_toggle(self.toggle_cb, self.valores.get("dialiserBalChambStrButt", 0.0))

#         logger.debug("Valores actualizados desde máquina")

#     def _actualizar_toggle(self, toggle, valor):
#         """Función auxiliar para actualizar toggle sin disparar señal."""
#         estado_nuevo = valor > 0
#         if toggle.is_checked() != estado_nuevo:
#             toggle.blockSignals(True)
#             toggle.setChecked(estado_nuevo)
#             toggle.blockSignals(False)

#     def update_time_input_val(self, time_input_widget, tag_hours, tag_minutes, local_timer_id):
#         """Actualiza campos de tiempo respetando hold-off."""
#         current_time = QDateTime.currentMSecsSinceEpoch()

#         hold_off_h = self._write_hold_off.get(tag_hours, 0) if tag_hours else 0
#         hold_off_m = self._write_hold_off.get(tag_minutes, 0) if tag_minutes else 0

#         if current_time < hold_off_h or current_time < hold_off_m:
#             return

#         if tag_hours is None and tag_minutes is None:
#             return

#         hours = int(self.valores.get(tag_hours, 0)) if tag_hours else 0
#         minutes = int(self.valores.get(tag_minutes, 0)) if tag_minutes else 0

#         if isinstance(time_input_widget, LabeledTimeInput):
#             time_input_widget.set_time_value(hours, minutes)
#         elif hasattr(time_input_widget, 'setText'):
#             if not time_input_widget.hasFocus():
#                 time_input_widget.setText(f"{hours:02d}:{minutes:02d}")
#         else:
#             logger.error(f"Tipo de widget no soportado para tiempo: {tag_hours}/{tag_minutes}")

#         if local_timer_id and local_timer_id in self._local_timers_state:
#             total_ms = (hours * 3600 + minutes * 60) * 1000
#             self._local_timers_state[local_timer_id]["duration_ms"] = total_ms

#     def update_input_val(self, widget, tag, precision=1, display_value=None):
#         """Actualiza valor en interfaz con hold-off."""
#         current_time = QDateTime.currentMSecsSinceEpoch()
#         hold_until = self._write_hold_off.get(tag, 0)

#         if current_time < hold_until:
#             return

#         value = display_value if display_value is not None else self.valores.get(tag, 0.0)

#         if isinstance(widget, LabeledParameterWidget):
#             widget.set_value(value)
#         elif hasattr(widget, "setText"):
#             if hasattr(widget, "hasFocus") and widget.hasFocus():
#                 return
#             widget.setText(f"{value:.{precision}f}")
#         else:
#             logger.error(f"Widget no soportado para tag '{tag}'")

#     def update_label_val(self, label_widget, tag, precision=1):
#         """Actualiza indicadores de solo lectura."""
#         value = self.valores.get(tag, 0.0)
#         if isinstance(label_widget, LabeledParameterWidget):
#             label_widget.set_value(value)
#         elif hasattr(label_widget, 'setText'):
#             label_widget.setText(f"{value:.{precision}f}")
#         else:
#             logger.error(f"Widget no soportado para tag '{tag}'")

#     def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
#         """Control doble de arranque/paro de bombas (REQ-SW-005)."""
#         if activado:
#             logger.info(f"Arrancando bomba: {tag_start}")
#             self.escribir_comando(tag_start, True)
#             self.escribir_comando(tag_stop, False)

#             if timer_id and timer_id in self._local_timers_state:
#                 state = self._local_timers_state[timer_id]
#                 total_ms = state["duration_ms"]
#                 if total_ms > 0:
#                     state["active"] = True
#                     state["start_ms"] = QDateTime.currentMSecsSinceEpoch()
#                     timer_obj = getattr(self, f"timer_{timer_id}")
#                     timer_obj.start(total_ms)
#                     logger.info(f"Timer '{timer_id}' iniciado por {total_ms} ms")
#                 else:
#                     logger.warning(f"Timer '{timer_id}' sin duración configurada")
#         else:
#             logger.info(f"Deteniendo bomba: {tag_start}")
#             self.escribir_comando(tag_stop, True)
#             self.escribir_comando(tag_start, False)

#             if timer_id and timer_id in self._local_timers_state:
#                 state = self._local_timers_state[timer_id]
#                 if state["active"]:
#                     state["active"] = False
#                     timer_obj = getattr(self, f"timer_{timer_id}")
#                     if timer_obj.isActive():
#                         timer_obj.stop()
#                     if state["elapsed_lbl"]:
#                         state["elapsed_lbl"].setText("00:00")
#                     if state["remaining_lbl"]:
#                         h = state["duration_ms"] // 3600000
#                         m = (state["duration_ms"] % 3600000) // 60000
#                         state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")
#                     logger.info(f"Timer '{timer_id}' detenido")

#     def escribir_setpoint(self, tag, value=None, widget_input=None):
#         """REQ-SW-015: Escritura segura de setpoints."""
#         try:
#             if value is not None:
#                 valor = float(value)
#                 texto = str(valor)
#             elif widget_input is not None:
#                 if isinstance(widget_input, LabeledParameterWidget):
#                     texto = widget_input.get_value()
#                 elif isinstance(widget_input, LabeledTimeInput):
#                     texto = widget_input.get_time_value()
#                 elif hasattr(widget_input, 'text'):
#                     texto = widget_input.text()
#                 else:
#                     logger.error(f"Tipo de widget desconocido para '{tag}'")
#                     QMessageBox.critical(self, "Error", f"Tipo desconocido para '{tag}'")
#                     return

#                 texto = texto.replace(',', '.')
#                 if not texto:
#                     current_value = self.valores.get(tag, 0.0)
#                     if widget_input and hasattr(widget_input, 'set_value'):
#                         widget_input.set_value(current_value)
#                     return
#                 valor = float(texto)
#             else:
#                 logger.error(f"Sin valor ni widget para '{tag}'")
#                 return

#             logger.info(f"Intentando escribir setpoint {tag} = {valor}")

#             target_group = target_id = -1
#             found = False
#             for group_key, vars_group in VARIABLES.items():
#                 if isinstance(vars_group, dict):
#                     for var_id, info in vars_group.items():
#                         if info.get("tag") == tag:
#                             target_group = group_key
#                             target_id = var_id
#                             found = True
#                             break
#                 if found: break

#             if found and target_group != -1 and target_id != -1:
#                 if VARIABLES[target_group][target_id].get("rw", False):
#                     if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:
#                         if self.parent_window.serial.conectado:
#                             self.parent_window.serial.escribir_double(target_group, target_id, valor)
#                             logger.info(f"Setpoint escrito: {tag} = {valor}")
#                         else:
#                             logger.warning("Serial no conectado")
#                             QMessageBox.warning(self, "Comunicación", "Serial no conectado")
#                     else:
#                         logger.warning("Serial no disponible")
#                 else:
#                     logger.warning(f"Tag '{tag}' es de solo lectura")
#                     QMessageBox.warning(self, "Error", f"'{tag}' es de solo lectura")
#             else:
#                 logger.error(f"Tag '{tag}' no encontrado en mapa de variables")
#                 QMessageBox.critical(self, "Error", f"Tag '{tag}' no encontrado")

#             if widget_input and hasattr(widget_input, 'clearFocus'):
#                 widget_input.clearFocus()

#         except ValueError:
#             display_text = str(value) if value is not None else texto
#             logger.error(f"Valor inválido para {tag}: {display_text}")
#             QMessageBox.warning(self, "Error", f"Valor inválido para {tag}")
#         except Exception as e:
#             logger.error(f"Error crítico al escribir {tag}: {e}")
#             QMessageBox.critical(self, "Error Crítico", f"Error al escribir {tag}: {e}")

#     def escribir_comando(self, tag, estado):
#         """Envía comando booleano."""
#         logger.info(f"Comando: {tag} → {estado}")
#         direccion = -1
#         if 0x01 in VARIABLES:
#             for id_var, info in VARIABLES[0x01].items():
#                 if info.get("tag") == tag:
#                     direccion = id_var
#                     break

#         if direccion != -1:
#             if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:
#                 try:
#                     if self.parent_window.serial.conectado:
#                         self.parent_window.serial.escribir_booleano(direccion, estado)
#                         logger.info(f"Comando enviado: Addr {direccion} = {estado}")
#                     else:
#                         logger.warning("Serial no conectado")
#                         QMessageBox.warning(self, "Error", "Serial no conectado")
#                 except Exception as e:
#                     logger.error(f"Fallo al enviar comando {tag}: {e}")
#                     QMessageBox.warning(self, "Error", "Fallo en comunicación serial")
#             else:
#                 logger.warning("Serial no disponible")
#         else:
#             logger.error(f"Tag '{tag}' no encontrado")
#             QMessageBox.critical(self, "Error", f"Tag '{tag}' no encontrado")

#     def open_numpad(self, tag, widget_input, title="Ingrese valor"):
#         """Abre numpad para valores decimales (REQ-SW-010)."""
#         if isinstance(widget_input, LabeledParameterWidget):
#             act_value = widget_input.get_value()
#         else:
#             act_value = widget_input.text()

#         dialog = NumpadDialog(self, initial_value=act_value, title=title)
#         if dialog.exec():
#             new_value = dialog.get_value()
#             if isinstance(widget_input, LabeledParameterWidget):
#                 widget_input.set_value(new_value)
#             else:
#                 widget_input.setText(str(new_value))
#             self.escribir_setpoint(tag, widget_input=widget_input)

#             current_ts = QDateTime.currentMSecsSinceEpoch()
#             self._write_hold_off[tag] = current_ts + 3000

#     def open_time_numpad(self, time_input_widget, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
#         """Abre numpad para tiempo HH:MM (REQ-SW-018)."""
#         if isinstance(time_input_widget, LabeledTimeInput):
#             texto_actual = time_input_widget.get_time_value()
#         else:
#             texto_actual = time_input_widget.text()

#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)
#         if dialog.exec():
#             h, m = dialog.get_hours_minutes()

#             if isinstance(time_input_widget, LabeledTimeInput):
#                 time_input_widget.set_time_value(h, m)
#             else:
#                 time_input_widget.setText(f"{h:02d}:{m:02d}")

#             total_ms = (h * 3600 + m * 60) * 1000
#             current_ts = QDateTime.currentMSecsSinceEpoch()
#             hold_duration = 3000

#             if tag_hours and tag_minutes:
#                 logger.info(f"Enviando horas ({h}) a {tag_hours}")
#                 self.escribir_setpoint(tag_hours, value=h)
#                 self._write_hold_off[tag_hours] = current_ts + hold_duration

#                 logger.info(f"Enviando minutos ({m}) a {tag_minutes}")
#                 self.escribir_setpoint(tag_minutes, value=m)
#                 self._write_hold_off[tag_minutes] = current_ts + hold_duration

#             if local_timer_id and local_timer_id in self._local_timers_state:
#                 state = self._local_timers_state[local_timer_id]
#                 state["duration_ms"] = total_ms
#                 if state["elapsed_lbl"]:
#                     state["elapsed_lbl"].setText("00:00")
#                 if state["remaining_lbl"]:
#                     state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")
#                 logger.info(f"Timer {local_timer_id} configurado: {h:02d}:{m:02d}")

#     def _stop_pump_generic(self, timer_key, stop_tag, start_tag, toggle_widget):
#         """Paro genérico de bomba por timeout (REQ-SW-012)."""
#         logger.warning(f"Timeout: {timer_key} - Paro automático")
#         timer_obj = getattr(self, f"timer_{timer_key}", None)
#         if timer_obj:
#             timer_obj.stop()

#         self._local_timers_state[timer_key]["active"] = False
#         self.escribir_comando(stop_tag, True)
#         self.escribir_comando(start_tag, False)

#         toggle_widget.blockSignals(True)
#         toggle_widget.setChecked(False)
#         toggle_widget.blockSignals(False)

#         state = self._local_timers_state[timer_key]
#         if state["elapsed_lbl"]:
#             state["elapsed_lbl"].setText("00:00")
#         if state["remaining_lbl"]:
#             h = state["duration_ms"] // 3600000
#             m = (state["duration_ms"] % 3600000) // 60000
#             state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

#     def _stop_blood_pump_on_timeout(self):
#         self._stop_pump_generic("op_pb", "bloodPumpStopButton", "bloodPumpStartButton", self.toggle_sangre)

#     def _stop_dialysate_pump_on_timeout(self):
#         self._stop_pump_generic("op_pd", "dialyserPumpStopButton", "dialyserPumpStartButton", self.toggle_dializante)

#     def _stop_uf_pump_on_timeout(self):
#         self._stop_pump_generic("op_puf", "dialyUltraFPumpStoptButt", "dialyUltraFPumpStartButt", self.toggle_uf)

#     def _stop_heparin_pump_on_timeout(self):
#         self._stop_pump_generic("op_ph", "heparinePumpsStopButton", "heparinePumpsStartButton", self.toggle_heparina)

#     def _stop_balance_chamber_on_timeout(self):
#         self._stop_pump_generic("op_cb", "dialiserBalChambStpButt", "dialiserBalChambStrButt", self.toggle_cb)

#     def _format_ms_to_hh_mm(self, ms):
#         total_seconds = max(0, ms // 1000)
#         hours = total_seconds // 3600
#         minutes = (total_seconds % 3600) // 60
#         return f"{hours:02d}:{minutes:02d}"

#     def _update_local_time_displays(self):
#         """Actualiza contadores de tiempo local."""
#         current_ms = QDateTime.currentMSecsSinceEpoch()
#         for timer_id, state in self._local_timers_state.items():
#             if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
#                 elapsed_ms = current_ms - state["start_ms"]
#                 remaining_ms = max(0, state["duration_ms"] - elapsed_ms)
#                 if remaining_ms <= 0:
#                     remaining_ms = 0
#                     elapsed_ms = state["duration_ms"]

#                 if state["elapsed_lbl"]:
#                     state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
#                 if state["remaining_lbl"]:
#                     state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))
#             elif not state["active"]:
#                 if state["elapsed_lbl"] and state["elapsed_lbl"].text() != "00:00":
#                     state["elapsed_lbl"].setText("00:00")
#                 if state["remaining_lbl"]:
#                     h = state["duration_ms"] // 3600000
#                     m = (state["duration_ms"] % 3600000) // 60000
#                     state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

#     def _handle_flow_cb_input(self):
#         """Input flujo Cámara Balance (ml/min → ciclos)."""
#         current_text = self.input_flow_cb.text()
#         dialog = NumpadDialog(self, initial_value=current_text, title="Flujo CB (ml/min)")
#         if dialog.exec():
#             new_value = dialog.get_value()
#             self.input_flow_cb.setText(str(new_value))
#             try:
#                 ciclos = convertir_flujo_a_ciclos(new_value)
#                 self.escribir_setpoint("balanceChamberSetTiming", value=ciclos)
#                 self._write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
#             except Exception as e:
#                 logger.error(f"Error flujo CB: {e}")

#     def _handle_flow_uf_input(self):
#         """Input flujo Ultra Filtración (L/h → ml/min)."""
#         current_text = self.lbl_input_indUF.text()
#         dialog = NumpadDialog(self, initial_value=current_text, title="Flujo UF (L/h)")
#         if dialog.exec():
#             new_value = dialog.get_value()
#             self.lbl_input_indUF.setText(str(new_value))
#             try:
#                 ml_min = convertir_litros_h_a_ml_min(new_value)
#                 self.escribir_setpoint("ultraFilterPumpSpeed", value=ml_min)
#                 self._write_hold_off["ultraFilterPumpSpeed"] = QDateTime.currentMSecsSinceEpoch() + 3000
#             except Exception as e:
#                 logger.error(f"Error flujo UF: {e}")

#     def crear_input_inline(self, label_text, tag, val_inicial, unit_text, is_editable, grid_layout, row, col_start, callback=None):
#         """Crea par Label + Input inline."""
#         style_input = """
#             background: #FFFFE5; color: #000000; font-size: 18px; font-weight: bold;
#             border: 2px solid #000000; border-radius: 5px; padding: 4px;
#         """
#         lbl = QLabel(label_text, self.control_area)
#         lbl.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;")
#         lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

#         if is_editable:
#             inp = ClickableLineEdit(str(val_inicial))
#             inp.setStyleSheet(style_input)
#             inp.setReadOnly(True)
#             if callback:
#                 inp.clicked.connect(callback)
#             else:
#                 inp.clicked.connect(lambda: self.open_numpad(tag, inp, label_text))
#         else:
#             inp = QLabel(str(val_inicial))
#             inp.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px; background: transparent;")
#             inp.setAlignment(Qt.AlignCenter)

#         inp.setFixedSize(90, 35)

#         grid_layout.addWidget(lbl, row, col_start, 1, 2)
#         grid_layout.addWidget(inp, row, col_start + 2, 1, 2)

#         if unit_text:
#             lbl_unit = QLabel(unit_text)
#             lbl_unit.setStyleSheet("color: #94a3b8; font-size: 16px;")
#             grid_layout.addWidget(lbl_unit, row, col_start + 4)

#         return inp



