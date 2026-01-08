import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import Qt

class LED(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(100, 100)
        self.state = 'off'  # Estado inicial

    def set_state(self, state):
        if state in ['on', 'off']:
            self.state = state
            self.update()  # Actualiza el widget para redibujar

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.state == 'on':
            painter.setBrush(QColor(0, 255, 0))  # Verde
        else:
            painter.setBrush(QColor(255, 0, 0))  # Rojo
        painter.drawEllipse(10, 10, 30, 30)  # Dibuja un círculo

class LEDApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LED Indicator")
        self.setGeometry(100, 100, 200, 200)

        # Crear un diseño vertical
        layout = QVBoxLayout(self)

        # Crear el LED
        self.led = LED()
        layout.addWidget(self.led)

        # Crear un botón para alternar el estado del LED
        self.button = QPushButton("Toggle LED", self)
        self.button.clicked.connect(self.toggle_led)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def toggle_led(self):
        # Alternar el estado del LED
        if self.led.state == 'on':
            self.led.set_state('off')
        else:
            self.led.set_state('on')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LEDApp()
    window.show()
    sys.exit(app.exec())
