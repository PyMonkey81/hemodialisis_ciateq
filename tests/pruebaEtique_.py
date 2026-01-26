# from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
# from PySide6.QtCore import Qt

# class ValorSimple(QWidget):
#     def __init__(self, titulo, valor="0.0", unidad="", es_critico=False):
#         super().__init__()
#         self.setFixedSize(180, 140)

#         # Fondo y borde único para TODO el widget
#         fondo = "#f1c30b" if es_critico else "#e9e9f8"
#         borde_color = "#dc2626" if es_critico else "#64748b"   # ← cámbialo a #c9d0db si prefieres más claro

#         self.setStyleSheet(f"""
#             ValorSimple {{
#                 background: {fondo};
#                 border: 3px solid {borde_color};
#                 border-radius: 10px;
#             }}
#             QLabel {{
#                 background: transparent;
#                 border: none;
#             }}
#         """)

#         # Desactivamos fondo automático en TODOS los hijos
#         self.setAutoFillBackground(False)

#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(12,2, 2, 10)
#         layout.setSpacing(4)          # pequeño espacio entre título y valor
#         layout.setAlignment(Qt.AlignCenter)

#         # Título + unidad (arriba, centrado)
#         texto_superior = f"{titulo} ({unidad})" if unidad else titulo
#         self.lbl_superior = QLabel(texto_superior)
#         self.lbl_superior.setAlignment(Qt.AlignCenter)
#         self.lbl_superior.setStyleSheet("""
#             color: #1e293b;
#             font-size: 18px;
#             font-weight: bold;
#             background: transparent;
#         """)
#         layout.addWidget(self.lbl_superior)

#         # Valor grande (centrado)
#         self.lbl_valor = QLabel(str(valor))
#         self.lbl_valor.setAlignment(Qt.AlignCenter)
#         self.lbl_valor.setStyleSheet("""
#             color: #000000;
#             font-size: 52px;
#             font-weight: bold;
#             background: transparent;
#         """)
#         layout.addWidget(self.lbl_valor)

#     def setValor(self, valor):
#         if isinstance(valor, (int, float)):
#             # Puedes ajustar el formato de decimales aquí
#             texto = f"{valor:.1f}" if valor >= 10 else f"{valor:.2f}"
#         else:
#             texto = str(valor)
#         self.lbl_valor.setText(texto)


# # ── Prueba rápida (sin cambios) ───────────────────────────────────────
# if __name__ == '__main__':
#     from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
#     import sys

#     app = QApplication(sys.argv)
#     window = QMainWindow()
#     central = QWidget()
#     window.setCentralWidget(central)
#     lay = QHBoxLayout(central)

#     w1 = ValorSimple("Temp.", 36.8, "°C")
#     lay.addWidget(w1)

#     w2 = ValorSimple("Presión", 101.3, "kPa", es_critico=True)
#     lay.addWidget(w2)

#     w3 = ValorSimple("Humedad", 65, "%")
#     lay.addWidget(w3)

#     lay.addStretch()
#     window.resize(800, 300)
#     window.show()
#     sys.exit(app.exec())

import sys
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QFrame, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class MonitorSerial(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Monitor Serial PySide6")
        self.resize(120, 100)

        # Widget central de la ventana
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal de la ventana
        main_layout = QVBoxLayout(central_widget)

        # --- CREACIÓN DEL FRAME PERSONALIZADO ---
        self.sensor_frame = QFrame()
        
        # Estilo para que se vea el marco (borde, fondo, radio)
        self.sensor_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #8b0000;
                border-radius: 10px;
            }
        """)
        
        # Layout vertical dentro del frame
        frame_layout = QVBoxLayout(self.sensor_frame)

        # 1. Etiqueta de Título/Unidad (Estática)
        self.lbl_unidad = QLabel("TEMPERATURA (°C)")
        self.lbl_unidad.setAlignment(Qt.AlignCenter)
        self.lbl_unidad.setStyleSheet("border: none; color: #333; font-weight: bold;")
        
        # 2. Etiqueta de Valor (Dinámica)
        self.lbl_valor = QLabel("--.--")
        self.lbl_valor.setAlignment(Qt.AlignCenter)
        # Fuente más grande para el valor
        font_valor = QFont("Arial", 24, QFont.Bold)
        self.lbl_valor.setFont(font_valor)
        self.lbl_valor.setStyleSheet("border: none; color: #0078d7;")

        # Añadir etiquetas al layout del frame
        frame_layout.addWidget(self.lbl_unidad)
        frame_layout.addWidget(self.lbl_valor)

        # Añadir el frame al layout principal
        main_layout.addWidget(self.sensor_frame)
        
        # --- SIMULACIÓN DE PUERTO SERIAL ---
        # En tu caso real, aquí conectarías la lógica de PySerial
        self.timer = QTimer()
        self.timer.timeout.connect(self.leer_datos_serial_simulado)
        self.timer.start(1000) # Actualizar cada 1 segundo

    def leer_datos_serial_simulado(self):
        """
        Simula la lectura de un dato. 
        Aquí pondrías tu código: serial.readline(), etc.
        """
        valor_simulado = random.uniform(20.0, 35.0)
        texto_valor = f"{valor_simulado:.2f}"
        
        # Actualizamos la etiqueta del valor
        self.lbl_valor.setText(texto_valor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorSerial()
    window.show()
    sys.exit(app.exec())
