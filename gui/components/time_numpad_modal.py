# gui/components/time_numpad_modal.py
"""
Módulo que implementa un diálogo modal de teclado numérico para la entrada de tiempo.

Este módulo proporciona una interfaz gráfica optimizada para pantallas táctiles
que permite al usuario ingresar valores de tiempo en formato **HH:MM**.
Se diferencia de un teclado numérico estándar en que gestiona la entrada
de dígitos con una lógica de desplazamiento (push) de derecha a izquierda,
manteniendo siempre el formato de tiempo visible, y valida que los valores
ingresados sean lógicos (horas 0-23, minutos 0-59).

Componentes principales:
-------------------------
- `TimeDisplayEdit`: Un widget de visualización personalizado (basado en `QLineEdit`)
  que maneja la lógica de manipulación de cadenas para simular un display digital
  de tiempo.
- `TimeNumpadDialog`: El cuadro de diálogo modal que contiene el teclado visual,
  el display y los botones de acción (Aceptar/Cancelar).

Características:
----------------
- **Entrada "Push"**: Los dígitos entran por la derecha y empujan los existentes
  hacia la izquierda (ej. escribir '1', '5' resulta en "00:15").
- **Validación**: Impide aceptar tiempos inválidos (como 65 minutos o 25 horas).
- **Estilo Oscuro**: Coherente con el resto de la interfaz HMI.
- **Botones Grandes**: Diseñado para facilitar la pulsación en pantallas táctiles.

Uso:
----
Generalmente se invoca desde widgets como `LabeledTimeInput`:
    dialog = TimeNumpadDialog(parent, initial_hh_mm="04:30")
    if dialog.exec():
        hours, minutes = dialog.get_hours_minutes()
"""


from PySide6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging
logger = logging.getLogger(__name__)


class TimeDisplayEdit(QLineEdit):
    """
    Widget de edición de línea personalizado para visualizar y manipular tiempo.
    """

    def __init__(self, parent=None, initial_hh_mm="00:00", theme_colors=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        # self.setFont(QFont("Consolas", 40, QFont.Bold))
        
        # Usar colores del tema pasado
        colors = theme_colors if theme_colors else {
            "display_bg": "#1e293b", 
            "display_border": "#475569", 
            "display_color": "#22d3ee"
        }
        self.setStyleSheet(f"""
            background-color: {colors['display_bg']};
            border: 2px solid {colors['display_border']};
            padding: 10px;
            color: {colors['display_color']};
            font-size: 36px; /* Tamaño de fuente del display de tiempo */
            font-weight: bold;
            font-family: "Consolas"; /* Fuente monoespaciada para mejor alineación de dígitos */
        """)

        self.raw_value = "0000"
        self.set_time_from_string(initial_hh_mm)
        self.update_display()

    def set_time_from_string(self, hh_mm: str):
        """Parse HH:MM string and set internal raw value."""
        parts = hh_mm.split(':')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            h = min(int(parts[0]), 99)   # Allows up to 99 hours (as in original)
            m = min(int(parts[1]), 59)
            self.raw_value = f"{h:02d}{m:02d}"
        else:
            self.raw_value = "0000"
        self.update_display()

    def add_digit(self, digit: str):
        """Append digit to raw value (push right, max 4 digits)."""
        if digit == '.':  # No decimal in time
            return

        if len(self.raw_value) < 4:
            self.raw_value += digit
        else:
            self.raw_value = self.raw_value[1:] + digit

        self.update_display()

    def backspace(self):
        """Remove last digit from raw value."""
        if self.raw_value:
            self.raw_value = self.raw_value[:-1]
        self.update_display()

    def update_display(self):
        """Format raw 4-digit value as HH:MM."""
        padded = self.raw_value.zfill(4)
        hh, mm = padded[:2], padded[2:]
        self.setText(f"{hh}:{mm}")

    def get_hours_minutes(self):
        """Return (hours, minutes) as integers."""
        padded = self.raw_value.zfill(4)
        return int(padded[:2]), int(padded[2:])

    def get_total_minutes(self):
        """Return total minutes (hours * 60 + minutes)."""
        h, m = self.get_hours_minutes()
        return h * 60 + m

    def set_time_from_minutes(self, total_minutes: int):
        """Set time from total minutes."""
        h = total_minutes // 60
        m = total_minutes % 60
        self.raw_value = f"{h:02d}{m:02d}"[-4:]
        self.update_display()

    def clear(self):
        """Reset to 00:00."""
        self.raw_value = "0000"
        self.update_display()


class TimeNumpadDialog(QDialog):
    """
    Diálogo modal que presenta un teclado numérico táctil para entrada de tiempo.
    """

    # ══════════════════════════════════════════════════════════════════════
    # DEFINICIÓN DE TEMAS
    # ══════════════════════════════════════════════════════════════════════
    THEMES = {
        "light": {
            "dialog_bg": "#ebebeb",
            "dialog_border": "#9ca3af",
            "label_color": "#1e293b", # Para QLabel general

            "display_bg": "#ffffff",
            "display_border": "#9ca3af",
            "display_color": "#1e293b",

            "btn_normal_bg": "#f3f4f6",
            "btn_normal_color": "#1e293b",
            "btn_normal_border": "#d1d5db",
            "btn_normal_hover": "#e5e7eb",
            "btn_normal_pressed_bg": "#22d3ee",
            "btn_normal_pressed_border": "#22d3ee",

            "btn_backspace_bg": "#fca5a5",
            "btn_backspace_color": "#7f1d1d",
            "btn_backspace_hover": "#f87171",
            "btn_backspace_pressed": "#ef4444",

            "btn_cancel_bg": "#9ca3af",
            "btn_cancel_color": "white",
            "btn_cancel_hover": "#6b7280",
            "btn_cancel_pressed": "#4b5563",

            "btn_accept_bg": "#22c55e",
            "btn_accept_color": "white",
            "btn_accept_hover": "#16a34a",
            "btn_accept_pressed": "#15803d",

            # Estilos para QMessageBox
            "msgbox_bg": "#ebebeb",
            "msgbox_border": "#9ca3af",
            "msgbox_label_bg": "transparent", # El QLabel ya es transparente por defecto en QMessageBox
            "msgbox_label_color": "#1e293b",
            "msgbox_btn_bg": "#3b82f6",
            "msgbox_btn_color": "#ffffff",
            "msgbox_btn_hover": "#60a5fa",
        },
        "dark": {
            "dialog_bg": "#0f172a",
            "dialog_border": "#334155",
            "label_color": "white",

            "display_bg": "#1e293b",
            "display_border": "#475569",
            "display_color": "#22d3ee",

            "btn_normal_bg": "#334155",
            "btn_normal_color": "#ffffff",
            "btn_normal_border": "#1e293b",
            "btn_normal_hover": "#475569",
            "btn_normal_pressed_bg": "#22d3ee",
            "btn_normal_pressed_border": "#22d3ee",

            "btn_backspace_bg": "#ef4444",
            "btn_backspace_color": "white",
            "btn_backspace_hover": "#dc2626",
            "btn_backspace_pressed": "#b91c1c",

            "btn_cancel_bg": "#64748b",
            "btn_cancel_color": "white",
            "btn_cancel_hover": "#475569",
            "btn_cancel_pressed": "#334155",

            "btn_accept_bg": "#22c55e",
            "btn_accept_color": "white",
            "btn_accept_hover": "#16a34a",
            "btn_accept_pressed": "#15803d",

            # Estilos para QMessageBox
            "msgbox_bg": "#0f172a",
            "msgbox_border": "#334155",
            "msgbox_label_bg": "#0f172a",
            "msgbox_label_color": "#e2e8f0",
            "msgbox_btn_bg": "#3b82f6",
            "msgbox_btn_color": "#ffffff",
            "msgbox_btn_hover": "#60a5fa",
        }
    }


    def __init__(self, parent=None, initial_hh_mm="00:00", title="Ingrese Tiempo (HH:MM)", theme: str = "light"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)

        # Cargar colores del tema seleccionado
        self.theme = theme
        self.colors = self.THEMES[theme]

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['dialog_bg']};
                border: 2px solid {self.colors['dialog_border']};
                border-radius: 12px;
            }}
            QLabel {{ color: {self.colors['label_color']}; }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ── Time Display ─────────────────────────────────────────────────────────
        self.time_display = TimeDisplayEdit(initial_hh_mm=initial_hh_mm, theme_colors=self.colors)
        self.time_display.setFixedSize(320, 100)
        main_layout.addWidget(self.time_display, alignment=Qt.AlignCenter)

        # ── Keypad Grid ──────────────────────────────────────────────────────────
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(12)

        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1), ('⌫', 3, 2)
        ]

        button_font = QFont("Arial", 36, QFont.Bold)

        for key, row, col in keys:
            btn = QPushButton(key)
            btn.setFixedSize(90, 90)
            btn.setFont(button_font)

            if key == '⌫':
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors['btn_backspace_bg']};
                        color: {self.colors['btn_backspace_color']};
                        border-radius: 12px;
                        border: none;
                    }}
                    QPushButton:hover {{ background-color: {self.colors['btn_backspace_hover']}; }}
                    QPushButton:pressed {{ background-color: {self.colors['btn_backspace_pressed']}; }}
                """)
                btn.clicked.connect(self.time_display.backspace)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors['btn_normal_bg']};
                        color: {self.colors['btn_normal_color']};
                        border-radius: 12px;
                        border: 2px solid {self.colors['btn_normal_border']};
                        font-size: 26px; /* Tamaño de fuente teclas numericas */
                        font-weight: bold;
                    }}
                    QPushButton:hover {{ background-color: {self.colors['btn_normal_hover']}; }}
                    QPushButton:pressed {{ background-color: {self.colors['btn_normal_pressed_bg']}; border-color: {self.colors['btn_normal_pressed_border']}; }}
                """)
                btn.clicked.connect(lambda _, k=key: self.time_display.add_digit(k))

            keypad_layout.addWidget(btn, row, col)

        
        spacer = QLabel("")
        spacer.setStyleSheet("background: transparent; border: none;") # Este spacer no se verá afectado por label_color
        keypad_layout.addWidget(spacer, 3, 0)

        main_layout.addLayout(keypad_layout)

        # ── Action Buttons ───────────────────────────────────────────────────────
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(70)
        cancel_btn.setFont(QFont("Arial", 18, QFont.Bold))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['btn_cancel_bg']};
                color: {self.colors['btn_cancel_color']};
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.colors['btn_cancel_hover']}; }}
            QPushButton:pressed {{ background-color: {self.colors['btn_cancel_pressed']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)

        accept_btn = QPushButton("ACEPTAR")
        accept_btn.setFixedHeight(70)
        accept_btn.setFont(QFont("Arial", 18, QFont.Bold))
        accept_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['btn_accept_bg']};
                color: {self.colors['btn_accept_color']};
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.colors['btn_accept_hover']}; }}
            QPushButton:pressed {{ background-color: {self.colors['btn_accept_pressed']}; }}
        """)
        accept_btn.clicked.connect(self.on_accept_clicked)
        action_layout.addWidget(accept_btn)

        main_layout.addLayout(action_layout)

    def get_hours_minutes(self):
        """Return current time as (hours, minutes) integers."""
        return self.time_display.get_hours_minutes()

    def get_total_minutes(self):
        """Return total minutes (hours × 60 + minutes)."""
        return self.time_display.get_total_minutes()

    def on_accept_clicked(self):
        """Validate time before accepting (hours 0-23, minutes 0-59)."""
        hours, minutes = self.time_display.get_hours_minutes()

        if not (0 <= minutes <= 59):
            self._show_invalid_time_message("Los minutos deben estar entre 00 y 59.")
            return

        if not (0 <= hours <= 23):  # 24-hour format validation
            self._show_invalid_time_message("Las horas deben estar entre 00 y 23.")
            return

        self.accept()

    def _show_invalid_time_message(self, detail_text: str):
        """Show styled warning message box for invalid time input."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setText("<b>Formato de tiempo inválido</b>")
        msg.setInformativeText(detail_text)
        msg.setWindowTitle("Error de entrada")
        msg.setStandardButtons(QMessageBox.Ok)

        # Aplicar estilos del tema al QMessageBox
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.colors['msgbox_bg']};
                border: 1px solid {self.colors['msgbox_border']};
            }}
            QMessageBox QLabel {{
                background-color: {self.colors['msgbox_label_bg']};
                color: {self.colors['msgbox_label_color']};
            }}
            QMessageBox QPushButton {{
                background-color: {self.colors['msgbox_btn_bg']};
                color: {self.colors['msgbox_btn_color']};
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 90px;
                font-weight: bold;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.colors['msgbox_btn_hover']};
            }}
        """)
        msg.exec()
















# # gui/components/time_numpad_modal.py
# """
# Módulo que implementa un diálogo modal de teclado numérico para la entrada de tiempo.

# Este módulo proporciona una interfaz gráfica optimizada para pantallas táctiles
# que permite al usuario ingresar valores de tiempo en formato **HH:MM**.
# Se diferencia de un teclado numérico estándar en que gestiona la entrada
# de dígitos con una lógica de desplazamiento (push) de derecha a izquierda,
# manteniendo siempre el formato de tiempo visible, y valida que los valores
# ingresados sean lógicos (horas 0-23, minutos 0-59).

# Componentes principales:
# -------------------------
# - `TimeDisplayEdit`: Un widget de visualización personalizado (basado en `QLineEdit`)
#   que maneja la lógica de manipulación de cadenas para simular un display digital
#   de tiempo.
# - `TimeNumpadDialog`: El cuadro de diálogo modal que contiene el teclado visual,
#   el display y los botones de acción (Aceptar/Cancelar).

# Características:
# ----------------
# - **Entrada "Push"**: Los dígitos entran por la derecha y empujan los existentes
#   hacia la izquierda (ej. escribir '1', '5' resulta en "00:15").
# - **Validación**: Impide aceptar tiempos inválidos (como 65 minutos o 25 horas).
# - **Estilo Oscuro**: Coherente con el resto de la interfaz HMI.
# - **Botones Grandes**: Diseñado para facilitar la pulsación en pantallas táctiles.

# Uso:
# ----
# Generalmente se invoca desde widgets como `LabeledTimeInput`:
#     dialog = TimeNumpadDialog(parent, initial_hh_mm="04:30")
#     if dialog.exec():
#         hours, minutes = dialog.get_hours_minutes()
# """


# from PySide6.QtWidgets import (
#     QDialog, QGridLayout, QPushButton, QLineEdit,
#     QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
# )
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QFont
# import logging
# logger = logging.getLogger(__name__)



# class TimeDisplayEdit(QLineEdit):
#     """
#     Widget de edición de línea personalizado para visualizar y manipular tiempo.

#     Actúa como la "pantalla" del teclado numérico. No permite la edición directa
#     con el teclado físico (es de solo lectura), sino que recibe comandos para
#     agregar dígitos o borrar. Mantiene internamente una cadena cruda de 4 dígitos
#     y la formatea visualmente como "HH:MM".

#     Características:
#     - **Lógica de Desplazamiento**: Al agregar un dígito, se añade al final y
#       el primer dígito se descarta, simulando una entrada de calculadora.
#     - **Formato Visual**: Siempre muestra 5 caracteres (2 dígitos de hora,
#       dos puntos, 2 dígitos de minutos).

#     Métodos clave:
#     - `add_digit(digit)`: Inserta un nuevo número.
#     - `backspace()`: Elimina el último número ingresado.
#     - `get_hours_minutes()`: Retorna el valor actual como tupla de enteros.
#     """

#     def __init__(self, parent=None, initial_hh_mm="00:00"):
#         super().__init__(parent)
#         self.setReadOnly(True)
#         self.setAlignment(Qt.AlignCenter)
#         self.setFont(QFont("Consolas", 24, QFont.Bold))
#         self.setStyleSheet("""
#             background-color: #1e293b;
#             border: 2px solid #475569;
#             padding: 5px;
#             color: #22d3ee;
#         """)

#         self.raw_value = "0000"
#         self.set_time_from_string(initial_hh_mm)
#         self.update_display()

#     def set_time_from_string(self, hh_mm: str):
#         """Parse HH:MM string and set internal raw value."""
#         parts = hh_mm.split(':')
#         if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
#             h = min(int(parts[0]), 99)   # Allows up to 99 hours (as in original)
#             m = min(int(parts[1]), 59)
#             self.raw_value = f"{h:02d}{m:02d}"
#         else:
#             self.raw_value = "0000"
#         self.update_display()

#     def add_digit(self, digit: str):
#         """Append digit to raw value (push right, max 4 digits)."""
#         if digit == '.':  # No decimal in time
#             return

#         if len(self.raw_value) < 4:
#             self.raw_value += digit
#         else:
#             self.raw_value = self.raw_value[1:] + digit

#         self.update_display()

#     def backspace(self):
#         """Remove last digit from raw value."""
#         if self.raw_value:
#             self.raw_value = self.raw_value[:-1]
#         self.update_display()

#     def update_display(self):
#         """Format raw 4-digit value as HH:MM."""
#         padded = self.raw_value.zfill(4)
#         hh, mm = padded[:2], padded[2:]
#         self.setText(f"{hh}:{mm}")

#     def get_hours_minutes(self):
#         """Return (hours, minutes) as integers."""
#         padded = self.raw_value.zfill(4)
#         return int(padded[:2]), int(padded[2:])

#     def get_total_minutes(self):
#         """Return total minutes (hours * 60 + minutes)."""
#         h, m = self.get_hours_minutes()
#         return h * 60 + m

#     def set_time_from_minutes(self, total_minutes: int):
#         """Set time from total minutes."""
#         h = total_minutes // 60
#         m = total_minutes % 60
#         self.raw_value = f"{h:02d}{m:02d}"[-4:]
#         self.update_display()

#     def clear(self):
#         """Reset to 00:00."""
#         self.raw_value = "0000"
#         self.update_display()


# class TimeNumpadDialog(QDialog):
#     """
#     Diálogo modal que presenta un teclado numérico táctil para entrada de tiempo.

#     Proporciona una interfaz completa para que el usuario configure horas y minutos.
#     Incluye un `TimeDisplayEdit` en la parte superior y una cuadrícula de botones
#     en la parte inferior.

#     Características:
#     - **Modal y Sin Bordes**: Se superpone a la aplicación bloqueando la interacción
#       con otras ventanas y elimina los bordes del sistema operativo para un look integrado.
#     - **Validación de Rango**: Al pulsar "ACEPTAR", verifica que las horas estén
#       entre 00-23 y los minutos entre 00-59. Si no es válido, muestra una alerta
#       y no cierra el diálogo.
#     - **Estilizado**: Utiliza hojas de estilo (QSS) para definir colores oscuros,
#       bordes redondeados y estados de los botones (hover/pressed).

#     Args:
#         parent (QWidget, optional): Widget padre.
#         initial_hh_mm (str): Valor inicial a mostrar (por defecto "00:00").
#         title (str): Título de la ventana (útil para contexto, ej. "Tiempo de Heparina").

#     Métodos:
#         get_hours_minutes() -> tuple[int, int]: Retorna la hora ingresada validada.
#         get_total_minutes() -> int: Retorna la duración total en minutos.
#     """


#     def __init__(self, parent=None, initial_hh_mm="00:00", title="Ingrese Tiempo (HH:MM)"):
#         super().__init__(parent)
#         self.setWindowTitle(title)
#         self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
#         self.setModal(True)

#         self.setStyleSheet("""
#             QDialog {
#                 background-color: #0f172a;
#                 border: 2px solid #334155;
#                 border-radius: 12px;
#             }
#             QLabel { color: white; }
#         """)

#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(20, 20, 20, 20)
#         main_layout.setSpacing(15)

#         # ── Time Display ─────────────────────────────────────────────────────────
#         self.time_display = TimeDisplayEdit(initial_hh_mm=initial_hh_mm)
#         self.time_display.setFixedSize(250, 70)
#         main_layout.addWidget(self.time_display, alignment=Qt.AlignCenter)

#         # ── Keypad Grid ──────────────────────────────────────────────────────────
#         keypad_layout = QGridLayout()
#         keypad_layout.setSpacing(12)

#         keys = [
#             ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
#             ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
#             ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
#             ('0', 3, 1), ('⌫', 3, 2)
#         ]

#         button_font = QFont("Arial", 36, QFont.Bold)

#         for key, row, col in keys:
#             btn = QPushButton(key)
#             btn.setFixedSize(90, 90)
#             btn.setFont(button_font)

#             if key == '⌫':
#                 btn.setStyleSheet("""
#                     QPushButton {
#                         background-color: #ef4444;
#                         color: white;
#                         border-radius: 12px;
#                         border: none;
#                     }
#                     QPushButton:hover { background-color: #dc2626; }
#                     QPushButton:pressed { background-color: #b91c1c; }
#                 """)
#                 btn.clicked.connect(self.time_display.backspace)
#             else:
#                 btn.setStyleSheet("""
#                     QPushButton {
#                         background-color: #334155;
#                         color: #ffffff;
#                         border-radius: 12px;
#                         border: 2px solid #1e293b;
#                     }
#                     QPushButton:hover { background-color: #475569; }
#                     QPushButton:pressed { background-color: #22d3ee; border-color: #22d3ee; }
#                 """)
#                 btn.clicked.connect(lambda _, k=key: self.time_display.add_digit(k))

#             keypad_layout.addWidget(btn, row, col)

        
#         spacer = QLabel("")
#         spacer.setStyleSheet("background: transparent; border: none;")
#         keypad_layout.addWidget(spacer, 3, 0)

#         main_layout.addLayout(keypad_layout)

#         # ── Action Buttons ───────────────────────────────────────────────────────
#         action_layout = QHBoxLayout()
#         action_layout.setSpacing(20)

#         cancel_btn = QPushButton("Cancelar")
#         cancel_btn.setFixedHeight(70)
#         cancel_btn.setFont(QFont("Arial", 18, QFont.Bold))
#         cancel_btn.setStyleSheet("""
#             QPushButton {
#                 background-color: #64748b;
#                 color: #ffffff;
#                 border-radius: 12px;
#                 border: none;
#             }
#             QPushButton:hover { background-color: #475569; }
#             QPushButton:pressed { background-color: #334155; }
#         """)
#         cancel_btn.clicked.connect(self.reject)
#         action_layout.addWidget(cancel_btn)

#         accept_btn = QPushButton("ACEPTAR")
#         accept_btn.setFixedHeight(70)
#         accept_btn.setFont(QFont("Arial", 18, QFont.Bold))
#         accept_btn.setStyleSheet("""
#             QPushButton {
#                 background-color: #22c55e;
#                 color: #ffffff;
#                 border-radius: 12px;
#                 border: none;
#             }
#             QPushButton:hover { background-color: #16a34a; }
#             QPushButton:pressed { background-color: #15803d; }
#         """)
#         accept_btn.clicked.connect(self.on_accept_clicked)
#         action_layout.addWidget(accept_btn)

#         main_layout.addLayout(action_layout)

#     def get_hours_minutes(self):
#         """Return current time as (hours, minutes) integers."""
#         return self.time_display.get_hours_minutes()

#     def get_total_minutes(self):
#         """Return total minutes (hours × 60 + minutes)."""
#         return self.time_display.get_total_minutes()

#     def on_accept_clicked(self):
#         """Validate time before accepting (hours 0-23, minutes 0-59)."""
#         hours, minutes = self.time_display.get_hours_minutes()

#         if not (0 <= minutes <= 59):
#             self._show_invalid_time_message("Los minutos deben estar entre 00 y 59.")
#             return

#         if not (0 <= hours <= 23):  # 24-hour format validation
#             self._show_invalid_time_message("Las horas deben estar entre 00 y 23.")
#             return

#         self.accept()

#     def _show_invalid_time_message(self, detail_text: str):
#         """Show styled warning message box for invalid time input."""
#         msg = QMessageBox(self)
#         msg.setIcon(QMessageBox.Warning)
#         msg.setText("<b>Formato de tiempo inválido</b>")
#         msg.setInformativeText(detail_text)
#         msg.setWindowTitle("Error de entrada")
#         msg.setStandardButtons(QMessageBox.Ok)

#         msg.setStyleSheet("""
#             QMessageBox {
#                 background-color: #0f172a;
#                 border: 1px solid #334155;
#             }
#             QMessageBox QLabel {
#                 background-color: #0f172a;
#                 color: #e2e8f0;
#             }
#             QMessageBox QPushButton {
#                 background-color: #3b82f6;
#                 color: #ffffff;
#                 border-radius: 6px;
#                 padding: 8px 20px;
#                 min-width: 90px;
#                 font-weight: bold;
#             }
#             QMessageBox QPushButton:hover {
#                 background-color: #60a5fa;
#             }
#         """)
#         msg.exec()