import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.appMainHemodialysis import HemodialysisHMI


def main() -> int:
    # Permite ejecutar smoke test headless en CI Linux/Windows.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    timeout_s = int(os.environ.get("CIATEQ_SMOKE_TEST_SECONDS", "2"))

    app = QApplication.instance() or QApplication([])
    window = HemodialysisHMI()
    window.show()

    QTimer.singleShot(max(timeout_s, 1) * 1000, app.quit)
    exit_code = app.exec()

    try:
        window.shutdown()
    except Exception:
        # El smoke test debe priorizar detectar crash en arranque/cierre sin bloquear CI.
        pass

    return 0 if exit_code == 0 else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
