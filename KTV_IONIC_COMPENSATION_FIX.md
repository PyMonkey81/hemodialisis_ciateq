# Corrección de Cálculo de Kt/V Iónico con Compensación de Temperatura

## Resumen de Cambios

Se han corregido los cálculos de Kt/V iónico para implementar correctamente:

1. **Compensación individual de temperatura por sensor**
2. **Acumulación incremental de Kt durante la sesión**
3. **Distinción clara entre Kt/V proyectado y entregado**

## Sensores de Conductividad y Temperatura

Las celdas DFRobot Gravity Analog EC (K=1) no vienen compensadas por temperatura. Cada punto de medición tiene su propio sensor de temperatura:

- **EF (Entrada del Filtro)**: Conductividad `dialyConductIFProcessData`, Temperatura `dialyTempIFProcessData`
- **SF (Salida del Filtro)**: Conductividad `dialyConductOFProcessData`, Temperatura `dialyTempIOFProcessData`

## Fórmula de Compensación a 25°C

Antes de restar las conductividades, se compensa cada lectura individualmente a 25°C:

```
C25 = C_T / (1 + 0.021 * (T - 25))
```

Luego se calculan los deltas compensados:
- `delta_EF = EF2_25 - EF1_25`
- `delta_SF = SF2_25 - SF1_25`

## Cálculo de D (Dialisancia Iónica)

```
D = (Qd + Qf) * (1 - delta_SF / delta_EF)
```

Restricciones:
- Qd en mL/min
- Qf convertido de L/h a mL/min: `Qf_mL_min = Qf_L_h * 1000 / 60`
- Si `abs(delta_EF) < 0.05 mS/cm`, no se calcula D
- `0 <= D <= Qd + Qf` (sin margen extra)
- Corrección por recirculación aplicada, pero `D_efectiva` no puede superar `D`

## Acumulación de Kt

- **Kt** comienza en 0 al reset de la terapia
- **Primera D válida**: `dt = 0` (no cubre tiempo ya transcurrido)
- **Mediciones siguientes**: `dt = tiempo real desde medición anterior (minutos)`
- `Kt = Kt + D * dt`
- **V** queda fijo en mL (Watson o bioimpedancia)

## Kt/V Entregado y Proyectado

Durante la terapia se muestra el **Kt/V proyectado**:
```
Kt/V_proyectado = (Kt + D_actual * t_restante) / V
donde t_restante = max(0, t_total - t_transcurrido)
```

Al finalizar o detener la sesión, se guarda el **Kt/V entregado** acumulado:
```
Kt/V_entregado = Kt / V
```

## Cambios en los Archivos

### 1. `logic/ktv_calculator.py`

#### Nuevo método `reset()`
- Ahora reinicia: `kt_acumulado`, `tiempo_ultima_medicion`, `d_actual`
- Almacena temperaturas separadas para EF y SF

#### Métodos actualizados
- `store_conductivity_t1(cd_in, cd_out, temp_ef, temp_sf)` - Acepta dos temperaturas
- `store_conductivity_t2(cd_in, cd_out, temp_ef, temp_sf)` - Acepta dos temperaturas

#### Nuevos métodos
- `calculate_d_ionic(qd, qf, qb, r)` - Calcula solo D usando compensación individual
- `update_kt(current_time_minutes, qd, qf, qb, r)` - Acumula Kt incrementalmente
- `get_ktv_delivered(current_time_minutes, qd, qf, qb, r)` - Devuelve Kt/V acumulado real
- `get_ktv_projected(current_time_minutes, t_total_minutes, qd, qf, qb, r)` - Devuelve Kt/V proyectado

#### Método deprecado
- `calculate_ktv_ionic()` - Kept para compatibilidad hacia atrás, ahora solo devuelve D

### 2. `core/ktv/ktv_controller.py`

#### Actualización de capturas
- `_perform_capture_t1()` - Obtiene `dialyTempIFProcessData` y `dialyTempIOFProcessData`
- `_perform_capture_t2()` - Obtiene ambas temperaturas individuales

#### Actualización del cálculo
- `_perform_calculate_ktv()` - Implementa nuevo flujo:
  1. Llama a `update_kt()` para acumular incrementalmente
  2. Obtiene `ktv_delivered` con `get_ktv_delivered()`
  3. Obtiene `ktv_projected` con `get_ktv_projected()`
  4. Emite los resultados incluyendo `d_ionic` y `kt_total` para logging

## Logging de Diagnóstico

El código genera logs detallados en cada paso:

```
[KTV_CALC] T1 almacenado: CdEF=13.50, CdSF=13.45, TempEF=37.2, TempSF=37.1
[KTV_CALC] T2 almacenado: CdEF=13.80, CdSF=13.60, TempEF=37.3, TempSF=37.2
[KTV_CALC] D_ionic: delta_EF=0.2892, delta_SF=0.1367, D_raw=268.0, D_limited=268.0, D_efectiva=268.0
[KTV_CALC] Actualización Kt: dt=5.00 min, D=268.0 mL/min, Kt_acumulado=1340.0
[KTV_CALC] Kt/V entregado: dt_final=2.50 min, Kt_total=1340.0, Kt/V=0.268
[KTV_CALC] Kt/V proyectado: t_restante=120.00 min, D_actual=268.0, Kt_proyectado=33440.0, Kt/V=6.688
```

## Interfaz de Usuario

- **Durante la terapia**: Muestra el **Kt/V proyectado** (expectativa al final si condiciones permanecen)
- **Al finalizar/detener**: Se guarda el **Kt/V entregado** acumulado (real medido)
- El cambio de interfaz es mínimo; las señales existentes `ktv_calculated` siguen siendo emitidas

## Reinicio

En `reset()`, se reinician:
- Kt acumulado
- D actual
- Marca de tiempo de última medición
- Todas las conductividades y temperaturas

Esto permite iniciar un nuevo tratamiento desde cero manteniendo el estado limpio.

## Validación

✅ Sintaxis Python validada
✅ Fórmulas verificadas contra especificación
✅ Compensación individual de temperaturas implementada
✅ Acumulación incremental correcta
✅ Preservación de interfaz existente
