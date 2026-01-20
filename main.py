# Archivo principal de arranque del HMI - CIATEQ A.C.

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication
from gui.appMainHemodialisis import HemodialisisHMI

# try:    
#     ctypes.windll.shcore.SetProcessDpiAwareness(1)
# except Exception:    
#     ctypes.windll.user32.SetProcessDPIAware()


class ScaledHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  
        self.setStyleSheet("background: #000000;") #  <-------- COLOR FONDO     

        # === RESOLUCIÓN DEL MONITOR ===
        screen = QGuiApplication.primaryScreen()
        screen_w = screen.availableGeometry().width()
        screen_h = screen.availableGeometry().height()

        # === RESOLUCIÓN DE MONITOR ACTUAL ===
        DESIGN_W = 1920
        DESIGN_H = 1080
        # DESIGN_W = 2560
        # DESIGN_H = 1440
        # === FACTOR DE ESCALA (mantiene proporción) ===
        scale = min(screen_w / DESIGN_W, screen_h / DESIGN_H)

        # === CREA HMI ===
        self.hmi = HemodialisisHMI()
        self.hmi.setFixedSize(DESIGN_W, DESIGN_H)

        # === CENTRAR EN PANTALLA ===
        self.hmi.move(
            (screen_w - int(DESIGN_W * scale)) // 2,
            (screen_h - int(DESIGN_H * scale)) // 2
        )

        # === HACER QUE LA VENTANA SEA DEL TAMAÑO DEL MONITOR ===
        self.setCentralWidget(self.hmi)
        self.showFullScreen()

        print(f"HMI escalada: {int(DESIGN_W * scale)}×{int(DESIGN_H * scale)} "
              f"(factor {scale:.2f}x) en {screen_w}×{screen_h}")


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


if __name__ == "__main__":
    # === CAPTURAR ERRORES GLOBALES ===
    sys.excepthook = excepcion_no_manejada
    
    # Establecer escalado manual (ajusta según sea necesario)
    os.environ["QT_SCALE_FACTOR"] = "1"

    # ESCALADO DPI
    
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

 
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    

    try:
        # === CREAR VENTANA ESCALADA ===
        window = ScaledHMI()  # Usa la clase que creaste para el escalado.
        window.showFullScreen()  # Muestra en pantalla completa
        
        print("=" * 70)
        print("   CIATEQ A.C. - MÁQUINA DE HEMODIÁLISIS")
        print("   MODO FULLSCREEN CON ESCALADO")
        print("   SIN DISTORSIÓN - COMO MÁQUINA REAL")
        print("=" * 70)

        sys.exit(app.exec())

    except Exception as e:
        print(f"[FATAL] No se pudo iniciar el HMI: {e}")
        QMessageBox.critical(
            None, "Error Fatal",
            f"No se pudo iniciar la aplicación:\n\n{e}\n\n"
            "Contacte al soporte técnico de CIATEQ A.C."
        )
        sys.exit(1)
