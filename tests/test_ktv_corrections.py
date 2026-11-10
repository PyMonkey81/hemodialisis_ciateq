"""Tests for Kt/V calculation corrections:
1. Cycle-to-flow conversion for balanceChamberSetTiming
2. Projected Kt/V formula based on time from last measurement
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.calculos import convertir_ciclos_a_flujo, convertir_flujo_a_ciclos, FACTOR_CONVERSION_CICLOS, OFFSET_CALIBRACION
from logic.ktv_calculator import CalculadoraKtV

QD = 500.0
QF_L_H = 10.0
QB = 300.0


def _pair_for_d(d_target: float, ef1: float = 13.5, sf1: float = 13.45):
    """Arma T2 para una D exacta con Qd=500 mL/min y Qf=10 L/h."""
    qf_ml = QF_L_H * 1000.0 / 60.0
    ratio = 1.0 - (d_target / (QD + qf_ml))
    delta_ef = 0.20
    delta_sf = ratio * delta_ef
    return (ef1, sf1, ef1 + delta_ef, sf1 + delta_sf)


class TestCycleToFlowConversion(unittest.TestCase):
    """Tests for convertir_ciclos_a_flujo function."""

    def test_500_ml_min_converts_to_3_55_cycles(self):
        """500 mL/min should convert to approximately 3.55 cycles."""
        # Inverse: cycles = (1800 / 500) - 0.05 = 3.6 - 0.05 = 3.55
        target_qd = 500.0
        cycles = convertir_flujo_a_ciclos(target_qd)
        self.assertAlmostEqual(cycles, 3.55, places=2)

    def test_3_55_cycles_converts_back_to_500_ml_min(self):
        """3.55 cycles should convert back to approximately 500 mL/min."""
        cycles = 3.55
        qd = convertir_ciclos_a_flujo(cycles)
        self.assertAlmostEqual(qd, 500.0, places=1)

    def test_zero_cycles_returns_zero(self):
        """Zero or negative cycles should return 0."""
        self.assertEqual(convertir_ciclos_a_flujo(0), 0.0)
        self.assertEqual(convertir_ciclos_a_flujo(-1), 0.0)

    def test_invalid_cycles_returns_zero(self):
        """Invalid inputs should return 0."""
        self.assertEqual(convertir_ciclos_a_flujo(None), 0.0)
        self.assertEqual(convertir_ciclos_a_flujo("invalid"), 0.0)

    def test_round_trip_conversion_maintains_precision(self):
        """Flow → cycles → flow should maintain reasonable precision."""
        original_qd = 500.0
        cycles = convertir_flujo_a_ciclos(original_qd)
        recovered_qd = convertir_ciclos_a_flujo(cycles)
        self.assertAlmostEqual(recovered_qd, original_qd, places=1)

    def test_typical_range_conversions(self):
        """Test typical clinical flow rates."""
        test_cases = [
            (300.0, convertir_flujo_a_ciclos(300.0)),
            (400.0, convertir_flujo_a_ciclos(400.0)),
            (500.0, convertir_flujo_a_ciclos(500.0)),
            (600.0, convertir_flujo_a_ciclos(600.0)),
        ]
        
        for expected_qd, cycles in test_cases:
            result_qd = convertir_ciclos_a_flujo(cycles)
            self.assertAlmostEqual(result_qd, expected_qd, places=1,
                                   msg=f"Failed for {expected_qd} mL/min (cycles={cycles})")


class TestProjectedKtvFormula(unittest.TestCase):
    """Tests for corrected get_ktv_projected() formula."""

    def setUp(self):
        self.calc = CalculadoraKtV()
        self.calc.set_volumen_bioimpedancia(30.0)

    def _load(self, d_target, ef1=13.5, sf1=13.45):
        ef1, sf1, ef2, sf2 = _pair_for_d(d_target, ef1, sf1)
        self.calc.store_conductivity_t1(ef1, sf1)
        self.calc.store_conductivity_t2(ef2, sf2)

    def test_projected_does_not_decrease_between_measurements_with_constant_d(self):
        """With constant D, projected Kt/V should not decrease between measurements."""
        # First measurement at 20 minutes, D = 200
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        
        # No second measurement; D remains 200
        # Check projected at 20, 30, 40, 50 minutes (all within 240-minute session)
        projections = [
            (20.0, self.calc.get_ktv_projected(20.0, 240.0)),
            (30.0, self.calc.get_ktv_projected(30.0, 240.0)),
            (40.0, self.calc.get_ktv_projected(40.0, 240.0)),
            (50.0, self.calc.get_ktv_projected(50.0, 240.0)),
        ]
        
        # All projections should be the same with constant D
        for time, proj in projections:
            self.assertAlmostEqual(proj, projections[0][1], places=3,
                                   msg=f"Projected Kt/V changed at {time} min: {proj} vs {projections[0][1]}")

    def test_projected_includes_time_from_last_measurement_to_session_end(self):
        """Projected should account for time from last measurement to session end, not current time."""
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        
        # Session is 240 minutes total
        # Last measurement at 20 minutes
        # Time remaining = 240 - 20 = 220 minutes
        
        t_session = 240.0
        current_time = 50.0  # We're at 50 minutes now
        
        projected = self.calc.get_ktv_projected(current_time, t_session)
        
        # Formula: Kt = 0 (at first measurement), D = 200, time_from_last = 240 - 20 = 220
        # Kt_proj = 0 + 200 * 220 = 44000
        # Kt/V = 44000 / 30000 = 1.467
        expected = 44000.0 / 30000.0
        self.assertAlmostEqual(projected, expected, places=2)

    def test_projected_zero_without_valid_d(self):
        """Projected should return 0 if no valid D has been calculated."""
        # No measurement loaded, so d_vigente = 0
        projected = self.calc.get_ktv_projected(50.0, 240.0)
        self.assertEqual(projected, 0.0)

    def test_projected_increases_when_d_increases_at_new_measurement(self):
        """When D increases at a new measurement, projected should increase."""
        # First measurement: D = 100
        self._load(100.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        proj_before = self.calc.get_ktv_projected(20.0, 240.0)
        
        # Second measurement with higher D = 200
        self._load(200.0, ef1=13.7, sf1=13.59)
        self.calc.update_kt(50.0, QD, QF_L_H, QB, 0.0)
        proj_after = self.calc.get_ktv_projected(50.0, 240.0)
        
        # Projected should increase due to higher D
        self.assertGreater(proj_after, proj_before,
                           msg="Projected Kt/V should increase when D increases")

    def test_projected_stability_during_measurement_interval(self):
        """Projected Kt/V should remain stable during a measurement interval if D doesn't change."""
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        
        # At minute 30
        proj_30 = self.calc.get_ktv_projected(30.0, 240.0)
        
        # At minute 40
        proj_40 = self.calc.get_ktv_projected(40.0, 240.0)
        
        # At minute 50
        proj_50 = self.calc.get_ktv_projected(50.0, 240.0)
        
        # All should be equal (same D from time 20 to end)
        self.assertAlmostEqual(proj_30, proj_40, places=3)
        self.assertAlmostEqual(proj_40, proj_50, places=3)


if __name__ == "__main__":
    unittest.main()
