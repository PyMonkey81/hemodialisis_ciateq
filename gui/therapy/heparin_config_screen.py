# gui/therapy/heparin_config_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDateTime, QEvent

from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit
from core.state_manager import TreatmentPhase

import logging
logger = logging.getLogger(__name__)


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
        self.setup_ui()

    def setup_ui(self):
        self.style_enabled = """
            QPushButton { background: #39ec21; color: #ffffff; font-weight: bold; font-size: 20px; border-radius: 15px; border: 3px solid #1e293b; }
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

        content_layout = QHBoxLayout()
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

        lbl_bolus = QLabel("Bolo (ml):")
        lbl_bolus.setStyleSheet(label_style)
        lbl_bolus.setAlignment(Qt.AlignRight)
        self.input_bolus = ClickableLineEdit("0.0")
        self.input_bolus.setFixedSize(120, 50)
        self.input_bolus.setAlignment(Qt.AlignCenter)
        self.input_bolus.setStyleSheet(input_style)
        self.input_bolus.setReadOnly(True)
        self.input_bolus.clicked.connect(
            lambda: self.open_numpad("heparineBolusQuantity", self.input_bolus, "Bolo (ml)")
        )
        hep_frame_layout.addWidget(lbl_bolus)
        hep_frame_layout.addWidget(self.input_bolus)

        btn_heparin_home = PushbuttonEvent("HOME", self)
        btn_heparin_home.setFixedSize(120, 80)
        btn_heparin_home.setStyleSheet(button_style)
        btn_heparin_home.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", True))
        btn_heparin_home.released.connect(lambda: self.on_user_boolean_command("heparinePumpHomePosition", False))
        hep_frame_layout.addWidget(btn_heparin_home)

        btn_rev_hep = PushbuttonEvent("REV", self)
        btn_rev_hep.setFixedSize(120, 80)
        btn_rev_hep.setStyleSheet(button_style)
        btn_rev_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", True))
        btn_rev_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpREVButton", False))
        hep_frame_layout.addWidget(btn_rev_hep)

        btn_fwd_hep = PushbuttonEvent("FWD", self)
        btn_fwd_hep.setFixedSize(120, 80)
        btn_fwd_hep.setStyleSheet(button_style)
        btn_fwd_hep.pressed.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", True))
        btn_fwd_hep.released.connect(lambda: self.on_user_boolean_command("heparinePumpFWDButton", False))
        hep_frame_layout.addWidget(btn_fwd_hep)

        btn_apply_bolus = QPushButton("APLICAR BOLO")
        btn_apply_bolus.setFixedHeight(80)
        btn_apply_bolus.setStyleSheet(self.style_enabled)
        btn_apply_bolus.clicked.connect(self.apply_bolus)
        hep_frame_layout.addWidget(btn_apply_bolus)


        content_layout.addWidget(hep_frame)

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

        content_layout.addWidget(params_frame)
        main_layout.addStretch(1)

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

    def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        if widget.hasFocus():
            return
        value = self.current_values.get(tag, 0.0)
        widget.setText(f"{value:.{precision}f}")

    def update_values(self, new_values: dict):
        self.current_values = new_values
        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_bolus, "heparineBolusQuantity")

    def apply_bolus(self):
        self.on_user_boolean_command("heparinApplyBolusDose", True)
        self.on_user_boolean_command("heparinApplyBolusDose", False)

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
