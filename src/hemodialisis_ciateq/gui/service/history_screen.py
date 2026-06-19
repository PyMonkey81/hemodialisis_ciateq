#gui/service/history_screen.py

"""Pantalla de consulta de historial de tratamientos realizados y mantenimientos
 realizados, con opción de exportar a PDF o CSV."""

from hemodialisis_ciateq.gui.components.floating_confirm import FloatingConfirmDialog   
from hemodialisis_ciateq.gui.components.floating_message import FloatingMessage


# gui/service/history_screen.py
"""
Pantalla de consulta de historial de tratamientos y limpiezas
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import json
import os
from datetime import datetime


class HistoryScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # HemodialysisHMI
        
        self.treatments = []
        self.cleanings = []
        self.current_filter = "Tratamientos"

        # Fondo claro
        self.setStyleSheet("""
            HistoryScreen {
                background-color: #f8fafc;
                color: #1e293b;
            }
        """)
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # ==================== TÍTULO ====================
        title = QLabel("Historial de Tratamientos y Mantenimientos")
        title.setStyleSheet("color: #1e293b; font-size: 36px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ==================== FILTRO Y TOTAL ====================
        filter_layout = QHBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Tratamientos", "Limpieza"])
        self.type_combo.setFixedWidth(220)
        self.type_combo.setFixedHeight(50)
        self.type_combo.setStyleSheet("color: #0f172a;font-size: 24px; padding: 2px;")
        self.type_combo.currentTextChanged.connect(self.on_filter_changed)

        self.load_button = QPushButton("Cargar Datos")
        self.load_button.setFixedSize(250, 50)
        self.load_button.setStyleSheet("""
            QPushButton { background: #2563eb; font-size:22px; color: #FFFFFF; }
            QPushButton:hover { background: #1e40af; }
            QPushButton:pressed { background: #b91c1c; }
        """)        
        self.load_button.clicked.connect(self.refresh_data)

        lbl_tipo_registro = QLabel("Tipo de Registro:")
        lbl_tipo_registro.setStyleSheet("font-size: 22px; color: #1e293b;")
        filter_layout.addWidget(lbl_tipo_registro)
        filter_layout.addWidget(self.type_combo)
        filter_layout.addWidget(self.load_button)
        filter_layout.addStretch()

        # Indicador de total de horas
        self.total_label = QLabel("Total de horas: 0.0 h")
        self.total_label.setStyleSheet("""
            QLabel { 
                background: #e0f2fe; 
                color: #1e40af; 
                font-size: 26px; 
                font-weight: bold; 
                padding: 5px 20px;
                border-radius: 8px;
            }
        """)
        self.total_label.setAlignment(Qt.AlignCenter)
        filter_layout.addWidget(self.total_label)

        main_layout.addLayout(filter_layout)

        # ==================== TABLA DENTRO DE SCROLL ====================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # scroll.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 1px;")
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #e0e0e5;
                width: 34px;
                margin: 0px 0px 0px 0px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical {
                background: #8a8a9c;
                min-height: 60px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b6b7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Fecha", 
            "Hora Inicio", 
            "Hora Fin", 
            "Tipo", 
            "Duración"
        ])
        # self.table.styleSheet("QHeaderView::section { background-color: #f1f5f9; color: #1e293b; font-size: 26px; padding: 2px; }")
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 16px;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        
        scroll.setWidget(self.table)
        main_layout.addWidget(scroll)

        # ==================== BOTONES INFERIORES ====================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.export_btn = QPushButton("Exportar a CSV")
        self.export_btn.setFixedHeight(80)
        self.export_btn.setFixedWidth(250)
        self.export_btn.setStyleSheet("""
            QPushButton { background: #2563eb; font-size: 22px; color: #FFFFFF; }
            QPushButton:hover { background: #1e40af; }
            QPushButton:pressed { background: #1e40af; }
        """)        
        self.export_btn.clicked.connect(self.export_to_csv)

        self.delete_btn = QPushButton("Eliminar Historial")
        self.delete_btn.setFixedHeight(80)
        self.delete_btn.setFixedWidth(250)
        self.delete_btn.setStyleSheet("""
            QPushButton { background: #991b1b; font-size: 22px; color: #FFFFFF; }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #b91c1c; }
        """)
        self.delete_btn.clicked.connect(self.confirm_delete_all)

        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

    def refresh_data(self):
        """Actualiza los datos desde el main window"""
        if self.parent_window:
            self.treatments = getattr(self.parent_window, 'treatment_history', [])
            self.cleanings = getattr(self.parent_window, 'cleaning_history', [])

        self.update_table()

    def on_filter_changed(self, text):
        self.current_filter = text
        self.update_table()

    def update_table(self):
        """Actualiza la tabla según el filtro seleccionado"""
        self.table.setRowCount(0)

        if self.current_filter == "Tratamientos":
            data = self.treatments
        else:
            data = self.cleanings

        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            items = [
                QTableWidgetItem(row_data.get("fecha", "")),
                QTableWidgetItem(row_data.get("hora_inicio", "")),
                QTableWidgetItem(row_data.get("hora_fin", "")),
                QTableWidgetItem(row_data.get("tipo_tratamiento", "")),
                QTableWidgetItem(row_data.get("duracion_hhmm", "00:00"))
            ]

            for col, item in enumerate(items):
                item.setForeground(QColor("#0f172a"))
                self.table.setItem(row, col, item)

        # Actualizar total de horas
        total_hours = sum(item.get("duracion_minutos", 0) for item in data) / 60.0
        self.total_label.setText(f"Total de horas: {total_hours:.1f} h")

    def export_to_csv(self):
        """Exporta los datos actuales a CSV"""
        if self.current_filter == "Tratamientos":
            data = self.treatments
            filename = f"historial_tratamientos_{datetime.now().strftime('%Y%m%d')}.csv"
        else:
            data = self.cleanings
            filename = f"historial_limpieza_{datetime.now().strftime('%Y%m%d')}.csv"

        if not data:
            self.parent_window.show_warning_message("No hay registros para exportar.", 2500)
            return

        try:
            import csv
            os.makedirs("exports", exist_ok=True)
            filepath = f"exports/{filename}"

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            self.parent_window.show_info_message(f"Archivo exportado correctamente:\n{filepath}", 2500)
            
        except Exception as e:
            self.parent_window.show_error_message(f"No se pudo exportar:\n{str(e)}", 2500)
            

    def confirm_delete_all(self):
        """Confirma antes de eliminar todo el historial"""
        dialog = FloatingConfirmDialog(self)
        msg = f"¿Estás seguro de eliminar TODO el historial de {self.current_filter}?\n\nEsta acción es irreversible."
        
        if dialog.show_confirm(msg, accept_text="Sí, Eliminar Todo", cancel_text="Cancelar"):
            if self.current_filter == "Tratamientos":
                self.treatments.clear()
                if self.parent_window:
                    self.parent_window.treatment_history = []
                    self.parent_window._save_treatment_history()
            else:
                self.cleanings.clear()
                if self.parent_window:
                    self.parent_window.cleaning_history = []
                    self.parent_window._save_cleaning_history()
            
            self.update_table()
            self.parent_window.show_success_message(f"Historial de {self.current_filter} eliminado correctamente.", 2500)
            