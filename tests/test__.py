import sys
from PySide6.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, 
                               QPushButton, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt

class PantallaEsquema(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esquema Gráficos y Datos")
        self.resize(1000, 700)

        # Layout Principal (La cuadrícula maestra)
        grid = QGridLayout(self)
        grid.setSpacing(10) # Espacio entre cuadritos

        # =======================================================
        # COLUMNA 0: LOS GRÁFICOS
        # =======================================================
        
        # GRÁFICO 1:
        # Fila: 0, Col: 0, Alto: 4 filas, Ancho: 1 col
        # (Cubre a la izquierda de Dato 1, 2, 3 y 4)
        lbl_grafico1 = self.crear_caja("GRÁFICO 1\n(Presión, etc.)", "#0ea5e9")
        grid.addWidget(lbl_grafico1, 0, 0, 4, 1)

        # GRÁFICO 2:
        # Fila: 4, Col: 0, Alto: 3 filas, Ancho: 1 col
        # (Cubre a la izquierda de Dato 5, 6 y los Botones)
        lbl_grafico2 = self.crear_caja("GRÁFICO 2\n(Flujo, etc.)", "#0284c7")
        grid.addWidget(lbl_grafico2, 4, 0, 3, 1)

        # =======================================================
        # COLUMNA 1 y 2: LOS DATOS
        # =======================================================
        
        # Fila 0
        grid.addWidget(self.crear_dato("Dato 1"), 0, 1)
        grid.addWidget(self.crear_dato("Dato 7"), 0, 2)

        # Fila 1
        grid.addWidget(self.crear_dato("Dato 2"), 1, 1)
        grid.addWidget(self.crear_dato("Dato 8"), 1, 2)

        # Fila 2
        grid.addWidget(self.crear_dato("Dato 3"), 2, 1)
        grid.addWidget(self.crear_dato("Dato 9"), 2, 2)

        # Fila 3
        grid.addWidget(self.crear_dato("Dato 4"), 3, 1)
        grid.addWidget(self.crear_dato("Dato 10"), 3, 2)

        # Fila 4 (Aquí empieza al lado del Gráfico 2)
        grid.addWidget(self.crear_dato("Dato 5"), 4, 1)
        grid.addWidget(self.crear_dato("Dato 11"), 4, 2)

        # Fila 5
        grid.addWidget(self.crear_dato("Dato 6"), 5, 1)
        grid.addWidget(self.crear_dato("Dato 12"), 5, 2)

        # =======================================================
        # FILA 6: LOS 5 BOTONES (FUSIONADO)
        # =======================================================
        
        # 1. Creamos un contenedor (Frame) para agrupar los botones
        contenedor_botones = QFrame()
        contenedor_botones.setStyleSheet("background: #e2e8f0; border-radius: 8px;")
        
        # 2. Le ponemos un Layout Horizontal interno
        layout_botones = QHBoxLayout(contenedor_botones)
        layout_botones.setContentsMargins(5, 5, 5, 5)
        
        # 3. Agregamos los 5 botones al contenedor
        for i in range(1, 6):
            btn = QPushButton(f"Btn {i}")
            btn.setMinimumHeight(50)
            btn.setStyleSheet("background: #475569; color: white; font-weight: bold;")
            layout_botones.addWidget(btn)

        # 4. Agregamos el contenedor al Grid Principal
        # Fila: 6, Col: 1, Alto: 1, Ancho: 2 (Ocupa col 1 y 2)
        grid.addWidget(contenedor_botones, 6, 1, 1, 2)

        # =======================================================
        # AJUSTE DE TAMAÑOS (Estética)
        # =======================================================
        # Hacemos que la columna de los gráficos sea más ancha (proporción 2)
        # Y las de datos un poco más estrechas (proporción 1)
        grid.setColumnStretch(0, 2) 
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

    def crear_caja(self, texto, color):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"background: {color}; color: white; border: 2px solid #333; font-weight: bold;")
        return lbl

    def crear_dato(self, texto):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background: white; border: 1px solid #ccc; padding: 10px;")
        return lbl

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PantallaEsquema()
    ventana.show()
    sys.exit(app.exec())
