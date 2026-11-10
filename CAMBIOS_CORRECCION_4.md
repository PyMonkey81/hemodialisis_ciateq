# Cuatro Correcciones en hemodialisis_ciateq

## Resumen
Se implementaron 4 correcciones específicas en la aplicación de hemodiálisis, enfocadas en: manejo correcto de alarmas de presión, validación mejorada de límites con nombres de parámetros, funcionamiento correcto del botón logo CIATEQ.

---

## 1. Corrección: `restore_all_defaults` en alarm_screen_config.py

### Problema
El método `restore_all_defaults()` llamaba a `self._write_pressure_limits_to_device()`, que no existe y causaba cierre de la aplicación.

### Solución
Se reemplazó la llamada al método no existente con el código que usa el mismo callback `write_setpoint_callback` que ya usa `save_configuration()`:

**Ubicación**: [gui/configuration/alarm_screen_config.py](gui/configuration/alarm_screen_config.py)

**Cambio**:
- Eliminada: `self._write_pressure_limits_to_device()`
- Agregado: Bloque try/except que lee arterial, venosa y PTM de los widgets y llama a `self.write_setpoint_callback()` con los mismos parámetros que `save_configuration()`
- Los límites de presión (arterial, venosa, PTM) se escriben al dispositivo con el callback existente, sin crear métodos nuevos

**Comportamiento**:
- Al restaurar defaults, los valores se guardan en JSON
- Automáticamente se escriben arterial y venosa al dispositivo (siempre presentes)
- PTM se escribe solo si está en pantalla (parámetro None si no existe)

---

## 2. Corrección: Validación de límites con nombre de parámetro

### Problema
Los mensajes de error/advertencia al rechazar un límite no mostraban el nombre del parámetro, dificultando identificar cuál variable tenía el problema. Además, si una fila fallaba la validación, no se garantizaba que nada se guardara.

### Solución

#### 2.1 Nuevo método en AlarmConfigManager
Se agregó `get_parameter_name(tag: str)` en [core/alarm_config_manager.py](core/alarm_config_manager.py):
```python
def get_parameter_name(self, tag: str) -> str:
    """Devuelve el nombre legible del parámetro para mostrar en mensajes."""
    info = self._get_default_info_from_variables_map(tag)
    name = info.get("name", info.get("label", tag))
    unit = info.get("unit", "")
    if unit:
        return f"{name} ({unit})"
    return name
```

#### 2.2 Mejora en save_configuration
En [gui/configuration/alarm_screen_config.py](gui/configuration/alarm_screen_config.py), `save_configuration()`:
- **PASO 1**: Valida TODAS las filas antes de guardar nada
- Si cualquier fila falla: muestra mensaje con nombre del parámetro y no guarda
- Si todas pasan: continúa a PASO 2

**Mensajes ahora incluyen nombre del parámetro**:
- "Temperatura (°C): límite inferior fuera de rango permitido (35.0 - 39.0)."
- "Presión venosa del circuito de sangre (mmHg): límite inferior debe ser menor que el superior."

#### 2.3 Soporte para valores negativos
El numpad ya detecta automáticamente si `min_val < 0` en `variables_map`:
- **Presión venosa**: limites (-100, 500) → muestra botones +/−
- **Presión arterial**: limites (-300, 300) → muestra botones +/−
- El valor guardado es positivo si el usuario lo ingresa sin signo, negativo si usa el botón −

**Flujo de captura**:
1. Usuario toca campo de límite
2. NumpadDialog recibe `allow_negative=True` si min < 0
3. Botones +/− se muestran solo cuando es necesario
4. Usuario puede ingresa -50 para presión venosa (dentro de rango -100 a 500)

---

## 3. Temperatura dialística: Rango sin cambios

**Verificado**: `dialyTempControlSetPoint` mantiene rango (35, 39.0)

```python
0x0C: {"name": "Temperatura", "label": "SP TEMP.", "type": "double", 
       "rw": True, "unit": "°C", "limites": (35, 39.0), 
       "tag": "dialyTempControlSetPoint", "nivel": "cian"}
```

✓ No se modificó

---

## 4. Logo CIATEQ: Botón plano con toque corto y largo

### Problema
El logo CIATEQ era un `QLabel` simple sin interacción.

### Solución

#### 4.1 Nueva clase LogoButton
En [gui/appMainHemodialysis.py](gui/appMainHemodialysis.py), se agregó clase `LogoButton`:

**Características**:
- Extiende `QPushButton` con estilo plano (`setFlat(True)`)
- Sin foco (`setFocusPolicy(Qt.NoFocus)`)
- Icono escalado 180×120px

**Manejo de toques**:
- **Toque corto** (<800ms): Abre diálogo "¿Desea salir de la aplicación?"
  - Si acepta: ejecuta `closeEvent(None)` 
  - Si cancela: no hace nada
- **Toque largo** (≥800ms): No hace nada (sin dibujar recuadro ni seleccionar)

**Lógica**:
1. `mousePressEvent()`: registra tiempo de inicio, inicia timer de 800ms
2. `mouseReleaseEvent()`: cancela timer, calcula tiempo transcurrido
3. Si < 800ms: ejecuta `_handle_short_press()` → callback
4. Si ≥ 800ms: timer llama `_handle_long_press()` (vacío)

#### 4.2 Integración en HemodialysisHMI
En [gui/appMainHemodialysis.py](gui/appMainHemodialysis.py) línea ~1054:

```python
logo1 = LogoButton(
    icon_path=resource_path("resources/images/logo_ciateq__.png"),
    close_callback=self._show_exit_confirmation,
    parent=self
)
header_layout.addWidget(logo1)
```

#### 4.3 Nuevo método _show_exit_confirmation
En [gui/appMainHemodialysis.py](gui/appMainHemodialysis.py) línea ~4217:

```python
def _show_exit_confirmation(self):
    """Muestra diálogo de confirmación para salir de la aplicación."""
    dialog = FloatingConfirmDialog(self)
    mensaje = "¿Desea salir de la aplicación?"
    reply = dialog.show_confirm(mensaje, accept_text="Sí", cancel_text="No")
    if reply:
        self.closeEvent(None)
```

#### 4.4 Protección de closeEvent
En [gui/appMainHemodialysis.py](gui/appMainHemodialysis.py) línea ~4242:

```python
if event:
    event.accept()
QApplication.quit()
```

Permite que `closeEvent(None)` se ejecute sin error.

---

## Archivos Modificados

1. **[gui/configuration/alarm_screen_config.py](gui/configuration/alarm_screen_config.py)**
   - `save_configuration()`: Mensajes con nombre de parámetro
   - `restore_all_defaults()`: Usa callback en lugar de método no existente

2. **[core/alarm_config_manager.py](core/alarm_config_manager.py)**
   - Nuevo método: `get_parameter_name(tag: str) → str`

3. **[gui/appMainHemodialysis.py](gui/appMainHemodialysis.py)**
   - Nueva clase: `LogoButton(QPushButton)` con manejo de toque corto/largo
   - Nuevo método: `_show_exit_confirmation()`
   - Protección en `closeEvent()` para event=None
   - Reemplazo de logo1 QLabel con LogoButton

---

## Validación

✓ Todos los archivos compilaron sin errores de sintaxis
✓ Variables_map no fue modificada (rango temperatura mantiene 35-39)
✓ Presión venosa soporta valores negativos (-100 a 500)
✓ Presión arterial soporta valores negativos (-300 a 300)
✓ Numpad detecta automáticamente si mostrar botones +/−
✓ Salida de aplicación protegida sin errores
✓ LogoButton: sin setTextInteractionFlags (QPushButton no tiene ese método)

---

## Notas

- No se tocaron Kt/V, heparina ni NIBP (como se solicitó)
- El callback `write_setpoint_callback` ya estaba disponible en AlarmScreenConfig
- FloatingConfirmDialog ya estaba importado en appMainHemodialysis.py
- QTimer ya estaba importado en los módulos necesarios
- LogoButton usa solo métodos válidos de QPushButton: setFlat(), setFocusPolicy(), setStyleSheet(), setIcon(), setIconSize(), setFixedSize()
