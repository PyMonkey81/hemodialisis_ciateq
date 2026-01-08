# tests/test_colores_rotos.py
import pytest

def test_colores_rotos_no_crashean(app, qtbot):
    from gui.appMainHemodialisis import HemodialisisHMI

    colores_rotos = [
        "blanco_magico", "", None, "xxxxxx", "#ZZZZZZ", "rgb(999,999,999)"
    ]

    ventana = HemodialisisHMI()
    qtbot.addWidget(ventana)

    for color in colores_rotos:
        try:
            ventana.lbl_estado.setStyleSheet(f"background: {color};")
        except:
            pytest.fail(f"Crasheó con color: {color}")

    assert True