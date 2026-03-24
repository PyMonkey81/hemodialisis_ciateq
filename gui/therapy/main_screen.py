# gui/therapy/main_screen.py
# Home / Welcome screen displayed at startup (stacked index 0)

"""
Pantalla de inicio / bienvenida de la interfaz HMI.

Este módulo define la clase `MainScreen`, que representa la vista inicial
que se muestra al arrancar la aplicación o cuando el sistema está en estado
de reposo/desconectado. Su función principal es informativa y de presentación
de marca.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt


class MainScreen(QWidget):
    """
    Widget principal de bienvenida de la máquina de hemodiálisis.

    Esta clase hereda de QWidget y se encarga de renderizar la pantalla "Home"
    (índice 0 en el QStackedWidget principal).

    Características:
    ----------------
    - **Identidad Visual:** Muestra el nombre del dispositivo ("MÁQUINA DE HEMODIÁLISIS")
      y el nombre del modelo/marca ("Yeztli").
    - **Información Técnica:** Presenta la versión del software actual y la entidad
      desarrolladora (CIATEQ A.C.).
    - **Diseño:** Utiliza un diseño limpio con fondo degradado suave y tipografía
      grande para facilitar la lectura a distancia.
    - **Layout:** Organiza los elementos verticalmente (QVBoxLayout) con espaciado
      y alineación centrada.

    Atributos Públicos:
    -------------------
    No expone métodos públicos complejos ni señales, ya que es una pantalla estática.
    """


    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_ui()

    def setup_ui(self):
        # Soft gradient background
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #f1f5f9, stop:1 #f1f5f9);
            border-radius: 15px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.addStretch(2)

        # Main title
        title_label = QLabel("MÁQUINA DE HEMODIÁLISIS")
        title_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #000000;
            background: transparent;
            padding: 20px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Subtitle / Brand
        subtitle_label = QLabel("Yeztli")
        subtitle_label.setStyleSheet("""
            font-size: 60px;
            font-weight: bold;
            color: #782E44;
            background: transparent;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacing(40)

        # Information block
        info_label = QLabel(
            "<div style='line-height: 180%;'>"
            "<span style='font-size: 20px; color: #1e293b;'><b>Equipo desarrollado por</b></span><br>"
            "<span style='font-size: 32px; color: #1e293b; font-weight: bold;'>CIATEQ A.C.</span><br><br>"
            "<span style='font-size: 20px; color: #1e293b;'><b>Versión Software:</b> </span>"
            "<span style='font-size: 24px; color: #1e293b; font-weight: bold;'>1.0.2</span><br><br>"
            "<span style='font-size: 22px; color: #1e293b; font-weight: bold;'>"
            "Sistema de Hemodiálisis"
            "</span>"
            "</div>"
        )
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)

        info_label.setStyleSheet("""
            QLabel {
                background: #f1f5f9;
                padding: 50px;
                border-radius: 25px;
                border: 3px solid #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        info_label.setMaximumWidth(1400)

        main_layout.addWidget(info_label, alignment=Qt.AlignCenter)

        main_layout.addStretch(3)