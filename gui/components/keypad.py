#gui/components/keypad.py

import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QGridLayout, QPushButton, QLineEdit, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

# =============================================================================
# 1. WIDGET REUTILIZABLE: TECLADO NUMÉRICO (NUMPAD)
# =============================================================================
class NumpadWidget(QWidget):
    # Señales: enviar tecla presionada o comando
    keyPressed = Signal(str)      # Envía '1', '2', '.', etc.
    backspacePressed = Signal()   # Envía señal de borrar
    enterPressed = Signal()       # Envía señal de confirmar

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10) # Espacio entre botones

        # Definición de teclas
        # Tupla: (Texto, Fila, Columna)
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('⌫', 3, 2) # ⌫ es Backspace
        ]

        font = QFont("Arial", 18, QFont.Bold)

        for key, r, c in keys:
            btn = QPushButton(key)
            btn.setFixedSize(80, 80) # Botones grandes para dedos
            btn.setFont(font)
            
            # Estilo "Médico"
            if key == '⌫':
                btn.setStyleSheet("background-color: #d9534f; color: white; border-radius: 10px;")
                btn.clicked.connect(self.backspacePressed.emit)
            else:
                btn.setStyleSheet("""
                    QPushButton { background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 10px; }
                    QPushButton:pressed { background-color: #d0d0d0; }
                """)
                # Usamos lambda para pasar el valor de la tecla
                btn.clicked.connect(lambda checked, k=key: self.keyPressed.emit(k))
            
            self.layout.addWidget(btn, r, c)

# =============================================================================
# 2. COMPONENTE PERSONALIZADO: INPUT DE TIEMPO (HH:MM)
# =============================================================================
class TimeLineEdit(QLineEdit):
    """
    Este campo captura números y los empuja de derecha a izquierda
    formateándolos siempre como HH:MM
    Ej: Escribir '1' -> 00:00
        Escribir '2' -> 00:00
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True) # No permitir teclado físico directo (opcional)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Consolas", 24, QFont.Bold)) # Fuente monoespaciada para que no bailen los números
        self.setStyleSheet("background-color: #e8f4f8; border: 2px solid #007ACC; padding: 5px; color: #333;")
        
        self.raw_value = "" # Aquí guardamos "1230" sin los dos puntos
        self.update_display()

    def add_digit(self, digit):
        if digit == '.': return # El tiempo no suele llevar decimales en la UI básica
        
        # Máximo 4 dígitos (HHMMSS) -> 99:59
        if len(self.raw_value) < 4:
            self.raw_value += digit
            self.update_display()

    def backspace(self):
        self.raw_value = self.raw_value[:-1]
        self.update_display()

    def update_display(self):
        # Rellenar con ceros a la izquierda hasta tener 6 dígitos
        padded = self.raw_value.zfill(4) 
        
        # Cortar en pedazos
        hh = padded[0:2]
        mm = padded[2:4]
        # ss = padded[4:6]
        
        # self.setText(f"{hh}:{mm}:{ss}")
        self.setText(f"{hh}:{mm}")

    def get_seconds(self):
        # Utilidad para obtener el total en segundos para la máquina
        padded = self.raw_value.zfill(4)
        h = int(padded[0:2])
        m = int(padded[2:4])
        # s = int(padded[4:6])
        return h * 3600 + m * 60 
# =============================================================================
# 3. PANTALLA DE CONFIGURACIÓN (Ejemplo de Integración)
# =============================================================================
class TherapyConfigScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Terapia")
        self.resize(800, 500)
        
        # Layout Principal: Izquierda (Campos) - Derecha (Teclado)
        main_layout = QHBoxLayout(self)

        # --- PANEL IZQUIERDO: FORMULARIO ---
        form_layout = QVBoxLayout()
        
        # CAMPO 1: Peso Objetivo (Numérico normal)
        lbl_weight = QLabel("Peso Seco (kg):")
        lbl_weight.setFont(QFont("Arial", 12))
        self.input_weight = QLineEdit()
        self.input_weight.setFont(QFont("Arial", 20))
        self.input_weight.setPlaceholderText("0.0")
        # Guardamos referencia del campo activo
        self.input_weight.mousePressEvent = lambda e: self.set_active_field("weight")

        # CAMPO 2: Tiempo de Terapia (Nuestro Widget Especial)
        lbl_time = QLabel("Duración Terapia (HH:MM:SS):")
        lbl_time.setFont(QFont("Arial", 12))
        self.input_time = TimeLineEdit()
        # Detectar click para enfocar (truco porque setReadOnly es True)
        # Usamos un EventFilter o sobrescribimos mousePressEvent
        self.input_time.mousePressEvent = lambda e: self.set_active_field("time")

        form_layout.addWidget(lbl_weight)
        form_layout.addWidget(self.input_weight)
        form_layout.addSpacing(20)
        form_layout.addWidget(lbl_time)
        form_layout.addWidget(self.input_time)
        form_layout.addStretch()
        
        # Indicador de campo activo
        self.lbl_status = QLabel("Seleccione un campo para editar")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addWidget(self.lbl_status)

        # --- PANEL DERECHO: TECLADO ---
        self.numpad = NumpadWidget()
        # Conectar señales del keypad a la función de manejo
        self.numpad.keyPressed.connect(self.handle_key_input)
        self.numpad.backspacePressed.connect(self.handle_backspace)

        # --- AGREGAR AL LAYOUT ---
        main_layout.addLayout(form_layout, 1) # Proporción 1
        main_layout.addWidget(self.numpad, 1) # Proporción 1

        self.current_field = None # Variable para saber en qué campo escribir

    def set_active_field(self, field_name):
        self.current_field = field_name
        
        # Feedback visual (Bordes)
        if field_name == "weight":
            self.input_weight.setStyleSheet("border: 2px solid orange;")
            self.input_time.setStyleSheet("border: 2px solid #007ACC;") # Reset
            self.lbl_status.setText("Editando: PESO")
        elif field_name == "time":
            self.input_time.setStyleSheet("border: 2px solid orange;")
            self.input_weight.setStyleSheet("border: 1px solid gray;") # Reset
            self.lbl_status.setText("Editando: TIEMPO")

    def handle_key_input(self, key):
        if self.current_field == "weight":
            # Lógica normal de texto
            current_text = self.input_weight.text()
            self.input_weight.setText(current_text + key)
            
        elif self.current_field == "time":
            # Lógica especial de tiempo
            self.input_time.add_digit(key)

    def handle_backspace(self):
        if self.current_field == "weight":
            current_text = self.input_weight.text()
            self.input_weight.setText(current_text[:-1])
            
        elif self.current_field == "time":
            self.input_time.backspace()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TherapyConfigScreen()
    window.show()
    sys.exit(app.exec())
