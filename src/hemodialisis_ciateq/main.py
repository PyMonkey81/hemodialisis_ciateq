# Archivo principal de arranque del HMI - CIATEQ A.C.
# Main HMI startup file - CIATEQ A.C.

import sys
import os
import logging
from logging.handlers import RotatingFileHandler  
import datetime
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QFont, QScreen, QIcon
from hemodialisis_ciateq.gui import theme_manager
from hemodialisis_ciateq.gui.appMainHemodialysis import HemodialysisHMI
from hemodialisis_ciateq.gui.theme_manager import ThemeManager


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


def resolve_app_icon_path() -> str:
    """Resolve icon path for development and PyInstaller builds."""
    candidates = [
        os.path.join(os.path.dirname(__file__), 'resources', 'images', 'icon.ico'),
        os.path.join(getattr(sys, '_MEIPASS', ''), 'resources', 'images', 'icon.ico'),
    ]
    for icon_path in candidates:
        if icon_path and os.path.exists(icon_path):
            return icon_path
    return ''

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
    """
    Adapta el tamaño de su widgwt central (HMI) a la resolución de la pantalla 
    mientras mantiene la relación de aspecto original del diseño

    QMainWindow that scales its central widget (the HMI) to fit the screen resolution
    while maintaining the original design aspect ratio.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background: #000000;")  # Base black background

        # Monitor resolution
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            screen_width, screen_height = 1920, 1080  
        else:
            geometry = screen.availableGeometry()
            screen_width = geometry.width()
            screen_height = geometry.height()

        DESIGN_WIDTH = 1920
        DESIGN_HEIGHT = 1080

        # Calculate scaling factor
        scale_factor = min(screen_width / DESIGN_WIDTH, screen_height / DESIGN_HEIGHT)

        # Create the main content widget (the Hemodialysis HMI)
        self.dialysis_hmi = HemodialysisHMI()
        self.dialysis_hmi.setFixedSize(DESIGN_WIDTH, DESIGN_HEIGHT)

        # Center the HMI on the screen
        self.dialysis_hmi.move(
            (screen_width - int(DESIGN_WIDTH * scale_factor)) // 2,
            (screen_height - int(DESIGN_HEIGHT * scale_factor)) // 2
        )

        self.setCentralWidget(self.dialysis_hmi)
        self.showFullScreen()

        logger.info(f"Scaled HMI: {int(DESIGN_WIDTH * scale_factor)}×{int(DESIGN_HEIGHT * scale_factor)} "
            f"(factor {scale_factor:.2f}x) on {screen_width}×{screen_height}")

if __name__ == "__main__":
    sys.excepthook = unhandled_exception_handler

    # ────────────────────────────────────────────────
    # HiDPI Configuration BEFORE QApplication creation
    # ────────────────────────────────────────────────
    QApplication.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)

    # Resolution fallback
    try:
        screen_instance = QGuiApplication.primaryScreen()
        if screen_instance is not None:
            geometry = screen_instance.availableGeometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
        else:
            raise AttributeError
    except Exception:
        try:
            # Fallback for Windows-specific resolution detection
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        except:
            screen_width, screen_height = 1920, 1080

    # Calculate scale factor for global QT_SCALE_FACTOR
    global_scale_factor = min(screen_width / 1920, screen_height / 1080)
    os.environ["QT_SCALE_FACTOR"] = f"{global_scale_factor:.2f}"

    # Only keep the rounding policy (this IS still valid)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough   # or .Round if preferred
        )

    app = QApplication(sys.argv)

    icon_path = resolve_app_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion")
    # Justo después de app = QApplication(sys.argv)
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

    theme_manager = ThemeManager(app)
    # Puedes cambiar fuente global y tema aquí:
    # theme_manager.apply_font("Arial Narrow", 16)
    theme_manager.apply_theme("dark")  # o "dark"
    theme_manager.apply_font(theme_manager.current_font_family, 16)

    try:
        main_window = ScaledHemodialysisHMI()
        if icon_path:
            main_window.setWindowIcon(QIcon(icon_path))
        main_window.showFullScreen()
        
        logger.info("=" * 70)
        logger.info("   CIATEQ A.C. - HEMODIALYSIS MACHINE HMI")
        logger.info("   FULLSCREEN MODE WITH DYNAMIC SCALING")
        logger.info(f"   Applied scaling factor: {global_scale_factor:.2f}x")
        logger.info("=" * 70)
        
        
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            logger.info("Application interrupted by user (KeyboardInterrupt). Exiting gracefully.")
            print("Application interrupted by user. Exiting gracefully.")
            app.quit()

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        QMessageBox.critical(
            None,
            "Fatal Application Error",
            f"Could not start the application:\n\n{e}\n\n"
            "Contacte al soporte técnico de CIATEQ A.C." 
        )
        sys.exit(1)