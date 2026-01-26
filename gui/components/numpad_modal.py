# gui/components/numpad_modal.py
from PySide6.QtWidgets import (QDialog, QGridLayout, QPushButton, QLineEdit, 
                               QVBoxLayout, QHBoxLayout, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class NumpadDialog(QDialog):
    def __init__(self, parent=None, initial_value="", title="Ingrese Valor"):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Quitamos el marco de ventana nativo para que se vea full touch (opcional)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; border: 2px solid #334155; }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout(self)
        
        # --- VISOR DEL VALOR ---
        self.display = QLineEdit(str(initial_value))
        self.display.setFixedHeight(60)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True) # Para que solo se use el teclado en pantalla
        self.display.setFont(QFont("Arial", 28, QFont.Bold))
        self.display.setStyleSheet("""
            QLineEdit { 
                background-color: #1e293b; 
                color: #22d3ee; 
                border: 2px solid #475569; 
                border-radius: 8px; 
                padding-right: 10px;
            }
        """)
        layout.addWidget(self.display)

        # --- GRID DE BOTONES ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('⌫', 3, 2)
        ]

        font_btn = QFont("Arial", 20, QFont.Bold)

        for key, r, c in keys:
            btn = QPushButton(key)
            btn.setFixedSize(80, 70)
            btn.setFont(font_btn)
            
            if key == '⌫':
                btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 10px;")
                btn.clicked.connect(self.backspace)
            else:
                btn.setStyleSheet("""
                    QPushButton { background-color: #334155; color: white; border-radius: 10px; border: 2px solid #1e293b; }
                    QPushButton:pressed { background-color: #475569; border-color: #22d3ee; }
                """)
                btn.clicked.connect(lambda ch, k=key: self.add_digit(k))
            
            grid_layout.addWidget(btn, r, c)

        layout.addLayout(grid_layout)

        # --- BOTONES DE ACCIÓN (ACEPTAR / CANCELAR) ---
        action_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(60)
        btn_cancel.setFont(QFont("Arial", 16, QFont.Bold))
        btn_cancel.setStyleSheet("background-color: #64748b; color: white; border-radius: 10px;")
        btn_cancel.clicked.connect(self.reject) # Cierra devolviendo 0 (False)

        btn_accept = QPushButton("ACEPTAR")
        btn_accept.setFixedHeight(60)
        btn_accept.setFont(QFont("Arial", 16, QFont.Bold))
        btn_accept.setStyleSheet("background-color: #22c55e; color: white; border-radius: 10px;")
        btn_accept.clicked.connect(self.accept) # Cierra devolviendo 1 (True)

        action_layout.addWidget(btn_cancel)
        action_layout.addWidget(btn_accept)
        layout.addLayout(action_layout)

    def add_digit(self, digit):
        text = self.display.text()
        
        # Evitar múltiples puntos
        if digit == '.' and '.' in text:
            return
        
        # Si es 0 inicial y presionan un numero, reemplazar (excepto si es punto)
        if text == "0" and digit != ".":
            text = ""
            
        self.display.setText(text + digit)

    def backspace(self):
        text = self.display.text()
        self.display.setText(text[:-1])

    def get_value(self):
        val = self.display.text()
        if val == "" or val == ".":
            return 0.0
        return float(val)
