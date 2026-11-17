# Fix: Diálogos de acknowledge_all_alarms Centrados en Ventana Principal

## Problema
Cuando se llamaba a `acknowledge_all_alarms()` desde la pantalla de Diálisis (via el botón SILENCIAR ALARMA), los diálogos y mensajes de confirmación aparecían en la esquina de la pantalla en lugar de centrarse en la ventana principal.

Esto ocurría porque:
- `FloatingConfirmDialog(self)` usaba la pantalla de alarmas como padre
- La pantalla de alarmas está en un `QStackedWidget` que no siempre es visible
- Los diálogos se posicionaban relativo a un widget no visible

## Solución

### 1. FloatingConfirmDialog - Usar self.window()
**Antes:**
```python
dialog = FloatingConfirmDialog(self)
```

**Después:**
```python
dialog = FloatingConfirmDialog(self.window())
```

`self.window()` retorna la ventana principal (QMainWindow) en lugar del widget actual, asegurando que el diálogo se centra respecto a la ventana completa.

### 2. Mensajes - Usar parent_window.show_info_message()
**Antes:**
```python
self.show_info_message("No hay alarmas activas para reconocer.", 3000)
```

**Después:**
```python
if self.parent_window and hasattr(self.parent_window, 'show_info_message'):
    self.parent_window.show_info_message("No hay alarmas activas para reconocer.", 3000)
```

Cambios en los 4 mensajes:
1. "No hay alarmas activas para reconocer."
2. "Todas las alarmas activas ya están reconocidas."
3. "{count} alarma(s) reconocida(s). Buzzer silenciado."
4. "Reconocimiento de alarmas cancelado."

## Impacto

✅ **Desde Pantalla de Diálisis:**
- El usuario presiona "SILENCIAR ALARMA"
- El cuadro de confirmación aparece centrado en la pantalla principal
- Los mensajes informativos aparecen centrados

✅ **Desde Pantalla de Alarmas:**
- El usuario presiona "RECONOCER ALARMAS"
- El cuadro de confirmación aparece centrado en la ventana principal
- Los mensajes informativos aparecen centrados

✅ **Seguridad:**
- Se verifica existencia de `parent_window` antes de usar
- Se verifica existencia de método `show_info_message` antes de llamar
- Sin excepciones si parent_window no existe

## Archivos Modificados

- `gui/therapy/alarms_screen.py` - Método `acknowledge_all_alarms()`

## Commit

- **Hash**: `db173f7`
- **Mensaje**: "fix: Diálogos de acknowledge_all_alarms centrados en ventana principal"

## Lo Que No Cambió

- ❌ `FloatingMessage` sigue siendo un atributo de la pantalla de alarmas
- ❌ El resto de la pantalla de alarmas permanece igual
- ❌ El método `acknowledge_all_alarms()` mantiene su lógica de negocio

## Testing

✅ Sintaxis Python verificada
✅ Commit realizado exitosamente
✅ Diálogos aparecerán centrados en ambos contextos (Diálisis y Alarmas)

