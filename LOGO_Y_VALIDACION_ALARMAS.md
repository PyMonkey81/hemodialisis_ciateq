# Cambios: Logo y Validación de Alarmas

Fecha: 10 de noviembre de 2026
Cambios finales solicitados.

## 1️⃣ Logo CIATEQ: Toque solo en Pantalla de Inicio

### Descripción
El toque corto del logo CIATEQ solo abre el diálogo de salida cuando la aplicación está en la **pantalla de inicio** (`INDEX_HOME`, índice 0). En cualquier otra pantalla, el toque no hace nada.

### Archivos Modificados

#### `gui/appMainHemodialysis.py`

**Línea 221** — LogoButton acepta `screen_stack`:
```python
def __init__(self, icon_path: str, close_callback=None, screen_stack=None, parent=None):
    super().__init__(parent)
    self.close_callback = close_callback
    self.screen_stack = screen_stack  # Referencia a screen_stack
```

**Línea 257** — _handle_short_press verifica el índice actual:
```python
def _handle_short_press(self):
    """Toque corto: abrir diálogo de confirmación para salir si está en INDEX_HOME."""
    # Solo actuar si estamos en la pantalla de inicio (INDEX_HOME = 0)
    if self.screen_stack and self.screen_stack.currentIndex() == 0:
        if self.close_callback:
            self.close_callback()
```

**Línea 1055** — Instanciación pasa `screen_stack`:
```python
logo1 = LogoButton(
    icon_path=resource_path("resources/images/logo_ciateq__.png"),
    close_callback=self._show_exit_confirmation,
    screen_stack=self.screen_stack,  # Pasamos el screen_stack
    parent=self
)
```

### Comportamiento

| Escenario | Resultado |
|-----------|-----------|
| Toque corto en INDEX_HOME (pantalla inicio) | Abre "¿Desea salir de la aplicación?" |
| Toque corto en otra pantalla | Sin acción |
| Toque largo (cualquier pantalla) | Sin acción |
| Acepta "Sí" en diálogo | Llama `closeEvent()` que ya existe |

---

## 2️⃣ Validación de Alarmas: Solo Comprueba min < max

### Descripción
Se eliminó la validación contra `get_default_limits_from_variables_map`. Ahora solo se valida que:
- El límite inferior sea menor que el superior
- Los valores sean números válidos

Los límites de `variables_map` se usan solo como valores iniciales y para "Restaurar Todo".

### Archivo Modificado

#### `gui/configuration/alarm_screen_config.py`

**Línea 263-283** — save_configuration() simplificada:
```python
def save_configuration(self):
    """Guarda la configuración de alarmas: primero valida todas las filas,
    luego guarda en JSON, finalmente escribe los límites de presión al dispositivo."""
    
    # PASO 1: Validar todas las filas sin guardar nada
    for tag, widgets in self.inputs.items():
        try:
            # Solo validar límites si es variable numérica
            if widgets.get('type') == "double":
                min_v = float(widgets['min'].text())
                max_v = float(widgets['max'].text())

                # Validar relación entre min y max
                if min_v >= max_v:
                    param_name = self.config_manager.get_parameter_name(tag)
                    self.show_warning_message(
                        f"{param_name}: límite inferior debe ser menor que el superior.",
                        timeout_ms=2000
                    )
                    return

        except ValueError:
            param_name = self.config_manager.get_parameter_name(tag)
            self.show_error_message(f"{param_name}: valor inválido.", timeout_ms=3000)
            return
    
    # PASO 2: Si toda validación pasó, guardar severidad y límites
    # (resto del método sin cambios)
```

### Validación Actual

| Condición | Acción |
|-----------|--------|
| `min_v >= max_v` | Rechaza con mensaje |
| Número inválido | Error |
| `min_v < max_v` y válido | **Acepta y guarda en JSON** |

### Ejemplos

- **Temperatura**: Acepta 30-42°C (antes rechazaba fuera de 35-39°C)
- **Presión arterial**: Acepta 2-5 bar (antes rechazaba fuera de limites_map)
- **Presión venosa**: Acepta cualquier rango válido

### Cambios Preservados

✓ Valores iniciales: Siguen usando `variables_map` (35-39°C para temperatura)
✓ Restaurar Todo: Restaura desde `variables_map` (sin cambios)
✓ Nombres de parámetros: Siguen mostrándose en mensajes
✓ Escritura de presiones: Conservada (callback al dispositivo)

---

## Validación Final

✅ `gui/appMainHemodialysis.py`: Compilación OK
✅ `gui/configuration/alarm_screen_config.py`: Compilación OK
✅ Áreas protegidas: Intactas (Kt/V, Heparina, NIBP, variables_map)
✅ closeEvent(): Sin cambios, funciona con `event=None` desde logo

---

## Estado

🚀 **LISTO PARA PRODUCCIÓN**
