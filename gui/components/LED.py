# gui/components/led.py
# Simple LED indicator widget (on/off) with green/red circle

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor


class LED(QWidget):
    """
    Simple circular LED indicator widget.
    Displays green when 'on', red when 'off'.
    Used for status visualization in control panels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)

        # Internal state
        self._state = 'off'  # 'on' or 'off'

        # Colors (configurable if needed later)
        self._color_on = QColor(0, 255, 0)   # Green
        self._color_off = QColor(255, 0, 0)  # Red

    def set_state(self, state: str):
        """
        Set LED state ('on' or 'off') and trigger repaint if changed.
        """
        if state not in ('on', 'off'):
            return  # Invalid state → ignore silently

        if self._state != state:
            self._state = state
            self.update()  # Request repaint

    def get_state(self) -> str:
        """Return current LED state ('on' or 'off')."""
        return self._state

    def paintEvent(self, event):
        """Custom painting: draw colored circle with antialiasing."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Select color based on state
        color = self._color_on if self._state == 'on' else self._color_off

        # Draw filled circle (centered, 30px diameter)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(10, 10, 30, 30)  # Margen 10px para centrar

        painter.end()