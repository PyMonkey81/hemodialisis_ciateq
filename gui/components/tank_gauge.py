# gui/components/tank_gauge.py



from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush

class TankGauge(QWidget):
    def __init__(self, titulo, min_val, max_val, unidad, color_liquido="#1640f9", parent=None):
        super().__init__(parent)
        self.titulo = titulo
        self.min_val = min_val
        self.max_val = max_val
        self.unidad = unidad
        self.color_liquido = QColor(color_liquido)
        self.val = min_val # Valor actual
        
        # Tamaño mínimo seguro
        self.setMinimumSize(100, 200)

    def setValue(self, valor):
        self.val = valor
        self.update()

    def paintEvent(self, event):
        # 1. PROTECCIÓN DE GEOMETRÍA 
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 150: # Si es muy pequeño, abortar dibujo
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 2. FONDO
        painter.fillRect(0, 0, w, h, QColor("#FCFCFC")) # Fondo oscuro panel "#090c33" <----- para cambio de fondo 

        # 3. CÁLCULOS DE GEOMETRÍA
        # Márgenes seguros
        margin_x = 40
        margin_top = 100
        margin_bottom = 60
        
        # Área del tanque
        tank_x = margin_x
        tank_y = margin_top
        tank_w = w - (margin_x * 2)
        tank_h = h - margin_top - margin_bottom

        # Protección extra por si el margen es mayor que el widget
        if tank_h <= 0 or tank_w <= 0:
            return

        # 4. DIBUJAR FONDO DEL TANQUE (Gris vacío)
        painter.setPen(QPen(QColor("#475569"), 6))
        painter.setBrush(QColor("#334155"))
        painter.drawRoundedRect(tank_x, tank_y, tank_w, tank_h, 10, 10)

        # 5. CÁLCULO DEL NIVEL DE LÍQUIDO
        rango = self.max_val - self.min_val
        if rango == 0: rango = 1 # Evitar división por cero
        
        # Clampear valor dentro del rango
        val_safe = max(self.min_val, min(self.max_val, self.val))
        
        pct = (val_safe - self.min_val) / rango
        fill_h = tank_h * pct
        
        # 6. DIBUJAR LÍQUIDO
        if fill_h > 0:
            painter.setBrush(self.color_liquido)
            # Dibujamos de abajo hacia arriba
            # Coordenada Y: (Base del tanque) - (Altura líquido)
            y_pos = (tank_y + tank_h) - fill_h
            
            # Usamos QRectF para precisión
            painter.drawRoundedRect(QRectF(float(tank_x), float(y_pos), float(tank_w), float(fill_h)), 10, 10)

        # 7. TEXTOS
        # Título
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Bold))
        painter.drawText(0, 15, w, 60, Qt.AlignCenter, self.titulo)

        # Valor
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(0, h - 110, w, 60, Qt.AlignCenter, f"{self.val:.1f}")
        
        # Unidad
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Segoe UI", 18))
        painter.drawText(0, h - 60, w, 40, Qt.AlignCenter, self.unidad)

    def sizeHint(self):
        return QSize(192, 451)

