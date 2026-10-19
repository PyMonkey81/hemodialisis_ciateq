# Fase 2: Preparación del Card de Ultrafiltración (UF)

## Resumen de Cambios

Se han completado las siguientes tareas para preparar el card de ultrafiltración en la pantalla de diálisis:

### 1. **Remapeo de Variable Hardware** (`core/variables_map.py`)

**Cambio:**
- **Antes:** Grupo 0x04, Dirección 0x17 contenía `variableCtrlParamData2` (variable de control genérica)
- **Después:** Reemplazada con `ufPumpPulseCount` (acumulado de pulsos de la bomba UF)

**Detalles:**
```python
0x17: {
    "name": "Acumulado de pulsos de bomba UF",
    "label": "PULSOS UF",
    "type": "int",  # Tipo entero (no double)
    "rw": False,     # Solo lectura (no escritura)
    "unit": "pulsos",
    "limites": (0, 1e9),  # Límites amplios
    "tag": "ufPumpPulseCount",
    "nivel": "cian"
}
```

**Propósito:** Recibir del firmware el acumulado de pulsos de la bomba UF para calcular el volumen total ultrafiltrado.

---

### 2. **Nueva Lógica de Cálculo de Volumen** (`logic/uf_volume.py`)

**Archivo creado:** Módulo puro sin dependencias de PySide6 ni hardware.

**Contenido:**
- **Constante:** `UF_PUMP_ML_PER_PULSE = 1.0` (ml/pulso)
  - Comentario: Debe reemplazarse con el valor real del desplazamiento de la hoja de datos
- **Función:** `litros_removidos(pulsos: int) -> float`
  - Convierte pulsos a litros: `litros = pulsos × 1.0 / 1000`
  - Retorna 0.0 si pulsos < 0 (protección contra valores inválidos)
  - Redondea a 2 decimales

**Validación:**
```python
litros_removidos(1000)  → 1.00 L
litros_removidos(500)   → 0.50 L
litros_removidos(-100)  → 0.00 L
litros_removidos(0)     → 0.00 L
```

---

### 3. **Actualización del Card UF en Pantalla de Diálisis** (`gui/therapy/dialysis_screenV2.py`)

**Cambio en `update_values()`:**

El método ahora calcula y actualiza tres valores del card UF:

#### a) **Tasa (L/h)**
```python
uf_rate = float(self.current_values.get("ultraFilterPumpSpeed", 0.0))
self.uf_rate_val.setText(f"{uf_rate:.2f}")
```
- Se toma directamente de `ultraFilterPumpSpeed` (el setpoint actual de la bomba)
- No es un cálculo derivado; es el valor deseado del control

#### b) **Objetivo (L)**
```python
uf_therapy_hours = float(self.current_values.get("heparineTherapyHours", 0.0))
uf_therapy_minutes = float(self.current_values.get("heparineTherapyMinutes", 0.0))
therapy_duration_hours = uf_therapy_hours + (uf_therapy_minutes / 60.0)

uf_goal = uf_rate * therapy_duration_hours
self.uf_goal_val.setText(f"{uf_goal:.2f} L")
```
- **Fórmula:** Tasa (L/h) × Duración Programada (horas)
- **Ejemplo:** 1 L/h × 3:00 h = 3.00 L
- **Nota:** Si hay un perfil de UF activo (futuro), no multiplicar la tasa instantánea por toda la duración

#### c) **UF Removida (L)**
```python
uf_pulse_count = float(self.current_values.get("ufPumpPulseCount", 0.0))
uf_removed = litros_removidos(int(uf_pulse_count))
self.uf_rem_val.setText(f"{uf_removed:.2f} L")
```
- Usa la función `litros_removidos()` con el acumulado de pulsos
- Refleja el volumen real removido en tiempo real

**Import agregado:**
```python
from logic.uf_volume import litros_removidos
```
Con fallback a una función dummy si no se puede importar.

---

### 4. **Estilo Deshabilitado para Tiempo de Heparina** (`gui/therapy/heparin_config_screenV2.py`)

**Cambio:** Se agregó la regla `:disabled` al stylesheet `input_style` para asegurar que cuando el campo de tiempo de heparina se deshabilite en RUNNING/PAUSED, se vea igual que el campo de "Vol. Heparina en Jeringa" deshabilitado.

**Antes:**
```css
input_style = """
    ClickableLineEdit {
        font-family: Consolas, "Courier New", monospace;
        font-size: 24px;
        color: #000000;
        background: #e2e8f0;
        border: 2px solid #64748b;
        border-radius: 8px;
        padding: 5px;
        min-width: 120px;
    }
    ClickableLineEdit:focus {
        border: 2px solid #3b82f6;
        background: #ffffff;
    }
"""
```

**Después:**
```css
input_style = """
    ClickableLineEdit {
        font-family: Consolas, "Courier New", monospace;
        font-size: 24px;
        color: #000000;
        background: #e2e8f0;
        border: 2px solid #64748b;
        border-radius: 8px;
        padding: 5px;
        min-width: 120px;
    }
    ClickableLineEdit:focus {
        border: 2px solid #3b82f6;
        background: #ffffff;
    }
    ClickableLineEdit:disabled {
        color: #94a3b8;
        background-color: #f1f5f9;
        border: 2px solid #cbd5e1;
    }
"""
```

**Colores deshabilitados:**
- Fondo: `#f1f5f9` (gris claro)
- Texto: `#94a3b8` (gris oscuro)
- Borde: `#cbd5e1` (gris medio)

---

## Validación Realizada

Se creó y ejecutó un test unitario que validó:

✅ `litros_removidos(1000)` retorna 1.00 L  
✅ `litros_removidos(500)` retorna 0.50 L  
✅ `litros_removidos(-100)` retorna 0.00 L  
✅ `litros_removidos(0)` retorna 0.00 L  
✅ Redondeo correcto a 2 decimales  
✅ Cálculo de objetivo: 1 L/h × 3 h = 3.00 L  
✅ Cálculo de objetivo con minutos: 1 L/h × 3:30 h = 3.50 L  
✅ Constante `UF_PUMP_ML_PER_PULSE = 1.0`

---

## Archivos Modificados

1. **core/variables_map.py**
   - 1 línea modificada (variable 0x17 en grupo 0x04)

2. **logic/uf_volume.py** ✨ NUEVO
   - 37 líneas (módulo completo con documentación)

3. **gui/therapy/dialysis_screenV2.py**
   - Import de `litros_removidos` agregado
   - Función `update_values()` completamente reescrita para el card UF
   - Cálculo de tasa, objetivo y UF removida

4. **gui/therapy/heparin_config_screenV2.py**
   - Regla `:disabled` agregada a `input_style` (2 occurrencias)

---

## Próximos Pasos (Futuro)

1. **Perfil de UF Activo:** Si se implementa un perfil de ultrafiltración variable, ajustar el cálculo del objetivo en `dialysis_screenV2.py` para no multiplicar la tasa instantánea por toda la terapia.

2. **Constante Real:** Reemplazar `UF_PUMP_ML_PER_PULSE = 1.0` con el valor real del desplazamiento de la bomba UF de la hoja de datos.

3. **Integración Hardware:** Asegurar que el firmware envíe correctamente el acumulado de pulsos en la variable `ufPumpPulseCount` (grupo 0x04, dirección 0x17).

---

## Commit

```
Preparar card de ultrafiltración: remapear variable UF, lógica de cálculo y estilo deshabilitado

- core/variables_map.py: Reemplazar variableCtrlParamData2 con ufPumpPulseCount
- logic/uf_volume.py: Crear módulo con constante y función de cálculo
- gui/therapy/dialysis_screenV2.py: Actualizar card UF con tasa, objetivo y UF removida
- gui/therapy/heparin_config_screenV2.py: Agregar estilo deshabilitado al tiempo de heparina
```

Commit ID: `0e58c18`
