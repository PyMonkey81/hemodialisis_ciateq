from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QSlider, QSpinBox, QLabel)
from PySide6.QtCore import Qt
import sys

class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alternativas a QDial")
        
        central = QWidget()
        layout = QVBoxLayout(central)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setValue(50)
        
        self.spin = QSpinBox()
        self.spin.setRange(0, 200)
        self.spin.setValue(50)
        self.spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #555;
                border-radius: 6px;
                padding-right: 30px;
                font-size: 16px;           /* también agranda el texto */
            }
    
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 35px;
                border-top-right-radius: 4px;
            }
    
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 35px;
                border-bottom-right-radius: 4px;
            }
    
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 18px;
                height: 18px;
            }
        """)
        
        label = QLabel("Valor: 50")
        
        layout.addWidget(QLabel("Slider:"))
        layout.addWidget(self.slider)
        layout.addWidget(QLabel("SpinBox:"))
        layout.addWidget(self.spin)
        layout.addWidget(label)
        
        # Sincronizar ambos
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(lambda v: label.setText(f"Valor: {v}"))
        
        self.setCentralWidget(central)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Ventana()
    win.show()
    sys.exit(app.exec())