# tests/test_no_crash.py
import pytest
from PySide6.QtWidgets import QApplication
from gui.appMainHemodialisis import HemodialisisHMI

@pytest.fixture
def app(qtbot):
    app = QApplication.instance() or QApplication([])
    return app

def test_app_se_abre_sin_crash(app, qtbot):
    """Prueba crítica: que la app se abra aunque todo esté roto"""
    ventana = HemodialisisHMI()
    qtbot.addWidget(ventana)
    ventana.show()
    qtbot.waitExposed(ventana)
    assert ventana.isVisible()  # ← Si llega aquí → NO crasheó

def test_colores_invalidos_no_crashean(app, qtbot, monkeypatch):
    """Simula colores rotos, textos None, etc."""
    ventana = HemodialisisHMI()
    qtbot.addWidget(ventana)

    # Forzar colores inválidos
    ventana.colores = {
        "header_fondo": "color_que_no_existe",
        "estado_normal": None,
        "estado_alarma": "xxxxxx"
    }

    # Forzar textos None
    ventana.lbl_estado = None  # ¡¡Simula error grave!!
    ventana.actualizar_estado()  # ← debe sobrevivir

    assert True  # ← Si no crasheó → pasa la prueba