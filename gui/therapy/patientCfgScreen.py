#gui/therapy/ufMenuScreen.py


from PySide6.QtWidgets import QWidget, QVBoxLayout,QLabel
from PySide6.QtCore import Qt

class patienCfgScr(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # ← guardar referencia al padre
        self.valores = parent.valores if parent else {}

        self.setFixedSize(1536, 726)  # ← tamaño exacto del stacked
        self.setStyleSheet("background: #0f172a;")  


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
