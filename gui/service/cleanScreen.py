#gui/service/cleanScreen.py
#Control de los ciclos de desinfección (química y térmica) y enjuague.

# stacked index 4
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class cleanScr(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # ← guardar referencia al padre
        self.valores = parent.valores if parent else {}

        self.setFixedSize(1536, 726)  # ← tamaño exacto del stacked
        self.setStyleSheet("background: #0f172a;")

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        titulo = QLabel("LIMPIEZA")
        titulo.setStyleSheet("color: white; font-size: 48px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo, 0, 0, 1, 4)


