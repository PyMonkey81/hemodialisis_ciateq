# Botón SILENCIAR ALARMA en Botonera

## Descripción
Se ha agregado un nuevo botón "SILENCIAR\nALARMA" a la botonera de la pantalla de diálisis (`dialysis_screenV2.py`).

## Especificaciones del Botón

| Propiedad | Valor |
|-----------|-------|
| **Texto** | "SILENCIAR\nALARMA" (con salto de línea) |
| **Color de Fondo** | #D9534F (rojo claro) |
| **Altura** | 80px (igual a los demás botones) |
| **Posición** | Después de "Kt/V", en la fila 2, columna 2 |
| **Estado** | Siempre habilitado (en cualquier fase de tratamiento) |
| **Acción al Presionar** | Llama a `alarms_screen.acknowledge_all_alarms()` |

## Distribución de Botones en Grid

```
Fila 0: [INICIAR] [PAUSAR] [DETENER] [APLICAR BOLO]
Fila 1: [MENÚ TERAPIA] [MENÚ PACIENTE] [INICIAR CEBADO] [DETENER CEBADO]
Fila 2: [HEPARINA] [Kt/V] [SILENCIAR ALARMA] [VACÍO]
```

- Grid: 4 columnas
- Total de botones: 11
- Botón "SILENCIAR ALARMA" es el botón 10 (índice 10)

## Implementación

### Cambio en `button_config` (línea ~703):
```python
button_config = [
    # ... botones anteriores ...
    ("Kt/V", "#06298a", self.parent_window.show_ktv_screen),
    ("SILENCIAR\nALARMA", "#D9534F", self.silence_alarms),  # NUEVO
]
```

### Método `silence_alarms()` (nuevo):
```python
def silence_alarms(self):
    """Llama a acknowledge_all_alarms() de la pantalla de alarmas."""
    if self.parent_window and hasattr(self.parent_window, 'alarms_screen'):
        alarms_screen = self.parent_window.alarms_screen
        if hasattr(alarms_screen, 'acknowledge_all_alarms'):
            alarms_screen.acknowledge_all_alarms()
```

## Lógica de Seguridad

1. **Verificación de parent_window**: Se valida que exista la referencia al main window
2. **Verificación de alarms_screen**: Se comprueba que el atributo exista en parent_window
3. **Verificación de método**: Se verifica que `acknowledge_all_alarms()` esté disponible
4. **Sin excepciones**: Si no existe la pantalla de alarmas, el botón simplemente no hace nada

## Comportamiento del Botón

- **No está en `set_start_stop_buttons_state()`**: No se deshabilita al pausar/detener tratamiento
- **No está en `set_priming_buttons_state()`**: No se deshabilita durante cebado
- **Siempre disponible**: El operador puede silenciar alarmas en cualquier fase

## Acción del Botón

Cuando se presiona, llama al método `acknowledge_all_alarms()` de la pantalla de alarmas, que:
- Realiza una confirmación (pregunta al usuario)
- Marca todas las alarmas como reconocidas
- Escribe el historial de alarmas
- Establece `buzzer_silenced_by_user = True`

## Archivos Modificados

- `gui/therapy/dialysis_screenV2.py`

## Commit

- **Hash**: `577129b`
- **Mensaje**: "feat: Agregar botón SILENCIAR ALARMA en la botonera de dialysis_screenV2"

## Testing

✅ Sintaxis Python verificada  
✅ Método `silence_alarms()` implementado correctamente  
✅ Verificación de seguridad ante pantalla de alarmas inexistente  
✅ Grid de 4 columnas mantiene distribución correcta  

