# gui/therapy/main_screen.py
# Home / Welcome screen displayed at startup (stacked index 0)

"""
Pantalla de inicio / bienvenida de la interfaz HMI.

Este módulo define la clase `MainScreen`, que representa la vista inicial
que se muestra al arrancar la aplicación o cuando el sistema está en estado
de reposo/desconectado. Su función principal es informativa y de presentación
de marca.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer
import logging
from _version import __version__
logger = logging.getLogger(__name__)


class ClickableLabel(QLabel):
    """Label clickeable con long-press (2 segundos) para cerrar."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
        self.close_callback = None
        self.parent_window = None
        
        # Timer para detectar long press
        self.long_press_timer = QTimer()
        self.long_press_timer.timeout.connect(self._on_long_press)
        self.long_press_timer.setSingleShot(True)
        self.long_press_duration = 2000  # 2 segundos en ms
    
    def mousePressEvent(self, event):
        # Iniciar timer de 2 segundos
        self.long_press_timer.start(self.long_press_duration)
    
    def mouseReleaseEvent(self, event):
        # Si se suelta antes de 2 segundos, no hacer nada
        if self.long_press_timer.isActive():
            self.long_press_timer.stop()
    
    def _on_long_press(self):
        """Ejecuta después de 2 segundos de presión."""
        if self.close_callback:
            self.close_callback()


class MainScreen(QWidget):
    """
    Widget principal de bienvenida de la máquina de hemodiálisis.

    Esta clase hereda de QWidget y se encarga de renderizar la pantalla "Home"
    (índice 0 en el QStackedWidget principal).

    Características:
    ----------------
    - **Identidad Visual:** Muestra el nombre del dispositivo ("MÁQUINA DE HEMODIÁLISIS")
      y el nombre del modelo/marca ("Yeztli").
    - **Información Técnica:** Presenta la versión del software actual y la entidad
      desarrolladora (CIATEQ A.C.).
    - **Diseño:** Utiliza un diseño limpio con fondo degradado suave y tipografía
      grande para facilitar la lectura a distancia.
    - **Layout:** Organiza los elementos verticalmente (QVBoxLayout) con espaciado
      y alineación centrada.

    Atributos Públicos:
    -------------------
    No expone métodos públicos complejos ni señales, ya que es una pantalla estática.
    """


    def __init__(self, parent=None):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.parent_window = parent
        self.setup_ui()
    
    def _show_shutdown_dialog(self):
        """Muestra diálogo de confirmación de apagado con mensaje variable según fase."""
        try:
            from gui.components.floating_confirm import FloatingConfirmDialog
            from core.state_manager import TreatmentPhase
            
            if not self.parent_window:
                return
            
            # Determinar el mensaje según la fase actual
            current_phase = getattr(self.parent_window.state, 'current_phase', None) if hasattr(self.parent_window, 'state') else None
            
            if current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.CLEANING):
                texto = "Hay un tratamiento en curso.\nApagar lo detiene."
            else:
                texto = "¿Apaga el sistema?"
            
            # Crear y mostrar el diálogo
            dialog = FloatingConfirmDialog(self.parent_window or self)
            aceptado = dialog.show_confirm(
                texto,
                accept_text="Apagar",
                cancel_text="Cancelar",
            )
            
            if aceptado:
                # Si el usuario confirma, llamar a close()
                if hasattr(self.parent_window, 'close'):
                    self.parent_window.close()
        except Exception as e:
            # Si el diálogo falla, no lanzar la excepción
            logger.error(f"Error mostrando diálogo de apagado: {e}")

    def setup_ui(self):
        # Soft gradient background
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #f1f5f9, stop:1 #f1f5f9);
            border-radius: 15px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.addStretch(2)

        # Main title
        title_label = QLabel("MÁQUINA DE HEMODIÁLISIS")
        title_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #000000;
            background: transparent;
            padding: 20px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Subtitle / Brand (clickeable con long-press para cerrar)
        subtitle_label = ClickableLabel("Yeztli")
        subtitle_label.setStyleSheet("""
            font-size: 60px;
            font-weight: bold;
            color: #782E44;
            background: transparent;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.parent_window = self.parent_window
        subtitle_label.close_callback = self._show_shutdown_dialog
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacing(40)

        # Information block
        info_label = QLabel(
            "<div style='line-height: 180%;'>"
            "<span style='font-size: 20px; color: #1e293b;'><b>Equipo desarrollado por</b></span><br>"
            "<span style='font-size: 32px; color: #1e293b; font-weight: bold;'>CIATEQ A.C.</span><br><br>"
            "<span style='font-size: 20px; color: #1e293b;'><b>Versión Software:</b> </span>"
            f"<span style='font-size: 24px; color: #1e293b; font-weight: bold;'>{__version__}</span><br><br>"
            "<span style='font-size: 22px; color: #1e293b; font-weight: bold;'>"
            "Sistema de Hemodiálisis"
            "</span>"
            "</div>"
        )
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)

        info_label.setStyleSheet("""
            QLabel {
                background: #f1f5f9;
                padding: 50px;
                border-radius: 25px;
                border: 3px solid #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        info_label.setMaximumWidth(1400)

        main_layout.addWidget(info_label, alignment=Qt.AlignCenter)

        main_layout.addStretch(3)
        logger.info("MainScreen initialized successfully.")