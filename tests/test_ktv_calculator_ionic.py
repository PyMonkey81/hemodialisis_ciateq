"""Pruebas del Kt/V iónico sin compensación de temperatura en Python.

La conductividad del tag ya viene a 25 °C desde el firmware de la celda.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


class TestKtvIonicCalculation(unittest.TestCase):
    def setUp(self):
        self.calc = CalculadoraKtV()
        self.calc.set_volumen_bioimpedancia(30.0)

    def _load(self, d_target, ef1=13.5, sf1=13.45):
        ef1, sf1, ef2, sf2 = _pair_for_d(d_target, ef1, sf1)
        self.calc.store_conductivity_t1(ef1, sf1)
        self.calc.store_conductivity_t2(ef2, sf2)

    def test_reset_clears_accumulation(self):
        self.calc.kt_acumulado = 100.0
        self.calc.tiempo_ultima_medicion = 5.0
        self.calc.d_vigente = 200.0
        self.calc._cierre_hecho = True
        self.calc.reset()
        self.assertEqual(self.calc.kt_acumulado, 0.0)
        self.assertIsNone(self.calc.tiempo_ultima_medicion)
        self.assertEqual(self.calc.d_vigente, 0.0)
        self.assertFalse(self.calc._cierre_hecho)

    def test_d_does_not_use_temperature(self):
        self._load(200.0)
        d = self.calc.calculate_d_ionic(QD, QF_L_H, QB, 0.0)
        self.assertAlmostEqual(d, 200.0, places=2)

    def test_small_delta_returns_zero_and_keeps_previous_d(self):
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        self.calc.store_conductivity_t1(14.0, 13.9)
        self.calc.store_conductivity_t2(14.02, 13.91)
        d = self.calc.calculate_d_ionic(QD, QF_L_H, QB, 0.0)
        self.assertEqual(d, 0.0)
        self.calc.update_kt(50.0, QD, QF_L_H, QB, 0.0)
        self.assertAlmostEqual(self.calc.d_vigente, 200.0, places=2)
        self.assertEqual(self.calc.kt_acumulado, 0.0)

    def test_interval_closes_with_previous_d(self):
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        self.assertEqual(self.calc.kt_acumulado, 0.0)

        self._load(100.0, ef1=13.7, sf1=13.59)
        self.calc.update_kt(50.0, QD, QF_L_H, QB, 0.0)
        self.assertAlmostEqual(self.calc.kt_acumulado, 6000.0, places=1)
        self.assertAlmostEqual(self.calc.get_ktv_delivered(50.0), 0.20, places=3)
        self.assertAlmostEqual(self.calc.get_ktv_delivered(80.0), 0.30, places=3)

    def test_commit_is_idempotent(self):
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        self._load(100.0, ef1=13.7, sf1=13.59)
        self.calc.update_kt(50.0, QD, QF_L_H, QB, 0.0)
        first = self.calc.commit_final_interval(80.0)
        second = self.calc.commit_final_interval(90.0)
        self.assertAlmostEqual(first, 0.30, places=3)
        self.assertAlmostEqual(second, 0.30, places=3)
        self.assertAlmostEqual(self.calc.kt_acumulado, 9000.0, places=1)

    def test_d_is_clamped_to_qd_plus_qf(self):
        self.calc.store_conductivity_t1(13.0, 13.0)
        self.calc.store_conductivity_t2(14.0, 12.0)
        d = self.calc.calculate_d_ionic(QD, QF_L_H, QB, 0.0)
        qf_ml = QF_L_H * 1000.0 / 60.0
        self.assertAlmostEqual(d, QD + qf_ml, places=2)

    def test_projected_uses_remaining_time(self):
        self._load(200.0)
        self.calc.update_kt(20.0, QD, QF_L_H, QB, 0.0)
        projected = self.calc.get_ktv_projected(20.0, 80.0)
        self.assertAlmostEqual(projected, 200.0 * 60.0 / 30000.0, places=3)


if __name__ == "__main__":
    unittest.main()
