# gui/components/tag_label.py
# Reusable labeled tag widget with theme-aware styling

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class TagLabel(QWidget):
    """
    Simple reusable widget to display a labeled tag/value with customizable text color
    and background based on theme (light/dark/default).
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