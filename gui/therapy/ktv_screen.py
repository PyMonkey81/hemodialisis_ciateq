# gui/therapy/ktv_screen.py

from PySide6.QtWidgets import (
    QGridLayout, QMessageBox, QWidget, QLabel, QPushButton,
    QVBoxLayout, QSizePolicy, QFrame, QComboBox, QListWidget
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor
import numpy as np
import pyqtgraph as pg
from collections import deque
import logging
import csv
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class KTVScreen(QWidget):
    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_background()

        self.history_length = 600
        self.time_axis = np.arange(-self.history_length + 1, 1, dtype=np.float32)

        # Historiales para gráfica
        self.heit_history = deque([np.nan] * self.history_length, maxlen=self.history_length)
        self.ktv_history = deque([np.nan] * self.history_length, maxlen=self.history_length)

        # Registros para reporte final
        self.ktv_records = []

        self.schedule = []
        self._last_recorded_ktv = 0.0
        self._waiting_manual_result = False  
        self.setup_ui()

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
        self.displays = {}

        for i, text in enumerate(fields):
            lbl = QLabel(text)
            lbl.setStyleSheet(label_style)
            data_layout.addWidget(lbl, i, 0)

        self.display_name = QLabel("N/A")
        self.display_age = QLabel("N/A")
        self.display_height = QLabel("N/A")
        self.display_weight = QLabel("N/A")

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

        label_bioz = QLabel("Bioimpedancia medida:")
        label_bioz.setStyleSheet(label_style)
        dl0.addWidget(label_bioz, 0, 0)
        self.display_bioz = QLabel("---")
        self.display_bioz.setStyleSheet(indicator_style)
        self.display_bioz.setAlignment(Qt.AlignCenter)
        dl0.addWidget(self.display_bioz, 0, 1)

        label_volume_heitmann =QLabel("Volumen Heitmann (L):")
        label_volume_heitmann.setStyleSheet(label_style)
        dl0.addWidget(label_volume_heitmann, 1, 0)
        self.display_heitmann = QLabel("---")
        self.display_heitmann.setStyleSheet(indicator_style)
        self.display_heitmann.setAlignment(Qt.AlignCenter)
        dl0.addWidget(self.display_heitmann, 1, 1)

        # ==================== CONFIGURACIÓN ====================
        data_container1 = QFrame()
        data_container1.setStyleSheet("background: #FCFCFC; border-radius: 12px; border: 4px solid #1e293b;")
        dl1 = QGridLayout(data_container1)
        dl1.setSpacing(10)
        dl1.setContentsMargins(15, 15, 15, 15)

        freq_label = QLabel("Frecuencia de cálculo:")
        freq_label.setStyleSheet(label_style)

        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["15 minutos", "30 minutos"])
        self.combo_freq.setStyleSheet(combo_style)
        self.combo_freq.setCurrentIndex(1)

        self.btn_run_ktv = QPushButton("Iniciar Cálculo Kt/V Ahora")
        self.btn_run_ktv.setStyleSheet(button_style)
        self.btn_run_ktv.clicked.connect(self._on_run_ktv_now)

        self.lbl_next_schedule = QLabel("Próxima medición: -")
        self.lbl_next_schedule.setStyleSheet(label_style)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(140)
        self.results_list.setStyleSheet("background: #f8fafc; font-size: 18px; color: #000000")

        dl1.addWidget(freq_label, 0, 0)
        dl1.addWidget(self.combo_freq, 0, 1)
        dl1.addWidget(self.btn_run_ktv, 0, 2)
        dl1.addWidget(self.lbl_next_schedule, 1, 0, 1, 3)
        dl1.addWidget(self.results_list, 2, 0, 1, 3)

        # ==================== GRÁFICA ====================
        data_container2 = QFrame()
        data_container2.setStyleSheet("background: #FCFCFC; border-radius: 12px; border: 4px solid #1e293b;")
        data_layout2 = QGridLayout(data_container2)
        data_layout2.setContentsMargins(10, 10, 10, 10)

        self.plot_layout = QVBoxLayout()
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        try:
            self.pg_main = pg.PlotWidget(background="#1e2421")
            self.pg_main.setFrameShape(QFrame.NoFrame)
            self.pg_main.setStyleSheet("border: none; background: #dedede;")

            p = self.pg_main.getPlotItem()
            p.showGrid(x=True, y=True, alpha=0.3)
            p.setTitle("Heitmann (L)  ─  Kt/V", color="#ffffff", size="15pt")

            legend = p.addLegend(offset=(10, 10), labelTextColor='#ffffff')
            self.curve_heit = p.plot([], [], pen=pg.mkPen('#ff8800', width=3), name='Heitmann (L)')

            p.showAxis('right')
            self.vb_right = pg.ViewBox()
            p.scene().addItem(self.vb_right)
            p.getAxis('right').linkToView(self.vb_right)
            self.vb_right.setXLink(p)

            self.curve_ktv = pg.PlotCurveItem([], [], pen=pg.mkPen('#00aaff', width=3), name='Kt/V')
            self.vb_right.addItem(self.curve_ktv)
            legend.addItem(self.curve_ktv, 'Kt/V')

            def _update_views():
                self.vb_right.setGeometry(p.vb.sceneBoundingRect())
                self.vb_right.linkedViewChanged(p.vb, self.vb_right.XAxis)

            p.vb.sigResized.connect(_update_views)

            p.vb.setYRange(0, 60, padding=0.05)
            self.vb_right.setYRange(0, 2.5, padding=0.05)

            self.plot_layout.addWidget(self.pg_main)
            data_layout2.addLayout(self.plot_layout, 0, 0)

        except Exception as e:
            logger.error(f"Error en gráfica: {e}")
            data_layout2.addWidget(QLabel("Error al cargar gráfica"), 0, 0)

        # Layout principal
        layout.addWidget(data_container, 0, 0)
        layout.addWidget(data_container0, 0, 1)
        layout.addWidget(data_container1, 1, 0, 1, 2)
        layout.addWidget(data_container2, 2, 0, 1, 2)

        self.setLayout(layout)

    # ====================== MÉTODOS ======================

    def _safe_value(self, value):
        try:
            val = float(value)
            return max(0.0, val)
        except:
            return np.nan

    def update_values(self, new_values: dict):
        self.current_values = new_values

        # Actualizar labels
        self.display_name.setText(str(self.current_values.get("patient_name", "N/A")))
        self.display_age.setText(str(self.current_values.get("patient_age", "N/A")))
        self.display_height.setText(str(self.current_values.get("patient_height_cm", "N/A")) + " cm")
        self.display_weight.setText(str(self.current_values.get("patient_pre_weight_kg", "N/A")) + " kg")

        self.display_bioz.setText(str(self.current_values.get("bioz_resistance", "---")))
        self.display_heitmann.setText(str(self.current_values.get("heitmann_value", "---")))

        # Gráficas
        heit = self._safe_value(self.current_values.get("heitmann_value"))
        ktv_val = self._safe_value(self.current_values.get("ktv_acumulado"))

        self.heit_history.append(heit)
        self.ktv_history.append(ktv_val)

        if hasattr(self, 'curve_heit'):
            self.curve_heit.setData(self.time_axis, np.array(self.heit_history, dtype=np.float32))

        if hasattr(self, 'curve_ktv'):
            arr_k = np.array(self.ktv_history, dtype=np.float32)
            self.curve_ktv.setData(self.time_axis, arr_k)
            valid = arr_k[~np.isnan(arr_k)]
            if len(valid) > 0:
                self.vb_right.setYRange(0, max(2.5, float(np.nanmax(valid)) * 1.15), padding=0.08)

        
        # === Guardar resultado (mejorado para manual y auto) ===
        if ktv_val > 0.01:   # Hay un valor significativo
            # is_new = (abs(ktv_val - self._last_recorded_ktv) > 0.001) or getattr(self, '_waiting_manual_result', False)
            last_ktv = self._last_recorded_ktv if self._last_recorded_ktv is not None else 0.0
            diff = abs(ktv_val - last_ktv)

            is_manual = getattr(self, '_waiting_manual_result', False)
            is_new = (diff > 0.001) or is_manual

            if is_new:
                # Actualizamos el último valor guardado inmediatamente
                self._last_recorded_ktv = ktv_val

                # 3. Creamos el registro del reporte según el tipo
                record = {
                    "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
                    "heitmann_l": round(heit, 2),
                    "ktv": round(ktv_val, 3),
                    "type": "Manual" if is_manual else "Auto"
                }
                self.ktv_records.append(record)

                # 4. Construimos el texto para la interfaz de usuario (UI)
                ts = QDateTime.currentDateTime().toString("dd/MM HH:mm")
                item_text = f"{ts} → Kt/V: {ktv_val:.3f} | Heit: {heit:.1f} L"
                
                # Aquí entra de forma totalmente segura y limpia
                if is_manual: 
                    item_text += "  [MANUAL]"

                # 5. Insertamos en la lista de la pantalla
                self.results_list.addItem(item_text)
                
                if self.results_list.count() > 60:
                    self.results_list.takeItem(0)

                # 6. Al final de TODO el proceso, si era manual, reseteamos la bandera de la clase
                if is_manual:
                    self._waiting_manual_result = False

    def on_master_tick(self):
        """Llamado desde el timer maestro"""
        self.update_values(self.current_values)

        if not self._is_therapy_active():
            self.lbl_next_schedule.setText("Esperando inicio de terapia...")
            return

        if not self.schedule:
            self._compute_schedule()

        self.lbl_next_schedule.setText(self._format_next())

        elapsed = self._get_elapsed_seconds()
        if self.schedule and elapsed >= self.schedule[0]:
            logger.info(f"[KTV Auto] Ejecutando medición programada a los {elapsed//60} minutos")
            if hasattr(self.parent_window, 'ktv_meassurement'):
                self.parent_window.ktv_meassurement()
            
            self.schedule.pop(0)

    # ====================== AUXILIARES ======================

    def _is_therapy_active(self) -> bool:
        if not self.parent_window:
            return False
        status = int(self.current_values.get("primingProcessStatus", 0))
        patient = str(self.current_values.get("patient_name", "")).strip()
        return status in (14, 15) and patient and patient != "N/A"

    def _get_elapsed_seconds(self) -> int:
        if not self.parent_window:
            return 0
        elapsed = getattr(self.parent_window, 'accumulated_therapy_seconds', 0)
        last_resume = getattr(self.parent_window, 'last_resume_time', None)
        if last_resume:
            elapsed += last_resume.secsTo(QDateTime.currentDateTime())
        return int(elapsed)

    def _compute_schedule(self):
        self.schedule.clear()
        if not self._is_therapy_active():
            return

        total_sec = getattr(self.parent_window, 'total_therapy_seconds', 0)
        elapsed = self._get_elapsed_seconds() # Get current elapsed time
        if total_sec <= 0:
            return

        freq_min = 15 if "15" in self.combo_freq.currentText() else 30
        start_at = freq_min * 60
        last_allowed = max(0, total_sec - 600)  # 10 minutos de margen

        t = start_at
        while t <= last_allowed:
            if t > elapsed:
                self.schedule.append(t)
            t += freq_min * 60


    def _format_next(self) -> str:
        if not self.schedule:
            return "No hay más mediciones programadas"
        minutes = self.schedule[0] // 60
        return f"Próxima medición: {minutes} minutos"

    def _on_run_ktv_now(self):
        if not self._is_therapy_active():            
            self.parent_window.show_warning_message("Debe haber tratamiento activo y paciente seleccionado.")
            return

        if hasattr(self.parent_window, 'ktv_meassurement'):
            self._waiting_manual_result = True
            self.parent_window.ktv_meassurement()            
            ts = QDateTime.currentDateTime().toString("dd/MM HH:mm")
            self.results_list.addItem(f"{ts} → **CÁLCULO MANUAL INICIADO**...")

        else:
            self.parent_window.show_error_message("Función de medición no disponible.")

    def save_final_report(self):
        """Guardar reporte final al terminar terapia"""
        if not self.ktv_records:
            return None

        try:
            os.makedirs("logs/ktv_reports", exist_ok=True)
            filename = f"logs/ktv_reports/ktv_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "heitmann_l", "ktv", "type"])
                writer.writeheader()
                writer.writerows(self.ktv_records)

            logger.info(f"Reporte Kt/V final guardado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error guardando reporte final: {e}")
            return None
        