# Corrección: Cuadro de Colocar Filtro en Estado 7

## Resumen
Se corrigió el cuadro de diálogo de colocar filtro en `gui/appMainHemodialysis.py` para seguir las reglas específicas de apertura, validación y cierre.

---

## Reglas Implementadas

### 1. **Una sola vez por cebado**
- El cuadro se resetea cuando entra a estado 1 o 16 (inicio de cebado nuevo)
- Se marca con `_last_status_prompt = 7` solo cuando se envía el pulso de filtro
- No se reabre si `_last_status_prompt == 7` ya está marcado
- No se reabre desde estado 9 u otros estados si regresa a 7

### 2. **Ventanas de Validación (NO bandas)**
- **Temperatura:** `setpoint - 5` a `setpoint + 3` (ventana asimétrica)
- **Conductividad:** `setpoint ± 2` (ventana simétrica, ignorando `dialyConductLoLimitBand` y `dialyConductHiLimitBand`)

**IMPORTANTE:** La banda se usa solo en el firmware para bypass, no en la interfaz.

### 3. **Encabezado en Estado 7**
- **Sin condiciones:** `"ESPERANDO CONDICIONES"`
- **Con condiciones:** `"COLOCAR FILTRO"`
- Se actualiza en `_update_header_during_filter_fill()`

### 4. **Lógica de Apertura**
- Solo en estado 7 cuando ambas condiciones están en rango
- Se llama desde `primingProcessStatus` solo cuando entra a 7 desde 1 o 16
- **NO** se llama desde cada lectura de `dialyTempIFProcessData` ni `dialyCondVariableData`
- Se protege con:
  - `if self._filter_fill_dialog is not None: return` (no abrir si ya está abierto)
  - `if self._last_status_prompt == 7: return` (no abrir si ya se preguntó)

### 5. **Cierre Correcto del Diálogo**
Cuando se sale de estado 7 (a bypass u otro estado):
```python
if hasattr(self._filter_fill_dialog, '_event_loop') and self._filter_fill_dialog._event_loop:
    if self._filter_fill_dialog._event_loop.isRunning():
        self._filter_fill_dialog._event_loop.quit()
```
- Esto sale del `QEventLoop` del diálogo, no solo lo esconde con `close()`
- La salida no es "Cancelar" (no reagenda el cuadro)

### 6. **Flujo de Dos Diálogos**
1. **Primer diálogo:** "Coloque el filtro..." (botón Cancelar oculto)
2. **Segundo diálogo:** "¿Confirma que el filtro ya está colocado?" (Aceptar + Cancelar)
   - **Aceptar:** Valida temperatura y conductividad, envía `dialyFilterFillButton`, arranca timer de 90s
   - **Cancelar:** Regresa al primer diálogo en 100ms

### 7. **Estado 13 (READY)**
- Sigue en `"PREPARANDO..."` hasta que pasen 90s desde el pulso del filtro
- Solo entonces muestra `"LISTO PARA INICIAR"` (si `_can_start_treatment()` es True)
- Mantiene `"PREPARANDO..."` si aún no se cumplen condiciones de inicio

---

## Cambios en el Código

### `_show_filter_fill_dialog_main()`
- **Antes:** Usaba `dialyConductLoLimitBand` y `dialyConductHiLimitBand`
- **Después:** Usa `cond_set ± 2.0` directamente
- **Antes:** No protegía contra reaperturas desde sensores
- **Después:** Protección completa en `_check_filter_fill_conditions_in_state_7()`

### `_check_filter_fill_conditions_in_state_7()`
- **Nuevo:** Añade protecciones:
  - Si `_filter_fill_dialog is not None`: no hace nada
  - Si `_last_status_prompt == 7`: no hace nada
  - Si `_last_status_prompt == 7` pero faltan condiciones: resetea para re-preguntar
- **Antes:** Se llamaba desde cada lectura de sensores (ineficiente)
- **Después:** Se llama solo desde `primingProcessStatus` en transiciones 1→7 o 16→7

### `_update_header_during_filter_fill()`
- **Antes:** Usaba bandas para conductividad
- **Después:** Usa `±2` del setpoint
- Ahora el encabezado es la fuente única de verdad para estado 7 y 13

### Manejo de `primingProcessStatus`
- **Nuevo:** Reset en estado 1 o 16:
  ```python
  if status_code in (1, 16):
      self._reset_filter_fill_flags()
      self._last_status_prompt = None
  ```
- **Nuevo:** Solo reevalúa en estado 7 si viene de 1 o 16:
  ```python
  if status_code == 7 and prev_status in (1, 16):
      QTimer.singleShot(100, self._check_filter_fill_conditions_in_state_7)
  ```
- **Simplificado:** Cierre con `quit()` del event loop en lugar de `close()`

---

## Eliminaciones

Fueron eliminadas estas llamadas innecesarias en `update_value()`:
```python
# Eliminado: Llamadas desde dialyTempIFProcessData
# self._check_filter_fill_conditions_in_state_7()

# Eliminado: Llamadas desde dialyCondVariableData
# self._check_filter_fill_conditions_in_state_7()
```

---

## Testing

✅ **Sintaxis verificada:** `python -m py_compile gui\appMainHemodialysis.py`

**Casos de prueba esperados:**
1. Iniciar cebado (estado 1) → entra a 7 sin condiciones → encabezado "ESPERANDO CONDICIONES"
2. Temperatura y conductividad llegan a rango → cuadro abierto una vez
3. Usuario presiona Aceptar → segundo cuadro → valida y envía pulso → estado 13
4. Estado 13 espera 90s → pasa a "LISTO PARA INICIAR"
5. Si sale de estado 7 (bypass) → cierra QEventLoop del diálogo
6. Si regresa a 7 desde 9 → NO abre cuadro de nuevo (ya se preguntó)
7. Vuelve a cebado (estado 1 o 16) → resetea todo y permite preguntar de nuevo

---

## Commit
- **Hash:** `2caad8d`
- **Mensaje:** "Corregir cuadro de colocar filtro en estado 7"
- **Archivo:** `gui/appMainHemodialysis.py`
- **Líneas modificadas:** ~62 insertadas, ~101 eliminadas (neto: -39)

---

## Referencias de Código

| Función | Línea | Cambio |
|---------|-------|--------|
| `_show_filter_fill_dialog_main()` | ~1371 | Usar `±2` en conductividad |
| `_check_filter_fill_conditions_in_state_7()` | ~2897 | Protecciones contra reaperturas |
| `_update_header_during_filter_fill()` | ~2933 | Usar `±2` en conductividad |
| `update_value()` | ~3205 | Eliminar llamadas desde sensores |
| `primingProcessStatus` | ~3267 | Reset en 1/16, eval en 7 desde 1/16 |
| `_filter_fill_dialog` close | ~3273 | Usar `quit()` en event loop |

---

**Estado:** ✅ Completado
**Actualizado:** 2026-11-13
**Repositorio:** https://github.com/PyMonkey81/hemodialisis_ciateq
