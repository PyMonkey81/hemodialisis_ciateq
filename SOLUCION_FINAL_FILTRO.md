# Solución Final: Cuadro de Filtro sin Validaciones (Commit 3eccfca)

## Problema Original
Stack overflow causado por recursión en QEventLoop:
- Cada lectura de sensores (`dialyTempIFProcessData`, `dialyCondVariableData`)
- Llamaba `_check_filter_fill_conditions_in_state_7()`
- Que abría diálogos dentro de un QEventLoop activo
- **Resultado:** Recursión infinita → CRASH

## Solución Implementada

### ✅ CUADRO DE FILTRO FUNCIONAL (SIN VALIDACIONES)

**El cuadro "Coloque el filtro" se mantiene con flujo de dos pasos:**

1. **Primer Cuadro**
   - Texto: "Coloque el filtro. Cuando esté colocado, presione Aceptar."
   - Botón Cancelar: **oculto**
   - Solo opción: Aceptar

2. **Segundo Cuadro** (si acepta en primero)
   - Texto: "¿Confirma que el filtro ya está colocado?"
   - Botones: Aceptar + Cancelar (ambos visibles)
   - **Aceptar:** Envía `dialyFilterFillButton=True` + `_start_filter()` → SIN validaciones
   - **Cancelar:** Regresa al primer cuadro

### 🎯 COMPORTAMIENTO CLAVE

| Evento | Acción |
|--------|--------|
| **Entra a 7 desde 1/16** | Abre cuadro (UNA SOLA VEZ) |
| **Ya hay cuadro abierto** | NO abre otro |
| **Regresa a 7 desde 9+** | NO abre nuevamente (marcado) |
| **Sale de estado 7** | quit() QEventLoop, no lo esconde solo |
| **Estado 1 o 16** | Resetea marca para próximo cebado |
| **Aceptar (2do cuadro)** | Envía pulso sin validaciones |
| **Cancelar (2do cuadro)** | Regresa al 1er cuadro (operador) |

### 🗑️ ELIMINADO COMPLETAMENTE

- ✅ Validaciones de conductividad (±2 del setpoint)
- ✅ Validaciones de temperatura (setpoint±5 a setpoint+3)
- ✅ Comparación contra `dialyConductLoLimitBand` y `dialyConductHiLimitBand`
- ✅ Llamadas desde `dialyTempIFProcessData` update
- ✅ Llamadas desde `dialyCondVariableData` update
- ✅ Encabezado "ESPERANDO CONDICIONES"
- ✅ Encabezado "COLOCAR FILTRO" dinámico (usa el del mapa)
- ✅ Función `_check_filter_fill_conditions_in_state_7()` (inútil, paso)
- ✅ Llamada a `_update_header_during_filter_fill()` en estado 7

### 📊 Cambios Finales

```
git log --oneline (últimos 5):
3eccfca Restituir cuadro de filtro sin validaciones de sensores ← FINAL
6cbe2ed Documentar simplificación final del llenado de filtro (revertido)
fd9d573 Simplificar llenado de filtro: envío automático (revertido)
5a7784f Documentar corrección de cuadro de filtro en estado 7 (revertido)
2caad8d Corregir cuadro de colocar filtro en estado 7 (revertido)
```

**Líneas modificadas en commit 3eccfca:**
- +93, -18 (neto +75)
- Función `_show_filter_fill_dialog_main()` restaurada
- Lógica de primingProcessStatus simplificada
- Cuadro abre una sola vez, sin recursión

### ✅ REQUISITOS CUMPLIDOS

1. ✅ Cuadro "Coloque el filtro" se muestra
2. ✅ Primer cuadro sin Cancelar (botón oculto)
3. ✅ Segundo cuadro con Aceptar + Cancelar
4. ✅ Aceptar: envía `dialyFilterFillButton=True` + `_start_filter()` sin validaciones
5. ✅ Cancelar: regresa al primer cuadro (acción del operador)
6. ✅ Abre UNA SOLA VEZ al entrar a 7 desde 1 o 16
7. ✅ NO abre si ya hay cuadro abierto
8. ✅ NO abre si regresa de 9 u otro estado (marcado)
9. ✅ Al salir de 7: quit() QEventLoop (no solo close())
10. ✅ NO es Cancelar, NO reagenda
11. ✅ Marca se borra solo en estado 1 o 16
12. ✅ Sin validaciones de sensores
13. ✅ Sin recursión en QEventLoop
14. ✅ Sin llamadas desde actualización de sensores
15. ✅ Encabezado estado 7: "COLOCAR FILTRO" (del mapa)
16. ✅ No cambiar botones de cebado ni de terapia

### 🔍 Código Principal

**Apertura del cuadro (primingProcessStatus):**
```python
if status_code == 7 and prev_status in (1, 16) and self._last_status_prompt != 7 and self._filter_fill_dialog is None:
    logger.info("[FILTER] Abriendo cuadro de filtro.")
    QTimer.singleShot(0, self._show_filter_fill_dialog_main)
    self._last_status_prompt = 7
```

**Cierre al salir de estado 7:**
```python
if prev_status == 7 and status_code != 7:
    if self._filter_fill_dialog is not None:
        if hasattr(self._filter_fill_dialog, '_event_loop') and self._filter_fill_dialog._event_loop:
            if self._filter_fill_dialog._event_loop.isRunning():
                self._filter_fill_dialog._event_loop.quit()
```

**Encabezado (NO se modifica):**
```python
# El mapa proporciona "COLOCAR FILTRO" para estado 7
display_text = self.hardware_mapper.get_display_text(status_code, treatment_mode)
self.current_process_status.setText(display_text)
# No hay actualización dinámica
```

---

**Estado:** ✅ **COMPLETADO, TESTEADO Y DEPLOYABLE**
**Commit:** `3eccfca` - Restituir cuadro de filtro sin validaciones de sensores
**Repositorio:** https://github.com/PyMonkey81/hemodialisis_ciateq
