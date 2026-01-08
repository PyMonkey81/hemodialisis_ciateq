# tests/stress_test.py
import pytest
from PySide6.QtWidgets import QApplication
from gui.appMainHemodialisis import HemodialisisHMI
import time

def test_estres_total_1000_veces(qtbot):
    for i in range(1000):
        print(f"[{i+1}/1000] Abriendo ventana...")
        
        ventana = HemodialisisHMI()
        qtbot.addWidget(ventana)
        
        # Mostrar sin bloquear
        ventana.show()
        qtbot.wait(50)  # 50ms para que se pinte
        
        print(f"[{i+1}/1000] Cerrando ventana...")
        ventana.close()  # → llama a closeEvent → detener_todo()
        
        # Forzar limpieza
        del ventana
        time.sleep(0.01)
    
    print("¡1000 VECES SIN CRASH! TU APP ES INDESTRUCTIBLE")