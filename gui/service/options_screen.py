# gui/service/options_screen.py
# Service / Settings screen (stacked index 4)
# Provides access to test panels, manual mode, calibration, network config, and variable monitor
"""
Módulo para la pantalla de Opciones y Configuración de Servicio.

Este módulo define la clase `OptionsScreen`, que funciona como un menú principal
para acceder a diversas herramientas y configuraciones relacionadas con el
servicio, diagnóstico, calibración y monitorización del dispositivo de
hemodiálisis. Es un punto de acceso clave para el personal técnico o de servicio.

Características principales:
-----------------------------
- **Menú de Navegación:** Presenta una serie de botones que permiten al usuario
  acceder directamente a sub-pantallas especializadas, como:
    - Panel de pruebas
    - Modo manual
    - Calibración
    - Configuración de red
    - Monitor de variables en tiempo real
- **Interfaz Intuitiva:** Diseño limpio y enfocado en la navegación, con botones
  claros y de gran tamaño adecuados para interacción táctil.
- **Integración:** Cada botón está conectado a un método de la ventana principal
  (`HemodialysisHMI`) para cambiar la pantalla activa en el `QStackedWidget`.

Clase principal:
----------------
- `OptionsScreen`: Widget que actúa como el centro de navegación para las funciones
  de servicio y configuración.

Dependencias:
-------------
- `PySide6`: Para la construcción de la interfaz gráfica de usuario.
"""


from PySide6.QtWidgets import QWidget, QGridLayout, QFrame, QLabel, QPushButton
from PySide6.QtCore import Qt


class OptionsScreen(QWidget):
    """
    Options / Settings screen for service and configuration access.
    Acts as a hub to enter diagnostic, manual operation, calibration,
    network setup, and real-time variable monitoring screens.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Reference to main HemodialysisHMI window
        self.values = parent.current_values if parent else {}  # Shared values dict

        self.setFixedSize(1536, 726)  # Matches stacked widget size
        self.setStyleSheet("background: #0f172a;")

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("AJUSTES Y CONFIGURACIÓN")
        title_label.setStyleSheet("color: #ffffff; font-size: 48px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label, 0, 0, 1, 4)

        # # Buttons container
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet(
            "background: #ffffff; border-radius: 20px; border: 4px solid #1e293b;"
        )

        buttons_layout = QGridLayout(buttons_frame)
        buttons_layout.setSpacing(30)
        buttons_layout.setContentsMargins(50, 50, 50, 50)

        # # Service options
        options = [
            ("Panel de pruebas",        "#3134df", self.parent_window.show_test_panel_screen),
            ("Modo manual",             "#3134df", self.parent_window.show_manual_mode_screen),
            ("Calibración",             "#3134df", self.parent_window.show_calibration_screen),
            ("Configuración red",       "#3134df", self.parent_window.show_network_config_screen),
            ("Monitor de variables",    "#3134df", self.parent_window.show_real_time_var_screen),
        ]

        for i, (text, color, callback) in enumerate(options):
            btn = QPushButton(text)
            btn.setFixedSize(400, 150)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                               font-size: 28px; border-radius: 10px; }}
                QPushButton:pressed {{ background: #334155; }}
            """)    
            btn.clicked.connect(callback)   
            row = i // 2
            col = i % 2
            buttons_layout.addWidget(btn, row, col)

        layout.addWidget(buttons_frame, 1, 0, 4, 4)

    def update_values(self, new_values: dict):
        """Method to receive updated values, for consistency."""
        self.values = new_values
        # Currently no dynamic UI elements to update based on these values.
