#gui/service/optionScreen.py
#pantalla para configuracion, entrada a pantallas de test 1 y test 2, modo manual 
#pantalla de ajustes.


# stacked index 3
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor



 #pantalla modo manual



class optionScr(QWidget):
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

        titulo = QLabel("AJUSTES Y CONFIGURACIÓN")
        titulo.setStyleSheet("color: #ffffff; font-size: 48px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo, 0, 0, 1, 4)

        # Area de botones
        botones_area = QFrame()
        botones_area.setStyleSheet("background: #ffffff; border-radius: 20px; border: 4px solid #1e293b;")
        bl = QGridLayout(botones_area)
        bl.setSpacing(30)
        bl.setContentsMargins(50, 50, 50, 50)

        opciones = [
            ("Panel de pruebas", "#3134df", self.parent.mostrar_panel_pruebas),
            ("Modo manual", "#3134df", self.parent.mostrar_modo_manual),
            ("Calibración", "#3134df", self.parent.mostrar_calibracion),
            ("Configuración red", "#3134df", self.parent.mostrar_config_red),
            ("Monitor de variables", "#3134df",self.parent.mostrar_monitor_variables)
        ]

        for i, (texto, color, func) in enumerate(opciones):
            btn = QPushButton(texto)
            btn.setFixedSize(400, 150)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                              font-size: 28px; border-radius: 20px; border: 4px solid #1e293b; }}
                QPushButton:pressed {{ background: #1e40af; }}
            """)
            btn.clicked.connect(func)
            row = i // 2
            col = i % 2
            bl.addWidget(btn, row, col)

        layout.addWidget(botones_area, 1, 0, 4, 4)
    
   
