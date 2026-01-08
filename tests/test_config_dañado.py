# tests/test_config_dañado.py
def test_config_dañado_no_crashea(tmp_path):
    import json
    from gui.appMainHemodialisis import HemodialisisHMI

    # Archivo JSON roto
    archivo = tmp_path / "colores.json"
    archivo.write_text('{"header_fondo": "rojo_sangre", "estado_normal": null}')

    # Forzar carga
    ventana = HemodialisisHMI()
    ventana.colores = ventana.cargar_colores(str(archivo))  # función que tengas

    assert ventana.isVisible()