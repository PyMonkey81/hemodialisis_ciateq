# gui/therapy/heparin_config_screen.py

from PySide6.QtWidgets import (
    QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QEvent

from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit
from core.state_manager import TreatmentPhase

import logging
logger = logging.getLogger(__name__)


HEPARIN_AUTO_STOP_HOURS_TAG = "heparineAutoStopHours"
HEPARIN_AUTO_STOP_MINUTES_TAG = "heparineAutoStopMinutes"


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

        if event.type() in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            self.setDown(False)
            self.released.emit()
            return True

        return super().event(event)


class HeparinConfigScreen(QWidget):
    valueChanged = Signal(str, float)
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.heparin_pause_latched = False
        self._selected_flujo_index = 1
        self.setup_ui()

    def setup_ui(self):
        self.style_enabled = """
            QPushButton { background: #0f172a<; color: #ffffff; font-weight: bold; font-size: 20px; border-radius: 15px; border: 3px solid #1e293b; }
            QPushButton:pressed { background: #334155; }
        """

        button_style = """
            QPushButton { background: #0f172a; color: #ffffff; border-radius: 20px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """

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

        combo_style = """
            QComboBox {
                color: #1f2937; font-size: 22px; font-weight: bold;
                background: #f8fafc; border: 2px solid #64748b; border-radius: 8px; padding: 8px 12px;
            }
            QComboBox:hover { border-color: #3b82f6; }
            QComboBox QAbstractItemView {
                background: #f8fafc; color: #1f2937; font-size: 20px; font-weight: bold;
                border: 2px solid #64748b; selection-background-color: #3b82f6;
            }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        title = QLabel("Configuración de Heparina")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep1)

        content_layout = QGridLayout()
        content_layout.setSpacing(30)
        main_layout.addLayout(content_layout)

        # Controles de bomba de heparina
        hep_frame = QFrame()
        hep_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #5c5c5c;
                border-radius: 8px;
                background-color: transparent;
            }
            QLabel { border: none; color: #2b2b2b; font-size: 18px; font-weight: bold; }
        """)

        
        hep_frame_layout = QHBoxLayout(hep_frame)
        hep_frame_layout.setContentsMargins(15, 15, 15, 15)
        hep_frame_layout.setSpacing(15)       

        lbl_hep_controls = QLabel("Controles Heparina:")
        lbl_hep_controls.setStyleSheet(label_style)
        hep_frame_layout.addWidget(lbl_hep_controls)
        btn_heparin_home = PushbuttonEvent("HOME", self)
        btn_heparin_home.setFixedSize(120, 80)
        btn_heparin_home.setStyleSheet(button_style)
        btn_heparin_home.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", True))
        # btn_heparin_home.released.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", False))
        hep_frame_layout.addWidget(btn_heparin_home)

        btn_rev_hep = PushbuttonEvent("REV", self)
        btn_rev_hep.setFixedSize(120, 80)
        btn_rev_hep.setStyleSheet(button_style)
        btn_rev_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", True))
        btn_rev_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", False))
        hep_frame_layout.addWidget(btn_rev_hep)

        self.btn_pause_hep = PushbuttonEvent("PAUSE", self)
        self.btn_pause_hep.setFixedSize(120, 80)
        self.btn_pause_hep.setStyleSheet(button_style)
        self.btn_pause_hep.pressed.connect(self._toggle_heparin_pause_resume)
        hep_frame_layout.addWidget(self.btn_pause_hep)

        btn_fwd_hep = PushbuttonEvent("FWD", self)
        btn_fwd_hep.setFixedSize(120, 80)
        btn_fwd_hep.setStyleSheet(button_style)
        btn_fwd_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", True))
        btn_fwd_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", False))
        hep_frame_layout.addWidget(btn_fwd_hep)


        # Controles de bolo de heparina
        bolo_frame = QFrame()
        bolo_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #5c5c5c;
                border-radius: 8px;
                background-color: transparent;
            }
            QLabel { border: none; color: #2b2b2b; font-size: 18px; font-weight: bold; }
        """)
        bolo_frame_layout = QGridLayout(bolo_frame)
        bolo_frame_layout.setSpacing(15)

        lbl_bolus = QLabel("Vol. Bolo Heparina (ml):")
        lbl_bolus.setStyleSheet(label_style)
        lbl_bolus.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.input_bolus = ClickableLineEdit("0.0")
        self.input_bolus.setFixedSize(120, 50)
        self.input_bolus.setAlignment(Qt.AlignCenter)
        self.input_bolus.setStyleSheet(input_style)
        self.input_bolus.setReadOnly(True)
        self.input_bolus.clicked.connect(
            lambda: self.open_numpad("heparineBolusQuantity", self.input_bolus, "Bolo (ml)")
        )
        bolo_frame_layout.addWidget(lbl_bolus, 0, 0, Qt.AlignVCenter)
        bolo_frame_layout.addWidget(self.input_bolus, 0, 1)

        btn_apply_bolus = QPushButton("APLICAR\n BOLO")
        btn_apply_bolus.setFixedHeight(80)
        btn_apply_bolus.setStyleSheet(button_style)
        btn_apply_bolus.clicked.connect(self.apply_bolus)
        bolo_frame_layout.addWidget(btn_apply_bolus, 0, 2)

        lbl_flujo = QLabel("Flujo Heparina (ml/h):")
        lbl_flujo.setStyleSheet(label_style)
        self.combo_flujo = QComboBox()
        self.combo_flujo.addItems(["1.0", "2.0", "3.0", "4.0"])
        self.combo_flujo.setStyleSheet(combo_style)
        self.combo_flujo.setCurrentIndex(0)
        self._selected_flujo_index = self.combo_flujo.currentIndex()
        self.combo_flujo.currentIndexChanged.connect(self._on_flujo_changed)
        bolo_frame_layout.addWidget(lbl_flujo,1, 0, Qt.AlignVCenter)
        bolo_frame_layout.addWidget(self.combo_flujo, 1, 1, Qt.AlignVCenter)        

        # Parametros de heparina y bolo
        params_frame = QFrame()
        params_frame.setStyleSheet("background: transparent; border-radius: 10px; padding: 25px;")
        params_layout = QGridLayout(params_frame)
        params_layout.setSpacing(20)

        lbl_heparin = QLabel("Dosis Heparina (ml):")
        lbl_heparin.setStyleSheet(label_style)
        lbl_heparin.setAlignment(Qt.AlignRight)
        self.input_heparin = ClickableLineEdit("0.0")
        self.input_heparin.setFixedSize(120, 50)
        self.input_heparin.setAlignment(Qt.AlignCenter)
        self.input_heparin.setStyleSheet(input_style)
        self.input_heparin.setReadOnly(True)
        self.input_heparin.clicked.connect(
            lambda: self.open_numpad("heparineTherapyDosage", self.input_heparin, "Dosis Heparina")
        )
        params_layout.addWidget(lbl_heparin, 0, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_heparin, 0, 1)


        lbl_hep_stop_time = QLabel("Paro heparina (hh:mm):")
        lbl_hep_stop_time.setStyleSheet(label_style)
        lbl_hep_stop_time.setAlignment(Qt.AlignRight)
        self.input_heparin_auto_stop = ClickableLineEdit("00:00")
        self.input_heparin_auto_stop.setFixedSize(120, 50)
        self.input_heparin_auto_stop.setAlignment(Qt.AlignCenter)
        self.input_heparin_auto_stop.setStyleSheet(input_style)
        self.input_heparin_auto_stop.setReadOnly(True)
        self.input_heparin_auto_stop.clicked.connect(
            lambda: self.open_time_numpad(
                self.input_heparin_auto_stop,
                HEPARIN_AUTO_STOP_HOURS_TAG,
                HEPARIN_AUTO_STOP_MINUTES_TAG,
                "Paro automático heparina"
            )
        )
        params_layout.addWidget(lbl_hep_stop_time, 1, 0, Qt.AlignVCenter)
        params_layout.addWidget(self.input_heparin_auto_stop, 1, 1)

        content_layout.addWidget(bolo_frame, 0, 0)   # Arriba Izquierda
        content_layout.addWidget(params_frame, 0, 1) # Arriba Derecha

        # Fila 1
        content_layout.addWidget(hep_frame, 1, 0) 

        main_layout.addStretch(1)

#================================FALTA DEFINIR SI HABRÁ FLUJO DE HEPARINA O NO, POR AHORA SE COMENTA EL MÉTODO========================================
    # # def _on_flow_hep_changed(self, index):  #validar el tag
    # def _on_flujo_changed(self, index):

    #     self._selected_flujo_index = index

    #     if hasattr(self, "combo_flujo") and self.combo_flujo is not None:
    #         flujo_value = float(self.combo_flujo.currentText())
    #         self.current_values["dialyHeparineBolusFlow"] = flujo_value
    #         if self.parent_window and hasattr(self.parent_window, "current_values"):
    #             self.parent_window.current_values["dialyHeparineBolusFlow"] = flujo_value
    #         self.on_user_input_setpoint("dialyHeparineBolusFlow", flujo_value)

    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
        dialog = NumpadDialog(self, initial_value="", title=title)
        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                float_val = float(new_value)
                input_widget.setText(str(new_value))
                self.current_values[tag] = float_val
                if self.parent_window and hasattr(self.parent_window, "current_values"):
                    self.parent_window.current_values[tag] = float_val
                self.on_user_input_setpoint(tag, float_val)
                if hasattr(input_widget, 'clearFocus'):
                    input_widget.clearFocus()
                self.setFocus()

    def open_time_numpad(self, input_widget: ClickableLineEdit,
                         tag_hours: str = None, tag_minutes: str = None,
                         title: str = "Config. Tiempo"):
        dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                if (
                    tag_hours == HEPARIN_AUTO_STOP_HOURS_TAG
                    and tag_minutes == HEPARIN_AUTO_STOP_MINUTES_TAG
                ):
                    hours, minutes = self._coerce_heparin_auto_stop_time(hours, minutes)

                input_widget.setText(f"{hours:02d}:{minutes:02d}")
                input_widget.clearFocus()  
                if tag_hours:
                    self.current_values[tag_hours] = float(hours)
                    if self.parent_window and hasattr(self.parent_window, "current_values"):
                        self.parent_window.current_values[tag_hours] = float(hours)
                if tag_minutes:
                    self.current_values[tag_minutes] = float(minutes)
                    if self.parent_window and hasattr(self.parent_window, "current_values"):
                        self.parent_window.current_values[tag_minutes] = float(minutes)
                if tag_hours and tag_minutes:
                    self.on_user_input_setpoint(tag_hours, float(hours))
                    self.on_user_input_setpoint(tag_minutes, float(minutes))

    def _coerce_heparin_auto_stop_time(self, hours: int, minutes: int) -> tuple[int, int]:
        requested_minutes = max(0, (int(hours) * 60) + int(minutes))

        therapy_hours = int(self.current_values.get("heparineTherapyHours", 0) or 0)
        therapy_minutes = int(self.current_values.get("heparineTherapyMinutes", 0) or 0)
        therapy_total_minutes = (therapy_hours * 60) + therapy_minutes
        max_allowed_minutes = max(0, therapy_total_minutes - 30)

        clamped_minutes = min(requested_minutes, max_allowed_minutes)
        if requested_minutes != clamped_minutes:
            max_h = max_allowed_minutes // 60
            max_m = max_allowed_minutes % 60
            msg = (
                f"Tiempo de heparina limitado a {max_h:02d}:{max_m:02d} "
                "(terapia menos 30 minutos)."
            )
            logger.warning(msg)
            if self.parent_window and hasattr(self.parent_window, "show_warning_message"):
                self.parent_window.show_warning_message(msg, 4000)

        return clamped_minutes // 60, clamped_minutes % 60

    def _toggle_heparin_pause_resume(self):
        """Alterna PAUSE/CONTINUAR para la bomba de heparina con comando latch."""
        self.heparin_pause_latched = not self.heparin_pause_latched
        self.on_user_boolean_command("heparineOperPauseResume", self.heparin_pause_latched)

        if hasattr(self, "btn_pause_hep") and self.btn_pause_hep is not None:
            self.btn_pause_hep.setText("CONT.." if self.heparin_pause_latched else "PAUSE")

        logger.info(
            f"Heparina pause/resume latch -> {self.heparin_pause_latched}"
        )

    
    def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        if widget.hasFocus():
            return
        value = self.current_values.get(tag, 0.0)
        widget.setText(f"{value:.{precision}f}")

    def update_values(self, new_values: dict):
        self.current_values = new_values
        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_bolus, "heparineBolusQuantity")
        auto_h = int(self.current_values.get(HEPARIN_AUTO_STOP_HOURS_TAG, 0) or 0)
        auto_m = int(self.current_values.get(HEPARIN_AUTO_STOP_MINUTES_TAG, 0) or 0)
        self.input_heparin_auto_stop.setText(f"{auto_h:02d}:{auto_m:02d}")

    def apply_bolus(self):
        self.on_user_boolean_command("heparinApplyBolusDose", True)
        

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)

    def update_state(self, phase: TreatmentPhase):
        enabled = phase not in (TreatmentPhase.CLEANING, TreatmentPhase.ERROR)
        self.input_heparin.setEnabled(enabled)
        self.input_bolus.setEnabled(enabled)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()


        
        # Fila 0
           # Abajo Izquierda (debajo de bolo)
        
        # Aquí puedes poner un placeholder para tus futuros controles
        # future_frame = QFrame()
        # # future_frame.setStyleSheet(...)
        # content_layout.addWidget(future_frame, 1, 1) # Abajo Derecha (debajo de params)

   
