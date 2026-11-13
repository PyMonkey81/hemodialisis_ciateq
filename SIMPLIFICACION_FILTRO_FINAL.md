# Simplificación Final: Llenado de Filtro (Commit fd9d573)

## Problema Identificado
**Stack Overflow por recursión en QEventLoop:**
- Cada lectura de `dialyTempIFProcessData` y `dialyCondVariableData` 
- Llamaba a `_check_filter_fill_conditions_in_state_7()`
- Que abría `_show_filter_fill_dialog_main()` con `QTimer.singleShot()`
- Dentro de un QEventLoop ya activo
- → Recursión infinita → Crash de la aplicación

## Solución: Simplificación Total

### ✅ NUEVA LÓGICA (SIN DIÁLOGOS)

**Al entrar a estado 7 SOLO desde 1 o 16:**
```python
if status_code == 7 and prev_status in (1, 16) and self._last_status_prompt != 7:
    self._filter_fill_button_sent = True
    self._write_boolean_command("dialyFilterFillButton", True)
    self._start_filter()
    self._last_status_prompt = 7
```

- ✅ **Sin diálogos**
- ✅ **Sin validaciones de sensores**
- ✅ **Sin QTimer**
- ✅ **Sin recursión**
- ✅ Una sola vez por cebado (marcado con `_last_status_prompt`)

### 🗑️ ELIMINADO

| Elemento | Estado |
|----------|--------|
| `_show_filter_fill_dialog_main()` | Sin uso (pass) |
| `_check_filter_fill_conditions_in_state_7()` | Sin uso (pass) |
| Llamadas desde `dialyTempIFProcessData` | ✅ Removidas |
| Llamadas desde `dialyCondVariableData` | ✅ Removidas |
| `QTimer.singleShot()` para diálogos | ✅ Removidos |
| Validaciones de conductividad/temperatura | ✅ Removidas |
| Cierre con `quit()` del event loop | ✅ No necesario |
| Encabezado "ESPERANDO CONDICIONES" | ✅ Eliminado |
| Encabezado "COLOCAR FILTRO" | ✅ Eliminado |

### 📊 Estadísticas del Cambio

- **Commits:** 2
  1. `5a7784f` - Documentar corrección de cuadro de filtro (REVERTIDO)
  2. `2caad8d` - Corregir cuadro de colocar filtro (REVERTIDO)
  3. `fd9d573` - **Simplificar llenado de filtro: envío automático sin diálogo** ✅

- **Líneas eliminadas:** 150+
- **Líneas modificadas en main:** -150 netas

### 🎯 Comportamiento Final

| Evento | Acción |
|--------|--------|
| **Estado 1 o 16** | Resetea `_last_status_prompt` |
| **Entra a 7 desde 1/16** | Envía `dialyFilterFillButton=True` + `_start_filter()` |
| **Regresa a 7 desde 9+** | NO re-envía pulso (ya marcado) |
| **Estado 13 (0-90s)** | Encabezado "PREPARANDO..." |
| **Estado 13 (90s+)** | Encabezado "LISTO PARA\nINICIAR" |

### ✅ Requisitos Cumplidos

- ✅ No llamar a diálogos ni `_check_filter_fill_conditions_in_state_7` desde sensores
- ✅ Quitar QTimer que abrían cuadros
- ✅ Al entrar a 7: mandar `dialyFilterFillButton=True` automáticamente
- ✅ Marca se borra solo en estado 1 o 16
- ✅ Si regresa a 7 desde bypass: no re-enviar pulso
- ✅ No cambiar botones de cebado ni de terapia
- ✅ Sin stack overflow, sin recursión, sin diálogos

---

**Estado:** ✅ COMPLETADO Y DEPLOYABLE
**Actualizado:** 2026-11-13
**Repositorio:** https://github.com/PyMonkey81/hemodialisis_ciateq
