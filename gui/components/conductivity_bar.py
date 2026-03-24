# # gui/components/ConductivityBar.py

"""
Módulo para el widget de barra indicadora de conductividad.

Este módulo define la clase `ConductivityBar`, un componente gráfico
personalizado que representa el valor de conductividad de forma visual
y analógica mediante una serie de barras de colores que se encienden
progresivamente. Está diseñado para proporcionar una lectura rápida
y perceptible del nivel de conductividad dentro de un rango operativo
específico, con énfasis en la codificación por colores para indicar
diferentes zonas de valor.

Características principales:
-----------------------------
- **Visualización Gradual**: El nivel de conductividad se representa
  mediante el encendido secuencial de hasta 21 barras individuales,
  cada una con un color ligeramente diferente para crear un gradiente
  dentro de cada "zona" (ej. zonas verde, amarilla, roja).
- **Codificación por Colores**: Utiliza un conjunto predefinido de colores
  base (rojo, naranja, amarillo, verde, azul) para dividir el rango
  total de conductividad en zonas, facilitando la identificación de
  rangos críticos, operativos o seguros.
- **Renderizado Personalizado**: El dibujo de las barras, el fondo,
  el valor numérico y las unidades se realiza mediante `QPainter`,
  asegurando gráficos vectoriales nítidos.
- **Rango Configurable**: Aunque los colores están predefinidos, la
  barra opera sobre un `min_value` y `max_value` configurables para
  mapear el valor de conductividad real a la escala visual.
- **Robustez en el Dibujo**: Incluye protección para manejar casos donde
  el widget pueda ser demasiado pequeño, evitando errores de dibujo.
- **Actualización Dinámica**: El método `setValue()` actualiza el estado
  visual del componente eficientemente solo cuando el valor cambia
  significativamente.

Clase principal:
----------------
- `ConductivityBar`: Widget que encapsula la lógica de dibujo y la
  representación visual de la conductividad.

Dependencias:
-------------
- `PySide6.QtWidgets.QWidget`: Clase base para widgets.
- `PySide6.QtCore`: Tipos de datos básicos (`Qt`, `QSize`).
- `PySide6.QtGui`: Clases de pintura (`QPainter`, `QColor`, `QFont`, `QPen`).

Uso:
----
1.  **Instanciación**:
    `conductivity_display = ConductivityBar(parent_widget)`
    (Los rangos `min_value`, `max_value` y los colores están predefinidos
    en el constructor o pueden ser modificados directamente en la clase).
2.  **Actualización**:
    `conductivity_display.setValue(14.25)`  // El valor se dibujará y se actualizará la barra.
"""


from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen

class ConductivityBar(QWidget):
    """
    Widget de barra indicadora vertical para mostrar la conductividad.

    Visualiza el valor de conductividad mediante una serie de barras de colores
    que se iluminan progresivamente, divididas en zonas con distintos colores
    para indicar rangos específicos (ej. seguridad, advertencia, peligro).
    Cada "zona" principal se subdivide en tres barras con tonalidades ligeras
    y oscuras para crear un gradiente más suave.

    Args:
        parent (QWidget, optional): Widget padre.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
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

        bar_x = self._padding + 10 
        bar_y = 60
        bar_width = w - 3 * self._padding
        

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
        
        painter.end()

    def sizeHint(self):
        
        return QSize(120, 452)
