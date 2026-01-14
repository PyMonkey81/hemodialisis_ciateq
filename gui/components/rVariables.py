# #gui/components/rVariables.py


from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QColor, QFont
from core.variables_map import VARIABLES, TVAR_TO_GROUP

class monitorVariables(QWidget):
    def __init__(self, parent=None, valores_dict=None, sistema_alarmas=None):
        super().__init__(parent)
        self.setStyleSheet("background: #f8fafc; font-family: 'Segoe UI';")

        # Guardamos referencia directa
        self.valores = valores_dict if valores_dict is not None else {}
        self.sistema_alarmas = sistema_alarmas

        layout = QVBoxLayout(self)

        titulo = QLabel("MONITOR DE VARIABLES - MÁQUINA HEMODIÁLISIS")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af; padding: 15px; background: #e0e7ff; border-radius: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        cols = ["#", "Grupo", "Nombre", "Tag", "Tipo", "Valor", "Límites", "Unidad", "Estado", "R/W"]
        self.tabla = QTableWidget(0, len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(False)
        
        self.tabla.setStyleSheet("""
        QTableWidget {
            gridline-color: #cbd5e1;
            font-size: 13px;
            background-color: #ffffff;
            alternate-background-color: #f1f5f9; /* Un gris muy suave alternado se ve mejor */
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
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Hacemos la columna Nombre y Tag un poco más anchas si es necesario
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # #
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Tag
        
        layout.addWidget(self.tabla)

        # Diccionario para mapear TAG -> (QTableWidgetItem Valor, QTableWidgetItem Estado, Nombre)
        self.celdas_referencia = {}
        
        self.construir_tabla() 

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_datos)
        self.timer.start(500) 

    def construir_tabla(self):
        """Crea todas las filas vacías al inicio."""
        self.tabla.setRowCount(0)
        idx = 0
        
        for grupo_key, vars_dict in VARIABLES.items():
            grupo = TVAR_TO_GROUP.get(grupo_key, f"0x{grupo_key:02X}")
            for addr, info in sorted(vars_dict.items(), key=lambda x: x[0]):
                nombre = info["name"]
                tag = info.get("tag", "N/A") # IMPORTANTE: Obtener TAG
                tipo = info["type"]
                rw = "R/W" if info.get("rw", False) else "R"
                unidad = info.get("unit", "")
                limites = info.get("limites")
                limites_str = f"{limites[0]}-{limites[1]}" if limites else "-"

                row = self.tabla.rowCount()
                self.tabla.insertRow(row)

                # Items estáticos
                self.tabla.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
                self.tabla.setItem(row, 1, QTableWidgetItem(grupo))
                self.tabla.setItem(row, 2, QTableWidgetItem(nombre))
                self.tabla.setItem(row, 3, QTableWidgetItem(tag)) # Mostramos el TAG también
                self.tabla.setItem(row, 4, QTableWidgetItem("DOUBLE" if tipo == "double" else "BOOL"))
                
                # Items dinámicos (Valor)
                item_valor = QTableWidgetItem("---")
                item_valor.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(row, 5, item_valor)

                self.tabla.setItem(row, 6, QTableWidgetItem(limites_str))
                self.tabla.setItem(row, 7, QTableWidgetItem(unidad))
                
                # Items dinámicos (Estado)
                item_estado = QTableWidgetItem("NORMAL")
                item_estado.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(row, 8, item_estado)

                self.tabla.setItem(row, 9, QTableWidgetItem(rw))

                # === CAMBIO CRÍTICO: LA CLAVE ES EL TAG ===
                # Guardamos: (Item Valor, Tipo de dato, Item Estado, Nombre para buscar alarmas)
                self.celdas_referencia[tag] = (item_valor, tipo, item_estado, nombre)
                
                idx += 1

    def actualizar_datos(self):
        """Solo actualiza los textos y colores usando el TAG como llave."""
        if not self.isVisible(): 
            return 

        alarmas = self.sistema_alarmas or (self.parent().sistema_alarmas if hasattr(self.parent(), 'sistema_alarmas') else None)

        # Iteramos sobre los TAGS que guardamos al construir
        for tag, (item_val, tipo, item_est, nombre_real) in self.celdas_referencia.items():
            
            # 1. Actualizar Valor (Usando el TAG para buscar en self.valores)
            raw_val = self.valores.get(tag, 0.0)
            
            if tipo == "double":
                texto = f"{raw_val:.3f}" # 3 decimales para precisión
            else:
                texto = "ON" if raw_val > 0 else "OFF"
            
            if item_val.text() != texto:
                item_val.setText(texto)

            # 2. Actualizar Estado (Alarmas usan NOMBRE, no TAG, según tu sistema actual)
            estado_texto = "NORMAL"
            bg_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)
            
            if alarmas:
                try:
                    # Las alarmas siguen usando el NOMBRE "Presión Arterial..."
                    if nombre_real in alarmas.nombres:
                        idx_alarma = alarmas.nombres.index(nombre_real)
                        if idx_alarma < len(alarmas.ultimo_estado) and alarmas.ultimo_estado[idx_alarma]:
                            estado_texto = "ALARM"
                            nivel = alarmas.niveles[idx_alarma]
                            
                            if nivel == "rojo":
                                bg_color = QColor(254, 205, 211)
                                text_color = QColor(127, 29, 29)
                            elif nivel == "amarillo":
                                bg_color = QColor(255, 255, 191)
                                text_color = QColor(120, 53, 15)
                            else: 
                                bg_color = QColor(220, 252, 255)
                                text_color = QColor(15, 66, 93)
                except:
                    pass

            if item_est.text() != estado_texto:
                item_est.setText(estado_texto)
                item_est.setBackground(bg_color)
                item_est.setForeground(text_color)
