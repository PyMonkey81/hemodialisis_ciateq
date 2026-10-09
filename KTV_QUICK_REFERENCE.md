# Guía Rápida: Cálculo de Kt/V Iónico

## ¿Qué se corrigió?

Se implementó correctamente la **acumulación incremental de Kt** con **compensación individual de temperatura** por sensor de conductividad.

## Flujo de Uso en KtvController

```python
# 1. CAPTURA DE MEDICIONES (dos puntos de conductividad)

# Primera medición (T1)
temp_ef_t1 = current_values.get("dialyTempIFProcessData")
temp_sf_t1 = current_values.get("dialyTempIOFProcessData")
calculadora_ktv.store_conductivity_t1(cd_ef, cd_sf, temp_ef_t1, temp_sf_t1)

# Segunda medición (T2) - después de cambiar setpoint
temp_ef_t2 = current_values.get("dialyTempIFProcessData")
temp_sf_t2 = current_values.get("dialyTempIOFProcessData")
calculadora_ktv.store_conductivity_t2(cd_ef, cd_sf, temp_ef_t2, temp_sf_t2)

# 2. CÁLCULO Y ACUMULACIÓN

t_elapsed = self._get_elapsed_therapy_minutes()
calculadora_ktv.update_kt(t_elapsed, qd, qf, qb, r)

# 3. OBTENER VALORES

ktv_delivered = calculadora_ktv.get_ktv_delivered(t_elapsed, qd, qf, qb, r)
ktv_projected = calculadora_ktv.get_ktv_projected(t_elapsed, t_total, qd, qf, qb, r)

# 4. EMITIR SEÑAL

results_dict = {
    "ktv_acumulado": ktv_delivered,  # Lo que muestra la UI
    "ktv_projectado": ktv_projected,  # Para referencia
    "d_ionic": calculadora_ktv.d_actual,
    "kt_total": calculadora_ktv.kt_acumulado,
}
self.ktv_calculated.emit(results_dict)
```

## Variables Clave

```python
class CalculadoraKtV:
    # Acumulación
    kt_acumulado: float              # Kt total acumulado en mL
    d_actual: float                  # D actual en mL/min
    tiempo_ultima_medicion: float    # Tiempo (min) de última medición
    
    # Almacenamiento de mediciones
    _cd_in_t1, _cd_out_t1              # Conductividades T1
    _temp_ef_t1, _temp_sf_t1           # Temperaturas T1 (separadas)
    _cd_in_t2, _cd_out_t2              # Conductividades T2
    _temp_ef_t2, _temp_sf_t2           # Temperaturas T2 (separadas)
```

## Métodos Principales

### `reset()`
Limpia todo para nuevo tratamiento.

### `store_conductivity_t1/t2(cd_in, cd_out, temp_ef, temp_sf)`
Guarda las dos conductividades con sus temperaturas respectivas.

```python
# Entrada del filtro (EF)
cd_in = conductividad antes del filtro
temp_ef = temperatura EF (tag: dialyTempIFProcessData)

# Salida del filtro (SF)
cd_out = conductividad después del filtro
temp_sf = temperatura SF (tag: dialyTempIOFProcessData)
```

### `update_kt(current_time_minutes, qd, qf, qb, r)`
Actualiza Kt acumulado.

**Primera llamada:** `dt = 0` (no suma nada)
**Llamadas siguientes:** `dt = tiempo_actual - tiempo_última`

### `get_ktv_delivered(t_current, qd, qf, qb, r)` → float
Retorna Kt/V acumulado real. Se usa para mostrar en UI durante terapia.

### `get_ktv_projected(t_current, t_total, qd, qf, qb, r)` → float
Retorna Kt/V proyectado al final. Se usa para expectativa.

## Fórmula de D (Dialisancia Iónica)

### Paso 1: Compensar a 25°C
```python
alpha = 0.021
cd_ef_t1_25 = cd_ef_t1 / (1 + alpha * (temp_ef_t1 - 25))
cd_sf_t1_25 = cd_sf_t1 / (1 + alpha * (temp_sf_t1 - 25))
cd_ef_t2_25 = cd_ef_t2 / (1 + alpha * (temp_ef_t2 - 25))
cd_sf_t2_25 = cd_sf_t2 / (1 + alpha * (temp_sf_t2 - 25))
```

### Paso 2: Calcular Deltas
```python
delta_ef = cd_ef_t2_25 - cd_ef_t1_25
delta_sf = cd_sf_t2_25 - cd_sf_t1_25
```

### Paso 3: Validar
```python
if abs(delta_ef) < 0.05:
    D = 0  # Medición inválida
```

### Paso 4: Calcular D
```python
qf_ml_min = qf_L_h * 1000 / 60
D = (qd + qf_ml_min) * (1 - delta_sf / delta_ef)
D = max(0, min(D, qd + qf_ml_min))  # Limitar
```

### Paso 5: Recirculación (opcional)
```python
if r > 0 and qb > 50 and D > 0:
    denom = 1 - r * (1 - D/qb)
    D_eff = D * ((1 - r) / denom)
    D = min(D_eff, D)
```

## Acumulación de Kt

```python
# Primera medición: dt = 0, no hay acumulación
Kt = 0

# Segunda medición (5 minutos después)
dt = 5.0 - 0.0 = 5.0 min
Kt = 0 + D * 5.0

# Tercera medición (10 minutos después)
dt = 10.0 - 5.0 = 5.0 min
Kt = (Kt anterior) + D * 5.0
```

## Kt/V Entregado (Real)

```python
Kt/V = Kt_acumulado / V

# Si falta el tramo final (ej. sesión pausada):
dt_final = t_actual - t_última_medición
Kt_total = Kt_acumulado + D_actual * dt_final
Kt/V = Kt_total / V
```

## Kt/V Proyectado (Expectativa)

```python
t_restante = max(0, t_total - t_actual)
Kt_proyectado = Kt_acumulado + D_actual * t_restante
Kt/V_proyectado = Kt_proyectado / V
```

## Parámetros Típicos

```python
qd = 500          # mL/min (flujo dializado)
qf = 10           # L/h (flujo filtración)
qb = 300          # mL/min (flujo sangre)
r = 0.0           # Recirculación (0 = ninguna)
v_watson = 40.0   # litros (volumen Watson × 1000 = mL)
```

## Ejemplo de Sesión

```
Tiempo: 0 min
  Capturar T1: EF=13.5 mS/cm @ 37.2°C, SF=13.45 mS/cm @ 37.1°C
  
Tiempo: 5 min
  Capturar T2: EF=13.8 mS/cm @ 37.3°C, SF=13.6 mS/cm @ 37.2°C
  update_kt(5.0, 500, 10, 300, 0.0)
    → dt = 0 (primera medición)
    → Kt = 0
  
Tiempo: 10 min
  Capturar T1: EF=13.8, SF=13.6 @ nuevas temps
  Capturar T2: EF=14.1, SF=13.75 @ nuevas temps
  update_kt(10.0, 500, 10, 300, 0.0)
    → dt = 10.0 - 5.0 = 5.0 min
    → D_nuevo ≈ 250 mL/min
    → Kt = 0 + 250 * 5.0 = 1250
  
  get_ktv_delivered(10.0, 500, 10, 300, 0.0)
    → Retorna: 1250 / 40000 = 0.0312

Tiempo: 240 min (fin de sesión)
  get_ktv_projected(240.0, 240.0, 500, 10, 300, 0.0)
    → t_restante = 0
    → Retorna: Kt_acumulado / 40000
```

## Debugging

### Ver estado actual
```python
print(f"Kt: {calc.kt_acumulado:.1f} mL")
print(f"D: {calc.d_actual:.1f} mL/min")
print(f"Última medición: {calc.tiempo_ultima_medicion} min")
print(f"V: {calc.volumen_distribucion_v:.1f} mL")
```

### Ver compensación
```python
alpha = 0.021
cd_ef_25 = 13.5 / (1 + alpha * (37.0 - 25))
print(f"13.5 mS/cm @ 37°C → {cd_ef_25:.4f} @ 25°C")
```

### Validar D
```python
if abs(delta_ef) < 0.05:
    print("⚠️ Delta EF muy pequeño, D = 0")
if d > qd + qf_ml_min:
    print("⚠️ D excede límite")
```

## Test Rápido

```bash
cd /ruta/al/proyecto
python -m pytest tests/test_ktv_calculator_ionic.py -v
```

Esperado: ✓ 13 passed

## Notas Importantes

1. **Temperaturas separadas**: EF usa `dialyTempIFProcessData`, SF usa `dialyTempIOFProcessData`
2. **Primera medición especial**: dt=0, no afecta Kt
3. **Sin promedios**: Cada temperatura se compensa individualmente
4. **D solo devuelve D**: No multiplica por tiempo
5. **Acumulación incremental**: Cada llamada suma el intervalo real
6. **Límites estrictos**: D no puede exceder Qd + Qf
7. **Logging abundante**: Revisar logs para debugging
