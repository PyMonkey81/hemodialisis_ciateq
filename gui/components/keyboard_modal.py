#gui/components/keyboard_modal.py

from PySide6.QtWidgets import (
    QDialog, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

class KeyboardDialog(QDialog):
    """
    Teclado QWERTY táctil completo.
    Mantiene el estilo del NumpadDialog para consistencia visual.
    """
    def __init__(self, parent=None, initial_text: str = "", title: str = "Ingrese Texto"):
        super().__init__(parent)
        self.setWindowTitle(title)

        # Configuración de ventana (Modal, sin bordes)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.resize(1024, 600)  # Tamaño sugerido para teclado completo

        self.caps_lock = False
        self.btn_chars = [] # Para guardar referencias y cambiar a Mayúsculas

        # Estilos idénticos a tu Numpad
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 12px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ─── 1. Pantalla de visualización ──────────────────────────────
        self.display = QLineEdit(initial_text)
        self.display.setFixedHeight(70)
        self.display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Alineado a izquierda para texto
        self.display.setReadOnly(True) # Solo lectura, entrada vía botones
        self.display.setFont(QFont("Arial", 28, QFont.Bold))
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #22d3ee;
                border: 2px solid #475569;
                border-radius: 10px;
                padding: 0 15px;
            }
        """)
        main_layout.addWidget(self.display)

        # ─── 2. Contenedor de Teclas ───────────────────────────────────
        keys_container = QVBoxLayout()
        keys_container.setSpacing(8)
        
        # Definición de filas del teclado
        # Fila 1: Números
        row1 = list("1234567890")
        # Fila 2: QWERTY...
        row2 = list("qwertyuiop")
        # Fila 3: ASDF...
        row3 = list("asdfghjklñ")
        # Fila 4: ZXCV...
        row4 = list("zxcvbnm")

        self._create_row(keys_container, row1)
        self._create_row(keys_container, row2)
        self._create_row(keys_container, row3)
        
        # Fila 4 especial (con Shift y Backspace)
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(8)
        
        # Botón SHIFT
        self.shift_btn = QPushButton("⇧")
        self.shift_btn.setFixedSize(90, 70)
        self.shift_btn.setFont(QFont("Arial", 20, QFont.Bold))
        self.shift_btn.setStyleSheet(self._get_func_btn_style())
        self.shift_btn.clicked.connect(self._toggle_caps)
        row4_layout.addWidget(self.shift_btn)

        # Letras Z-M
        for char in row4:
            self._add_char_button(row4_layout, char)

        # Botón BACKSPACE
        back_btn = QPushButton("⌫")
        back_btn.setFixedSize(90, 70)
        back_btn.setFont(QFont("Arial", 20, QFont.Bold))
        back_btn.setStyleSheet(self._get_danger_btn_style())
        back_btn.clicked.connect(self._backspace)
        row4_layout.addWidget(back_btn)
        
        keys_container.addLayout(row4_layout)

        # Fila 5: Espacio
        row5_layout = QHBoxLayout()
        space_btn = QPushButton("ESPACIO")
        space_btn.setFixedHeight(70)
        space_btn.setFont(QFont("Arial", 16, QFont.Bold))
        space_btn.setStyleSheet(self._get_func_btn_style())
        space_btn.clicked.connect(lambda: self._add_char(" "))
        row5_layout.addWidget(space_btn)
        keys_container.addLayout(row5_layout)

        main_layout.addLayout(keys_container)

        # ─── 3. Botones de Acción (Cancelar / Aceptar) ─────────────────
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(60)
        cancel_btn.setFont(QFont("Arial", 16, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b; color: white; border-radius: 12px; border: none;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:pressed { background-color: #334155; }
        """)
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)

        accept_btn = QPushButton("ACEPTAR")
        accept_btn.setFixedHeight(60)
        accept_btn.setFont(QFont("Arial", 16, QFont.Bold))
        accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e; color: white; border-radius: 12px; border: none;
            }
            QPushButton:hover { background-color: #16a34a; }
            QPushButton:pressed { background-color: #15803d; }
        """)
        accept_btn.clicked.connect(self.accept)
        action_layout.addWidget(accept_btn)

        main_layout.addLayout(action_layout)

    # ─── Métodos Auxiliares de Construcción ───
    def _create_row(self, parent_layout, chars):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        for char in chars:
            self._add_char_button(row_layout, char)
        parent_layout.addLayout(row_layout)

    def _add_char_button(self, layout, char):
        btn = QPushButton(char)
        btn.setFixedHeight(70) # Altura cómoda para dedo
        # Ancho flexible pero con mínimo
        btn.setMinimumWidth(60) 
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFont(QFont("Arial", 22, QFont.Bold))
        btn.setStyleSheet(self._get_normal_btn_style())
        
        # Conectamos usando una variable capturada 'char'
        # Usamos property para guardar la letra base (lowercase)
        btn.setProperty("char_base", char) 
        btn.clicked.connect(lambda ch=char: self._on_key_click(btn))
        
        layout.addWidget(btn)
        self.btn_chars.append(btn)

    # ─── Estilos (Reutilizando tu paleta) ───
    def _get_normal_btn_style(self):
        return """
            QPushButton {
                background-color: #334155; color: white; border-radius: 8px; border: 2px solid #1e293b;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:pressed { background-color: #22d3ee; border-color: #22d3ee; }
        """

    def _get_func_btn_style(self):
        return """
            QPushButton {
                background-color: #475569; color: #e2e8f0; border-radius: 8px; border: none;
            }
            QPushButton:pressed { background-color: #cbd5e1; color: #0f172a; }
        """

    def _get_danger_btn_style(self):
        return """
            QPushButton {
                background-color: #ef4444; color: white; border-radius: 8px; border: none;
            }
            QPushButton:pressed { background-color: #b91c1c; }
        """

    # ─── Lógica ───
    def _on_key_click(self, btn):
        text_to_add = btn.text()
        self._add_char(text_to_add)

    def _add_char(self, char):
        self.display.setText(self.display.text() + char)

    def _backspace(self):
        text = self.display.text()
        self.display.setText(text[:-1])

    def _toggle_caps(self):
        self.caps_lock = not self.caps_lock
        
        # Estilo visual para indicar activo/inactivo
        if self.caps_lock:
            self.shift_btn.setStyleSheet("background-color: #22d3ee; color: #0f172a; border-radius: 8px;")
        else:
            self.shift_btn.setStyleSheet(self._get_func_btn_style())

        # Actualizar texto de botones
        for btn in self.btn_chars:
            base_char = btn.property("char_base")
            if self.caps_lock:
                btn.setText(base_char.upper())
            else:
                btn.setText(base_char.lower())

    def get_value(self) -> str:
        return self.display.text().strip()
