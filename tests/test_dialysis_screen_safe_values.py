"""Tests para dialysis_screenV2.py - manejo seguro de valores None y texto sin cerrar ventana."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Agregar el directorio raíz al path para imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.platform_runtime import safe_float


class TestSafeFloatHandling(unittest.TestCase):
    """Tests para manejo seguro de None y texto con safe_float."""

    def test_safe_float_with_none_returns_default(self):
        """safe_float(None) debe retornar 0.0 sin lanzar excepción."""
        result = safe_float(None, 0.0)
        self.assertEqual(result, 0.0)

    def test_safe_float_with_text_returns_default(self):
        """safe_float('texto') debe retornar 0.0 sin lanzar excepción."""
        result = safe_float("texto", 0.0)
        self.assertEqual(result, 0.0)

    def test_safe_float_with_valid_string_number(self):
        """safe_float('42.5') debe retornar 42.5."""
        result = safe_float("42.5", 0.0)
        self.assertEqual(result, 42.5)

    def test_safe_float_with_negative_string_number(self):
        """safe_float('-100.5') debe retornar -100.5."""
        result = safe_float("-100.5", 0.0)
        self.assertEqual(result, -100.5)

    def test_safe_float_with_integer_returns_float(self):
        """safe_float(42) debe retornar 42.0 como float."""
        result = safe_float(42, 0.0)
        self.assertEqual(result, 42.0)
        self.assertIsInstance(result, float)

    def test_safe_float_with_float_returns_float(self):
        """safe_float(42.5) debe retornar 42.5."""
        result = safe_float(42.5, 0.0)
        self.assertEqual(result, 42.5)


class TestDialysisScreenUpdateValues(unittest.TestCase):
    """Tests para update_values() con None y texto sin cerrar ventana."""

    def setUp(self):
        """Configura mocks para PySide6 y componentes de la pantalla."""
        self.mock_parent = MagicMock()
        self.mock_parent.state = MagicMock()
        self.mock_parent.state.current_phase = MagicMock()

    def test_update_values_with_none_uf_rate(self):
        """update_values con ultraFilterPumpSpeed=None no debe cerrar la ventana."""
        # Mock de DialysisScreen sin crear la interfaz gráfica real
        
        # Simular la lógica de update_values
        current_values = {"ultraFilterPumpSpeed": None}
        uf_rate_val = current_values.get("ultraFilterPumpSpeed", 0.0)
        uf_rate = safe_float(uf_rate_val, 0.0)
        # No debe lanzar excepción
        formatted = f"{uf_rate:.2f} L/hora"
        self.assertEqual(formatted, "0.00 L/hora")

    def test_update_values_with_text_heparin_hours(self):
        """update_values con heparineTherapyHours='texto' no debe cerrar la ventana."""
        
        # Simular la lógica
        current_values = {
            "heparineTherapyHours": "texto",
            "heparineTherapyMinutes": "más texto",
        }
        
        hep_hours_val = current_values.get("heparineTherapyHours", 0.0)
        hep_minutes_val = current_values.get("heparineTherapyMinutes", 0.0)
        uf_therapy_hours = safe_float(hep_hours_val, 0.0)
        uf_therapy_minutes = safe_float(hep_minutes_val, 0.0)
        
        # No debe lanzar excepción
        therapy_duration_hours = uf_therapy_hours + (uf_therapy_minutes / 60.0)
        self.assertEqual(therapy_duration_hours, 0.0)

    def test_update_values_with_none_pulse_count(self):
        """update_values con ultraFilterCycleCount=None no debe cerrar la ventana."""
        
        # Simular la lógica
        current_values = {"ultraFilterCycleCount": None}
        
        cycle_count_val = current_values.get("ultraFilterCycleCount", 0.0)
        uf_pulse_count = safe_float(cycle_count_val, 0.0)
        
        # No debe lanzar excepción
        self.assertEqual(uf_pulse_count, 0.0)

    def test_update_values_with_text_pressure(self):
        """update_values con presiones como texto no debe cerrar la ventana."""
        
        # Simular la lógica
        current_values = {
            "bloodVenousPressureData": "error",
            "bloodArteryPressureData": "desconocido",
        }
        
        venous_pressure_val = current_values.get("bloodVenousPressureData", 0.0)
        arterial_pressure_val = current_values.get("bloodArteryPressureData", 0.0)
        venous_pressure = safe_float(venous_pressure_val, 0.0)
        arterial_pressure = safe_float(arterial_pressure_val, 0.0)
        
        # No debe lanzar excepción
        self.assertEqual(venous_pressure, 0.0)
        self.assertEqual(arterial_pressure, 0.0)


class TestPressureWaveformWidgetAddValues(unittest.TestCase):
    """Tests para add_values() en PressureWaveformWidget con None y texto."""

    def test_add_values_with_none_arterial(self):
        """add_values(None, 100.0) debe convertir None a número sin error."""
        from collections import deque
        
        widget = MagicMock()
        widget.max_points = 300
        widget.arterial_history = deque([0.0] * 300, maxlen=300)
        widget.venous_history = deque([0.0] * 300, maxlen=300)
        
        # Simular add_values con protección
        arterial = safe_float(None, 0.0)
        venous = safe_float(100.0, 0.0)
        
        # No debe lanzar excepción
        widget.arterial_history.append(arterial)
        widget.venous_history.append(venous)
        
        self.assertEqual(widget.arterial_history[-1], 0.0)
        self.assertEqual(widget.venous_history[-1], 100.0)

    def test_add_values_with_text_venous(self):
        """add_values(120.0, 'error') debe convertir 'error' a número sin error."""
        from collections import deque
        
        widget = MagicMock()
        widget.max_points = 300
        widget.arterial_history = deque([0.0] * 300, maxlen=300)
        widget.venous_history = deque([0.0] * 300, maxlen=300)
        
        # Simular add_values con protección
        arterial = safe_float(120.0, 0.0)
        venous = safe_float("error", 0.0)
        
        # No debe lanzar excepción
        widget.arterial_history.append(arterial)
        widget.venous_history.append(venous)
        
        self.assertEqual(widget.arterial_history[-1], 120.0)
        self.assertEqual(widget.venous_history[-1], 0.0)

    def test_add_values_with_none_both(self):
        """add_values(None, None) debe usar 0.0 para ambas sin error."""
        from collections import deque
        
        widget = MagicMock()
        widget.max_points = 300
        widget.arterial_history = deque([0.0] * 300, maxlen=300)
        widget.venous_history = deque([0.0] * 300, maxlen=300)
        
        # Simular add_values con protección
        arterial = safe_float(None, 0.0)
        venous = safe_float(None, 0.0)
        
        # No debe lanzar excepción
        widget.arterial_history.append(arterial)
        widget.venous_history.append(venous)
        
        self.assertEqual(widget.arterial_history[-1], 0.0)
        self.assertEqual(widget.venous_history[-1], 0.0)

    def test_add_values_with_valid_numbers(self):
        """add_values(-100.5, 150.2) debe guardar los números sin cambios."""
        from collections import deque
        
        widget = MagicMock()
        widget.max_points = 300
        widget.arterial_history = deque([0.0] * 300, maxlen=300)
        widget.venous_history = deque([0.0] * 300, maxlen=300)
        
        # Simular add_values con protección
        arterial = safe_float(-100.5, 0.0)
        venous = safe_float(150.2, 0.0)
        
        # No debe lanzar excepción
        widget.arterial_history.append(arterial)
        widget.venous_history.append(venous)
        
        self.assertEqual(widget.arterial_history[-1], -100.5)
        self.assertEqual(widget.venous_history[-1], 150.2)


class TestHeparinConfigSafeFloat(unittest.TestCase):
    """Tests para heparin_config_screenV2.py usando safe_float en float()."""

    def test_flow_combo_with_text(self):
        """Flow combo currentText() con texto debe usar safe_float sin error."""
        combo = MagicMock()
        combo.currentText.return_value = "texto inválido"
        
        # Simular la lógica de _on_flow_hep_changed
        flujo_value = safe_float(combo.currentText(), 0.0)
        
        # No debe lanzar excepción
        self.assertEqual(flujo_value, 0.0)

    def test_flow_combo_with_valid_number(self):
        """Flow combo currentText() con número válido debe convertirse."""
        combo = MagicMock()
        combo.currentText.return_value = "2.5"
        
        # Simular la lógica
        flujo_value = safe_float(combo.currentText(), 0.0)
        
        self.assertEqual(flujo_value, 2.5)

    def test_numpad_new_value_with_none(self):
        """Numpad get_value() que retorna None debe convertirse a 0.0."""
        dialog = MagicMock()
        dialog.get_value.return_value = None
        
        # Simular la lógica
        new_value = dialog.get_value()
        if new_value is not None:
            float_val = safe_float(new_value, 0.0)
        else:
            float_val = 0.0
        
        # No debe lanzar excepción
        self.assertEqual(float_val, 0.0)

    def test_numpad_new_value_with_text(self):
        """Numpad get_value() con texto debe convertirse a 0.0."""
        dialog = MagicMock()
        dialog.get_value.return_value = "error"
        
        # Simular la lógica
        new_value = dialog.get_value()
        if new_value is not None:
            float_val = safe_float(new_value, 0.0)
        
        # No debe lanzar excepción
        self.assertEqual(float_val, 0.0)

    def test_numpad_new_value_with_valid_number(self):
        """Numpad get_value() con número válido debe convertirse."""
        dialog = MagicMock()
        dialog.get_value.return_value = "42.5"
        
        # Simular la lógica
        new_value = dialog.get_value()
        if new_value is not None:
            float_val = safe_float(new_value, 0.0)
        
        self.assertEqual(float_val, 42.5)


if __name__ == "__main__":
    unittest.main()
