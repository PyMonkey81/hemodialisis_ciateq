# gui/components/time_numpad_modal.py

from PySide6.QtWidgets import (QDialog, QGridLayout, QPushButton, QLineEdit,
                               QVBoxLayout, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Importamos tu TimeLineEdit, asumiendo que está en el mismo módulo o accesible
# Si TimeLineEdit está en 'keypad.py' y este es 'time_numpad_modal.py', necesitas:
# from .keypad import TimeLineEdit
# O si ya lo importaste en mManualScr y este archivo está aparte:
# from gui.components.keypad import TimeLineEdit
# Para este ejemplo, lo incluiré aquí directamente como si fuera parte del mismo archivo conceptual.

class TimeLineEdit(QLineEdit):
    """
    Este campo captura números y los empuja de derecha a izquierda
    formateándolos siempre como HH:MM
    """
    def __init__(self, parent=None, initial_hh_mm="00:00"):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Consolas", 24, QFont.Bold))
        self.setStyleSheet("background-color: #1e293b; border: 2px solid #475569; padding: 5px; color: #22d3ee;")
        
        # Inicializar raw_value a partir de initial_hh_mm
        parts = initial_hh_mm.split(':')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            self.raw_value = f"{int(parts[0]):02d}{int(parts[1]):02d}"[-4:] # Asegura 4 dígitos
        else:
            self.raw_value = "0000"
            
        self.update_display()

    def add_digit(self, digit):
        if digit == '.': return # El tiempo no lleva decimales aquí
        
        # Máximo 4 dígitos para HHMM
        if len(self.raw_value) < 4:
            self.raw_value += digit
            self.update_display()
        else: # Si ya tiene 4 dígitos, desplaza el más antiguo
            self.raw_value = self.raw_value[1:] + digit
            self.update_display()

    def backspace(self):
        self.raw_value = self.raw_value[:-1]
        self.update_display()

    def update_display(self):
        # Rellenar con ceros a la izquierda para tener 4 dígitos
        padded = self.raw_value.zfill(4) 
        
        hh = padded[0:2]
        mm = padded[2:4]
        
        self.setText(f"{hh}:{mm}")

    def get_hours_minutes(self):
        # Devuelve las horas y minutos como enteros
        padded = self.raw_value.zfill(4)
        h = int(padded[0:2])
        m = int(padded[2:4])
        return h, m
    
    def get_total_minutes(self):
        h, m = self.get_hours_minutes()
        return h * 60 + m
    
    def set_time_from_minutes(self, total_minutes):
        h = total_minutes // 60
        m = total_minutes % 60
        self.raw_value = f"{h:02d}{m:02d}"[-4:]
        self.update_display()


class TimeNumpadDialog(QDialog):
    def __init__(self, parent=None, initial_hh_mm="00:00", title="Ingrese Tiempo (HH:MM)"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; border: 2px solid #334155; }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout(self)
        
        # --- VISOR DEL TIEMPO ---
        # Usamos tu TimeLineEdit aquí como el display del diálogo
        self.time_display = TimeLineEdit(initial_hh_mm=initial_hh_mm)
        self.time_display.setFixedSize(250, 60) # Tamaño fijo para el display
        layout.addWidget(self.time_display, alignment=Qt.AlignCenter)

        # --- GRID DE BOTONES ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1), ('⌫', 3, 2)
            # No hay botón de punto para el tiempo HH:MM
        ]

        font_btn = QFont("Arial", 20, QFont.Bold)

        for key, r, c in keys:
            btn = QPushButton(key)
            btn.setFixedSize(80, 70)
            btn.setFont(font_btn)
            
            if key == '⌫':
                btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 10px;")
                btn.clicked.connect(self.time_display.backspace) # Conectar al TimeLineEdit interno
            else:
                btn.setStyleSheet("""
                    QPushButton { background-color: #334155; color: white; border-radius: 10px; border: 2px solid #1e293b; }
                    QPushButton:pressed { background-color: #475569; border-color: #22d3ee; }
                """)
                btn.clicked.connect(lambda ch, k=key: self.time_display.add_digit(k)) # Conectar al TimeLineEdit interno
            
            grid_layout.addWidget(btn, r, c)
            
        # Añadir un espaciador en 3,0 para centrar el '0'
        grid_layout.addWidget(QLabel(""), 3, 0) # QLabel vacío como espaciador
        grid_layout.setColumnStretch(0,1)
        grid_layout.setColumnStretch(1,1)
        grid_layout.setColumnStretch(2,1)


        layout.addLayout(grid_layout)

        # --- BOTONES DE ACCIÓN (ACEPTAR / CANCELAR) ---
        action_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(60)
        btn_cancel.setFont(QFont("Arial", 16, QFont.Bold))
        btn_cancel.setStyleSheet("background-color: #64748b; color: white; border-radius: 10px;")
        btn_cancel.clicked.connect(self.reject)

        btn_accept = QPushButton("ACEPTAR")
        btn_accept.setFixedHeight(60)
        btn_accept.setFont(QFont("Arial", 16, QFont.Bold))
        btn_accept.setStyleSheet("background-color: #22c55e; color: white; border-radius: 10px;")
        btn_accept.clicked.connect(self.accept)

        action_layout.addWidget(btn_cancel)
        action_layout.addWidget(btn_accept)
        layout.addLayout(action_layout)

    def get_hours_minutes(self):
        # Devuelve el tiempo en formato (horas, minutos) como enteros
        return self.time_display.get_hours_minutes()

    def get_total_minutes(self):
        return self.time_display.get_total_minutes()
