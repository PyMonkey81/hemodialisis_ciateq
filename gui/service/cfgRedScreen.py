#gui/service/cfgRedScreen.py

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class cfgRedScr(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.valores = parent.valores if parent else {}

        self.setFixedSize(1536,726)
        self.setStyleSheet("background: #0f172a;")

        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        titulo = QLabel("Configuración de red")
        titulo.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo, 0, 0, 1, 4)