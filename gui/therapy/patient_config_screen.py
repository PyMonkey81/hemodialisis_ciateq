# gui/therapy/patient_config_screen.py
# Patient configuration screen for entering or editing patient-specific parameters

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class PatientConfigScreen(QWidget):
    """
    Patient configuration screen.
    Allows editing of patient-specific dialysis parameters (weight, dry weight, UF goal, etc.).
    Uses a soft gradient background and vertical layout with spacing.
    Stacked index: [ajusta según tu orden, probablemente 5 o similar].
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Reference to main HemodialysisHMI
        self.values = parent.current_values if parent else {}  # Shared values dict

        self.setFixedSize(1536, 726)  # Matches stacked widget size
        self.setup_ui()

    def setup_ui(self):
        # Soft blue-to-light gradient background (original colors preserved)
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #e0e7ff, stop:1 #c7d2fe);
            border-radius: 15px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)  # Breathing room
        main_layout.setSpacing(20)

        # Placeholder title (puedes personalizar o quitar)
        title_label = QLabel("CONFIGURACIÓN DEL PACIENTE")
        title_label.setStyleSheet("""
            color: #1e40af;
            font-size: 48px;
            font-weight: bold;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Spacer to center future content
        main_layout.addStretch(2)

        # Aquí agregarás los widgets reales (ej. peso seco, objetivo UF, alergias, etc.)
        # Ejemplo placeholder:
        # self.lbl_dry_weight = QLabel("Peso seco: 70.0 kg")
        # self.lbl_dry_weight.setStyleSheet("color: #1e293b; font-size: 28px;")
        # main_layout.addWidget(self.lbl_dry_weight, alignment=Qt.AlignCenter)

        # Bottom spacer
        main_layout.addStretch(1)

    def update_values(self, new_values: dict):
        """Method to receive updated values, for consistency."""
        self.values = new_values
        # Currently no dynamic UI elements to update based on these values.
