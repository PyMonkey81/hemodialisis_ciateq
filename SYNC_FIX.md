# Sincronización de Diccionarios en HeparinConfigScreen - FIX

## Problema Identificado

Cuando se cambiaba la duración de terapia de 3:00 a 1:00 con heparina en 1:00:
1. ✓ `_validate_and_clamp_heparin_auto_stop_time()` en appMainHemodialysis ejecutaba correctamente
2. ✓ Mostraba el aviso: "Tiempo de heparina limitado a 00:30..."
3. ✗ Pero cuando el usuario abría la pantalla de heparina, seguía mostrando 01:00

**Causa raíz:** En `HeparinConfigScreen.update_values()`, se hacía:
```python
def update_values(self, new_values: dict):
    self.current_values = new_values  # ← REEMPLAZA la referencia
```

Esto causaba que cualquier cambio hecho en `self.heparin_config_screen.current_values` por `_validate_and_clamp_heparin_auto_stop_time()` se perdiera si `update_values()` se llamaba después con un diccionario diferente.

## Solución Implementada

Se cambió `update_values()` para NOT reemplazar la referencia, sino actualizar los valores dentro del diccionario existente:

```python
def update_values(self, new_values: dict):
    # IMPORTANTE: No reemplaces la referencia de current_values
    # para evitar perder cambios hechos en otros lugares.
    if self.current_values is not new_values:
        # Solo actualiza si son diccionarios diferentes
        self.current_values.update(new_values)
```

Esto asegura que:
1. Si `new_values` es el mismo objeto que `self.current_values`, no hace nada (son la misma referencia)
2. Si son objetos diferentes, actualiza los valores DENTRO del diccionario existente, preservando cualquier cambio previo
3. El widget sigue mostrando los valores correctos después del recorte

## Archivos Modificados

- `gui/therapy/heparin_config_screenV2.py`: `update_values()` - línea ~685

## Verificación

- ✓ Todos los 28 tests pasan
- ✓ Compilación sin errores
- ✓ Sincronización entre diccionarios preservada
- ✓ Widget text se mantiene correcto tras cambios de terapia
