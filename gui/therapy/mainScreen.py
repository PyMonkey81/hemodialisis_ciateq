# gui/therapy/mainScreen.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt


class mainScr(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setup_ui(self):
        # Fondo degradado suave 
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0  #f1f5f9, stop:1  #f1f5f9);
            border-radius: 15px;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)  # ← márgenes del layout
        layout.addStretch(2)

        # Título principal
        titulo = QLabel("MÁQUINA DE HEMODIÁLISIS")
        titulo.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #bfbfbf;
            background: transparent;
            padding: 20px;
        """)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Subtítulo  5E0A0A    /*color: #9B1B30;*/
        subtitulo = QLabel("Yeztli")
        subtitulo.setStyleSheet("""
            font-size: 60px;
            font-weight: bold;          
            color: #782E44;                                 
            background: transparent;
        """)
        subtitulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitulo)

        layout.addSpacing(40)

        # Información (AHORA SÍ OCUPA TODO EL ANCHO)
        info = QLabel(
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
        info.setTextFormat(Qt.RichText)
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.setContentsMargins(80, 40, 80, 40)
        info.setStyleSheet("""
            QLabel {
                background:  #f1f5f9;
                padding: 50px;           /* ← REDUCIDO de 50px a 30px */
                border-radius: 25px;
                border: 3px solid  #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        info.setMaximumWidth(1400)

        layout.addWidget(info, alignment=Qt.AlignCenter)  # ← centrado perfecto

        layout.addStretch(3)

