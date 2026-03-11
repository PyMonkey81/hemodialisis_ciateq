# gui/components/numpad_modal.py
# Modal numeric keypad dialog for touch-friendly input of decimal values

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout,QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class NumpadDialog(QDialog):
    """
    Touch-friendly numeric keypad dialog for entering decimal values.
    Supports backspace, decimal point, and accept/cancel actions.
    """

    def __init__(self, parent=None, initial_value: str = "", title: str = "Ingrese Valor"):
        super().__init__(parent)
        self.setWindowTitle(title)

        # Frameless + modal for full touch experience
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 12px;
            }
            QLabel { color: white; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

# ── Título personalizado ──────────────────────────────────────────────────
        title_label = QLabel(title)  # Usa el parámetro title que pasas al __init__
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                background-color: #1e293b;
                padding: 12px;
                border-bottom: 2px solid #334155;
            }
        """)
        main_layout.addWidget(title_label)

        # ── Display (read-only value preview) ────────────────────────────────────
        self.display = QLineEdit(initial_value)
        self.display.setFixedHeight(70)
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display.setReadOnly(True)
        self.display.setFont(QFont("Arial", 36, QFont.Bold))
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

        # ── Keypad Grid ──────────────────────────────────────────────────────────
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(12)

        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('⌫', 3, 2)
        ]

        button_font = QFont("Arial", 36, QFont.Bold)

        for key, row, col in keys:
            btn = QPushButton(key)
            btn.setFixedSize(90, 90)
            btn.setFont(button_font)

            if key == '⌫':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ef4444;
                        color: white;
                        border-radius: 12px;
                        border: none;
                    }
                    QPushButton:hover { background-color: #dc2626; }
                    QPushButton:pressed { background-color: #b91c1c; }
                """)
                btn.clicked.connect(self._backspace)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #334155;
                        color: white;
                        border-radius: 12px;
                        border: 2px solid #1e293b;
                    }
                    QPushButton:hover { background-color: #475569; }
                    QPushButton:pressed { background-color: #22d3ee; border-color: #22d3ee; }
                """)
                btn.clicked.connect(lambda _, k=key: self._add_digit(k))

            keypad_layout.addWidget(btn, row, col)

        main_layout.addLayout(keypad_layout)

        # ── Action Buttons (Cancel / Accept) ─────────────────────────────────────
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(70)
        cancel_btn.setFont(QFont("Arial", 18, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
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
        accept_btn.setFont(QFont("Arial", 18, QFont.Bold))
        accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #16a34a; }
            QPushButton:pressed { background-color: #15803d; }
        """)
        accept_btn.clicked.connect(self.accept)
        action_layout.addWidget(accept_btn)

        main_layout.addLayout(action_layout)

    def _add_digit(self, digit: str):
        """Append digit or decimal point to display."""
        current_text = self.display.text()

        # Prevent multiple decimal points
        if digit == '.' and '.' in current_text:
            return

        # Replace leading zero with new digit (unless it's a decimal)
        if current_text == "0" and digit != ".":
            current_text = ""

        self.display.setText(current_text + digit)

    def _backspace(self):
        """Remove last character from display."""
        current_text = self.display.text()
        self.display.setText(current_text[:-1] if current_text else "")

    # def get_value(self) -> float:
    #     """Return the entered value as float (0.0 if empty or invalid)."""
    #     text = self.display.text().strip()
    #     if not text or text == ".":
    #         return 0.0
    #     try:
    #         return float(text)
    #     except ValueError:
    #         return 0.0


    def get_value(self): # Ya no necesita tipo hint float
        """
        Return the entered value as float or int, depending on if it contains a decimal point.
        Returns 0 if empty or invalid.
        """
        text = self.display.text().strip()
        if not text or text == ".":
            return 0 # Default to int 0 if empty/invalid

        try:
            # Si el texto contiene un punto, es un float
            if '.' in text:
                return float(text)
            # Si no contiene un punto, es un entero
            else:
                return int(text)
        except ValueError:
            return 0 # Default to int 0 if conversion fails
