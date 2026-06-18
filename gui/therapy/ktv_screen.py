# gui/therapy/ktv_screen.py
from PySide6.QtWidgets import (
    QGridLayout, QWidget, QLabel, QPushButton,
    QVBoxLayout, QSizePolicy, QFrame, QComboBox, QListWidget
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor
import numpy as np
import pyqtgraph as pg
import logging
import csv
import os
from datetime import datetime
from shiboken6 import isValid
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)


class KTVScreen(QWidget):
    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {} # Mantener esto para datos de paciente/otras variables de UI

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_background()

        self.ktv_records = []
        self.ktv_points = []      # (minutos_total, ktv)
        self.heit_points = []     # (minutos_total, heitmann)

        self._last_recorded_ktv = 0.0
        self._waiting_manual_result = False  
        self._selected_frequency_index = 2
        self._manual_pending_row: int = -1  # fila del placeholder "INICIADO..."
        self._last_calc_signature: str = ""

        self.setup_ui()
        self.init_plot() # Llamar a la inicialización de la gráfica aquí

    def setup_background(self):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#0f472a"))
        self.setPalette(p)

    def setup_ui(self):
        layout = QGridLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        label_style = "color: #000000; font-size: 22px; font-weight: bold; border: none; background: transparent;"
        indicator_style = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #1e293b; border-radius: 6px; padding: 6px;"

        button_style = """
            QPushButton { 
                background: #3b82f6; 
                color: #ffffff; 
                border: none; 
                border-radius: 8px; 
                font-size: 24px; 
                font-weight: bold; 
                padding: 10px;
            }
            QPushButton:pressed { background: #1e40af; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """

        combo_style = """
            QComboBox {
                color: #1f2937; font-size: 22px; font-weight: bold;
                background: #f8fafc; border: 2px solid #64748b; border-radius: 8px; padding: 8px 12px;
            }
            QComboBox:hover { border-color: #3b82f6; }
            QComboBox QAbstractItemView {
                background: #f8fafc; color: #1f2937; font-size: 20px; font-weight: bold;
                border: 2px solid #64748b; selection-background-color: #3b82f6;
            }
        """

        # ==================== DATOS DEL PACIENTE ====================
        data_container = QFrame()
        data_container.setStyleSheet("background: #FCFCFC; border-radius: 12px; border: 4px solid #1e293b;")
        data_layout = QGridLayout(data_container)
        data_layout.setSpacing(8)
        data_layout.setContentsMargins(15, 15, 15, 15)

        fields = ["Nombre de paciente:", "Edad:", "Altura:", "Peso:"]
        self.display_name = QLabel("N/A")
        self.display_age = QLabel("N/A")
        self.display_height = QLabel("N/A")
        self.display_weight = QLabel("N/A")

        for i, text in enumerate(fields):
            lbl = QLabel(text)
            lbl.setStyleSheet(label_style)
            data_layout.addWidget(lbl, i, 0)
        
        for i, widget in enumerate([self.display_name, self.display_age, self.display_height, self.display_weight]):
            widget.setStyleSheet(indicator_style)
            widget.setAlignment(Qt.AlignCenter)
            data_layout.addWidget(widget, i, 1)

        # ==================== BIOIMPEDANCIA + HEITMANN ====================
        data_container0 = QFrame()
        data_container0.setStyleSheet("background: #FCFCFC; border-radius: 12px; border: 4px solid #1e293b;")
        dl0 = QGridLayout(data_container0)
        dl0.setSpacing(8)
        dl0.setContentsMargins(15, 15, 15, 15)

        label_bioz = QLabel("Bioimpedancia (Z):")
        label_bioz.setStyleSheet(label_style)
        dl0.addWidget(label_bioz, 0, 0)
        self.display_bioz = QLabel("--- Ω")
        self.display_bioz.setStyleSheet(indicator_style)
        self.display_bioz.setAlignment(Qt.AlignCenter)
        dl0.addWidget(self.display_bioz, 0, 1)

        label_volume_heitmann = QLabel("Volumen Heitmann (L):")
        label_volume_heitmann.setStyleSheet(label_style)
        dl0.addWidget(label_volume_heitmann, 1, 0)
        self.display_heitmann = QLabel("--- L")
        self.display_heitmann.setStyleSheet(indicator_style)
        self.display_heitmann.setAlignment(Qt.AlignCenter)
        dl0.addWidget(self.display_heitmann, 1, 1)

        # ==================== CONFIGURACIÓN Y RESULTADOS ====================
        data_container1 = QFrame()
        data_container1.setStyleSheet("background: #FCFCFC; border-radius: 12px; border: 4px solid #1e293b;")
        dl1 = QGridLayout(data_container1)
        dl1.setSpacing(10)
        dl1.setContentsMargins(15, 15, 15, 15)

        freq_label = QLabel("Frecuencia cálculo automático:")
        freq_label.setStyleSheet(label_style)

        # Indicador visual de la frecuencia activa
        self.lbl_freq_indicator = QLabel("● Deshabilitado")
        self.lbl_freq_indicator.setStyleSheet(
            "color: #94a3b8; font-size: 18px; font-weight: bold; "
            "background: #1e293b; border-radius: 6px; padding: 4px 10px;"
        )
        self.lbl_freq_indicator.setAlignment(Qt.AlignCenter)

        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["15 minutos", "30 minutos", "Deshabilitado"]) # Añadir opción de deshabilitar
        self.combo_freq.setStyleSheet(combo_style)
        self.combo_freq.setCurrentIndex(2) # Valor por defecto: Deshabilitado
        self._selected_frequency_index = self.combo_freq.currentIndex()
        self.combo_freq.currentIndexChanged.connect(self._on_frequency_changed)

        self.btn_run_ktv = QPushButton("Iniciar Cálculo Kt/V Manual")
        self.btn_run_ktv.setStyleSheet(button_style)
        self.btn_run_ktv.clicked.connect(self._on_run_ktv_now)

        self.lbl_next_schedule = QLabel("Próxima medición: No programado")
        self.lbl_next_schedule.setStyleSheet(label_style)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(140)
        self.results_list.setStyleSheet("""
            QListWidget {
                background: #f8fafc;
                font-size: 18px;
                color: #000000;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 4px 8px;
            }
            QListWidget QScrollBar:vertical {
                border: none;
                background: #e0e0e5;
                width: 34px;
                margin: 0px 0px 0px 0px;
                border-radius: 14px;
            }
            QListWidget QScrollBar::handle:vertical {
                background: #8a8a9c;
                min-height: 60px;
                border-radius: 14px;
            }
            QListWidget QScrollBar::handle:vertical:hover {
                background: #6b6b7a;
            }
            QListWidget QScrollBar::add-line:vertical, QListWidget QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QListWidget QScrollBar::add-page:vertical, QListWidget QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        dl1.addWidget(freq_label, 0, 0)
        dl1.addWidget(self.combo_freq, 0, 1)
        dl1.addWidget(self.lbl_freq_indicator, 0, 2)
        dl1.addWidget(self.btn_run_ktv, 0, 3)
        dl1.addWidget(self.lbl_next_schedule, 1, 0, 1, 4)
        dl1.addWidget(self.results_list, 2, 0, 1, 4)

        # Panels superiores de datos y configuración
        layout.addWidget(data_container, 0, 0)
        layout.addWidget(data_container0, 0, 1)
        layout.addWidget(data_container1, 1, 0, 1, 2)

        # ==================== GRÁFICA ====================
        self.plot_widget = pg.PlotWidget() # Se inicializa en init_plot
        layout.addWidget(self.plot_widget, 2, 0, 1, 2)

        # Reparto de espacio vertical: prioridad a la gráfica sin ocultar paneles.
        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 2)
        layout.setRowStretch(2, 6)

        self.setLayout(layout)

    def init_plot(self):
        """Inicializa los parámetros de la gráfica pyqtgraph con dos ejes Y."""
        self.plot_widget.setBackground("#1e2421")
        self.plot_widget.setTitle("Kt/V y Heitmann durante la terapia", 
                                color="#ffffff", size="16pt")
        self.plot_widget.setLabel('left', 'Kt/V', color='#00aaff', size="14pt")
        self.plot_widget.setLabel('bottom', 'Tiempo de terapia (min)', 
                                color='#ffffff', size="14pt")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Eje derecho para Heitmann
        right_axis = self.plot_widget.plotItem.getAxis('right')
        right_axis.enableAutoSIPrefix(False)
        right_axis.setLabel('Heitmann (L)', color='#ff8800')

        # Curva Kt/V (eje izquierdo)
        self.curve_ktv = self.plot_widget.plot([], [], 
            pen=pg.mkPen('#00aaff', width=3),
            symbol='o', symbolSize=8, symbolBrush='#00aaff', 
            name='Kt/V')

        # ViewBox secundario para la curva de Heitmann (eje derecho)
        self.p2 = pg.ViewBox()
        self.plot_widget.scene().addItem(self.p2)
        
        # === Configuración correcta de enlace ===
        self.plot_widget.plotItem.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.plot_widget.plotItem)   # Comparten el eje X

        # Curva Heitmann en el ViewBox secundario
        self.curve_heit = pg.PlotDataItem([], [], 
            pen=pg.mkPen('#ff8800', width=3),
            symbol='o', symbolSize=8, symbolBrush='#ff8800', 
            name='Heitmann (L)')
        self.p2.addItem(self.curve_heit)

        self.plot_widget.addLegend()

        # Sincronizar geometría cuando se redimensiona
        def updateViews():
            self.p2.setGeometry(self.plot_widget.plotItem.vb.sceneBoundingRect())
            self.p2.linkedViewChanged(self.plot_widget.plotItem.vb, self.p2.XAxis)

        updateViews()
        self.plot_widget.plotItem.vb.sigResized.connect(updateViews)
    # ====================== ACTUALIZACIÓN DEL ESTADO GLOBAL (antes update_state) ======================
    # Renombrado para evitar conflictos con screen_state_manager y ser más claro
    def update_state(self, phase: TreatmentPhase): # Mantengo el nombre `update_state` para que ScreenStateManager lo llame
        """
        Actualiza el estado de la UI de la pantalla de Kt/V en función de la fase
        general de la aplicación (ej. si la terapia está activa).
        Este método es el que ScreenStateManager debería llamar.
        """
        # --- Medida defensiva contra RuntimeError por objetos Qt eliminados ---
        btn = getattr(self, "btn_run_ktv", None)
        combo = getattr(self, "combo_freq", None)
        lbl_schedule = getattr(self, "lbl_next_schedule", None)

        if btn is None or combo is None or lbl_schedule is None:
            logger.warning("KTVScreen.update_state: UI incompleta. Ignorando actualización.")
            return

        if not isValid(btn) or not isValid(combo) or not isValid(lbl_schedule):
            logger.warning("KTVScreen.update_state: widgets Qt ya eliminados. Ignorando actualización.")
            return
        # -----------------------------------------------------------------

        # Cálculo manual solo en RUNNING.
        active = phase == TreatmentPhase.RUNNING
        btn.setEnabled(active)

        # La frecuencia automática puede configurarse antes de iniciar terapia y en pausa.
        combo.setEnabled(phase in (TreatmentPhase.IDLE, TreatmentPhase.PAUSED, TreatmentPhase.RUNNING))

        # Solo resetear etiqueta al salir de modos de terapia (RUNNING/PAUSED).
        if phase not in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
            lbl_schedule.setText("Próxima medición: No programado")

    # ====================== ACTUALIZACIÓN DE DATOS DEL PACIENTE (Se llama desde appMainHemodialysis) ======================
    def update_patient_data(self, new_values: dict):
        """
        Actualiza solo la información del paciente y la Bioimpedancia (Z) mostrada.
        Esto se llama regularmente desde el master_timer.
        """
        required_widgets = [
            getattr(self, "display_name", None),
            getattr(self, "display_age", None),
            getattr(self, "display_height", None),
            getattr(self, "display_weight", None),
            getattr(self, "display_bioz", None),
        ]
        if any(w is None or not isValid(w) for w in required_widgets):
            logger.warning("KTVScreen.update_patient_data: widgets Qt no válidos. Ignorando actualización.")
            return

        self.current_values = new_values # Actualizar referencia a los valores globales
        self.display_name.setText(str(new_values.get("patient_name", "N/A")))
        self.display_age.setText(str(new_values.get("patient_age", "N/A")))
        self.display_height.setText(str(new_values.get("patient_height_cm", "N/A")) + " cm")
        self.display_weight.setText(str(new_values.get("patient_pre_weight_kg", "N/A")) + " kg")
        self.display_bioz.setText(f"{new_values.get('bioz_resistance', 0.0):.2f} Ω")

    # ====================== ACTUALIZACIÓN DE VALORES (Recibe los datos del KtvController) ======================
    def update_values(self, ktv_data: dict):
        """
        Recibe los datos calculados de Kt/V y Heitmann del KtvController
        para actualizar la interfaz de usuario.
        """
        if getattr(self, "display_heitmann", None) is None or not isValid(self.display_heitmann):
            logger.warning("KTVScreen.update_values: widgets Qt no válidos. Ignorando actualización.")
            return

        # HEITMANN y Kt/V se obtienen del diccionario ktv_data
        heit_val = ktv_data.get("heitmann_value", 0.0)
        ktv_val = ktv_data.get("ktv_acumulado", 0.0)
        measurement_type = ktv_data.get("type", "Auto")
        minutes_total = float(ktv_data.get("therapy_minutes", 0.0)) # El KtvController debe proporcionar esto
        is_calc_event = bool(ktv_data.get("calculation_event", False))
        event_signature = str(ktv_data.get("event_id", ""))

        self.display_heitmann.setText(f"{heit_val:.2f} L" if heit_val > 0 else "--- L")

        # Solo registrar/plotear cuando llega un evento real de cálculo del controlador.
        if not is_calc_event:
            return

        if event_signature and event_signature == self._last_calc_signature:
            logger.debug("[KTVScreen] Evento de cálculo duplicado ignorado.")
            return
        if event_signature:
            self._last_calc_signature = event_signature

        # Si el evento viene persistido en current_values, lo marcamos como consumido
        # para que no vuelva a registrarse al refrescar la pantalla.
        if isinstance(ktv_data, dict) and "calculation_event" in ktv_data:
            ktv_data["calculation_event"] = False

        x_val = max(0.0, minutes_total)
        self.ktv_points.append((x_val, float(ktv_val)))
        self.heit_points.append((x_val, float(heit_val)))

        total_therapy_minutes = self._get_total_therapy_minutes()
        x_max = max(1.0, total_therapy_minutes)

        # --- Actualizar curva Kt/V ---
        x_ktv, y_ktv = zip(*self.ktv_points)
        self.curve_ktv.setData(list(x_ktv), list(y_ktv))
        max_ktv = max([0.0] + list(y_ktv))
        self.plot_widget.setXRange(0.0, x_max, padding=0)
        self.plot_widget.setYRange(0.0, max(0.5, max_ktv * 1.3), padding=0)

        # --- Actualizar curva Heitmann (ViewBox secundario) ---
        x_h, y_h = zip(*self.heit_points)
        self.curve_heit.setData(list(x_h), list(y_h))
        max_heit = max([0.0] + list(y_h))
        self.p2.setYRange(0.0, max(1.0, max_heit * 1.3))

        # ── Guardar en registros CSV y añadir/reemplazar en la tabla ──
        record_entry = {
            "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "heitmann_l": round(heit_val, 2),
            "ktv": round(ktv_val, 3),
            "type": measurement_type,
            "therapy_minutes": minutes_total,
        }
        self.ktv_records.append(record_entry)

        ts = QDateTime.currentDateTime().toString("dd/MM HH:mm")
        is_manual = (measurement_type == "Manual")
        prefix = "[MANUAL]" if is_manual else "[AUTO]"
        item_text = (
            f"{ts} {prefix}  Kt/V: {ktv_val:.3f} | "
            f"Heit: {heit_val:.1f} L | t: {minutes_total:.1f} min"
        )

        if is_manual and 0 <= self._manual_pending_row < self.results_list.count():
            self.results_list.item(self._manual_pending_row).setText(item_text)
            self._manual_pending_row = -1
        else:
            self.results_list.addItem(item_text)

        self.results_list.scrollToBottom()
        while self.results_list.count() > 60:
            self.results_list.takeItem(0)

    def _get_total_therapy_minutes(self) -> float:
        """Obtiene la duración total programada de terapia en minutos para fijar el eje X."""
        hours = float(self.current_values.get("heparineTherapyHours", 0) or 0)
        minutes = float(self.current_values.get("heparineTherapyMinutes", 0) or 0)
        total = (hours * 60.0) + minutes
        return total if total > 0 else 180.0

    # ====================== Actualización de la programación automática ======================
    def update_schedule_display(self, next_measurement_time_str: str):
        """Actualiza la etiqueta que muestra la próxima medición programada."""
        label = getattr(self, "lbl_next_schedule", None)
        if label is None or not isValid(label):
            logger.warning("KTVScreen.update_schedule_display: lbl_next_schedule no válido. Ignorando actualización.")
            return
        label.setText(f"Próxima medición: {next_measurement_time_str}")

    # ====================== HANDLERS DE USUARIO ======================
    # ── Mapa de texto→frecuencia y color para el indicador visual ──
    _FREQ_MAP = {
        "15 minutos":  (15,  "#22c55e", "● 15 min"),
        "30 minutos":  (30,  "#3b82f6", "● 30 min"),
        "Deshabilitado": (0, "#94a3b8", "● Deshabilitado"),
    }

    def _on_frequency_changed(self, index: int):
        """
        Maneja el cambio en la selección de frecuencia de cálculo automático.
        Notifica al KtvController sobre la nueva frecuencia.
        """
        self._selected_frequency_index = index

        selected_text = self.combo_freq.currentText()
        freq_min, color, badge = self._FREQ_MAP.get(selected_text, (0, "#94a3b8", "● Deshabilitado"))

        # Actualizar indicador visual
        lbl = getattr(self, "lbl_freq_indicator", None)
        if lbl and isValid(lbl):
            lbl.setText(badge)
            lbl.setStyleSheet(
                f"color: {color}; font-size: 18px; font-weight: bold; "
                f"background: #1e293b; border-radius: 6px; padding: 4px 10px;"
            )

        if hasattr(self.parent_window, 'ktv_controller') and self.parent_window.ktv_controller:
            self.parent_window.ktv_controller.set_automatic_frequency(freq_min)
            logger.info(f"Frecuencia de cálculo automático de Kt/V cambiada a {freq_min} minutos.")
        
    def _on_run_ktv_now(self):
        """
        Inicia un cálculo manual de Kt/V.
        Delega la lógica de inicio y validación al KtvController.
        Guarda la fila del placeholder para reemplazarla con el resultado real.
        """
        if hasattr(self.parent_window, 'ktv_controller') and self.parent_window.ktv_controller:
            self.parent_window.ktv_controller.start_manual_measurement()
            ts = QDateTime.currentDateTime().toString("dd/MM HH:mm")
            # Guardamos el índice para reemplazarlo cuando llegue el resultado
            self._manual_pending_row = self.results_list.count()
            self.results_list.addItem(f"{ts} → [MANUAL] Cálculo iniciado, esperando resultado...")
            self.results_list.scrollToBottom()
        else:
            if hasattr(self.parent_window, 'show_error_message'):
                self.parent_window.show_error_message("Controlador Kt/V no disponible.")

    # ====================== REPORTE FINAL ======================
    def save_final_report(self):
        """Guardar reporte final al terminar terapia"""
        if not hasattr(self, 'ktv_records') or not self.ktv_records:
            return None

        try:
            os.makedirs("logs/ktv_reports", exist_ok=True)
            filename = f"logs/ktv_reports/ktv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv" # Añadir segundos para evitar colisiones
            
            # Definir los nombres de los campos en el CSV, incluyendo los nuevos
            fieldnames = ["timestamp", "heitmann_l", "ktv", "type", "therapy_minutes"]

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.ktv_records)

            logger.info(f"Reporte Kt/V final guardado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error guardando reporte final: {e}")
            return None

    def reset_screen_data(self, preserve_frequency: bool = True):
        """Resetea datos de pantalla y gráfica; por defecto conserva frecuencia automática."""
        self.ktv_records.clear()
        self.ktv_points.clear()
        self.heit_points.clear()
        self.results_list.clear()
        self.curve_ktv.setData([], [])
        self.curve_heit.setData([], [])
        self.display_name.setText("N/A")
        self.display_age.setText("N/A")
        self.display_height.setText("N/A")
        self.display_weight.setText("N/A")
        self.display_bioz.setText("--- Ω")
        self.display_heitmann.setText("--- L")
        self.lbl_next_schedule.setText("Próxima medición: No programado")
        self._last_recorded_ktv = 0.0
        self._waiting_manual_result = False
        self._manual_pending_row = -1
        self._last_calc_signature = ""
        if preserve_frequency:
            self.combo_freq.blockSignals(True)
            self.combo_freq.setCurrentIndex(self._selected_frequency_index)
            self.combo_freq.blockSignals(False)
        else:
            self.combo_freq.setCurrentIndex(2) # Deshabilitado por defecto
            self._selected_frequency_index = 2
