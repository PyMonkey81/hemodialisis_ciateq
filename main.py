# # Archivo principal de arranque del HMI - CIATEQ A.C.

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QFont, QScreen
from gui.appMainHemodialisis import HemodialisisHMI


def excepcion_no_manejada(tipo, valor, traceback):
    import traceback as tb
    error_msg = "".join(tb.format_exception(tipo, valor, traceback))
    print(error_msg)

    app = QApplication.instance()
    if app:
        QMessageBox.critical(
            None,
            "Error Crítico - CIATEQ A.C.",
            "La aplicación ha fallado inesperadamente.\n\n"
            "Se cerrará por seguridad.\n\n"
            "Detalles del error:\n\n" + error_msg[-1000:],
            QMessageBox.Close
        )
    sys.exit(1)


class ScaledHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background: #000000;")  # Fondo negro base

        # Resolución del monitor
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            screen_w, screen_h = 1920, 1080  # fallback
        else:
            geo = screen.availableGeometry()
            screen_w = geo.width()
            screen_h = geo.height()

        DESIGN_W = 1920
        DESIGN_H = 1080

        scale = min(screen_w / DESIGN_W, screen_h / DESIGN_H)

        # Crear el contenido principal
        self.hmi = HemodialisisHMI()
        self.hmi.setFixedSize(DESIGN_W, DESIGN_H)

        # Centrar
        self.hmi.move(
            (screen_w - int(DESIGN_W * scale)) // 2,
            (screen_h - int(DESIGN_H * scale)) // 2
        )

        self.setCentralWidget(self.hmi)
        self.showFullScreen()

        print(f"HMI escalada: {int(DESIGN_W * scale)}×{int(DESIGN_H * scale)} "
              f"(factor {scale:.2f}x) en {screen_w}×{screen_h}")


if __name__ == "__main__":
    sys.excepthook = excepcion_no_manejada

    # ────────────────────────────────────────────────
    # Configuración HiDPI ANTES de crear QApplication
    # ────────────────────────────────────────────────
    QApplication.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)

  # Fallback para resolución
    try:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            screen_w = geo.width()
            screen_h = geo.height()
        else:
            raise AttributeError
    except Exception:
        try:
            user32 = ctypes.windll.user32
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
        except:
            screen_w, screen_h = 1920, 1080

    scale = min(screen_w / 1920, screen_h / 1080)
    os.environ["QT_SCALE_FACTOR"] =  f"{scale:.2f}"

   
    # Solo dejamos la política de redondeo (esta SÍ sigue siendo válida)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough   # o .Round si prefieres
        )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Fuente global (opcional pero recomendado para consistencia)
    base_font = QFont("Arial Narrow", 14)
    base_font.setWeight(QFont.Bold)
    app.setFont(base_font)

    # Estilo global (descomenta y ajusta según necesites)
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

        /* Fondo normal (editable) */
        QLineEdit:!read-only,
        ClickableLineEdit:!read-only {
            background: #FFFFE5;
        }

        /* Fondo cuando está read-only  */
        QLineEdit:read-only,
        ClickableLineEdit:read-only,
        ClickableLineEdit[readOnly="true"] {
            background: #FFFFE5;           /* tu amarillo deseado */
            color: #000000;
            border: 2px solid #000000;
        }

        /* Opcional: cuando tiene foco (aunque sea read-only) */
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
        window = ScaledHMI()
        window.showFullScreen()

        print("=" * 70)
        print("   CIATEQ A.C. - MÁQUINA DE HEMODIÁLISIS")
        print("   MODO FULLSCREEN CON ESCALADO DINÁMICO")
        print(f"   Factor de escala aplicado: {scale:.2f}x")
        print("=" * 70)

        sys.exit(app.exec())

    except Exception as e:
        print(f"[FATAL] No se pudo iniciar el HMI: {e}")
        QMessageBox.critical(
            None,
            "Error Fatal",
            f"No se pudo iniciar la aplicación:\n\n{e}\n\n"
            "Contacte al soporte técnico de CIATEQ A.C."
        )
        sys.exit(1)