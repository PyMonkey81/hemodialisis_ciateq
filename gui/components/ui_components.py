# gui/components/ui_components.py
# Reusable UI helper components for Hemodialysis HMI
# - Clickable read-only inputs for virtual keypad
# - Labeled parameter displays (editable + units)
# - Labeled time (HH:MM) inputs with numpad trigger

from PySide6.QtWidgets import (
    QLineEdit, QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox
from gui.components.ToggleSwitch import ToggleSwitch

class ToggleBox(QFrame):
    def __init__(self, label, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #fcfcfc;
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>{label}</b>")
        lbl_info.setStyleSheet("color: #000000; font-size: 18px; border:none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=60, height=30)

        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(self.toggle)



class DoubleToggleBox(QFrame):
    def __init__(self, label1_text, label2_text, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8; /* Un fondo ligeramente diferente para destacar */
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(120) # Ajusta la altura si es necesario para acomodar dos filas

        # Layout principal de la DoubleToggleBox (vertical)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5) # Menos espacio vertical entre las filas

        # --- Primera Fila: Label 1 y Toggle 1 ---
        row1_layout = QHBoxLayout()
        lbl1 = QLabel(f"<b>{label1_text}</b>")
        lbl1.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl1.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle1 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row1_layout.addWidget(lbl1)
        row1_layout.addStretch()
        row1_layout.addWidget(self.toggle1)
        main_layout.addLayout(row1_layout)

        # --- Segunda Fila: Label 2 y Toggle 2 ---
        row2_layout = QHBoxLayout()
        lbl2 = QLabel(f"<b>{label2_text}</b>")
        lbl2.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl2.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle2 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row2_layout.addWidget(lbl2)
        row2_layout.addStretch()
        row2_layout.addWidget(self.toggle2)
        main_layout.addLayout(row2_layout)





class ClickableLineEdit(QLineEdit):
    """
    Read-only QLineEdit that emits a 'clicked' signal on press.
    Designed for touch interfaces to trigger virtual keypads.
    """

    clicked = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setReadOnly(True)  # Force keypad input (medical safety)
        self.setCursor(Qt.PointingHandCursor)  # Visual cue (touch-friendly)

    def mousePressEvent(self, event):
        """Emit clicked signal on left mouse/touch press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class LabeledParameterWidget(QWidget):
    """
    Labeled parameter display/input widget.
    Combines description label, value (editable or read-only), and units.
    Emits request_numpad signal when clicked (for virtual keypad).
    """

    # Signal: tag (str), widget_instance (self), numpad_title (str)
    request_numpad = Signal(str, object, str)

    def __init__(self,
                 label_text: str, # label_text: str,
                 tag: str = None, #               tag: str = None,
                 value: str = "",
                 units: str = "",
                 numpad_title: str = "",
                 is_editable: bool = True,
                 parent=None):
        super().__init__(parent)

        
        indicator_style = "color: #22d3ee; font-size: 26px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        input_style = """
            background: #FFFFE5; color: #000000; font-size: 26px; font-weight: bold;
            border: 2px solid #000000; border-radius: 5px; padding: 4px;
        """

        self.setFixedHeight(90)  # Consistent touch target size
        self._tag = tag
        self._numpad_title = numpad_title or label_text

        # Container frame
        self.frame = QFrame(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)

        # Inner layout
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(2)

        # Header label (description + units)
        header_text = f"{label_text} ({units})" if units else label_text
        self.header_label = QLabel(header_text)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("""
            border: none;
            color: #333333;
            font-weight: bold;
            font-size: 18px;
        """)

        # Value widget (editable or read-only)
        if is_editable:
            self.value_widget = ClickableLineEdit(value)
            self.value_widget.setStyleSheet(input_style)
            self.value_widget.setMinimumWidth(80)
            self.value_widget.setFixedHeight(40)
            self.value_widget.setAlignment(Qt.AlignCenter)
            self.value_widget.clicked.connect(self._emit_numpad_request)
        else:
            self.value_widget = QLabel(value)
            self.value_widget.setStyleSheet(indicator_style)      
            self.value_widget.setMinimumWidth(80)
            self.value_widget.setFixedHeight(40)
            self.value_widget.setAlignment(Qt.AlignCenter)

        frame_layout.addWidget(self.header_label)
        frame_layout.addWidget(self.value_widget)

    def _emit_numpad_request(self):
        """Internal handler to emit numpad request signal."""
        self.request_numpad.emit(self._tag, self, self._numpad_title)

    def set_value(self, value):
        """Update displayed value with safe formatting."""
        try:
            if isinstance(value, (int, float)):
                # Consistent medical formatting: 1 decimal if >=10, 2 if <10
                display_text = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
            else:
                display_text = str(value)

            if isinstance(self.value_widget, QLineEdit):
                self.value_widget.setText(display_text)
            elif isinstance(self.value_widget, QLabel):
                self.value_widget.setText(display_text)

        except Exception as e:
            print(f"[ERROR] Failed to set value in LabeledParameterWidget: {e}")
            fallback = "ERR"
            if isinstance(self.value_widget, QLineEdit):
                self.value_widget.setText(fallback)
            elif isinstance(self.value_widget, QLabel):
                self.value_widget.setText(fallback)

    def get_value(self) -> str:
        """Return current text value."""
        if isinstance(self.value_widget, QLineEdit):
            return self.value_widget.text()
        elif isinstance(self.value_widget, QLabel):
            return self.value_widget.text()
        return ""


class LabeledTimeInput(QWidget):
    """
    Labeled time (HH:MM) input widget for Hemodialysis HMI.
    Combines description label and clickable time display.
    Emits request_time_numpad when clicked.
    """

    # Signal: widget_instance (self), tag_hours, tag_minutes, local_timer_id, title
    request_time_numpad = Signal(object, str, str, str, str)

    def __init__(self,
                 label_text: str,
                 initial_hh_mm: str = "00:00",
                 tag_hours: str = None,
                 tag_minutes: str = None,
                 local_timer_id: str = None,
                 numpad_title: str = "",
                 is_editable: bool = True,
                 parent=None):
        super().__init__(parent)

        self.setFixedHeight(90)
        self._tag_hours = tag_hours
        self._tag_minutes = tag_minutes
        self._local_timer_id = local_timer_id
        self._numpad_title = numpad_title or label_text

        indicator_style = "color: #22d3ee; font-size: 26px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        input_style = """
            background: #FFFFE5; color: #000000; font-size: 26px; font-weight: bold;
            border: 2px solid #000000; border-radius: 5px; padding: 4px;
        """

        # Container frame
        self.frame = QFrame(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)

        # Inner layout
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(2)

        # Header label
        self.header_label = QLabel(label_text)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("""
            border: none;
            color: #333333;
            font-weight: bold;
            font-size: 18px;
        """)

        # Clickable time display
        if is_editable:
            self.time_display = ClickableLineEdit(initial_hh_mm)
            self.time_display.setStyleSheet(input_style)
            self.time_display.setReadOnly(True)
            self.time_display.setMinimumWidth(80)
            self.time_display.setFixedHeight(40)
            self.time_display.setAlignment(Qt.AlignCenter)
            self.time_display.clicked.connect(self._emit_time_numpad_request)
        else:
            self.time_display = QLabel(initial_hh_mm)
            self.time_display.setStyleSheet(indicator_style)
            self.time_display.setMinimumWidth(80)
            self.time_display.setFixedHeight(40)
            self.time_display.setAlignment(Qt.AlignCenter)
            

        frame_layout.addWidget(self.header_label)
        frame_layout.addWidget(self.time_display)

    def _emit_time_numpad_request(self):
        """Internal handler to emit time numpad request signal."""
        self.request_time_numpad.emit(
            self,
            self._tag_hours,
            self._tag_minutes,
            self._local_timer_id,
            self._numpad_title
        )

    def set_time_value(self, hours: int, minutes: int):
        """Update displayed time in HH:MM format."""
        self.time_display.setText(f"{hours:02d}:{minutes:02d}")

    def get_time_value(self) -> str:
        """Return current displayed time as HH:MM string."""
        return self.time_display.text()

    def get_hours_minutes(self) -> tuple[int, int]:
        """Parse displayed time into (hours, minutes)."""
        try:
            h_str, m_str = self.time_display.text().split(':')
            return int(h_str), int(m_str)
        except ValueError:
            print(f"[ERROR] Invalid time format in LabeledTimeInput: {self.time_display.text()}")
#             return 0, 0



def show_dark_message(parent, title: str, text: str, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    """
    Muestra un QMessageBox con estilo oscuro consistente.
    - Usa el estilo manual para que funcione en Windows.
    - Puedes personalizar icono y botones.
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(QMessageBox.Ok if buttons & QMessageBox.Ok else QMessageBox.Yes)

    # Estilo (puedes moverlo al global si prefieres, pero aquí lo dejamos por si acaso)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #2b2b2b;
        }
        QLabel {
            color: #ffffff;
            background-color: #2b2b2b;
            padding: 10px;
            min-width: 350px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            min-width: 100px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #45a049; }
        QPushButton:pressed { background-color: #3e8e41; }
    """)

    return msg.exec()