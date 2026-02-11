# #gui/components/LED.py
# import sys
# from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout,  QLabel
# from PySide6.QtGui import QColor, QPainter
# from PySide6.QtCore import Qt

# class LED(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setFixedSize(50, 50)
#         self.state = 'off'  # Estado inicial

#     def set_state(self, state):
#         if state in ['on', 'off']:
#             self.state = state
#             self.update()  # Actualiza el widget para redibujar

#     def paintEvent(self, event):
#         painter = QPainter(self)
#         if self.state == 'on':
#             painter.setBrush(QColor(0, 255, 0))  # Verde
#         else:
#             painter.setBrush(QColor(255, 0, 0))  # Rojo
#         painter.drawEllipse(10, 10, 30, 30)  # Dibuja un círculo

# gui/components/LED.py
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout,  QLabel
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import Qt

class LED(QWidget):
    # --- CORRECCIÓN CLAVE AQUÍ ---
    # Añadir 'parent=None' al constructor para aceptar el widget padre
    def __init__(self, parent=None): 
        # Pasar 'parent' a la llamada al constructor de la clase base QWidget
        super().__init__(parent) 
        self.setFixedSize(50, 50)
        self.state = 'off'  # Estado inicial

    def set_state(self, state):
        if state in ['on', 'off']:
            # También podrías añadir un check para evitar repintados innecesarios
            if self.state != state: 
                self.state = state
                self.update()  # Actualiza el widget para redibujar

    def get_state(self):
        """Método añadido para compatibilidad con el código de actualización."""
        return self.state

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Suavizado para el círculo
        if self.state == 'on':
            painter.setBrush(QColor(0, 255, 0))  # Verde
        else:
            painter.setBrush(QColor(255, 0, 0))  # Rojo
        painter.drawEllipse(10, 10, 30, 30)  # Dibuja un círculo




