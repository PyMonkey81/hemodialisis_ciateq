# gui/therapy/alarms_screen.py
# Dedicated screen for active alarms + event/history log
# Stacked index: 5 ("Alarmas")

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame,
    QPushButton, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont

from core.variables_map import VARIABLES


class AlarmsScreen(QWidget):
    """
    Screen displaying currently active alarms and full event history.
    Connects to AlarmSystem signals for real-time updates.
    """

    def __init__(self, parent=None, values_dict=None, alarm_system=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI';")

        # References
        self.values = values_dict if values_dict is not None else {}
        self.alarm_system = alarm_system

        self.setFixedSize(1536, 726)

        # Active alarms cache: name → (value, severity_level, activation_time)
        self.active_alarms = {}

        self.setup_ui()

        # Connect signals and sync initial state
        if self.alarm_system:
            print("AlarmsScreen: alarm_system found. Known alarm count:",
                  len(getattr(self.alarm_system, 'display_names', [])))

            self.alarm_system.alarm_changed.connect(self.on_alarm_changed)
            self.alarm_system.new_event.connect(self.on_new_event)

            # Critical: Sync current alarm states on initialization
            self._sync_initial_state()
        else:
            print("Warning: alarm_system not available in AlarmsScreen")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)

        # Title
        title = QLabel("ALARMAS Y EVENTOS DEL SISTEMA")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #f87171;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #475569; max-height: 2px;")
        layout.addWidget(sep1)

        # Active Alarms Section
        lbl_active = QLabel("ALARMAS ACTIVAS")
        lbl_active.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #ef4444; 
            background: transparent;
            padding: 8px 0;
        """)
        layout.addWidget(lbl_active)

        self.active_alarms_display = QTextEdit()
        self.active_alarms_display.setReadOnly(True)
        self.active_alarms_display.setStyleSheet("""
            QTextEdit {
                background: #1e293b;
                color: #fef2f2;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 20px;
                border: 2px solid #7f1d1d;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        self.active_alarms_display.setMinimumHeight(220)
        layout.addWidget(self.active_alarms_display)

        # Acknowledge All Button
        btn_ack_all = QPushButton("RECONOCER TODAS")
        btn_ack_all.setFixedSize(320, 60)
        btn_ack_all.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                font-size: 22px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        btn_ack_all.clicked.connect(self.acknowledge_all_alarms)
        layout.addWidget(btn_ack_all, alignment=Qt.AlignRight)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #475569; max-height: 2px;")
        layout.addWidget(sep2)

        # Event History Section
        lbl_history = QLabel("HISTORIAL COMPLETO")
        lbl_history.setStyleSheet("""
            font-size: 26px; 
            font-weight: bold; 
            color: #94a3b8;
        """)
        layout.addWidget(lbl_history)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setStyleSheet("""
            QTextEdit {
                background: #0f172a;
                color: #cbd5e1;
                font-family: Consolas, monospace;
                font-size: 17px;
                border: none;
                padding: 8px;
            }
        """)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.history_display)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setMinimumHeight(280)
        layout.addWidget(scroll_area)

        # Initial message
        self._update_active_alarms_display()
        self.history_display.append(
            f'<span style="color:#64748b;">[Sistema iniciado — {QTime.currentTime().toString("hh:mm:ss")}]</span>'
        )

    def _sync_initial_state(self):
        """Read current alarm states from AlarmSystem and populate active_alarms."""
        if not all(hasattr(self.alarm_system, attr) for attr in 
                   ['display_names', 'previous_states', 'severity_levels']):
            print("AlarmsScreen: alarm_system missing expected attributes "
                  "(display_names, previous_states, severity_levels)")
            return

        current_time = QTime.currentTime().toString("hh:mm:ss")
        loaded_count = 0

        for i, name in enumerate(self.alarm_system.display_names):
            if i < len(self.alarm_system.previous_states) and self.alarm_system.previous_states[i]:
                level = (self.alarm_system.severity_levels[i] 
                         if i < len(self.alarm_system.severity_levels) else "info")
                value = None  # Could fetch from self.values if tag is mapped
                self.active_alarms[name] = (value, level, current_time)
                loaded_count += 1

        print(f"AlarmsScreen: initial sync → {loaded_count} active alarms loaded")
        self._update_active_alarms_display()

    def on_alarm_changed(self, idx, is_active, value, name, level, limits):
        current_time = QTime.currentTime().toString("hh:mm:ss")

        if is_active:
            self.active_alarms[name] = (value, level, current_time)
        else:
            self.active_alarms.pop(name, None)

        self._update_active_alarms_display()
        self._append_to_history(name, value, level, is_active, current_time)

    def on_new_event(self, event_msg, value, timestamp):
        self._append_to_history(event_msg, value, "info", True, timestamp)

    def _update_active_alarms_display(self):
        if not self.active_alarms:
            html = '<center><span style="color:#94a3b8; font-size:20px;">Ninguna alarma activa en este momento</span></center>'
        else:
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
            sorted_alarms = sorted(
                self.active_alarms.items(),
                key=lambda item: priority_map.get(item[1][1], 0),
                reverse=True
            )

            lines = []
            for name, (value, level, time_str) in sorted_alarms:
                color_map = {
                    "rojo": "#f87171",
                    "naranja": "#fb923c",
                    "amarillo": "#fbbf24",
                    "cian": "#22d3ee",
                    "info": "#94a3b8"
                }
                color = color_map.get(level, "#cbd5e1")

                value_str = f"  {value:.1f}" if value is not None else ""
                line = (
                    f'<span style="color:{color}; font-weight:bold; font-size:21px;">'
                    f'[{time_str}]  {name.upper()}{value_str}</span>'
                    f'<span style="color:#64748b; font-size:18px;">  — {level.upper()}</span>'
                )
                lines.append(line)

            html = "<br>".join(lines)

        self.active_alarms_display.setHtml(html)

    def _append_to_history(self, text, value, level, is_active, time_str):
        color_map = {
            "rojo": "#f87171",
            "naranja": "#fb923c",
            "amarillo": "#fbbf24",
            "cian": "#22d3ee",
            "info": "#94a3b8"
        }
        color = color_map.get(level, "#94a3b8")

        if level == "info":
            status = ""
            value_str = ""
        else:
            status = "ACTIVADA" if is_active else "DESACTIVADA"
            value_str = f" ({value:.1f})" if value is not None and value != 0 else ""

        line = (
            f'<span style="color:#64748b;">[{time_str}]</span> '
            f'<span style="color:{color}; font-weight:bold;">'
            f'{status} {text}{value_str}</span>'
        )

        self.history_display.append(line)
        self.history_display.verticalScrollBar().setValue(
            self.history_display.verticalScrollBar().maximum()
        )

    def acknowledge_all_alarms(self):
        if not self.active_alarms:
            QMessageBox.information(self, "Información", "No hay alarmas activas.")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Reconocer TODAS las alarmas activas?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.active_alarms.clear()
            self._update_active_alarms_display()
            current_time = QTime.currentTime().toString("hh:mm:ss")
            self._append_to_history(
                "Todas las alarmas reconocidas por el usuario",
                None, "info", True, current_time
            )
            QMessageBox.information(self, "Listo", "Alarmas reconocidas.")

    def update_values(self, values_dict):
        """Compatibility method called from main window."""
        self.values = values_dict
        # Not directly used here, but kept for interface consistency

    # Note: The write_setpoint method seems unrelated to alarms screen.
    #       If it's not used here, consider moving it to a more appropriate screen
    #       (e.g. therapy_config_screen or options_screen).
    #       For now, it's kept commented out or removed unless you confirm it's needed.