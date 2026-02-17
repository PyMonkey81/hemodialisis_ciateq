# # Archivo principal de arranque del HMI - CIATEQ A.C.
# Main HMI startup file - CIATEQ A.C.

import sys
import os
import logging
import datetime
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QFont, QScreen
from gui.appMainHemodialisis import HemodialysisHMI # Changed class name here


LOG_DIR = os.path.join(os.path.dirname(__file__), 'var', 'log')
os.makedirs(LOG_DIR, exist_ok=True)  # Crea la carpeta si no existe

LOG_FILE = os.path.join(LOG_DIR, 'hemodialisis_hmi.log')

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    filemode='a'  # 'a' para append, no sobreescribe cada vez
)
logger = logging.getLogger(__name__)

def unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for unexpected application failures.
    Displays a critical error message and exits the application for safety.
    """
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
            screen_width, screen_height = 1920, 1080  # fallback
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
    app.setStyle("Fusion")

    # Global font (optional but recommended for consistency)
    base_font = QFont("Arial Narrow", 14)
    base_font.setWeight(QFont.Bold)
    app.setFont(base_font)

    # Global style (uncomment and adjust as needed)
    app.setStyleSheet("""
        * {
            font-family: "Arial Narrow", "Helvetica Condensed", Arial, sans-serif;
            font-weight: bold;
            color: #000000;
        }
        QLabel { font-size: 18px; }
        QLineEdit,
        ClickableLineEdit {
            font-family: Consolas, "Courier New", monospace;
            font-size: 20px;
            color: #000000;
            border: 2px solid #000000;
            border-radius: 6px;
            padding: 4px;
            min-width: 80px;
        }

        /* Normal background (editable) */
        QLineEdit:!read-only,
        ClickableLineEdit:!read-only {
            background: #FFFFE5;
        }

        /* Read-only background */
        QLineEdit:read-only,
        ClickableLineEdit:read-only,
        ClickableLineEdit[readOnly="true"] {
            background: #FFFFE5;           /* desired yellow */
            color: #000000;
            border: 2px solid #000000;
        }

        /* Optional: when focused (even if read-only) */
        QLineEdit:focus,
        ClickableLineEdit:focus {
            border: 2px solid #3b82f6;
        }
                      
        QPushButton {
            background: #3b82f6;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            padding: 6px;
            font-weight: bold;
        }
        QPushButton:pressed { background: #1e40af; }
        QWidget { background: #fcfcfc; }
    """)

    try:
        main_window = ScaledHemodialysisHMI()
        main_window.showFullScreen()
        
        logger.info("=" * 70)
        logger.info("   CIATEQ A.C. - HEMODIALYSIS MACHINE HMI")
        logger.info("   FULLSCREEN MODE WITH DYNAMIC SCALING")
        logger.info(f"   Applied scaling factor: {global_scale_factor:.2f}x")
        logger.info("=" * 70)
        
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        QMessageBox.critical(
            None,
            "Fatal Application Error",
            f"Could not start the application:\n\n{e}\n\n"
            "Contacte al soporte técnico de CIATEQ A.C." # Kept in Spanish as requested
        )
        sys.exit(1)

