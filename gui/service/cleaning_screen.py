# gui/service/cleaning_screen.py
# Cleaning / Disinfection screen (stacked index 3)
# Controls chemical disinfection cycle with progress tracking and safety checks

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
import logging
try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

logger = logging.getLogger(__name__)

class CleaningScreen(QWidget):
    """
    Cleaning and disinfection screen.
    Manages the chemical disinfection cycle with progress bar,
    remaining time display, and conditional start button.
    """
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}

        # Internal state
        self.cleaning_in_progress = False

        # Fixed size matching stacked widget
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #0f172a;")  # Industrial dark blue

        # Cycle tracking
        self.current_phase = "Esperando condiciones..."
        self.total_time_seconds = 0
        self.remaining_time_seconds = 0

        # Timer for progress updates (1 second interval)
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(30)

        # ── Title ────────────────────────────────────────────────────────────────
        title_label = QLabel("Limpieza / Desinfección")
        title_label.setStyleSheet("""
            color: #3d3d3d;
            font-size: 52px;
            font-weight: bold;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # ── Current Phase / Status ───────────────────────────────────────────────
        self.phase_label = QLabel(self.current_phase)
        self.phase_label.setStyleSheet("""
            color: #94a3b8;
            font-size: 32px;
            font-weight: bold;
            background: transparent;
            min-height: 60px;
        """)
        self.phase_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.phase_label)

        # ── Progress Bar ─────────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m seg")
        self.progress_bar.setFixedHeight(60)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b;
                border: 2px solid #475569;
                border-radius: 10px;
                text-align: center;
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3b82f6, stop:1 #60a5fa);
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # ── Remaining Time ───────────────────────────────────────────────────────
        self.time_label = QLabel("Tiempo restante: --:--")
        self.time_label.setStyleSheet("""
            color: #cbd5e1;
            font-size: 28px;
            font-weight: bold;
            background: transparent;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.time_label)

        # Spacer
        main_layout.addStretch()

        # ── Start / Restart Button ───────────────────────────────────────────────

        
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Iniciar limpieza")
        self.start_button.setFixedSize(300, 100)
        self.start_button.setEnabled(False)  # Disabled until ready state
        self.start_button.setProperty("base_color", "#047857")         
        self.start_button.setStyleSheet("""
            QPushButton {
                background: #047857;
                color: white;
                font-size: 38px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
                padding: 10px;
            }
            QPushButton:hover { background: #065f46; }
            QPushButton:pressed { background: #064e3b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        self.start_button.clicked.connect(self._start_cleaning)
        button_layout.addWidget(self.start_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Initial UI state
        self.phase_label.setText("Esperando estado listo...")
        self.progress_bar.setValue(0)
        self.progress_timer.stop()

    def reset_ui(self):
        """Reset UI to initial waiting state."""
        self.cleaning_in_progress = False
        self.current_phase = "Esperando condiciones..."
        self.phase_label.setText(self.current_phase)
        self.progress_bar.setValue(0)
        self.time_label.setText("Tiempo restante: --:--")

        self.start_button.setEnabled(False)
        self.start_button.setText("Iniciar limpieza")

        # Reconnect original signal (in case it was changed to reset)
        try:
            self.start_button.clicked.disconnect()
        except TypeError:
            pass
        self.start_button.clicked.connect(self._start_cleaning)

        self.progress_timer.stop()

    def _start_cleaning(self):
        """Initiate the disinfection cycle."""
        self.cleaning_in_progress = True

        # Send command to controller
        try:
            self.on_user_input_setpoint("treatmentModeSelection", 3.0)
            self.on_user_boolean_command("dialyModeOperationStart",True)
        except Exception as e:
            logger.error(f"Error {e}")

        # Configure cycle duration (900 seconds = 15 minutes)
        self.total_time_seconds = 900
        self.remaining_time_seconds = self.total_time_seconds

        self.current_phase = "Desinfección química en curso..."
        self.phase_label.setText(self.current_phase)
        self.start_button.setEnabled(False)
        self.start_button.setText("En proceso...")

        self.progress_bar.setMaximum(self.total_time_seconds)
        self.progress_bar.setValue(0)

        # Start 1-second update timer
        self.progress_timer.start(1000)

        self._update_time_display()

    def _update_progress(self):
        """Update progress every second."""
        if self.remaining_time_seconds > 0:
            self.remaining_time_seconds -= 1
            self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
            self._update_time_display()
        else:
            self.progress_timer.stop()
            self._finish_cleaning()

    def _update_time_display(self):
        """Format and display remaining time."""
        minutes = self.remaining_time_seconds // 60
        seconds = self.remaining_time_seconds % 60
        self.time_label.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

    def _finish_cleaning(self):
        """Handle cycle completion."""
        self.cleaning_in_progress = False
        self.current_phase = "Limpieza completada"
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
        self.time_label.setText("Tiempo restante: 00:00")
        self.progress_bar.setValue(self.total_time_seconds)

        self.start_button.setText("Reiniciar")
        self.start_button.setEnabled(True)

        # Change button action to reset
        try:
            self.start_button.clicked.disconnect()
        except TypeError:
            pass
        self.start_button.clicked.connect(self.reset_ui)

    def update_values(self, new_values: dict):
        """Receive and process updated values from main window."""
        self.current_values = new_values
        pass


    def update_buttons_state(self, status_code):
        """
        Habilita o deshabilita el botón de limpieza basado en el estado.
        Estandarizado con DialysisScreen.
        """
        if self.cleaning_in_progress:
            return

        # Estilo deshabilitado (Gris)
        style_disabled = """
            QPushButton {
                background: #334155; color: #64748b;
                font-size: 38px; font-weight: bold; border: none;
                border-radius: 16px; padding: 10px;
            }
        """
        # Función para aplicar estilo habilitado (Verde original)
        def set_enabled_style(btn):
            color = btn.property("base_color")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: white;
                    font-size: 38px; font-weight: bold; border: none;
                    border-radius: 16px; padding: 10px;
                }}
                QPushButton:hover {{ background: #065f46; }}
                QPushButton:pressed {{ background: #064e3b; }}
            """)

        # Lógica de Estados
        # 6 = INFUSION (Listo para limpieza)
        if status_code == 6:
            if not self.start_button.isEnabled():
                self.start_button.setEnabled(True)
                set_enabled_style(self.start_button)
                
                # Feedback visual en etiquetas
                self.current_phase = "Sistema listo para limpieza"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
        
        else:
            # Cualquier otro estado deshabilita el botón
            if self.start_button.isEnabled():
                self.start_button.setEnabled(False)
                self.start_button.setStyleSheet(style_disabled)
                
                # Feedback visual
                self.current_phase = f"Esperando estado (Actual: {status_code})"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")


    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)       