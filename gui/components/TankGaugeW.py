# gui/components/TankGaugeW.py



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
        painter.fillRect(0, 0, w, h, QColor("#00594c")) # Fondo oscuro panel "#090c33" <----- para cambio de fondo 

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
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(0, 15, w, 60, Qt.AlignCenter, self.titulo)

        # Valor
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(0, h - 110, w, 60, Qt.AlignCenter, f"{self.val:.1f}")
        
        # Unidad
        painter.setFont(QFont("Segoe UI", 18))
        painter.drawText(0, h - 60, w, 40, Qt.AlignCenter, self.unidad)

    def sizeHint(self):
        return QSize(192, 451)

# from PySide6.QtWidgets import QWidget
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QPainter, QColor, QFont, QPen


# class TankGauge(QWidget):
#     def __init__(self, title, min_val=0, max_val=100, unit="", color="#10b981", parent=None):
#         super().__init__(parent)
#         self.title = title
#         self.min_val = float(min_val)
#         self.max_val = float(max_val)
#         self.unit = unit
#         self.base_color = color
#         self.value = self.min_val

#         self.setFixedSize(150, 520)
#         self.setMinimumHeight(400)

#     def setValue(self, value):
#         try:
#             v = float(value)
#             if abs(v - self.value) > 0.05:
#                 self.value = max(self.min_val, min(self.max_val, v))
#                 self.update()
#         except:
#             pass

#     def paintEvent(self, event):
#         if self.width() <= 0 or self.height() < 100:
#             return 
#         # ================================

#         # p = QPainter(self)

#         p = QPainter(self)
#         p.setRenderHint(QPainter.Antialiasing)

#         w = self.width()
#         h = self.height()

#         # === Fondo oscuro ===
#         p.setBrush(QColor("#090c33"))
#         p.setPen(Qt.NoPen)
#         p.drawRoundedRect(0, 0, w, h, 10, 10)

#         # === Área del tanque (BAJADO PARA DEJAR ESPACIO AL TÍTULO) ===
#         margin = 30
#         tank_width = w - 2 * margin
#         tank_height = h - 200          # ← MÁS ESPACIO ARRIBA
#         tank_x = margin
#         tank_y = 90                    # ← BAJADO DE 70 A 90

#         # Fondo del tanque
#         p.setBrush(QColor("#1e293b"))
#         p.setPen(QPen(QColor("#475569"), 6))
#         p.drawRoundedRect(tank_x, tank_y, tank_width, tank_height, 10, 10)

#         # === Nivel de líquido (LIMITADO PARA NO SUBIR AL TÍTULO) ===
#         if self.max_val > self.min_val:
#             percent = (self.value - self.min_val) / (self.max_val - self.min_val)
#             fill_height = int(tank_height * percent)

#             # ← ¡AQUÍ ESTÁ LA CLAVE! → no llenar más allá del 95%
#             max_fill = tank_height - 20
#             fill_height = min(fill_height, max_fill)

#             if fill_height > 0:
#                 if self.value > self.max_val * 0.9:
#                     fill_color = "#dc2626"
#                 elif self.value > self.max_val * 0.75:
#                     fill_color = "#f97316"
#                 elif self.value < self.min_val * 0.25:
#                     fill_color = "#dc2626"
#                 else:
#                     fill_color = self.base_color

#                 p.setBrush(QColor(fill_color))
#                 p.setPen(Qt.NoPen)
#                 p.drawRoundedRect(
#                     tank_x + 6,
#                     tank_y + tank_height - fill_height + 6,
#                     tank_width - 12,
#                     fill_height - 12,
#                     10, 10
#                 )

#         # === TÍTULO ARRIBA (SIEMPRE VISIBLE) ===
#         p.setPen(QPen(QColor("#c3c9cf")))
#         p.setFont(QFont("Segoe UI", 14, QFont.Bold))
#         p.drawText(0, 15, w, 60, Qt.AlignCenter | Qt.TextWordWrap, self.title)

#         # === Valor grande abajo ===
#         p.setPen(QPen(QColor("#878e96")))
#         p.setFont(QFont("Segoe UI", 30, QFont.Bold))
#         p.drawText(0, h - 110, w, 60, Qt.AlignCenter, f"{self.value:.1f}")

#         # === Unidad ===
#         p.setPen(QPen(QColor("#d4d9df")))
#         p.setFont(QFont("Segoe UI", 18))
#         p.drawText(0, h - 60, w, 40, Qt.AlignCenter, self.unit)

#     def sizeHint(self):
#         return Qt.QSize(150, 450)