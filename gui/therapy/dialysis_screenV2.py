

# gui/therapy/dialysis_screenV2.py

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


from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPainterPath
import pyqtgraph as pg
import numpy as np
from collections import deque
from gui.components.ui_components import LabeledParameterWidget, LabeledTimeInput
from core.state_manager import TreatmentPhase
import logging
logger = logging.getLogger(__name__)



try:
    from logic.calculos import calculo_ptm
except ImportError:
    def calculo_ptm(a, b, c, d): return 0.0

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class PressureWaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_points = 300
        self.arterial_history = deque([-120.0] * self.max_points, maxlen=self.max_points)
        self.venous_history = deque([110.0] * self.max_points, maxlen=self.max_points)
        
        # Colores idénticos al primer código
        self.bg_color = QColor("#fcfcfc")    # Fondo claro para resaltar la rejilla
        self.grid_color = QColor("#64748b")  # Rejilla
        self.art_color = QColor("#0059ff")   # Cyan brillante (Arterial)
        self.ven_color = QColor("#ef4444")   # Rojo brillante (Venosa)
        self.panel_bg = QColor("#2d3e58")    # Fondo del panel de valores
        
    def add_values(self, arterial, venous):
        self.arterial_history.append(arterial)
        self.venous_history.append(venous)
        self.update()

    def paintEvent(self, event):
        if self.width() < 100 or self.height() < 100:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            width = self.width()
            height = self.height()
            graph_width = max(1, width - 85)

            # 1. Dibujar fondo total
            painter.fillRect(0, 0, width, height, self.bg_color)

            # 2. Dibujar rejilla (Grid)
            grid_pen = QPen(self.grid_color, 1, Qt.DashLine)
            painter.setPen(grid_pen)

            def to_y(val):
                # Mapeo de presión [-300, 300] mmHg a coordenadas del widget
                val_clamped = max(-300.0, min(300.0, val))
                percentage = (val_clamped + 300.0) / 600.0
                return int(height - 15 - percentage * (height - 30))

            # Líneas de presión de referencia
            for val in [-200, -100, 0, 100, 200]:
                y_pos = to_y(val)
                painter.drawLine(0, y_pos, width, y_pos)
                painter.setPen(QPen(QColor("#334155"), 1))
                painter.drawText(8, y_pos - 4, f"{val} mmHg")
                painter.setPen(grid_pen)

            for step in range(1, 6):
                x_pos = int((step / 6) * graph_width)
                painter.drawLine(x_pos, 12, x_pos, height - 12)

            # 3. Dibujar las trayectorias de las ondas
            art_path = QPainterPath()
            if len(self.arterial_history) > 1:
                art_path.moveTo(0, to_y(self.arterial_history[0]))
                for i, val in enumerate(self.arterial_history):
                    x = int((i / (self.max_points - 1)) * graph_width)
                    art_path.lineTo(x, to_y(val))
            painter.setPen(QPen(self.art_color, 2))
            painter.drawPath(art_path)

            ven_path = QPainterPath()
            if len(self.venous_history) > 1:
                ven_path.moveTo(0, to_y(self.venous_history[0]))
                for i, val in enumerate(self.venous_history):
                    x = int((i / (self.max_points - 1)) * graph_width)
                    ven_path.lineTo(x, to_y(val))
            painter.setPen(QPen(self.ven_color, 2))
            painter.drawPath(ven_path)

            # 4. Panel de leyendas derecho
            right_panel_x = width - 160

            curr_art = self.arterial_history[-1]
            painter.setFont(QFont("Consolas", 16, QFont.Bold))
            painter.setPen(QPen(self.art_color))
            painter.drawText(right_panel_x + 5, 35, "ART (mmHg)")
            painter.drawText(right_panel_x + 5, 55, f"{int(curr_art):+4d}")

            curr_ven = self.venous_history[-1]
            painter.setPen(QPen(self.ven_color))
            painter.drawText(right_panel_x + 5, height // 2 + 45, "VEN (mmHg)")
            painter.drawText(right_panel_x + 5, height // 2 + 65, f"{int(curr_ven):+4d}")
        finally:
            painter.end()

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
        self.setFixedHeight(100)

        self.frame = QFrame()
        background_color = "#fff1b8" if is_critical else "#f8fafc"

        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: {background_color};
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.frame)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(6)

        tag_text = f"{label_text} ({units})" if units else label_text

        self.label_tag_units = QLabel(tag_text)
        self.label_tag_units.setAlignment(Qt.AlignCenter)
        self.label_tag_units.setStyleSheet("border: none; color: #334155; font-weight: 600; font-size: 18px;")

        self.label_value = QLabel(initial_value)
        self.label_value.setAlignment(Qt.AlignCenter)
        self.label_value.setStyleSheet("border: none; color: #0078d7; font-weight: bold; font-size: 38px;") 

        frame_layout.addWidget(self.label_tag_units)
        frame_layout.addWidget(self.label_value)

    def set_value(self, value):
        if isinstance(value, (int, float)):
            text = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
        else:
            text = str(value)
        self.label_value.setText(text)

    def set_time_value(self, time_str: str):
        """Método específico para mostrar tiempo en formato HH:MM:SS"""
        self.label_value.setText(time_str)


class DialysisScreen(QWidget):
    
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent  # Referencia a HemodialysisHMI
        self.current_values = values_dict if values_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#edf3f9"))
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
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)

        # Estructura principal:
        # Fila 0: cards (ocupan todo el ancho)
        # Fila 1: izquierda botones, derecha gráfica
        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)


# panel de parametros 4 columna dos renglones o cards 
        grid_params = QGridLayout()
        grid_params.setSpacing(14)
        grid_params.setRowStretch(0, 1)
        for column in range(4):
            grid_params.setColumnStretch(column, 1)

        #  circuito de sangre 
        blood_card = QFrame()
        blood_card.setObjectName("card")
        blood_card.setMinimumHeight(300)
        blood_layout = QVBoxLayout(blood_card)
        blood_layout.setContentsMargins(16, 16, 16, 16)
        blood_layout.setSpacing(14)

        blood_title = QLabel("CIRCUITO DE SANGRE")
        blood_title.setObjectName("card_title")
        blood_layout.addWidget(blood_title)

        #flujo de sangre (BFR) control 
        bfr_layout = QHBoxLayout()
        bfr_layout.setSpacing(8)
        bfr_v = QVBoxLayout()
        bfr_v.setSpacing(6)
        bfr_v.addWidget(QLabel("FLUJO DE SANGRE (BFR)"))
        bfr_value_row = QHBoxLayout()
        bfr_value_row.setSpacing(6)
        self.bfr_value = QLabel("0")
        self.bfr_value.setObjectName("val_large")
        bfr_unit = QLabel("mL/min")
        bfr_unit.setStyleSheet("font-size: 26px; color: #475569; font-weight: 600;")
        bfr_value_row.addWidget(self.bfr_value)
        bfr_value_row.addWidget(bfr_unit)
        bfr_value_row.addStretch()
        bfr_v.addLayout(bfr_value_row)
        bfr_layout.addLayout(bfr_v)
        bfr_layout.addStretch()
        blood_layout.addLayout(bfr_layout)

        # Presion arterial 
        art_p_layout = QHBoxLayout()
        art_p_label = QLabel("ART:")
        art_p_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        art_p_layout.addWidget(art_p_label)
        self.art_p_value = QLabel("-120 mmHg")
        self.art_p_value.setStyleSheet("color: #0078d7; font-weight: bold; font-family: monospace; font-size: 28px;")
        art_p_layout.addStretch()
        art_p_layout.addWidget(self.art_p_value)
        blood_layout.addLayout(art_p_layout)

        #presion venosa
        ven_p_layout = QHBoxLayout()
        ven_p_label = QLabel("VEN:")
        ven_p_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        ven_p_layout.addWidget(ven_p_label)
        self.ven_p_value = QLabel("-80 mmHg")
        self.ven_p_value.setStyleSheet("color: #dc2626; font-weight: bold; font-family: monospace; font-size: 28px;")
        ven_p_layout.addStretch()
        ven_p_layout.addWidget(self.ven_p_value)
        blood_layout.addLayout(ven_p_layout)

        # Detector de burbujas / aire (LED Indicator)
        air_layout = QHBoxLayout()        
        self.air_indicator = QLabel("DETECTOR DE AIRE")
        self.air_indicator.setAlignment(Qt.AlignCenter)
        self.air_indicator.setFixedHeight(42)
        self.air_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.air_indicator.setStyleSheet("background-color: #86efac; color: #FFFFFF; font-weight: bold; border-radius: 8px; font-size: 28px;")
        # air_layout.addStretch()
        air_layout.addWidget(self.air_indicator)
        blood_layout.addLayout(air_layout)

        grid_params.addWidget(blood_card, 0, 0)

        # Card de circuito de dializado
        dialysate_card = QFrame()
        dialysate_card.setObjectName("card")
        dialysate_card.setMinimumHeight(300)
        dialysate_layout = QVBoxLayout(dialysate_card)
        dialysate_layout.setContentsMargins(16, 16, 16, 16)
        dialysate_layout.setSpacing(14)

        dialysate_title = QLabel("CIRCUITO DIALIZADOR")
        dialysate_title.setObjectName("card_title")
        dialysate_layout.addWidget(dialysate_title)

        # temperatura del dializado
        temp_layout = QHBoxLayout()
        temp_v = QVBoxLayout()
        temp_v.addWidget(QLabel("TEMPERATURA DIALIZADO"))
        temp_value_row = QHBoxLayout()
        temp_value_row.setSpacing(6)
        self.temp_value = QLabel("0.0")
        self.temp_value.setObjectName("val_large_green")
        temp_unit = QLabel("°C")
        temp_unit.setStyleSheet("font-size: 22px; color: #475569; font-weight: 600;")
        temp_value_row.addWidget(self.temp_value)
        temp_value_row.addWidget(temp_unit)
        temp_value_row.addStretch()
        temp_v.addLayout(temp_value_row)
        temp_layout.addLayout(temp_v)
        dialysate_layout.addLayout(temp_layout)


        # Conductividad del Dializado
        cond_layout = QHBoxLayout()
        cond_label = QLabel("Conductividad:")
        cond_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        cond_layout.addWidget(cond_label)
        self.cond_val = QLabel("14.1 mS/cm")
        self.cond_val.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        cond_layout.addStretch()
        cond_layout.addWidget(self.cond_val)
        dialysate_layout.addLayout(cond_layout)

        # Flujo de Dializado (DFR)
        dfr_layout = QHBoxLayout()
        dfr_label = QLabel("Flujo Dializado:")
        dfr_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        dfr_layout.addWidget(dfr_label)
        self.dfr_val_label = QLabel("500 mL/min")
        self.dfr_val_label.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        dfr_layout.addStretch()
        dfr_layout.addWidget(self.dfr_val_label)
        dialysate_layout.addLayout(dfr_layout)

        # Presión Transmembrana (TMP)
        tmp_layout = QHBoxLayout()
        tmp_label = QLabel("PTM:")
        tmp_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        tmp_layout.addWidget(tmp_label)
        self.tmp_val = QLabel("85 mmHg")
        self.tmp_val.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        tmp_layout.addStretch()
        tmp_layout.addWidget(self.tmp_val)
        dialysate_layout.addLayout(tmp_layout)

        grid_params.addWidget(dialysate_card, 0, 1)

        # Ultrafiltracion card 
        uf_card = QFrame()
        uf_card.setObjectName("card")
        uf_card.setMinimumHeight(300)
        uf_layout = QVBoxLayout(uf_card)
        uf_layout.setContentsMargins(16, 16, 16, 16)
        uf_layout.setSpacing(14)
        
        uf_title = QLabel("ULTRAFILTRACIÓN (UF)")
        uf_title.setObjectName("card_title")
        uf_layout.addWidget(uf_title)

        ufr_layout = QHBoxLayout()
        ufr_v = QVBoxLayout()
        ufr_v.setSpacing(6)
        ufr_v.addWidget(QLabel("TASA DE ULTRAFILTRACIÓN (UF)"))
        ufr_value_row = QHBoxLayout()
        ufr_value_row.setSpacing(6)
        self.uf_rate_val = QLabel("0.60")
        self.uf_rate_val.setObjectName("val_large_cyan")
        uf_rate_unit = QLabel("L/hora")
        uf_rate_unit.setStyleSheet("font-size: 22px; color: #475569; font-weight: 600;")
        ufr_value_row.addWidget(self.uf_rate_val)
        ufr_value_row.addWidget(uf_rate_unit)
        ufr_value_row.addStretch()
        ufr_v.addLayout(ufr_value_row)
        
        ufr_layout.addLayout(ufr_v)
        ufr_layout.addStretch()
        uf_layout.addLayout(ufr_layout)
   
        # Meta y Extraído
        meta_layout = QHBoxLayout()
        meta_label = QLabel("Objetivo Total UF:")
        meta_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        meta_layout.addWidget(meta_label)
        self.uf_goal_val = QLabel("2.50 L")
        self.uf_goal_val.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        meta_layout.addStretch()
        meta_layout.addWidget(self.uf_goal_val)
        uf_layout.addLayout(meta_layout)

        rem_layout = QHBoxLayout()
        rem_label = QLabel("UF Removida:")
        rem_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        rem_layout.addWidget(rem_label)
        self.uf_rem_val = QLabel("0.00 L")
        self.uf_rem_val.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        rem_layout.addStretch()
        rem_layout.addWidget(self.uf_rem_val)
        uf_layout.addLayout(rem_layout)

        ktv_layout = QHBoxLayout()
        ktv_label = QLabel("Kt/V Acumulado:")
        ktv_label.setStyleSheet("font-size: 24px; color: #334155; font-weight: 600;")
        ktv_layout.addWidget(ktv_label)
        self.ktv_val = QLabel("0.00")
        self.ktv_val.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 28px;")
        ktv_layout.addStretch()
        ktv_layout.addWidget(self.ktv_val)
        uf_layout.addLayout(ktv_layout)

        grid_params.addWidget(uf_card, 0, 2)


        # --- Columna 4: Paciente y Tiempo ---
        columna_4_layout = QVBoxLayout()
        columna_4_layout.setSpacing(10)

        # ── Card de Signos Vitales (NUEVA) ──
        vitals_card = QFrame()
        vitals_card.setObjectName("card")
        vitals_card.setMinimumHeight(230)
        vitals_layout = QVBoxLayout(vitals_card)
        vitals_layout.setContentsMargins(12, 12, 12, 12)
        vitals_layout.setSpacing(8)

        vitals_title = QLabel("SIGNOS VITALES")
        vitals_title.setObjectName("card_title")
        vitals_layout.addWidget(vitals_title)

        # Presión Arterial (NIBP)
        nibp_layout = QHBoxLayout()
        nibp_layout.addWidget(QLabel("P.A. (NIBP):"))
        self.nibp_value = QLabel("-- / --")
        self.nibp_value.setStyleSheet("color: #047857; font-weight: bold; font-size: 22px; font-family: monospace;")
        nibp_layout.addStretch()
        nibp_layout.addWidget(self.nibp_value)
        vitals_layout.addLayout(nibp_layout)

        # Saturación de Oxígeno (SpO2)
        spo2_layout = QHBoxLayout()
        spo2_layout.addWidget(QLabel("Saturación (SpO2):"))
        self.spo2_value = QLabel("-- %")
        self.spo2_value.setStyleSheet("color: #0369a1; font-weight: bold; font-size: 22px; font-family: monospace;")
        spo2_layout.addStretch()
        spo2_layout.addWidget(self.spo2_value)
        vitals_layout.addLayout(spo2_layout)

        # ── Card de Tiempos (Rediseñada) ──
        time_card = QFrame()
        time_card.setObjectName("card")
        time_card.setMinimumHeight(100) 
        time_layout = QVBoxLayout(time_card)
        time_layout.setContentsMargins(10, 10, 10, 10)
        time_layout.setSpacing(8)

        # Usamos versiones más compactas de SimpleValueDisplay o labels directos
        self.remaining_time_display = SimpleValueDisplay("T. Restante", "00:00", "")
        self.elapsed_time_display = SimpleValueDisplay("T. Terapia", "00:00", "")
        
        # OJO: Para que quepan bien, tendrías que quitar el setFixedHeight(132) 
        # del SimpleValueDisplay o hacerlo más pequeño (ej. 80px)
        # self.remaining_time_display.setFixedHeight(85)
        self.elapsed_time_display.setFixedHeight(85)

        # self.remaining_time_display ahora se muestra en el header principal.
        # Se deja comentado por si se requiere restaurarlo en esta tarjeta.
        # time_layout.addWidget(self.remaining_time_display)
        time_layout.addWidget(self.elapsed_time_display)

        # Agregamos ambas al layout vertical de la columna 4
        columna_4_layout.addWidget(vitals_card, 2)
        columna_4_layout.addWidget(time_card, 1)

        # Añadimos el layout vertical al grid general de parámetros
        grid_params.addLayout(columna_4_layout, 0, 3)


        layout.addLayout(grid_params, 0, 0, 1, 2)
        
        # ── Área Gráfica ──
        self.pressure_plot = PressureWaveformWidget()
        self.pressure_plot.setMinimumHeight(320)
        graph_container = QFrame()
        graph_container.setObjectName("graph_card")
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(10, 10, 10, 10)
        graph_layout.addWidget(self.pressure_plot)

        layout.addWidget(graph_container, 1, 1, 1, 1)

        # ── Botones de Control ──
        buttons_container = QFrame()
        buttons_container.setMinimumWidth(400)
        buttons_container.setStyleSheet("background: #ffffff; border-radius: 14px; border: 1px solid #cbd5e1;")

        buttons_layout = QGridLayout(buttons_container)
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(14, 14, 14, 14)
        for i in range(3):
            buttons_layout.setColumnStretch(i, 1)

        self.action_buttons = {} # guardar referencias de botones

        button_config = [
            ("INICIAR", "#39ec21", self.parent_window.start_treatment),
            ("PAUSAR", "#FFC400", self.parent_window.pause_treatment),
            ("DETENER", "#DD2911", self.parent_window.stop_treatment),
            ("MENÚ TERAPIA", "#06298a", self.show_therapy_config),
            ("MENÚ PACIENTE", "#06298a", self.show_patient_config),
            ("HEPARINA", "#06298a", self.show_heparin_config_screen),
            ("INICIAR CEBADO", "#06298a", self.parent_window.start_priming),
            ("DETENER CEBADO", "#06298a", self.parent_window.stop_priming),
            ("Kt/V", "#06298a", self.parent_window.show_ktv_screen),       
        ]

        for i, (text, color, callback) in enumerate(button_config):
            btn = QPushButton(text)
            btn.setFixedHeight(80)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(self._button_style(color))
            btn.clicked.connect(callback)
            self.action_buttons[text] = btn # === Guardar el botón en el diccionario ===
            row = i // 3
            col = i % 3
            buttons_layout.addWidget(btn, row, col)            
     
        layout.addWidget(buttons_container, 1, 0, 1, 1)

        

         

    def update_values(self, new_values: dict):
        """Update all displayed values."""
        self.current_values = new_values

         # 1. Obtener valores necesarios
        uf_goal = float(self.current_values.get("uf_goal_liters", 0.0))
        uf_removed = float(self.current_values.get("UF Total", 0.0))
    
        # 2. Obtener el tiempo restante (esto suele venir del state_manager o del timer)
        # Supongamos que lo guardamos en una variable de clase al actualizar tiempos
        time_text = self.remaining_time_display.label_value.text() # Lee "02:30"
        hours_left = self._time_to_decimal_hours(time_text)
    
        # 3. Calcular la Tasa (UFR)
        if hours_left > 0:
            ufr_calculated = (uf_goal - uf_removed) / hours_left
            # Asegurarse de que no sea negativa si ya se pasó de la meta
            ufr_calculated = max(0.0, ufr_calculated)
        else:
            ufr_calculated = 0.0
        
        # 4. Mostrar el valor en el label
        self.uf_rate_val.setText(f"{ufr_calculated:.2f}")

        # Actualizar gráfico
        venous_pressure = self.current_values.get("bloodVenousPressureData", 0.0)
        arterial_pressure = self.current_values.get("bloodArteryPressureData", 0.0)   
        self.pressure_plot.add_values(arterial_pressure, venous_pressure)

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
            "bloodArteryPressureData":   self.art_p_value,
            "bloodVenousPressureData":   self.ven_p_value,
            "CALC_PTM":                  self.tmp_val,
            "dialyCondVariableData":     self.cond_val,
            "bloodFlowVariableData":     self.bfr_value,
            "balanceChamberSetTiming":   self.dfr_val_label,  #verificar la salida 
            "dialyTempIFProcessData":    self.temp_value, 
            # "ultraFilterPumpSpeed":      self.uf_rate_display,  # no esta aun
            "UF Total":                  self.uf_rem_val,
            "uf_goal_liters":            self.uf_goal_val,
            # "heparineBolusQuantity":     self.bolus_display,   # no esta en pantalla 
            "ktv_acumulado":             self.ktv_val,
            "airBubbleInBloodDetected":  self.air_indicator,  
            # "dialyLinePresProcessData":  self.pt_3_display,  # Placeholder para futura métrica de depuración PT-3
            # "dialyBChamPresProcessData": self.pt_7_display,  # Placeholder para futura métrica de depuración PT-7
            # "ktv_projectado":            self.ktv_display,  
        }


        for tag, widget in parameter_mapping.items():
            value = self.current_values.get(tag, 0.0)
            self._set_label_value(tag, widget, value)

        air_bubble = self.current_values.get("airBubbleInBloodDetected", 0.0)
        self.update_air_bubble_indicator(air_bubble)
        
        if hasattr(self, 'parent_window') and hasattr(self.parent_window, 'state'):
            self.update_state(self.parent_window.state.current_phase)#

    def _time_to_decimal_hours(self, time_str: str) -> float:
        """Convierte un string 'HH:MM' a un float de horas (ej: '01:30' -> 1.5)"""
        try:
            if ":" not in time_str: return 0.0
            h, m = map(int, time_str.split(":"))
            return h + (m / 60.0)
        except:
            return 0.0


    def update_air_bubble_indicator(self, value):
        """Actualiza el indicador de burbuja de aire según el valor recibido."""
        if value == 1.0 or value == 1:  # Alarma activa
            self.air_indicator.setText("BURBUJA DE AIRE")
            self.air_indicator.setStyleSheet("""
                background-color: #ef4444; 
                color: #ffffff; 
                font-weight: bold; 
                border-radius: 8px; 
                font-size: 18px;
            """)
            logger.warning("¡ALERTA! Burbuja de aire detectada en línea de sangre.")
        else:  # Normal
            self.air_indicator.setText("DETECTOR DE AIRE")
            self.air_indicator.setStyleSheet("""
                background-color: #10B924; 
                color: #ffffff; 
                font-weight: bold; 
                border-radius: 8px; 
                font-size: 18px;
            """)

    def show_heparin_config_screen(self):
        if self.parent_window and hasattr(self.parent_window, "show_heparin_config_screen"):
            self.parent_window.show_heparin_config_screen()

    def _format_display_value(self, tag: str, value):
        try:
            # Si el valor es None, poner 0.0 por defecto
            if value is None:
                val_float = 0.0
            else:
                val_float = float(value)
        except (TypeError, ValueError):
            return str(value) # Si no es número, devolver el texto tal cual

        if tag in {"bloodArteryPressureData", "bloodVenousPressureData", "CALC_PTM"}:
            try:
                return f"{val_float:.1f} mmHg"
            except (TypeError, ValueError):
                return str(val_float)

        if tag == "dialyCondVariableData":
            try:
                return f"{val_float:.2f} mS/cm"
            except (TypeError, ValueError):
                return str(val_float)

        if tag == "bloodFlowVariableData":
            try:
                return f"{val_float:.0f}"
            except (TypeError, ValueError):
                return str(val_float)

        if tag == "balanceChamberSetTiming":
            try:
                return f"{val_float:.0f} mL/min"
            except (TypeError, ValueError):
                return str(val_float)

        if tag == "dialyTempIFProcessData":
            try:
                return f"{val_float:.1f}"
            except (TypeError, ValueError):
                return str(val_float)

        if tag in {"UF Total", "uf_goal_liters"}:
            try:
                return f"{val_float:.2f} L"
            except (TypeError, ValueError):
                return str(val_float)

        if tag == "ktv_acumulado":
            try:
                return f"{val_float:.2f}"
            except (TypeError, ValueError):
                return str(val_float)

        return str(val_float)

    def _set_label_value(self, tag: str, widget: QLabel, value):
        widget.setText(self._format_display_value(tag, value))

    def _button_style(self, background_color: str, enabled: bool = True):
        if not enabled:
            return """
                QPushButton {
                    background: #334155;
                    color: #94a3b8;
                    font-weight: bold;
                    font-size: 22px;
                    border-radius: 12px;
                    border: 3px solid #1e293b;
                }
            """

        return f"""
            QPushButton {{
                background: {background_color};
                color: #ffffff;
                font-weight: bold;
                font-size: 22px;
                border-radius: 12px;
                border: 3px solid #1e293b;
            }}
            QPushButton:pressed {{
                background: #334155;
            }}
        """

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)
    
    def set_start_stop_buttons_state(self, enable_start: bool, enable_stop: bool, enable_pause: bool):
        """
        Recibe instrucciones directas del Main para habilitar/deshabilitar.
        """
        btn_iniciar = self.action_buttons.get("INICIAR")
        btn_detener = self.action_buttons.get("DETENER")
        btn_pausar = self.action_buttons.get("PAUSAR") # se agrego este boton a la logica de activación/desactivación
        
        if btn_iniciar:
            btn_iniciar.setEnabled(enable_start)
            btn_iniciar.setStyleSheet(self._button_style("#39ec21", enable_start))
        
        if btn_detener:
            btn_detener.setEnabled(enable_stop)            
            btn_detener.setStyleSheet(self._button_style("#DD2911", enable_stop))
        
        if btn_pausar:
            btn_pausar.setEnabled(enable_pause)
            btn_pausar.setStyleSheet(self._button_style("#FFC400", enable_pause))  


    def show_therapy_config(self):
        """Navigate to therapy configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_therapy_config_screen"):
            self.parent_window.show_therapy_config_screen()

    def show_patient_config(self):
        """Navigate to patient configuration screen."""
        if self.parent_window and hasattr(self.parent_window, "show_patient_config_screen"):
            self.parent_window.show_patient_config_screen()


    def update_therapy_times(self, elapsed_str: str, remaining_str: str):
        """Método llamado desde el Main para actualizar tiempos"""
        if hasattr(self, 'elapsed_time_display') and self.elapsed_time_display:
            self.elapsed_time_display.set_time_value(elapsed_str)
        if hasattr(self, 'remaining_time_display') and self.remaining_time_display:
            self.remaining_time_display.set_time_value(remaining_str)


    def set_priming_buttons_state(self, enable_start_priming: bool, enable_stop_priming: bool):
        """
        Recibe instrucciones directas del Main para habilitar/deshabilitar
        los botones de 'INICIAR CEBADO' y 'DETENER CEBADO'.
        """
        btn_start_priming = self.action_buttons.get("INICIAR CEBADO")
        btn_stop_priming = self.action_buttons.get("DETENER CEBADO")

        # Estilos
        if btn_start_priming:
            btn_start_priming.setEnabled(enable_start_priming)
            btn_start_priming.setStyleSheet(self._button_style("#06298a", enable_start_priming))
        
        if btn_stop_priming:
            btn_stop_priming.setEnabled(enable_stop_priming)
            btn_stop_priming.setStyleSheet(self._button_style("#06298a", enable_stop_priming))
    
    
    def update_state(self, phase: TreatmentPhase):
        """Actualiza el estado visual de esta pantalla"""
        treatment_mode_selection = self.current_values.get("treatmentModeSelection", 0.0)        
        if int(treatment_mode_selection) == 3:
            self.set_priming_buttons_state(False, False)
            self.set_start_stop_buttons_state(False, False, False)
            return

        # === LÓGICA CENTRALIZADA DE CONDICIONES ===
        if hasattr(self.parent_window, '_can_start_treatment'):
            can_start = self.parent_window._can_start_treatment()
        else:
            # Fallback (mientras implementas el helper en el main)
            temp_actual = self.current_values.get("dialyTempIFProcessData", 0.0)
            temp_set    = self.current_values.get("dialyTempControlSetPoint", 0.0)
            cond_actual = self.current_values.get("dialyCondVariableData", 0.0)
            cond_set    = self.current_values.get("dialyCondControlSetPoint", 0.0)
            
            temp_ok = (temp_actual - temp_set <= 2.0) and (temp_set - temp_actual <= 5.0)
            cond_ok = abs(cond_actual - cond_set) <= 2.0
            can_start = temp_ok and cond_ok   # ← Aquí estaba bien, pero mejor dejarlo claro

        # === ACTUALIZACIÓN DE BOTONES ===
        if phase == TreatmentPhase.RUNNING:   # Estado 14
            self.set_priming_buttons_state(False, False)
            self.set_start_stop_buttons_state(False, True, True)
        elif phase == TreatmentPhase.PAUSED: # Estado 15
            self.set_priming_buttons_state(False, False)
            self.set_start_stop_buttons_state(can_start, True, False)
        elif phase == TreatmentPhase.READY: # estado 13
            self.set_priming_buttons_state(False, True)
            self.set_start_stop_buttons_state(can_start, False, False)
        elif phase == TreatmentPhase.PREPARING:
            self.set_priming_buttons_state(False, True)
            self.set_start_stop_buttons_state(False, False, False)
        elif phase == TreatmentPhase.IDLE: 
            self.set_priming_buttons_state(True, False)
            self.set_start_stop_buttons_state(False, False, False)
        else:
            # Seguridad: deshabilitar todo en estados desconocidos
            self.set_priming_buttons_state(False, False)
            self.set_start_stop_buttons_state(False, False, False)
        

    


