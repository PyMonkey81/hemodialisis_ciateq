# Excepción: Límites de Alarma vs Setpoint de Temperatura

## Problema
Se necesita permitir límites de alarma más amplios que el rango del setpoint de temperatura.

## Solución
En `gui/configuration/alarm_screen_config.py` (línea ~281-282), se añade una excepción específica para `dialyTempControlSetPoint`:

```python
# Excepción: dialyTempControlSetPoint acepta alarmas 30-42°C (más amplios que setpoint 35-39°C)
if tag == "dialyTempControlSetPoint":
    default_min, default_max = 30.0, 42.0
```

## Diferencia de Rangos

| Aspecto | Rango | Ubicación |
|---------|-------|-----------|
| **Límites de ALARMA** | 30.0 - 42.0°C | `alarm_screen_config.py` (Validación) |
| **Rango del SETPOINT** | 35 - 39°C | `variables_map.py` (Pantalla de Terapia) |

## Comportamiento

### Pantalla de Configuración de Alarmas
- El usuario **puede** configurar límites de alarma desde 30.0°C hasta 42.0°C
- Rango amplio para detectar anomalías fuera de los límites operativos

### Pantalla de Terapia
- El usuario **solo puede** establecer setpoint entre 35-39°C
- Rango restrictivo para mantener seguridad clínica
- Este rango **NO se modifica** en `variables_map.py`

## Archivos Modificados

### `gui/configuration/alarm_screen_config.py` (línea ~281-282)
- Añadida excepción en `save_configuration()` después de obtener `default_min, default_max`
- Solo afecta validación de límites de alarma para este parámetro

### `core/variables_map.py`
- **SIN CAMBIOS** — `dialyTempControlSetPoint` sigue en (35, 39.0)

## Validación
✅ Límites de alarma aceptan 30-42°C
✅ Mensajes de error siguen mostrando el nombre del parámetro y rango permitido
✅ Pantalla de terapia no afectada (35-39°C intacto)
✅ Compilación Python: OK

## Ejemplo de Mensaje de Error
Si usuario intenta guardar límite inferior < 30°C:
```
"Temperatura (°C): límite inferior fuera de rango permitido (30.0 - 42.0)."
```
