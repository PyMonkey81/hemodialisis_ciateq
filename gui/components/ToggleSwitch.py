# gui/components/toggle_switch.py
# Animated toggle switch widget for on/off controls (touch-friendly)

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Property, QEasingCurve, QPropertyAnimation, Signal
from PySide6.QtGui import QPainter, QColor


class ToggleSwitch(QWidget):
    """
    Animated toggle switch widget (on/off) with smooth transition.
    Emits 'toggled' signal when state changes.
    Supports programmatic control via setChecked() and is_checked().
    """

    # Signal emitted when the toggle state changes (True = on, False = off)
    toggled = Signal(bool)

    def __init__(self,
                 parent=None,
                 width: int = 60,
                 height: int = 32,
                 bg_color: str = "#4b5563",       # Off background (gray)
                 active_color: str = "#22c55e"):  # On background (green)
        super().__init__(parent)

        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        # Internal state
        self._is_checked = False
        self._bg_color_off = bg_color
        self._bg_color_on = active_color
        self._circle_color = "#ffffff"  # White circle

        # Animation setup
        self._circle_x = 4  # Initial left margin
        self.animation = QPropertyAnimation(self, b"circle_x", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(300)  # 300ms smooth transition

    # Property for animation binding
    @Property(float)
    def circle_x(self):
        return self._circle_x

    @circle_x.setter
    def circle_x(self, value: float):
        self._circle_x = value
        self.update()  # Trigger repaint

    def mouseReleaseEvent(self, event):
        """Toggle state on left click/touch release."""
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mouseReleaseEvent(event)

    def toggle(self):
        """Toggle current state and start animation."""
        self.setChecked(not self._is_checked)

    def setChecked(self, checked: bool):
        """Programmatically set toggle state with animation."""
        if self._is_checked == checked:
            return

        self._is_checked = checked
        self.animation.stop()

        end_value = self.width() - self.height() + 4 if checked else 4
        self.animation.setEndValue(end_value)
        self.animation.start()

        self.toggled.emit(checked)
        self.update()

    def is_checked(self) -> bool:
        """Return current toggle state."""
        return self._is_checked

    def paintEvent(self, event):
        """Custom painting of background and animated circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Background (rounded rect)
        current_bg = self._bg_color_on if self._is_checked else self._bg_color_off
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(current_bg))
        painter.drawRoundedRect(0, 0, self.width(), self.height(),
                                self.height() // 2, self.height() // 2)

        # 2. Circle (animated position)
        painter.setBrush(QColor(self._circle_color))
        circle_radius = self.height() - 8
        painter.drawEllipse(int(self._circle_x), 4, circle_radius, circle_radius)

        painter.end()