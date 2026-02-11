# # gui/service/mManualScr.py
# # Ejecución del autotest de la máquina y visualización de resultados.
# # Control manual de los elementos de actuadores, bombas, válvulas



# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QDateTime
# from PySide6.QtGui import QColor, QDoubleValidator, QFont

# from gui.components.numpad_modal import NumpadDialog
# from gui.components.time_numpad_modal import TimeNumpadDialog
# from gui.components.ui_components import ClickableLineEdit
# from gui.components.ui_components import LabeledTimeInput

# try:
#     from logic.calculos import convertir_flujo_a_ciclos # convierte el flujo deseado a ciclos de cámara de balance
#     from logic.calculos import convertir_ciclos_a_flujo # convierte ciclos a flujo para lectura y/o actualizacion label
#     from logic.calculos import convertir_litros_h_a_ml_min
#     from logic.calculos import convertir_ml_min_a_litros_h
# except ImportError:
#     pass

# try:
#     from core.variables_map import VARIABLES, ANALOG_MAP
# except ImportError:
#     VARIABLES = {0x01: {}, 0x02: {}} # Mock vacío


# try:
#     from gui.components.LED import LED
#     from gui.components.ToggleSwitch import ToggleSwitch
# except ImportError:
#     class LED(QWidget):
#         def __init__(self): super().__init__(); self.state = 'off'
#         def set_state(self, s): self.state = s
#     class ToggleSwitch(QCheckBox):
#         def __init__(self, width=60, height=30, active_color=None): super().__init__()



# class TempInput:
#     def __init__(self, valor):
#         self.valor = valor
#     def text(self):
#         return str(self.valor)
#     def clearFocus(self):
#         pass 
#     def setText(self, t):
#         pass


# class ValveCard(QFrame):
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

#         lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>")
#         lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
#         lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

#         self.toggle = ToggleSwitch(width=60, height=30)

#         layout.addWidget(lbl_info)
#         layout.addStretch()
#         layout.addWidget(self.toggle)

     


# class LabeledParameterWidget(QWidget):
#     """
#     Custom widget for Hemodialysis HMI parameters.
#     Combines a description label, a value display/input, and unit tracking.
#     """
    
#     # Signal emitted when the user wants to edit the value
#     request_numpad = Signal(str, object, str) # tag, widget_reference, title

#     def __init__(self, label_text: str, tag: str, value="0.0", units: str = "", 
#                  numpad_title: str = "", is_editable: bool = True):
#         super().__init__()
        
#         # Standard height for touch targets
#         self.setFixedHeight(90)
        
#         # Main layout container
#         self.control_frame = QFrame()
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(0, 0, 0, 0)
#         self.main_layout.addWidget(self.control_frame)

#         # Inner layout
#         self.frame_layout = QVBoxLayout(self.control_frame)
#         self.frame_layout.setContentsMargins(5, 5, 5, 5)
#         self.frame_layout.setSpacing(2) # Tight spacing between label and value

#         # 1. Create the Header Label (Text + Units)
#         header_text = f"{label_text} ({units})" if units else label_text
#         self.lbl_header = QLabel(header_text)
#         self.lbl_header.setAlignment(Qt.AlignCenter)
#         # Style hint: Avoid hardcoding styles inside python if possible, use QSS file.
#         # But for this example, we keep it here for clarity.
#         self.lbl_header.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 18px;")
        
#         # 2. Create the Input/Display Widget
#         # We store it in self.value_widget to access it later in set_value
#         if is_editable:
#             self.value_widget = ClickableLineEdit(str(value))
#             self.value_widget.setReadOnly(True) # ReadOnly implies use of virtual keyboard
#             # Connect signal safely using the defined signal instead of passing self
#             self.value_widget.clicked.connect(lambda: self._handle_click(tag, numpad_title))
#         else:
#             self.value_widget = QLabel(str(value))
#             self.value_widget.setProperty("class", "read_only_value")

#         # FIX: Adjusted size. 8px was a bug. 
#         # Using a minimum width allows layout flexibility.
#         self.value_widget.setMinimumWidth(80) 
#         self.value_widget.setFixedHeight(40)
#         self.value_widget.setAlignment(Qt.AlignCenter)

#         # Add widgets to layout
#         self.frame_layout.addWidget(self.lbl_header)
#         self.frame_layout.addWidget(self.value_widget)

#     def _handle_click(self, tag, title):
#         """Internal handler to emit the signal for the main controller."""
#         self.request_numpad.emit(tag, self.value_widget, title)
    
#     def set_value(self, value):
#         """
#         Updates the displayed value securely.
#         Handles formatting for floats and strings.
#         """
#         display_text = ""
        
#         try:
#             if isinstance(value, (int, float)):
#                 # Medical standard: consistent decimal places usually required
#                 # Logic: If >= 10, 1 decimal. If < 10, 2 decimals.
#                 display_text = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
#             else:
#                 display_text = str(value)
                
#             self.value_widget.setText(display_text)
            
#         except Exception as e:
#             print(f"[ERROR] Failed to set value in LabeledParameterWidget: {e}")
#             self.value_widget.setText("ERR")

#     def get_value(self):
#         """Returns the current text value."""
#         return self.value_widget.text()



# class mManualScr(QWidget):
#     def __init__(self, parent=None, valores_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent  
#         self.valores = valores_dict if valores_dict is not None else {}

#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setMinimumSize(1024, 600)

#         # Fondo
#         self.setAutoFillBackground(True)
#         p = self.palette()
#         p.setColor(self.backgroundRole(), QColor("#fcfcfc"))
#         self.setPalette(p)

#         # if hasattr(self.control, 'clicked'):
#         #     self.control.clicked.connect(self._on_control_clicked)
#         self._write_hold_off = {} 

#         # Timers locales para cada bomba 
#         self.timer_op_pb = QTimer(self) # Bomba de sangre
#         self.timer_op_pd = QTimer(self) # Bomba de dializante 
#         self.timer_op_puf = QTimer(self) # Bomba de ultraFiltración
#         self.timer_op_ph = QTimer(self) # Bomba de heparina (terapia)
#         self.timer_op_cb = QTimer(self) # Cámara de balance

#         # Conectar señales timeout de los timers a sus slots de detención
#         self.timer_op_pb.timeout.connect(self._stop_blood_pump_on_timeout)
#         self.timer_op_pd.timeout.connect(self._stop_dialysate_pump_on_timeout)
#         self.timer_op_puf.timeout.connect(self._stop_uf_pump_on_timeout)
#         self.timer_op_ph.timeout.connect(self._stop_heparin_pump_on_timeout)
#         self.timer_op_cb.timeout.connect(self._stop_balance_chamber_on_timeout)

        
#         self._display_update_timer = QTimer(self)
#         self._display_update_timer.timeout.connect(self._update_local_time_displays)
#         self._display_update_timer.start(500) # Actualizar cada 500ms para una sensación más fluida

        
#         self._local_timers_state = {
#             "op_pb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_pd": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_puf": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_ph": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_cb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#         }
        
#         self.setup_ui()

#     def setup_ui(self):
#         layout = QGridLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(15)

#         # ==================================================================
#         #          AREA 1: CONTROL DE BOMBAS
#         # ==================================================================
       
#         self.control_area = QWidget()
#         self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

#         grid = QGridLayout(self.control_area)
#         grid.setSpacing(15)
#         grid.setContentsMargins(5, 5, 5, 5)
        

#         # Estilos comunes
#         style_lbl = "color: #000000; font-size: 18px; font-weight: bold; "
#         style_lbl_ = "color: #22d3ee; font-size: 20px; font-weight: bold;border: 2px solid #000000; border-radius: 5px; padding: 2px;"
#         style_unit = "color: #94a3b8; font-size: 16px;"
#         style_input = """
#             QLineEdit { background: #FFFFE5; color: #000000; font-size: 18px; 
#                         font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px; }
#         """
#         style_btn = """
#             QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
#             QPushButton:pressed { background: #1e40af; }
#         """        

#         # ================================================
#         # Estilos adicionales para mejorar visualmente
#         # ================================================
#         style_section_title = """
#             color: #0ea5e9; 
#             font-size: 20px; 
#             font-weight: bold; 
#             background: #e0f2fe; 
#             padding: 6px 10px; 
#             border-radius: 6px;
#         """

#         style_group_label = "color: #000000; font-size: 18px; font-weight: bold;"
#         style_input = """
#             background: #FFFFE5; 
#             color: #000000; 
#             font-size: 18px; 
#             font-weight: bold; 
#             border: 2px solid #000000; 
#             border-radius: 5px; 
#             padding: 4px;
#         """
#         style_unit = "color: #64748b; font-size: 16px; font-weight: normal;"
#         style_remaining = "color: #f59e0b; font-size: 18px; font-weight: bold; background: #fffbeb; border-radius: 4px; padding: 4px;"        
#         # ----------------------------------------------------------------------
#         # FILA 0: BOMBA DE SANGRE (B. Sangre)
#         # ----------------------------------------------------------------------
#         lbl_sangre = QLabel("B. Sangre")
#         lbl_sangre.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_sangre, 0, 0, 2, 2)

#         self.toggle_sangre = ToggleSwitch(width=60, height=35)
#         self.toggle_sangre.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk, timer_id="op_pb")
#         )
#         grid.addWidget(self.toggle_sangre, 0, 2,2,1)

#         btn_rev = QPushButton("REV")
#         btn_rev.setFixedSize(80, 70)
#         btn_rev.setStyleSheet(style_btn)
#         btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
#         btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
        
#         btn_fwd = QPushButton("FWD")
#         btn_fwd.setFixedSize(80, 70)
#         btn_fwd.setStyleSheet(style_btn)
#         btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
#         btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))

#         grid.addWidget(btn_rev, 0, 3,2,2)
#         grid.addWidget(btn_fwd, 0, 5,2,2)

#         # lbl_flujo = QLabel("Flujo:")
#         # lbl_flujo.setStyleSheet(style_lbl)
#         # grid.addWidget(lbl_flujo, 0, 7,2,1)

#         # self.input_flujo_sangre = ClickableLineEdit("0")
#         # self.input_flujo_sangre.setFixedSize(80, 35)
#         # self.input_flujo_sangre.setAlignment(Qt.AlignCenter)
#         # self.input_flujo_sangre.setStyleSheet(style_input)
#         # self.input_flujo_sangre.setReadOnly(True)        
#         # self.input_flujo_sangre.clicked.connect(
#         #     lambda: self.open_numpad("bloodFlowControlSetPoint",self.input_flujo_sangre, "Flujo de Sangre")
#         # )

#         self.input_flujo_sangre = LabeledParameterWidget( 
#             label_text="Flujo",
#             tag="bloodFlowControlSetPoint",
#             value="0",
#             units="ml/min",
#             numpad_title="Flujo de Sangre",
#             is_editable=True
#         )   
#         self.input_flujo_sangre.request_numpad.connect(self.open_numpad)

#         # self.input_flujo_sangre = LabeledInput(
#         #     label_text="Qb (ml/min)",
#         #     is_numeric=True,
#         #     default_value="0.0",
#         #     decimals=2,
#         #     min_val=0,
#         #     max_val=1000,
#         #     readonly=False
#         # )
#         # self.input_flujo_sangre.clicked.connect(
#         #     lambda: self.open_numpad("bloodFlowControlSetPoint",self.input_flujo_sangre, "Flujo de Sangre")
#         # )
#         grid.addWidget(self.input_flujo_sangre, 0, 7, 2, 2)
#         # grid.addWidget(self.input_flujo_sangre, 0, 8,2,1)

#         # lbl_u1 = QLabel("ml/min")
#         # lbl_u1.setStyleSheet(style_unit)
#         # grid.addWidget(lbl_u1, 0, 9,2,1)

#         # lbl_vel = QLabel("Vel:")
#         # lbl_vel.setStyleSheet(style_lbl)
#         # grid.addWidget(lbl_vel, 0, 10,2,1)

#         # self.lbl_velocidad_val = QLabel("0.0")
#         # self.lbl_velocidad_val.setStyleSheet(style_lbl_)
#         # self.lbl_velocidad_val.setFixedHeight(35)
#         self.lbl_velocidad_val = LabeledParameterWidget(
#             label_text="Vel",
#             tag=None, # No es editable, solo display
#             value="0.0",
#             units="rpm",
#             numpad_title="",
#             is_editable=False
#         )
#         grid.addWidget(self.lbl_velocidad_val, 0, 10,2,2)

#         # lbl_u2 = QLabel("rpm")
#         # lbl_u2.setStyleSheet(style_unit)
#         # grid.addWidget(lbl_u2, 0, 12,2,1)

#         # T. Operación de Bomba de Sangre (input_t_BloodPump)
#         # lbl_tiempo = QLabel("T.:")  
#         # lbl_tiempo.setStyleSheet(style_lbl)
#         # grid.addWidget(lbl_tiempo, 0, 13,2,1)

        
#         # self.input_t_BloodPump = ClickableLineEdit("00:00")
#         # self.input_t_BloodPump.setFixedSize(100, 35)
#         # self.input_t_BloodPump.setStyleSheet(style_input) # Usa style_input definido arriba
#         # self.input_t_BloodPump.setAlignment(Qt.AlignCenter)
#         # self.input_t_BloodPump.setReadOnly(True)
#         # self.input_t_BloodPump.clicked.connect(
#         #     lambda: self.open_time_numpad(
#         #         self.input_t_BloodPump,
#         #         tag_hours=None,        # No envía a PLC
#         #         tag_minutes=None,      # No envía a PLC
#         #         local_timer_id="op_pb", # Identificador para timer local de la bomba de sangre
#         #         title="Tiempo de operación de bomba de sangre"
#         #     )
#         # )        

#         self.input_t_BloodPump = LabeledTimeInput(
#             label_text="Tiempo Op.:", # Esto será el lbl_header del LabeledTimeInput
#             initial_hh_mm="00:00",
#             tag_hours=None,        # No envía a PLC
#             tag_minutes=None,      # No envía a PLC
#             local_timer_id="op_pb",
#             numpad_title="Tiempo de operación de bomba de sangre"
#         )
#         # Conectar la señal del LabeledTimeInput a tu manejador open_time_numpad
#         self.input_t_BloodPump.request_time_numpad.connect(self.open_time_numpad)
#         grid.addWidget(self.input_t_BloodPump, 0, 13, 2, 3) 

#         # grid.addWidget(self.input_t_BloodPump, 0, 14, 2, 2)
        
#         lbl_remaining_pb_title = QLabel("Rest.:")
#         lbl_remaining_pb_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_pb_title, 0, 16,2,1, alignment=Qt.AlignRight)

#         self.lbl_remaining_pb = QLabel("00:00")
#         self.lbl_remaining_pb.setStyleSheet(style_lbl_) # Color ámbar para restante
#         self.lbl_remaining_pb.setFixedSize(100,35)
#         grid.addWidget(self.lbl_remaining_pb, 0, 17,2,1, alignment=Qt.AlignLeft)

#         # ### ALMACENAR REFERENCIAS a las etiquetas en _local_timers_state
#         self._local_timers_state["op_pb"]["elapsed_lbl"] = None # self.lbl_elapsed_pb
#         self._local_timers_state["op_pb"]["remaining_lbl"]

#         style_section_lbl = "color: #0ea5e9; font-size: 20px; font-weight: bold; background: #e0f2fe; padding: 4px; border-radius: 4px;"
        
#         # ----------------------------------------------------------------------
#         # FILA 1: BOMBA DE HEPARINA (B. Hep.)
#         # ----------------------------------------------------------------------
#         lbl_bHeparina = QLabel("B. Hep.")
#         lbl_bHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_bHeparina, 2, 0, 1, 2)

#         self.toggle_heparina = ToggleSwitch(width=60, height=35)
#         # El timer_id "op_ph" se utiliza para la bomba de heparina, 
#         # y su duración se establece a través de "T. Terapia" (input_t_therapy)
#         self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk, timer_id="op_ph"))
#         grid.addWidget(self.toggle_heparina, 2, 2, 1, 1)


#         btn_homeHep = QPushButton("HOME")
#         btn_homeHep.setFixedSize(60, 35)
#         btn_homeHep.setStyleSheet(style_btn)
#         btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
#         btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False))
        
#         btn_rev_hep = QPushButton("REV")
#         btn_rev_hep.setFixedSize(60,35)
#         btn_rev_hep.setStyleSheet(style_btn)
#         btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton",True))
#         btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))

#         btn_pause_hep = QPushButton("PAUSE")
#         btn_pause_hep.setFixedSize(60,35)
#         btn_pause_hep.setStyleSheet(style_btn)
#         btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume",True))
#         btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))

#         btn_fwd_hep = QPushButton("FWD")
#         btn_fwd_hep.setFixedSize(60,35)
#         btn_fwd_hep.setStyleSheet(style_btn)
#         btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton",True))
#         btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))

#         grid.addWidget(btn_homeHep, 2, 3)
#         grid.addWidget(btn_rev_hep, 2, 4)
#         grid.addWidget(btn_pause_hep, 2, 5)
#         grid.addWidget(btn_fwd_hep, 2, 6)

#         lbl_indHeparina = QLabel("Heparina")
#         lbl_indHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_indHeparina, 2,7,1,2)
        
#         self.indHeparinCurrentDosage = QLabel("0.0")
#         self.indHeparinCurrentDosage.setStyleSheet(style_lbl_)
#         self.indHeparinCurrentDosage.setFixedSize(80,35)
#         self.indHeparinCurrentDosage.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.indHeparinCurrentDosage,2,9,1,2)
        
#         lbl_unit_hep = QLabel("ml")
#         lbl_unit_hep.setStyleSheet(style_unit)
#         # lbl_unit_hep.setFixedSize(80,35)
#         grid.addWidget(lbl_unit_hep,2,11)
        
#         lbl_dosis = QLabel("Dosis Hep.")
#         lbl_dosis.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dosis, 2, 12, 1, 2)

#         self.input_dosis_hep = ClickableLineEdit("0.0")
#         self.input_dosis_hep.setFixedSize(80, 35)
#         self.input_dosis_hep.setAlignment(Qt.AlignCenter)
#         self.input_dosis_hep.setStyleSheet(style_input)
#         self.input_dosis_hep.setReadOnly(True) 
#         self.input_dosis_hep.clicked.connect(
#             lambda: self.open_numpad("heparineTherapyDosage", self.input_dosis_hep, "Dosis Heparina")
#         )
#         grid.addWidget(self.input_dosis_hep, 2, 14)

#         lbl_udosis_hep = QLabel("ml/h")
#         lbl_udosis_hep.setStyleSheet(style_unit)
#         grid.addWidget(lbl_udosis_hep, 2,15 )

#         # ----------------------------------------------------------------------
#         # FILA 2: DOSIS HEPARINA (Input)
#         # ----------------------------------------------------------------------
        

#         lbl_dosis_bolo = QLabel("Bolo:")
#         lbl_dosis_bolo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dosis_bolo, 2, 5)

#         self.input_dosis_bolo = ClickableLineEdit("0.0")
#         self.input_dosis_bolo.setFixedSize(80, 35)
#         self.input_dosis_bolo.setAlignment(Qt.AlignCenter)
#         self.input_dosis_bolo.setStyleSheet(style_input)
#         self.input_dosis_bolo.setReadOnly(True)
#         self.input_dosis_bolo.clicked.connect(
#             lambda: self.open_numpad("heparineBolusQuantity", self.input_dosis_bolo, "Dosis Bolo")
#         )
#         grid.addWidget(self.input_dosis_bolo, 2, 6,1,2)

#         lbl_udosis_bol = QLabel("ml")
#         lbl_udosis_bol.setStyleSheet(style_unit)
#         grid.addWidget(lbl_udosis_bol, 2, 8)

#         lbl_size_syringe = QLabel("Jeringa")
#         lbl_size_syringe.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_size_syringe, 2, 9)

#         self.input_size_syringe = ClickableLineEdit("0.0")
#         self.input_size_syringe.setFixedSize(80,35)
#         self.input_size_syringe.setAlignment(Qt.AlignCenter)
#         self.input_size_syringe.setStyleSheet(style_input)
#         self.input_size_syringe.setReadOnly(True)
#         self.input_size_syringe.clicked.connect(
#             lambda: self.open_numpad("heparineSyrinjeScaleSize", self.input_size_syringe, "Tamaño de jeringa")
#         )
#         grid.addWidget(self.input_size_syringe, 2, 10,1,2)

#         lbl_usize_syringe = QLabel("mm/ml")
#         lbl_usize_syringe.setStyleSheet(style_unit)
#         grid.addWidget(lbl_usize_syringe, 2, 12)

#         # Tiempo de terapia: este sí se escribe al control (PLC), 
#         # y su valor también rige el timer local de la bomba de heparina (op_ph).
#         lbl_t_therapy = QLabel("T.") #tiempo de terapia
#         lbl_t_therapy.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_therapy, 2, 13)

#         self.input_t_therapy = ClickableLineEdit("00:00")
#         self.input_t_therapy.setFixedSize(100, 35)
#         self.input_t_therapy.setStyleSheet(style_input)
#         self.input_t_therapy.setAlignment(Qt.AlignCenter)
#         self.input_t_therapy.setReadOnly(True)
#         self.input_t_therapy.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_therapy,
#                 tag_hours="heparineTherapyHours", 
#                 tag_minutes="heparineTherapyMinutes",
#                 local_timer_id="op_ph", # Este timer local es regido por este campo
#                 title="Tiempo de terapia"
#             )
#         )
#         grid.addWidget(self.input_t_therapy, 2, 14,1,2) 

#         lbl_remaining_ph_title = QLabel("Rest.:")
#         lbl_remaining_ph_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_ph_title, 2, 18, alignment=Qt.AlignRight)

#         self.lbl_remaining_ph = QLabel("00:00")
#         self.lbl_remaining_ph.setStyleSheet(style_lbl_) 
#         grid.addWidget(self.lbl_remaining_ph, 2, 19,1,2, alignment=Qt.AlignLeft)

#         # ### ALMACENAR REFERENCIAS a las etiquetas en _local_timers_state
#         self._local_timers_state["op_ph"]["elapsed_lbl"] = None #self.lbl_elapsed_ph
#         self._local_timers_state["op_ph"]["remaining_lbl"] = self.lbl_remaining_ph

        
#         # ----------------------------------------------------------------------
#         # FILA 3: B. DIALIZANTE
#         # ----------------------------------------------------------------------
#         lbl_dializante = QLabel("B. Dializante")
#         lbl_dializante.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dializante, 3, 0, 1, 2)

#         self.toggle_dializante = ToggleSwitch(width=60, height=35)
#         self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk, timer_id="op_pd"))
#         grid.addWidget(self.toggle_dializante, 3,2)

#         self.lbl_input_indSDializante = ClickableLineEdit("0.0")
#         self.lbl_input_indSDializante.setFixedSize(80,35)
#         self.lbl_input_indSDializante.setStyleSheet(style_input)
#         self.lbl_input_indSDializante.setAlignment(Qt.AlignCenter)
#         self.lbl_input_indSDializante.setReadOnly(True)
#         self.lbl_input_indSDializante.clicked.connect(
#             lambda: self.open_numpad("dialyFlowControlOutput", self.lbl_input_indSDializante,"Salida Dializante (%)")
#         )
#         grid.addWidget(self.lbl_input_indSDializante, 3,3)

#         lbl_unit_indSdializante = QLabel("%")
#         lbl_unit_indSdializante.setStyleSheet(style_unit)
#         # lbl_unit_indSdializante.setFixedSize(100,35)
#         grid.addWidget(lbl_unit_indSdializante, 3, 5)

#         lbl_e_tOpBD = QLabel("T.:")
#         lbl_e_tOpBD.setStyleSheet(style_lbl)
#         lbl_e_tOpBD.setFixedSize(80,35)
#         grid.addWidget(lbl_e_tOpBD, 3, 6)

#         self.lbl_tiempo_OpBD = ClickableLineEdit("00:00") # ¡CORRECCIÓN!
#         self.lbl_tiempo_OpBD.setStyleSheet(style_input)
#         self.lbl_tiempo_OpBD.setFixedSize(100,35)
#         self.lbl_tiempo_OpBD.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_OpBD.setReadOnly(True)
#         self.lbl_tiempo_OpBD.clicked.connect( # ¡CORRECCIÓN!
#             lambda: self.open_time_numpad(
#             self.lbl_tiempo_OpBD,
#             tag_hours=None,
#             tag_minutes=None,
#             local_timer_id="op_pd", # Identificador para timer local
#             title="Tiempo Op. Dializante"
#             )
#         )
#         grid.addWidget(self.lbl_tiempo_OpBD,3,7)

    
#         lbl_remaining_pd_title = QLabel("Rest.:")
#         lbl_remaining_pd_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_pd_title, 3, 12, alignment=Qt.AlignRight)

#         self.lbl_remaining_pd = QLabel("00:00")
#         self.lbl_remaining_pd.setStyleSheet(style_lbl_)
#         self.lbl_remaining_pd.setFixedSize(100,35)
#         self.lbl_remaining_pd.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_pd, 3, 13, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_pd"]["elapsed_lbl"] = None #self.lbl_elapsed_pd
#         self._local_timers_state["op_pd"]["remaining_lbl"] = self.lbl_remaining_pd

        
#         # ----------------------------------------------------------------------
#         # FILA 4: B. Ultra Filtrado
#         # ----------------------------------------------------------------------
#         lbl_ultrafiltado = QLabel("B. UF")
#         lbl_ultrafiltado.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_ultrafiltado, 4,0, 1 ,2)

#         self.toggle_uf = ToggleSwitch(width=60, height=35)
#         self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt","dialyUltraFPumpStoptButt",chk, timer_id="op_puf"))
#         grid.addWidget(self.toggle_uf, 4,2)

#         self.lbl_input_indUF = ClickableLineEdit("0.0")
#         self.lbl_input_indUF.setFixedSize(80,35)
#         self.lbl_input_indUF.setAlignment(Qt.AlignCenter)
#         self.lbl_input_indUF.setStyleSheet(style_input)
#         self.lbl_input_indUF.setReadOnly(True)
#         self.lbl_input_indUF.clicked.connect(self._handle_flow_uf_input)
#         grid.addWidget(self.lbl_input_indUF, 4, 3)

#         lbl_unit_indUF = QLabel("L/h")
#         lbl_unit_indUF.setStyleSheet(style_unit)
#         # lbl_unit_indUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indUF, 4,5)

#         lbl_e_tOpBUF = QLabel("T.:")
#         lbl_e_tOpBUF.setStyleSheet(style_lbl)
#         lbl_e_tOpBUF.setFixedSize(80, 35)
#         grid.addWidget(lbl_e_tOpBUF, 4, 6)

#         self.lbl_tiempo_opBUF = ClickableLineEdit("00:00") # ¡CORRECCIÓN!
#         self.lbl_tiempo_opBUF.setStyleSheet(style_input)
#         self.lbl_tiempo_opBUF.setFixedSize(100, 35)
#         self.lbl_tiempo_opBUF.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_opBUF.setReadOnly(True)
#         self.lbl_tiempo_opBUF.clicked.connect( # ¡CORRECCIÓN!
#             lambda: self.open_time_numpad(
#                 self.lbl_tiempo_opBUF,
#                 tag_hours=None,
#                 tag_minutes=None,
#                 local_timer_id="op_puf", # Identificador para timer local
#                 title="Tiempo Op. Ultra Filtrado"
#             )
#         )
#         grid.addWidget(self.lbl_tiempo_opBUF, 4, 7)

        
#         lbl_remaining_puf_title = QLabel("Rest.:")
#         lbl_remaining_puf_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_puf_title, 4, 12, alignment=Qt.AlignRight)

#         self.lbl_remaining_puf = QLabel("00:00")
#         self.lbl_remaining_puf.setFixedSize(100,35)
#         self.lbl_remaining_puf.setStyleSheet(style_lbl_)
#         self.lbl_remaining_puf.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_remaining_puf, 4, 13, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_puf"]["elapsed_lbl"] = None #self.lbl_elapsed_puf
#         self._local_timers_state["op_puf"]["remaining_lbl"] = self.lbl_remaining_puf
  


#         # ----------------------------------------------------------------------
#         # FILA 5: B. Bicarbonato Na+
#         # ----------------------------------------------------------------------
#         lbl_bicarbonato = QLabel("B. Na+")
#         lbl_bicarbonato.setStyleSheet(style_lbl)
#         lbl_bicarbonato.setFixedSize(100, 35)
#         grid.addWidget(lbl_bicarbonato, 5, 0, 1, 2)

#         self.toggle_Na = ToggleSwitch(width=60, height=35)
#         self.toggle_Na.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt","dialyBicarbonPumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_Na, 5, 2)

#         self.lbl_indBNa = QLabel("0.0")
#         self.lbl_indBNa.setStyleSheet(style_lbl_)
#         self.lbl_indBNa.setFixedSize(80, 35)
#         self.lbl_indBNa.setAlignment(Qt.AlignCenter)
#         grid.addWidget(self.lbl_indBNa, 5, 3)

#         lbl_unit_indBNa = QLabel("%")
#         lbl_unit_indBNa.setStyleSheet(style_unit)
#         lbl_unit_indBNa.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBNa, 5, 5)
                                                                                                                                                                                                                                                                         
#         # ----------------------------------------------------------------------
#         # FILA 6: B. Acido Citrico
#         # ----------------------------------------------------------------------
#         lbl_acidocitrico = QLabel("B. A. Citrico")
#         lbl_acidocitrico.setStyleSheet(style_lbl)
#         lbl_acidocitrico.setFixedSize(100, 35)
#         grid.addWidget(lbl_acidocitrico, 6, 0, 1 ,2)

#         self.toggle_acidocitrico = ToggleSwitch(width=60, height=35)
#         self.toggle_acidocitrico.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt","dialyCitricAcPumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_acidocitrico, 6, 2)

#         self.lbl_indBAC = QLabel("0.0")
#         self.lbl_indBAC.setStyleSheet(style_lbl_)
#         self.lbl_indBAC.setAlignment(Qt.AlignCenter)
#         self.lbl_indBAC.setFixedSize(80, 35)
#         grid.addWidget(self.lbl_indBAC, 6, 3)

#         lbl_unit_indBAC = QLabel("%")
#         lbl_unit_indBAC.setStyleSheet(style_unit)
#         # lbl_unit_indBAC.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBAC, 6, 5)

#         # ----------------------------------------------------------------------
#         # FILA 7: B. Purga de Aire
#         # ----------------------------------------------------------------------
#         lbl_purga = QLabel("B. Purga")
#         lbl_purga.setStyleSheet(style_lbl)
#         lbl_purga.setFixedSize(100, 35)
#         grid.addWidget(lbl_purga, 7, 0,1,2)

#         self.toggle_purga = ToggleSwitch(width=60, height=35)
#         self.toggle_purga.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt","dialyPurgePumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_purga, 7, 2)

#         self.lbl_indPurga = ClickableLineEdit("0.0")
#         self.lbl_indPurga.setFixedSize(80, 35)
#         self.lbl_indPurga.setStyleSheet(style_input)
#         self.lbl_indPurga.setAlignment(Qt.AlignCenter)
#         self.lbl_indPurga.setReadOnly(True)
#         self.lbl_indPurga.clicked.connect(
#             lambda: self.open_numpad("dialyDeaerControlOutput", self.lbl_indPurga, "Salida b. Purga (%)")
#         )
#         grid.addWidget(self.lbl_indPurga, 7, 3)

#         lbl_unit_indPurga = QLabel("%")
#         lbl_unit_indPurga.setStyleSheet(style_unit)
#         # lbl_unit_indPurga.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indPurga, 7, 5) 


#         # ----------------------------------------------------------------------
#         # FILAS 8: C. Balance (Cámara de Balance)
#         # ----------------------------------------------------------------------
#         lbl_cb = QLabel("C. Balance")
#         lbl_cb.setStyleSheet(style_lbl)
#         lbl_cb.setFixedSize(100, 35)
#         grid.addWidget(lbl_cb, 8, 0, 1, 2)

#         self.toggle_cb = ToggleSwitch(width=70, height=35)
#         self.toggle_cb.toggled.connect(lambda chk: self.manejar_bomba_doble("dialiserBalChambStrButt","dialiserBalChambStpButt",chk, timer_id="op_cb"))
#         grid.addWidget(self.toggle_cb, 8, 2)

#         # Campo de configuración de tiempo (Input)
#         lbl_t_op_cb = QLabel("T.:")
#         lbl_t_op_cb.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_op_cb, 8, 4) 

#         self.input_t_BalanceChamber = ClickableLineEdit("00:00")
#         self.input_t_BalanceChamber.setFixedSize(100, 35)
#         self.input_t_BalanceChamber.setStyleSheet(style_input)
#         self.input_t_BalanceChamber.setAlignment(Qt.AlignCenter)
#         self.input_t_BalanceChamber.setReadOnly(True)
#         self.input_t_BalanceChamber.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_BalanceChamber,
#                 tag_hours=None,
#                 tag_minutes=None,
#                 local_timer_id="op_cb", 
#                 title="Tiempo Op. Cámara de Balance"
#             )
#         )
#         grid.addWidget(self.input_t_BalanceChamber, 8, 5, 1, 2)       
        
#         # Etiqueta de Tiempo Restante (Mantenida)
#         lbl_remaining_cb_title = QLabel("Rest.:")
#         lbl_remaining_cb_title.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_remaining_cb_title, 8, 7, alignment=Qt.AlignRight) # Ajusté la columna para pegar a la izquierda

#         self.lbl_remaining_cb = QLabel("00:00")
#         self.lbl_remaining_cb.setStyleSheet(style_lbl_)
#         self.lbl_remaining_cb.setAlignment(Qt.AlignCenter)
#         self.lbl_remaining_cb.setFixedSize(100,35)
#         grid.addWidget(self.lbl_remaining_cb, 8, 8, alignment=Qt.AlignLeft) # Ajusté la columna

#         # Configuración del estado del timer
#         self._local_timers_state["op_cb"]["elapsed_lbl"] = None  # <--- IMPORTANTE: None porque ya no existe visualmente
#         self._local_timers_state["op_cb"]["remaining_lbl"] = self.lbl_remaining_cb

#         # Ciclos (Movido para aprovechar el espacio)
#         lbl_cycles_chamber = QLabel("Ciclos CB")
#         lbl_cycles_chamber.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_cycles_chamber, 8, 10,1,2) # Columna ajustada

#         self.input_cycles_chamber = ClickableLineEdit("0")
#         self.input_cycles_chamber.setFixedSize(80,35)
#         self.input_cycles_chamber.setAlignment(Qt.AlignCenter)
#         self.input_cycles_chamber.setStyleSheet(style_input)
#         self.input_cycles_chamber.setReadOnly(True)
#         self.input_cycles_chamber.clicked.connect(
#             lambda: self.open_numpad("balanceChamberCycleSet", self.input_cycles_chamber, "Ciclos CB")
#         )
#         grid.addWidget(self.input_cycles_chamber, 8, 12, 1, 2) # Columna ajustada

#         lbl_flow_cb = QLabel("Flujo")
#         lbl_flow_cb.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_flow_cb,8,14)

#         self.input_flow_cb = ClickableLineEdit("0")
#         self.input_flow_cb.setFixedSize(80, 35)
#         self.input_flow_cb.setAlignment(Qt.AlignCenter)
#         self.input_flow_cb.setStyleSheet(style_input)
#         self.input_flow_cb.setReadOnly(True)
#         self.input_flow_cb.clicked.connect(self._handle_flow_cb_input)
#         grid.addWidget(self.input_flow_cb, 8, 15)

#         lbl_unit_flow_cb = QLabel("ml/min")
#         lbl_unit_flow_cb.setStyleSheet(style_unit)
#         grid.addWidget(lbl_unit_flow_cb, 8, 18)
       
#         grid.setColumnStretch(0, 1)   # Espacio izquierda para títulos
#         grid.setColumnStretch(16, 1)  # Espacio derecha para Remaining y extras
#         grid.setColumnMinimumWidth(3, 70)   # Toggle
#         grid.setColumnMinimumWidth(13, 110) # Campos de tiempo
#         grid.setColumnMinimumWidth(16, 120) # Remaining

#         layout.addWidget(self.control_area, 0, 0)
#         # ==================================================================
#         #          AREA 2: INDICADORES LED
#         # ==================================================================
#         self.ind_area = QWidget()
#         self.ind_area.setFixedSize(180,726)
#         grid_ind_area = QGridLayout(self.ind_area)
#         grid_ind_area.setSpacing(10)
#         grid_ind_area.setContentsMargins(10, 10,10, 10)

#         led_nombres = ["B. Sangre","B. Dializante","B. Heparina","B. UltraF","Purga de\n aire","C.Balance","A. sangre","C.Deaereación","Fin de\n ciclos","Protec.\n Resist.","S.Dializante","Nivel de\ntanque"]   
#         self.leds = []
#         for i, nombre in enumerate(led_nombres):
#             lbl = QLabel(nombre)
#             lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
#             lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#             grid_ind_area.addWidget(lbl, i, 0)

#             led = LED()
#             led.setFixedSize(45, 45)
#             grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
#             self.leds.append(led)

#         layout.addWidget(self.ind_area, 0, 1, 2, 1)

#         # ==============================================================================================
#         # AREA 3: VÁLVULAS
#         # ==============================================================================================
#         self.ctrl_valvulas = QWidget()
#         self.ctrl_valvulas.setFixedSize(1300,180)
#         layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas) 
#         layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
#         layout_ctrl_valvulas.setSpacing(5)
        
#         self.container_mop = QFrame()
#         self.container_mop.setFixedSize(100,180)
#         self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
#         layout_mop = QVBoxLayout(self.container_mop) 
       
#         lbl_modo = QLabel("Modo de \n Op.")
#         lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
#         lbl_modo.setAlignment(Qt.AlignCenter)
        
#         self.toggle_modo = ToggleSwitch(width=60, height=30, active_color="#facc15") 
#         self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))

#         layout_mop.addStretch()
#         layout_mop.addWidget(lbl_modo)
#         layout_mop.setSpacing(10)
#         layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
#         layout_mop.addStretch()
        
#         layout_ctrl_valvulas.addWidget(self.container_mop)

#         self.container_val = QWidget()
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
#             parts = desc.split(" ",1)
#             codigo = parts[0]
#             texto = parts[1] if len(parts) > 1 else ""

#             card = ValveCard(codigo, texto)
#             self.valvulas_map[tag] = card
#             grid_valvulas_area.addWidget(card, r, c)
#             card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

#         layout_ctrl_valvulas.addWidget(self.container_val)
#         layout.addWidget(self.ctrl_valvulas, 1, 0)    

#     def _actualizar_toggle(self, toggle, valor):
#         """Función auxiliar para actualizar toggle sin disparar señal"""
#         estado_nuevo = (valor > 0)
        
#         if toggle.is_checked() != estado_nuevo:
#             toggle.blockSignals(True)  # Importante: Evita bucle infinito con el PLC
#             toggle.setChecked(estado_nuevo)
#             toggle.blockSignals(False)

#     def actualizar_valores(self, nuevos_valores):
#         self.valores = nuevos_valores
        
#         # ACTUALIZAR LEDS
#         variables_leds = [
#             "bloodPumpStartButton",       
#             "dialyserPumpStartButton",    
#             "heparinePumpsStartButton",   
#             "dialyUltraFPumpStartButt",   
#             "dialyPurgePumpStartButt",    
#             "dialiserBalChambStrButt",    
#             "airBubbleInBloodDetected",   
#             "dialyDeaerChamLevSwitch",    
#             "dialyBalanceChambCycleEnd",  
#             "watterTankHeaterProtect",    
#             "bloodInDialyCircDetected",   
#             "dialyTankHiLevelSwitch"      
#         ]
#         for i, led in enumerate(self.leds):
#             if i < len(variables_leds):
#                 nombre_var = variables_leds[i]
#                 valor = self.valores.get(nombre_var, 0.0)
#                 estado = 'on' if valor > 0 else 'off'
#                 if led.state != estado:
#                     led.set_state(estado)
        
#         # ACTUALIZAR VÁLVULAS
#         for tag, card in self.valvulas_map.items():
#             val = self.valores.get(tag, 0.0)
#             nuevo_estado = True if val > 0 else False
#             if card.toggle.is_checked() != nuevo_estado:
#                 card.toggle.blockSignals(True)
#                 if hasattr(card.toggle, "setChecked"):
#                     card.toggle.setChecked(nuevo_estado)
#                 card.toggle.blockSignals(False)
        
#         # ACTUALIZAR INDICADORES NUMÉRICOS
        
#         cycle_to_flow = self.valores.get("balanceChamberSetTiming", 0.0)
#         try:
#             calc_cycle_to_flow = convertir_ciclos_a_flujo(cycle_to_flow)
#         except Exception:
#             calc_cycle_to_flow = 0.0
#         temp_tag_cycle_to_flow = "calc_c_to_f"
#         self.valores[temp_tag_cycle_to_flow] = calc_cycle_to_flow
#         if not self.input_flow_cb.hasFocus(): 
#             self.input_flow_cb.setText(f"{calc_cycle_to_flow:.1f}") 
        
#         uf_flow_to_liters = self.valores.get("ultraFilterPumpSpeed", 0.0)
#         try:
#             calc_uf_flow_to_liters = convertir_ml_min_a_litros_h(uf_flow_to_liters)
#         except Exception:
#             calc_uf_flow_to_liters = 0.0
#         temp_tag_cycle_to_flow = "calc_uf_flow_to_liters"
#         self.valores[temp_tag_cycle_to_flow] = calc_uf_flow_to_liters
#         if not self.lbl_input_indUF.hasFocus():
#             self.lbl_input_indUF.setText(f"{calc_uf_flow_to_liters:.1f}")

        

#         self.update_label_val(self.lbl_velocidad_val, "bloodSpeedVariableData" )
#         self.update_label_val(self.lbl_indBNa, "bicarbonatePumpSpeed" )
#         self.update_label_val(self.lbl_indBAC, "citricAcidPumpSpeed" )        
#         self.update_label_val(self.indHeparinCurrentDosage, "heparineCurrentDosage" )
#         self.update_input_val(self.input_cycles_chamber,"balanceChamberCycleSet" )
#         self.update_input_val(self.lbl_input_indSDializante, "dialyFlowControlOutput")
#         self.update_input_val(self.lbl_indPurga, "dialyDeaerControlOutput")
#         self.update_input_val(self.input_dosis_hep, "heparineTherapyDosage")
#         self.update_input_val(self.input_size_syringe,"heparineSyrinjeScaleSize")
#         self.update_input_val(self.input_dosis_bolo, "heparineBolusQuantity")
#         self.update_input_val(self.input_flujo_sangre,"bloodFlowControlSetPoint" )        
#         self.update_time_input_val(self.input_t_therapy, "heparineTherapyHours", "heparineTherapyMinutes")


#         # ACTUALIZAR TOGGLES DE BOMBAS 
#         self._actualizar_toggle(self.toggle_sangre, self.valores.get("bloodPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_heparina, self.valores.get("heparinePumpsStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_dializante, self.valores.get("dialyserPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_acidocitrico, self.valores.get("dialyCitricAcPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_Na, self.valores.get("dialyBicarbonPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_purga, self.valores.get("dialyPurgePumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_uf, self.valores.get("dialyUltraFPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_modo, self.valores.get("dialyCircuitElementsOpSel", 0.0))

#         # ### CORRECCIÓN: Actualizar el toggle de la Cámara de Balance
#         self._actualizar_toggle(self.toggle_cb,self.valores.get("dialiserBalChambStrButt",0.0))

#     # def update_time_input_val(self, widget: ClickableLineEdit, tag_hours: str, tag_minutes: str):
#     #     """
#     #     Actualiza un ClickableLineEdit con formato HH:MM a partir de dos tags (horas y minutos).
#     #     Solo actualiza si el widget no tiene el foco.
#     #     """
#     #     if not widget.hasFocus():
#     #         hours = int(self.valores.get(tag_hours, 0))
#     #         minutes = int(self.valores.get(tag_minutes, 0))
#     #         widget.setText(f"{hours:02d}:{minutes:02d}")


#     def update_time_input_val(self, time_input_widget, tag_hours: str, tag_minutes: str):
#         """
#         Actualiza un LabeledTimeInput o ClickableLineEdit con un valor HH:MM
#         proveniente del PLC, respetando el "hold-off" si el usuario acaba de escribir.
#         """
#         # --- 1. Aplicar lógica de "hold-off" para evitar el parpadeo ---
#         current_time = QDateTime.currentMSecsSinceEpoch()
        
#         # Obtenemos el tiempo hasta el que se debe mantener el "hold-off" para ambos tags.
#         # Si uno de los tags es None (no se escribe al PLC), su hold_off_time será 0,
#         # lo cual significa que no hay hold-off activo para ese tag.
#         hold_off_h_time = self._write_hold_off.get(tag_hours, 0) if tag_hours else 0
#         hold_off_m_time = self._write_hold_off.get(tag_minutes, 0) if tag_minutes else 0

#         # Si el tiempo actual es menor que cualquiera de los tiempos de "hold-off" registrados,
#         # significa que el usuario acaba de interactuar con este campo (o una parte de él).
#         # Por lo tanto, NO actualizamos la UI con el valor del PLC aún.
#         if current_time < hold_off_h_time or current_time < hold_off_m_time:
#             return

#         # --- 2. Obtener valores del PLC ---
#         hours = int(self.valores.get(tag_hours, 0)) if tag_hours else 0
#         minutes = int(self.valores.get(tag_minutes, 0)) if tag_minutes else 0
        
#         # --- 3. Actualizar el widget según su tipo ---
#         if isinstance(time_input_widget, LabeledTimeInput):
#             # Si es tu widget compuesto LabeledTimeInput, usa su método set_time_value.
#             time_input_widget.set_time_value(hours, minutes)
#         elif hasattr(time_input_widget, 'setText'): 
#             # Si es un ClickableLineEdit (o QLineEdit), usa setText.
#             # Solo actualizamos si no tiene el foco (para ClickableLineEdit/QLineEdit)
#             if not time_input_widget.hasFocus(): 
#                 time_input_widget.setText(f"{hours:02d}:{minutes:02d}")
#         else:
#             print(f"[ADVERTENCIA] update_time_input_val recibió un tipo de widget no soportado para tags de tiempo: ({tag_hours}, {tag_minutes}).")

    
#     # def update_input_val(self, widget, tag, precision=1):
#     #     value = self.valores.get(tag, 0.0)
#     #     if not widget.hasFocus():
#     #         widget.setText(f"{value:.{precision}f}")
#     def update_input_val(self, widget, tag, precision=1):
#         """
#         Actualiza el valor en la interfaz. 
#         Detecta si es un widget simple (QLineEdit/Label) o el compuesto (LabeledParameterWidget).
#         """
#         # 1. Obtener el valor del diccionario de datos
#         value = self.valores.get(tag, 0.0)
#         # 2. Verificar el tipo de widget y usar el método correcto
#         if isinstance(widget, LabeledParameterWidget):
#             # CASO 1: Es tu widget compuesto. Usa su método específico.
#             widget.set_value(value)        
#         elif hasattr(widget, "setText"):
#             # CASO 2: Es un QLineEdit, ClickableLineEdit o QLabel normal.
#             # Verificamos si tiene foco para no interrumpir al usuario (solo para inputs)
#             if hasattr(widget, "hasFocus") and widget.hasFocus():
#                 return            
#             # Formatear y setear
#             widget.setText(f"{value:.{precision}f}")            
#         else:
#             print(f"[ERROR UI] El widget para el tag '{tag}' no soporta setText ni set_value.")

#     # def update_label_val(self, label, tag, precision=1):
#     #         """
#     #         Actualiza un label indicador (siempre, ya que no tiene foco).
#     #         """
#     #         value = self.valores.get(tag, 0.0)

#     #         label.setText(f"{value:.{precision}f}")
#     def update_label_val(self, label_widget, tag, precision=1):
#         """
#         Actualiza un widget indicador (Label o LabeledParameterWidget no editable).
#         Siempre actualiza, ya que estos widgets no tienen foco para edición.
#         """
#         value = self.valores.get(tag, 0.0)
        
#         # Detectar el tipo de widget y usar el método de actualización adecuado
#         if isinstance(label_widget, LabeledParameterWidget):
#             # Si es tu widget compuesto, usa su método set_value.
#             # Nota: LabeledParameterWidget.set_value ya tiene su propia lógica de formato.
#             # Si quieres que 'precision' sea respetado por LabeledParameterWidget,
#             # deberías modificar su método set_value para aceptarlo como argumento.
#             label_widget.set_value(value) 
#         elif hasattr(label_widget, 'setText'):
#             # Si es un QLabel estándar o un widget similar con setText
#             label_widget.setText(f"{value:.{precision}f}")
#         else:
#             print(f"[ADVERTENCIA] update_label_val recibió un tipo de widget no soportado para el tag '{tag}'.")
            


#     def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
#         if activado:
#             print(f"[BOMBA] Arrancando {tag_start}")
#             self.escribir_comando(tag_start, True)
#             self.escribir_comando(tag_stop, False) 
            
#             # --- CORRECCIÓN: Obtener duración del diccionario de estado ---
#             if timer_id:
#                 state = self._local_timers_state[timer_id]
#                 total_ms_duration = state["duration_ms"] # ¡AHORA LEE DEL DICCIONARIO!

#                 if total_ms_duration > 0:
#                     state["active"] = True # Marcar como activo
#                     state["start_ms"] = QDateTime.currentMSecsSinceEpoch() # Guardar el timestamp de inicio

#                     timer_obj = getattr(self, f"timer_{timer_id}") # Obtiene el QTimer
#                     timer_obj.start(total_ms_duration) # Inicia el QTimer de un solo disparo

#                     print(f"[APP_TIMER] Iniciando timer '{timer_id}' por {total_ms_duration} ms.")
#                 else:
#                     print(f"[APP_TIMER] Advertencia: Timer '{timer_id}' no tiene duración establecida (0 ms). No se inició.")

#         else: # Bomba desactivada
#             print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
#             self.escribir_comando(tag_stop, True) 
#             self.escribir_comando(tag_start, False)
            
#             if timer_id:
#                 state = self._local_timers_state[timer_id]
#                 if state["active"]: # Solo si estaba activo, entonces lo detengo
#                     state["active"] = False # Marcar como inactivo
                    
#                     # Detener el QTimer de un solo disparo
#                     timer_obj = getattr(self, f"timer_{timer_id}")
#                     if timer_obj.isActive():
#                         timer_obj.stop()
                    
#                     # ### RESETEAR LAS ETIQUETAS DE TIEMPO DEL DISPLAY
#                     # if state["elapsed_lbl"]: state["elapsed_lbl"].setText("00:00")
#                     # if state["remaining_lbl"]: 
#                     #     h_config = state["duration_ms"] // 3600000
#                     #     m_config = (state["duration_ms"] % 3600000) // 60000
#                     #     state["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}") # Vuelve a mostrar la duración configurada

#                     if state["elapsed_lbl"] is not None: 
#                         state["elapsed_lbl"].setText("00:00")
                        
#                     if state["remaining_lbl"] is not None: 
#                         h_config = state["duration_ms"] // 3600000
#                         m_config = (state["duration_ms"] % 3600000) // 60000
#                         state["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}") 

#                     print(f"[APP_TIMER] Deteniendo timer '{timer_id}'.")


#     # def escribir_setpoint(self, tag, widget_input):
#     #     try:
#     #         texto = widget_input.text().replace(',', '.')
#     #         if not texto:                 
#     #             current_value = self.valores.get(tag, 0.0)
#     #             widget_input.setText(f"{current_value:.1f}") 
#     #             return 
                
#     #         valor = float(texto)
#     #         print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
#     #         target_group = -1
#     #         target_id = -1
#     #         found = False
            
#     #         for group_key, variables_in_group in VARIABLES.items():                
#     #             if isinstance(variables_in_group, dict): 
#     #                 for var_id, info in variables_in_group.items():
#     #                     if info.get("tag") == tag:
#     #                         target_group = group_key
#     #                         target_id = var_id
#     #                         found = True
#     #                         break
#     #             if found: break 
            
#     #         if found and target_group != -1 and target_id != -1:
#     #             if VARIABLES[target_group][target_id].get("rw", False):
#     #                 print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
#     #                 if self.parent_window and hasattr(self.parent_window, 'serial'):                      
#     #                     self.parent_window.serial.escribir_double(target_group, target_id, valor)
#     #                 else:
#     #                     print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
#     #             else:
#     #                 print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
#     #         else:
#     #             print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")

#     #         widget_input.clearFocus()

#     #     except ValueError:
#     #         print(f"[ERROR] Valor numérico inválido en input para {tag}: {widget_input.text()}")
#     #     except Exception as e:
#     #         print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
#     def escribir_setpoint(self, tag, widget_input):
#         try:
#             # --- MODIFICACIÓN CLAVE: Diferenciar el tipo de widget para leer el valor ---
#             texto = ""
#             if isinstance(widget_input, LabeledParameterWidget):
#                 texto = widget_input.get_value() # Usa el método específico de tu LabeledParameterWidget
#             elif hasattr(widget_input, 'text'): # Para QLineEdit, ClickableLineEdit o QLabel con .text()
#                 texto = widget_input.text()
#             # Si pasas un TempInput (como en open_time_numpad), también necesitamos manejarlo:
#             elif hasattr(widget_input, 'valor'):
#                 texto = str(widget_input.valor)
#             else:
#                 print(f"[ERROR] Tipo de widget desconocido para el tag '{tag}'. No se puede leer el valor.")
#                 return

#             texto = texto.replace(',', '.') # Reemplazar coma por punto para decimales
            
#             if not texto:                 
#                 current_value = self.valores.get(tag, 0.0)
#                 # --- MODIFICACIÓN CLAVE: Diferenciar el tipo de widget para escribir el valor ---
#                 if isinstance(widget_input, LabeledParameterWidget):
#                     widget_input.set_value(current_value) # Usa el método específico de tu LabeledParameterWidget
#                 elif hasattr(widget_input, 'setText'):
#                     widget_input.setText(f"{current_value:.1f}") 
#                 return 
                
#             valor = float(texto)
#             print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
#             target_group = -1
#             target_id = -1
#             found = False
            
#             for group_key, variables_in_group in VARIABLES.items():                
#                 if isinstance(variables_in_group, dict): 
#                     for var_id, info in variables_in_group.items():
#                         if info.get("tag") == tag:
#                             target_group = group_key
#                             target_id = var_id
#                             found = True
#                             break
#                 if found: break 
            
#             if found and target_group != -1 and target_id != -1:
#                 if VARIABLES[target_group][target_id].get("rw", False):
#                     print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
#                     if self.parent_window and hasattr(self.parent_window, 'serial'):                      
#                         self.parent_window.serial.escribir_double(target_group, target_id, valor)
#                     else:
#                         print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
#                 else:
#                     print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
#             else:
#                 print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")

#             # --- MODIFICACIÓN CLAVE: Limpiar foco solo si el widget tiene el método ---
#             if hasattr(widget_input, 'clearFocus'):
#                 widget_input.clearFocus()

#         except ValueError:
#             # Asegúrate de que el mensaje de error también maneje los diferentes tipos de widget
#             display_text = ""
#             if isinstance(widget_input, LabeledParameterWidget):
#                 display_text = widget_input.get_value()
#             elif hasattr(widget_input, 'text'):
#                 display_text = widget_input.text()
#             elif hasattr(widget_input, 'valor'):
#                 display_text = str(widget_input.valor)
#             print(f"[ERROR] Valor numérico inválido en input para {tag}: {display_text}")
#         except Exception as e:
#             print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")

  
#     def escribir_comando(self, tag, estado):
#         print(f"[COMANDO] Usuario cambió {tag} a {estado}")
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
#                         print(f" -> Enviando: Addr {direccion} Val {estado}")
#                         self.parent_window.serial.escribir_booleano(direccion, estado)
#                     else:
#                         print(" -> Error: Serial no conectado")
#                 except AttributeError:
#                     print(f"[INFO] Fallo en envío: Addr {direccion} Val {estado}")
#             else:
#                  print(f"[INFO] Error no se completo la escritura: Addr {direccion} Val {estado}")
#         else:
#             print(f" -> Error: No se encontró ID para el tag '{tag}'")

#     # def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
#     #     act_value = widget_input.text()
#     #     dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
#     #     if dialog.exec(): 
#     #         new_value = dialog.get_value() 
#     #         widget_input.setText(str(new_value))            
#     #         self.escribir_setpoint(tag, widget_input)
#     def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
#         # 1. OBTENER EL VALOR ACTUAL
#         # Verificamos qué tipo de widget es para usar el método correcto de lectura
#         if isinstance(widget_input, LabeledParameterWidget):
#             # Tu widget personalizado usa get_value()
#             act_value = widget_input.get_value()
#         else:
#             # Los widgets estándar de Qt (QLineEdit, QLabel) usan text()
#             act_value = widget_input.text()

#         # Abrir el diálogo numérico
#         dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
        
#         if dialog.exec(): 
#             new_value = dialog.get_value() 
            
#             # 2. ACTUALIZAR LA INTERFAZ VISUALMENTE
#             # Verificamos el tipo de widget para escribir el valor de vuelta
#             if isinstance(widget_input, LabeledParameterWidget):
#                 widget_input.set_value(new_value)
#             else:
#                 widget_input.setText(str(new_value))            
            
#             # 3. ENVIAR EL CAMBIO AL PLC O LÓGICA INTERNA
#             self.escribir_setpoint(tag, widget_input)

#     def open_time_numpad(self, time_input_widget, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
#         """
#         1. Abre el TimeNumpadDialog con el valor actual del widget.
#         2. Al aceptar, actualiza el widget visual a "HH:MM".
#         3. Desglosa Horas y Minutos.
#         4. Si tiene tags, llama a escribir_setpoint para el PLC.
#         5. Si tiene local_timer_id, configura el QTimer correspondiente.
#         """
#         # --- MODIFICACIÓN CLAVE AQUÍ ---
#         # Si el widget es un LabeledTimeInput, usa su método get_time_value()
#         if isinstance(time_input_widget, LabeledTimeInput):
#             texto_actual = time_input_widget.get_time_value()
#         else:
#             # Si es un ClickableLineEdit (o similar), usa su método text()
#             texto_actual = time_input_widget.text()

#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

#         if dialog.exec():
#             h, m = dialog.get_hours_minutes()
            
#             # --- Y también aquí, para actualizar el widget de vuelta ---
#             if isinstance(time_input_widget, LabeledTimeInput):
#                 time_input_widget.set_time_value(h, m)
#             else:
#                 time_input_widget.setText(f"{h:02d}:{m:02d}")
            
#             # Calcular duración total en milisegundos
#             total_ms = (h * 3600 + m * 60) * 1000

#             # ... (el resto de tu función open_time_numpad sigue igual,
#             #      incluyendo la lógica de hold-off y el envío a escribir_setpoint) ...
#             current_timestamp = QDateTime.currentMSecsSinceEpoch()
#             hold_off_duration_ms = 3000 # 3 segundos de espera

#             if tag_hours and tag_minutes:
#                 print(f"[MH_WRITE] Enviando horas ({h}) al tag: {tag_hours}")
#                 fake_widget_h = TempInput(h) 
#                 self.escribir_setpoint(tag_hours, fake_widget_h)
#                 self._write_hold_off[tag_hours] = current_timestamp + hold_off_duration_ms

#                 print(f"[MH_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}")
#                 fake_widget_m = TempInput(m)
#                 self.escribir_setpoint(tag_minutes, fake_widget_m)
#                 self._write_hold_off[tag_minutes] = current_timestamp + hold_off_duration_ms
#             elif tag_hours or tag_minutes:
#                 print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

#             if local_timer_id:
#                 state = self._local_timers_state[local_timer_id] 
#                 state["duration_ms"] = total_ms 
                
#                 if state["elapsed_lbl"] is not None: 
#                     state["elapsed_lbl"].setText("00:00")
                
#                 if state["remaining_lbl"] is not None: 
#                     state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

#                 print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")


# gui/service/mManualScr.py
# Ejecución del autotest de la máquina y visualización de resultados.
# Control manual de los elementos de actuadores, bombas, válvulas

from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QGridLayout, QSizePolicy, QPushButton, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QDateTime
from PySide6.QtGui import QColor, QFont, QPainter # QPainter para el mock de LED

from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
# Importa todos los componentes personalizados desde el archivo unificado
from gui.components.ui_components import ClickableLineEdit, LabeledParameterWidget, LabeledTimeInput


# Mock de funciones de lógica de cálculo si no están presentes
try:
    from logic.calculos import convertir_flujo_a_ciclos
    from logic.calculos import convertir_ciclos_a_flujo
    from logic.calculos import convertir_litros_h_a_ml_min
    from logic.calculos import convertir_ml_min_a_litros_h
except ImportError:
    print("[WARNING] 'logic.calculos' not found. Using mock functions.")
    def convertir_flujo_a_ciclos(flow): return flow * 10
    def convertir_ciclos_a_flujo(cycles): return cycles / 10
    def convertir_litros_h_a_ml_min(lh): return lh * (1000/60)
    def convertir_ml_min_a_litros_h(mlm): return mlm / (1000/60)

# Mock de variables de control si no están presentes
try:
    from core.variables_map import VARIABLES, ANALOG_MAP
except ImportError:
    print("[WARNING] 'core.variables_map' not found. Using mock VARIABLES.")
    # Un mapa de variables de mock más completo para evitar KeyError
    VARIABLES = {
        0x01: { # Grupo 1 para comandos/estados
            # Bomba de Sangre
            0x01: {"tag": "bloodPumpStartButton", "rw": True},
            0x02: {"tag": "bloodPumpStopButton", "rw": True},
            0x03: {"tag": "bloodPumpREVButton", "rw": True},
            0x04: {"tag": "bloodPumpFWDButton", "rw": True},
            0x05: {"tag": "bloodFlowControlSetPoint", "rw": True},
            0x06: {"tag": "bloodSpeedVariableData", "rw": False},
            # Bomba de Heparina
            0x07: {"tag": "heparinePumpsStartButton", "rw": True},
            0x08: {"tag": "heparinePumpsStopButton", "rw": True},
            0x09: {"tag": "heparinePumpHomePosition", "rw": True},
            0x0A: {"tag": "heparinePumpREVButton", "rw": True},
            0x0B: {"tag": "heparineOperPauseResume", "rw": True},
            0x0C: {"tag": "heparinePumpFWDButton", "rw": True},
            0x0D: {"tag": "heparineTherapyDosage", "rw": True},
            0x0E: {"tag": "heparineBolusQuantity", "rw": True},
            0x0F: {"tag": "heparineSyrinjeScaleSize", "rw": True},
            0x10: {"tag": "heparineTherapyHours", "rw": True},
            0x11: {"tag": "heparineTherapyMinutes", "rw": True},
            0x12: {"tag": "heparineCurrentDosage", "rw": False},
            # Bomba de Dializante
            0x13: {"tag": "dialyserPumpStartButton", "rw": True},
            0x14: {"tag": "dialyserPumpStopButton", "rw": True},
            0x15: {"tag": "dialyFlowControlOutput", "rw": True}, # Asumimos rw para este
            # Bomba de Ultra Filtración
            0x16: {"tag": "dialyUltraFPumpStartButt", "rw": True},
            0x17: {"tag": "dialyUltraFPumpStoptButt", "rw": True},
            0x18: {"tag": "ultraFilterPumpSpeed", "rw": True}, # Asumimos rw para este
            # Bomba de Bicarbonato Na+
            0x19: {"tag": "dialyBicarbonPumpStartButt", "rw": True},
            0x1A: {"tag": "dialyBicarbonPumpStopButt", "rw": True},
            0x1B: {"tag": "bicarbonatePumpSpeed", "rw": False},
            # Bomba de Ácido Cítrico
            0x1C: {"tag": "dialyCitricAcPumpStartButt", "rw": True},
            0x1D: {"tag": "dialyCitricAcPumpStopButt", "rw": True},
            0x1E: {"tag": "citricAcidPumpSpeed", "rw": False},
            # Bomba de Purga de Aire
            0x1F: {"tag": "dialyPurgePumpStartButt", "rw": True},
            0x20: {"tag": "dialyPurgePumpStopButt", "rw": True},
            0x21: {"tag": "dialyDeaerControlOutput", "rw": True}, # Asumimos rw para este
            # Cámara de Balance
            0x22: {"tag": "dialiserBalChambStrButt", "rw": True},
            0x23: {"tag": "dialiserBalChambStpButt", "rw": True},
            0x24: {"tag": "balanceChamberCycleSet", "rw": True},
            0x25: {"tag": "balanceChamberSetTiming", "rw": True}, # Tag para ciclos, si se edita desde UI de flujo
            # Válvulas
            0x26: {"tag": "dialyInputFilterCutButt", "rw": True},
            0x27: {"tag": "dialyOutputFilterCutButt", "rw": True},
            0x28: {"tag": "dialyBypassFilterButt", "rw": True},
            0x29: {"tag": "dialyWaterInletValveButt", "rw": True},
            0x2A: {"tag": "dialyRecirculatValveButt", "rw": True},
            0x2B: {"tag": "dialyAirVentSepChambButt", "rw": True},
            0x2C: {"tag": "dialyHotChambValveButt", "rw": True},
            0x2D: {"tag": "dialyWaterDrainValveButt", "rw": True},
            # Modo de Operación
            0x2E: {"tag": "dialyCircuitElementsOpSel", "rw": True}, # Selector de modo operación
            # LEDs (Solo lectura)
            0x2F: {"tag": "airBubbleInBloodDetected", "rw": False},
            0x30: {"tag": "dialyDeaerChamLevSwitch", "rw": False},
            0x31: {"tag": "dialyBalanceChambCycleEnd", "rw": False},
            0x32: {"tag": "watterTankHeaterProtect", "rw": False},
            0x33: {"tag": "bloodInDialyCircDetected", "rw": False},
            0x34: {"tag": "dialyTankHiLevelSwitch", "rw": False},
        },
        0x02: {} # Mock vacío para otros grupos
    }
    ANALOG_MAP = {} # Mock vacío


# Mock de LED y ToggleSwitch si no están presentes
try:
    from gui.components.LED import LED
    from gui.components.ToggleSwitch import ToggleSwitch
except ImportError:
    print("[WARNING] 'gui.components.LED' or 'ToggleSwitch' not found. Using mock classes.")
    class LED(QWidget):
        def __init__(self, parent=None): 
            super().__init__(parent)
            self._state = 'off'
            self.setFixedSize(20,20) # Default size for mock LED
        def set_state(self, s): 
            if self._state != s:
                self._state = s
                self.update() # Request repaint
        def get_state(self): return self._state # Added for completeness
        def paintEvent(self, event): # Simple visual mock
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            color = QColor("green") if self._state == 'on' else QColor("red")
            painter.setBrush(color)
            painter.drawEllipse(0,0,self.width(), self.height())


    class ToggleSwitch(QCheckBox):
        def __init__(self, width=60, height=30, active_color=None, parent=None): 
            super().__init__(parent)
            self.setFixedSize(width, height)
            # Use self.isChecked() directly, it's more robust than an internal _is_checked
            # if setChecked is called without also updating _is_checked manually.
            # self._is_checked = False # No longer needed
            # self.toggled.connect(self._update_checked_state) # No longer needed

        def is_checked(self): # Helper method to match original usage pattern
            return self.isChecked() # Use built-in method


class TempInput:
    """
    Mock class to simulate a QLineEdit for passing numeric values to escribir_setpoint
    when the actual UI widget is not a QLineEdit (e.g., just passing a calculated value).
    """
    def __init__(self, valor):
        self._valor = valor
    def text(self):
        return str(self._valor)
    def clearFocus(self):
        pass 
    def setText(self, t):
        try:
            self._valor = float(t) # Try to update internal value if it's a number
        except ValueError:
            self._valor = t # Keep as string if not valid float, or handle error
        print(f"[TempInput] Internal value set to: {self._valor}")


class ValveCard(QFrame):
    def __init__(self, codigo, descripcion, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>", self)
        lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=60, height=30, parent=self)

        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(self.toggle)


class mManualScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        self.parent_window = parent  
        self.valores = valores_dict if valores_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1024, 600)

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#fcfcfc"))
        self.setPalette(p)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: INICIALIZACIÓN DE _write_hold_off <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Diccionario para controlar el tiempo de espera de escritura (hold-off).
        # Guardará: "tag_variable": timestamp_ms_de_fin_de_hold_off
        self._write_hold_off = {} 
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        self.timer_op_pb = QTimer(self) # Bomba de sangre
        self.timer_op_pd = QTimer(self) # Bomba de dializante 
        self.timer_op_puf = QTimer(self) # Bomba de ultraFiltración
        self.timer_op_ph = QTimer(self) # Bomba de heparina (terapia)
        self.timer_op_cb = QTimer(self) # Cámara de balance

        self.timer_op_pb.timeout.connect(self._stop_blood_pump_on_timeout)
        self.timer_op_pd.timeout.connect(self._stop_dialysate_pump_on_timeout)
        self.timer_op_puf.timeout.connect(self._stop_uf_pump_on_timeout)
        self.timer_op_ph.timeout.connect(self._stop_heparin_pump_on_timeout)
        self.timer_op_cb.timeout.connect(self._stop_balance_chamber_on_timeout)
        
        self._display_update_timer = QTimer(self)
        self._display_update_timer.timeout.connect(self._update_local_time_displays)
        self._display_update_timer.start(500) # Actualizar cada 500ms para una sensación más fluida

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: _local_timers_state se inicializa con Nones <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Los QLabel para elapsed_lbl y remaining_lbl se asignarán en setup_ui() una vez que los widgets estén creados.
        # Esto previene AttributeError en _update_local_time_displays y _stop_*_on_timeout.
        self._local_timers_state = {
            "op_pb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "op_pd": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "op_puf": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "op_ph": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
            "op_cb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
        }
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.control_area = QWidget(self)
        self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid = QGridLayout(self.control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)
        
        style_lbl = "color: #000000; font-size: 18px; font-weight: bold; "
        style_lbl_indicator = "color: #22d3ee; font-size: 20px; font-weight: bold;border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        style_unit = "color: #94a3b8; font-size: 16px;" # Style for standalone unit labels (if any remain)
        style_btn = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """        

        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 0: BOMBA DE SANGRE (B. Sangre) <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_sangre = QLabel("B. Sangre", self.control_area)
        lbl_sangre.setStyleSheet(style_lbl)
        grid.addWidget(lbl_sangre, 0, 0, 2, 2)

        self.toggle_sangre = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_sangre.toggled.connect(
            lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk, timer_id="op_pb")
        )
        grid.addWidget(self.toggle_sangre, 0, 2,2,2)

        btn_rev = QPushButton("REV", self.control_area)
        btn_rev.setFixedSize(80, 70)
        btn_rev.setStyleSheet(style_btn)
        btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
        btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
        
        btn_fwd = QPushButton("FWD", self.control_area)
        btn_fwd.setFixedSize(80, 70)
        btn_fwd.setStyleSheet(style_btn)
        btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
        btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))

        grid.addWidget(btn_rev, 0, 4,2,2)
        grid.addWidget(btn_fwd, 0, 6,2,2)

        self.input_flujo_sangre = LabeledParameterWidget( 
            label_text="Flujo",
            tag="bloodFlowControlSetPoint",
            value="0",
            units="ml/min",
            numpad_title="Flujo de Sangre",
            is_editable=True,
            parent=self.control_area
        )   
        self.input_flujo_sangre.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_flujo_sangre, 0, 8, 2, 2) # Ocupa 2 columnas para el label y el input

        self.lbl_velocidad_val = LabeledParameterWidget(
            label_text="Vel",
            tag="bloodSpeedVariableData", # El tag es para el valor del PLC
            value="0.0",
            units="rpm",
            numpad_title="",
            is_editable=False, # ES UN INDICADOR
            parent=self.control_area
        )
        grid.addWidget(self.lbl_velocidad_val, 0, 10, 2, 2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: LabeledTimeInput para Tiempo Operación Bomba de Sangre <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Eliminado el QLabel "T.:" redundante
        self.input_t_BloodPump = LabeledTimeInput(
            label_text="T. Op.:", # Texto interno del widget
            initial_hh_mm="00:00",
            tag_hours=None,        # No envía a PLC
            tag_minutes=None,      # No envía a PLC
            local_timer_id="op_pb",
            numpad_title="Tiempo de operación de bomba de sangre",
            parent=self.control_area
        )
        self.input_t_BloodPump.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.input_t_BloodPump, 0, 13, 2, 3) # Ajustado span para el LabeledTimeInput

        lbl_remaining_pb_title = QLabel("Rest.:", self.control_area)
        lbl_remaining_pb_title.setStyleSheet(style_lbl)
        grid.addWidget(lbl_remaining_pb_title, 0, 16, 2, 1, alignment=Qt.AlignRight)

        self.lbl_remaining_pb = QLabel("00:00", self.control_area)
        self.lbl_remaining_pb.setStyleSheet(style_lbl_indicator) # Color ámbar para restante
        self.lbl_remaining_pb.setFixedSize(100,35)
        self.lbl_remaining_pb.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_remaining_pb, 0, 17, 2, 1, alignment=Qt.AlignLeft)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: ASIGNACIÓN DE LABELS A _local_timers_state <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._local_timers_state["op_pb"]["remaining_lbl"] = self.lbl_remaining_pb 
        # Si tuvieras un self.lbl_elapsed_pb, también lo asignarías aquí:
        # self._local_timers_state["op_pb"]["elapsed_lbl"] = self.lbl_elapsed_pb
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 2: BOMBA DE HEPARINA (B. Hep.) <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_bHeparina = QLabel("B. Hep.", self.control_area)
        lbl_bHeparina.setStyleSheet(style_lbl)
        grid.addWidget(lbl_bHeparina, 2, 0, 2, 2)

        self.toggle_heparina = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk, timer_id="op_ph"))
        grid.addWidget(self.toggle_heparina, 2, 2, 2, 1)

        btn_homeHep = QPushButton("HOME", self.control_area)
        btn_homeHep.setFixedSize(80, 70)
        btn_homeHep.setStyleSheet(style_btn)
        btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
        btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False))
        
        btn_rev_hep = QPushButton("REV", self.control_area)
        btn_rev_hep.setFixedSize(80, 70)
        btn_rev_hep.setStyleSheet(style_btn)
        btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton",True))
        btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))

        btn_pause_hep = QPushButton("PAUSE", self.control_area)
        btn_pause_hep.setFixedSize(80, 70)
        btn_pause_hep.setStyleSheet(style_btn)
        btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume",True))
        btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))

        btn_fwd_hep = QPushButton("FWD", self.control_area)
        btn_fwd_hep.setFixedSize( 80, 70)
        btn_fwd_hep.setStyleSheet(style_btn)
        btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton",True))
        btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))

        grid.addWidget(btn_homeHep, 2, 4,2,2)
        grid.addWidget(btn_rev_hep, 2, 6,2 ,2)
        grid.addWidget(btn_pause_hep, 2, 8,2 ,2 )
        grid.addWidget(btn_fwd_hep, 2, 10,2,2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Heparina Actual <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget para consistencia de estilo y manejo
        self.indHeparinCurrentDosage = LabeledParameterWidget(
            label_text="Heparina", # Label principal del widget
            tag="heparineCurrentDosage",
            value="0.0",
            units="ml", # Unidades internas
            is_editable=False, # ES UN INDICADOR
            parent=self.control_area
        )
        grid.addWidget(self.indHeparinCurrentDosage, 2,12,2,3) # Ajustado span
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> Dosis Heparina <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.input_dosis_hep = LabeledParameterWidget(
            label_text="Dosis Hep.", 
            tag="heparineTherapyDosage",
            value="0.0",
            units="ml/h",
            numpad_title="Dosis Heparina",
            is_editable=True,
            parent=self.control_area
        )
        self.input_dosis_hep.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_dosis_hep, 2, 15, 2, 3) # Ajustado span
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> DOSIS BOLO <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.input_dosis_bolo = LabeledParameterWidget(
            label_text="Bolo",
            tag="heparineBolusQuantity",
            value="0.0",
            units="ml",
            numpad_title="Dosis Bolo",
            is_editable=True,
            parent=self.control_area
        )
        self.input_dosis_bolo.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_dosis_bolo, 4, 0, 1, 3) # Ajustado fila y span (ejemplo de reordenamiento)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> TAMAÑO JERINGA <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.input_size_syringe = LabeledParameterWidget(
            label_text="Jeringa",
            tag="heparineSyrinjeScaleSize",
            value="0.0",
            units="mm/ml",
            numpad_title="Tamaño de jeringa",
            is_editable=True,
            parent=self.control_area
        )
        self.input_size_syringe.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_size_syringe, 4, 3, 1, 3) # Ajustado fila y span (ejemplo)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: LabeledTimeInput para Tiempo de Terapia <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Eliminado lbl_t_therapy redundante
        self.input_t_therapy = LabeledTimeInput(
            label_text="T. Terapia:", # Texto interno del widget
            initial_hh_mm="00:00",
            tag_hours="heparineTherapyHours", 
            tag_minutes="heparineTherapyMinutes",
            local_timer_id="op_ph",
            numpad_title="Tiempo de terapia",
            parent=self.control_area
        )
        self.input_t_therapy.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.input_t_therapy, 4, 13,     1, 3) # Ajustado span (ejemplo)
        
        lbl_remaining_ph_title = QLabel("Rest.:", self.control_area)
        lbl_remaining_ph_title.setStyleSheet(style_lbl)
        grid.addWidget(lbl_remaining_ph_title, 4, 16, alignment=Qt.AlignRight)

        self.lbl_remaining_ph = QLabel("00:00", self.control_area)
        self.lbl_remaining_ph.setStyleSheet(style_lbl_indicator) 
        self.lbl_remaining_ph.setFixedSize(100,35)
        self.lbl_remaining_ph.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_remaining_ph, 4, 17, 1, 1, alignment=Qt.AlignLeft)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: ASIGNACIÓN DE LABELS A _local_timers_state <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._local_timers_state["op_ph"]["remaining_lbl"] = self.lbl_remaining_ph
        # self._local_timers_state["op_ph"]["elapsed_lbl"] = self.lbl_elapsed_ph
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 4: B. DIALIZANTE <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_dializante = QLabel("B. Dializante", self.control_area)
        lbl_dializante.setStyleSheet(style_lbl)
        grid.addWidget(lbl_dializante, 6, 0, 2, 2) 

        self.toggle_dializante = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk, timer_id="op_pd"))
        grid.addWidget(self.toggle_dializante, 6,2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Salida Dializante <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.lbl_input_indSDializante = LabeledParameterWidget(
            label_text="Salida",
            tag="dialyFlowControlOutput",
            value="0.0",
            units="%",
            numpad_title="Salida Dializante (%)",
            is_editable=True,
            parent=self.control_area
        )
        self.lbl_input_indSDializante.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.lbl_input_indSDializante, 6, 3, 1, 2) # Ajuste de span
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: LabeledTimeInput para Tiempo Op. Dializante <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Eliminado lbl_e_tOpBD redundante
        self.lbl_tiempo_OpBD = LabeledTimeInput(
            label_text="T. Op.:",
            initial_hh_mm="00:00",
            tag_hours=None,
            tag_minutes=None,
            local_timer_id="op_pd",
            numpad_title="Tiempo Op. Dializante",
            parent=self.control_area
        )
        self.lbl_tiempo_OpBD.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.lbl_tiempo_OpBD, 6, 6, 1, 3) # Ajustado span
    
        lbl_remaining_pd_title = QLabel("Rest.:", self.control_area)
        lbl_remaining_pd_title.setStyleSheet(style_lbl)
        grid.addWidget(lbl_remaining_pd_title, 6, 12, alignment=Qt.AlignRight)

        self.lbl_remaining_pd = QLabel("00:00", self.control_area)
        self.lbl_remaining_pd.setStyleSheet(style_lbl_indicator)
        self.lbl_remaining_pd.setFixedSize(100,35)
        self.lbl_remaining_pd.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_remaining_pd, 6, 13, alignment=Qt.AlignLeft)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: ASIGNACIÓN DE LABELS A _local_timers_state <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._local_timers_state["op_pd"]["remaining_lbl"] = self.lbl_remaining_pd
        # self._local_timers_state["op_pd"]["elapsed_lbl"] = self.lbl_elapsed_pd
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 5: B. Ultra Filtrado <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_ultrafiltado = QLabel("B. UF", self.control_area)
        lbl_ultrafiltado.setStyleSheet(style_lbl)
        grid.addWidget(lbl_ultrafiltado, 8, 0, 1 ,2) 

        self.toggle_uf = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt","dialyUltraFPumpStoptButt",chk, timer_id="op_puf"))
        grid.addWidget(self.toggle_uf, 8,2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Flujo UF <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget. Usa un manejador especial para la conversión L/h <-> ml/min.
        self.lbl_input_indUF = LabeledParameterWidget( 
            label_text="Flujo",
            tag="ultraFilterPumpSpeed", # El tag del PLC es ml/min
            value="0.0",
            units="L/h", # La UI muestra L/h
            numpad_title="Flujo UF (L/h)",
            is_editable=True,
            parent=self.control_area
        )
        self.lbl_input_indUF.request_numpad.connect(lambda tag_var, widget_ref, title_str: self._handle_flow_uf_input(tag_var, widget_ref, title_str))
        grid.addWidget(self.lbl_input_indUF, 8, 3, 1, 2)
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: LabeledTimeInput para Tiempo Op. Ultra Filtrado <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Eliminado lbl_e_tOpBUF redundante
        self.lbl_tiempo_opBUF = LabeledTimeInput(
            label_text="T. Op.:",
            initial_hh_mm="00:00",
            tag_hours=None,
            tag_minutes=None,
            local_timer_id="op_puf",
            numpad_title="Tiempo Op. Ultra Filtrado",
            parent=self.control_area
        )
        self.lbl_tiempo_opBUF.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.lbl_tiempo_opBUF, 8, 6, 1, 3)

        lbl_remaining_puf_title = QLabel("Rest.:", self.control_area)
        lbl_remaining_puf_title.setStyleSheet(style_lbl)
        grid.addWidget(lbl_remaining_puf_title, 8, 12, alignment=Qt.AlignRight)

        self.lbl_remaining_puf = QLabel("00:00", self.control_area)
        self.lbl_remaining_puf.setFixedSize(100,35)
        self.lbl_remaining_puf.setStyleSheet(style_lbl_indicator)
        self.lbl_remaining_puf.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_remaining_puf, 8, 13, alignment=Qt.AlignLeft)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: ASIGNACIÓN DE LABELS A _local_timers_state <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._local_timers_state["op_puf"]["remaining_lbl"] = self.lbl_remaining_puf
        # self._local_timers_state["op_puf"]["elapsed_lbl"] = self.lbl_elapsed_puf
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  
        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 6: B. Bicarbonato Na+ <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_bicarbonato = QLabel("B. Na+", self.control_area)
        lbl_bicarbonato.setStyleSheet(style_lbl)
        grid.addWidget(lbl_bicarbonato, 10, 0, 1, 2) 

        self.toggle_Na = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_Na.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt","dialyBicarbonPumpStopButt",chk, timer_id=None))
        grid.addWidget(self.toggle_Na, 10   , 2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Indicador B. Na+ <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.lbl_indBNa = LabeledParameterWidget( 
            label_text="Flujo", # Label interno para el widget
            tag="bicarbonatePumpSpeed",
            value="0.0",
            units="%",
            is_editable=False, # ES UN INDICADOR
            parent=self.control_area
        )
        grid.addWidget(self.lbl_indBNa, 10, 3, 1, 2) 
                                                                                                                                                                                                                                                                         
        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 7: B. Acido Citrico <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_acidocitrico = QLabel("B. A. Citrico", self.control_area)
        lbl_acidocitrico.setStyleSheet(style_lbl)
        grid.addWidget(lbl_acidocitrico, 10, 5, 1 ,2) 

        self.toggle_acidocitrico = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_acidocitrico.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt","dialyCitricAcPumpStopButt",chk, timer_id=None))
        grid.addWidget(self.toggle_acidocitrico, 10, 7)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Indicador B. A. Cítrico <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.lbl_indBAC = LabeledParameterWidget( 
            label_text="Flujo", # Label interno
            tag="citricAcidPumpSpeed",
            value="0.0",
            units="%",
            is_editable=False, # ES UN INDICADOR
            parent=self.control_area
        )
        grid.addWidget(self.lbl_indBAC, 10, 8, 1, 2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILA 8: B. Purga de Aire <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_purga = QLabel("B. Purga", self.control_area)
        lbl_purga.setStyleSheet(style_lbl)
        grid.addWidget(lbl_purga, 8, 0,1,2) 

        self.toggle_purga = ToggleSwitch(width=60, height=35, parent=self.control_area)
        self.toggle_purga.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt","dialyPurgePumpStopButt",chk, timer_id=None))
        grid.addWidget(self.toggle_purga, 8, 2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Salida B. Purga <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.lbl_indPurga = LabeledParameterWidget( 
            label_text="Salida",
            tag="dialyDeaerControlOutput",
            value="0.0",
            units="%",
            numpad_title="Salida b. Purga (%)",
            is_editable=True,
            parent=self.control_area
        )
        self.lbl_indPurga.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.lbl_indPurga, 8, 3, 1, 2) 

        # >>>>>>>>>>>>>>>>>>>>>>>>>> FILAS 9: C. Balance (Cámara de Balance) <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        lbl_cb = QLabel("C. Balance", self.control_area)
        lbl_cb.setStyleSheet(style_lbl)
        grid.addWidget(lbl_cb, 9, 0, 1, 2) 

        self.toggle_cb = ToggleSwitch(width=70, height=35, parent=self.control_area)
        self.toggle_cb.toggled.connect(lambda chk: self.manejar_bomba_doble("dialiserBalChambStrButt","dialiserBalChambStpButt",chk, timer_id="op_cb"))
        grid.addWidget(self.toggle_cb, 9, 2)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: LabeledTimeInput para Tiempo Op. Cámara de Balance <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Eliminado lbl_t_op_cb redundante
        self.input_t_BalanceChamber = LabeledTimeInput(
            label_text="T. Op.:",
            initial_hh_mm="00:00",
            tag_hours=None,
            tag_minutes=None,
            local_timer_id="op_cb", 
            numpad_title="Tiempo Op. Cámara de Balance",
            parent=self.control_area
        )
        self.input_t_BalanceChamber.request_time_numpad.connect(self.open_time_numpad)
        grid.addWidget(self.input_t_BalanceChamber, 9, 4, 1, 3) 
        
        lbl_remaining_cb_title = QLabel("Rest.:", self.control_area)
        lbl_remaining_cb_title.setStyleSheet(style_lbl)
        grid.addWidget(lbl_remaining_cb_title, 9, 7, alignment=Qt.AlignRight)

        self.lbl_remaining_cb = QLabel("00:00", self.control_area)
        self.lbl_remaining_cb.setStyleSheet(style_lbl_indicator)
        self.lbl_remaining_cb.setAlignment(Qt.AlignCenter)
        self.lbl_remaining_cb.setFixedSize(100,35)
        grid.addWidget(self.lbl_remaining_cb, 9, 8, alignment=Qt.AlignLeft)

        # >>>>>>>>>>>>>>>>>>>>>>>>>> CORRECCIÓN: ASIGNACIÓN DE LABELS A _local_timers_state <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._local_timers_state["op_cb"]["remaining_lbl"] = self.lbl_remaining_cb
        # self._local_timers_state["op_cb"]["elapsed_lbl"] = self.lbl_elapsed_cb
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Ciclos CB <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget
        self.input_cycles_chamber = LabeledParameterWidget( 
            label_text="Ciclos",
            tag="balanceChamberCycleSet",
            value="0",
            units="CB",
            numpad_title="Ciclos CB",
            is_editable=True,
            parent=self.control_area
        )
        self.input_cycles_chamber.request_numpad.connect(self.open_numpad)
        grid.addWidget(self.input_cycles_chamber, 9, 10, 1, 2) 

        # >>>>>>>>>>>>>>>>>>>>>>>>>> Flujo CB <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Convertido a LabeledParameterWidget. Usa un manejador especial para la conversión Flujo <-> Ciclos.
        self.input_flow_cb = LabeledParameterWidget( 
            label_text="Flujo",
            tag="balanceChamberSetTiming", 
            value="0",
            units="ml/min",
            numpad_title="Flujo CB (ml/min)",
            is_editable=True,
            parent=self.control_area
        )
        # Conectado a un manejador especial que gestiona la conversión de Flujo a Ciclos
        self.input_flow_cb.request_numpad.connect(lambda tag_var, widget_ref, title_str: self._handle_flow_cb_input(tag_var, widget_ref, title_str))

        #self.input_flow_cb.request_numpad.connect(lambda tag_var, widget_ref, title_str: self._handle_flow_cb_input(tag_var, widget_ref, title_str))
        grid.addWidget(self.input_flow_cb, 9, 13, 1, 2) 

        grid.setColumnStretch(0, 1)   
        grid.setColumnStretch(16, 1)  
        grid.setColumnMinimumWidth(3, 70)   
        grid.setColumnMinimumWidth(13, 110)
        grid.setColumnMinimumWidth(16, 120)

        layout.addWidget(self.control_area, 0, 0)
        # ==================================================================
        #          AREA 2: INDICADORES LED
        # ==================================================================
        self.ind_area = QWidget(self)
        self.ind_area.setFixedSize(180,726)
        grid_ind_area = QGridLayout(self.ind_area)
        grid_ind_area.setSpacing(10)
        grid_ind_area.setContentsMargins(10, 10,10, 10)

        led_nombres = ["B. Sangre","B. Dializante","B. Heparina","B. UltraF","Purga de\n aire","C.Balance","A. sangre","C.Deaereación","Fin de\n ciclos","Protec.\n Resist.","S.Dializante","Nivel de\ntanque"]   
        led_tags = [
            "bloodPumpStartButton",       
            "dialyserPumpStartButton",    
            "heparinePumpsStartButton",   
            "dialyUltraFPumpStartButt",   
            "dialyPurgePumpStartButt",    
            "dialiserBalChambStrButt",    
            "airBubbleInBloodDetected",   
            "dialyDeaerChamLevSwitch",    
            "dialyBalanceChambCycleEnd",  
            "watterTankHeaterProtect",    
            "bloodInDialyCircDetected",   
            "dialyTankHiLevelSwitch"      
        ]

        self.leds = []
        for i, nombre in enumerate(led_nombres):
            lbl = QLabel(nombre, self.ind_area)
            lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid_ind_area.addWidget(lbl, i, 0)

            led = LED(self.ind_area)
            led.setFixedSize(45, 45)
            grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.leds.append((led, led_tags[i])) # Guardar LED y su tag para fácil actualización

        layout.addWidget(self.ind_area, 0, 1, 2, 1) # Modificado para ocupar 2 filas en el layout principal

        # ==============================================================================================
        # AREA 3: VÁLVULAS
        # ==============================================================================================
        self.ctrl_valvulas = QWidget(self)
        self.ctrl_valvulas.setFixedSize(1300,180) # Asumiendo un ancho fijo para esta sección
        layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas) 
        layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
        layout_ctrl_valvulas.setSpacing(5)
        
        self.container_mop = QFrame(self.ctrl_valvulas)
        self.container_mop.setFixedSize(100,180)
        self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
        layout_mop = QVBoxLayout(self.container_mop) 
       
        lbl_modo = QLabel("Modo de \n Op.", self.container_mop)
        lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
        lbl_modo.setAlignment(Qt.AlignCenter)
        
        self.toggle_modo = ToggleSwitch(width=60, height=30, active_color="#facc15", parent=self.container_mop) 
        self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))

        layout_mop.addStretch()
        layout_mop.addWidget(lbl_modo)
        layout_mop.setSpacing(10)
        layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
        layout_mop.addStretch()
        
        layout_ctrl_valvulas.addWidget(self.container_mop)

        self.container_val = QWidget(self.ctrl_valvulas)
        grid_valvulas_area = QGridLayout(self.container_val)
        grid_valvulas_area.setContentsMargins(0, 0, 0, 0)
        grid_valvulas_area.setSpacing(10)
       
        valvulas_tag = [
            (0, 0, "dialyInputFilterCutButt", "SV_24 E. Filtro UF"),
            (0, 1, "dialyOutputFilterCutButt", "SV_25 S. Filtro UF"),
            (0, 2, "dialyBypassFilterButt", "SV_26 Bypass UF"),
            (0, 3, "dialyWaterInletValveButt", "SV_27 E. Agua"),
            (1, 0, "dialyRecirculatValveButt", "SV_39 Recirculación"),
            (1, 1, "dialyAirVentSepChambButt", "SV_43 Venteo CS Aire"),
            (1, 2, "dialyHotChambValveButt", "SV_50 C. Caliente"),
            (1, 3, "dialyWaterDrainValveButt", "SV_30 Drenaje"),
        ]
        self.valvulas_map = {}

        for r, c, tag, desc in valvulas_tag:
            parts = desc.split(" ",1)
            codigo = parts[0]
            texto = parts[1] if len(parts) > 1 else ""

            card = ValveCard(codigo, texto, parent=self.container_val)
            self.valvulas_map[tag] = card
            grid_valvulas_area.addWidget(card, r, c)
            card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

        layout_ctrl_valvulas.addWidget(self.container_val)
        layout.addWidget(self.ctrl_valvulas, 10, 0, 1, 1) 


    def _actualizar_toggle(self, toggle, valor):
        """Función auxiliar para actualizar toggle sin disparar señal"""
        estado_nuevo = (valor > 0)
        
        # Uso isChecked() en ToggleSwitch para mayor consistencia
        if toggle.is_checked() != estado_nuevo: 
            toggle.blockSignals(True)  # Importante: Evita bucle infinito con el PLC
            toggle.setChecked(estado_nuevo)
            toggle.blockSignals(False)

    def actualizar_valores(self, nuevos_valores):
        """
        Actualiza todos los widgets de la pantalla con los nuevos valores del PLC.
        """
        self.valores = nuevos_valores
        
        # ACTUALIZAR LEDS
        for led, tag in self.leds: # Ahora self.leds guarda (LED_widget, tag_asociado)
            valor = self.valores.get(tag, 0.0)
            estado = 'on' if valor > 0 else 'off'
            led.set_state(estado) # Se llama set_state siempre, el LED decide si cambia

        # ACTUALIZAR VÁLVULAS
        for tag, card in self.valvulas_map.items():
            val = self.valores.get(tag, 0.0)
            nuevo_estado = True if val > 0 else False
            if card.toggle.is_checked() != nuevo_estado: # Usar isChecked()
                card.toggle.blockSignals(True)
                card.toggle.setChecked(nuevo_estado)
                card.toggle.blockSignals(False)
        
        # ACTUALIZAR CALCULOS Y SUS DISPLAY (CON HOLD-OFF)
        # -----------------------------------------------------------------------------------------
        # Flujo CB: El PLC envía 'balanceChamberSetTiming' (ciclos), la UI muestra 'ml/min'.
        # Necesitamos convertir ciclos a ml/min para la UI.
        cycle_val_from_control = self.valores.get("balanceChamberSetTiming", 0.0) # Obtener ciclos del PLC
        try:
            calc_flow_cb_for_ui = convertir_ciclos_a_flujo(cycle_val_from_control)
        except Exception as e:
            print(f"[ERROR] Falló la conversión de ciclos a flujo para CB: {e}")
            calc_flow_cb_for_ui = 0.0
        # self.input_flow_cb es un LabeledParameterWidget, usar update_input_val.
        # Le pasamos el tag "balanceChamberCycleSet" para el hold-off, pero el valor a mostrar es calc_flow_cb_for_ui.
        self.update_input_val(self.input_flow_cb, "balanceChamberSetTiming", precision=1, display_value=calc_flow_cb_for_ui)
        
       
        # Necesitamos convertir ml/min a L/h para la UI.
        uf_flow_ml_min_from_plc = self.valores.get("ultraFilterPumpSpeed", 0.0)
        try:
            calc_uf_flow_liters_h_for_ui = convertir_ml_min_a_litros_h(uf_flow_ml_min_from_plc)
        except Exception as e:
            print(f"[ERROR] Falló la conversión de ml/min a L/h para UF: {e}")
            calc_uf_flow_liters_h_for_ui = 0.0
        # self.lbl_input_indUF es un LabeledParameterWidget.
        # Le pasamos el tag "ultraFilterPumpSpeed" para el hold-off, pero el valor a mostrar es calc_uf_flow_liters_h_for_ui.
        self.update_input_val(self.lbl_input_indUF, "ultraFilterPumpSpeed", precision=1, display_value=calc_uf_flow_liters_h_for_ui)

        # -----------------------------------------------------------------------------------------
        # ACTUALIZAR CAMPOS DE ENTRADA NUMÉRICOS (LabeledParameterWidget)
        self.update_input_val(self.input_flujo_sangre,"bloodFlowControlSetPoint" )        
        self.update_input_val(self.input_dosis_hep, "heparineTherapyDosage")
        self.update_input_val(self.input_dosis_bolo, "heparineBolusQuantity")
        self.update_input_val(self.input_size_syringe,"heparineSyrinjeScaleSize")
        self.update_input_val(self.lbl_input_indSDializante, "dialyFlowControlOutput")
        self.update_input_val(self.lbl_indPurga, "dialyDeaerControlOutput")
        self.update_input_val(self.input_cycles_chamber,"balanceChamberCycleSet" )
        
        # ACTUALIZAR INDICADORES NUMÉRICOS (LabeledParameterWidget)
        self.update_label_val(self.lbl_velocidad_val, "bloodSpeedVariableData" )
        self.update_label_val(self.lbl_indBNa, "bicarbonatePumpSpeed" )
        self.update_label_val(self.lbl_indBAC, "citricAcidPumpSpeed" )        
        self.update_label_val(self.indHeparinCurrentDosage, "heparineCurrentDosage" )

        # >>>>>>>>>>>>>>>>>>>>>>>>>> ACTUALIZAR CAMPOS DE TIEMPO (LabeledTimeInput) <<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Nota: Los campos de tiempo que no envían tags al PLC (tag_hours=None, tag_minutes=None)
        # serán actualizados con 00:00 si no hay una duración configurada, o mantendrán su valor local.
        # El duration_ms en _local_timers_state se actualiza aquí para todos los campos de tiempo.
        self.update_time_input_val(self.input_t_BloodPump, tag_hours=None, tag_minutes=None, local_timer_id="op_pb")
        self.update_time_input_val(self.input_t_therapy, "heparineTherapyHours", "heparineTherapyMinutes", local_timer_id="op_ph")
        self.update_time_input_val(self.lbl_tiempo_OpBD, tag_hours=None, tag_minutes=None, local_timer_id="op_pd")
        self.update_time_input_val(self.lbl_tiempo_opBUF, tag_hours=None, tag_minutes=None, local_timer_id="op_puf")
        self.update_time_input_val(self.input_t_BalanceChamber, tag_hours=None, tag_minutes=None, local_timer_id="op_cb")
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # ACTUALIZAR TOGGLES DE BOMBAS 
        self._actualizar_toggle(self.toggle_sangre, self.valores.get("bloodPumpStartButton", 0.0))
        self._actualizar_toggle(self.toggle_heparina, self.valores.get("heparinePumpsStartButton", 0.0))
        self._actualizar_toggle(self.toggle_dializante, self.valores.get("dialyserPumpStartButton", 0.0))
        self._actualizar_toggle(self.toggle_acidocitrico, self.valores.get("dialyCitricAcPumpStartButt", 0.0))
        self._actualizar_toggle(self.toggle_Na, self.valores.get("dialyBicarbonPumpStartButt", 0.0))
        self._actualizar_toggle(self.toggle_purga, self.valores.get("dialyPurgePumpStartButt", 0.0))
        self._actualizar_toggle(self.toggle_uf, self.valores.get("dialyUltraFPumpStartButt", 0.0))
        self._actualizar_toggle(self.toggle_modo, self.valores.get("dialyCircuitElementsOpSel", 0.0))
        self._actualizar_toggle(self.toggle_cb,self.valores.get("dialiserBalChambStrButt",0.0))

    def update_time_input_val(self, time_input_widget, tag_hours: str, tag_minutes: str, local_timer_id: str):
        """
        Actualiza un LabeledTimeInput o ClickableLineEdit con un valor HH:MM
        proveniente del PLC, respetando el "hold-off" si el usuario acaba de escribir.
        """
        # --- 1. Aplicar lógica de "hold-off" para evitar el parpadeo ---
        current_time = QDateTime.currentMSecsSinceEpoch()
        
        # Obtenemos el tiempo hasta el que se debe mantener el "hold-off" para cada tag.
        # Si un tag es None, su hold_off_time es 0 (no hay hold-off activo para ese tag).
        hold_off_h_time = self._write_hold_off.get(tag_hours, 0) if tag_hours else 0
        hold_off_m_time = self._write_hold_off.get(tag_minutes, 0) if tag_minutes else 0

        # Si el tiempo actual es menor que cualquiera de los tiempos de "hold-off" registrados,
        # NO actualizamos la UI con el valor del PLC aún.
        if current_time < hold_off_h_time or current_time < hold_off_m_time:
            return
        
        if tag_hours is None and tag_minutes is None:

            return # Salir temprano
        
        hours = int(self.valores.get(tag_hours, 0)) if tag_hours else 0
        minutes = int(self.valores.get(tag_minutes, 0)) if tag_minutes else 0
        
        
        if isinstance(time_input_widget, LabeledTimeInput):
            time_input_widget.set_time_value(hours, minutes)
        elif hasattr(time_input_widget, 'setText'): 
            # Para ClickableLineEdit (o QLineEdit). Solo si no tiene foco.
            if not hasattr(time_input_widget, 'hasFocus') or not time_input_widget.hasFocus(): 
                time_input_widget.setText(f"{hours:02d}:{minutes:02d}")
        else:
            print(f"[ADVERTENCIA] update_time_input_val recibió un tipo de widget no soportado para tags de tiempo: ({tag_hours}, {tag_minutes}).")
        
        if local_timer_id and local_timer_id in self._local_timers_state:
            total_ms = (hours * 3600 + minutes * 60) * 1000
            self._local_timers_state[local_timer_id]["duration_ms"] = total_ms


    def update_input_val(self, widget, tag, precision=1, display_value=None):
        """
        Actualiza el valor en la interfaz. 
        Detecta si es un widget simple (QLineEdit/ClickableLineEdit) o el compuesto (LabeledParameterWidget).
        Aplica hold-off. Permite un display_value opcional para valores calculados.
        """
        # 1. Aplicar lógica de "hold-off" para evitar el parpadeo
        current_time = QDateTime.currentMSecsSinceEpoch()
        hold_until = self._write_hold_off.get(tag, 0)
        
        if current_time < hold_until:
            return

        # 2. Obtener valor: Usar display_value si se proporciona (para valores calculados), 
        #    sino obtenerlo del diccionario de valores del PLC.
        value_to_display = display_value if display_value is not None else self.valores.get(tag, 0.0)

        # 3. Actualizar según el tipo de widget
        if isinstance(widget, LabeledParameterWidget):
            widget.set_value(value_to_display)
        
        elif hasattr(widget, "setText"):
            # Para ClickableLineEdit (o QLineEdit). Solo si no tiene foco.
            if hasattr(widget, "hasFocus") and widget.hasFocus():
                return            
            widget.setText(f"{value_to_display:.{precision}f}")            
        else:
            print(f"[ERROR UI] El widget para el tag '{tag}' no soporta setText ni set_value.")

    def update_label_val(self, label_widget, tag, precision=1):
        """
        Actualiza un widget indicador (QLabel o LabeledParameterWidget no editable).
        Siempre actualiza, ya que estos widgets no tienen foco para edición.
        """
        value = self.valores.get(tag, 0.0)
        
        if isinstance(label_widget, LabeledParameterWidget):
            label_widget.set_value(value) 
        elif hasattr(label_widget, 'setText'): # Para QLabel o ClickableLineEdit que actúan como indicadores
            label_widget.setText(f"{value:.{precision}f}")
        else:
            print(f"[ADVERTENCIA] update_label_val recibió un tipo de widget no soportado para el tag '{tag}'.")
            
    def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
        if activado:
            print(f"[BOMBA] Arrancando {tag_start}")
            self.escribir_comando(tag_start, True)
            self.escribir_comando(tag_stop, False) 
            
            if timer_id and timer_id in self._local_timers_state:
                state = self._local_timers_state[timer_id]
                total_ms_duration = state["duration_ms"] # Duración configurada (del PLC o numpad)

                if total_ms_duration > 0:
                    state["active"] = True 
                    state["start_ms"] = QDateTime.currentMSecsSinceEpoch() # Marca el inicio del timer
                    
                    timer_obj = getattr(self, f"timer_{timer_id}") 
                    timer_obj.start(total_ms_duration) # Inicia el QTimer de un solo disparo

                    print(f"[APP_TIMER] Iniciando timer '{timer_id}' por {total_ms_duration} ms.")
                else:
                    print(f"[APP_TIMER] Advertencia: Timer '{timer_id}' no tiene duración establecida (0 ms). No se inició.")

        else: # Bomba desactivada
            print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
            self.escribir_comando(tag_stop, True) 
            self.escribir_comando(tag_start, False)
            
            if timer_id and timer_id in self._local_timers_state:
                state = self._local_timers_state[timer_id]
                if state["active"]: # Solo si estaba activo, entonces lo detengo
                    state["active"] = False 
                    
                    timer_obj = getattr(self, f"timer_{timer_id}")
                    if timer_obj.isActive():
                        timer_obj.stop()
                    
                    # Restablecer visualmente el tiempo transcurrido y restante al valor configurado
                    if state["elapsed_lbl"] is not None: 
                        state["elapsed_lbl"].setText("00:00")
                        
                    if state["remaining_lbl"] is not None: 
                        h_config = state["duration_ms"] // 3600000
                        m_config = (state["duration_ms"] % 3600000) // 60000
                        state["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}") 

                    print(f"[APP_TIMER] Deteniendo timer '{timer_id}'.")

    def escribir_setpoint(self, tag, widget_input):
        """
        Escribe un valor numérico a un tag específico del mapa de variales.
        Maneja diferentes tipos de widgets de entrada.
        """
        try:
            texto = ""
            # Leer el valor del widget de entrada
            if isinstance(widget_input, LabeledParameterWidget):
                texto = widget_input.get_value() 
            elif isinstance(widget_input, LabeledTimeInput): 
                # LabeledTimeInput no envía su texto directamente al PLC como un float general.
                # Se espera que open_time_numpad lo descomponga en horas y minutos
                # y llame a escribir_setpoint con TempInput(h) o TempInput(m).
                # Por lo tanto, aquí, solo tomamos el texto para fines de log/error.
                texto = widget_input.get_time_value()
            elif hasattr(widget_input, 'text'): # Para ClickableLineEdit, QLineEdit
                texto = widget_input.text()
            elif hasattr(widget_input, 'valor'): # Para la clase TempInput
                texto = str(widget_input.valor)
            else:
                print(f"[ERROR] Tipo de widget desconocido para el tag '{tag}'. No se puede leer el valor.")
                QMessageBox.critical(self, "Error Interno", f"Tipo de widget desconocido para leer valor de '{tag}'.")
                return

            texto = texto.replace(',', '.') # Asegurar formato de punto decimal
            
            if not texto:                 
                current_value = self.valores.get(tag, 0.0)
                # Si el campo está vacío, restaurar el valor actual del PLC.
                if isinstance(widget_input, LabeledParameterWidget):
                    widget_input.set_value(current_value) 
                elif hasattr(widget_input, 'setText'):
                    widget_input.setText(f"{current_value:.1f}") 
                return 
                
            valor = float(texto)
            print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
            target_group = -1
            target_id = -1
            found = False
            
            for group_key, variables_in_group in VARIABLES.items():                
                if isinstance(variables_in_group, dict): 
                    for var_id, info in variables_in_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found: break 
            
            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:                      
                        # Asumiendo que serial.escribir_double puede manejar tanto float como int.
                        self.parent_window.serial.escribir_double(target_group, target_id, valor)
                    else:
                        print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
                        QMessageBox.warning(self, "Comunicación", f"El serial no está conectado. Valor {valor} para {tag} no enviado.")
                else:
                    print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
                    QMessageBox.warning(self, "Error de Configuración", f"La variable '{tag}' es de solo lectura. No se pudo modificar.")
            else:
                print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")
                QMessageBox.critical(self, "Error de Configuración", f"No se encontró el tag '{tag}' en el mapa de variables. Contacte a soporte.")

            if hasattr(widget_input, 'clearFocus'): # Llamar clearFocus solo si el widget lo tiene
                widget_input.clearFocus()

        except ValueError:
            # Obtener el texto del widget para el mensaje de error
            display_text = ""
            if isinstance(widget_input, LabeledParameterWidget):
                display_text = widget_input.get_value()
            elif hasattr(widget_input, 'text'):
                display_text = widget_input.text()
            elif hasattr(widget_input, 'valor'):
                display_text = str(widget_input.valor)
            print(f"[ERROR] Valor numérico inválido en input para {tag}: {display_text}")
            QMessageBox.warning(self, "Error de Entrada", f"El valor '{display_text}' no es un número válido para {tag}.")
        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
            QMessageBox.critical(self, "Error Crítico", f"Error inesperado al escribir {tag}: {e}")
  
    def escribir_comando(self, tag, estado):
        """
        Envía un comando booleano a un tag específico del PLC.
        """
        print(f"[COMANDO] Usuario cambió {tag} a {estado}")
        direccion = -1
        # Busca el tag en el grupo 0x01 (comandos/estados)
        if 0x01 in VARIABLES:
            for id_var, info in VARIABLES[0x01].items():
                if info.get("tag") == tag:
                    direccion = id_var
                    break
        
        if direccion != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:
                try:
                    if self.parent_window.serial.conectado:
                        print(f" -> Enviando: Addr {direccion} Val {estado}")
                        # Asumiendo que serial.escribir_booleano maneja booleanos directamente
                        self.parent_window.serial.escribir_booleano(direccion, estado)
                    else:
                        print(" -> Error: Serial no conectado")
                        QMessageBox.warning(self, "Error de Comunicación", "El puerto serial no está conectado. No se pudo enviar el comando.")
                except AttributeError:
                    print(f"[INFO] Fallo en envío: Addr {direccion} Val {estado}")
                    QMessageBox.warning(self, "Error de Comunicación", "Fallo al enviar comando a través del serial. Verifique la conexión.")
            else:
                 print(f"[INFO] Error no se completo la escritura: Addr {direccion} Val {estado}")
                 QMessageBox.warning(self, "Error Interno", "No se encontró el objeto de comunicación serial para enviar el comando.")
        else:
            print(f" -> Error: No se encontró ID para el tag '{tag}'")
            QMessageBox.critical(self, "Error de Configuración", f"No se encontró la definición de la variable '{tag}' en el mapa de variables. Contacte a soporte.")

    def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
        """
        Abre el teclado numérico para la entrada de valores decimales.
        Aplica la lógica de "hold-off" para evitar parpadeo.
        """
        # 1. OBTENER EL VALOR ACTUAL del widget
        if isinstance(widget_input, LabeledParameterWidget):
            act_value = widget_input.get_value()
        else: # Para ClickableLineEdit si aún se usa alguno
            act_value = widget_input.text()

        dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
        
        if dialog.exec(): 
            new_value = dialog.get_value() 
            
            # 2. ACTUALIZAR LA INTERFAZ VISUALMENTE (feedback inmediato)
            if isinstance(widget_input, LabeledParameterWidget):
                widget_input.set_value(new_value)
            else: # Para ClickableLineEdit
                widget_input.setText(str(new_value))            
            
            # 3. ENVIAR EL CAMBIO AL PLC O LÓGICA INTERNA
            self.escribir_setpoint(tag, widget_input)

            # >>>>>>>>>>>>>>>>>>>>>>>>>> APLICAR HOLD-OFF <<<<<<<<<<<<<<<<<<<<<<<<<<<<
            # Esto evita que el valor recién editado sea sobrescrito por una lectura del PLC durante un tiempo.
            current_timestamp = QDateTime.currentMSecsSinceEpoch()
            hold_off_duration_ms = 3000 # 3 segundos de espera para que el PLC procese y responda
            self._write_hold_off[tag] = current_timestamp + hold_off_duration_ms
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def open_time_numpad(self, time_input_widget, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
        """
        Abre el teclado numérico para la entrada de valores de tiempo (HH:MM).
        Aplica la lógica de "hold-off" para evitar parpadeo.
        """
        # --- 1. Leer el valor inicial del widget ---
        if isinstance(time_input_widget, LabeledTimeInput):
            texto_actual = time_input_widget.get_time_value()
        else: # Para ClickableLineEdit (si aún se usa alguno)
            texto_actual = time_input_widget.text()

        dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

        if dialog.exec():
            h, m = dialog.get_hours_minutes()
            
            # --- 2. Actualizar visualmente el widget ---
            if isinstance(time_input_widget, LabeledTimeInput):
                time_input_widget.set_time_value(h, m)
            else: # Para ClickableLineEdit
                time_input_widget.setText(f"{h:02d}:{m:02d}")
            
            total_ms = (h * 3600 + m * 60) * 1000

            current_timestamp = QDateTime.currentMSecsSinceEpoch()
            hold_off_duration_ms = 3000 # 3 segundos de hold-off

            # --- 3. Lógica para escribir a la Máquina de Hemodiálisis (PLC) ---
            if tag_hours and tag_minutes:
                print(f"[MH_WRITE] Enviando horas ({h}) al tag: {tag_hours}")
                fake_widget_h = TempInput(h) # Usar TempInput para pasar el valor int
                self.escribir_setpoint(tag_hours, fake_widget_h)
                self._write_hold_off[tag_hours] = current_timestamp + hold_off_duration_ms

                print(f"[MH_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}")
                fake_widget_m = TempInput(m) # Usar TempInput para pasar el valor int
                self.escribir_setpoint(tag_minutes, fake_widget_m)
                self._write_hold_off[tag_minutes] = current_timestamp + hold_off_duration_ms
            elif tag_hours or tag_minutes:
                print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")
                QMessageBox.warning(self, "Configuración Parcial", "Se necesitan tags para horas Y minutos para escribir el tiempo al PLC.")

            # --- 4. Lógica para configurar QTimer locales de la aplicación ---
            if local_timer_id and local_timer_id in self._local_timers_state:
                state = self._local_timers_state[local_timer_id] 
                state["duration_ms"] = total_ms # Guarda la duración total para el timer local
                
                # Al configurar una nueva duración, reseteamos las etiquetas de tiempo visibles.
                if state["elapsed_lbl"] is not None: 
                    state["elapsed_lbl"].setText("00:00")
                if state["remaining_lbl"] is not None: 
                    state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

                print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")
    
    # --- Métodos de detención de bombas por Timeout ---
    def _stop_blood_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_pb' finalizado. Deteniendo Bomba de Sangre.")
        self.timer_op_pb.stop()
        self._local_timers_state["op_pb"]["active"] = False

        self.escribir_comando("bloodPumpStopButton", True)  
        self.escribir_comando("bloodPumpStartButton", False) 

        self.toggle_sangre.blockSignals(True)
        self.toggle_sangre.setChecked(False)
        self.toggle_sangre.blockSignals(False)

        # Restablecer visualmente el tiempo transcurrido y restante
        if self._local_timers_state["op_pb"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_pb"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_pb"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_pb"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_pb"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_pb"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_dialysate_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_pd' finalizado. Deteniendo Bomba de Dializante.")
        self.timer_op_pd.stop()
        self._local_timers_state["op_pd"]["active"] = False

        self.escribir_comando("dialyserPumpStopButton", True)
        self.escribir_comando("dialyserPumpStartButton", False)

        self.toggle_dializante.blockSignals(True)
        self.toggle_dializante.setChecked(False)
        self.toggle_dializante.blockSignals(False)

        if self._local_timers_state["op_pd"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_pd"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_pd"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_pd"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_pd"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_pd"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_uf_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_puf' finalizado. Deteniendo Bomba de Ultrafiltración.")
        self.timer_op_puf.stop()
        self._local_timers_state["op_puf"]["active"] = False

        self.escribir_comando("dialyUltraFPumpStoptButt", True)
        self.escribir_comando("dialyUltraFPumpStartButt", False)

        self.toggle_uf.blockSignals(True)
        self.toggle_uf.setChecked(False)
        self.toggle_uf.blockSignals(False)

        if self._local_timers_state["op_puf"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_puf"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_puf"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_puf"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_puf"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_puf"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_heparin_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_ph' finalizado. Deteniendo Bomba de Heparina.")
        self.timer_op_ph.stop()
        self._local_timers_state["op_ph"]["active"] = False

        self.escribir_comando("heparinePumpsStopButton", True)
        self.escribir_comando("heparinePumpsStartButton", False)

        self.toggle_heparina.blockSignals(True)
        self.toggle_heparina.setChecked(False)
        self.toggle_heparina.blockSignals(False)

        if self._local_timers_state["op_ph"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_ph"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_ph"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_ph"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_ph"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_ph"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_balance_chamber_on_timeout(self):
        print("[APP_TIMER] Timer 'op_cb' finalizado. Deteniendo Cámara de Balance.")
        self.timer_op_cb.stop()
        self._local_timers_state["op_cb"]["active"] = False

        self.escribir_comando("dialiserBalChambStpButt", True)
        self.escribir_comando("dialiserBalChambStrButt", False)

        self.toggle_cb.blockSignals(True)
        self.toggle_cb.setChecked(False)
        self.toggle_cb.blockSignals(False)

        if self._local_timers_state["op_cb"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_cb"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_cb"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_cb"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_cb"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_cb"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _format_ms_to_hh_mm(self, ms):
        """Formatea milisegundos a HH:MM."""
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def _update_local_time_displays(self):
        """
        Actualiza las etiquetas de tiempo transcurrido y restante para los timers locales.
        Esta función se llama periódicamente por _display_update_timer.
        """
        current_ms = QDateTime.currentMSecsSinceEpoch()
        
        for timer_id, state in self._local_timers_state.items():
            # Si el timer está ACTIVO
            if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
                elapsed_ms = current_ms - state["start_ms"]
                remaining_ms = state["duration_ms"] - elapsed_ms

                if remaining_ms < 0: # El timer debería haber finalizado
                    remaining_ms = 0
                    # Forzar la llamada a la función de _stop para este timer
                    stop_method = getattr(self, f"_stop_{timer_id}_on_timeout", None)
                    if stop_method:
                        stop_method()
                    else:
                        print(f"[ERROR] No se encontró método _stop para timer_id: {timer_id}")
                        # Asegurar que el estado se marque como inactivo
                        state["active"] = False
                        
                # Actualizar las etiquetas visualmente, si están asignadas
                if state["elapsed_lbl"] is not None:
                    state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
                
                if state["remaining_lbl"] is not None:
                    state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))

            # Si el timer está INACTIVO
            elif not state["active"]:
                # Resetear transcurrido (Solo si existe la etiqueta y no es "00:00")
                if state["elapsed_lbl"] is not None and state["elapsed_lbl"].text() != "00:00":
                    state["elapsed_lbl"].setText("00:00")
                
                # Resetear restante al valor configurado (Solo si existe la etiqueta y es diferente)
                if state["remaining_lbl"] is not None:
                    h_config = state["duration_ms"] // 3600000
                    m_config = (state["duration_ms"] % 3600000) // 60000
                    config_str = f"{h_config:02d}:{m_config:02d}"
                    
                    if state["remaining_lbl"].text() != config_str:
                         state["remaining_lbl"].setText(config_str)

   
    def _handle_flow_cb_input(self, tag: str, widget_input: LabeledParameterWidget, title: str):
        """
        Manejador especial para el flujo de la cámara de balance.
        Se introduce como flujo (ml/min) en la UI, pero se convierte a ciclos
        y se envía como ciclos al control.
        """
        # 1. Obtener el valor actual (del LabeledParameterWidget)
        current_flow_text = widget_input.get_value()
        numpad_dialog =  NumpadDialog(self, initial_value=current_flow_text, title=title)
        
        if numpad_dialog.exec():
            new_flow_value_num = numpad_dialog.get_value()
            
            # 2. Actualizar visualmente el LabeledParameterWidget con el nuevo flujo
            widget_input.set_value(new_flow_value_num)

            try:
                # 3. Convertir flujo a ciclos (para el PLC)
                value_to_send_to_plc = convertir_flujo_a_ciclos(new_flow_value_num)
                
                # 4. Enviar los ciclos al PLC (usando el tag balanceChamberCycleSet)
                # 'tag' aquí es "balanceChamberCycleSet", que es lo que el PLC espera para ciclos.
                self.escribir_setpoint(tag, TempInput(value_to_send_to_plc)) 
                
                # 5. Aplicar lógica de HOLD-OFF al tag que se escribe al PLC
                current_timestamp = QDateTime.currentMSecsSinceEpoch()
                hold_off_duration_ms = 3000
                self._write_hold_off[tag] = current_timestamp + hold_off_duration_ms

            except ValueError:
                print(f"[ERROR] El valor '{new_flow_value_num}' no es un número válido para conversión a ciclos.")
                QMessageBox.warning(self, "Error de Entrada", "El valor introducido no es válido para el cálculo de ciclos.")
            except Exception as e:
                print(f"[ERROR] Falló la conversión o escritura del Flujo CB: {e}")
                QMessageBox.critical(self, "Error Crítico", f"Error inesperado al procesar flujo de CB: {e}")


    def _handle_flow_uf_input(self, tag, widget_input, title):
        """
        Manejador especial para el flujo de ultrafiltración.
        Se introduce como L/h en la UI, pero se convierte a ml/min y se envía al PLC.
        """
        # 1. Obtener el valor actual (del LabeledParameterWidget)
        current_flow_uf_text = widget_input.get_value()
        numpad_dialog = NumpadDialog(self, initial_value=current_flow_uf_text, title=title)

        if numpad_dialog.exec():
            new_flow_uf_liters_h = numpad_dialog.get_value()
            
            # 2. Actualizar visualmente el LabeledParameterWidget con el nuevo flujo en L/h
            widget_input.set_value(new_flow_uf_liters_h)

            try:
                # 3. Convertir L/h a ml/min (para el PLC)
                value_to_send_to_plc = convertir_litros_h_a_ml_min(new_flow_uf_liters_h)
                
                # 4. Enviar los ml/min al PLC (usando el tag ultraFilterPumpSpeed)
                self.escribir_setpoint(tag, TempInput(value_to_send_to_plc))
                
                # 5. Aplicar lógica de HOLD-OFF al tag que se escribe al PLC
                current_timestamp = QDateTime.currentMSecsSinceEpoch()
                hold_off_duration_ms = 3000
                self._write_hold_off[tag] = current_timestamp + hold_off_duration_ms

            except ValueError:
                print(f"[ERROR] El valor '{new_flow_uf_liters_h}' no es válido para conversión.")
                QMessageBox.warning(self, "Error de Entrada", "El valor introducido no es válido para el cálculo de ultrafiltración.")
            except Exception as e:
                print(f"[ERROR] Falló la conversión o escritura en parámetro UF: {e}")
                QMessageBox.critical(self, "Error Crítico", f"Error inesperado al procesar flujo de UF: {e}")


    # def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
    #     """
    #     1. Abre el TimeNumpadDialog con el valor actual del widget.
    #     2. Al aceptar, actualiza el widget visual a "HH:MM".
    #     3. Desglosa Horas y Minutos.
    #     4. Si tiene tags, llama a escribir_setpoint para el PLC.
    #     5. Si tiene local_timer_id, configura el QTimer correspondiente.
    #     """
    #     texto_actual = widget_input.text()
    #     dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

    #     if dialog.exec():
    #         h, m = dialog.get_hours_minutes()
    #         widget_input.setText(f"{h:02d}:{m:02d}")
            
    #         # Calcular duración total en milisegundos
    #         total_ms = (h * 3600 + m * 60) * 1000

    #         # 1. Lógica para escribir a la Máquina de Hemodiálisis
    #         if tag_hours and tag_minutes:
    #             print(f"[MH_WRITE] Enviando horas ({h}) al tag: {tag_hours}") # Máquina de hemodiálisis
    #             fake_widget_h = TempInput(h) 
    #             self.escribir_setpoint(tag_hours, fake_widget_h)

    #             print(f"[MH_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}") # Máquina de Hemodiálisis
    #             fake_widget_m = TempInput(m)
    #             self.escribir_setpoint(tag_minutes, fake_widget_m)
    #         elif tag_hours or tag_minutes:
    #             print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

    #         # 2. Lógica para configurar QTimer locales de la aplicación
    #         if local_timer_id:
    #             state = self._local_timers_state[local_timer_id] # Obtiene la referencia al estado del timer
    #             state["duration_ms"] = total_ms # Guarda la duración total
                
    #             # ### RESETEAR LAS ETIQUETAS DE TIEMPO al configurar una nueva duración
    #             #if state["elapsed_lbl"]: state["elapsed_lbl"].setText("00:00")
    #             #if state["remaining_lbl"]: 
    #              #   state["remaining_lbl"].setText(f"{h:02d}:{m:02d}") # Muestra la duración configurada
    #             if state["elapsed_lbl"] is not None: 
    #                 state["elapsed_lbl"].setText("00:00")
                
    #             if state["remaining_lbl"] is not None: 
    #                 state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

    #             print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")
    
    def _stop_blood_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_pb' finalizado. Deteniendo Bomba de Sangre.")
        self.timer_op_pb.stop()
        self._local_timers_state["op_pb"]["active"] = False

        # 1. Enviar directamente el comando de parada a la Máquina de Hemodiálisis
        self.escribir_comando("bloodPumpStopButton", True)  
        self.escribir_comando("bloodPumpStartButton", False) 

        # 2. Actualizar el Toggle en la UI, bloqueando señales para evitar re-entradas
        self.toggle_sangre.blockSignals(True)
        self.toggle_sangre.setChecked(False)
        self.toggle_sangre.blockSignals(False)

        # 3. Resetear las etiquetas de tiempo inmediatamente
        if self._local_timers_state["op_pb"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_pb"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_pb"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_pb"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_pb"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_pb"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_dialysate_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_pd' finalizado. Deteniendo Bomba de Dializante.")
        self.timer_op_pd.stop()
        self._local_timers_state["op_pd"]["active"] = False

        # Enviar comandos a la Máquina
        self.escribir_comando("dialyserPumpStopButton", True)
        self.escribir_comando("dialyserPumpStartButton", False)

        # Actualizar UI localmente
        self.toggle_dializante.blockSignals(True)
        self.toggle_dializante.setChecked(False)
        self.toggle_dializante.blockSignals(False)

        # Resetear tiempo
        if self._local_timers_state["op_pd"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_pd"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_pd"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_pd"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_pd"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_pd"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_uf_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_puf' finalizado. Deteniendo Bomba de Ultrafiltración.")
        self.timer_op_puf.stop()
        self._local_timers_state["op_puf"]["active"] = False

        # Enviar comandos a la Máquina
        self.escribir_comando("dialyUltraFPumpStoptButt", True)
        self.escribir_comando("dialyUltraFPumpStartButt", False)

        # Actualizar UI localmente
        self.toggle_uf.blockSignals(True)
        self.toggle_uf.setChecked(False)
        self.toggle_uf.blockSignals(False)

        # Resetear tiempo
        if self._local_timers_state["op_puf"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_puf"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_puf"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_puf"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_puf"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_puf"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_heparin_pump_on_timeout(self):
        print("[APP_TIMER] Timer 'op_ph' finalizado. Deteniendo Bomba de Heparina.")
        self.timer_op_ph.stop()
        self._local_timers_state["op_ph"]["active"] = False

        # Enviar comandos a la Máquina
        self.escribir_comando("heparinePumpsStopButton", True)
        self.escribir_comando("heparinePumpsStartButton", False)

        # Actualizar UI localmente
        self.toggle_heparina.blockSignals(True)
        self.toggle_heparina.setChecked(False)
        self.toggle_heparina.blockSignals(False)

        # Resetear tiempo
        if self._local_timers_state["op_ph"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_ph"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_ph"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_ph"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_ph"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_ph"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")

    def _stop_balance_chamber_on_timeout(self):
        print("[APP_TIMER] Timer 'op_cb' finalizado. Deteniendo Cámara de Balance.")
        self.timer_op_cb.stop()
        self._local_timers_state["op_cb"]["active"] = False

        # Enviar comandos a la Máquina
        self.escribir_comando("dialiserBalChambStpButt", True)
        self.escribir_comando("dialiserBalChambStrButt", False)

        # Actualizar UI localmente
        self.toggle_cb.blockSignals(True)
        self.toggle_cb.setChecked(False)
        self.toggle_cb.blockSignals(False)

        # Resetear tiempo
        if self._local_timers_state["op_cb"]["elapsed_lbl"] is not None:
            self._local_timers_state["op_cb"]["elapsed_lbl"].setText("00:00")
        if self._local_timers_state["op_cb"]["remaining_lbl"] is not None:
            h_config = self._local_timers_state["op_cb"]["duration_ms"] // 3600000
            m_config = (self._local_timers_state["op_cb"]["duration_ms"] % 3600000) // 60000
            self._local_timers_state["op_cb"]["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}")


    def _format_ms_to_hh_mm(self, ms):
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def _update_local_time_displays(self):
        current_ms = QDateTime.currentMSecsSinceEpoch()
        
        for timer_id, state in self._local_timers_state.items():
            
            # Si el timer está ACTIVO
            if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
                elapsed_ms = current_ms - state["start_ms"]
                remaining_ms = state["duration_ms"] - elapsed_ms

                if remaining_ms < 0:
                    remaining_ms = 0
                    elapsed_ms = state["duration_ms"] 
                
                # VERIFICAMOS SI EXISTE LA ETIQUETA ANTES DE ACTUALIZAR
                if state["elapsed_lbl"] is not None:
                    state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
                
                if state["remaining_lbl"] is not None:
                    state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))

            # Si el timer está INACTIVO
            elif not state["active"]:
                
                # Resetear transcurrido (Solo si existe la etiqueta)
                if state["elapsed_lbl"] is not None and state["elapsed_lbl"].text() != "00:00":
                    state["elapsed_lbl"].setText("00:00")
                
                # Resetear restante al valor configurado
                if state["remaining_lbl"] is not None:
                    h_config = state["duration_ms"] // 3600000
                    m_config = (state["duration_ms"] % 3600000) // 60000
                    config_str = f"{h_config:02d}:{m_config:02d}"
                    
                    if state["remaining_lbl"].text() != config_str:
                         state["remaining_lbl"].setText(config_str)


    # def _handle_flow_cb_input(self):
    #     current_flow_text = self.input_flow_cb.text()
    #     numpad_dialog =  NumpadDialog(self, initial_value=current_flow_text, title="Flujo CB (ml/min)")
        

    #     if numpad_dialog.exec():
    #         new_flow_value_num= numpad_dialog.get_value()
    #         self.input_flow_cb.setText(str(new_flow_value_num))

    #         try:
    #             value = convertir_flujo_a_ciclos(new_flow_value_num)
    #             temp_value = TempInput(value)
    #             self.escribir_setpoint("balanceChamberSetTiming", temp_value)
    #         except ValueError:
    #             print(f"[ERROR] El valor '{new_flow_value_num}' no es un número válido para convertir a ciclos.")
    #         except Exception as e:
    #             print(f"[ERROR] Falló la conversión o escritura del Flujo CB: {e}")


    # def _handle_flow_uf_input(self):
    #     current_flow_uf_text = self.lbl_input_indUF.text()
    #     numpad_dialog = NumpadDialog(self, initial_value=current_flow_uf_text, title="Flujo UF (L/h)")

    #     if numpad_dialog.exec():
    #         new_flow_uf = numpad_dialog.get_value()
    #         self.lbl_input_indUF.setText(str(new_flow_uf))
    #         try:
    #             value = convertir_litros_h_a_ml_min(new_flow_uf)
    #             temp_value = TempInput(value)
    #             self.escribir_setpoint("ultraFilterPumpSpeed", temp_value)
    #         except ValueError:
    #             print(f"[ERROR] el valor  '{new_flow_uf}' es válido")
    #         except Exception as e:
    #             print(f"[ERROR] Fállo la vonversión o escritura en parametro: {e}")



    # def _update_local_time_displays(self):
    #     current_ms = QDateTime.currentMSecsSinceEpoch()
    #     for timer_id, state in self._local_timers_state.items():
    #         if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
    #             elapsed_ms = current_ms - state["start_ms"]
    #             remaining_ms = state["duration_ms"] - elapsed_ms

    #             if remaining_ms < 0:
    #                 remaining_ms = 0
    #                 elapsed_ms = state["duration_ms"] 
                
    #             if state["elapsed_lbl"]:
    #                 state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
    #             if state["remaining_lbl"]:
    #                 state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))
    #         elif not state["active"] and state["elapsed_lbl"] and state["remaining_lbl"]:
    #             if state["elapsed_lbl"].text() != "00:00":
    #                 state["elapsed_lbl"].setText("00:00")
                
    #             h_config = state["duration_ms"] // 3600000
    #             m_config = (state["duration_ms"] % 3600000) // 60000
    #             config_str = f"{h_config:02d}:{m_config:02d}"
    #             if state["remaining_lbl"].text() != config_str:
    #                  state["remaining_lbl"].setText(config_str)




# # gui/service/mManualScr.py
# # Ejecución del autotest de la máquina y visualización de resultados.
# # control manual de los elementos de actuadores, bombas, válvulas

# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QDateTime
# from PySide6.QtGui import QColor, QDoubleValidator

# from gui.components.numpad_modal import NumpadDialog
# from gui.components.time_numpad_modal import TimeNumpadDialog

# try:
#     from logic.calculos import convertir_flujo_a_ciclos # convierte el flujo deseado a ciclos de cámara de balance
#     from logic.calculos import convertir_ciclos_a_flujo # convierte ciclos a flujo para lectura y/o actualizacion label
#     from logic.calculos import convertir_litros_h_a_ml_min
#     from logic.calculos import convertir_ml_min_a_litros_h
# except ImportError:
#     pass

# try:
#     from core.variables_map import VARIABLES, ANALOG_MAP
# except ImportError:
#     VARIABLES = {0x01: {}, 0x02: {}} # Mock vacío


# try:
#     from gui.components.LED import LED
#     from gui.components.ToggleSwitch import ToggleSwitch
# except ImportError:
#     class LED(QWidget):
#         def __init__(self): super().__init__(); self.state = 'off'
#         def set_state(self, s): self.state = s
#     class ToggleSwitch(QCheckBox):
#         def __init__(self, width=60, height=30, active_color=None): super().__init__()

# class ClickableLineEdit(QLineEdit):
#     clicked = Signal() # Señal 
    
#     def __init__(self, text="", parent=None):
#         super().__init__(text, parent)
    
#     def mousePressEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.clicked.emit()
#         super().mousePressEvent(event)

# class TempInput:
#     def __init__(self, valor):
#         self.valor = valor
#     def text(self):
#         return str(self.valor)
#     def clearFocus(self):
#         pass 
#     def setText(self, t):
#         pass


# class ValveCard(QFrame):
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

#         lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>")
#         lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
#         lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

#         self.toggle = ToggleSwitch(width=60, height=30)

#         layout.addWidget(lbl_info)
#         layout.addStretch()
#         layout.addWidget(self.toggle)


# class mManualScr(QWidget):
#     def __init__(self, parent=None, valores_dict=None):
#         super().__init__(parent)
#         self.parent_window = parent  
#         self.valores = valores_dict if valores_dict is not None else {}

#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         #self.setFixedSize(1536, 726)
#         self.setMinimumSize(1024, 600) # Ajustado un poco para probar, Valores originales (1536, 726) es el tamaño del stacked

#         # Fondo
#         self.setAutoFillBackground(True)
#         p = self.palette()
#         p.setColor(self.backgroundRole(), QColor("#fcfcfc"))
#         self.setPalette(p)
#         # Timers locales para cadaba bomba 
#         self.timer_op_pb = QTimer(self) # Bomba de sangre
#         self.timer_op_pd = QTimer(self) # Bomba de dializante 
#         self.timer_op_puf = QTimer(self) # Bomba de ultraFiltrado
#         self.timer_op_ph = QTimer(self) # Bomba de heparina
#         self.timer_op_cb = QTimer(self) # Cámara de balance

#         # Conectar señales timeout de los times a sus slots de detención
#         self.timer_op_pb.timeout.connect(self._stop_blood_pump_on_timeout)
#         self.timer_op_pd.timeout.connect(self._stop_dialysate_pump_on_timeout)
#         self.timer_op_puf.timeout.connect(self._stop_uf_pump_on_timeout)
#         self.timer_op_ph.timeout.connect(self._stop_heparin_pump_on_timeout)
#         self.timer_op_cb.timeout.connect(self._stop_balance_chamber_on_timeout)

#         # Variables de almacenamiento tiempo total para cada timer
#         # self._total_ms_op_pb = 0
#         # self._total_ms_op_pd = 0
#         # self._total_ms_op_puf = 0
#         # self._total_ms_op_ph = 0
#         # self._total_ms_op_cb = 0

#         # ### NUEVO: QTimer para actualizar la visualización cada segundo
#         self._display_update_timer = QTimer(self)
#         self._display_update_timer.timeout.connect(self._update_local_time_displays)
#         self._display_update_timer.start(500) # Actualizar cada 500ms para una sensación más fluida

#         # ### NUEVO: Diccionario para almacenar el estado de cada timer local
#         # Contiene: duration_ms (total configurado), start_ms (cuando empezó), active (si está corriendo),
#         # y referencias a las etiquetas de la UI para actualizar.
#         self._local_timers_state = {
#             "op_pb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_pd": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_puf": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_ph": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#             "op_cb": {"duration_ms": 0, "start_ms": 0, "active": False, "elapsed_lbl": None, "remaining_lbl": None},
#         }
        

        
#         self.setup_ui()

#     def setup_ui(self):
#         layout = QGridLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(15)

#         # ==================================================================
#         #          AREA 1: CONTROL DE BOMBAS
#         # ==================================================================
       
#         self.control_area = QWidget()
#         self.control_area.setFixedSize(1300, 480) 
#         self.control_area.setMinimumSize(1080,300)
#         grid = QGridLayout(self.control_area)
#         grid.setSpacing(15)
#         grid.setContentsMargins(5, 5, 5, 5)

#         # Estilos comunes
#         style_lbl = "color: #000000; font-size: 18px; font-weight: bold;"
#         style_unit = "color: #94a3b8; font-size: 16px;"
#         style_input = """
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
#                         font-weight: bold; border-radius: 5px; padding: 2px; }
#         """
#         style_btn = """
#             QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
#             QPushButton:pressed { background: #1e40af; }
#         """        

#         # ----------------------------------------------------------------------
#         # FILA 0: BOMBA DE SANGRE
#         # ----------------------------------------------------------------------
#         lbl_sangre = QLabel("B. Sangre")
#         lbl_sangre.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_sangre, 0, 0)

#         self.toggle_sangre = ToggleSwitch(width=70, height=35)
#         self.toggle_sangre.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk, timer_id="op_pb")
#         )
#         grid.addWidget(self.toggle_sangre, 0, 1)

#         btn_rev = QPushButton("REV")
#         btn_rev.setFixedSize(60, 35)
#         btn_rev.setStyleSheet(style_btn)
#         btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
#         btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
        
#         btn_fwd = QPushButton("FWD")
#         btn_fwd.setFixedSize(60, 35)
#         btn_fwd.setStyleSheet(style_btn)
#         btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
#         btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))

#         grid.addWidget(btn_rev, 0, 2)
#         grid.addWidget(btn_fwd, 0, 3)

#         lbl_flujo = QLabel("Flujo:")
#         lbl_flujo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_flujo, 0, 4)

#         self.input_flujo_sangre = ClickableLineEdit("0")
#         self.input_flujo_sangre.setFixedSize(80, 35)
#         self.input_flujo_sangre.setAlignment(Qt.AlignCenter)
#         self.input_flujo_sangre.setStyleSheet(style_input)
#         self.input_flujo_sangre.setReadOnly(True)        
#         self.input_flujo_sangre.clicked.connect(
#             lambda: self.open_numpad("bloodFlowControlSetPoint",self.input_flujo_sangre, "Flujo de Sangre")
#         )
#         grid.addWidget(self.input_flujo_sangre, 0, 5)

#         lbl_u1 = QLabel("ml/min")
#         lbl_u1.setStyleSheet(style_unit)
#         grid.addWidget(lbl_u1, 0, 6)

#         lbl_vel = QLabel("Vel:")
#         lbl_vel.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_vel, 0, 7)

#         self.lbl_velocidad_val = QLabel("0")
#         self.lbl_velocidad_val.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         grid.addWidget(self.lbl_velocidad_val, 0, 8)

#         lbl_u2 = QLabel("rpm")
#         lbl_u2.setStyleSheet(style_unit)
#         grid.addWidget(lbl_u2, 0, 9)

#         # TIEMPOS
#         lbl_tiempo = QLabel("T. Operación:")  # Tiempo de operacion de bomba de sangre 
#         lbl_tiempo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_tiempo, 0, 10)
        
#         self.input_t_BloodPump = ClickableLineEdit("00:00")
#         self.input_t_BloodPump.setFixedSize(120, 35)
#         self.input_t_BloodPump.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px;
#                         font-weight: bold; border-radius: 5px; padding: 2px;}
#         """)
#         self.input_t_BloodPump.setAlignment(Qt.AlignCenter)
#         self.input_t_BloodPump.setReadOnly(True)

#         # PENDIENTE DE MODIFICAR, PUES NO ESCRIBE AL CONTROL, SOLO MANEJA UN TIMER INTERNO
#         self.input_t_BloodPump.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_BloodPump,
#                 tag_hours=None,        # No envía 
#                 tag_minutes=None,      # No envía 
#                 local_timer_id="op_pb", # Identificador para timer local
#                 title="Tiempo de operación de bomba de sangre"
#             )
#         )        
#         grid.addWidget(self.input_t_BloodPump, 0, 11, 1, 3)

#         # ### NUEVO: Etiquetas de Tiempo Transcurrido y Restante para Bomba de Sangre
#         lbl_elapsed_pb_title = QLabel("Transcurrido:")
#         lbl_elapsed_pb_title.setStyleSheet(style_lbl.replace("bold", "normal") + "font-size: 14px;")
#         grid.addWidget(lbl_elapsed_pb_title, 0, 14, alignment=Qt.AlignRight)

#         self.lbl_elapsed_pb = QLabel("00:00")
#         self.lbl_elapsed_pb.setStyleSheet("color: #4CAF50; font-size: 18px; font-weight: bold;") # Color verde para transcurrido
#         grid.addWidget(self.lbl_elapsed_pb, 0, 15, alignment=Qt.AlignLeft)
        
#         lbl_remaining_pb_title = QLabel("Restante:")
#         lbl_remaining_pb_title.setStyleSheet(style_lbl.replace("bold", "normal") + "font-size: 14px;")
#         grid.addWidget(lbl_remaining_pb_title, 0, 16, alignment=Qt.AlignRight)

#         self.lbl_remaining_pb = QLabel("00:00")
#         self.lbl_remaining_pb.setStyleSheet("color: #FFC107; font-size: 18px; font-weight: bold;") # Color ámbar para restante
#         grid.addWidget(self.lbl_remaining_pb, 0, 17, alignment=Qt.AlignLeft)

#         # ### ALMACENAR REFERENCIAS a las etiquetas en _local_timers_state
#         self._local_timers_state["op_pb"]["elapsed_lbl"] = self.lbl_elapsed_pb
#         self._local_timers_state["op_pb"]["remaining_lbl"] = self.lbl_remaining_pb


#         # ----------------------------------------------------------------------
#         # FILA 1: BOMBA DE HEPARINA
#         # ----------------------------------------------------------------------
#         lbl_bHeparina = QLabel("B. Hep.")
#         lbl_bHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_bHeparina, 1, 0)

#         # self.toggle_heparina = ToggleSwitch(width=70, height=35)
#         # self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk))
#         # grid.addWidget(self.toggle_heparina, 1, 1)

#         self.toggle_heparina = ToggleSwitch(width=70, height=35)
#         self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk, timer_id="op_ph"))
#         grid.addWidget(self.toggle_heparina, 1, 1)


#         btn_homeHep = QPushButton("HOME")
#         btn_homeHep.setFixedSize(70, 35)
#         btn_homeHep.setStyleSheet(style_btn)
#         btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
#         btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False))
        
#         btn_rev_hep = QPushButton("REV")
#         btn_rev_hep.setFixedSize(70,35)
#         btn_rev_hep.setStyleSheet(style_btn)
#         btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton",True))
#         btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))

#         btn_pause_hep = QPushButton("PAUSE")
#         btn_pause_hep.setFixedSize(70,35)
#         btn_pause_hep.setStyleSheet(style_btn)
#         btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume",True))
#         btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))

#         btn_fwd_hep = QPushButton("FWD")
#         btn_fwd_hep.setFixedSize(70,35)
#         btn_fwd_hep.setStyleSheet(style_btn)
#         btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton",True))
#         btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))

#         grid.addWidget(btn_homeHep, 1, 2)
#         grid.addWidget(btn_rev_hep, 1, 3)
#         grid.addWidget(btn_pause_hep, 1, 4)
#         grid.addWidget(btn_fwd_hep, 1, 5)

#         lbl_indHeparina = QLabel("Heparina")
#         lbl_indHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_indHeparina, 1,6)
        
#         self.indHeparinCurrentDosage = QLabel("0.0")
#         self.indHeparinCurrentDosage.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.indHeparinCurrentDosage.setFixedSize(100,35)
#         grid.addWidget(self.indHeparinCurrentDosage,1,7)
        
#         lbl_unit_hep = QLabel("ml")
#         lbl_unit_hep.setStyleSheet(style_unit)
#         lbl_unit_hep.setFixedSize(100,35)
#         grid.addWidget(lbl_unit_hep,1,8)

#         # ----------------------------------------------------------------------
#         # FILA 2: DOSIS HEPARINA (Input)
#         # ----------------------------------------------------------------------
#         lbl_dosis = QLabel("Dosis Hep.")
#         lbl_dosis.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dosis, 2, 0)

#         self.input_dosis_hep = ClickableLineEdit("0.0")
#         self.input_dosis_hep.setFixedSize(100, 35)
#         self.input_dosis_hep.setAlignment(Qt.AlignCenter)
#         self.input_dosis_hep.setStyleSheet(style_input)

#         self.input_dosis_hep.setReadOnly(True) #ReadOnly para que no aparezca el cursor de texto

#         self.input_dosis_hep.clicked.connect(
#             lambda: self.open_numpad("heparineTherapyDosage", self.input_dosis_hep, "Dosis Heparina")
#         )
#         grid.addWidget(self.input_dosis_hep, 2, 1)

#         lbl_udosis_hep = QLabel("ml/h")
#         lbl_udosis_hep.setStyleSheet(style_unit)
#         grid.addWidget(lbl_udosis_hep, 2, 2)

#         lbl_dosis_bolo = QLabel("Bolo")
#         lbl_dosis_bolo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dosis_bolo, 2, 3)

#         self.input_dosis_bolo = ClickableLineEdit("0.0")
#         self.input_dosis_bolo.setFixedSize(100, 35)
#         self.input_dosis_bolo.setAlignment(Qt.AlignCenter)
#         self.input_dosis_bolo.setStyleSheet(style_input)
#         self.input_dosis_bolo.setReadOnly(True)
#         self.input_dosis_bolo.clicked.connect(
#             lambda: self.open_numpad("heparineBolusQuantity", self.input_dosis_bolo, "Dosis Bolo")
#         )
#         grid.addWidget(self.input_dosis_bolo, 2, 4)

#         lbl_udosis_bol = QLabel("ml")
#         lbl_udosis_bol.setStyleSheet(style_unit)
#         grid.addWidget(lbl_udosis_bol, 2, 5)

#         lbl_size_syringe = QLabel("Jeringa")
#         lbl_size_syringe.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_size_syringe, 2, 6)

#         self.input_size_syringe = ClickableLineEdit("0.0")
#         self.input_size_syringe.setFixedSize(100,35)
#         self.input_size_syringe.setAlignment(Qt.AlignCenter)
#         self.input_size_syringe.setStyleSheet(style_input)
#         self.input_size_syringe.setReadOnly(True)
#         self.input_size_syringe.clicked.connect(
#             lambda: self.open_numpad("heparineSyrinjeScaleSize", self.input_size_syringe, "Tamaño de jeringa")
#         )
#         grid.addWidget(self.input_size_syringe, 2, 7)

#         lbl_usize_syringe = QLabel("mm/ml")
#         lbl_usize_syringe.setStyleSheet(style_unit)
#         grid.addWidget(lbl_usize_syringe, 2, 8)

#         # Tiempo de terapia, este si se escribe al control, se utilizara lo mismo en pantalla configuración de tratamiento
#         lbl_t_therapy = QLabel("T. Terapia")
#         lbl_t_therapy.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_therapy, 2, 9)

#         self.input_t_therapy = ClickableLineEdit("00:00")
#         self.input_t_therapy.setFixedSize(120, 35)
#         self.input_t_therapy.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px;
#                         font-weight: bold; border-radius: 5px; padding: 2px;}
#         """)
#         self.input_t_therapy.setAlignment(Qt.AlignCenter)
#         self.input_t_therapy.setReadOnly(True)

#         self.input_t_therapy.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_therapy,
#                 tag_hours="heparineTherapyHours", 
#                 tag_minutes="heparineTherapyMinutes",
#                 local_timer_id="op_ph", # No es un timer local de app
#                 title="Tiempo de terapia" # tambien es para el timer de bomba de heparina.
#             )
#         )

#         grid.addWidget(self.input_t_therapy, 2, 10)





#         # ----------------------------------------------------------------------
#         # FILA 3: B. DIALIZANTE
#         # ----------------------------------------------------------------------
#         lbl_dializante = QLabel("B. Dializante")
#         lbl_dializante.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dializante, 3, 0)

#         # self.toggle_dializante = ToggleSwitch(width=70, height=35)
#         # self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk))
#         # grid.addWidget(self.toggle_dializante, 3,1)

#         self.toggle_dializante = ToggleSwitch(width=70, height=35)
#         self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk, timer_id="op_pd"))
#         grid.addWidget(self.toggle_dializante, 3,1)

#         self.lbl_indSDializante = QLabel("0.0")
#         self.lbl_indSDializante.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indSDializante.setFixedSize(100,35)
#         grid.addWidget(self.lbl_indSDializante, 3,2)

#         lbl_unit_indSdializante = QLabel("%")
#         lbl_unit_indSdializante.setStyleSheet(style_unit)
#         lbl_unit_indSdializante.setFixedSize(100,35)
#         grid.addWidget(lbl_unit_indSdializante, 3, 3)

#         lbl_e_tOpBD = QLabel("Tiempo Op.")
#         lbl_e_tOpBD.setStyleSheet(style_lbl)
#         lbl_e_tOpBD.setFixedSize(100,35)
#         grid.addWidget(lbl_e_tOpBD, 3, 4)

#         self.lbl_tiempo_OpBD = ClickableLineEdit("00:00") # ¡CORRECCIÓN!
#         self.lbl_tiempo_OpBD.setStyleSheet(style_input)
#         self.lbl_tiempo_OpBD.setFixedSize(100,35)
#         self.lbl_tiempo_OpBD.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_OpBD.setReadOnly(True)
#         self.lbl_tiempo_OpBD.clicked.connect( # ¡CORRECCIÓN!
#             lambda: self.open_time_numpad(
#             self.lbl_tiempo_OpBD,
#             tag_hours=None,
#             tag_minutes=None,
#             local_timer_id="op_pd", # Identificador para timer local
#             title="Tiempo Op. Dializante"
#             )
#         )
        
#         grid.addWidget(self.lbl_tiempo_OpBD,3,5)

#         # ### NUEVO: Etiquetas de Tiempo Transcurrido y Restante para Bomba de Dializante
#         lbl_elapsed_pd_title = QLabel("Transcurrido:")
#         lbl_elapsed_pd_title.setStyleSheet(style_lbl.replace("bold", "normal") + "font-size: 14px;")
#         grid.addWidget(lbl_elapsed_pd_title, 3, 8, alignment=Qt.AlignRight) # Columnas ajustadas

#         self.lbl_elapsed_pd = QLabel("00:00")
#         self.lbl_elapsed_pd.setStyleSheet("color: #4CAF50; font-size: 18px; font-weight: bold;")
#         grid.addWidget(self.lbl_elapsed_pd, 3, 9, alignment=Qt.AlignLeft)
        
#         lbl_remaining_pd_title = QLabel("Restante:")
#         lbl_remaining_pd_title.setStyleSheet(style_lbl.replace("bold", "normal") + "font-size: 14px;")
#         grid.addWidget(lbl_remaining_pd_title, 3, 10, alignment=Qt.AlignRight)

#         self.lbl_remaining_pd = QLabel("00:00")
#         self.lbl_remaining_pd.setStyleSheet("color: #FFC107; font-size: 18px; font-weight: bold;")
#         grid.addWidget(self.lbl_remaining_pd, 3, 11, alignment=Qt.AlignLeft)

#         self._local_timers_state["op_pd"]["elapsed_lbl"] = self.lbl_elapsed_pd
#         self._local_timers_state["op_pd"]["remaining_lbl"] = self.lbl_remaining_pd



#         # ----------------------------------------------------------------------
#         # FILA 4: B. Ultra Filtrado
#         # ----------------------------------------------------------------------
#         lbl_ultrafiltado = QLabel("B. UF")
#         lbl_ultrafiltado.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_ultrafiltado, 4,0)

#         # self.toggle_uf = ToggleSwitch(width=70, height=35)
#         # self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt","dialyUltraFPumpStoptButt",chk))
#         # grid.addWidget(self.toggle_uf, 4,1)

#         self.toggle_uf = ToggleSwitch(width=70, height=35)
#         self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt","dialyUltraFPumpStoptButt",chk, timer_id="op_puf"))
#         grid.addWidget(self.toggle_uf, 4,1)

#         self.lbl_indUF = QLabel("0.0")
#         self.lbl_indUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indUF.setFixedSize(100,35)
#         grid.addWidget(self.lbl_indUF, 4, 2)

#         lbl_unit_indUF = QLabel("L/h")
#         lbl_unit_indUF.setStyleSheet(style_unit)
#         lbl_unit_indUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indUF, 4,3)

#         lbl_e_tOpBUF = QLabel("Tiempo Op.")
#         lbl_e_tOpBUF.setStyleSheet(style_lbl)
#         lbl_e_tOpBUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_e_tOpBUF, 4, 4)

#         self.lbl_tiempo_opBUF = ClickableLineEdit("00:00") # ¡CORRECCIÓN!
#         self.lbl_tiempo_opBUF.setStyleSheet(style_input)
#         self.lbl_tiempo_opBUF.setFixedSize(100, 35)
#         self.lbl_tiempo_opBUF.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_opBUF.setReadOnly(True)
#         self.lbl_tiempo_opBUF.clicked.connect( # ¡CORRECCIÓN!
#             lambda: self.open_time_numpad(
#                 self.lbl_tiempo_opBUF,
#                 tag_hours=None,
#                 tag_minutes=None,
#                 local_timer_id="op_puf", # Identificador para timer local
#                 title="Tiempo Op. Ultra Filtrado"
#             )
#         )
#         grid.addWidget(self.lbl_tiempo_opBUF, 4, 5)

#         lbl_e_tRestBUF = QLabel("T. Restante")
#         lbl_e_tRestBUF.setStyleSheet(style_lbl)
#         lbl_e_tRestBUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_e_tRestBUF, 4, 6)

#         self.lbl_tiempo_RestBUF = QLabel("00:00")
#         self.lbl_tiempo_RestBUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_tiempo_RestBUF.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_tiempo_RestBUF, 4, 7)

#         # ----------------------------------------------------------------------
#         # FILA 5: B. Bicarbonato Na+
#         # ----------------------------------------------------------------------
#         lbl_bicarbonato = QLabel("B. Na+")
#         lbl_bicarbonato.setStyleSheet(style_lbl)
#         lbl_bicarbonato.setFixedSize(100, 35)
#         grid.addWidget(lbl_bicarbonato, 5, 0)

#         self.toggle_Na = ToggleSwitch(width=70, height=35)
#         self.toggle_Na.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt","dialyBicarbonPumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_Na, 5, 1)

#         self.lbl_indBNa = QLabel("0.0")
#         self.lbl_indBNa.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indBNa.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indBNa, 5, 2)

#         lbl_unit_indBNa = QLabel("%")
#         lbl_unit_indBNa.setStyleSheet(style_unit)
#         lbl_unit_indBNa.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBNa, 5, 3)
                                                                                                                                                                                                                                                                         
#         # ----------------------------------------------------------------------
#         # FILA 6: B. Acido Citrico
#         # ----------------------------------------------------------------------
#         lbl_acidocitrico = QLabel("B. A. Citrico")
#         lbl_acidocitrico.setStyleSheet(style_lbl)
#         lbl_acidocitrico.setFixedSize(100, 35)
#         grid.addWidget(lbl_acidocitrico, 6, 0)

#         self.toggle_acidocitrico = ToggleSwitch(width=70, height=35)
#         self.toggle_acidocitrico.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt","dialyCitricAcPumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_acidocitrico, 6, 1)

#         self.lbl_indBAC = QLabel("0.0")
#         self.lbl_indBAC.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indBAC.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indBAC, 6, 2)

#         lbl_unit_indBAC = QLabel("%")
#         lbl_unit_indBAC.setStyleSheet(style_unit)
#         lbl_unit_indBAC.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBAC, 6, 3)

#         # ----------------------------------------------------------------------
#         # FILA 7: B. Purga de Aire
#         # ----------------------------------------------------------------------
#         lbl_purga = QLabel("B. Purga")
#         lbl_purga.setStyleSheet(style_lbl)
#         lbl_purga.setFixedSize(100, 35)
#         grid.addWidget(lbl_purga, 7, 0)

#         self.toggle_purga = ToggleSwitch(width=70, height=35)
#         self.toggle_purga.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt","dialyPurgePumpStopButt",chk, timer_id=None))
#         grid.addWidget(self.toggle_purga, 7, 1)

#         self.lbl_indPurga = QLabel("0.0")
#         self.lbl_indPurga.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indPurga.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indPurga, 7, 2)

#         lbl_unit_indPurga = QLabel("%")
#         lbl_unit_indPurga.setStyleSheet(style_unit)
#         lbl_unit_indPurga.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indPurga, 7, 3) # OJO: Aquí se repite lbl_unit_indBAC en el grid original. Puede ser intencional o error.

#         # ----------------------------------------------------------------------
#         # FILAS 8: C. Balance (Esta la metiste en la lista de bombas simples en tu codigo original)
#         # ----------------------------------------------------------------------
#         lbl_cb = QLabel("C. Balance")
#         lbl_cb.setStyleSheet(style_lbl)
#         lbl_cb.setFixedSize(100, 35)
#         grid.addWidget(lbl_cb, 8, 0)

#         self.toggle_cb = ToggleSwitch(width=70, height=35)
#         self.toggle_cb.toggled.connect(lambda chk: self.manejar_bomba_doble("dialiserBalChambStrButt","dialiserBalChambStpButt",chk, timer_id="op_cb"))
#         grid.addWidget(self.toggle_cb, 8, 1)
        
#         lbl_t_op_cb = QLabel("T. Operación:")
#         lbl_t_op_cb.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_op_cb, 8, 2)

#         self.input_t_BalanceChamber = ClickableLineEdit("00:00")
#         self.input_t_BalanceChamber.setFixedSize(120, 35)
#         self.input_t_BalanceChamber.setStyleSheet(style_input)
#         self.input_t_BalanceChamber.setAlignment(Qt.AlignCenter)
#         self.input_t_BalanceChamber.setReadOnly(True)
#         self.input_t_BalanceChamber.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_BalanceChamber,
#                 tag_hours=None,
#                 tag_minutes=None,
#                 local_timer_id="op_cb", # Identificador para timer local de cámara de balance
#                 title="Tiempo Op. Cámara de Balance"
#             )
#         )
#         grid.addWidget(self.input_t_BalanceChamber, 8, 3, 1, 3)

#         # self.lbl_indPurga = QLabel("0.0")
#         # self.lbl_indPurga.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         # self.lbl_indPurga.setFixedSize(100, 35)
#         # grid.addWidget(self.lbl_indPurga, 7, 2)

#         # lbl_unit_indPurga = QLabel("%")
#         # lbl_unit_indPurga.setStyleSheet(style_unit)
#         # lbl_unit_indPurga.setFixedSize(100, 35)
#         # grid.addWidget(lbl_unit_indBAC, 7, 3)
        
#         # bombas_simples = [
#         #     (7, "C. Balance", "dialiserBalChambStrButt", "dialiserBalChambStpButt"),
#         # ]

#         # self.toggles_simples = {} 

#         # for row_idx, nombre, tag_start, tag_stop in bombas_simples:
#         #     lbl = QLabel(nombre)
#         #     lbl.setStyleSheet(style_lbl)
#         #     grid.addWidget(lbl, row_idx, 0)

#         #     toggle = ToggleSwitch(width=70, height=35)
#         #     toggle.toggled.connect(
#         #         lambda chk, ts=tag_start, tp=tag_stop: self.manejar_bomba_doble(ts, tp, chk)
#         #     )
#         #     self.toggles_simples[tag_start] = toggle
#         #     grid.addWidget(toggle, row_idx, 1)



#         layout.addWidget(self.control_area, 0, 0)

#         # ==================================================================
#         #          AREA 2: INDICADORES LED
#         # ==================================================================
#         self.ind_area = QWidget()
#         self.ind_area.setFixedSize(180,726)
#         grid_ind_area = QGridLayout(self.ind_area)
#         grid_ind_area.setSpacing(10)
#         grid_ind_area.setContentsMargins(10, 10,10, 10)

#         led_nombres = ["B. Sangre","B. Dializante","B. Heparina","B. UltraF","Purga de\n aire","C.Balance","A. sangre","C.Deaereación","Fin de\n ciclos","Protec.\n Resist.","S.Dializante","Nivel de\ntanque"]   
#         self.leds = []
#         for i, nombre in enumerate(led_nombres):
#             lbl = QLabel(nombre)
#             lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
#             lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#             grid_ind_area.addWidget(lbl, i, 0)

#             led = LED()
#             led.setFixedSize(45, 45)
#             grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
#             self.leds.append(led)

#         layout.addWidget(self.ind_area, 0, 1, 2, 1)

#         # ==============================================================================================
#         # AREA 3: VÁLVULAS
#         # ==============================================================================================
#         self.ctrl_valvulas = QWidget()
#         self.ctrl_valvulas.setFixedSize(1300,240)
#         layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas) 
#         layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
#         layout_ctrl_valvulas.setSpacing(10)
        
#         self.container_mop = QFrame()
#         self.container_mop.setFixedSize(110,240)
#         self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
#         layout_mop = QVBoxLayout(self.container_mop) 
       
#         lbl_modo = QLabel("Modo de \n Op.")
#         lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
#         lbl_modo.setAlignment(Qt.AlignCenter)
        
#         self.toggle_modo = ToggleSwitch(width=60, height=30, active_color="#facc15") 
#         self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))

#         layout_mop.addStretch()
#         layout_mop.addWidget(lbl_modo)
#         layout_mop.setSpacing(10)
#         layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
#         layout_mop.addStretch()
        
#         layout_ctrl_valvulas.addWidget(self.container_mop)

#         self.container_val = QWidget()
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
#             parts = desc.split(" ",1)
#             codigo = parts[0]
#             texto = parts[1] if len(parts) > 1 else ""

#             card = ValveCard(codigo, texto)
#             self.valvulas_map[tag] = card
#             grid_valvulas_area.addWidget(card, r, c)
#             card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

#         layout_ctrl_valvulas.addWidget(self.container_val)
#         layout.addWidget(self.ctrl_valvulas, 1, 0)    

#     def _actualizar_toggle(self, toggle, valor):
#         """Función auxiliar para actualizar toggle sin disparar señal"""
#         estado_nuevo = (valor > 0)
        
#         # USAMOS is_checked() PORQUE ES EL MÉTODO DEFINIDO EN TU COMPONENTE
#         if toggle.is_checked() != estado_nuevo:
#             toggle.blockSignals(True)  # Importante: Evita bucle infinito con el PLC
#             toggle.setChecked(estado_nuevo)
#             toggle.blockSignals(False)

#     def actualizar_valores(self, nuevos_valores):
#         self.valores = nuevos_valores
        
#         # ACTUALIZAR LEDS
#         variables_leds = [
#             "bloodPumpStartButton",       
#             "dialyserPumpStartButton",    
#             "heparinePumpsStartButton",   
#             "dialyUltraFPumpStartButt",   
#             "dialyPurgePumpStartButt",    
#             "dialiserBalChambStrButt",    
#             "airBubbleInBloodDetected",   
#             "dialyDeaerChamLevSwitch",    
#             "dialyBalanceChambCycleEnd",  
#             "watterTankHeaterProtect",    
#             "bloodInDialyCircDetected",   
#             "dialyTankHiLevelSwitch"      
#         ]
#         for i, led in enumerate(self.leds):
#             if i < len(variables_leds):
#                 nombre_var = variables_leds[i]
#                 valor = self.valores.get(nombre_var, 0.0)
#                 estado = 'on' if valor > 0 else 'off'
#                 if led.state != estado:
#                     led.set_state(estado)
        
#         # ACTUALIZAR VÁLVULAS
#         for tag, card in self.valvulas_map.items():
#             val = self.valores.get(tag, 0.0)
#             nuevo_estado = True if val > 0 else False
#             # Bloquear señales para evitar que la actualización visual re-envíe comando al PLC
#             if card.toggle.is_checked() != nuevo_estado:
#                 card.toggle.blockSignals(True)
#                 if hasattr(card.toggle, "setChecked"):
#                     card.toggle.setChecked(nuevo_estado)
#                 card.toggle.blockSignals(False)
        
#         # ACTUALIZAR INDICADORES NUMÉRICOS
#         # Velocidad sangre
#         vel_sangre = self.valores.get("bloodSpeedVariableData", 0.0)
#         self.lbl_velocidad_val.setText(f"{vel_sangre:.0f}")
        
#         # Dosis heparina
#         val_heparina = self.valores.get("heparineCurrentDosage", 0.0) 
#         self.indHeparinCurrentDosage.setText(f"{val_heparina:.1f}")

#         # Input Dosis Heparina (solo si no tiene foco)
#         in_heparinTherapyDosage = self.valores.get("heparineTherapyDosage", 0.0)
#         if not self.input_dosis_hep.hasFocus():
#             self.input_dosis_hep.setText(f"{in_heparinTherapyDosage:.1f}")

#         in_usizesyringe = self.valores.get("heparineSyrinjeScaleSize", 0.0)
#         if not self.input_size_syringe.hasFocus():
#             self.input_size_syringe.setText(f"{in_usizesyringe:.1f}")
        
#         in_dosis_bolo = self.valores.get("heparineBolusQuantity", 0.0)
#         if not self.input_dosis_bolo.hasFocus():
#             self.input_dosis_bolo.setText(f"{in_dosis_bolo:.1f}")
        
#         in_input_flujo_sangre = self.valores.get("bloodFlowControlSetPoint", 0.0)
#         if not self.input_flujo_sangre.hasFocus():
#             self.input_flujo_sangre.setText(f"{in_input_flujo_sangre:.1f}")
        
#         in_input_t_therapy_hours = int(self.valores.get("heparineTherapyHours", 0)) 
#         in_input_t_therapy_minutes = int(self.valores.get("heparineTherapyMinutes", 0))
#         if not self.input_t_therapy.hasFocus():
#             # Formatear como enteros de dos dígitos (HH:MM)
#             self.input_t_therapy.setText(f"{in_input_t_therapy_hours:02d}:{in_input_t_therapy_minutes:02d}")


#         # ACTUALIZAR TOGGLES DE BOMBAS 
#         # Uso helper _actualizar_toggle para código más limpio y bloqueo de señales
        
#         self._actualizar_toggle(self.toggle_sangre, self.valores.get("bloodPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_heparina, self.valores.get("heparinePumpsStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_dializante, self.valores.get("dialyserPumpStartButton", 0.0))
#         self._actualizar_toggle(self.toggle_acidocitrico, self.valores.get("dialyCitricAcPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_Na, self.valores.get("dialyBicarbonPumpStartButt", 0.0))
        
#         # CORREGIDO: purga estaba leyendo 'dialyserPumpStartButton' en el código original
#         self._actualizar_toggle(self.toggle_purga, self.valores.get("dialyPurgePumpStartButt", 0.0))
        
#         self._actualizar_toggle(self.toggle_uf, self.valores.get("dialyUltraFPumpStartButt", 0.0))
#         self._actualizar_toggle(self.toggle_modo, self.valores.get("dialyCircuitElementsOpSel", 0.0))

#         self._actualizar_toggle(self.toggle_cb,self.valores.get("dialiserBalChambStrButt",0.0))

#         # 5. ACTUALIZAR TOGGLES SIMPLES (Balance)
#         # for tag_start, toggle in self.toggles_simples.items():
#         #     val = self.valores.get(tag_start, 0.0)
#         #     self._actualizar_toggle(toggle, val)

#     # def manejar_bomba_doble(self, tag_start, tag_stop, activado):
#     #     if activado:
#     #         print(f"[BOMBA] Arrancando {tag_start}")
#     #         self.escribir_comando(tag_start, True)
#     #         self.escribir_comando(tag_stop, False) 
#     #     else:
#     #         print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
#     #         self.escribir_comando(tag_stop, True) 
#     #         self.escribir_comando(tag_start, False)

#     # def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
#     #     if activado:
#     #         print(f"[BOMBA] Arrancando {tag_start}")
#     #         self.escribir_comando(tag_start, True)
#     #         self.escribir_comando(tag_stop, False) 
            
#     #         # --- NUEVO: Iniciar timer si existe y se configuró un tiempo ---
#     #         if timer_id:
#     #             timer_obj = getattr(self, f"timer_{timer_id}")
#     #             total_ms_duration = getattr(self, f"_total_ms_{timer_id}")
                
#     #             if total_ms_duration > 0:
#     #                 timer_obj.start(total_ms_duration)
#     #                 print(f"[APP_TIMER] Iniciando timer '{timer_id}' por {total_ms_duration} ms.")
#     #             else:
#     #                 print(f"[APP_TIMER] Advertencia: Timer '{timer_id}' no tiene duración establecida (0 ms). No se inició.")

#     #     else: # Bomba desactivada
#     #         print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
#     #         self.escribir_comando(tag_stop, True) 
#     #         self.escribir_comando(tag_start, False)
            
#     #         # --- NUEVO: Detener timer si está corriendo ---
#     #         if timer_id:
#     #             timer_obj = getattr(self, f"timer_{timer_id}")
#     #             if timer_obj.isActive():
#     #                 timer_obj.stop()
#     #                 print(f"[APP_TIMER] Deteniendo timer '{timer_id}'.")
    
    


#     def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
#         if activado:
#             print(f"[BOMBA] Arrancando {tag_start}")
#             self.escribir_comando(tag_start, True)
#             self.escribir_comando(tag_stop, False) 
            
#             # --- CORRECCIÓN AQUÍ: Obtener duración del diccionario de estado ---
#             if timer_id:
#                 state = self._local_timers_state[timer_id]
#                 total_ms_duration = state["duration_ms"] # ¡AHORA LEE DEL DICCIONARIO!

#                 if total_ms_duration > 0:
#                     state["active"] = True # Marcar como activo
#                     state["start_ms"] = QDateTime.currentMSecsSinceEpoch() # Guardar el timestamp de inicio

#                     timer_obj = getattr(self, f"timer_{timer_id}") # Obtiene el QTimer
#                     timer_obj.start(total_ms_duration) # Inicia el QTimer de un solo disparo

#                     print(f"[APP_TIMER] Iniciando timer '{timer_id}' por {total_ms_duration} ms.")
#                 else:
#                     print(f"[APP_TIMER] Advertencia: Timer '{timer_id}' no tiene duración establecida (0 ms). No se inició.")

#         else: # Bomba desactivada
#             print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
#             self.escribir_comando(tag_stop, True) 
#             self.escribir_comando(tag_start, False)
            
#             # --- CORRECCIÓN AQUÍ: Obtener duración del diccionario de estado para actualizar display ---
#             if timer_id:
#                 state = self._local_timers_state[timer_id]
#                 if state["active"]: # Solo si estaba activo, entonces lo detengo
#                     state["active"] = False # Marcar como inactivo
                    
#                     # Detener el QTimer de un solo disparo
#                     timer_obj = getattr(self, f"timer_{timer_id}")
#                     if timer_obj.isActive():
#                         timer_obj.stop()
                    
#                     # ### RESETEAR LAS ETIQUETAS DE TIEMPO DEL DISPLAY
#                     if state["elapsed_lbl"]: state["elapsed_lbl"].setText("00:00")
#                     if state["remaining_lbl"]: 
#                         h_config = state["duration_ms"] // 3600000
#                         m_config = (state["duration_ms"] % 3600000) // 60000
#                         state["remaining_lbl"].setText(f"{h_config:02d}:{m_config:02d}") # Vuelve a mostrar la duración configurada

#                     print(f"[APP_TIMER] Deteniendo timer '{timer_id}'.")


#     def escribir_setpoint(self, tag, widget_input):
#         try:
#             texto = widget_input.text().replace(',', '.')
#             if not texto:                 
#                 current_value = self.valores.get(tag, 0.0)
#                 widget_input.setText(f"{current_value:.1f}") # O el formato que corresponda
#                 return 
                
#             valor = float(texto)
#             print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
#             target_group = -1
#             target_id = -1
#             found = False
            
#             # Buscar el grupo y el ID de la variable usando el tag
#             # Recorremos los grupos definidos en VARIABLES
#             for group_key, variables_in_group in VARIABLES.items():                
#                 if isinstance(variables_in_group, dict): 
#                     for var_id, info in variables_in_group.items():
#                         if info.get("tag") == tag:
#                             target_group = group_key
#                             target_id = var_id
#                             found = True
#                             break
#                 if found: break # Salir del bucle exterior una vez encontrada
            
#             if found and target_group != -1 and target_id != -1:
#                 # Verificar que la variable sea RW (si aún no lo has hecho, es buena idea)
#                 if VARIABLES[target_group][target_id].get("rw", False):
#                     print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
#                     if self.parent_window and hasattr(self.parent_window, 'serial'):                      
#                         self.parent_window.serial.escribir_double(target_group, target_id, valor)
#                         #print(f" -> Comando enviado para {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
#                     else:
#                         print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
#                 else:
#                     print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
#             else:
#                 print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")

#             widget_input.clearFocus()

#         except ValueError:
#             print(f"[ERROR] Valor numérico inválido en input para {tag}: {widget_input.text()}")
#         except Exception as e:
#             print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
  

#     def escribir_comando(self, tag, estado):
#         print(f"[COMANDO] Usuario cambió {tag} a {estado}")
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
#                         print(f" -> Enviando: Addr {direccion} Val {estado}")
#                         self.parent_window.serial.escribir_booleano(direccion, estado)
#                     else:
#                         print(" -> Error: Serial no conectado")
#                 except AttributeError:
#                     print(f"[INFO] Fallo en envío: Addr {direccion} Val {estado}")
#             else:
#                  print(f"[INFO] Error no se completo la escritura: Addr {direccion} Val {estado}")
#         else:
#             print(f" -> Error: No se encontró ID para el tag '{tag}'")

#     def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
#         act_value = widget_input.text()
#         dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
#         if dialog.exec(): # Si el usuario presiona "ACEPTAR"
#             new_value = dialog.get_value() 
#             widget_input.setText(str(new_value))            
#             self.escribir_setpoint(tag, widget_input)


#     def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
#         """
#         1. Abre el TimeNumpadDialog con el valor actual del widget.
#         2. Al aceptar, actualiza el widget visual a "HH:MM".
#         3. Desglosa Horas y Minutos.
#         4. Si tiene tags, llama a escribir_setpoint para el PLC.
#         5. Si tiene local_timer_id, configura el QTimer correspondiente.
#         """
#         texto_actual = widget_input.text()
#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

#         if dialog.exec():
#             h, m = dialog.get_hours_minutes()
#             widget_input.setText(f"{h:02d}:{m:02d}")
            
#             # Calcular duración total en milisegundos
#             total_ms = (h * 3600 + m * 60) * 1000

#             # 1. Lógica para escribir al PLC (si se proporcionaron tags)
#             if tag_hours and tag_minutes:
#                 print(f"[PLC_WRITE] Enviando horas ({h}) al tag: {tag_hours}")
#                 fake_widget_h = TempInput(h) 
#                 self.escribir_setpoint(tag_hours, fake_widget_h)

#                 print(f"[PLC_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}")
#                 fake_widget_m = TempInput(m)
#                 self.escribir_setpoint(tag_minutes, fake_widget_m)
#             elif tag_hours or tag_minutes: # Solo como aviso, esto no debería pasar si la lógica es correcta
#                 print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

#             # 2. Lógica para configurar QTimer locales de la aplicación
#             if local_timer_id:
#                 timer_attr_name = f"timer_{local_timer_id}" # Ej: "timer_op_pb"
#                 total_ms_attr_name = f"_total_ms_{local_timer_id}" # Ej: "_total_ms_op_pb"
                
#                 # Acceder al QTimer y a la variable de duración usando getattr/setattr
#                 timer_obj = getattr(self, timer_attr_name)
#                 setattr(self, total_ms_attr_name, total_ms) # Guardar la duración total

#                 print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")
                
#                 # Opcional: Mostrar algún feedback de que el timer está listo
#                 # widget_input.setStyleSheet(style_input + "border: 2px solid green;") 

#     def _stop_blood_pump_on_timeout(self):
#         print("[APP_TIMER] Timer 'op_pb' finalizado. Deteniendo Bomba de Sangre.")
#         self.timer_op_pb.stop()
#         self._local_timers_state["op_pb"]["active"] = False # ¡Añadir esta línea!
#         self.toggle_sangre.setChecked(False)

#     def _stop_dialysate_pump_on_timeout(self):
#         print("[APP_TIMER] Timer 'op_pd' finalizado. Deteniendo Bomba de Dializante.")
#         self.timer_op_pd.stop()
#         self._local_timers_state["op_pd"]["active"] = False # ¡Añadir esta línea!
#         self.toggle_dializante.setChecked(False)

#     def _stop_uf_pump_on_timeout(self):
#         print("[APP_TIMER] Timer 'op_puf' finalizado. Deteniendo Bomba de Ultrafiltración.")
#         self.timer_op_puf.stop()
#         self._local_timers_state["op_puf"]["active"] = False # ¡Añadir esta línea!
#         self.toggle_uf.setChecked(False)

#     def _stop_heparin_pump_on_timeout(self):
#         print("[APP_TIMER] Timer 'op_ph' finalizado. Deteniendo Bomba de Heparina.")
#         self.timer_op_ph.stop()
#         self._local_timers_state["op_ph"]["active"] = False # ¡Añadir esta línea!
#         self.toggle_heparina.setChecked(False)

#     def _stop_balance_chamber_on_timeout(self):
#         print("[APP_TIMER] Timer 'op_cb' finalizado. Deteniendo Cámara de Balance.")
#         self.timer_op_cb.stop()
#         self._local_timers_state["op_cb"]["active"] = False # ¡Añadir esta línea!
#         self.toggle_cb.setChecked(False)


        
#         # ### NUEVO: Función auxiliar para formatear ms a HH:MM
#     def _format_ms_to_hh_mm(self, ms):
#         total_seconds = max(0, ms // 1000) # Asegurarse de que no sea negativo
#         hours = total_seconds // 3600
#         minutes = (total_seconds % 3600) // 60
#         # seconds = total_seconds % 60 # Si quisieras HH:MM:SS
#         return f"{hours:02d}:{minutes:02d}"

#     # ### NUEVO: Método para actualizar todas las pantallas de tiempo de los timers locales
#     def _update_local_time_displays(self):
#         current_ms = QDateTime.currentMSecsSinceEpoch()
#         for timer_id, state in self._local_timers_state.items():
#             if state["active"] and state["duration_ms"] > 0 and state["start_ms"] > 0:
#                 elapsed_ms = current_ms - state["start_ms"]
#                 remaining_ms = state["duration_ms"] - elapsed_ms

#                 # Asegurarse de que el restante no sea negativo
#                 if remaining_ms < 0:
#                     remaining_ms = 0
#                     elapsed_ms = state["duration_ms"] # Asegurar que el transcurrido sea igual a la duración
#                     # Opcional: Podrías forzar el apagado aquí también si el QTimer de un solo disparo falla
#                     # self._stop_X_pump_on_timeout()
                
#                 if state["elapsed_lbl"]:
#                     state["elapsed_lbl"].setText(self._format_ms_to_hh_mm(elapsed_ms))
#                 if state["remaining_lbl"]:
#                     state["remaining_lbl"].setText(self._format_ms_to_hh_mm(remaining_ms))
#             elif not state["active"] and state["elapsed_lbl"] and state["remaining_lbl"]:
#                 # Si el timer no está activo, asegúrate de que se muestre el estado de reposo (00:00 y duración configurada)
#                 if state["elapsed_lbl"].text() != "00:00":
#                     state["elapsed_lbl"].setText("00:00")
                
#                 h_config = state["duration_ms"] // 3600000
#                 m_config = (state["duration_ms"] % 3600000) // 60000
#                 config_str = f"{h_config:02d}:{m_config:02d}"
#                 if state["remaining_lbl"].text() != config_str:
#                      state["remaining_lbl"].setText(config_str)

    
    # def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, title="Config. Tiempo"):
    #     """
    #     1. Abre el TimeNumpadDialog con el valor actual del widget.
    #     2. Al aceptar, actualiza el widget visual a "HH:MM".
    #     3. Desglosa Horas y Minutos y llama a escribir_setpoint por separado para cada uno.
    #     """
    #     # 1. Obtener texto actual "HH:MM"
    #     texto_actual = widget_input.text()
        
    #     # Creamos el diálogo
    #     dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

    #     if dialog.exec():
    #         # 2. Obtener valores separados
    #         h, m = dialog.get_hours_minutes()
            
    #         # 3. Actualizar la interfaz visual (UI)
    #         widget_input.setText(f"{h:02d}:{m:02d}")

    #         # 4. Enviar al sistema (PLC/Backend)
    #         # Usamos la clase interna TempInput para simular un widget y reutilizar escribir_setpoint
            
    #         if tag_hours:
    #             print(f"[SPLIT] Enviando horas ({h}) al tag: {tag_hours}")
    #             fake_widget_h = TempInput(h) 
    #             self.escribir_setpoint(tag_hours, fake_widget_h)

    #         if tag_minutes:
    #             print(f"[SPLIT] Enviando minutos ({m}) al tag: {tag_minutes}")
    #             fake_widget_m = TempInput(m)
    #             self.escribir_setpoint(tag_minutes, fake_widget_m)


 #gui/service/mManualScr.py
# #Ejecución del autotest de la máquina y visualización de resultados.
# #control manual de los elementos de actuadores, bombas, válvulas

# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QColor, QDoubleValidator

# from core.variables_map import VARIABLES, TVAR_TO_GROUP
# from gui.components.LED import LED
# from gui.components.ToggleSwitch import ToggleSwitch


# class ValveCard(QFrame):
#     def _init_(self, codigo, descripcion, parent=None):
#         super()._init_(parent)
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: #1e293b;
#                 border-radius: 8px;
#                 border: 1px solid #334155;
#                 }
#         """)
#         self.setFixedHeight(80)

#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(10)

#         lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>")
#         lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
#         lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

#         self.toggle = ToggleSwitch(width=60, height=30)

#         layout.addWidget(lbl_info)
#         layout.addStretch()
#         layout.addWidget(self.toggle)


# class mManualScr(QWidget):
#     def _init_(self, parent=None, valores_dict=None):
#         super()._init_(parent)
#         # Guarda la referencia
#         self.parent_window = parent  
#         self.valores = valores_dict if valores_dict is not None else {}

#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.setFixedSize(1536, 726)
        
#         # Fondo
#         self.setAutoFillBackground(True)
#         p = self.palette()
#         p.setColor(self.backgroundRole(), QColor("#fcfcfc"))
#         self.setPalette(p)

#         self.setup_ui()

#     def setup_ui(self):
#         layout = QGridLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(15)

#         # ==================================================================
#         #          AREA 1: CONTROL DE BOMBAS
#         # ==================================================================
       
#         self.control_area = QWidget()
#         self.control_area.setFixedSize(1300, 480) 
#         grid = QGridLayout(self.control_area)
#         grid.setSpacing(15)
#         grid.setContentsMargins(5, 5, 5, 5)

#         # Estilos comunes
#         style_lbl = "color: #000000; font-size: 18px; font-weight: bold;"
#         style_unit = "color: #94a3b8; font-size: 16px;"
#         style_input = """
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
#                         font-weight: bold; border-radius: 5px; padding: 2px; }
#         """
#         style_btn = """
#             QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
#             QPushButton:pressed { background: #1e40af; }
#         """        

#         # ----------------------------------------------------------------------
#         # FILA 0: BOMBA DE SANGRE
#         # ----------------------------------------------------------------------
#         lbl_sangre = QLabel("B. Sangre")
#         lbl_sangre.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_sangre, 0, 0)

#         self.toggle_sangre = ToggleSwitch(width=70, height=35)
#         self.toggle_sangre.toggled.connect(
#             lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk)
#         )
#         grid.addWidget(self.toggle_sangre, 0, 1)

#         btn_rev = QPushButton("REV")
#         btn_rev.setFixedSize(60, 35)
#         btn_rev.setStyleSheet(style_btn)
#         btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
#         btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
        
#         btn_fwd = QPushButton("FWD")
#         btn_fwd.setFixedSize(60, 35)
#         btn_fwd.setStyleSheet(style_btn)
#         btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
#         btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))

#         grid.addWidget(btn_rev, 0, 2)
#         grid.addWidget(btn_fwd, 0, 3)

#         lbl_flujo = QLabel("Flujo:")
#         lbl_flujo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_flujo, 0, 4)

#         self.input_flujo_sangre = QLineEdit("0")
#         self.input_flujo_sangre.setFixedSize(80, 35)
#         self.input_flujo_sangre.setAlignment(Qt.AlignCenter)
#         self.input_flujo_sangre.setStyleSheet(style_input)
#         self.input_flujo_sangre.setValidator(QDoubleValidator(0, 600, 1))
#         self.input_flujo_sangre.editingFinished.connect(
#             lambda: self.escribir_setpoint("bloodFlowControlSetPoint", self.input_flujo_sangre)
#         )
#         grid.addWidget(self.input_flujo_sangre, 0, 5)

#         lbl_u1 = QLabel("ml/min")
#         lbl_u1.setStyleSheet(style_unit)
#         grid.addWidget(lbl_u1, 0, 6)

#         lbl_vel = QLabel("Vel:")
#         lbl_vel.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_vel, 0, 7)

#         self.lbl_velocidad_val = QLabel("0")
#         self.lbl_velocidad_val.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         grid.addWidget(self.lbl_velocidad_val, 0, 8)

#         lbl_u2 = QLabel("rpm")
#         lbl_u2.setStyleSheet(style_unit)
#         grid.addWidget(lbl_u2, 0, 9)

#         # TIEMPOS
#         lbl_tiempo = QLabel("Tiempo Terapia:")
#         lbl_tiempo.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_tiempo, 0, 10)

#         time_widget = QWidget()
#         time_layout = QHBoxLayout(time_widget)
#         time_layout.setContentsMargins(0,0,0,0)
        
#         self.input_horas = QLineEdit("0")
#         self.input_horas.setFixedSize(50, 35)
#         self.input_horas.setStyleSheet(style_input)
#         self.input_horas.editingFinished.connect(lambda: self.escribir_setpoint("heparineTherapyHours", self.input_horas))
        
#         self.input_mins = QLineEdit("0")
#         self.input_mins.setFixedSize(50, 35)
#         self.input_mins.setStyleSheet(style_input)
#         self.input_mins.editingFinished.connect(lambda: self.escribir_setpoint("heparineTherapyMinutes", self.input_mins))

#         time_layout.addWidget(self.input_horas)
#         time_layout.addWidget(QLabel("h"))
#         time_layout.addWidget(self.input_mins)
#         time_layout.addWidget(QLabel("m"))
        
#         grid.addWidget(time_widget, 0, 11, 1, 3)

#         # ----------------------------------------------------------------------
#         # FILA 1: BOMBA DE HEPARINA
#         # ----------------------------------------------------------------------
#         lbl_bHeparina = QLabel("B. Heparina")
#         lbl_bHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_bHeparina, 1, 0)

#         self.toggle_heparina = ToggleSwitch(width=70, height=35)
#         self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk))
#         grid.addWidget(self.toggle_heparina, 1, 1)

#         btn_homeHep = QPushButton("HOME")
#         btn_homeHep.setFixedSize(70, 35)
#         btn_homeHep.setStyleSheet(style_btn)
#         btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
#         btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False)) # Changed pressed to released for latching if needed
        
#         btn_rev_hep = QPushButton("REV")
#         btn_rev_hep.setFixedSize(70,35)
#         btn_rev_hep.setStyleSheet(style_btn)
#         btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton",True))
#         btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))

#         btn_pause_hep = QPushButton("PAUSE")
#         btn_pause_hep.setFixedSize(70,35)
#         btn_pause_hep.setStyleSheet(style_btn)
#         btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume",True))
#         btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))

#         btn_fwd_hep = QPushButton("FWD")
#         btn_fwd_hep.setFixedSize(70,35)
#         btn_fwd_hep.setStyleSheet(style_btn)
#         btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton",True))
#         btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))

#         grid.addWidget(btn_homeHep, 1, 2)
#         grid.addWidget(btn_rev_hep, 1, 3)
#         grid.addWidget(btn_pause_hep, 1, 4)
#         grid.addWidget(btn_fwd_hep, 1, 5)

#         lbl_indHeparina = QLabel("Heparina")
#         lbl_indHeparina.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_indHeparina, 1,6)
        
#         self.indHeparinCurrentDosage = QLabel("0.0")
#         self.indHeparinCurrentDosage.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.indHeparinCurrentDosage.setFixedSize(100,35)
#         grid.addWidget(self.indHeparinCurrentDosage,1,7)
        
#         lbl_unit_hep = QLabel("ml")
#         lbl_unit_hep.setStyleSheet(style_unit)
#         lbl_unit_hep.setFixedSize(100,35)
#         grid.addWidget(lbl_unit_hep,1,8)

#         # ----------------------------------------------------------------------
#         # FILA 2: B. DIALIZANTE
#         # ----------------------------------------------------------------------
#         lbl_dializante = QLabel("B. Dializante")
#         lbl_dializante.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dializante, 2, 0)

#         self.toggle_dializante = ToggleSwitch(width=70, height=35)
#         self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk))
#         grid.addWidget(self.toggle_dializante, 2,1)

#         self.lbl_indSDializante = QLabel("0.0")
#         self.lbl_indSDializante.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indSDializante.setFixedSize(100,35)
#         grid.addWidget(self.lbl_indSDializante, 2,2)

#         lbl_unit_indSdializante = QLabel("%")
#         lbl_unit_indSdializante.setStyleSheet(style_unit)
#         lbl_unit_indSdializante.setFixedSize(100,35)
#         grid.addWidget(lbl_unit_indSdializante, 2, 3)

#         lbl_e_tOpBD = QLabel("Tiempo Op.")
#         lbl_e_tOpBD.setStyleSheet(style_lbl)
#         lbl_e_tOpBD.setFixedSize(100,35)
#         grid.addWidget(lbl_e_tOpBD, 2, 4)

#         self.lbl_tiempo_OpBD = QLineEdit("00:00")
#         self.lbl_tiempo_OpBD.setStyleSheet(style_input)
#         self.lbl_tiempo_OpBD.setFixedSize(100,35)
#         grid.addWidget(self.lbl_tiempo_OpBD,2,5)

#         lbl_e_tRestBD = QLabel("T. Restante")
#         lbl_e_tRestBD.setStyleSheet(style_lbl)
#         lbl_e_tRestBD.setFixedSize(100,35)
#         grid.addWidget(lbl_e_tRestBD,2,6)

#         self.lbl_tiempo_RestBD = QLabel("00:00")
#         self.lbl_tiempo_RestBD.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_tiempo_RestBD.setFixedSize(100,40)
#         grid.addWidget(self.lbl_tiempo_RestBD,2,7)


        
#          # ----------------------------------------------------------------------
#         # FILA 3: B. Ultra Filtrado
#         # ----------------------------------------------------------------------
#         lbl_ultrafiltado = QLabel("B. UF")
#         lbl_ultrafiltado.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_ultrafiltado,3,0)

#         self.toggle_uf = ToggleSwitch(width=70, height=35)
#         self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt","dialyUltraFPumpStoptButt",chk))
#         grid.addWidget(self.toggle_uf,3,1)

#         self.lbl_indUF = QLabel("0.0")
#         self.lbl_indUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indUF.setFixedSize(100,35)
#         grid.addWidget(self.lbl_indUF, 3, 2)

#         lbl_unit_indUF = QLabel("L/h")
#         lbl_unit_indUF.setStyleSheet(style_unit)
#         lbl_unit_indUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indUF, 3,3)

#         lbl_e_tOpBUF = QLabel("Tiempo Op.")
#         lbl_e_tOpBUF.setStyleSheet(style_lbl)
#         lbl_e_tOpBUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_e_tOpBUF, 3, 4)

#         self.lbl_tiempo_opBUF = QLineEdit("00,00")
#         self.lbl_tiempo_opBUF.setStyleSheet(style_input)
#         self.lbl_tiempo_opBUF.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_tiempo_opBUF, 3, 5)

#         lbl_e_tRestBUF = QLabel("T. Restante")
#         lbl_e_tRestBUF.setStyleSheet(style_lbl)
#         lbl_e_tRestBUF.setFixedSize(100, 35)
#         grid.addWidget(lbl_e_tRestBUF, 3, 6)

#         self.lbl_tiempo_RestBUF = QLabel("00:00")
#         self.lbl_tiempo_RestBUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_tiempo_RestBUF.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_tiempo_RestBUF, 3, 7)

#         # ----------------------------------------------------------------------
#         # FILA 4: B. Bicarbonato Na+
#         # ----------------------------------------------------------------------
#         lbl_bicarbonato = QLabel("B. Na+")
#         lbl_bicarbonato.setStyleSheet(style_lbl)
#         lbl_bicarbonato.setFixedSize(100, 35)
#         grid.addWidget(lbl_bicarbonato, 4, 0)

#         self.toggle_Na = ToggleSwitch(width=70, height=35)
#         self.toggle_Na.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt","dialyBicarbonPumpStopButt",chk))
#         grid.addWidget(self.toggle_Na, 4, 1)

#         self.lbl_indBNa = QLabel("0.0")
#         self.lbl_indBNa.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indBNa.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indBNa, 4, 2)

#         lbl_unit_indBNa = QLabel("%")
#         lbl_unit_indBNa.setStyleSheet(style_unit)
#         lbl_unit_indBNa.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBNa, 4, 3)
                                                                                                                                                                                                                                                                         
#         # ----------------------------------------------------------------------
#         # FILA 5: B. Acido Citrico
#         # ----------------------------------------------------------------------
#         lbl_acidocitrico = QLabel("B. A. Citrico")
#         lbl_acidocitrico.setStyleSheet(style_lbl)
#         lbl_acidocitrico.setFixedSize(100, 35)
#         grid.addWidget(lbl_acidocitrico, 5, 0)

#         self.toggle_acidocitrico = ToggleSwitch(width=70, height=35)
#         self.toggle_acidocitrico.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt","dialyCitricAcPumpStopButt",chk))
#         grid.addWidget(self.toggle_acidocitrico, 5, 1)

#         self.lbl_indBAC = QLabel("0.0")
#         self.lbl_indBAC.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indBAC.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indBAC, 5, 2)

#         lbl_unit_indBAC = QLabel("%")
#         lbl_unit_indBAC.setStyleSheet(style_unit)
#         lbl_unit_indBAC.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBAC, 5, 3)

#         # ----------------------------------------------------------------------
#         # FILA 6: B. Purga de Aire
#         # ----------------------------------------------------------------------
#         lbl_purga = QLabel("B. Purga")
#         lbl_purga.setStyleSheet(style_lbl)
#         lbl_purga.setFixedSize(100, 35)
#         grid.addWidget(lbl_purga, 6, 0)

#         self.toggle_purga = ToggleSwitch(width=70, height=35)
#         self.toggle_purga.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt","dialyPurgePumpStopButt",chk))
#         grid.addWidget(self.toggle_purga, 6, 1)

#         self.lbl_indPurga = QLabel("0.0")
#         self.lbl_indPurga.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
#         self.lbl_indPurga.setFixedSize(100, 35)
#         grid.addWidget(self.lbl_indPurga, 6, 2)

#         lbl_unit_indPurga = QLabel("%")
#         lbl_unit_indPurga.setStyleSheet(style_unit)
#         lbl_unit_indPurga.setFixedSize(100, 35)
#         grid.addWidget(lbl_unit_indBAC, 6, 3)


#         # ----------------------------------------------------------------------
#         # FILAS 3 a 7: BOMBAS SIMPLES
#         # ----------------------------------------------------------------------
#         bombas_simples = [
#             #(3, "B. UltraF", "dialyUltraFPumpStartButt", "dialyUltraFPumpStoptButt"), 
#             #(4, "B. Bicarbonato", "dialyBicarbonPumpStartButt", "dialyBicarbonPumpStopButt"),
#             #(5, "B. Acido Cítrico", "dialyCitricAcPumpStartButt", "dialyCitricAcPumpStopButt"),
#             #(6, "B. Purga Aire", "dialyPurgePumpStartButt", "dialyPurgePumpStopButt"),
#             (7, "C. Balance", "dialiserBalChambStrButt", "dialiserBalChambStpButt"),
#         ]

#         self.toggles_simples = {} 

#         for row_idx, nombre, tag_start, tag_stop in bombas_simples:
#             lbl = QLabel(nombre)
#             lbl.setStyleSheet(style_lbl)
#             grid.addWidget(lbl, row_idx, 0)

#             toggle = ToggleSwitch(width=70, height=35)
#             toggle.toggled.connect(
#                 lambda chk, ts=tag_start, tp=tag_stop: self.manejar_bomba_doble(ts, tp, chk)
#             )
#             self.toggles_simples[tag_start] = toggle
#             grid.addWidget(toggle, row_idx, 1)

#         # ----------------------------------------------------------------------
#         # FILA 8: DOSIS HEPARINA (Input)
#         # ----------------------------------------------------------------------
#         lbl_dosis = QLabel("Dosis Hep.")
#         lbl_dosis.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_dosis, 8, 0)

#         self.input_dosis_hep = QLineEdit("0.0")
#         self.input_dosis_hep.setFixedSize(100, 35)
#         self.input_dosis_hep.setAlignment(Qt.AlignCenter)
#         self.input_dosis_hep.setStyleSheet(style_input)
#         self.input_dosis_hep.setValidator(QDoubleValidator(0.0, 50.0, 1))
#         self.input_dosis_hep.editingFinished.connect(
#             lambda: self.escribir_setpoint("heparineTherapyDosage", self.input_dosis_hep)
#         )
#         grid.addWidget(self.input_dosis_hep, 8, 1)

#         lbl_udosis = QLabel("ml/h")
#         lbl_udosis.setStyleSheet(style_unit)
#         grid.addWidget(lbl_udosis, 8, 2)

#         layout.addWidget(self.control_area, 0, 0)

#         # ==================================================================
#         #          AREA 2: INDICADORES LED
#         # ==================================================================
#         self.ind_area = QWidget()
#         self.ind_area.setFixedSize(180,726)
#         grid_ind_area = QGridLayout(self.ind_area)
#         grid_ind_area.setSpacing(10)
#         grid_ind_area.setContentsMargins(10, 10,10, 10)

#         led_nombres = ["B. Sangre","B. Dializante","B. Heparina","B. UltraF","Purga de\n aire","C.Balance","A. sangre","C.Deaereación","Fin de\n ciclos","Protec.\n Resist.","S.Dializante","Nivel de\ntanque"]   
#         self.leds = []
#         for i, nombre in enumerate(led_nombres):
#             lbl = QLabel(nombre)
#             lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
#             lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#             grid_ind_area.addWidget(lbl, i, 0)

#             led = LED()
#             led.setFixedSize(45, 45)
#             grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
#             self.leds.append(led)

#         layout.addWidget(self.ind_area, 0, 1, 2, 1)

#         # ==============================================================================================
#         # AREA 3: VÁLVULAS
#         # ==============================================================================================
#         self.ctrl_valvulas = QWidget()
#         self.ctrl_valvulas.setFixedSize(1300,240)
#         layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas) 
#         layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
#         layout_ctrl_valvulas.setSpacing(10)
        
#         self.container_mop = QFrame()
#         self.container_mop.setFixedSize(110,240)
#         self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
#         layout_mop = QVBoxLayout(self.container_mop) 
       
#         lbl_modo = QLabel("Modo de \n Op.")
#         lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
#         lbl_modo.setAlignment(Qt.AlignCenter)
        
#         self.toggle_modo = ToggleSwitch(width=60, height=30, active_color="#facc15") 
#         self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))

#         layout_mop.addStretch()
#         layout_mop.addWidget(lbl_modo)
#         layout_mop.setSpacing(10)
#         layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
#         layout_mop.addStretch()
        
#         layout_ctrl_valvulas.addWidget(self.container_mop)

#         self.container_val = QWidget()
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
#             parts = desc.split(" ",1)
#             codigo = parts[0]
#             texto = parts[1] if len(parts) > 1 else ""

#             card = ValveCard(codigo, texto)
#             self.valvulas_map[tag] = card
#             grid_valvulas_area.addWidget(card, r, c)
#             card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

#         layout_ctrl_valvulas.addWidget(self.container_val)
#         layout.addWidget(self.ctrl_valvulas, 1, 0)    

#     def actualizar_valores(self, nuevos_valores):
#         self.valores = nuevos_valores
        
#         # ACTUALIZAR LEDS (Tags verificados)
#         variables_leds = [
#             "bloodPumpStartButton",       
#             "dialyserPumpStartButton",    
#             "heparinePumpsStartButton",   
#             "dialyUltraFPumpStartButt",   
#             "dialyPurgePumpStartButt",    
#             "dialiserBalChambStrButt",    
#             "airBubbleInBloodDetected",   
#             "dialyDeaerChamLevSwitch",    
#             "dialyBalanceChambCycleEnd",  
#             "watterTankHeaterProtect",    
#             "bloodInDialyCircDetected",   
#             "dialyTankHiLevelSwitch"      
#         ]
#         for i, led in enumerate(self.leds):
#             if i < len(variables_leds):
#                 nombre_var = variables_leds[i]
#                 valor = self.valores.get(nombre_var, 0.0)
#                 estado = 'on' if valor > 0 else 'off'
#                 if led.state != estado:
#                     led.set_state(estado)
        
#         # ACTUALIZAR VÁLVULAS
#         for tag, card in self.valvulas_map.items():
#             val = self.valores.get(tag, 0.0)
#             nuevo_estado = True if val > 0 else False
#             if card.toggle.is_checked() != nuevo_estado:
#                 if hasattr(card.toggle, "setChecked"):
#                     card.toggle.setChecked(nuevo_estado)
        
#         # ACTUALIZAR INDICADORES NUMÉRICOS
#         vel_sangre = self.valores.get("bloodSpeedVariableData", 0.0)
#         self.lbl_velocidad_val.setText(f"{vel_sangre:.0f}")
        
#         val_heparina = self.valores.get("heparineCurrentDosage", 0.0) # 0x05 dosis de heparina actual
#         self.indHeparinCurrentDosage.setText(f"{val_heparina:.1f}")

#         in_heparinTherapyDosage = self.valores.get("heparineTherapyDosage", 0.0)
#         if not self.input_dosis_hep.hasFocus():
#             self.input_dosis_hep.setText(f"{in_heparinTherapyDosage:.1f}")


#         # ACTUALIZAR TOGGLES DE BOMBAS (CORREGIDO EL ERROR DE SINTAXIS)
#         act_toogle_sangre = self.valores.get("bloodPumpStartButton", 0.0)
#         if hasattr(self.toggle_sangre, "setChecked"):
#             self.toggle_sangre.setChecked(act_toogle_sangre > 0)

#         act_toogle_heparina = self.valores.get("heparinePumpsStartButton", 0.0)
#         if hasattr(self.toggle_heparina, "setChecked"):
#             self.toggle_heparina.setChecked(act_toogle_heparina > 0)

#         act_toggle_dializante = self.valores.get("dialyserPumpStartButton", 0.0)
#         if hasattr(self.toggle_dializante, "setChecked"):
#             self.toggle_dializante.setChecked(act_toggle_dializante > 0)
        
#         act_toggle_acidocitrico = self.valores.get("dialyCitricAcPumpStartButt", 0.0)
#         if hasattr(self.toggle_acidocitrico, "setChecked"):
#             self.toggle_acidocitrico.setChecked(act_toggle_acidocitrico > 0)

#         act_toggle_heparina = self.valores.get("heparinePumpsStartButton", 0.0)
#         if hasattr(self.toggle_heparina, "setChecked"):
#             self.toggle_heparina.setChecked(act_toggle_heparina > 0)

#         act_toggle_na = self.valores.get("dialyBicarbonPumpStartButt", 0.0)
#         if hasattr(self.toggle_Na, "setChecked"):
#             self.toggle_Na.setChecked(act_toggle_na > 0)

#         act_toggle_purga = self.valores.get("dialyPurgePumpStartButt", 0.0)
#         if hasattr(self.toggle_purga, "setChecked"):
#             self.toggle_purga.setChecked(act_toggle_purga > 0)
        
#         act_toggle_uf = self.valores.get("dialyUltraFPumpStartButt", 0.0)
#         if hasattr(self.toggle_uf, "setChecked"):
#             self.toggle_uf.setChecked(act_toggle_uf > 0)
        

        
#         act_toggle_modo = self.valores.get("dialyCircuitElementsOpSel", 0.0)
#         if hasattr(self.toggle_modo, "setChecked"):
#             self.toggle_modo.setChecked(act_toggle_modo > 0)
        

#         # 5. ACTUALIZAR TOGGLES SIMPLES
#         for tag_start, toggle in self.toggles_simples.items():
#             val = self.valores.get(tag_start, 0.0)
#             if hasattr(toggle, "setChecked"):
#                 toggle.setChecked(val > 0)

#         # 6. ACTUALIZAR INPUT DOSIS (Solo si no tiene foco)
#         if hasattr(self, 'dosis_heparina_edit'):
#             val_dosis = self.valores.get("heparineTherapyDosage", 0.0)
#             if not self.dosis_heparina_edit.hasFocus():
#                 self.dosis_heparina_edit.setText(f"{val_dosis:.1f}")

#     def manejar_bomba_doble(self, tag_start, tag_stop, activado):
#         if activado:
#             print(f"[BOMBA] Arrancando {tag_start}")
#             self.escribir_comando(tag_start, True)
#             self.escribir_comando(tag_stop, False) 
#         else:
#             print(f"[BOMBA] Deteniendo {tag_stop}")
#             self.escribir_comando(tag_stop, True) 
#             self.escribir_comando(tag_start, False)

    # def escribir_setpoint(self, tag, widget_input):
    #     try:
    #         texto = widget_input.text().replace(',', '.')
    #         valor = float(texto)
    #         print(f"[SETPOINT] Escribiendo {tag} = {valor}")
            
    #         found = False
    #         for grupo in [0x02, 0x03, 0x04, 0x05, 0x06]:
    #             if grupo in VARIABLES:
    #                 for id_var, info in VARIABLES[grupo].items():
    #                     if info["tag"] == tag:
    #                         if self.parent_window and hasattr(self.parent_window, 'serial'):
    #                             self.parent_window.serial.escribir_double(id_var, valor)
    #                         found = True
    #                         break
    #             if found: break
            
    #         if not found:
    #             print(f"[ERROR] No se encontró ID para tag analógico {tag}")

    #     except ValueError:
    #         print("[ERROR] Valor numérico inválido")

    # def escribir_comando(self, tag, estado):
    #     print(f"[COMANDO] Usuario cambió {tag} a {estado}")
    #     direccion = -1
    #     if 0x01 in VARIABLES:
    #         for id_var, info in VARIABLES[0x01].items():
    #             if info["tag"] == tag:
    #                 direccion = id_var
    #                 break
        
    #     if direccion != -1:
    #         if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial.conectado:
    #             try:
    #                 if self.parent_window.serial.conectado:
    #                     print(f" -> Enviando: Addr {direccion} Val {estado}")
    #                     self.parent_window.serial.escribir_booleano(direccion, estado)
    #                 else:
    #                     print(" -> Error: Serial no conectado")
    #             except AttributeError:
    #                 print(f"[INFO] Fallo de envió")    
    #         else:
    #             print(f" -> Error: No se encontró ID para el tag '{tag}'")