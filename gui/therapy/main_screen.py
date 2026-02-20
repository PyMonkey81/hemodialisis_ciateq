# gui/therapy/main_screen.py
# Home / Welcome screen displayed at startup (stacked index 0)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt


class MainScreen(QWidget):
    """
    Main welcome/home screen of the hemodialysis machine HMI.
    Displays device name, version, developer information and branding.
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