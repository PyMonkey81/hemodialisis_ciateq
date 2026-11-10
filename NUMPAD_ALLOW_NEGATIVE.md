# Numpad: allow_negative desde variables_map

Fecha: 10 de noviembre de 2026  
Cambio: Numpad muestra +/− basado en límites iniciales, no en valores guardados.

## Descripción

En `open_numpad()`, el parámetro `allow_negative` ahora se obtiene de `get_default_limits_from_variables_map()` en lugar de `get_limits()`.

**Beneficio**: Las presiones (arterial, venosa, PTM) siempre pueden capturarse en negativo, incluso si el valor guardado es 0 o positivo.

## Archivo Modificado

### `gui/configuration/alarm_screen_config.py`

**Línea 220-232** — Función `open_numpad()`:

```python
def open_numpad(self, line_edit, tag, param_name, field):
    # Obtener los límites INICIALES del mapa para determinar allow_negative
    # Esto permite que presión arterial, venosa y PTM siempre puedan capturarse en negativo
    min_val_default, max_val_default = self.config_manager.get_default_limits_from_variables_map(tag)
    allow_negative = min_val_default < 0
    
    # Título sin la unidad, mostrando el nombre legible del parámetro
    dialog = NumpadDialog(self, initial_value="", 
                         title=f"Límite {field.upper()} \n {param_name}",
                         allow_negative=allow_negative)
    
    if dialog.exec():
        val = dialog.get_value()
        line_edit.setText(f"{val:.1f}")
```

## Cambio de Lógica

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Origen de límites | `get_limits()` (guardados) | `get_default_limits_from_variables_map()` (iniciales) |
| Determina | Si valor guardado era negativo | Si límite inicial del mapa es negativo |

## Comportamiento Resultante

### Parámetros con mínimo < 0

Estos **siempre** muestran +/−:

| Parámetro | Límites en Mapa | Numpad Muestra +/− |
|-----------|-----------------|-------------------|
| **Presión Arterial** | (-300, 300) | ✅ **SÍ** |
| **Presión Venosa** | (-100, 500) | ✅ **SÍ** |
| **PTM (CALC_PTM)** | < 0 (si aplica) | ✅ **SÍ** |

Esto permite capturar valores negativos aunque se guarden en positivo después.

### Parámetros con mínimo ≥ 0

Estos **nunca** muestran +/−:

| Parámetro | Límites en Mapa | Numpad Muestra +/− |
|-----------|-----------------|-------------------|
| Temperatura | (35, 39.0) | ❌ **NO** |
| Conductividad | (12.5, 15.5) | ❌ **NO** |
| Flujo Dializado | (300, 800) | ❌ **NO** |

## Ejemplos de Uso

### Presión Arterial (permite negativo)
1. Usuario toca campo de límite
2. Numpad abre **con +/−** visible (porque mínimo inicial = -300)
3. Usuario puede escribir `-50` o `150`
4. Valor se guarda en JSON sin validación de rango

### Temperatura (no permite negativo)
1. Usuario toca campo de límite
2. Numpad abre **sin +/−** (porque mínimo inicial = 35)
3. Usuario solo puede escribir números positivos
4. Valor se guarda en JSON

## Lo que NO Cambia

✓ **Guardado**: Los valores se guardan igual en JSON  
✓ **Validación al guardar**: `min_v < max_v` sigue siendo el único requerimiento  
✓ **Escritura presiones**: Callback al dispositivo intacto  
✓ **Teclado**: NumpadDialog sin cambios  
✓ **Nombres**: Siguen mostrándose en mensajes  

## Archivos Relacionados

- `gui/configuration/alarm_screen_config.py` — `open_numpad()` (línea 220)
- `core/alarm_config_manager.py` — `get_default_limits_from_variables_map()` (método usado)
- `core/variables_map.py` — Define límites iniciales (sin cambios)

## Validación

✅ `alarm_screen_config.py`: Compilación OK  
✅ No afecta guardado ni validación  
✅ Mantiene compatibilidad con valores ya guardados  

---

## Estado

🚀 **LISTO PARA PRODUCCIÓN**
