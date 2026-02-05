#gui/components/ui_components.py

# códicos auxiliares para mostrar eventos de entrada de parametros, o customizar widgets para mejorar la 
# presentación en pantalla (DRY - Don´t repeat yourself)
from PySide6.QtWidgets import QLineEdit, QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from gui.components.ToggleSwitch import ToggleSwitch


class ClickableLineEdit(QLineEdit):
    clicked = Signal() # Señal 
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ToggleBox(QFrame):
    def __init__(self, label, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #fcfcfc;
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>{label}</b>")
        lbl_info.setStyleSheet("color: #000000; font-size: 18px; border:none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=60, height=30)

        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(self.toggle)



class DoubleToggleBox(QFrame):
    def __init__(self, label1_text, label2_text, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8; /* Un fondo ligeramente diferente para destacar */
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(120) # Ajusta la altura si es necesario para acomodar dos filas

        # Layout principal de la DoubleToggleBox (vertical)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5) # Menos espacio vertical entre las filas

        # --- Primera Fila: Label 1 y Toggle 1 ---
        row1_layout = QHBoxLayout()
        lbl1 = QLabel(f"<b>{label1_text}</b>")
        lbl1.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl1.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle1 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row1_layout.addWidget(lbl1)
        row1_layout.addStretch()
        row1_layout.addWidget(self.toggle1)
        main_layout.addLayout(row1_layout)

        # --- Segunda Fila: Label 2 y Toggle 2 ---
        row2_layout = QHBoxLayout()
        lbl2 = QLabel(f"<b>{label2_text}</b>")
        lbl2.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl2.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle2 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row2_layout.addWidget(lbl2)
        row2_layout.addStretch()
        row2_layout.addWidget(self.toggle2)
        main_layout.addLayout(row2_layout)
