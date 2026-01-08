#gui/components/ToggleSwitch.py

#import sys
from PySide6.QtWidgets import QWidget
# 1. AGREGAMOS Signal
from PySide6.QtCore import Qt, Property, QEasingCurve, QPropertyAnimation, Signal 
from PySide6.QtGui import QPainter, QColor

# =============================================================================
# TOGGLE SWITCH 
# =============================================================================
class ToggleSwitch(QWidget):
    
    toggled = Signal(bool)
    
    def __init__(self, parent=None, width=60, height=32, 
                 bg_color="#4b5563", active_color="#22c55e"):
        super().__init__(parent)
        
        # Configuración
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        
        # Estado interno
        self._checked = False
        self._bg_color = bg_color        # Gris oscuro (apagado)
        self._active_color = active_color # Color (encendido)
        self._circle_color = "#ffffff"   # Blanco (botón)
        
        # Animación
        self._circle_position = 4 # Margen inicial
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(300) # 300ms de animación

    # Propiedad necesaria para la animación
    @Property(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update() # Repintar el widget

    # Evento al hacer click (Ratón o Táctil)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mouseReleaseEvent(event)

    # Función lógica de cambio de estado
    def toggle(self):
        self._checked = not self._checked
        # Emitir señal manual si quisieras (aquí usamos lógica simple visual)
        self.start_transition(self._checked)
        # Disparamos un evento personalizado si es necesario (opcional)
        self.toggled.emit(self._checked) 
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.start_transition(checked)
            self.update()

    # Comprobar estado desde fuera
    def is_checked(self):
        return self._checked

    # Iniciar la animación
    def start_transition(self, state):
        self.animation.stop()
        if state:
            # Mover a la derecha
            self.animation.setEndValue(self.width() - self.height() + 4)
        else:
            # Mover a la izquierda
            self.animation.setEndValue(4)
        self.animation.start()

    # Dibujar el widget
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 1. Fondo
        current_bg = self._active_color if self._checked else self._bg_color
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(current_bg))
        p.drawRoundedRect(0, 0, self.width(), self.height(), self.height()/2, self.height()/2)

        # 2. Círculo
        p.setBrush(QColor(self._circle_color))
        radio = self.height() - 8 # Un poco más pequeño que el fondo
        p.drawEllipse(int(self._circle_position), 4, radio, radio)
        p.end()

