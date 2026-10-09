# Detalles Técnicos de Implementación de Kt/V Iónico

## Cambios Realizados

### 1. **Archivo: `logic/ktv_calculator.py`**

#### Método `reset()`
Se agregaron tres nuevos atributos que rastrean la acumulación:

```python
self.kt_acumulado: float = 0.0                    # Kt acumulado total
self.tiempo_ultima_medicion: Optional[float] = None  # Marca de tiempo de última medición
self.d_actual: float = 0.0                        # D (dialisancia) actual
```

Estos permiten que la acumulación sea incremental y no dependiente de tiempo total.

#### Método `store_conductivity_t1()` y `store_conductivity_t2()`
Firmaba anterior:
```python
store_conductivity_t1(cd_in, cd_out, temp)
```

Nueva firma:
```python
store_conductivity_t1(cd_in, cd_out, temp_ef, temp_sf)
store_conductivity_t2(cd_in, cd_out, temp_ef, temp_sf)
```

Esto permite compensar cada sensor de conductividad con su propia temperatura.

#### Nuevo método: `calculate_d_ionic(qd, qf, qb, r)`
Computa solo D sin acumular tiempo. Pseudocódigo:

```
1. Obtener C_EF y C_SF a T1 y T2
2. Compensar cada uno a 25°C usando:
   C25 = C_T / (1 + 0.021 * (T - 25))
3. Calcular deltas compensados
4. Si abs(delta_EF) < 0.05: return 0
5. D = (Qd + Qf_mL_min) * (1 - delta_SF / delta_EF)
6. Limitar: D = max(0, min(D, Qd + Qf_mL_min))
7. Aplicar recirculación: D_eff = min(D_eff, D)
8. Retornar D_eff
```

#### Nuevo método: `update_kt(current_time_minutes, qd, qf, qb, r)`
Gestiona la acumulación incremental:

```python
D_actual = calculate_d_ionic(...)

if D_actual <= 0:
    return  # No accumulate if invalid

if tiempo_ultima_medicion is None:
    dt = 0  # Primera medición: no cubre tiempo anterior
else:
    dt = current_time_minutes - tiempo_ultima_medicion
    Kt += D_actual * dt

tiempo_ultima_medicion = current_time_minutes
```

#### Nuevo método: `get_ktv_delivered(current_time_minutes, qd, qf, qb, r)`
Retorna Kt/V acumulado real:

```python
Kt_total = Kt_acumulado

# Si hay un intervalo pendiente desde última medición hasta ahora
if tiempo_ultima_medicion is not None and current_time_minutes > tiempo_ultima_medicion:
    dt_final = current_time_minutes - tiempo_ultima_medicion
    Kt_total += D_actual * dt_final

return Kt_total / V
```

#### Nuevo método: `get_ktv_projected(current_time_minutes, t_total_minutes, qd, qf, qb, r)`
Proyecta Kt/V al final de sesión:

```python
t_restante = max(0, t_total_minutes - current_time_minutes)
Kt_proyectado = Kt_acumulado + (D_actual * t_restante)
return Kt_proyectado / V
```

#### Método deprecado: `calculate_ktv_ionic()`
Ahora solo devuelve D por compatibilidad hacia atrás:

```python
def calculate_ktv_ionic(self, qd, qf, qb, t_min, r=0.0) -> float:
    """DEPRECATED: Use update_kt(), get_ktv_delivered(), get_ktv_projected()"""
    return self.calculate_d_ionic(qd, qf, qb, r)
```

---

### 2. **Archivo: `core/ktv/ktv_controller.py`**

#### Método `_perform_capture_t1()`
Cambio: Obtiene dos temperaturas diferentes

```python
# Anterior:
temp_t1 = current_values.get("dialyTempIFProcessData", 25.0)
self.calculadora_ktv.store_conductivity_t1(cd_in_t1, cd_out_t1, temp_t1)

# Nuevo:
temp_ef_t1 = current_values.get("dialyTempIFProcessData", 25.0)
temp_sf_t1 = current_values.get("dialyTempIOFProcessData", 25.0)
self.calculadora_ktv.store_conductivity_t1(cd_in_t1, cd_out_t1, temp_ef_t1, temp_sf_t1)
```

#### Método `_perform_capture_t2()`
Cambio idéntico al de T1

#### Método `_perform_calculate_ktv()`
Cambio completo de lógica de cálculo:

**Anterior (incorrecto):**
```python
ktv_projected = self.calculadora_ktv.calculate_ktv_ionic(qd, qf, qb, t_programmed_min)
ktv_accumulated = self.calculadora_ktv.calculate_ktv_ionic(qd, qf, qb, t_elapsed_min)
```

Esto era incorrecto porque:
- Llamaba dos veces a un método que devolvía solo D
- No acumulaba incrementalmente
- Multiplicaba D por todo el tiempo transcurrido

**Nuevo (correcto):**
```python
# 1. Actualizar Kt acumulado con la nueva D
self.calculadora_ktv.update_kt(t_elapsed_min, qd, qf, qb, r)

# 2. Obtener Kt/V entregado (acumulado real)
ktv_delivered = self.calculadora_ktv.get_ktv_delivered(t_elapsed_min, qd, qf, qb, r)

# 3. Obtener Kt/V proyectado (expectativa al final)
ktv_projected = self.calculadora_ktv.get_ktv_projected(
    t_elapsed_min, t_programmed_min, qd, qf, qb, r
)

# 4. Obtener valores para logging
d_actual = self.calculadora_ktv.d_actual
kt_acumulado = self.calculadora_ktv.kt_acumulado
```

El diccionario emitido ahora incluye:
```python
results_dict = {
    "ktv_acumulado": ktv_delivered,      # Usar entregado, no proyectado
    "ktv_projectado": ktv_projected,     # Para referencia
    "d_ionic": d_actual,                 # D actual para logging
    "kt_total": kt_acumulado,            # Kt total para logging
    # ... otros campos ...
}
```

---

## Fórmulas Implementadas

### Compensación de Temperatura (DFRobot K=1)
Para cada lectura de conductividad:

```
C_25°C = C_T / (1 + α * (T - 25°C))
```

Donde:
- `C_T` = conductividad a temperatura T
- `α = 0.021` (2.1% por °C)
- `T` = temperatura en °C

**Nota importante:** Se compensa ANTES de restar, no después.

### Cálculo de D (Dialisancia Iónica)
```
delta_EF = EF_2_25°C - EF_1_25°C
delta_SF = SF_2_25°C - SF_1_25°C

Qf_mL/min = Qf_L/h * 1000 / 60

D = (Qd + Qf_mL/min) * (1 - delta_SF / delta_EF)
```

**Restricciones:**
- Si `abs(delta_EF) < 0.05 mS/cm`: D = 0 (medición inválida)
- `0 ≤ D ≤ Qd + Qf_mL/min` (límite superior estricto)

### Corrección por Recirculación
```
D_eff = D * ((1 - r) / (1 - r * (1 - D/Qb)))
D_eff = min(D_eff, D)  # No puede exceder D
```

### Acumulación de Kt
```
Primera medición:
  dt = 0 (no cubre tiempo ya transcurrido)
  Kt = Kt (no cambia)

Mediciones siguientes:
  dt = t_actual - t_última (en minutos)
  Kt = Kt + D * dt
```

### Kt/V Entregado
```
Kt/V = Kt / V
```

Donde V está en mL (resultado de Watson o bioimpedancia × 1000).

### Kt/V Proyectado
```
t_restante = max(0, t_total - t_actual)
Kt/V_proyectado = (Kt + D_actual * t_restante) / V
```

---

## Validación de Entrada

El controlador valida:

1. **Volumen V**
   - Debe ser > 0 (tanto Watson como bioimpedancia)
   - Si no es válido, D = 0.0

2. **Delta de Conductividad**
   - Si `abs(delta_EF) < 0.05 mS/cm`, D = 0.0
   - Previene ruido y división por valores muy pequeños

3. **Parámetros de Flujo**
   - Qd en mL/min
   - Qf en L/h (convertido automáticamente)
   - Qb en mL/min
   - r en [0, 1]

---

## Logging de Diagnóstico

Los logs incluyen (nivel DEBUG e INFO):

```
[KTV_CALC] T1 almacenado: CdEF=13.50, CdSF=13.45, TempEF=37.2, TempSF=37.1
[KTV_CALC] T2 almacenado: CdEF=13.80, CdSF=13.60, TempEF=37.3, TempSF=37.2
[KTV_CALC] D_ionic: delta_EF=0.2892, delta_SF=0.1367, D_raw=268.0, D_limited=268.0, D_efectiva=268.0
[KTV_CALC] Actualización Kt: dt=5.00 min, D=268.0 mL/min, Kt_acumulado=1340.0
[KTV_CALC] Kt/V entregado: dt_final=2.50 min, Kt_total=1340.0, Kt/V=0.268
[KTV_CALC] Kt/V proyectado: t_restante=120.00 min, D_actual=268.0, Kt_proyectado=33440.0, Kt/V=6.688
[KtvController] Cálculo Kt/V: D=268.0 mL/min | Kt=1340.0 | Entregado=0.268 | Proyectado=6.688
```

---

## Pruebas Unitarias

Se incluyen 13 pruebas en `tests/test_ktv_calculator_ionic.py`:

1. ✓ `test_reset_initializes_correctly` - Reset limpia todos los valores
2. ✓ `test_temperature_compensation_single_point` - Fórmula a 25°C correcta
3. ✓ `test_store_conductivity_t1_with_separate_temps` - Almacena temperaturas distintas
4. ✓ `test_calculate_d_ionic_valid_measurement` - D calcula correctamente
5. ✓ `test_calculate_d_ionic_small_delta_ef` - Delta < 0.05 devuelve D=0
6. ✓ `test_accumulate_kt_first_measurement` - Primera medición: dt=0
7. ✓ `test_accumulate_kt_second_measurement` - Segunda: acumula con dt real
8. ✓ `test_get_ktv_delivered` - KTV entregado es correcto
9. ✓ `test_get_ktv_projected` - KTV proyectado es correcto
10. ✓ `test_temperature_difference_impact` - Temperaturas distintas se usan
11. ✓ `test_invalid_volume` - V <= 0 → D = 0
12. ✓ `test_qf_conversion` - Qf L/h → mL/min correcto
13. ✓ `test_no_division_by_zero` - Manejo seguro de edge cases

---

## Interfaz de Usuario

**Durante la terapia (RUNNING):**
- Pantalla principal muestra: "Kt/V Acumulado: `ktv_acumulado`"
- Este es el **Kt/V entregado**, que es el valor real medido hasta el momento

**Al finalizar o detener:**
- Se guarda el **Kt/V entregado** acumulado final
- El controlador suma el último tramo (dt_final) hasta el tiempo real de parada

**Sin cambios significativos de interfaz:**
- El diccionario emitido por KtvController sigue usando las mismas claves
- La GUI recibe los datos igual que antes

---

## Resumen de Correcciones

| Aspecto | Anterior | Nuevo |
|---------|----------|-------|
| Compensación | Promedio de temperaturas | Individual por sensor |
| Sensor SF | Usa temp EF | Usa temp SF (`dialyTempIOFProcessData`) |
| Acumulación | D × tiempo_total | Incremental: Kt += D × dt |
| Primera medición | Afecta Kt | dt=0, no afecta |
| Cálculo D | Incluido en KTV | Separado |
| Interfaz | `calculate_ktv_ionic()` | `update_kt()`, `get_ktv_delivered()`, `get_ktv_projected()` |
| Flujo de datos | Una llamada retorna Kt/V | Dos llamadas: acumular + obtener valores |

---

## Compatibilidad

- ✓ Método deprecado mantiene firmaque anterior para compatibilidad
- ✓ Señales emitidas usan las mismas claves de diccionario
- ✓ No se requieren cambios en GUI
- ✓ No se requieren cambios en almacenamiento de datos existentes
