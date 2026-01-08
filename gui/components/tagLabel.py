
#gui/components/tagLabel.py

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout,  QLabel
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import Qt

class CustomLabel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    def crear_etiqueta(self, texto, color_texto, tema):
        """Crea una etiqueta con texto y color de texto basados en un tema."""
        lbl = QLabel(texto)
        
        # Define color de fondo según el tema
        if tema == 'light':
            fondo_color = '#ffffff'
        elif tema == 'dark':
            fondo_color = '#000000'
        else:
            fondo_color = "#AEADC0"  # Color por defecto para otro tema
        
        # Configurar el estilo de la etiqueta
        lbl.setStyleSheet(f"color: {color_texto}; background-color: {fondo_color}; padding: 5px;")
        
        # Añadir la etiqueta al layout
        self.layout.addWidget(lbl)