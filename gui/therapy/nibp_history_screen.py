# gui/therapy/nibp_history_screen.py
"""
Pantalla de historial de mediciones de presión arterial (NIBP) para una sesión de terapia.
- Gráfica pyqtgraph con sistólica (rojo), diastólica (azul), FC (verde)
- Tabla con todas las mediciones incluyendo las "antes" (sin elapsed_s)
- Botón para volver a la pantalla del baumanómetro
"""

import logging
from os import name
from typing import Optional
from PySide6.QtWidgets import (
    QGridLayout, QWidget, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

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
        
        # Márgenes DPI-aware
        dpi = self.logicalDpiX() / 96.0
        margen = int(16 * max(dpi, 1.0))
        main.setContentsMargins(margen, margen, margen, margen)
        main.setSpacing(10)
        
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
        
        main.addLayout(header_layout, 0, 0, 1, 4)
        
        # ─── GRÁFICA ───────────────────────────────────────────────────
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#ffffff")
        self.plot_widget.hideButtons()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.plot_item = self.plot_widget.plotItem
        self.plot_item.setLabel("left", "mmHg", color="#0f172a")
        self.plot_item.setLabel("bottom", "", color="#0f172a")
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        
        # Configurar eje izquierdo
        left_axis = self.plot_item.getAxis("left")
        left_axis.enableAutoSIPrefix(False)
        left_axis.setPen(pg.mkPen("#0f172a"))
        left_axis.setTextPen(pg.mkPen("#0f172a"))
        left_axis.setStyle(tickTextOffset=7)
        left_axis.setWidth(110)

     
        # Configurar eje inferior
        bottom_axis = self.plot_item.getAxis("bottom")
        bottom_axis.enableAutoSIPrefix(False)
        bottom_axis.setPen(pg.mkPen("#0f172a"))
        bottom_axis.setTextPen(pg.mkPen("#0f172a"))
        bottom_axis.setStyle(tickTextOffset=6)
        
        self.plot_item.hideAxis("top")
        self.plot_item.hideAxis("right")
        self.plot_item.vb.setBorder(pg.mkPen("#0f172a", width=1))



        # ViewBox con rangos fijos
        self.plot_item.vb.setBackgroundColor("#ffffff")
        self.plot_item.vb.enableAutoRange(False)
        self.plot_item.vb.setYRange(40, 200, padding=0)
        self.plot_item.vb.setXRange(0, max(self.programmed_therapy_minutes, 1), padding=0)
        

        # Crear las tres curvas
        self.curve_sys = self.plot_widget.plot(
            [], [], pen=pg.mkPen("#dc2626", width=2),
            symbol="o", symbolSize=7, symbolBrush="#dc2626", name="Sistólica",
        )
        self.curve_dia = self.plot_widget.plot(
            [], [], pen=pg.mkPen("#2563eb", width=2),
            symbol="o", symbolSize=7, symbolBrush="#2563eb", name="Diastólica",
        )
        self.curve_hr = self.plot_widget.plot(
            [], [], pen=pg.mkPen("#15803d", width=2),
            symbol="o", symbolSize=7, symbolBrush="#15803d", name="FC (lpm)",
        )

        # Leyenda flotante dentro de la cuadrícula
        legend = pg.LegendItem(offset=(8, 8))
        legend.setParentItem(self.plot_item.vb)
        legend.addItem(self.curve_sys, "Sistólica")
        legend.addItem(self.curve_dia, "Diastólica")
        legend.addItem(self.curve_hr, "FC (lpm)")
        legend.setBrush(pg.mkBrush(255, 255, 255, 230))
        legend.setPen(pg.mkPen("#cbd5e1"))

        # Agregar plot a la fila 1, columnas 0-1
        main.addWidget(self.plot_widget, 1, 0, 1, 2)
        
        # ─── LABEL DEL EJE X (separado) ───────────────────────────────
        lbl_x_axis = QLabel("Minutos de Terapia")
        lbl_x_axis.setStyleSheet("font-size: 13px; color: #0f172a; font-weight: normal;")
        lbl_x_axis.setAlignment(Qt.AlignCenter)
        
        # Agregar label en fila 2, columnas 0-1 (solo bajo la gráfica)
        main.addWidget(lbl_x_axis, 2, 0, 1, 2)
        
        # ─── TABLA ─────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No.", "Tiempo", "SYS", "DIA", "MAP", "FC", "SpO2", "Origen"
        ])
        
        # Estilos de la tabla
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
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Agregar tabla en fila 3, 4 columnas
        main.addWidget(self.table, 3, 0, 1, 4)
        
        # ─── PIE DE PÁGINA ─────────────────────────────────────────────
        footer_layout = QHBoxLayout()
        self.lbl_count = QLabel("Total: 0 mediciones")
        self.lbl_count.setStyleSheet("font-size: 14px; color: #0f172a;")
        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch()
        
        # Agregar pie en fila 4, 4 columnas
        main.addLayout(footer_layout, 4, 0, 1, 4)

        # ─── CONFIGURAR STRETCH FACTORS ────────────────────────────────
        # Columnas: igual stretch para 0, 1, 2, 3
        main.setColumnStretch(0, 1)
        main.setColumnStretch(1, 1)
        main.setColumnStretch(2, 1)
        main.setColumnStretch(3, 1)
        
        # Filas: gráfica 3, tabla 2
        main.setRowStretch(0, 0)  # Encabezado: auto
        main.setRowStretch(1, 3)  # Gráfica: 3 partes
        main.setRowStretch(2, 0)  # Label eje X: auto
        main.setRowStretch(3, 2)  # Tabla: 2 partes
        main.setRowStretch(4, 0)  # Footer: auto
        
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

        self.lbl_count.setText(f"Total: {len(measurements)} mediciones")
    
    def set_programmed_duration(self, hours: int, minutes: int):
        """Establece la duración programada de la terapia para el rango del eje X."""
        self.programmed_therapy_minutes = hours * 60 + minutes
    
    def on_close_clicked(self):
        """Vuelve a la pantalla del baumanómetro."""
        if self.parent_window and hasattr(self.parent_window, "show_nibp_screen"):
            self.parent_window.show_nibp_screen()
