#gui/therapy/treatment_mode_screen.py


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QGridLayout, QFrame, QLineEdit, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import time


class TreatmentModeScreen(QWidget):
    """
    Configuration treatment: Selection mode (HD, HDF, UF, Cleanning)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.values = parent.current_values if parent else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("backgrond: #0f172a")

        self.pending_mode_change_deadline = None
        self.command_mode_value = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #1a2a4a, stop:1 #0f172a);
            color: #f8fafc;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Title
        title = QLabel("Tipo de Terapía")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)



