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
                 value: str = "0.0",
                 units: str = "",
                 numpad_title: str = "",
                 is_editable: bool = True,
                 parent=None):
        super().__init__(parent)

        
#               value="0.0",    
#               units: str = "",
#               numpad_title: str = "",
#               is_editable: bool = True,
#               parent=None):

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
            self.value_widget.setMinimumWidth(80)
            self.value_widget.setFixedHeight(40)
            self.value_widget.setAlignment(Qt.AlignCenter)
            self.value_widget.clicked.connect(self._emit_numpad_request)
        else:
            self.value_widget = QLabel(value)
            self.value_widget.setStyleSheet("""
                color: #22d3ee;
                font-size: 20px;
                font-weight: bold;
                border: 2px solid #000000;
                border-radius: 1px;
                padding: 2px;
            """)
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
                 parent=None):
        super().__init__(parent)

        self.setFixedHeight(90)
        self._tag_hours = tag_hours
        self._tag_minutes = tag_minutes
        self._local_timer_id = local_timer_id
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
        self.time_display = ClickableLineEdit(initial_hh_mm)
        self.time_display.setReadOnly(True)
        self.time_display.setMinimumWidth(80)
        self.time_display.setFixedHeight(40)
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.clicked.connect(self._emit_time_numpad_request)

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

# # # # gui/components/ui_components.py (o un nuevo archivo LabeledTimeInput.py)
# # # from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
# # # from PySide6.QtCore import Qt, Signal
# # # # Asegúrate de que ClickableLineEdit esté importado correctamente
# # # from gui.components.ui_components import ClickableLineEdit # Asumiendo que reside aquí

# # class LabeledTimeInput(QWidget):
# #     """
# #     Custom widget for Hemodialysis HMI time inputs (HH:MM).
# #     Combines a description label and a clickable time display.
# #     """
    
# #     # Signal emitted when the user wants to edit the time value.
# #     # We pass 'self' (the instance of LabeledTimeInput) so the receiver
# #     # knows which widget to update after the numpad closes.
# #     request_time_numpad = Signal(object, str, str, str, str) # time_input_widget, tag_hours, tag_minutes, local_timer_id, title

# #     def __init__(self, label_text: str, initial_hh_mm: str = "00:00", 
# #                  tag_hours: str = None, tag_minutes: str = None,
# #                  local_timer_id: str = None, numpad_title: str = ""):
# #         super().__init__()
        
# #         self.setFixedHeight(90) # Consistent height for touch targets
        
# #         # Store parameters internally for emitting the signal later
# #         self._tag_hours = tag_hours
# #         self._tag_minutes = tag_minutes
# #         self._local_timer_id = local_timer_id
# #         self._numpad_title = numpad_title if numpad_title else label_text # Use label_text as fallback

# #         # Main layout container
# #         self.control_frame = QFrame()
# #         self.main_layout = QVBoxLayout(self)
# #         self.main_layout.setContentsMargins(0, 0, 0, 0)
# #         self.main_layout.addWidget(self.control_frame)

# #         # Inner layout
# #         self.frame_layout = QVBoxLayout(self.control_frame)
# #         self.frame_layout.setContentsMargins(5, 5, 5, 5)
# #         self.frame_layout.setSpacing(2) # Tight spacing between label and value

# #         # 1. Create the Header Label
# #         self.lbl_header = QLabel(label_text)
# #         self.lbl_header.setAlignment(Qt.AlignCenter)
# #         self.lbl_header.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 18px;")
        
# #         # 2. Create the Clickable Time Widget
# #         self.time_display_widget = ClickableLineEdit(initial_hh_mm)
# #         self.time_display_widget.setReadOnly(True) # Always read-only, value set via numpad
# #         self.time_display_widget.setMinimumWidth(80) 
# #         self.time_display_widget.setFixedHeight(40)
# #         self.time_display_widget.setAlignment(Qt.AlignCenter)
# #         self.time_display_widget.clicked.connect(self._handle_click_internal) # Connect internal click to emit signal

# #         # Add widgets to layout
# #         self.frame_layout.addWidget(self.lbl_header)
# #         self.frame_layout.addWidget(self.time_display_widget)

# #     def _handle_click_internal(self):
# #         """Internal handler to emit the signal for the main controller."""
# #         self.request_time_numpad.emit(
# #             self, # Pass reference to THIS widget instance
# #             self._tag_hours,
# #             self._tag_minutes,
# #             self._local_timer_id,
# #             self._numpad_title
# #         )
    
# #     def set_time_value(self, hours: int, minutes: int):
# #         """
# #         Updates the displayed time in HH:MM format.
# #         """
# #         self.time_display_widget.setText(f"{hours:02d}:{minutes:02d}")

# #     def get_time_value(self) -> str:
# #         """
# #         Returns the current displayed time as a "HH:MM" string.
# #         """
# #         return self.time_display_widget.text()

# #     def get_hours_minutes(self) -> tuple[int, int]:
# #         """
# #         Parses the displayed time into (hours, minutes).
# #         """
# #         try:
# #             h_str, m_str = self.time_display_widget.text().split(':')
# #             return int(h_str), int(m_str)
# #         except ValueError:
# #             return 0, 0 # Return default if format is invalid



# # # gui/components/ui_components.py

# # from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QLineEdit
# # from PySide6.QtCore import Qt, Signal
# # from PySide6.QtGui import QPainter, QColor # Para el mock de LED

# # --- ClickableLineEdit ---
# class ClickableLineEdit(QLineEdit):
#     """
#     A QLineEdit that emits a 'clicked' signal when pressed.
#     Designed for touch interfaces where a virtual keypad is used for input.
#     """
#     clicked = Signal() 
    
#     def __init__(self, text="", parent=None):
#         super().__init__(text, parent)
#         # MEDICAL STD: Ensure ReadOnly to force interaction through virtual keypad.
#         # This prevents direct typing if a physical keyboard is connected.
#         self.setReadOnly(True) 
#         # UX: Change cursor to indicate it's clickable, not selectable text.
#         # On a touchscreen without a mouse, this is less visible but good practice.
#         self.setCursor(Qt.PointingHandCursor) 
    
#     def mousePressEvent(self, event):
#         """
#         Intercepts mouse/touch press to emit the clicked signal.
#         """
#         if event.button() == Qt.LeftButton:
#             self.clicked.emit()
#         super().mousePressEvent(event)

# # --- LabeledParameterWidget ---
# class LabeledParameterWidget(QWidget):
#     """
#     Custom widget for Hemodialysis HMI parameters.
#     Combines a description label, a value display/input, and unit tracking.
#     """
    
#     # Signal emitted when the user wants to edit the value.
#     # Args: tag_variable (str), widget_instance (object), numpad_title (str)
#     request_numpad = Signal(str, object, str) 

#     def __init__(self, 
#               label_text: str,
#               tag: str = None,
#               value="0.0",    
#               units: str = "",
#               numpad_title: str = "",
#               is_editable: bool = True,
#               parent=None):
#         super().__init__(parent)
        
#         self.setFixedHeight(90) # Consistent height for touch targets
#         self._tag = tag # Store tag internally
        
#         self.control_frame = QFrame(self)
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(0, 0, 0, 0)
#         self.main_layout.addWidget(self.control_frame)

#         self.frame_layout = QVBoxLayout(self.control_frame)
#         self.frame_layout.setContentsMargins(5, 5, 5, 5)
#         self.frame_layout.setSpacing(2) # Tight spacing between label and value

#         header_text = f"{label_text} ({units})" if units else label_text
#         self.lbl_header = QLabel(header_text, self.control_frame)
#         self.lbl_header.setAlignment(Qt.AlignCenter)
#         self.lbl_header.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 18px;")
        
#         if is_editable:
#             self.value_widget = ClickableLineEdit(str(value), self.control_frame)
#             # Connecting the internal ClickableLineEdit's signal to an internal handler
#             # which then emits the LabeledParameterWidget's signal.
#             self.value_widget.clicked.connect(lambda: self._handle_click(self._tag, numpad_title))
#         else:
#             self.value_widget = QLabel(str(value), self.control_frame)
#             # Styling for non-editable indicators, matching the style_lbl_ from mManualScr
#             self.value_widget.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;border: 2px solid #000000; border-radius: 5px; padding: 2px;")

#         self.value_widget.setMinimumWidth(80) 
#         self.value_widget.setFixedHeight(40)
#         self.value_widget.setAlignment(Qt.AlignCenter)

#         self.frame_layout.addWidget(self.lbl_header)
#         self.frame_layout.addWidget(self.value_widget)

#     def _handle_click(self, tag, title):
#         """Internal handler to emit the LabeledParameterWidget's signal."""
#         # Emits 'self' (this LabeledParameterWidget instance) as the widget_instance.
#         self.request_numpad.emit(tag, self, title) 
    
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
            
#             # Update the internal QLineEdit/QLabel based on its actual type
#             if isinstance(self.value_widget, QLineEdit):
#                 self.value_widget.setText(display_text)
#             elif isinstance(self.value_widget, QLabel):
#                 self.value_widget.setText(display_text)
            
#         except Exception as e:
#             print(f"[ERROR] Failed to set value in LabeledParameterWidget: {e}")
#             # Fallback to "ERR" on display in case of formatting error
#             if isinstance(self.value_widget, QLineEdit):
#                 self.value_widget.setText("ERR")
#             elif isinstance(self.value_widget, QLabel):
#                 self.value_widget.setText("ERR")


#     def get_value(self):
#         """Returns the current text value from the internal QLineEdit or QLabel."""
#         if isinstance(self.value_widget, QLineEdit):
#             return self.value_widget.text()
#         elif isinstance(self.value_widget, QLabel):
#             return self.value_widget.text()
#         return "" # Fallback for unexpected internal widget type


# # --- LabeledTimeInput ---
# class LabeledTimeInput(QWidget):
#     """
#     Custom widget for Hemodialysis HMI time inputs (HH:MM).
#     Combines a description label and a clickable time display.
#     """
#     # Signal emitted when the user wants to edit the time value.
#     # Args: widget_instance (object), tag_hours (str), tag_minutes (str), 
#     #       local_timer_id (str), numpad_title (str)
#     request_time_numpad = Signal(object, str, str, str, str) 

#     def __init__(self, label_text: str, initial_hh_mm: str = "00:00", 
#                  tag_hours: str = None, tag_minutes: str = None,
#                  local_timer_id: str = None, numpad_title: str = "", parent=None):
#         super().__init__(parent)
        
#         self.setFixedHeight(90) # Consistent height for touch targets
        
#         self._tag_hours = tag_hours
#         self._tag_minutes = tag_minutes
#         self._local_timer_id = local_timer_id
#         self._numpad_title = numpad_title if numpad_title else label_text

#         self.control_frame = QFrame(self)
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(0, 0, 0, 0)
#         self.main_layout.addWidget(self.control_frame)

#         self.frame_layout = QVBoxLayout(self.control_frame)
#         self.frame_layout.setContentsMargins(5, 5, 5, 5)
#         self.frame_layout.setSpacing(2)

#         self.lbl_header = QLabel(label_text, self.control_frame)
#         self.lbl_header.setAlignment(Qt.AlignCenter)
#         self.lbl_header.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 18px;")
        
#         self.time_display_widget = ClickableLineEdit(initial_hh_mm, self.control_frame)
#         self.time_display_widget.setReadOnly(True) # Always read-only, value set via numpad
#         self.time_display_widget.setMinimumWidth(80) 
#         self.time_display_widget.setFixedHeight(40)
#         self.time_display_widget.setAlignment(Qt.AlignCenter)
#         self.time_display_widget.clicked.connect(self._handle_click_internal)

#         self.frame_layout.addWidget(self.lbl_header)
#         self.frame_layout.addWidget(self.time_display_widget)

#     def _handle_click_internal(self):
#         """Internal handler to emit the LabeledTimeInput's signal."""
#         # Emits 'self' (this LabeledTimeInput instance) as the widget_instance.
#         self.request_time_numpad.emit(
#             self, 
#             self._tag_hours,
#             self._tag_minutes,
#             self._local_timer_id,
#             self._numpad_title
#         )
    
#     def set_time_value(self, hours: int, minutes: int):
#         """
#         Updates the displayed time in HH:MM format.
#         """
#         self.time_display_widget.setText(f"{hours:02d}:{minutes:02d}")

#     def get_time_value(self) -> str:
#         """
#         Returns the current displayed time as a "HH:MM" string.
#         """
#         return self.time_display_widget.text()

#     def get_hours_minutes(self) -> tuple[int, int]:
#         """
#         Parses the displayed time into (hours, minutes).
#         """
#         try:
#             h_str, m_str = self.time_display_widget.text().split(':')
#             return int(h_str), int(m_str)
#         except ValueError:
#             print(f"[ERROR] Invalid time format in LabeledTimeInput: {self.time_display_widget.text()}. Returning 0,0.")
#             return 0, 0 # Return default if format is invalid
