# tests/test_widgets_exist.py

from gui.appMainHemodialisis import HemodialisisHMI

def test_todos_los_widgets_existen(app, qtbot):
    ventana = HemodialisisHMI()
    qtbot.addWidget(ventana)

    widgets_criticos = [
        ventana.lbl_estado,
        ventana.lbl_alarmas,
        ventana.lbl_pantalla_actual,
        ventana.lbl_fecha_hora,
        ventana.gauge_art,
        ventana.gauge_ven,
        ventana.powbar,
        ventana.stacked,
    ]

    for w in widgets_criticos:
        assert w is not None
        assert w.isVisible() or w.isHidden()  # solo que exista