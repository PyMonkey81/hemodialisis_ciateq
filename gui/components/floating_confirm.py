# gui/components/floating_confirm.py
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEventLoop, Signal
from PySide6.QtGui import QFont


class FloatingConfirmDialog(QWidget):
    """Diálogo flotante de confirmación moderno y estable"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._result = False
        self._event_loop = None
        self._animation = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(25)

        self.frame = QFrame()
        self.frame.setObjectName("confirmFrame")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setSpacing(20)

        # Texto
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        frame_layout.addWidget(self.label)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(25)

        self.btn_accept = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")

        for btn in (self.btn_accept, self.btn_cancel):
            btn.setFixedHeight(70)
            btn.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        self.btn_accept.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: #ffffff;
                border-radius: 12px; padding: 12px 40px;
            }
            QPushButton:hover { background-color: #059669; }
        """)

        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: #ffffff;
                border-radius: 12px; padding: 12px 40px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_accept)
        frame_layout.addLayout(btn_layout)

        layout.addWidget(self.frame)

        # Estilo general
        self.setStyleSheet("""
            #confirmFrame {
                background-color: #1a3561;
                border: 3px solid #1a3561;
                border-radius: 18px;
            }
            QLabel {
                    background: transparent;
                    color: #ffffff;
                    font-size: 22px;                     
                    font-weight: bold; }
        """)

        self.btn_accept.clicked.connect(self._on_accept)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def show_confirm(self, text: str, accept_text="Sí, Resetear", cancel_text="Cancelar") -> bool:
        """Muestra el diálogo de forma modal y retorna True si se aceptó"""
        self._result = False
        self.label.setText(text)
        
        self.btn_accept.setText(accept_text)
        self.btn_cancel.setText(cancel_text)

        # Ajustar tamaño
        self.adjustSize()
        # self.setFixedWidth(max(self.width() + 50, 1000))
        self.setFixedWidth(1000)

        # Centrar en la pantalla padre
        # parent_rect = self.parent().rect()
        # x = (parent_rect.width() - self.width()) // 2
        # y = (parent_rect.height() - self.height()) // 2 - 80

                # Centrar correctamente usando coordenadas globales del padre
        if self.parent():
            # Obtener el punto 0,0 del padre en coordenadas de la pantalla global
            global_pos = self.parent().mapToGlobal(self.parent().rect().topLeft())
            
            x = global_pos.x() + (self.parent().width() - self.width()) // 2
            y = global_pos.y() + (self.parent().height() - self.height()) // 2 - 80
            self.move(x, y)

        self.show()
        self.fade_in()

        # === EVENT LOOP MODAL (forma correcta) ===
        self._event_loop = QEventLoop()
        self._event_loop.exec()

        return self._result

    def _on_accept(self):
        self._result = True
        self._close_dialog()

    def _on_cancel(self):
        self._result = False
        self._close_dialog()

    def _close_dialog(self):
        self._animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._animation.setDuration(250)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.finished.connect(self._finish_close)
        self._animation.start()

    def _finish_close(self):
        if self._event_loop and self._event_loop.isRunning():
            self._event_loop.quit()
        self.deleteLater()

    def fade_in(self):
        self.setWindowOpacity(0.0)
        self._animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._animation.setDuration(300)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.start()