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

        botones_area = QFrame()
        botones_area.setStyleSheet("background: white; border-radius: 20px; border: 4px solid #1e293b;")
        bl = QGridLayout(botones_area)
        bl.setSpacing(30)
        bl.setContentsMargins(50, 50, 50, 50)

        opciones = [
            ("Panel de pruebas", "#3134df", lambda: print("TEST 1")),
            ("Modo manual", "#3134df", lambda: print("MODO MANUAL")),
            ("Calibración", "#3134df", lambda: print("CALIBRACIÓN")),
            ("Configuración red", "#3134df", lambda: print("RED")),
        ]

        for i, (texto, color, func) in enumerate(opciones):
            btn = QPushButton(texto)
            btn.setFixedSize(400, 150)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: white; font-weight: bold;
                              font-size: 28px; border-radius: 20px; border: 4px solid #1e293b; }}
                QPushButton:pressed {{ background: #1e40af; }}
            """)
            btn.clicked.connect(func)
            row = i // 2
            col = i % 2
            bl.addWidget(btn, row, col)

        layout.addWidget(botones_area, 1, 0, 3, 4)

    # def pantalla_test_Screen1(self):
    #     return testSrc1()

    # def mostrar_pantalla_testScr1(self):
    #     self.stacked.setCurrentIndex(6)
    #     self.actualizar_label_pantalla("Panel de pruebas", "#ffffff")

    # def actualizar_valores(self, valores_dict):
    #     self.valores = valores_dict
