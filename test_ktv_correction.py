#!/usr/bin/env python
"""
Test simple de la corrección de Kt/V iónico.
Verifica la lógica con el ejemplo dado:

V = 30000 mL
D = 200 a los 20 min (NO suma)
D = 100 a los 50 min (suma 200 * 30 = 6000)
Paro a los 80 min (suma 100 * 30 = 3000)

A los 50: entregado = 200*30/30000 = 0.20
Al paro: guardado = (200*30 + 100*30)/30000 = 0.30
"""

import sys
sys.path.insert(0, '.')

from logic.ktv_calculator import CalculadoraKtV

def test_ktv_correction():
    calc = CalculadoraKtV()
    
    # Configurar V = 30 litros = 30000 mL
    calc.set_volumen_bioimpedancia(30.0)
    print(f"✓ V configurado: {calc.volumen_distribucion_v:.0f} mL")
    
    # t=20 min: Primera D válida = 200
    # Simular: delta_ef = 0.2, delta_sf = 0.1
    # D = (500 + 166.67) * (1 - 0.1/0.2) = 666.67 * 0.5 = 333.33
    # Ajustar conductividades para que D = 200:
    # D = (Qd + Qf_ml) * (1 - delta_sf / delta_ef)
    # 200 = 666.67 * (1 - delta_sf / delta_ef)
    # 200 / 666.67 = 1 - delta_sf / delta_ef
    # 0.3 = 1 - delta_sf / delta_ef
    # delta_sf / delta_ef = 0.7
    
    qd = 500  # mL/min
    qf = 10   # L/h = 166.67 mL/min
    qb = 300
    r = 0.0
    
    qf_ml = qf * 1000 / 60
    print(f"Qf: {qf} L/h = {qf_ml:.2f} mL/min")
    print(f"Qd + Qf: {qd + qf_ml:.2f} mL/min")
    
    # Primera medición T1: cd_in=13.5, cd_out=13.45
    calc.store_conductivity_t1(13.5, 13.45)
    
    # Segunda medición T2: para obtener D=200
    # delta_ef = 0.2, delta_sf = 0.14 (ratio 0.7)
    # cd_in_t2 = 13.5 + 0.2 = 13.7
    # cd_out_t2 = 13.45 + 0.14 = 13.59
    calc.store_conductivity_t2(13.7, 13.59)
    
    d_test = calc.calculate_d_ionic(qd, qf, qb, r)
    print(f"\nt=20 min: D calculada = {d_test:.1f} mL/min (esperado ≈200)")
    
    # Actualizar a t=20 min con D=200
    calc.update_kt(20.0, qd, qf, qb, r)
    print(f"  D_vigente: {calc.d_vigente:.1f}")
    print(f"  Kt acumulado: {calc.kt_acumulado:.1f} (esperado 0, primera medición)")
    print(f"  Tiempo última medición: {calc.tiempo_ultima_medicion:.2f}")
    
    # Segunda medición a t=50 min: D=100
    # delta_ef = 0.1, delta_sf = 0.07 (ratio 0.7)
    calc.store_conductivity_t1(13.7, 13.59)
    calc.store_conductivity_t2(13.8, 13.66)
    
    d_test2 = calc.calculate_d_ionic(qd, qf, qb, r)
    print(f"\nt=50 min: D calculada = {d_test2:.1f} mL/min (esperado ≈100)")
    
    # Actualizar a t=50 min: debe sumar con D_vigente anterior (200)
    calc.update_kt(50.0, qd, qf, qb, r)
    print(f"  D_vigente actualizada: {calc.d_vigente:.1f}")
    print(f"  Kt acumulado: {calc.kt_acumulado:.1f} (esperado 200*30=6000)")
    print(f"  Kt/V entregado: {calc.get_ktv_delivered(50.0):.3f} (esperado 0.200)")
    
    # Simular paro a t=80 min: suma con D_vigente (100)
    ktv_final = calc.get_ktv_delivered(80.0)
    print(f"\nt=80 min (paro): Kt/V entregado = {ktv_final:.3f} (esperado 0.300)")
    
    # Validaciones
    assert abs(calc.kt_acumulado - 6000) < 1, f"Kt a los 50 min: esperado 6000, got {calc.kt_acumulado}"
    assert abs(calc.get_ktv_delivered(50.0) - 0.200) < 0.001, f"KTV a los 50: esperado 0.200"
    assert abs(ktv_final - 0.300) < 0.001, f"KTV a los 80: esperado 0.300, got {ktv_final}"
    
    print("\n✓ TODAS LAS VALIDACIONES PASARON")

if __name__ == "__main__":
    test_ktv_correction()
