from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QProgressBar, QLabel
from PySide6.QtGui import QIntValidator

class NumericIndicatorApp(QWidget):
    def __init__(self):
        super().__init__()

        # Configurar la interfaz de usuario
        self.setWindowTitle("Numeric Input with Indicator")
        self.setGeometry(100, 100, 300, 200)

        # Crear un diseño vertical
        layout = QVBoxLayout(self)

        # Crear un campo de entrada QLineEdit solo para números
        self.numeric_input = QLineEdit(self)
        self.numeric_input.setValidator(QIntValidator(0, 100, self))
        self.numeric_input.setPlaceholderText("Enter a number (0-100)")
        
        # Crear una barra de progreso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)

        # Crear una etiqueta para mostrar el valor ingresado
        self.value_label = QLabel("Current Value: 0", self)

        # Conectar la entrada de texto con la función de actualización de progreso
        self.numeric_input.textChanged.connect(self.update_progress)

        # Añadir widgets al diseño
        layout.addWidget(self.numeric_input)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.value_label)

    def update_progress(self, text):
        # Convertir el texto ingresado a un número
        if text.isdigit():
            value = int(text)
            self.progress_bar.setValue(value)
            self.value_label.setText(f"Current Value: {value}")

if __name__ == "__main__":
    app = QApplication([])
    window = NumericIndicatorApp()
    window.show()
    app.exec()
