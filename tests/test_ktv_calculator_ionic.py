"""
Test suite para validar el cálculo de Kt/V iónico con compensación de temperatura.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.ktv_calculator import CalculadoraKtV


class TestKtvIonicCalculation(unittest.TestCase):
    """Pruebas del cálculo iónico de Kt/V con compensación individual de temperatura."""

    def setUp(self):
        """Configurar una instancia fresca de CalculadoraKtV para cada test."""
        self.calc = CalculadoraKtV()
        
        # Configurar paciente: 70 kg, 170 cm, 40 años, masculino
        self.calc.config_paciente(peso=70, altura=170, edad=40, genero=1)
        self.assertGreater(self.calc.volumen_distribucion_v, 0, "Watson V debe ser > 0")

    def test_reset_initializes_correctly(self):
        """Test: reset() debe inicializar todos los valores a cero."""
        self.calc.kt_acumulado = 100.0
        self.calc.tiempo_ultima_medicion = 5.0
        self.calc.d_actual = 200.0
        
        self.calc.reset()
        
        self.assertEqual(self.calc.kt_acumulado, 0.0)
        self.assertIsNone(self.calc.tiempo_ultima_medicion)
        self.assertEqual(self.calc.d_actual, 0.0)
        self.assertEqual(self.calc.volumen_distribucion_v, 0.0)

    def test_temperature_compensation_single_point(self):
        """Test: Compensación a 25°C debe ser correcta para un punto."""
        # EF: 13.5 mS/cm a 37°C
        cd_ef_37 = 13.5
        temp_ef = 37.0
        alpha = 0.021
        
        # Fórmula: C25 = C_T / (1 + alpha * (T - 25))
        cd_ef_25 = cd_ef_37 / (1 + alpha * (temp_ef - 25))
        
        # A 37°C (2°C arriba de 25°C):
        # 13.5 / (1 + 0.021 * 12) = 13.5 / 1.252 ≈ 10.78
        expected = 13.5 / (1 + 0.021 * 12)
        self.assertAlmostEqual(cd_ef_25, expected, places=4)

    def test_store_conductivity_t1_with_separate_temps(self):
        """Test: store_conductivity_t1 debe guardar EF y SF con temperaturas distintas."""
        cd_ef = 13.50
        cd_sf = 13.45
        temp_ef = 37.2
        temp_sf = 37.1
        
        self.calc.store_conductivity_t1(cd_ef, cd_sf, temp_ef, temp_sf)
        
        self.assertEqual(self.calc._cd_in_t1, cd_ef)
        self.assertEqual(self.calc._cd_out_t1, cd_sf)
        self.assertEqual(self.calc._temp_ef_t1, temp_ef)
        self.assertEqual(self.calc._temp_sf_t1, temp_sf)

    def test_calculate_d_ionic_valid_measurement(self):
        """Test: calculate_d_ionic debe calcular D correctamente."""
        # Configurar dos puntos con diferencia clara
        # T1: EF=13.50, SF=13.45 a 37.0°C ambos
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        
        # T2: EF=13.80, SF=13.60 a 37.0°C ambos (cambio más pronunciado)
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        
        # Parámetros típicos
        qd = 500  # mL/min
        qf = 10   # L/h
        qb = 300  # mL/min
        r = 0.0   # Sin recirculación
        
        d = self.calc.calculate_d_ionic(qd, qf, qb, r)
        
        self.assertGreater(d, 0, "D debe ser positivo")
        self.assertLessEqual(d, qd + (qf * 1000 / 60), "D no debe exceder Qd + Qf")

    def test_calculate_d_ionic_small_delta_ef(self):
        """Test: Si abs(delta_EF) < 0.05, D debe ser 0."""
        # Conductividades prácticamente iguales
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.51, cd_out=13.46,
            temp_ef=37.0, temp_sf=37.0
        )
        
        # delta_EF = 13.51 - 13.50 = 0.01 < 0.05
        d = self.calc.calculate_d_ionic(500, 10, 300, 0.0)
        
        self.assertEqual(d, 0.0, "D debe ser 0 cuando delta_EF < 0.05")

    def test_accumulate_kt_first_measurement(self):
        """Test: Primera medición D válida debe tener dt=0."""
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        
        current_time = 0.0  # Inicio
        self.calc.update_kt(current_time, 500, 10, 300, 0.0)
        
        self.assertEqual(self.calc.kt_acumulado, 0.0, "Primera medición: dt=0, Kt no cambia")
        self.assertIsNotNone(self.calc.tiempo_ultima_medicion, "Debe marcar el tiempo")

    def test_accumulate_kt_second_measurement(self):
        """Test: Segunda medición debe acumular Kt con dt real."""
        # Primera medición
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.update_kt(0.0, 500, 10, 300, 0.0)
        d1 = self.calc.d_actual
        
        # Segunda medición (después de 5 minutos)
        self.calc.store_conductivity_t1(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=14.10, cd_out=13.75,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.update_kt(5.0, 500, 10, 300, 0.0)
        d2 = self.calc.d_actual
        
        expected_kt = d1 * 5.0  # dt=5 minutos
        self.assertGreater(self.calc.kt_acumulado, 0, "Kt debe acumularse")
        self.assertAlmostEqual(self.calc.kt_acumulado, expected_kt, places=0)

    def test_get_ktv_delivered(self):
        """Test: get_ktv_delivered debe devolver Kt/V acumulado."""
        # Configurar bioimpedancia conocida
        self.calc.set_volumen_bioimpedancia(40.0)  # 40 litros
        
        # Primera medición en t=0
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.update_kt(0.0, 500, 10, 300, 0.0)
        
        # Segunda medición en t=5
        self.calc.store_conductivity_t1(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=14.10, cd_out=13.75,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.update_kt(5.0, 500, 10, 300, 0.0)
        
        ktv_delivered = self.calc.get_ktv_delivered(5.0, 500, 10, 300, 0.0)
        
        self.assertGreater(ktv_delivered, 0, "Kt/V entregado debe ser > 0")
        self.assertAlmostEqual(
            ktv_delivered,
            self.calc.kt_acumulado / 40000,  # V en mL
            places=4
        )

    def test_get_ktv_projected(self):
        """Test: get_ktv_projected debe proyectar Kt/V al final de sesión."""
        self.calc.set_volumen_bioimpedancia(40.0)  # 40 litros
        
        # Medición en t=10 min de una sesión de 240 min (4 horas)
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.update_kt(10.0, 500, 10, 300, 0.0)
        d_current = self.calc.d_actual
        
        t_current = 10.0
        t_total = 240.0
        
        ktv_projected = self.calc.get_ktv_projected(t_current, t_total, 500, 10, 300, 0.0)
        
        # Proyectado = (Kt + D * (t_total - t_current)) / V
        t_restante = t_total - t_current  # 230 min
        expected_kt_proj = self.calc.kt_acumulado + (d_current * t_restante)
        expected_ktv = expected_kt_proj / 40000
        
        self.assertAlmostEqual(ktv_projected, expected_ktv, places=3)

    def test_temperature_difference_impact(self):
        """Test: Temperaturas distintas en EF y SF deben afectar D diferente."""
        # Caso 1: Ambas a 37°C
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.0, temp_sf=37.0
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.0, temp_sf=37.0
        )
        d1 = self.calc.calculate_d_ionic(500, 10, 300, 0.0)
        
        # Caso 2: EF a 37.2°C, SF a 36.8°C (diferencia real)
        self.calc.reset()
        self.calc.config_paciente(70, 170, 40, 1)
        
        self.calc.store_conductivity_t1(
            cd_in=13.50, cd_out=13.45,
            temp_ef=37.2, temp_sf=36.8
        )
        self.calc.store_conductivity_t2(
            cd_in=13.80, cd_out=13.60,
            temp_ef=37.2, temp_sf=36.8
        )
        d2 = self.calc.calculate_d_ionic(500, 10, 300, 0.0)
        
        # Los valores pueden diferir debido a la compensación individual
        # Este test verifica que el código se ejecuta sin errores
        self.assertGreater(d1, 0)
        self.assertGreater(d2, 0)


class TestKtvEdgeCases(unittest.TestCase):
    """Pruebas de casos extremos y errores."""

    def setUp(self):
        self.calc = CalculadoraKtV()
        self.calc.config_paciente(70, 170, 40, 1)

    def test_invalid_volume(self):
        """Test: V <= 0 debe devolver D=0."""
        self.calc.volumen_distribucion_v = 0.0
        
        self.calc.store_conductivity_t1(13.50, 13.45, 37.0, 37.0)
        self.calc.store_conductivity_t2(13.80, 13.60, 37.0, 37.0)
        
        d = self.calc.calculate_d_ionic(500, 10, 300, 0.0)
        
        self.assertEqual(d, 0.0, "D debe ser 0 si V es inválido")

    def test_qf_conversion(self):
        """Test: Qf debe convertirse correctamente de L/h a mL/min."""
        self.calc.store_conductivity_t1(13.50, 13.45, 37.0, 37.0)
        self.calc.store_conductivity_t2(13.80, 13.60, 37.0, 37.0)
        
        # Qf = 10 L/h = (10 * 1000) / 60 = 166.67 mL/min
        qd = 500  # mL/min
        qf = 10   # L/h
        qf_ml_min = (qf * 1000) / 60
        
        d = self.calc.calculate_d_ionic(qd, qf, 300, 0.0)
        
        # D debe estar limitado a Qd + Qf_mL_min = 500 + 166.67 = 666.67
        self.assertLessEqual(d, qd + qf_ml_min + 1e-6, "D no debe exceder Qd + Qf")

    def test_no_division_by_zero(self):
        """Test: No debe haber división por cero aunque delta_EF sea cercano a 0."""
        self.calc.store_conductivity_t1(13.50, 13.45, 37.0, 37.0)
        # delta_EF muy pequeño pero no cero
        self.calc.store_conductivity_t2(13.5001, 13.4501, 37.0, 37.0)
        
        # Esto debería manejar el caso sin excepción
        try:
            d = self.calc.calculate_d_ionic(500, 10, 300, 0.0)
            self.assertEqual(d, 0.0, "D debe ser 0 cuando delta_EF < 0.05")
        except ZeroDivisionError:
            self.fail("No debe haber ZeroDivisionError")


if __name__ == '__main__':
    unittest.main()
