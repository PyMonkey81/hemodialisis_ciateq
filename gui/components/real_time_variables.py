# gui/components/real_time_variables_monitor.py
# Real-time variable monitoring table with alarm status indicators

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from core.variables_map import VARIABLES, TVAR_TO_GROUP

class RealTimeVariablesMonitor(QWidget):
    """
    Widget that displays a real-time table of all machine variables,
    including current values, limits, units, read/write access, and alarm status.
    Updates every 500 ms.
    """

    def __init__(self, parent=None, values_dict=None, alarm_system=None):
        super().__init__(parent)
        self.setStyleSheet("background: #f8fafc; font-family: 'Segoe UI';")

        # References
        self.values = values_dict if values_dict is not None else {}
        self.alarm_system = alarm_system

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("MONITOR DE VARIABLES - MÁQUINA HEMODIÁLISIS")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #1e40af; "
            "padding: 15px; background: #e0e7ff; border-radius: 10px;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Table columns (in Spanish as visible to user)
        columns = ["#", "Grupo", "Nombre", "Tag", "Tipo", "Valor", "Límites", "Unidad", "Estado", "R/W"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)

        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                font-size: 13px;
                background-color: #ffffff;
                alternate-background-color: #f1f5f9;
            }
            QTableWidget::item {
                background-color: #ffffff;
                color: #000000;
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QHeaderView::section {
                background: #1e40af;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # #
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Tag

        layout.addWidget(self.table)

        # Mapping: tag → (value_item, type, status_item, display_name)
        self.cell_references = {}

        self._build_table()

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(500)

    def _build_table(self):
        """Populate the table with all variables from VARIABLES map."""
        self.table.setRowCount(0)
        row_index = 0

        for group_key, vars_in_group in VARIABLES.items():
            group_name = TVAR_TO_GROUP.get(group_key, f"0x{group_key:02X}")

            for address, info in sorted(vars_in_group.items(), key=lambda x: x[0]):
                display_name = info["name"]
                tag = info.get("tag", "N/A")
                var_type = info["type"]
                read_write = "R/W" if info.get("rw", False) else "R"
                unit = info.get("unit", "")
                limits = info.get("limites")
                limits_str = f"{limits[0]}-{limits[1]}" if limits else "-"

                row = self.table.rowCount()
                self.table.insertRow(row)

                # Static columns
                self.table.setItem(row, 0, QTableWidgetItem(str(row_index + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(group_name))
                self.table.setItem(row, 2, QTableWidgetItem(display_name))
                self.table.setItem(row, 3, QTableWidgetItem(tag))
                self.table.setItem(row, 4, QTableWidgetItem("DOUBLE" if var_type == "double" else "BOOL"))

                # Dynamic: Value
                value_item = QTableWidgetItem("---")
                value_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 5, value_item)

                self.table.setItem(row, 6, QTableWidgetItem(limits_str))
                self.table.setItem(row, 7, QTableWidgetItem(unit))

                # Dynamic: Status
                status_item = QTableWidgetItem("NORMAL")
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, status_item)

                self.table.setItem(row, 9, QTableWidgetItem(read_write))

                # Store references using TAG as key
                self.cell_references[tag] = (value_item, var_type, status_item, display_name)

                row_index += 1

    def update_data(self):
        """Refresh value and alarm status columns."""
        if not self.isVisible():
            return

        # Fallback to parent's alarm_system if not directly provided
        alarm_system = self.alarm_system or (
            self.parent().alarm_system
            if hasattr(self.parent(), 'alarm_system') else None
        )

        for tag, (value_item, var_type, status_item, display_name) in self.cell_references.items():
            # 1. Update Value
            raw_value = self.values.get(tag, 0.0)

            if var_type == "double":
                display_text = f"{raw_value:.3f}"
            else:
                display_text = "ON" if raw_value > 0 else "OFF"

            if value_item.text() != display_text:
                value_item.setText(display_text)

            # 2. Update Status (based on alarm system using display_name)
            status_text = "NORMAL"
            bg_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)

            if alarm_system:
                try:
                    if display_name in alarm_system.display_names:
                        idx = alarm_system.display_names.index(display_name)
                        if idx < len(alarm_system.previous_states) and alarm_system.previous_states[idx]:
                            status_text = "ALARM"
                            level = alarm_system.severity_levels[idx]

                            if level == "rojo":
                                bg_color = QColor(254, 205, 211)
                                text_color = QColor(127, 29, 29)
                            elif level == "amarillo":
                                bg_color = QColor(255, 255, 191)
                                text_color = QColor(120, 53, 15)
                            else:
                                bg_color = QColor(220, 252, 255)
                                text_color = QColor(15, 66, 93)
                except Exception:
                    pass  # Silent fail if index out of range or attribute missing

            if status_item.text() != status_text:
                status_item.setText(status_text)
                status_item.setBackground(bg_color)
                status_item.setForeground(text_color)