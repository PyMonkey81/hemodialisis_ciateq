# gui/components/ConductivityBar.py
# Barra VERTICAL de Conductividad (12.0 – 16.0 mS/cm)
# Estilo profesional, moderno y 100% funcional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient


class ConductivityBar(QWidget):
    """
    Medidor vertical de conductividad para hemodiálisis
    Rango: 12.0 – 16.0 mS/cm
    Zonas: rojo / naranja / verde
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 500)          # ancho fijo, alto generoso
        self.setMinimumHeight(400)

        self.value = 14.0
        self.min_value = 12.0
        self.max_value = 16.0

        # Colores por zona
        self.color_low     = QColor("#dc2626")   # < 13.0 o > 16.0
        self.color_warning  = QColor("#f97316")   # 13.0–13.5 y 15.5–16.0
        self.color_good    = QColor("#10b981")   # 13.5–15.5
        self.color_bg      = QColor("#1e293b")
        self.color_border  = QColor("#475569")
        self.color_text    = QColor("#e2e8f0")

    def setValue(self, value):
        try:
            v = float(value)
            if 10 <= v <= 18:  # rango razonable
                if abs(v - self.value) > 0.01:
                    self.value = v
                    self.update()
        except:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        margin = 25
        bar_width = w - 2 * margin
        bar_height = h - 100  # dejamos espacio arriba/abajo para texto
        bar_x = margin
        bar_y = 80

        # === Fondo del widget ===
        painter.setBrush(QColor("#0f172a"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 20, 20)

        # === Barra de fondo (gris oscuro) ===
        painter.setBrush(self.color_bg)
        painter.setPen(QPen(self.color_border, 6))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 20, 20)

        # === Relleno según valor (de abajo hacia arriba) ===
        range_val = self.max_value - self.min_value
        percent = max(0, min(100, (self.value - self.min_value) / range_val * 100))
        fill_height = int(bar_height * percent / 100)

        # Color dinámico
        if self.value < 13.0 or self.value > 16.0:
            fill_color = self.color_low
        elif 13.0 <= self.value < 13.5 or 15.5 < self.value <= 16.0:
            fill_color = self.color_warning
        else:
            fill_color = self.color_good

        if fill_height > 0:
            gradient = QLinearGradient(bar_x, bar_y + bar_height - fill_height,
                                     bar_x, bar_y + bar_height)
            gradient.setColorAt(0, fill_color.lighter(130))
            gradient.setColorAt(1, fill_color.darker(140))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                bar_x, bar_y + bar_height - fill_height,
                bar_width, fill_height,
                20, 20
            )

        # === Marcas de escala (12, 13, 14, 15, 16) ===
        painter.setPen(QPen(QColor("#94a3b8"), 4))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))

        for val in [12, 13, 14, 15, 16]:
            y = bar_y + bar_height - int(bar_height * (val - self.min_value) / range_val)
            painter.drawLine(bar_x - 15, y, bar_x + 5, y)
            painter.setPen(QPen(QColor("#e2e8f0")))
            painter.drawText(8, y + 6, f"{val:.0f}")

        # === Valor actual (grande) ===
        painter.setPen(QPen(QColor("white")))
        painter.setFont(QFont("Segoe UI", 36, QFont.Bold))
        text = f"{self.value:.2f}"
        painter.drawText(0, bar_y + bar_height + 70, w, 40,
                        Qt.AlignCenter, text)

        # === Unidad ===
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.setFont(QFont("Segoe UI", 18))
        painter.drawText(0, bar_y + bar_height + 105, w, 30,
                        Qt.AlignCenter, "mS/cm")

        # === Título ===
        painter.setPen(QPen(QColor("#e2e8f0")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(0, 30, w, 30, Qt.AlignCenter, "Conductividad")
