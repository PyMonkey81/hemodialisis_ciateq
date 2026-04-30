# gui/therapy/dialysis_screen.py

"""
Pantalla principal de monitorización y control de la terapia de diálisis.

Este módulo define la clase `DialysisScreen`, que sirve como el panel de control central
durante una sesión de tratamiento. Proporciona una interfaz rica en datos para que el
personal clínico supervise el progreso de la terapia y tome acciones inmediatas.

Componentes Principales:
------------------------
1. **Visualización Gráfica (PyQtGraph):**
   - Muestra gráficas en tiempo real de la Presión Venosa y Arterial.
   - Mantiene un historial de datos (`deque`) para visualizar tendencias.

2. **Panel de Control (Botones):**
   - Gestión del ciclo de vida del tratamiento: Iniciar, Pausar, Detener.
   - Gestión del ciclo de cebado (Priming): Iniciar/Detener.
   - Acceso rápido a submenús: Configuración de Terapia, Paciente.
   - Acciones directas: Aplicación de bolo de heparina.

3. **Monitores de Parámetros (SimpleValueDisplay):**
   - Visualización numérica de variables críticas (Presiones, Conductividad, Flujos, Temperatura).
   - Cálculo y visualización de métricas derivadas como PTM (Presión Transmembrana) y Kt/V.
   - Temporizadores de tiempo transcurrido y restante de la terapia.

4. **Lógica de Estado:**
   - Métodos para habilitar/deshabilitar controles según el estado de la máquina (recibido desde `Main`).
   - Actualización periódica de valores (`update_values`) provenientes del controlador central.

Dependencias:
-------------
- `PySide6`: Elementos de UI.
- `pyqtgraph`: Graficación de alto rendimiento.
- `gui.components.ui_components`: Widgets personalizados reutilizables.
- `logic.calculos`: Fórmulas médicas (PTM).
"""

import logging
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDateTime, QTimer, Signal
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque
from gui.components.ui_components import LabeledParameterWidget, LabeledTimeInput



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
    Widget compuesto para mostrar un parámetro clínico de forma estandarizada.
    
    Combina una etiqueta (nombre del parámetro y unidad) y un valor numérico grande.
    Permite cambiar el color de fondo para resaltar parámetros críticos.
    
    Args:
        label_text (str): Nombre del parámetro (ej. "Presión Art.").
        initial_value (str): Valor inicial a mostrar.
        units (str): Unidades de medida (ej. "mmHg").
        is_critical (bool): Si es True, el fondo será amarillo claro para destacar; 
                            si es False, será blanco.
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
    
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent  # Referencia a HemodialysisHMI
        self.current_values = values_dict if values_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        

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
        self.pressure_plot.setBackground("#E0E0E0")
        self.pressure_plot.setTitle('<span style="font-size: 20pt; color: #020C4B;">Presión Ven vs. Art</span>')
        self.pressure_plot.setLabel('left', '<span style="font-size: 16pt; color: #020c4b;">Presión (mmHg)</span>')
        self.pressure_plot.setLabel('bottom', '<span style="font-size: 12pt; color: #000000;">Tiempo (s)</span>')
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
            ("PAUSAR", "#FFC400", self.parent_window.pause_treatment),
            ("DETENER", "#DD2911", self.parent_window.stop_treatment),
            ("MENÚ TERAPIA", "#0f172a", self.show_therapy_config),
            ("MENÚ PACIENTE", "#0f172a", self.show_patient_config),
            ("APLICAR BOLO", "#0f172a", self.bolus_apply_dosage),
            ("INICIAR CEBADO", "#0f172a", self.parent_window.start_priming),
            ("DETENER CEBADO", "#0f172a", self.parent_window.stop_priming), 
            ("Kt/V", "#0f172a", self.parent_window.ktv_meassurement),           
        ]

        for i, (text, color, callback) in enumerate(button_config):
            btn = QPushButton(text)
            btn.setFixedHeight(70)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                               font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(callback)
            self.action_buttons[text] = btn # === Guardar el botón en el diccionario ===
            row = i // 3
            col = i % 3
            buttons_layout.addWidget(btn, row, col)            
     
        layout.addWidget(buttons_container, 4, 0, 4, 1)

        # ── Displays de Parámetros ──
        self.arterial_pressure_display = SimpleValueDisplay("Art", "0", "mmHg", is_critical=True)
        self.venous_pressure_display   = SimpleValueDisplay("Ven", "0", "mmHg", is_critical=True)
        self.ptm_display               = SimpleValueDisplay("PTM", "0", "mmHg", is_critical=True)
        self.remaining_time_display    = SimpleValueDisplay("T. Restante", "00:00", "h:min") 
        self.elapsed_time_display      = SimpleValueDisplay("T. Terapia", "00:00", "h:min")  
        self.uf_target_display         = SimpleValueDisplay("UF Objetivo", "0.00", "L")
        self.uf_total_display          = SimpleValueDisplay("UF Total", "0.00", "L")
        self.uf_rate_display           = SimpleValueDisplay("Tasa UF", "0", "mL/h")
        self.conductivity_display      = SimpleValueDisplay("Cond.", "0.0", "mS/cm")
        self.blood_flow_display        = SimpleValueDisplay("Qb", "0", "mL/min")
        self.dialysate_flow_display    = SimpleValueDisplay("Qd", "0", "mL/min")
        self.temperature_display       = SimpleValueDisplay("Temp.", "0.0", "°C")
        self.bolus_display             = SimpleValueDisplay("Bolo", "0.0", "ml")
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
        layout.addWidget(self.bolus_display,             5, 2)
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
            "bloodFlowVariableData":     self.blood_flow_display,
            "dialyFlowControlOutput":    self.dialysate_flow_display,  #verificar la salida 
            "dialyTempIFProcessData":    self.temperature_display,  #Temperatura a la entrada del filtro - Cambio comentado 
            "ultraFilterPumpSpeed":      self.uf_rate_display,
            "UF Total":                  self.uf_total_display,
            "uf_goal_liters":            self.uf_target_display,
            "heparineBolusQuantity":     self.bolus_display,   
            "ktv_acumulado":             self.ktv_display,        
        }


        for tag, widget in parameter_mapping.items():
            value = self.current_values.get(tag, 0.0)
            widget.set_value(value)
        
        # # Kt/V placeholder (implement when CalculadoraKtV is ready)
        # ktv_value = 0.00 # Aquí iría tu cálculo real para Kt/V
        # self.ktv_display.set_value(ktv_value)


    def bolus_apply_dosage(self):
        try:
            self.on_user_boolean_command("heparinApplyBolusDose",True)
            self.on_user_boolean_command("heparinApplyBolusDose",False)
        except Exception as e:
            pass 

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)
    
    def set_start_stop_buttons_state(self, enable_start: bool, enable_stop: bool, enable_pause: bool):
        """
        Recibe instrucciones directas del Main para habilitar/deshabilitar.
        """
        btn_iniciar = self.action_buttons.get("INICIAR")
        btn_detener = self.action_buttons.get("DETENER")
        btn_pausar = self.action_buttons.get("PAUSAR") # se agrego este boton a la logica de activación/desactivación


        style_enabled = """
            QPushButton { background: #39ec21; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
            QPushButton:pressed { background: #334155; }
        """
        style_disabled = """
            QPushButton { background: #334155; color: #94a3b8; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
        """
        style_stop_enabled = """
             QPushButton { background: #DD2911; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
             QPushButton:pressed { background: #334155; }
        """
        style_pause_enabled = """
             QPushButton { background: #FFC400; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
             QPushButton:pressed { background: #334155; }
        """

        if btn_iniciar:
            btn_iniciar.setEnabled(enable_start)
            btn_iniciar.setStyleSheet(style_enabled if enable_start else style_disabled)
        
        if btn_detener:
            btn_detener.setEnabled(enable_stop)            
            btn_detener.setStyleSheet(style_stop_enabled if enable_stop else style_disabled)
        
        if btn_pausar:
            btn_pausar.setEnabled(enable_pause)
            btn_pausar.setStyleSheet(style_pause_enabled if enable_pause else style_disabled)        


    def show_therapy_config(self):
        """Navigate to therapy configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_therapy_config_screen"):
            self.parent_window.show_therapy_config_screen()

    def show_patient_config(self):
        """Navigate to patient configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_patient_config_screen"):
            self.parent_window.show_patient_config_screen()

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

        if remaining_seconds <= 0 and self.is_treatment_running:
            self.stop_treatment()

    
    def _format_ms_to_hh_mm(self, ms: int) -> str:
        total_seconds = max(0, ms // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"


    def set_priming_buttons_state(self, enable_start_priming: bool, enable_stop_priming: bool):
        """
        Recibe instrucciones directas del Main para habilitar/deshabilitar
        los botones de 'INICIAR CEBADO' y 'DETENER CEBADO'.
        """
        btn_start_priming = self.action_buttons.get("INICIAR CEBADO")
        btn_stop_priming = self.action_buttons.get("DETENER CEBADO")

        # Estilos
        style_priming_enabled = """
            QPushButton { background: #0f172a; color: #ffffff; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
            QPushButton:pressed { background: #334155; }
        """
        style_priming_disabled = """
            QPushButton { background: #334155; color: #94a3b8; font-weight: bold; font-size: 30px; border-radius: 15px; border: 3px solid #1e293b; }
        """

        if btn_start_priming:
            btn_start_priming.setEnabled(enable_start_priming)
            btn_start_priming.setStyleSheet(style_priming_enabled if enable_start_priming else style_priming_disabled)
        
        if btn_stop_priming:
            btn_stop_priming.setEnabled(enable_stop_priming)
            btn_stop_priming.setStyleSheet(style_priming_enabled if enable_stop_priming else style_priming_disabled)
    
    



