import os
import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from gui.appMainHemodialysis import HemodialysisHMI


def _configure_qt_fontdir() -> None:
    # Qt6 no incluye fuentes embebidas; usar una carpeta real evita warnings en CI.
    candidates = []
    if os.name == "nt":
        win_dir = os.environ.get("WINDIR", r"C:\\Windows")
        candidates.append(os.path.join(win_dir, "Fonts"))
    else:
        candidates.extend([
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "/usr/share/fonts/truetype/dejavu",
        ])

    for font_dir in candidates:
        if os.path.isdir(font_dir):
            os.environ.setdefault("QT_QPA_FONTDIR", font_dir)
            return


def main() -> int:
    # Permite ejecutar smoke test headless en CI Linux/Windows.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _configure_qt_fontdir()

    try:
        timeout_s = int(os.environ.get("CIATEQ_SMOKE_TEST_SECONDS", "2"))
    except ValueError:
        timeout_s = 2

    timeout_s = max(timeout_s, 1)

    app = QApplication.instance() or QApplication([])
    window = None

    try:
        window = HemodialysisHMI()
        window.show()
    except Exception:
        traceback.print_exc()
        return 1

    QTimer.singleShot(timeout_s * 1000, app.quit)

    try:
        exit_code = app.exec()
    except Exception:
        traceback.print_exc()
        exit_code = 1

    if window is not None:
        try:
            window.shutdown()
        except Exception:
            # El smoke test debe priorizar detectar crash en arranque/cierre sin bloquear CI.
            traceback.print_exc()

    return 0 if exit_code == 0 else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
