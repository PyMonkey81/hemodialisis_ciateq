# # gui/components/ConductivityBar.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen

class ConductivityBar(QWidget):
    """
    Barra vertical de conductividad con muchas barras por zona
    → Cada zona dividida en 3 barras
    → Total: 21 barras
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Eliminamos restricciones fijas para permitir adaptabilidad
        # self.setFixedWidth(150) <-- Quitar esto permite que el padre decida el ancho
        
        # IMPORTANTE: Definir un tamaño mínimo razonable para evitar crash por geometría negativa
        self.setMinimumSize(100, 200) 

        self.min_value = 8.5
        self.max_value = 16.0
        self.value = 14.0

        # === ZONAS BASE ===
        self.base_colors = [
            "#9e0142", "#d53e4f", "#f46d43", "#fdae61",
            "#10b981", "#3288bd", "#dc2626"
        ]

        # === DIVIDIR CADA ZONA EN 3 BARRAS ===
        self.colors = []
        for color in self.base_colors:
            c = QColor(color)
            self.colors.append(c.darker(120))
            self.colors.append(c)
            self.colors.append(c.lighter(120))

        self.n_steps = len(self.colors)
        self._bar_solid_percent = 0.90
        self._background_color = QColor("#FCFCFC") #"#090c33" 
        self._padding = 18

    def setValue(self, value):
        try:
            v = float(value)
            # Ampliamos un poco el rango de seguridad de entrada
            if 0.0 <= v <= 20.0:
                if abs(v - self.value) > 0.01:
                    self.value = v
                    self.update()
        except:
            pass

    def paintEvent(self, event):
        w = self.width()
        h = self.height()

        # PROTECCIÓN CRÍTICA: Si el widget es muy pequeño, no dibujar para evitar crash
        if w <= 0 or h <= 180: 
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fondo oscuro
        painter.setBrush(self._background_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 10, 10)

        # Área de la barra
        # Usamos porcentajes o márgenes fijos seguros
        bar_x = self._padding + 10 
        bar_y = 60
        bar_width = w - 3 * self._padding
        
        # Aquí estaba el problema: si h < 170, esto daba negativo
        bar_height = h - 170 
        
        if bar_height <= 0: return # Doble seguridad

        step_size = bar_height / self.n_steps
        bar_height_step = step_size * self._bar_solid_percent

        # Calcular cuántas barras encender
        range_total = self.max_value - self.min_value
        if range_total == 0: range_total = 1 # Evitar div/0
        
        pc = max(0, min(1, (self.value - self.min_value) / range_total))
        steps_to_draw = int(pc * self.n_steps)
        steps_to_draw = max(0, min(self.n_steps, steps_to_draw))

        # Dibujar barras (de abajo hacia arriba)
        for i in range(steps_to_draw):
            color = QColor(self.colors[i])
            
            # Cálculo de Y corregido para asegurar float
            y_pos = bar_y + bar_height - ((i + 1) * step_size) + (step_size * (1 - self._bar_solid_percent) / 2)

            painter.setBrush(color)
            painter.setPen(QPen(color.darker(150), 3))
            
            # Asegurar dimensiones positivas y enteros para drawRoundedRect
            rh_w = max(1, int(bar_width))
            rh_h = max(1, int(bar_height_step))
            
            painter.drawRoundedRect(
                int(bar_x),
                int(y_pos),
                rh_w,
                rh_h,
                8, 8
            )

        # === Valor grande ===
        painter.setPen(QPen(QColor("#0f0f0f")))
        # Ajustar fuente según tamaño si es necesario, pero 38 está bien para >200px
        painter.setFont(QFont("Segoe UI", 38, QFont.Bold))
        painter.drawText(0, h - 100, w, 50, Qt.AlignCenter, f"{self.value:.2f}")

        # === Unidad ===
        painter.setPen(QPen(QColor("#203a4e")))
        painter.setFont(QFont("Segoe UI", 18))
        painter.drawText(0, h - 60, w, 40, Qt.AlignCenter, "mS/cm")

        # === Título ===
        painter.setPen(QPen(QColor("#141313")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(0, 30, w, 30, Qt.AlignCenter, "Conductividad")
        
        painter.end() # Buena práctica cerrar el painter explícitamente

    def sizeHint(self):
        # Sugerimos un tamaño ideal pero no forzamos
        return QSize(120, 452)
