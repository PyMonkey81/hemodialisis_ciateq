# ✅ FIX: La Pantalla de Diálisis No se Cierra si Llega Valor Vacío

## Problema

Un valor `None` o texto en lugar de un número puede lanzar excepción `ValueError` o `TypeError`, causando que:
- La pantalla de diálisis se cerre inesperadamente
- Los gráficos de presión fallent
- El teclado de heparina causa error

Ejemplos:
- `bloodArteryPressureData = None` → `float(None)` → ❌ crash
- `heparineTherapyHours = "error"` → `float("error")` → ❌ crash
- `ultraFilterCycleCount = "texto"` → `float("texto")` → ❌ crash

---

## Solución Implementada

### 1. **dialysis_screenV2.py** - Uso de `safe_float`

#### Cambio 1: Importar `safe_float`
```python
from utilities.platform_runtime import safe_float
```

#### Cambio 2: Proteger `update_values()`
- **Horas/Minutos de terapia** (línea ~733-734)
  - Antes: `float(hep_hours_val) if hep_hours_val is not None else 0.0`
  - Después: `safe_float(hep_hours_val, 0.0)`

- **Pulsos de bomba UF** (línea ~745)
  - Antes: `float(cycle_count_val) if cycle_count_val is not None else 0.0`
  - Después: `safe_float(cycle_count_val, 0.0)`

- **Presiones arterial/venosa** (línea ~754-755)
  - Antes: `venous_pressure_val if venous_pressure_val is not None else 0.0`
  - Después: `safe_float(venous_pressure_val, 0.0)`

#### Cambio 3: Proteger `_format_display_value()`
```python
def _format_display_value(self, tag: str, value):
    # Antes: try/except con float()
    # Después: usar safe_float directamente
    val_float = safe_float(value, 0.0)
    # Rest of logic...
```

### 2. **heparin_config_screenV2.py** - Proteger combo y numpad

#### Cambio 1: `_on_flow_hep_changed()` (línea ~323)
```python
# Antes:
flujo_value = float(self.heparin_flow_combo.currentText())

# Después:
flujo_value = safe_float(self.heparin_flow_combo.currentText(), 0.0)
```

#### Cambio 2: `open_numpad()` (línea ~342)
```python
# Antes:
float_val = float(new_value)

# Después:
float_val = safe_float(new_value, 0.0)
```

#### Cambio 3: `_recalculate_therapy_dosage()` (línea ~698)
```python
# Antes:
flow_ml_per_h = float(self.heparin_flow_combo.currentText())

# Después:
flow_ml_per_h = safe_float(self.heparin_flow_combo.currentText(), 0.0)
```

---

## Función `safe_float`

Ubicada en `utilities/platform_runtime.py:212-228`:

```python
def safe_float(value, default: float = 0.0) -> float:
    """Convierte valores numéricos sin forzar truncamiento al cargar horas persistentes."""
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            return float(stripped)
        return default
    except (TypeError, ValueError):
        return default
```

### Comportamiento:
| Entrada | Salida | Tipo |
|---------|--------|------|
| `None` | `0.0` | float |
| `"texto"` | `0.0` | float |
| `""` (vacío) | `0.0` | float |
| `"  "` (espacios) | `0.0` | float |
| `42` | `42.0` | float |
| `42.5` | `42.5` | float |
| `"-100.5"` | `-100.5` | float |
| `"42.5abc"` | `0.0` | float (ValueError capturado) |

---

## Tests Sin Hardware

**Archivo:** `tests/test_dialysis_screen_safe_values.py`

### Clases de Tests:
1. **TestSafeFloatHandling** (6 tests)
   - None, texto, números válidos, negativos

2. **TestDialysisScreenUpdateValues** (4 tests)
   - `update_values()` con None y texto
   - Horas, minutos, pulsos, presiones

3. **TestPressureWaveformWidgetAddValues** (4 tests)
   - `add_values()` con None y texto
   - Ambos parámetros válidos/inválidos

4. **TestHeparinConfigSafeFloat** (5 tests)
   - Flow combo, numpad, valores válidos

### Resultados:
```
Ran 19 tests in 0.003s
OK ✅
```

---

## Flujo de Ejecución Seguro

### Antes (❌ Inseguro):
```
datos de serial/hardware
    ↓
update_values(new_values)
    ├─ float(None)  ❌ ValueError
    ├─ float("error")  ❌ ValueError
    └─ Exception no capturada
         ↓
    Pantalla se cierra 💥
```

### Después (✅ Seguro):
```
datos de serial/hardware
    ↓
update_values(new_values)
    ├─ safe_float(None, 0.0) → 0.0 ✅
    ├─ safe_float("error", 0.0) → 0.0 ✅
    ├─ safe_float(42.5, 0.0) → 42.5 ✅
    └─ display.setText("0.00 mmHg")
         ↓
    Pantalla sigue funcionando 🎯
```

---

## Campos Protegidos

### dialysis_screenV2.py:
- ✅ `heparineTherapyHours` (duración)
- ✅ `heparineTherapyMinutes` (duración)
- ✅ `ultraFilterCycleCount` (pulsos)
- ✅ `bloodVenousPressureData` (presión)
- ✅ `bloodArteryPressureData` (presión)
- ✅ Kt/V (en `_format_display_value`)

### heparin_config_screenV2.py:
- ✅ `heparin_flow_combo.currentText()` (flujo)
- ✅ `dialog.get_value()` (numpad)
- ✅ Recálculo de dosis

---

## ⚠️ Lo Que No Se Cambió

Por solicitud del usuario:
- ❌ No cambié `core/connection/serial_communication.py` (ya atrapa errores)
- ❌ No cambié el hilo del baumanómetro (ya atrapa errores)
- ❌ No cambié `_master_timer_tick` más allá de lo que ya tenía (ya tiene try/finally)
- ❌ No cambié cálculo de Kt/V
- ❌ No cambié heparina (solo conversión segura)
- ❌ No cambié protocolo serial
- ❌ No cambié teclados de flujo, ultrafiltración, tiempo
- ❌ No cambié el +/− del teclado de alarmas

---

## Validación

### Sintaxis:
```bash
python -m py_compile gui/therapy/dialysis_screenV2.py ✅
python -m py_compile gui/therapy/heparin_config_screenV2.py ✅
```

### Tests:
```bash
python tests/test_dialysis_screen_safe_values.py -v
Ran 19 tests... OK ✅
```

---

## Commit

```
Commit: 4b962e5
Autor: Miguel de Jesus Cuauhtemoc Espinoza Calderon

fix: la pantalla de diálisis no se cierra si llega un valor vacío

Cambios:
- Importar safe_float en dialysis_screenV2.py
- Proteger update_values() con safe_float
- Proteger _format_display_value() con safe_float
- Proteger heparin_config_screenV2.py (3 lugares)
- Agregar 19 tests sin hardware
```

---

## Resultado Final

| Escenario | Antes | Después |
|-----------|-------|---------|
| None llega | ❌ Crash | ✅ Muestra 0.00 |
| Texto llega | ❌ Crash | ✅ Muestra 0.00 |
| Número válido | ✅ Funciona | ✅ Funciona igual |
| Pantalla abierta | ❌ Se cierra | ✅ Sigue funcionando |
| Gráfico | ❌ Error | ✅ Dibuja con 0 |
| Heparina | ❌ Excepción | ✅ Usa valor por defecto |

---

**Status:** ✅ Completado  
**Pruebas:** 19/19 pasan  
**No cambios sin autorización:** ✓  
**Sin push:** ✓
