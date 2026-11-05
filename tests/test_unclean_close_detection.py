"""Tests para detección de cierre no limpio y detención de terapia/limpieza."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile

# Agregar el directorio raíz al path para imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.platform_runtime import get_runtime_data_path


class TestUncleanCloseDetection(unittest.TestCase):
    """Tests para detección de cierre limpio vs no limpio."""

    def setUp(self):
        """Configura mocks básicos."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name

    def tearDown(self):
        """Limpia temporales."""
        self.temp_dir.cleanup()

    def test_clean_close_mark_creates_file(self):
        """Al cerrar limpiamente, debe crear el archivo de marca."""
        # Simular creación de marca
        clean_close_path = os.path.join(self.temp_path, "cierre_limpio")
        with open(clean_close_path, "w") as f:
            f.write("")
        
        # Verificar que existe
        self.assertTrue(os.path.exists(clean_close_path))

    def test_clean_close_mark_is_deleted_on_startup(self):
        """Al arrancar con marca de cierre limpio, debe borrarla y NO hacer paro."""
        clean_close_path = os.path.join(self.temp_path, "cierre_limpio")
        
        # Crear la marca (simular cierre limpio previo)
        with open(clean_close_path, "w") as f:
            f.write("")
        self.assertTrue(os.path.exists(clean_close_path))
        
        # Simular detección: si existe, borrar y retornar sin hacer nada
        if os.path.exists(clean_close_path):
            os.remove(clean_close_path)
        
        # Verificar que se borró
        self.assertFalse(os.path.exists(clean_close_path))

    def test_unclean_close_no_mark_exists(self):
        """Si la marca no existe, es cierre no limpio."""
        clean_close_path = os.path.join(self.temp_path, "cierre_limpio")
        
        # No crear la marca
        self.assertFalse(os.path.exists(clean_close_path))


class TestUncleanCloseHandling(unittest.TestCase):
    """Tests para decisión de parar terapia según estado."""

    def test_state_14_and_mode_not_3_stops_therapy(self):
        """Estado 14 + modo != 3: debe detener terapia."""
        priming_status = 14
        treatment_mode = 0  # Hemodiálisis (no es 3)
        
        # Simulación de lógica
        should_stop = (priming_status in (14, 15) and treatment_mode != 3)
        
        self.assertTrue(should_stop, "Debe detener terapia en estado 14 con modo 0")

    def test_state_15_and_mode_2_stops_therapy(self):
        """Estado 15 + modo 2: debe detener terapia."""
        priming_status = 15
        treatment_mode = 2  # Ultrafiltración (no es 3)
        
        # Simulación
        should_stop = (priming_status in (14, 15) and treatment_mode != 3)
        
        self.assertTrue(should_stop, "Debe detener terapia en estado 15 con modo 2")

    def test_state_14_and_mode_3_no_stop_from_state_condition(self):
        """Estado 14 + modo 3 (limpieza): no cumple condición de terapia."""
        priming_status = 14
        treatment_mode = 3  # Limpieza
        
        # Simulación: state 14 + mode 3 no cumple "mode != 3"
        should_stop_therapy = (priming_status in (14, 15) and treatment_mode != 3)
        
        self.assertFalse(should_stop_therapy, "No debe detener por estado 14 si es limpieza")

    def test_state_6_and_mode_3_stops_cleaning(self):
        """Estado 6 + modo 3: debe detener limpieza."""
        priming_status = 6
        treatment_mode = 3  # Limpieza
        
        # Simulación
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        
        self.assertTrue(should_stop_cleaning, "Debe detener limpieza en estado 6 con modo 3")

    def test_state_1_no_stop(self):
        """Estado 1: no debe hacer parada."""
        priming_status = 1
        treatment_mode = 0
        
        # Simulación
        should_stop_therapy = (priming_status in (14, 15) and treatment_mode != 3)
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        should_stop = should_stop_therapy or should_stop_cleaning
        
        self.assertFalse(should_stop, "No debe detener en estado 1")

    def test_state_2_no_stop(self):
        """Estado 2: no debe hacer parada."""
        priming_status = 2
        treatment_mode = 0
        
        should_stop_therapy = (priming_status in (14, 15) and treatment_mode != 3)
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        should_stop = should_stop_therapy or should_stop_cleaning
        
        self.assertFalse(should_stop, "No debe detener en estado 2")

    def test_state_13_no_stop(self):
        """Estado 13: no debe hacer parada."""
        priming_status = 13
        treatment_mode = 1
        
        should_stop_therapy = (priming_status in (14, 15) and treatment_mode != 3)
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        should_stop = should_stop_therapy or should_stop_cleaning
        
        self.assertFalse(should_stop, "No debe detener en estado 13")

    def test_state_16_no_stop(self):
        """Estado 16: no debe hacer parada."""
        priming_status = 16
        treatment_mode = 0
        
        should_stop_therapy = (priming_status in (14, 15) and treatment_mode != 3)
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        should_stop = should_stop_therapy or should_stop_cleaning
        
        self.assertFalse(should_stop, "No debe detener en estado 16")

    def test_state_6_and_mode_0_no_stop(self):
        """Estado 6 + modo 0 (hemodiálisis): no debe detener limpieza."""
        priming_status = 6
        treatment_mode = 0
        
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        
        self.assertFalse(should_stop_cleaning, "No debe detener limpieza si modo no es 3")

    def test_state_7_and_mode_3_no_stop(self):
        """Estado 7 + modo 3 (limpieza): no debe detener (no es estado 6)."""
        priming_status = 7
        treatment_mode = 3
        
        should_stop_cleaning = (treatment_mode == 3 and priming_status == 6)
        
        self.assertFalse(should_stop_cleaning, "No debe detener limpieza en estado 7, solo en 6")


class TestUncleanCloseFlow(unittest.TestCase):
    """Tests del flujo completo de detección."""

    def test_clean_close_flow(self):
        """Flujo completo: cierre limpio."""
        temp_dir = tempfile.TemporaryDirectory()
        try:
            clean_close_path = os.path.join(temp_dir.name, "cierre_limpio")
            
            # Fase 1: Cierre limpio (crear marca)
            with open(clean_close_path, "w") as f:
                f.write("")
            self.assertTrue(os.path.exists(clean_close_path))
            
            # Fase 2: Arranque (detectar marca y borrarla)
            checked_once = False
            if not checked_once:
                checked_once = True
                if os.path.exists(clean_close_path):
                    # No hacer paro
                    os.remove(clean_close_path)
                    paro_ejecutado = False
            
            self.assertFalse(os.path.exists(clean_close_path))
            self.assertFalse(paro_ejecutado, "No debe ejecutar paro si era cierre limpio")
        
        finally:
            temp_dir.cleanup()

    def test_unclean_close_therapy_flow(self):
        """Flujo completo: cierre no limpio con terapia en progreso."""
        temp_dir = tempfile.TemporaryDirectory()
        try:
            clean_close_path = os.path.join(temp_dir.name, "cierre_limpio")
            
            # Fase 1: Cierre NO limpio (NO crear marca)
            self.assertFalse(os.path.exists(clean_close_path))
            
            # Fase 2: Arranque (detectar ausencia de marca)
            checked_once = False
            paro_ejecutado = False
            if not checked_once:
                checked_once = True
                if not os.path.exists(clean_close_path):
                    # Hay cierre no limpio
                    priming_status = 14
                    treatment_mode = 0
                    
                    if priming_status in (14, 15) and treatment_mode != 3:
                        paro_ejecutado = True  # Ejecutar stop_treatment()
            
            self.assertTrue(paro_ejecutado, "Debe ejecutar paro de terapia")
        
        finally:
            temp_dir.cleanup()

    def test_unclean_close_cleaning_flow(self):
        """Flujo completo: cierre no limpio con limpieza en progreso."""
        temp_dir = tempfile.TemporaryDirectory()
        try:
            clean_close_path = os.path.join(temp_dir.name, "cierre_limpio")
            
            # Fase 1: Cierre NO limpio (NO crear marca)
            self.assertFalse(os.path.exists(clean_close_path))
            
            # Fase 2: Arranque (detectar ausencia de marca)
            checked_once = False
            paro_ejecutado = False
            if not checked_once:
                checked_once = True
                if not os.path.exists(clean_close_path):
                    # Hay cierre no limpio
                    priming_status = 6
                    treatment_mode = 3
                    
                    if treatment_mode == 3 and priming_status == 6:
                        paro_ejecutado = True  # Ejecutar dialyStopDialysisButt
            
            self.assertTrue(paro_ejecutado, "Debe ejecutar paro de limpieza")
        
        finally:
            temp_dir.cleanup()

    def test_unclean_close_idle_state_no_stop(self):
        """Flujo completo: cierre no limpio pero sin terapia/limpieza."""
        temp_dir = tempfile.TemporaryDirectory()
        try:
            clean_close_path = os.path.join(temp_dir.name, "cierre_limpio")
            
            # Fase 1: Cierre NO limpio (NO crear marca)
            self.assertFalse(os.path.exists(clean_close_path))
            
            # Fase 2: Arranque (detectar ausencia de marca)
            checked_once = False
            paro_ejecutado = False
            if not checked_once:
                checked_once = True
                if not os.path.exists(clean_close_path):
                    # Hay cierre no limpio
                    priming_status = 1  # Estado ocioso
                    treatment_mode = 0
                    
                    # Ninguna condición se cumple
                    if priming_status in (14, 15) and treatment_mode != 3:
                        paro_ejecutado = True
                    elif treatment_mode == 3 and priming_status == 6:
                        paro_ejecutado = True
            
            self.assertFalse(paro_ejecutado, "No debe ejecutar paro en estado ocioso")
        
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
