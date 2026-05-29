from PySide6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout,QLabel, QMessageBox # <-- AGREGAR QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
# from pyqtgraph import colors # <-- Esto parece un import no usado o para un tema, lo quito para limpieza


class NumpadDialog(QDialog):
    """
    Diálogo modal con teclado numérico virtual.

    Proporciona una interfaz limpia para la entrada de números. Incluye un
    título descriptivo, una pantalla de visualización del valor actual,
    una cuadrícula de botones numéricos (0-9, punto, retroceso) y botones
    de acción (Aceptar/Cancelar).

    Args:
        parent (QWidget, optional): Widget padre del diálogo.
        initial_value (str, optional): Valor inicial a mostrar en la pantalla
                                       al abrir el diálogo. Por defecto "".
        title (str, optional): Título descriptivo que aparece en la cabecera
                               (ej. "Configurar Temperatura"). Por defecto "Ingrese Valor".
        min_value (float | None, optional): Valor mínimo permitido. Si es None, no hay mínimo.
        max_value (float | None, optional): Valor máximo permitido. Si es None, no hay máximo.

    Métodos:
        get_value() -> Union[int, float, None]: Retorna el valor ingresado convertido
                                                  al tipo numérico apropiado, o None si
                                                  la entrada está vacía, es inválida o fuera de rango.
    """

    # ══════════════════════════════════════════════════════════════════════
    # DEFINICIÓN DE TEMAS
    # ══════════════════════════════════════════════════════════════════════
    THEMES = {
        "light": {
            "dialog_bg": "#ebebeb",
            "dialog_border": "#9ca3af",
            "title_bg": "#ebebeb",
            "title_color": "#1e293b",
            "display_bg": "#ffffff",
            "display_color": "#1e293b",
            "display_border": "#9ca3af",
            "button_bg": "#f3f4f6",
            "button_color": "#1e293b",
            "button_border": "#d1d5db",
            "button_hover": "#e5e7eb",
            "backspace_bg": "#fca5a5",
            "backspace_color": "#7f1d1d",
            "backspace_hover": "#f87171",
            "backspace_pressed": "#ef4444",
        },
        "dark": {
            "dialog_bg": "#1e293b",
            "dialog_border": "#334155",
            "title_bg": "#0f172a",
            "title_color": "#ffffff",
            "display_bg": "#0f172a",
            "display_color": "#22d3ee",
            "display_border": "#475569",
            "button_bg": "#334155",
            "button_color": "#ffffff",
            "button_border": "#1e293b",
            "button_hover": "#475569",
            "backspace_bg": "#ef4444",
            "backspace_color": "#ffffff",
            "backspace_hover": "#dc2626",
            "backspace_pressed": "#b91c1c",
        }
    }


    def __init__(self, parent=None, initial_value: str = "", title: str = "Ingrese Valor",
                 theme: str = "light", min_value: float | None = None, max_value: float | None = None): 
        super().__init__(parent)
        self.setWindowTitle(title)
        self.theme = theme
        self._min_value = min_value  
        self._max_value = max_value 
        
        colors = self.THEMES[theme]

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['dialog_bg']};
                border: 2px solid {colors['dialog_border']};
                border-radius: 12px;
            }}
                QLabel {{ color: {colors['title_color']}; }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['title_color']};
                font-size: 24px;
                font-weight: bold;
                background-color: {colors['title_bg']};
                padding: 12px;
                border: 2px solid {colors['dialog_border']};
            }}
        """)
        main_layout.addWidget(title_label)

        self.display = QLineEdit(initial_value)
        self.display.setFixedHeight(70)
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display.setReadOnly(True)
        self.display.setFont(QFont("Arial", 36, QFont.Bold))
        self.display.setStyleSheet(f"""
            QLineEdit {{
                font-size: 36px;
                font-family: "Arial";
                font-weight: bold;
                background-color: {colors['display_bg']};
                color: {colors['display_color']};
                border: 2px solid {colors['display_border']};
                border-radius: 10px;
                padding: 0 15px;
            }}
        """)
        main_layout.addWidget(self.display)

        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(12)

        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('⌫', 3, 2)
        ]

        button_font = QFont("Arial", 32, QFont.Bold)

        for key, row, col in keys:
            btn = QPushButton(key)
            btn.setFixedSize(90, 90)
            btn.setFont(button_font)

            if key == '⌫':
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['backspace_bg']};
                        color: {colors['backspace_color']};
                        border-radius: 12px;
                        border: none;
                    }}
                    QPushButton:hover {{ background-color: {colors['backspace_hover']}; }}
                    QPushButton:pressed {{ background-color: {colors['backspace_pressed']}; }}
                """)
                btn.clicked.connect(self._backspace)

            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-size: 32px;
                        font-family: "Arial";
                        font-weight: bold;
                        background-color: {colors['button_bg']};
                        color: {colors['button_color']};
                        border-radius: 12px;
                        border: 2px solid {colors['button_border']};
                    }}
                    QPushButton:hover {{ background-color: {colors['button_hover']}; }}
                    QPushButton:pressed {{ background-color: #22d3ee; border-color: #22d3ee; }}
                """)
                btn.clicked.connect(lambda _, k=key: self._add_digit(k))

            keypad_layout.addWidget(btn, row, col)

        main_layout.addLayout(keypad_layout)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(70)
        cancel_btn.setFont(QFont("Arial", 24, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-family: "Arial";
                font-weight: bold;
                background-color: #64748b;
                color: #ffffff;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:pressed { background-color: #334155; }
        """)
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)

        accept_btn = QPushButton("ACEPTAR")
        accept_btn.setFixedHeight(70)
        accept_btn.setFont(QFont("Arial", 24, QFont.Bold))
        accept_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-family: "Arial";
                font-weight: bold;
                background-color: #22c55e;
                color: #ffffff;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #16a34a; }
            QPushButton:pressed { background-color: #15803d; }
        """)
        accept_btn.clicked.connect(self.accept) # La validación final ocurrirá en get_value() al presionar ACEPTAR
        action_layout.addWidget(accept_btn)

        main_layout.addLayout(action_layout)

    def _add_digit(self, digit: str):
        """Append digit or decimal point to display."""
        current_text = self.display.text()

        # Evitar múltiples puntos decimales
        if digit == '.' and '.' in current_text:
            return

        # Para un display vacío o "0", si no es punto, reemplaza el "0"
        if not current_text and digit == '.': # Si empieza con ".", añade "0."
            current_text = "0"
        elif current_text == "0" and digit != '.': # Si es "0" y no ".", lo reemplaza
            current_text = ""
        
        potential_text = current_text + digit

        # Validación intermedia para MAX_VALUE mientras se escribe
        if self._max_value is not None and potential_text and potential_text != '.':
            try:
                # Si el valor potencial excede el máximo, no añadir el dígito
                if float(potential_text) > self._max_value:
                    # Opcional: Mostrar una advertencia al usuario aquí mismo.
                    # QMessageBox.warning(self, "Advertencia", f"El valor no puede exceder {self._max_value}")
                    return
            except ValueError:
                # Esto manejaría casos como '1..', que float() no puede convertir
                pass
        
        self.display.setText(potential_text)


    def _backspace(self):
        """Remove last character from display."""
        current_text = self.display.text()
        self.display.setText(current_text[:-1] if current_text else "")
        # Si se borra todo, y hay min_value > 0, el display debería volver a "0" o mantenerse vacío
        if not self.display.text() and self._min_value is not None and self._min_value > 0:
            self.display.setText("0") # Para evitar que quede vacío y rompa la validación de min_value al aceptar

    def get_value(self):
        """
        Return the entered value as float or int, depending on if it contains a decimal point.
        Returns None if empty, invalid, or out of range.
        """
        text = self.display.text().strip()
        if not text:
            QMessageBox.warning(self, "Entrada Vacía", "Por favor, ingrese un valor.")
            return None # Retornar None si está vacío

        try:
            val = float(text)
            # Determinar si es int o float para el retorno
            if '.' not in text and val.is_integer():
                val = int(val)
        except ValueError:
            QMessageBox.critical(self, "Valor Inválido", "El valor ingresado no es un número válido.")
            return None # Retornar None si es inválido

        # Validar contra min_value
        if self._min_value is not None and val < self._min_value:
            QMessageBox.warning(self, "Valor Fuera de Rango",
                                f"El valor no puede ser menor a {self._min_value}.")
            return None

        # Validar contra max_value
        if self._max_value is not None and val > self._max_value:
            QMessageBox.warning(self, "Valor Fuera de Rango",
                                f"El valor no puede ser mayor a {self._max_value}.")
            return None
        
        return val # Retornar el valor si pasa todas las validaciones
