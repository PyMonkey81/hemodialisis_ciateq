# gui/components/tag_label.py
"""
Módulo para el widget `TagLabel`, un componente de etiqueta reutilizable.

Este módulo define una clase simple pero flexible para crear etiquetas de texto
estilizadas que pueden agruparse verticalmente. Es útil para mostrar valores,
estados o categorías con colores de fondo y texto personalizables, permitiendo
diferenciar visualmente la información crítica o agrupada en la interfaz HMI.

Características principales:
-----------------------------
- **Estilos Predefinidos**: Soporta temas de fondo básicos ('light', 'dark', 'default')
  para asegurar la legibilidad del texto en diferentes contextos de la interfaz.
- **Personalización de Texto**: Permite especificar el color del texto para cada
  etiqueta individualmente.
- **Agrupación Vertical**: Diseñado para apilar múltiples etiquetas verticalmente
  si se añaden secuencialmente, aunque comúnmente se usa para una sola etiqueta.
- **Gestión de Limpieza**: Incluye un método `clear()` para eliminar todas las
  etiquetas creadas, facilitando la actualización dinámica del contenido sin
  fugas de memoria visuales.

Clase principal:
----------------
- `TagLabel`: Widget contenedor que gestiona la creación y disposición
  de las etiquetas estilizadas.

Dependencias:
-------------
- `PySide6.QtWidgets`: `QWidget`, `QVBoxLayout`, `QLabel` para la estructura visual.
- `PySide6.QtCore`: `Qt` para alineación y constantes básicas.

Uso:
----
1.  **Instanciación**:
    `tag_widget = TagLabel(parent_widget)`
2.  **Añadir Etiqueta**:
    `tag_widget.add_tag("ERROR", "red", theme="light")`
    `tag_widget.add_tag("OK", "#00ff00", theme="dark")`
3.  **Limpiar**:
    `tag_widget.clear()` - Elimina todas las etiquetas para reutilizar el widget.
"""


from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
import logging
logger = logging.getLogger(__name__)


class TagLabel(QWidget):
    """
    Widget contenedor para etiquetas de texto estilizadas y apilables.

    Proporciona métodos convenientes para crear `QLabel`s con estilos CSS
    predefinidos (bordes redondeados, padding, fuentes negritas) y colores
    basados en temas simples.

    Args:
        parent (QWidget, optional): Widget padre.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def add_tag(self, text: str, text_color: str, theme: str = 'default') -> QLabel:
        """
        Create and add a styled label tag to the widget.

        Args:
            text: The text to display on the label.
            text_color: CSS color for the text (e.g., '#ffffff', 'red').
            theme: Background theme ('light', 'dark', or 'default').

        Returns:
            The created QLabel instance.
        """
        label = QLabel(text)

        # Background color based on theme
        if theme == 'light':
            bg_color = '#ffffff'
        elif theme == 'dark':
            bg_color = '#000000'
        else:
            bg_color = '#AEADC0'  # Default neutral gray

        # Unified style
        label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: {bg_color};
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)

        label.setAlignment(Qt.AlignCenter)

        # Add to layout
        self.layout.addWidget(label)

        return label

    def clear(self):
        """Remove all tags/labels from the widget."""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()