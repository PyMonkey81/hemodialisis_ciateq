

# gui/therapy/dialysis_screen.py
import logging
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque
from gui.components.ui_components import LabeledParameterWidget, LabeledTimeInput


# Imports opcionales con fallback para evitar crasheos si faltan archivos
try:
    from logic.calculos import calculo_ptm
except ImportError:
    def calculo_ptm(a, b, c, d): return 0.0

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

logger = logging.getLogger(__name__)

class SimpleValueDisplay(QWidget):
    """
    Widget reutilizable para mostrar un parámetro con etiqueta, valor y unidades.
    """
    def __init__(self, label_text: str, initial_value: str = "0.0", units: str = "", is_critical: bool = False):
        super().__init__()
        self.setFixedHeight(90)

        self.frame = QFrame()
        background_color = "#fffd96" if is_critical else "#ffffff"

        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {background_color};
                border: 2px solid #000000;
                border-radius: 10px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(2)

        tag_text = f"{label_text} ({units})" if units else label_text

        self.label_tag_units = QLabel(tag_text)
        self.label_tag_units.setAlignment(Qt.AlignCenter)
        self.label_tag_units.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 20px;")

        self.label_value = QLabel(initial_value)
        self.label_value.setAlignment(Qt.AlignCenter)
        # self.label_value.setStyleSheet("border: none; color ")
        # font_value = QFont("Arial", 36, QFont.Bold)
        # self.label_value.setFont(font_value)

        self.label_value.setStyleSheet("border: none; color: #0078d7; font-weight: bold; font-size: 36px;") 

        frame_layout.addWidget(self.label_tag_units)
        frame_layout.addWidget(self.label_value)

    def set_value(self, value):
        if isinstance(value, (int, float)):
            text = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
        else:
            text = str(value)
        self.label_value.setText(text)


class DialysisScreen(QWidget):
    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent  # Referencia a HemodialysisHMI
        self.current_values = values_dict if values_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1024, 600)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#0f172a"))
        self.setPalette(palette)

        # Historial para gráficas
        self.history_length = 600
        nan_array = [np.nan] * self.history_length
        self.venous_pressure_history = deque(nan_array, maxlen=self.history_length)
        self.arterial_pressure_history = deque(nan_array, maxlen=self.history_length)
        self.time_axis = np.arange(-self.history_length + 1, 1, dtype=np.float32)

 #==============================REVISAR ESTA PARTE DEL TIMER============================       
        # Nuevos atributos para manejo de tiempo
        # self.therapy_start_time = None          # Timestamp de inicio (QDateTime o segundos)
        # self.total_therapy_seconds = 0          # Duración total programada en segundos
        # self.is_treatment_running = False

        # # Timer para actualizar tiempo cada segundo
        # self.time_timer = QTimer(self)
        # self.time_timer.timeout.connect(self._update_elapsed_and_remaining_time)
        # self.time_timer.start(1000)  # cada 1 segundo


        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)

        # ── Área Gráfica ──
        graphics_container = QWidget()
        graphics_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        graphics_layout = QGridLayout(graphics_container)
        graphics_layout.setSpacing(15)
        graphics_layout.setContentsMargins(5, 5, 5, 5)

        tick_font = QFont()
        tick_font.setPixelSize(12)

        self.pressure_plot = pg.PlotWidget()
        self.pressure_plot.setBackground("#e0e0e0")
        self.pressure_plot.setTitle('<span style="font-size: 11pt; color: black;">Presión Ven vs. Art</span>')
        self.pressure_plot.setLabel('left', '<span style="font-size: 9pt; color: black;">Presión (mmHg)</span>')
        self.pressure_plot.setLabel('bottom', '<span style="font-size: 9pt; color: #000000;">Tiempo (s)</span>')
        self.pressure_plot.addLegend()

        self.curve_venous = self.pressure_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Presión Venosa")
        self.curve_arterial = self.pressure_plot.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Presión Arterial")

        self.pressure_plot.getAxis('bottom').setStyle(tickFont=tick_font)
        self.pressure_plot.getAxis('left').setStyle(tickFont=tick_font)

        graphics_layout.addWidget(self.pressure_plot, 0, 0, 1, 1)
        layout.addWidget(graphics_container, 0, 0, 4, 1)

        # ── Botones de Control ──
        buttons_container = QFrame()
        buttons_container.setMinimumWidth(400)
        buttons_container.setStyleSheet("background: #FCFCFC; border-radius: 10px; border: 4px solid #1e293b;")

        buttons_layout = QGridLayout(buttons_container)
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(20, 20, 20, 20)

        self.action_buttons = {} # guardar referencias de botones

        button_config = [
            ("INICIAR", "#39ec21", self.parent_window.start_treatment),
            ("DETENER", "#DD2911", self.parent_window.stop_treatment),
            ("MENÚ TERAPIA", "#0f172a", self.show_therapy_config),
            ("MENÚ PACIENTE", "#0f172a", self.show_patient_config),
            ("INICIAR CEBADO", "#0f172a", self.parent_window.start_priming),
            ("DETENER CEBADO", "#0f172a", self.parent_window.stop_priming),
        ]

        for i, (text, color, callback) in enumerate(button_config):
            btn = QPushButton(text)
            btn.setFixedHeight(70)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                               font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(callback)
            self.action_buttons[text] = btn # === Guardar el botón en el diccionario ===
            row = i // 2
            col = i % 2
            buttons_layout.addWidget(btn, row, col)            
        # Deshabilitar botones por defecto al iniciar
        # self.update_buttons_state(0) # Estado 0 o inicial
        layout.addWidget(buttons_container, 4, 0, 4, 1)

        # ── Displays de Parámetros ──
        self.arterial_pressure_display = SimpleValueDisplay("Art", "0", "mmHg", is_critical=True)
        self.venous_pressure_display   = SimpleValueDisplay("Ven", "0", "mmHg", is_critical=True)
        self.ptm_display               = SimpleValueDisplay("PTM", "0", "mmHg", is_critical=True)
        self.remaining_time_display    = SimpleValueDisplay("T. Restante", "00:00", "h:min") # y aqui el tiempo restante 
        self.elapsed_time_display      = SimpleValueDisplay("Tiempo UF", "00:00", "h:min")  # aqui actualizar el tiempo
        self.uf_target_display         = SimpleValueDisplay("UF Objetivo", "0.00", "L")
        self.uf_total_display          = SimpleValueDisplay("UF Total", "0.00", "L")
        self.uf_rate_display           = SimpleValueDisplay("Tasa UF", "0", "mL/h")
        self.conductivity_display      = SimpleValueDisplay("Cond.", "0.0", "mS/cm")
        self.blood_flow_display        = SimpleValueDisplay("Qb", "0", "mL/min")
        self.dialysate_flow_display    = SimpleValueDisplay("Qd", "0", "mL/min")
        self.temperature_display       = SimpleValueDisplay("Temp.", "0.0", "°C")
        self.sodium_display            = SimpleValueDisplay("Na+", "0.0", "mmol/L")
        self.ktv_display               = SimpleValueDisplay("Kt/V", "0.00", "")

        

        # Grid placement
        layout.addWidget(self.arterial_pressure_display, 0, 1)
        layout.addWidget(self.remaining_time_display,    0, 2)
        layout.addWidget(self.venous_pressure_display,   1, 1)
        layout.addWidget(self.elapsed_time_display,      1, 2)
        layout.addWidget(self.ptm_display,               2, 1)
        layout.addWidget(self.uf_target_display,         2, 2)
        layout.addWidget(self.conductivity_display,      3, 1)
        layout.addWidget(self.uf_total_display,          3, 2)
        layout.addWidget(self.blood_flow_display,        4, 1)
        layout.addWidget(self.uf_rate_display,           4, 2)
        layout.addWidget(self.dialysate_flow_display,    5, 1)
        layout.addWidget(self.sodium_display,            5, 2)
        layout.addWidget(self.temperature_display,       6, 1)
        layout.addWidget(self.ktv_display,               6, 2)
        layout.addWidget(QWidget(), 7, 1)

    def update_values(self, new_values: dict):
        """Update all displayed values."""
        self.current_values = new_values

        # Actualizar gráfico
        venous_pressure = self.current_values.get("bloodVenousPressureData", 0.0)
        arterial_pressure = self.current_values.get("bloodArteryPressureData", 0.0)
        self.venous_pressure_history.append(venous_pressure)
        self.arterial_pressure_history.append(arterial_pressure)
        self.curve_venous.setData(self.time_axis, list(self.venous_pressure_history))
        self.curve_arterial.setData(self.time_axis, list(self.arterial_pressure_history))
        self.pressure_plot.setXRange(-self.history_length + 1, 0)

        
        # Calculo PTM
        pd_in = self.current_values.get("dialyPresIFProcessData", 0.0)
        pd_out = self.current_values.get("dialyPresOFProcessData", 0.0)
        try:
            ptm_calculated = calculo_ptm(pd_in, pd_out, arterial_pressure, venous_pressure)
        except Exception:
            ptm_calculated = 0.0
        self.current_values["CALC_PTM"] = ptm_calculated


        # Mapeo de variables
        parameter_mapping = {
            "bloodArteryPressureData":   self.arterial_pressure_display,
            "bloodVenousPressureData":   self.venous_pressure_display,
            "CALC_PTM":                  self.ptm_display,
            "dialyCondVariableData":     self.conductivity_display,
            "bloodSpeedVariableData":    self.blood_flow_display,
            "dialyFlowControlOutput":    self.dialysate_flow_display,
            "dialyTempVariableData":    self.temperature_display,
            "ultraFilterPumpSpeed":      self.uf_rate_display,
            "UF Total":                  self.uf_total_display,
            "uf_goal_liters":            self.uf_target_display,            
        }


        for tag, widget in parameter_mapping.items():
            value = self.current_values.get(tag, 0.0)
            widget.set_value(value)
        
        # Kt/V placeholder (implement when CalculadoraKtV is ready)
        ktv_value = 0.00 # Aquí iría tu cálculo real para Kt/V
        self.ktv_display.set_value(ktv_value)


    # ── Treatment Control Methods ────────────────────────────────────────────────
    # def start_treatment(self):
    #     """Initiate dialysis treatment."""
    #     # Ejemplo: envía comandos de selección de modo (ajusta valores según protocolo)
    #     self._write_setpoint("treatmentModeSelection", 0.0) # Hemodiálisis
    #     # self._write_setpoint("treatmentModeSelection", 1.0) # Hemodiafiltración
    #     # self._write_setpoint("treatmentModeSelection", 2.0) # Ultrafiltración sola

    def pause_treatment(self):
        """Pause the ongoing treatment session."""
        pass  # Implement pause logic here

    # def stop_treatment(self):
    #     """Stop the treatment session completely."""
    #     pass  # Implement stop logic here

    def start_priming(self):
        """Start priming / rinsing phase."""
        "dialyStartDialysisButt"
        
        pass  # Implement priming logic here

    # def update_buttons_state(self, status_code: int):
    #     """
    #     Habi    lita o deshabilita botones INICIAR/DETENER basado en el estado de la máquina.
    #     - status_code 12: Listo para iniciar → habilitar INICIAR si temperatura OK
    #     - status_code 13: Tratamiento iniciado → habilitar DETENER
    #     - Otros estados: ambos deshabilitados (por seguridad)
    #     """
    #     if not hasattr(self, 'action_buttons'):
    #         return

    #     btn_iniciar = self.action_buttons.get("INICIAR")
    #     btn_detener = self.action_buttons.get("DETENER")

    #     if not btn_iniciar or not btn_detener:
    #         return  # Evitar errores si los botones no existen

    #     # Estilos base
    #     style_enabled = """
    #         QPushButton { background: #0f172a; color: #ffffff; font-weight: bold; font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }
    #         QPushButton:pressed { background: #334155; }
    #     """
    #     style_disabled = """
    #         QPushButton {
    #             background: #334155;
    #             color: #94a3b8;
    #             font-weight: bold;
    #             font-size: 16px;
    #             border-radius: 15px;
    #             border: 3px solid #1e293b;
    #         }
    #     """
# En gui/therapy/dialysis_screen.py

    # BORRA O COMENTA TU MÉTODO update_buttons_state ACTUAL
    # def update_buttons_state(self, status_code: int): ...
    
    
    def set_start_stop_buttons_state(self, enable_start: bool, enable_stop: bool):
        """
        Recibe instrucciones directas del Main para habilitar/deshabilitar.
        """
        btn_iniciar = self.action_buttons.get("INICIAR")
        btn_detener = self.action_buttons.get("DETENER")

        # Estilos (puedes mantenerlos aquí o pasarlos como constantes)
        style_enabled = """
            QPushButton { background: #39ec21; color: #ffffff; font-weight: bold; font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }
            QPushButton:pressed { background: #334155; }
        """
        style_disabled = """
            QPushButton { background: #334155; color: #94a3b8; font-weight: bold; font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }
        """
        style_stop_enabled = """
             QPushButton { background: #DD2911; color: #ffffff; font-weight: bold; font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }
             QPushButton:pressed { background: #334155; }
        """

        if btn_iniciar:
            btn_iniciar.setEnabled(enable_start)
            btn_iniciar.setStyleSheet(style_enabled if enable_start else style_disabled)
        
        if btn_detener:
            btn_detener.setEnabled(enable_stop)
            # Nota: Al botón detener le ponemos rojo si está activo
            btn_detener.setStyleSheet(style_stop_enabled if enable_stop else style_disabled)


    def show_therapy_config(self):
        """Navigate to therapy configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_therapy_config_screen"):
            self.parent_window.show_therapy_config_screen()

    def show_patient_config(self):
        """Navigate to patient configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_patient_config_screen"):
            self.parent_window.show_patient_config_screen()

    def _write_setpoint(self, tag: str, value: float):
        """Send a setpoint value to the controller via serial."""
        try:
            print(f"[SETPOINT] Writing {tag} = {value}")

            target_group = -1
            target_id = -1
            found = False

            for group_key, vars_in_group in VARIABLES.items():
                if isinstance(vars_in_group, dict):
                    for var_id, info in vars_in_group.items():
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
                    # Usa el nuevo nombre de la instancia serial
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm') and self.parent_window.serial_comm:
                        self.parent_window.serial_comm.write_double(target_group, target_id, value)
                        self.parent_window.current_values[tag] = value 
                    else:
                        print(f"[INFO] Serial not connected or 'serial_comm' attribute missing in parent. Cannot write {tag}.")
                else:
                    print(f"[ADVERTENCIA] Variable '{tag}' no escribible (rw=False).")
            else:
                print(f"[ERROR] Tag '{tag}' no encontrado en variables_map.")

            self.setFocus() # Esto no tiene efecto en un QWidget. Podrías quitarlo.

        except Exception as e:
            print(f"[ERROR] Failed to write setpoint {tag}: {e}")

    def _write_boolean_command(self, tag: str, state: bool):
        logger.info(f"Command: {tag} → {state}")
        address = -1
        for group_key, vars_group in VARIABLES.items():
            if isinstance(vars_group, dict):
                for var_id, info in vars_group.items():
                    if info.get("tag") == tag:
                        address = var_id
                        break
            if address != -1:
                break

        if address != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                if self.parent_window.serial_comm.is_connected:
                    self.parent_window.serial_comm.write_boolean(address, state)
                    
                    logger.info(f"Boolean command sent: Addr {address} = {state}")
                else:
                    logger.warning("Serial not connected")
                    QMessageBox.warning(self, "Error", "Serial no conectado")
            else:
                logger.warning("Serial communication not available")
        else:
            logger.error(f"Tag '{tag}' not found in VARIABLES map")

    def _update_label_display(self, label, value, precision=1):
        if isinstance(label, LabeledParameterWidget):
            label.set_value(value)
        elif hasattr(label, 'setText'):
            label.setText(f"{value:.{precision}f}")

    def _update_time_display(self, time_widget, tag_hours: str, tag_minutes: str, timer_id: str):
        if not tag_hours and not tag_minutes:
            return
        
        current_ms = QDateTime.currentMSecsSinceEpoch()
        hold_hours = self.write_hold_off.get(tag_hours, 0) if tag_hours else 0
        hold_minutes = self.write_hold_off.get(tag_minutes, 0) if tag_minutes else 0

        if current_ms < hold_hours or current_ms < hold_minutes:
            return

        hours = int(self.current_values.get(tag_hours, 0)) if tag_hours else 0
        minutes = int(self.current_values.get(tag_minutes, 0)) if tag_minutes else 0

        if isinstance(time_widget, LabeledTimeInput):
            time_widget.set_time_value(hours, minutes)
        elif hasattr(time_widget, 'setText'):
            if not time_widget.hasFocus():
                time_widget.setText(f"{hours:02d}:{minutes:02d}")

        if timer_id and timer_id in self.local_timer_states:
            if not self.local_timer_states[timer_id]["active"]:
                total_ms = (hours * 3600 + minutes * 60) * 1000
                self.local_timer_states[timer_id]["duration_ms"] = total_ms


    def _update_elapsed_and_remaining_time(self):
        """Actualiza displays de tiempo transcurrido y restante"""
        if not self.is_treatment_running or self.therapy_start_time is None:
            self.elapsed_time_display.set_value("00:00")
            self.remaining_time_display.set_value("00:00")
            return

        # Tiempo transcurrido
        elapsed = self.therapy_start_time.secsTo(QDateTime.currentDateTime())
        elapsed_hours = elapsed // 3600
        elapsed_min = (elapsed % 3600) // 60
        elapsed_str = f"{elapsed_hours:02d}:{elapsed_min:02d}"
        self.elapsed_time_display.set_value(elapsed_str)

        # Tiempo restante
        remaining_seconds = max(0, self.total_therapy_seconds - elapsed)
        rem_hours = remaining_seconds // 3600
        rem_min = (remaining_seconds % 3600) // 60
        remaining_str = f"{rem_hours:02d}:{rem_min:02d}"
        self.remaining_time_display.set_value(remaining_str)

        # Opcional: detener tratamiento automáticamente al llegar a 0
        if remaining_seconds <= 0 and self.is_treatment_running:
            self.stop_treatment()
            QMessageBox.information(self, "Finalizado", "Tiempo de terapia completado.")
    
    def _format_ms_to_hh_mm(self, ms: int) -> str:
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    

