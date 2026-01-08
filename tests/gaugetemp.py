from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QRect
import sys

class ThermometerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.temperature = 0  # Temperature value

    def set_temperature(self, value):
        self.temperature = value
        self.update()  # Trigger a redraw when temperature changes

    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width() / 4
        height = self.height()

        # Draw thermometer outline
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(width, 0, width*2, height)

        # Draw temperature level
        thermometer_height = (self.temperature / 100) * height  # Assuming temperature 0-100
        painter.setBrush(QColor(255, 0, 0))  # Red color for temperature level
        painter.drawRect(width, height - thermometer_height, width*2, thermometer_height)

        # Draw temperature text
        painter.setPen(Qt.black)
        painter.drawText(QRect(0, height - 30, self.width(), 30), Qt.AlignCenter, f"{self.temperature} °C")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thermometer = ThermometerWidget()
        self.setCentralWidget(self.thermometer)
        self.setWindowTitle("Thermometer Example")
        self.setGeometry(100, 100, 200, 400)

        # Set a temperature for demonstration
        self.thermometer.set_temperature(75)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
