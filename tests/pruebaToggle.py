import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame)
from PySide6.QtCore import Qt, Property, QEasingCurve, QPropertyAnimation, QPoint
from PySide6.QtGui import QPainter, QColor, QFont

# =============================================================================
# 1. LA CLASE DEL TOGGLE SWITCH (El componente)
# =============================================================================
class ToggleSwitch(QWidget):
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
        # self.toggled.emit(self._checked) 

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

# =============================================================================
# 2. LA APLICACIÓN DE PRUEBA (Visualización)
# =============================================================================
class DemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo Toggle Switch - PySide6")
        self.resize(400, 500)
        self.setStyleSheet("background-color: #1e293b; color: white;") # Fondo oscuro moderno

        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        lbl_titulo = QLabel("Configuración del Sistema")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Bold))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        layout.addSpacing(10)

        # --- SWITCH 1: BOMBA DE SANGRE (Verde) ---
        self.row1 = self.crear_fila("Bomba de Sangre", "#22c55e") # Verde
        layout.addLayout(self.row1)

        # --- SWITCH 2: MODO MANTENIMIENTO (Naranja) ---
        self.row2 = self.crear_fila("Modo Mantenimiento", "#f59e0b") # Naranja
        layout.addLayout(self.row2)

        # --- SWITCH 3: PARADA DE EMERGENCIA (Rojo) ---
        self.row3 = self.crear_fila("Deshabilitar Alarmas", "#ef4444") # Rojo
        layout.addLayout(self.row3)

        # Etiqueta de estado para feedback visual
        layout.addStretch()
        self.lbl_status = QLabel("Estado: Esperando acción...")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

    def crear_fila(self, texto, color_activo):
        """Ayudante para crear una fila con Texto + Switch"""
        h_layout = QHBoxLayout()
        
        lbl = QLabel(texto)
        lbl.setFont(QFont("Arial", 14))
        
        # Instanciamos nuestro widget personalizado
        switch = ToggleSwitch(active_color=color_activo)
        
        # Conectamos un evento "trucho" para ver que funciona el click
        # (Sobrescribimos el mouseReleaseEvent en la clase para simplificar el ejemplo,
        # pero en producción usaríamos señales)
        original_mouse_event = switch.mouseReleaseEvent
        
        def nuevo_evento(event):
            original_mouse_event(event) # Ejecutar la lógica original
            estado = "ACTIVADO" if switch.is_checked() else "DESACTIVADO"
            self.lbl_status.setText(f"{texto}: {estado}")
            self.lbl_status.setStyleSheet(f"color: {color_activo if switch.is_checked() else '#94a3b8'}; font-weight: bold;")

        switch.mouseReleaseEvent = nuevo_evento

        h_layout.addWidget(lbl)
        h_layout.addStretch() # Empujar el switch a la derecha
        h_layout.addWidget(switch)
        
        return h_layout

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DemoApp()
    ventana.show()
    sys.exit(app.exec())
