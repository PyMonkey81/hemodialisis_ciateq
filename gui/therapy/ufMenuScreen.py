#gui/therapy/ufMenuScreen.py


from PySide6.QtWidgets import QWidget, QVBoxLayout,QLabel
from PySide6.QtCore import Qt

class ufMenuScr(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Fondo 
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #e0e7ff, stop:1 #c7d2fe);
            border-radius: 15px;
        """)

        layout = QVBoxLayout(self)
        layout.addStretch(2)
