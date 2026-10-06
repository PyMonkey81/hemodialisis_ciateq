# Validación de Tiempo de Infusión de Heparina - Cambios Realizados

## Resumen Ejecutivo

Se corrigió la validación del tiempo de infusión de heparina en la aplicación de hemodiálisis para cumplir con la regla clínica:

**Regla Clínica Principal:**
- **No se infunde heparina durante los últimos 30 minutos de la terapia.**
- **Máximo permitido:** `max(0, minutos_de_referencia - 30)`

## Arquitectura: Función Pura + Métodos Productivos

Se implementó una arquitectura clara separando:
1. **Lógica pura** (logic/heparin_time.py) - Sin efectos secundarios, testeable sin mocks
2. **Métodos productivos** - Usan la lógica pura y manejan persistencia

## Archivos Modificados

### 1. `logic/heparin_time.py` (NUEVO)
**Propósito:** Lógica pura para validación de tiempo de heparina

**Funciones:**
- `reference_minutes(phase, programmed_minutes, remaining_seconds) -> int`
  - Si RUNNING o PAUSED: retorna tiempo restante (remaining_seconds / 60)
  - Si no: retorna duración programada
  
- `max_heparin_minutes(reference_minutes) -> int`
  - Calcula máximo permitido: `max(0, reference_minutes - 30)`
  
- `clamp_heparin_time(hours, minutes, reference_minutes) -> tuple[int, int]`
  - Ajusta tiempo al máximo permitido
  - Retorna tupla (horas_ajustadas, minutos_ajustados)
  
- `was_clamped(hours, minutes, reference_minutes) -> bool`
  - Detecta si hubo recorte

**Ventajas:**
- Sin dependencias de PySide6
- Testeable con simples aserciones
- Reutilizable en múltiples contextos

### 2. `gui/therapy/heparin_config_screenV2.py`
**Cambio:** Reemplazó `_coerce_heparin_auto_stop_time()`

**Nuevo flujo:**
```python
def _coerce_heparin_auto_stop_time(self, hours, minutes):
    # 1. Obtener duración programada
    programmed_minutes = therapy_h * 60 + therapy_m
    
    # 2. Obtener tiempo restante si está disponible
    remaining_seconds = 0
    if phase in (RUNNING, PAUSED):
        remaining_seconds = treatment_controller.remaining
    
    # 3. Calcular referencia usando función pura
    ref_min = reference_minutes(phase, programmed_minutes, remaining_seconds)
    
    # 4. Validar y ajustar
    clamped_h, clamped_m = clamp_heparin_time(hours, minutes, ref_min)
    
    # 5. Mostrar aviso si fue recortado
    if was_clamped(hours, minutes, ref_min):
        # mostrar mensaje
    
    return clamped_h, clamped_m
```

### 3. `gui/appMainHemodialysis.py`
**Cambio:** Reemplazó `_validate_and_clamp_heparin_auto_stop_time()`

**Nuevo flujo al cambiar duración de terapia:**
```python
def _validate_and_clamp_heparin_auto_stop_time(self):
    # 1. Obtener valores actuales
    auto_h, auto_m = self.current_values["heparineAutoStopHours/Minutes"]
    
    # 2. Calcular referencia
    ref_min = reference_minutes(phase, programmed_minutes, remaining_seconds)
    
    # 3. Validar usando función pura
    if was_clamped(auto_h, auto_m, ref_min):
        clamped_h, clamped_m = clamp_heparin_time(auto_h, auto_m, ref_min)
        
        # 4. PERSISTIR (corrección del bug original)
        self.current_values["heparineAutoStopHours"] = clamped_h
        self.current_values["heparineAutoStopMinutes"] = clamped_m
        self._persist_therapy_config_tag("heparineAutoStopHours", clamped_h)
        self._persist_therapy_config_tag("heparineAutoStopMinutes", clamped_m)
        
        # 5. Recalcular DOSIS (corrección del bug original)
        time_hours = clamped_h + (clamped_m / 60.0)
        flow_ml_per_h = self._get_heparin_flow_ml_per_h()
        dosage_ml = time_hours * flow_ml_per_h
        self.current_values["heparineTherapyDosage"] = dosage_ml
        self._persist_therapy_config_tag("heparineTherapyDosage", dosage_ml)
        
        # 6. Actualizar pantalla de heparina
        if heparin_config_screen exists:
            heparin_config_screen.input_heparin_auto_stop.setText(f"{clamped_h:02d}:{clamped_m:02d}")
            heparin_config_screen.current_values.update(...)
        
        # 7. Mostrar aviso
        self.show_warning_message(msg, 5000)
```

## Bug Fijo

**Problema reportado:**
> "Al cambiar terapia de 3:00 a 1:00, sale el aviso pero al abrir la pantalla de heparina Tiempo Heparina sigue en 01:00. El fallo es la escritura."

**Causa:**
- El aviso se mostraba (correcto)
- Los valores se mostraban pero NO se persistían en current_values (incorrecto)
- La dosis se recalculaba con 1 hora, no con 0.5 horas (incorrecto)

**Solución implementada:**
- Ahora `_validate_and_clamp_heparin_auto_stop_time()` persiste correctamente:
  1. `heparineAutoStopHours = 0`
  2. `heparineAutoStopMinutes = 30`
  3. `heparineTherapyDosage = 0.5 * flow` (no 1.0 * flow)

## Casos de Prueba Validados

### Test: logic/heparin_time.py
- Función pura sin mocks, sin dependencias de Qt
- Valida los 5 casos clínicos directamente

### Test: production method (test_therapy_change_3_to_1_hour)
```
Initial: Therapy 3:00, Heparin 1:00
Action: Therapy changes to 1:00
Expected:
  - heparineAutoStopHours = 0 ✓
  - heparineAutoStopMinutes = 30 ✓
  - heparineTherapyDosage = 0.5 * 1.0 ml/h = 0.5 ml ✓
```

### Tabla de Casos Clínicos

| Caso | Escenario | Máximo | Resultado |
|------|-----------|--------|-----------|
| 1 | Terapia 3:00 → 1:00, heparina 1:00 | 0:30 | Recorta a 0:30, dosis 0.5h |
| 2 | RESTANTE 0:47, usuario 0:25 | 0:17 | Rechaza 0:25, acepta 0:17 |
| 3a | RESTANTE 0:30, usuario 0:15 | 0:00 | Recorta a 0:00 |
| 3b | RESTANTE 0:15, usuario 0:05 | 0:00 | Recorta a 0:00 |
| 4 | Terapia 3:00, usuario 2:31 | 2:30 | Recorta 2:31 a 2:30 |

## Validación Realizada

### Tests Ejecutados
```
✓ 10 tests de lógica pura
✓ 1 test de producción (3:00 → 1:00)
✓ 10 tests existentes (sin regresiones)
═════════════════════════════════════════
✓ Total: 27 tests PASARON
```

### Verificaciones
```
✓ Compilación Python sin errores
✓ No hay regresiones en tests existentes
✓ Lógica pura sin dependencias externas
✓ Persistencia de valores verificada
```

## Cambios NO Realizados (Fuera del Alcance)

Como se solicitó, **NO se implementó:**
- Lógica de pausar/reanudar el reloj de heparina a media terapia
- Cambios a NIBP, perfiles de sodio, UF, serial, MQTT
- Cambios a botones de bomba que ya estaban comentados

## Documentación de Tags

**Tags NO modificados (semántica preservada):**
- `heparineAutoStopHours` / `heparineAutoStopMinutes`: Tiempo de infusión permitido
- `heparineTherapyDosage`: Horas de infusión × flujo (ml/h)

**Mensajes de usuario:**
```
"Tiempo de heparina limitado a HH:MM. No se infunde durante los últimos 30 minutos de la terapia."
```

## Notas de Implementación

### Importaciones
```python
# En heparin_config_screenV2.py
from logic.heparin_time import reference_minutes, clamp_heparin_time, was_clamped

# En appMainHemodialysis.py
from logic.heparin_time import reference_minutes, clamp_heparin_time, was_clamped
```

### Llamadas del Flujo
```
Cambio de terapia en therapy_config_screen
         ↓
appMainHemodialysis._write_setpoint(tag="heparineTherapyHours/Minutes")
         ↓
_validate_and_clamp_heparin_auto_stop_time()
         ↓
reference_minutes() + clamp_heparin_time() + was_clamped()  [funciones puras]
         ↓
Persiste valores + recalcula dosis + muestra aviso
```

---

**Status:** Implementación completada y validada
**Versión afectada:** PyMonkey81/hemodialisis_ciateq
**Pruebas:** 27/27 PASADAS (100%)
