# gui/therapy/therapy_config_screen.py
# Pantalla de configuración de parámetros de terapia (sin selección de modo)

from tkinter import dialog

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QEvent


from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit
from logic.calculos import convertir_flujo_a_ciclos, convertir_litros_h_a_ml_min
from core.state_manager import TreatmentPhase

import logging
logger = logging.getLogger(__name__)

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

class PushbuttonEvent(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(Qt.NoFocus) 


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
        # self.setStyleSheet("background: #0f172a;")
        self.write_hold_off = {}
        self.toggle_hold_off = {}
        self.status_code = 0.0
        self.setup_ui()



    def setup_ui(self):
        # self.setStyleSheet("""
        #     background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        #                                stop:0 #1a2a4a, stop:1 #0f172a);
        #     color: #f8fafc;
        # """)

        button_style = """
            QPushButton { background: #0f172a; color: #ffffff; border-radius: 20px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """

        self.style_enabled = """
            QPushButton { background: #39ec21; color: #ffffff; font-weight: bold; font-size: 20px; border-radius: 15px; border: 3px solid #1e293b; }
            QPushButton:pressed { background: #334155; }
        """
        self.style_disabled = """
            QPushButton { background: #334155; color: #94a3b8; font-weight: bold; font-size: 20px; border-radius: 15px; border: 3px solid #1e293b; }
        """
        self.style_stop_enabled = """
             QPushButton { background: #DD2911; color: #ffffff; font-weight: bold; font-size: 20px; border-radius: 15px; border: 3px solid #1e293b; }
             QPushButton:pressed { background: #334155; }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
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

        # ─── LAYOUT PRINCIPAL DE DOS COLUMNAS ────────────────────────────────
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(30)
        
        col1_layout = QVBoxLayout() # Columna 1: Bombas y Filtro
        col1_layout.setSpacing(120)
        
        col2_layout = QVBoxLayout() # Columna 2: Parámetros
        
        main_layout.addLayout(columns_layout)

        # =====================================================================
        # COLUMNA 1: CONFIGURACIÓN Y OPERACIÓN DE BOMBAS
        # =====================================================================
        
        # label_style = "color: #000000; font-size: 22px; font-weight: bold;"
        label_style = "color: #000000; font-size: 22px; font-weight: bold; min-height: 50px;"
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

        # 2. Bomba de Sangre
        blood_operation_frame = QFrame()
        blood_operation_frame.setStyleSheet("""
                QFrame {
                    border: 2px solid #5c5c5c;
                    border-radius: 8px;                
                    background-color: transparent;
                }
                QLabel { border: none; color: #2b2b2b; font-size: 18px; font-weight: bold; }
        """)      
        blood_layout = QHBoxLayout(blood_operation_frame)
        blood_layout.setContentsMargins(15, 15, 15, 15)
        blood_layout.setSpacing(15)

        lbl_bloob_pump = QLabel("Bomba de Sangre")
        lbl_bloob_pump.setStyleSheet(label_style)
        lbl_bloob_pump.setAlignment(Qt.AlignCenter)
        blood_layout.addWidget(lbl_bloob_pump)
        blood_layout.addStretch()

        self.btn_start_blood_pump = PushbuttonEvent("START", self)
        self.btn_start_blood_pump.setFixedSize(120, 80)
        self.btn_start_blood_pump.setStyleSheet(self.style_enabled)
        self.btn_start_blood_pump.pressed.connect(self._start_blood_pump)
        blood_layout.addWidget(self.btn_start_blood_pump)

        self.btn_stop_blood_pump = PushbuttonEvent("STOP", self)
        self.btn_stop_blood_pump.setFixedSize(120, 80)
        self.btn_stop_blood_pump.setStyleSheet(self.style_stop_enabled)
        self.btn_stop_blood_pump.pressed.connect(self._stop_blood_pump)
        blood_layout.addWidget(self.btn_stop_blood_pump)

        # 3. Llenado de filtro
        filter_fill_frame = QFrame()
        filter_fill_frame.setStyleSheet("""
                QFrame {
                    border: 2px solid #5c5c5c;
                    border-radius: 8px;                
                    background-color: transparent;
                }
                QLabel { border: none; color: #2b2b2b; font-size: 18px; font-weight: bold; }
        """)
        filter_fill_layout = QHBoxLayout(filter_fill_frame)
        filter_fill_layout.setContentsMargins(15, 15, 15, 15)
        filter_fill_layout.setSpacing(15)

        lbl_filter_fill_button = QLabel("Llenado de filtro")
        lbl_filter_fill_button.setStyleSheet(label_style)
        lbl_filter_fill_button.setAlignment(Qt.AlignCenter)
        filter_fill_layout.addWidget(lbl_filter_fill_button)
        filter_fill_layout.addStretch()

        self.btn_filter_fill = PushbuttonEvent("START",self)
        self.btn_filter_fill.setFixedSize(120, 80)
        self.btn_filter_fill.setStyleSheet(self.style_enabled)
        self.btn_filter_fill.pressed.connect(self._start_filter_fill)
        filter_fill_layout.addWidget(self.btn_filter_fill)

        # Agregamos los frames a la Columna 1
        col1_layout.addWidget(blood_operation_frame)
        col1_layout.addWidget(filter_fill_frame)
        col1_layout.addStretch(1)

        # =====================================================================
        # COLUMNA 2: PARÁMETROS DE TERAPIA (Una sola columna)
        # =====================================================================
        
        params_frame = QFrame()
        params_frame.setStyleSheet("background: transparent; border-radius: 10px; padding: 25px;")
        params_layout = QGridLayout(params_frame)
        params_layout.setSpacing(20)

        # params_layout.setColumnStretch(0, 1) # Las etiquetas toman todo el espacio posible
        # params_layout.setColumnStretch(1, 0) # Los inputs se quedan con su tamaño fijo


        # Flujo de Sangre (Qb)
        lbl_blood_flow = QLabel("Flujo de Sangre (Qb, mL/min):")
        lbl_blood_flow.setStyleSheet(label_style)
        lbl_blood_flow.setAlignment(Qt.AlignRight)
        self.input_blood_flow = ClickableLineEdit("0.0")
        self.input_blood_flow.setFixedSize(120, 50)
        self.input_blood_flow.setAlignment(Qt.AlignCenter)
        self.input_blood_flow.setStyleSheet(input_style)
        self.input_blood_flow.setReadOnly(True)
        self.input_blood_flow.clicked.connect(
            lambda: self.open_numpad("bloodFlowControlSetPoint", self.input_blood_flow, "Flujo de Sangre (Qb)")
        )
        params_layout.addWidget(lbl_blood_flow, 0, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_blood_flow, 0, 1)

        # Flujo Dializante (Qd)
        lbl_dialysate_flow = QLabel("Flujo Dializante (Qd, mL/min):")
        lbl_dialysate_flow.setStyleSheet(label_style)
        lbl_dialysate_flow.setAlignment(Qt.AlignRight)
        self.input_dialysate_flow = ClickableLineEdit("0.0")
        self.input_dialysate_flow.setFixedSize(120, 50)
        self.input_dialysate_flow.setAlignment(Qt.AlignCenter)
        self.input_dialysate_flow.setStyleSheet(input_style)
        self.input_dialysate_flow.setReadOnly(True)
        self.input_dialysate_flow.clicked.connect(self._handle_cb_flow_input)
        params_layout.addWidget(lbl_dialysate_flow, 1, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_dialysate_flow, 1, 1)

        # Flujo de ultrafiltración
        lbl_uf_flow = QLabel("Flujo UF (L/h):")
        lbl_uf_flow.setStyleSheet(label_style)
        lbl_uf_flow.setAlignment(Qt.AlignRight)
        self.lbl_input_UF = ClickableLineEdit("0.0")
        self.lbl_input_UF.setFixedSize(120, 50)
        self.lbl_input_UF.setAlignment(Qt.AlignCenter)
        self.lbl_input_UF.setStyleSheet(input_style)
        self.lbl_input_UF.setReadOnly(True)
        self.lbl_input_UF.clicked.connect(self._handle_uf_flow_input)
        params_layout.addWidget(lbl_uf_flow, 2, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.lbl_input_UF, 2, 1)

        # Temperatura
        lbl_temperature = QLabel("Temperatura (°C):")
        lbl_temperature.setStyleSheet(label_style)
        lbl_temperature.setAlignment(Qt.AlignRight)
        self.input_temperature = ClickableLineEdit("0.0")
        self.input_temperature.setFixedSize(120, 50)
        self.input_temperature.setAlignment(Qt.AlignCenter)
        self.input_temperature.setStyleSheet(input_style)
        self.input_temperature.setReadOnly(True)
        self.input_temperature.clicked.connect(
            lambda: self.open_numpad("dialyTempControlSetPoint", self.input_temperature, "Temperatura")
        )
        params_layout.addWidget(lbl_temperature, 3, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_temperature, 3, 1)

        # Conductividad
        lbl_conductivity = QLabel("Conductividad (mS/cm):")
        lbl_conductivity.setStyleSheet(label_style)
        lbl_conductivity.setAlignment(Qt.AlignRight)
        self.input_conductivity = ClickableLineEdit("0.0")
        self.input_conductivity.setFixedSize(120, 50)
        self.input_conductivity.setAlignment(Qt.AlignCenter)
        self.input_conductivity.setStyleSheet(input_style)
        self.input_conductivity.setReadOnly(True)
        self.input_conductivity.clicked.connect(
            lambda: self.open_numpad("dialyCondControlSetPoint", self.input_conductivity, "Conductividad")
        )
        params_layout.addWidget(lbl_conductivity, 4, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_conductivity, 4, 1)

        # Duración de Terapia (hh:mm)
        lbl_duration = QLabel("T. Terapia (hh:mm)")
        lbl_duration.setStyleSheet(label_style)
        lbl_duration.setAlignment(Qt.AlignRight)
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
        params_layout.addWidget(lbl_duration, 5, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_duration, 5, 1)

        # Agregamos los parámetros a la Columna 2
        col2_layout.addWidget(params_frame)
        col2_layout.addStretch()

        # Agregamos las columnas al layout horizontal que está en el layout principal
        columns_layout.addLayout(col1_layout)
        columns_layout.addLayout(col2_layout)


        main_layout.addStretch(1)


    def _start_blood_pump(self):
        """Maneja el encendido seguro de la bomba de sangre"""
        try:
            logger.info("Comando START bomba de sangre solicitado")
          
            self._handle_dual_pump_toggle("bloodPumpStartButton", "bloodPumpStopButton", True)
            self.setFocus()        

        except Exception as e:
            logger.error(f"Error en _start_blood_pump: {e}", exc_info=True)

    def _start_filter_fill(self):
        try:
            logger.info("Comando Start de llenado de filtro")
            self.on_user_boolean_command("dialyFilterFillButton",True)
            if hasattr(self.parent_window, '_start_filter'):
                self.parent_window._start_filter()
            self.setFocus()
        except Exception as e:
            logger.error(f"Error en _start_filter_fill: {e}",exc_info=True)

    def _stop_blood_pump(self):
        """Maneja el apagado seguro de la bomba de sangre"""
        try:
            logger.info("Comando STOP bomba de sangre solicitado")

            # 1. Deshabilitar loop de control
            # self.on_user_boolean_command("bloodControlLoopEnable", False)

            # 2. Activar secuencia de parada de la bomba
            self._handle_dual_pump_toggle("bloodPumpStartButton", "bloodPumpStopButton", False)

            # 3. Detener movimiento hacia adelante
            # self.on_user_boolean_command("bloodPumpFWDButton", False)
            self.setFocus()
        except Exception as e:
            logger.error(f"Error en _stop_blood_pump: {e}", exc_info=True)

    def _update_filter_fill_button_state(self, enable: bool):
        """Habilita/deshabilita botón de llenado de filtro"""
        if enable:
            self.btn_filter_fill.setEnabled(True)
            self.btn_filter_fill.setStyleSheet(self.style_enabled)
            logger.info("Botón Llenado de Filtro → HABILITADO (Estado 7)")
        else:
            self.btn_filter_fill.setEnabled(False)
            self.btn_filter_fill.setStyleSheet(self.style_disabled)
            logger.debug("Botón Llenado de Filtro → DESHABILITADO")

    def _update_bloop_pump_controls_state(self):   
        current_phase = None
        if hasattr(self, 'parent_window') and hasattr(self.parent_window, 'state'):
            current_phase = self.parent_window.state.current_phase
        status_code = int(self.current_values.get("primingProcessStatus", 0))

        # Restricción aplicada solo a botones de bomba de sangre.
        # Se bloquean en RUNNING o en estado 14 de priming.
        if current_phase == TreatmentPhase.RUNNING or status_code == 14:
            self.btn_start_blood_pump.setEnabled(False)
            self.btn_stop_blood_pump.setEnabled(False)
            self.btn_start_blood_pump.setStyleSheet(self.style_disabled)
            self.btn_stop_blood_pump.setStyleSheet(self.style_disabled)
            logger.debug(f"Bomba de sangre bloqueada (phase={current_phase}, priming={status_code})")
            return
        
        pump_start_state = self.current_values.get("bloodPumpStartButton", 0)         
        pump_stop_state = self.current_values.get("bloodPumpStopButton", 0)
        # fwd_state = self.current_values.get("bloodPumpFWDButton", 0)
        
        logger.info(f" Start: {pump_start_state}, Stop: {pump_stop_state} ") 
        can_start = True  
        can_stop = False  
        # Estado: Bomba funcionando (START debería estar deshabilitado, STOP habilitado)
        # Esto ocurre cuando el lazo de control está activo, el botón de inicio fue presionado,
        # el botón de parada NO fue presionado y la dirección es hacia adelante.
        if (pump_start_state == 1 and 
            pump_stop_state == 0):
            can_start = False
            can_stop = True
            logger.info("Estado de la bomba: FUNCIONANDO")

        # Estado: Bomba explícitamente detenida (START habilitado, STOP deshabilitado)
        # Esto ocurre cuando el lazo de control está inactivo, el botón de inicio no fue presionado,
        # el botón de parada SI fue presionado y la dirección no es hacia adelante.
        elif (pump_start_state == 0 and 
              pump_stop_state == 1):
            can_start = True
            can_stop = False
            logger.info("Estado de la bomba: DETENIDA")
        
        # Si no encaja en ninguno de los estados anteriores, el comportamiento por defecto ya está definido.
        # (can_start = True, can_stop = False), lo que significa que la app asume un estado detenido/listo para arrancar.
        else:
            logger.info("Estado de la bomba: INDETERMINADO o listo para arrancar (por defecto)")
            #
            # can_start = False
            # can_stop = False
            # Pero normalmente es mejor que el usuario pueda intentar arrancar si no hay una señal clara de que está corriendo.

        # Referencias a los botones
        btn_startbp = self.btn_start_blood_pump
        btn_stop_bp = self.btn_stop_blood_pump

        # Actualizar el estado 'enabled' y el estilo del botón START
        # Solo actualizamos si el estado ha cambiado para evitar repintados innecesarios
        if btn_startbp.isEnabled() != can_start:
            btn_startbp.setEnabled(can_start)
            btn_startbp.setStyleSheet(self.style_enabled if can_start else self.style_disabled)
            logger.info(f"Botón START: {'HABILITADO' if can_start else 'DESHABILITADO'}")

        # Actualizar el estado 'enabled' y el estilo del botón STOP
        if btn_stop_bp.isEnabled() != can_stop:
            btn_stop_bp.setEnabled(can_stop)
            # Usa el estilo apropiado para el botón STOP cuando está habilitado/deshabilitado
            btn_stop_bp.setStyleSheet(self.style_stop_enabled if can_stop else self.style_disabled)
            logger.info(f"Botón STOP: {'HABILITADO' if can_stop else 'DESHABILITADO'}")

    def _handle_single_pump_toggle(self, tag: str, enabled: bool):
        if enabled:
            logger.info(f"Enviando comando START para {tag}")
            self.on_user_boolean_command(tag, True)
            # self.toggle_hold_off[tag] = QDateTime.currentMSecsSinceEpoch() + 1000
        else:
            logger.info(f"Enviando comando STOP para {tag}")
            self.on_user_boolean_command(tag, False)
            # self.toggle_hold_off[tag] = QDateTime.currentMSecsSinceEpoch() + 1000

    def _handle_dual_pump_toggle(self, start_tag: str, stop_tag:str, enabled: bool):
        if enabled:
            logger.info(f"Enviando comando START para {start_tag}")
            self.on_user_boolean_command(start_tag, True)
            self.on_user_boolean_command(stop_tag, False)
            # self.toggle_hold_off[start_tag] = QDateTime.currentMSecsSinceEpoch() + 1000
        else:
            logger.info(f"Enviando comando STOP para {stop_tag}")
            self.on_user_boolean_command(stop_tag, True)
            self.on_user_boolean_command(start_tag, False)
            # self.toggle_hold_off[stop_tag] = QDateTime.currentMSecsSinceEpoch() + 1000
            
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

        self.current_values.get("dialyFilterFillButton", 0.0)
        self.current_values.get("bloodPumpStartButton", 0.0)
        self.current_values.get("bloodPumpStopButton", 0.0)
        self._update_input_display(self.input_blood_flow, "bloodFlowControlSetPoint")
        self._update_input_display(self.input_temperature, "dialyTempControlSetPoint")
        self._update_input_display(self.input_conductivity, "dialyCondControlSetPoint")
        self._update_input_display(self.input_dialysate_flow, self.current_values.get("balanceChamberSetTiming", 0.0)) 
        self._update_input_display(self.lbl_input_UF, self.current_values.get("ultraFilterPumpSpeed", 0.0))
        self._update_time_display(self.input_duration, "heparineTherapyHours", "heparineTherapyMinutes")
        self._update_bloop_pump_controls_state()
        
        if hasattr(self, 'parent_window') and hasattr(self.parent_window, 'state'):
            self.update_state(self.parent_window.state.current_phase)
        



    def _handle_cb_flow_input(self):
        """
        Maneja el input del usuario:
        1. Abre el numpad para pedir mL/min.
        2. Convierte mL/min -> Ciclos/timing.
        3. Escribe el valor en ciclos a la máquina.
        """
        dialog = NumpadDialog(self, initial_value="", title="Flujo Dializante (mL/min)")
        
        if dialog.exec():
            # El usuario ingresó un valor en mL/min (ej: 500)
            value_str = dialog.get_value()
            if hasattr(self.input_dialysate_flow, 'setText'):
                self.input_dialysate_flow.setText(str(value_str))

            flow_ml_min = float(value_str)            
            
            self.setFocus()
            
            try:
                cycles_value = convertir_flujo_a_ciclos(flow_ml_min)
                tag = "balanceChamberSetTiming"
                self.on_user_input_setpoint(tag, cycles_value)
                print(f"Flujo {flow_ml_min} mL/min convertido a {cycles_value} ciclos/timing y enviado a la máquina.")                               
                self.write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
                
            except Exception as e:
                logger.error(f"Error convirtiendo flujo a ciclos: {e}")


  

    def _handle_uf_flow_input(self):
        """Handle UF flow input (L/h → ml/min)."""
    
        # 1. Obtener el valor actual del widget para mostrarlo en el numpad
        current_text = ""
        
        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo UF (L/h)")
    
        if dialog.exec():            
            new_value_str = dialog.get_value()
        
            if new_value_str is not None:
                try:
                    # 2. Convertir a float una sola vez y validar
                    val_float = float(new_value_str)
                
                    # 3. Actualizar la interfaz inmediatamente
                    if hasattr(self.lbl_input_UF, 'setText'):
                        self.lbl_input_UF.setText(f"{val_float:.2f}")

                    # 4. Realizar el cálculo matemático con el número, NO con el texto
                    ml_min = convertir_litros_h_a_ml_min(val_float)
                
                    # 5. Enviar al controlador
                    self.on_user_input_setpoint("ultraFilterPumpSpeed", ml_min)
                
                    # 6. Bloquear actualización de lectura por 3 segundos para dar tiempo al PLC
                    self.write_hold_off["ultraFilterPumpSpeed"] = QDateTime.currentMSecsSinceEpoch() + 3000
                
                except ValueError:
                    logger.error(f"El valor ingresado no es un número válido: {new_value_str}")
                except Exception as e:
                    logger.error(f"Error convirtiendo flujo UF: {e}")



    def _update_input_display(self, widget: ClickableLineEdit, tag_or_value, precision: int = 1):
        if widget.hasFocus():
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

    def update_state(self, phase: TreatmentPhase):
        """Actualiza el estado de botones de bomba de sangre y deja el resto habilitado."""
        treatment_mode = int(self.current_values.get("treatmentModeSelection", 0))
        status_code = int(self.current_values.get("primingProcessStatus", 0))

        logger.debug(f"TherapyConfigScreen - update_state: Phase={phase.name}, Status={status_code}")

        # ==================== BOTÓN LLENADO DE FILTRO ====================
        if phase == TreatmentPhase.PREPARING and status_code == 7:
            self._update_filter_fill_button_state(True)   # Solo se habilita en estado 7
        else:
            self._update_filter_fill_button_state(False)

        # ==================== BOTONES BOMBA DE SANGRE ====================
        self._update_bloop_pump_controls_state()

        # ==================== OTROS BOTONES / CONTROLES ====================
        # Mantener inputs habilitados incluso durante terapia activa (RUNNING/PAUSED)
        enabled_inputs = phase not in (TreatmentPhase.CLEANING, TreatmentPhase.ERROR)

        for widget in [self.input_blood_flow, self.input_dialysate_flow,
                       self.lbl_input_UF, self.input_temperature, self.input_conductivity,
                       self.input_duration]:
            if hasattr(widget, 'setEnabled'):
                widget.setEnabled(enabled_inputs)

   

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

    
