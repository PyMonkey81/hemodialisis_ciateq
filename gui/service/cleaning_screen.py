# gui/service/cleaning_screen.py
# Cleaning / Disinfection screen (stacked index 3)
# Controls chemical disinfection cycle with progress tracking and safety checks

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class CleaningScreen(QWidget):
    """
    Cleaning and disinfection screen.
    Manages the chemical disinfection cycle with progress bar,
    remaining time display, and conditional start button.
    """

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.values = values_dict if values_dict is not None else {}

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
            QPushButton:hover {
                background: #065f46;
            }
            QPushButton:pressed {
                background: #064e3b;
            }
            QPushButton:disabled {
                background: #334155;
                color: #64748b;
            }
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
        self._write_setpoint("treatmentModeSelection", 3.0)

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
        self.values = new_values

        # If cleaning is already in progress, do not interfere with button state
        if self.cleaning_in_progress:
            return

        # Get priming/cleaning status (assuming tag "primingProcessStatus")
        current_status = self.values.get("primingProcessStatus", 0.0)

        # Example ready state: 6 = infusion / ready for cleaning
        IS_READY_STATE = (int(current_status) == 6)

        if IS_READY_STATE:
            if not self.start_button.isEnabled():
                self.start_button.setEnabled(True)
                self.current_phase = "Sistema listo para limpieza"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
        else:
            if self.start_button.isEnabled():
                self.start_button.setEnabled(False)

                # Optional: friendly status names (for debug/UI)
                status_names = {
                    1: "INICIALIZANDO (1)",
                    2: "LLENADO TANQUE (2)",
                    3: "LLENADO LÍNEA (3)",
                    4: "LLENADO DE CÁMARA (4)",
                    5: "CALENTAMIENTO DIALIZANTE (5)",
                    6: "INFUSIÓN (6)",
                    7: "DIÁLISIS (7)",
                    12: "LISTO (HDUF_RDY)"
                }
                status_name = status_names.get(int(current_status), f"ESPERANDO (Estado {int(current_status)})")
                self.current_phase = status_name
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")

    def _write_setpoint(self, tag: str, value: float):
        """Safe setpoint write to controller."""
        try:
            print(f"[SETPOINT] Intentando escribir {tag} = {value}")

            target_group = target_id = -1
            found = False

            for group_key, vars_group in VARIABLES.items():
                if isinstance(vars_group, dict):
                    for var_id, info in vars_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found:
                    break

            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" → Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                        if self.parent_window.serial_comm.is_connected:
                            self.parent_window.serial_comm.write_double(target_group, target_id, value)
                        else:
                            print(f"[INFO] Serial no conectado. {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {value}")
                    else:
                        print(f"[INFO] No serial_comm disponible en parent. {tag}={value}")
                else:
                    print(f"[ADVERTENCIA] Variable '{tag}' no escribible (rw=False).")
            else:
                print(f"[ERROR] Tag '{tag}' no encontrado en variables_map.")

            self.setFocus()

        except Exception as e:
            print(f"[ERROR] Error al escribir setpoint {tag}: {e}")
