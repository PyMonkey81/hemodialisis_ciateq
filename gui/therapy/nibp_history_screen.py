# gui/therapy/nibp_history_screen.py
"""
Pantalla de historial de mediciones de presión arterial (NIBP) para una sesión de terapia.
- Gráfica pyqtgraph con sistólica (rojo), diastólica (azul), FC (verde)
- Tabla con todas las mediciones incluyendo las "antes" (sin elapsed_s)
- Botón para volver a la pantalla del baumanómetro
"""

import logging
from timeit import main
from typing import Optional, List
from PySide6.QtWidgets import (
    QGridLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from numpy.f2py import main
import pyqtgraph as pg
import numpy as np

from core.nibp_pressure_history import NibpPressureHistory

logger = logging.getLogger(__name__)


class NibpHistoryScreen(QWidget):
    """Pantalla de visualización del historial de presiones de una terapia."""
    
    def __init__(self, parent=None, history: Optional[NibpPressureHistory] = None):
        super().__init__(parent)
        self.parent_window = parent
        self.history = history if history is not None else NibpPressureHistory()
        
        self.programmed_therapy_minutes = 240  # duración programada (se actualiza desde main)
        
        self.setup_background()
        self.setup_ui()
        self.update_from_history()
    
    def setup_background(self):
        """Fondo de la pantalla."""
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#ffffff"))
        self.setPalette(p)
    
    def setup_ui(self):
        """Construye la interfaz: encabezado, gráfica, tabla, botón."""
        main = QGridLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # main_layout = QVBoxLayout(self)
        # main_layout.setContentsMargins(10, 10, 10, 10)
        # main_layout.setSpacing(10)
        
        # ─── ENCABEZADO ───────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title = QLabel("Historial de Presión Arterial")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_close.clicked.connect(self.on_close_clicked)
        header_layout.addWidget(btn_close)
        
        main.addLayout(header_layout,0, 0, 1, 2)
        
        # ─── ÁREA DE CONTENIDO: GRÁFICA (izq) + TABLA (abajo) ────────
        # Gráfica en la columna izquierda, ocupa mitad del ancho útil, mín 320px alto
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#ffffff")
        self.plot_widget.hideButtons()
        # self.plot_widget.setMinimumHeight(250)
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        plot_item = self.plot_widget.plotItem
        self.plot_item = plot_item 
        plot_item.setLabel("left", "mmHg", color="#0f172a")
        plot_item.setLabel("bottom", "Minutos de Terapia", color="#0f172a")
        plot_item.showGrid(x=True, y=True, alpha=0.25)
        plot_item.showAxis("right")
        plot_item.getAxis("right").setLabel("lpm", color="#15803d")
        for name in ("left", "bottom", "right"):
            axis = plot_item.getAxis(name)
            axis.enableAutoSIPrefix(False)
            axis.setPen(pg.mkPen("#0f172a"))
            axis.setTextPen(pg.mkPen("#0f172a"))

        plot_item.vb.setBackgroundColor("#ffffff")
        plot_item.vb.enableAutoRange(False)
        plot_item.vb.setYRange(40, 200, padding=0)
        plot_item.vb.setXRange(0, max(self.programmed_therapy_minutes, 1), padding=0)

        self.curve_sys = self.plot_widget.plot(
            [], [], pen=pg.mkPen("#dc2626", width=2),
            symbol="o", symbolSize=7, symbolBrush="#dc2626", name="Sistólica",
        )
        self.curve_dia = self.plot_widget.plot(
            [], [], pen=pg.mkPen("#2563eb", width=2),
            symbol="o", symbolSize=7, symbolBrush="#2563eb", name="Diastólica",
        )

        self.vb_hr = pg.ViewBox()
        self.vb_hr.setBackgroundColor((0, 0, 0, 0))  # transparente: esto quita el negro
        self.vb_hr.enableAutoRange(False)
        self.vb_hr.setYRange(40, 160, padding=0)
        plot_item.scene().addItem(self.vb_hr)
        plot_item.getAxis("right").linkToView(self.vb_hr)
        self.vb_hr.setXLink(plot_item)

        self.curve_hr = pg.PlotDataItem(
            [], [], pen=pg.mkPen("#15803d", width=2),
            symbol="o", symbolSize=7, symbolBrush="#15803d",
        )
        self.vb_hr.addItem(self.curve_hr)

        legend = plot_item.addLegend(offset=(10, 10))
        legend.addItem(self.curve_sys, "Sistólica")
        legend.addItem(self.curve_dia, "Diastólica")
        legend.addItem(self.curve_hr, "FC")

        def update_views():
            self.vb_hr.setGeometry(plot_item.vb.sceneBoundingRect())

        update_views()
        plot_item.vb.sigResized.connect(update_views)

        plot_layout = QHBoxLayout()
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.plot_widget, 1)
        # plot_layout.addStretch(1)

        plot_container = QFrame()
        plot_container.setStyleSheet("background-color: #ffffff; border: none;")
        plot_container.setLayout(plot_layout)

        # main.addWidget(plot_container, 1, 0, 1, 2)
        
        # ─── TABLA ─────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No.", "Tiempo", "SYS", "DIA", "MAP", "FC", "SpO2", "Origen"
        ])
        
        # Estilos de la tabla: tema claro, sin barra negra en el encabezado
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e2e8f0;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
                background-color: #ffffff;
                color: #0f172a;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
            }
            QHeaderView {
                background-color: #ffffff;
                border: none;
            }
            QHeaderView::section {
                background-color: #ffffff;
                color: #0f172a;
                padding: 4px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #ffffff;
                border: none;
            }
        """)
        
        # Ajustar columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        
        # self.table.setMaximumHeight(280)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # main.addWidget(self.table, 2, 0, 2, 1)
        
        # ─── PIE DE PÁGINA ────────────────────────────────────────────
        footer_layout = QHBoxLayout()
        self.lbl_count = QLabel("Total: 0 mediciones")
        self.lbl_count.setStyleSheet("font-size: 14px; color: #0f172a;")
        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch()

        self.plot_widget.setMinimumHeight(330)
        self.plot_widget.setMaximumHeight(350)
        
        main.addWidget(plot_container, 1, 0, 1, 2)
        main.addWidget(self.table, 2, 0, 1, 2)
        main.addLayout(footer_layout, 3, 0, 1, 2)

        main.setRowStretch(0, 0)
        main.setRowStretch(1, 0)
        main.setRowStretch(2, 1)
        main.setRowStretch(3, 0)
        
        self.setLayout(main)
    
    def update_from_history(self):
        """Actualiza gráfica y tabla desde el historial."""
        measurements = self.history.get_all_measurements()
        self.table.setRowCount(len(measurements))

        for row_idx, measurement in enumerate(measurements):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(measurement.n)))

            if measurement.elapsed_s is not None:
                minutes = int(measurement.elapsed_s // 60)
                seconds = int(measurement.elapsed_s % 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
            else:
                time_str = "antes"

            self.table.setItem(row_idx, 1, QTableWidgetItem(time_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(measurement.sys)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(measurement.dia)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(measurement.map_mmhg)))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(measurement.hr)))
            spo2_str = str(measurement.spo2) if measurement.spo2 is not None else "—"
            self.table.setItem(row_idx, 6, QTableWidgetItem(spo2_str))
            self.table.setItem(row_idx, 7, QTableWidgetItem(measurement.origen))

        measurements_with_elapsed = self.history.get_measurements_with_elapsed()

        if measurements_with_elapsed:
            x_data = np.array([m.elapsed_s / 60.0 for m in measurements_with_elapsed], dtype=float)
            sys_data = np.array([m.sys for m in measurements_with_elapsed], dtype=float)
            dia_data = np.array([m.dia for m in measurements_with_elapsed], dtype=float)
            hr_data = np.array([m.hr for m in measurements_with_elapsed], dtype=float)

            self.curve_sys.setData(x_data, sys_data)
            self.curve_dia.setData(x_data, dia_data)
            self.curve_hr.setData(x_data, hr_data)
        else:
            self.curve_sys.clear()
            self.curve_dia.clear()
            self.curve_hr.clear()

            # Rangos fijos (se aplican siempre, con o sin datos)
        self.plot_item.vb.enableAutoRange(False)
        self.plot_item.vb.setXRange(0, max(self.programmed_therapy_minutes, 1), padding=0)
        self.plot_item.vb.setYRange(40, 200, padding=0)
        self.vb_hr.enableAutoRange(False)
        self.vb_hr.setYRange(40, 160, padding=0)

        self.lbl_count.setText(f"Total: {len(measurements)} mediciones")
    
    def set_programmed_duration(self, hours: int, minutes: int):
        """Establece la duración programada de la terapia para el rango del eje X."""
        self.programmed_therapy_minutes = hours * 60 + minutes
    
    def on_close_clicked(self):
        """Vuelve a la pantalla del baumanómetro."""
        if self.parent_window and hasattr(self.parent_window, "show_nibp_screen"):
            self.parent_window.show_nibp_screen()

