# gui/therapy/therapy_config_screen.py
# Pantalla de configuración de parámetros de terapia (sin selección de modo)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QEvent

import logging
from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit
from logic.calculos import convertir_flujo_a_ciclos, convertir_ciclos_a_flujo

logger = logging.getLogger(__name__)

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

class PushbuttonEvent(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

    def event(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            self.setDown(True)
            self.pressed.emit()
            return True

        elif event.type() in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            self.setDown(False)
            self.released.emit()
            return True

        return super().event(event)
    
class TherapyConfigScreen(QWidget):
    """
    Pantalla de configuración de parámetros numéricos para la terapia.
    Solo inputs de heparina, flujos, temperatura, conductividad, sodio y duración.
    """
    valueChanged = Signal(str, float)  # Emite el tag y el nuevo valor
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)    


    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}         
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #0f172a;")
        self.write_hold_off = {}
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #1a2a4a, stop:1 #0f172a);
            color: #f8fafc;
        """)

        button_style = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 20px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        logger.info("Configuracion de terapia (V1.0.0)")
        # Título
        title = QLabel("Configuración de Terapia")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep1)

        # ── Parámetros ───────────────────────────────────────────────────────
        params_frame = QFrame()
        params_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 25px;")
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
                min-width: 110px;
            }
            ClickableLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
            }
        """

        # Heparina
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

        # Flujo de Sangre (Qb)
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

        # Flujo Dializante (Qd)
        lbl_dialysate_flow = QLabel("Flujo Dializante (Qd, mL/min):")   # FLUJO DE CÁMARA DE BALANCE
        lbl_dialysate_flow.setStyleSheet(label_style)
        self.input_dialysate_flow = ClickableLineEdit("0.0")
        self.input_dialysate_flow.setFixedSize(120, 50)
        self.input_dialysate_flow.setAlignment(Qt.AlignCenter)
        self.input_dialysate_flow.setStyleSheet(input_style)
        self.input_dialysate_flow.setReadOnly(True)
        self.input_dialysate_flow.clicked.connect(self._handle_cb_flow_input)
        params_layout.addWidget(lbl_dialysate_flow, 2, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_dialysate_flow, 2, 1)

        # Temperatura
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

        # Conductividad
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

   

        # Duración de Terapia (hh:mm)
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
                tag_hours="heparineTherapyHours",
                tag_minutes="heparineTherapyMinutes",
                title="Tiempo de terapia"
            )
        )
        params_layout.addWidget(lbl_duration, 2, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_duration, 2, 3)               

        hep_config_frame = QFrame()    
        hep_config_frame.setStyleSheet("""
                QFrame {
                    border: 2px solid #5c5c5c;
                    border-radius: 8px;
                    background-color: transparent;
                }
                QLabel { border: none; color: #2b2b2b; font-size: 18px; font-weight: bold; }
        """)
        
        # Layout horizontal para el frame (Bolo a la izq, Botones a la derecha)
        hep_frame_layout = QHBoxLayout(hep_config_frame)
        hep_frame_layout.setContentsMargins(15, 15, 15, 15)
        hep_frame_layout.setSpacing(15)

        # -- Sección Bolo (Vertical: Label arriba, Input abajo) --
        bolus_layout = QHBoxLayout()
        bolus_layout.setSpacing(5)
        
        lbl_bolus = QLabel("Bolo (ml):")       
        lbl_bolus.setStyleSheet(label_style) 
        lbl_bolus.setAlignment(Qt.AlignCenter)
        
        self.input_bolus = ClickableLineEdit("0.0")
        self.input_bolus.setFixedSize(120, 50)
        self.input_bolus.setAlignment(Qt.AlignCenter)
        self.input_bolus.setStyleSheet(input_style)
        self.input_bolus.setReadOnly(True)
        self.input_bolus.clicked.connect(
            lambda: self.open_numpad("heparineBolusQuantity", self.input_bolus, "bolo (ml)")
        )
        
        bolus_layout.addWidget(lbl_bolus)
        bolus_layout.addWidget(self.input_bolus)
        
        # Agregamos el layout del bolo al frame principal
        hep_frame_layout.addLayout(bolus_layout)
        
        # Espacio flexible para separar el bolo de los botones (opcional)
        hep_frame_layout.addStretch() 

        # -- Botones de Control --        
        btn_heparin_home = PushbuttonEvent("HOME", self)
        btn_heparin_home.setFixedSize(120, 80)
        btn_heparin_home.setStyleSheet(button_style)
        btn_heparin_home.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", True))
        btn_heparin_home.released.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", False))
        hep_frame_layout.addWidget(btn_heparin_home)

        #  Btn REV heparina
        btn_rev_hep = PushbuttonEvent("REV", self)
        btn_rev_hep.setFixedSize(120 ,80)
        btn_rev_hep.setStyleSheet(button_style)
        btn_rev_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", True))
        btn_rev_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", False))
        hep_frame_layout.addWidget(btn_rev_hep)
        #  Btn FWD heparina
        btn_fwd_hep = PushbuttonEvent("FWD", self)
        btn_fwd_hep.setFixedSize(120, 80)
        btn_fwd_hep.setStyleSheet(button_style)
        btn_fwd_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", True))
        btn_fwd_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", False))
        hep_frame_layout.addWidget(btn_fwd_hep)

        # ─── Agregando al layout principal ──────────────────────────────────
        main_layout.addWidget(params_frame)
        main_layout.addWidget(hep_config_frame) 
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
                padding: 10px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
        """)
        btn_back.clicked.connect(self.parent_window.show_dialysis_screen)
        main_layout.addWidget(btn_back, alignment=Qt.AlignRight)

    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
        current_text = input_widget.text()
        dialog = NumpadDialog(self, initial_value="", title=title)
        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                float_val = float(new_value)
                input_widget.setText(str(new_value))   
                self.current_values[tag] = float_val                         
                self.on_user_input_setpoint(tag, float_val)  #solicitar cambio en comunicación serial
                self.write_hold_off[tag] = QDateTime.currentMSecsSinceEpoch() + 300 
                if hasattr(input_widget, 'clearFocus'):
                    input_widget.clearFocus()
                self.setFocus()

    def open_time_numpad(self, input_widget: ClickableLineEdit,
                         tag_hours: str = None, tag_minutes: str = None,
                         title: str = "Config. Tiempo"):
        current_text = input_widget.text()
       
        dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                input_widget.setText(f"{hours:02d}:{minutes:02d}")
                input_widget.clearFocus()  
                if tag_hours:
                    self.current_values[tag_hours] = float(hours)
                    self.parent_window.current_values[tag_hours] = float(hours)   
                if tag_minutes:
                    self.current_values[tag_minutes] = float(minutes)
                    self.parent_window.current_values[tag_minutes] = float(minutes)
                if tag_hours and tag_minutes:
                    self.on_user_input_setpoint(tag_hours, float(hours))
                    self.on_user_input_setpoint(tag_minutes, float(minutes))
                  

    def _update_time_display(self, widget: ClickableLineEdit, tag_hours: str, tag_minutes: str):
        if not widget.hasFocus():
            hours = int(self.current_values.get(tag_hours, 0))
            minutes = int(self.current_values.get(tag_minutes, 0))
            widget.setText(f"{hours:02d}:{minutes:02d}")

    def update_values(self, new_values: dict):
        """Actualiza solo los campos numéricos y de tiempo"""

        self.current_values = new_values
        current_ms = QDateTime.currentMSecsSinceEpoch()

        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_blood_flow, "bloodFlowControlSetPoint")
        self._update_input_display(self.input_temperature, "dialyTempControlSetPoint")
        self._update_input_display(self.input_conductivity, "dialyCondControlSetPoint")
        self._update_input_display(self.input_bolus, "heparineBolusQuantity")

        self._update_time_display(self.input_duration, "heparineTherapyHours", "heparineTherapyMinutes")
        tag_cb = "balanceChamberSetTiming"
        hold_time = self.write_hold_off.get(tag_cb, 0)

        if current_ms < hold_time:
            pass
        else:
            raw_cycles = self.current_values.get(tag_cb,0.0)
            try:
                if raw_cycles == 0:
                    flow_to_show = 0.0
                else:
                    flow_to_show = convertir_ciclos_a_flujo(raw_cycles)
                    if not self.input_dialysate_flow.hasFocus():
                        self.input_dialysate_flow.setText(f"{flow_to_show:.1f}")
            except Exception as e:
                self.input_dialysate_flow.setText("0.0")



    def _handle_cb_flow_input(self):
        """
        Maneja el input del usuario:
        1. Abre el numpad para pedir mL/min.
        2. Convierte mL/min -> Ciclos/timing.
        3. Escribe el valor en ciclos a la máquina.
        """
        # Obtenemos el texto actual del widget correcto
        current_text = self.input_dialysate_flow.text()

        dialog = NumpadDialog(self, initial_value="", title="Flujo Dializante (mL/min)")
        
        if dialog.exec():
            # El usuario ingresó un valor en mL/min (ej: 500)
            value_str = dialog.get_value()
            if not value_str:return 

            flow_ml_min = float(value_str)            

            self.input_dialysate_flow.setText(f"{flow_ml_min:.1f}")
            self.input_dialysate_flow.clearFocus()
            self.setFocus()
            
            try:
                cycles_value = convertir_flujo_a_ciclos(flow_ml_min)                               
                tag = "balanceChamberSetTiming"
                self.on_user_input_setpoint(tag, cycles_value)                               
                self.write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
                
            except Exception as e:
                logger.error(f"Error convirtiendo flujo a ciclos: {e}")

    def _update_input_display(self, widget: ClickableLineEdit, tag_or_value, precision: int = 1):
        if widget.hasFocus():
            self.setFocus()
            return
        val_to_show = 0.0
        if isinstance(tag_or_value, str):
            val_to_show = self.current_values.get(tag_or_value, 0.0)
        elif isinstance(tag_or_value, (int, float)):
            val_to_show = tag_or_value

        widget.setText(f"{val_to_show:.{precision}f}")

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)
        print("confirmado")


    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

 