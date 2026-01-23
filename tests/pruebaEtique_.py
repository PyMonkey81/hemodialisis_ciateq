from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class ValorSimple(QWidget):
    def __init__(self, titulo, valor="0.0", unidad="", es_critico=False):
        super().__init__()
        self.setFixedSize(180, 140)

        # Fondo y borde único para TODO el widget
        fondo = "#f1c30b" if es_critico else "#e9e9f8"
        borde_color = "#dc2626" if es_critico else "#64748b"   # ← cámbialo a #c9d0db si prefieres más claro

        self.setStyleSheet(f"""
            ValorSimple {{
                background: {fondo};
                border: 3px solid {borde_color};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        # Desactivamos fondo automático en TODOS los hijos
        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,2, 2, 10)
        layout.setSpacing(4)          # pequeño espacio entre título y valor
        layout.setAlignment(Qt.AlignCenter)

        # Título + unidad (arriba, centrado)
        texto_superior = f"{titulo} ({unidad})" if unidad else titulo
        self.lbl_superior = QLabel(texto_superior)
        self.lbl_superior.setAlignment(Qt.AlignCenter)
        self.lbl_superior.setStyleSheet("""
            color: #1e293b;
            font-size: 18px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self.lbl_superior)

        # Valor grande (centrado)
        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setAlignment(Qt.AlignCenter)
        self.lbl_valor.setStyleSheet("""
            color: #000000;
            font-size: 52px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self.lbl_valor)

    def setValor(self, valor):
        if isinstance(valor, (int, float)):
            # Puedes ajustar el formato de decimales aquí
            texto = f"{valor:.1f}" if valor >= 10 else f"{valor:.2f}"
        else:
            texto = str(valor)
        self.lbl_valor.setText(texto)


# ── Prueba rápida (sin cambios) ───────────────────────────────────────
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
    import sys

    app = QApplication(sys.argv)
    window = QMainWindow()
    central = QWidget()
    window.setCentralWidget(central)
    lay = QHBoxLayout(central)

    w1 = ValorSimple("Temp.", 36.8, "°C")
    lay.addWidget(w1)

    w2 = ValorSimple("Presión", 101.3, "kPa", es_critico=True)
    lay.addWidget(w2)

    w3 = ValorSimple("Humedad", 65, "%")
    lay.addWidget(w3)

    lay.addStretch()
    window.resize(800, 300)
    window.show()
    sys.exit(app.exec())