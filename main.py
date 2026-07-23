# Archivo principal de arranque del HMI - CIATEQ A.C.
# Main HMI startup file - CIATEQ A.C.

import sys
import os
import logging
from logging.handlers import RotatingFileHandler  
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from gui import theme_manager
from gui.appMainHemodialysis import HemodialysisHMI
from gui.theme_manager import ThemeManager
from version import __version__
from utilities.platform_runtime import is_windows, load_platform_features


LOG_DIR = os.path.join(os.path.dirname(__file__), 'var', 'log')
os.makedirs(LOG_DIR, exist_ok=True)  # Crea la carpeta si no existe

LOG_FILE = os.path.join(LOG_DIR, 'hemodialisis.log')

# Configuracion del logger con rotación de archivos
max_log_size = 5 * 1024 * 1024  # 5 MB
backup_count = 2

# handler rotativo

handler = RotatingFileHandler(LOG_FILE, maxBytes=max_log_size, backupCount=backup_count, encoding='utf-8') 

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)

# logger central de toda la app
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)


def detect_screen_size() -> tuple[int, int]:
    """Detecta resolucion usando Qt; si no está disponible usa una resolución segura."""
    try:
        screen_instance = QGuiApplication.primaryScreen()
        if screen_instance is not None:
            geometry = screen_instance.availableGeometry()
            return geometry.width(), geometry.height()
    except Exception:
        pass

    return 1920, 1080

def unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Manejo de excepciones global de fallos inesperados de la aplicación 
    Muestra mensaje de error  crítico  y cierra la aplicación por seguridad 

    Global exception handler for unexpected application failures.
    Displays a critical error message and exits the application for safety.
    """
    if exc_type is KeyboardInterrupt:
        logger.info("KeyboardInterrupt recibido - cerrando aplicación de forma controlada")
        sys.exit(0)   # Salida limpia

    import traceback as tb
    error_message = "".join(tb.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled exception:\n{error_message}")
    
    app = QApplication.instance()
    if app:
        QMessageBox.critical(
            None,
            "Critical System Error - CIATEQ A.C.",
            "La aplicación ha fallado de forma inesperada.\n\n"
            "Se cerrará por seguridad.\n\n"
            "Detalles del error:\n\n" + error_message[-1000:],
            QMessageBox.Close
        )
    sys.exit(1)

class ScaledHemodialysisHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.DESIGN_WIDTH = 1920
        self.DESIGN_HEIGHT = 1080
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background: #000000;")
        
        # Widget principal del HMI
        self.dialysis_hmi = HemodialysisHMI()
        # IMPORTANTE: No fijar el tamaño aquí si queremos que sea flexible, 
        # o manejarlo en el resizeEvent.
        
        self.setCentralWidget(self.dialysis_hmi)
        self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_scaling()

    def apply_scaling(self):
        # Obtener el tamaño actual de la ventana (pantalla completa)
        screen_w = self.width()
        screen_h = self.height()

        # Calcular factor de escala manteniendo relación de aspecto
        scale_w = screen_w / self.DESIGN_WIDTH
        scale_h = screen_h / self.DESIGN_HEIGHT
        scale = min(scale_w, scale_h)

        new_width = int(self.DESIGN_WIDTH * scale)
        new_height = int(self.DESIGN_HEIGHT * scale)

        # Calcular márgenes para centrar el HMI si la pantalla no es 16:9
        margin_x = (screen_w - new_width) // 2
        margin_y = (screen_h - new_height) // 2

        # Ajustar el HMI (esto asume que dialysis_hmi es el widget central)
        # Si dialysis_hmi usa Layouts internos, se ajustará solo.
        self.dialysis_hmi.setFixedSize(new_width, new_height)
        self.dialysis_hmi.move(margin_x, margin_y)
        
        # Log para depuración
        logger.info(f"Escalado aplicado: {new_width}x{new_height} en pantalla {screen_w}x{screen_h}")


if __name__ == "__main__":
    sys.excepthook = unhandled_exception_handler

    platform_features = load_platform_features()
    logger.info("Platform: %s | Features: %s", sys.platform, platform_features)

    # Configuración HiDPI por plataforma.
    # En Windows mantenemos comportamiento legado para estabilidad de HMI fija.
    # En Linux dejamos que Qt/desktop gestionen HiDPI de forma nativa.
    use_windows_legacy_prescale = is_windows() and platform_features.get("enable_windows_legacy_prescale", True)
    if use_windows_legacy_prescale:
        os.environ["QT_SCALE_FACTOR"] = "1.0"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        logger.info("HiDPI mode: Windows legacy prescale activo")
    else:
        os.environ.pop("QT_SCALE_FACTOR", None)
        os.environ.pop("QT_AUTO_SCREEN_SCALE_FACTOR", None)
        os.environ.pop("QT_ENABLE_HIGHDPI_SCALING", None)
        logger.info("HiDPI mode: nativo de Qt/desktop")

    QApplication.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
    
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Palette oscura
    from PySide6.QtGui import QPalette, QColor
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor("#1e1e1e"))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor("#2b2b2b"))
    dark_palette.setColor(QPalette.AlternateBase, QColor("#353535"))
    dark_palette.setColor(QPalette.ToolTipBase, QColor("#2b2b2b"))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor("#4CAF50"))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    app.setPalette(dark_palette)

    # Theme
    theme_manager = ThemeManager(app)
    theme_manager.apply_theme("dark")
    theme_manager.apply_font(theme_manager.current_font_family, 16)

    # ==================== USAR LA CLASE CON ESCALADO ====================
    try:
        main_window = ScaledHemodialysisHMI()
        main_window.showFullScreen()

        logger.info("=" * 80)
        logger.info("   CIATEQ A.C. - HEMODIALYSIS HMI STARTED")
        logger.info(f"   Platform: {sys.platform} | Resolution: 1920x1080 (design)")
        logger.info(f"   Windows legacy prescale: {use_windows_legacy_prescale}")
        logger.info("=" * 80)

        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Fatal", str(e))
        sys.exit(1)
