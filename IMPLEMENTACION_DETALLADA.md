# Implementación Detallada: Cuatro Correcciones

## Contenido
1. [Corrección 1: restore_all_defaults](#corrección-1-restore_all_defaults)
2. [Corrección 2: Validación con nombre de parámetro](#corrección-2-validación-con-nombre-de-parámetro)
3. [Corrección 3: Temperatura sin cambios](#corrección-3-temperatura-sin-cambios)
4. [Corrección 4: Logo CIATEQ interactivo](#corrección-4-logo-ciateq-interactivo)

---

## Corrección 1: restore_all_defaults

### Ubicación
**Archivo**: `gui/configuration/alarm_screen_config.py`  
**Método**: `restore_all_defaults()` (líneas 352-402)

### Cambio Implementado

#### Antes (INCORRECTO)
```python
def restore_all_defaults(self):
    # ... código de restauración ...
    self.config_manager.save_config()
    
    # ❌ LÍNEA PROBLEMÁTICA:
    self._write_pressure_limits_to_device()  # NO EXISTE
    
    self.show_info_message("...")
```

**Problema**: El método `_write_pressure_limits_to_device()` no existe en la clase, causando `AttributeError` y cierre de la aplicación.

#### Después (CORRECTO)
```python
def restore_all_defaults(self):
    # ... código de restauración ...
    self.config_manager.save_config()
    
    # ✓ NUEVO CÓDIGO:
    try:
        # Leer valores de arterial (siempre presente)
        art_min = float(self.inputs["bloodArteryPressureData"]['min'].text())
        art_max = float(self.inputs["bloodArteryPressureData"]['max'].text())
        
        # Leer valores de venosa (siempre presente)
        ven_min = float(self.inputs["bloodVenousPressureData"]['min'].text())
        ven_max = float(self.inputs["bloodVenousPressureData"]['max'].text())
        
        # Leer PTM solo si está en pantalla
        if "CALC_PTM" in self.inputs:
            ptm_min = float(self.inputs["CALC_PTM"]['min'].text())
            ptm_max = float(self.inputs["CALC_PTM"]['max'].text())
        else:
            ptm_min = None
            ptm_max = None
        
        # Usar el mismo callback que save_configuration()
        if self.write_setpoint_callback:
            self.write_setpoint_callback(art_min, art_max, ven_min, ven_max, ptm_min, ptm_max)
        
    except (ValueError, KeyError) as e:
        logger.warning(f"Error leyendo valores: {e}")
    
    self.show_info_message("Todos los límites y niveles han sido restaurados...")
```

### Detalles Técnicos

**Callback utilizado**: `self.write_setpoint_callback`
- Inicializado en `__init__` como parámetro
- Asignado a `self._emit_pressure_alarm_limits` en `appMainHemodialysis.py` línea ~3630

**Etiquetas escritas**:
| Tag | Descripción | Siempre presente |
|-----|-------------|-----------------|
| `artPresCircAlarmLoLimData` | Presión arterial baja | ✓ |
| `artPresCircAlarmHiLimData` | Presión arterial alta | ✓ |
| `venPresCircAlarmLoLimData` | Presión venosa baja | ✓ |
| `venPresCircAlarmHiLimData` | Presión venosa alta | ✓ |
| `membPressAlarmLoLimData` | PTM baja | Condicional |
| `membPressAlarmHiLimData` | PTM alta | Condicional |

**Manejo de None**:
- El callback ignora valores `None` (no escribe si la etiqueta no está en pantalla)
- Ver verificación en `_emit_pressure_alarm_limits()` línea ~3673:
  ```python
  if value is None:
      logger.info("OMITO alarma %s: valor None", tag)
      continue
  ```

---

## Corrección 2: Validación con nombre de parámetro

### Parte 2.1: Nuevo método get_parameter_name()

**Ubicación**: `core/alarm_config_manager.py` (línea ~87)

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

**Ejemplo de uso**:
```python
>>> manager.get_parameter_name("dialyTempControlSetPoint")
"Temperatura (°C)"

>>> manager.get_parameter_name("bloodVenousPressureData")
"Presión venosa del circuito de sangre (mmHg)"

>>> manager.get_parameter_name("CALC_PTM")
"Presión transmembrana (mmHg)"
```

### Parte 2.2: Mejora en save_configuration()

**Ubicación**: `gui/configuration/alarm_screen_config.py` (líneas 261-310)

#### Arquitectura de validación

```
┌─────────────────────────────────────────────┐
│ save_configuration()                        │
├─────────────────────────────────────────────┤
│                                             │
│ PASO 1: VALIDAR TODAS LAS FILAS             │
│ ├─ Si cualquier fila falla → RETURN         │
│ └─ Si todas pasan → continuar               │
│                                             │
│ PASO 2: GUARDAR EN QSETTINGS                │
│ ├─ Severidad de cada variable               │
│ └─ Límites de variables numéricas           │
│                                             │
│ PASO 3: GUARDAR JSON                        │
│ └─ config_manager.save_config()             │
│                                             │
│ PASO 4: ESCRIBIR AL DISPOSITIVO             │
│ └─ write_setpoint_callback()                │
│                                             │
└─────────────────────────────────────────────┘
```

#### Validaciones por paso

**PASO 1: Validar todas las filas sin guardar nada**

Para cada variable numérica (`type == "double"`):

1. **Extrae valores**
   ```python
   min_v = float(widgets['min'].text())
   max_v = float(widgets['max'].text())
   ```

2. **Valida relación min < max**
   ```python
   if min_v >= max_v:
       param_name = self.config_manager.get_parameter_name(tag)
       self.show_warning_message(
           f"{param_name}: límite inferior debe ser menor que el superior.",
           timeout_ms=2000
       )
       return  # ← DETIENE AQUÍ, no guarda nada
   ```

3. **Valida rangos permitidos**
   ```python
   default_min, default_max = self.config_manager.get_default_limits_from_variables_map(tag)
   
   if min_v < default_min or min_v > default_max:
       param_name = self.config_manager.get_parameter_name(tag)
       self.show_warning_message(
           f"{param_name}: límite inferior fuera de rango permitido ({default_min} - {default_max}).",
           timeout_ms=2000
       )
       return  # ← DETIENE AQUÍ
   
   if max_v < default_min or max_v > default_max:
       param_name = self.config_manager.get_parameter_name(tag)
       self.show_warning_message(
           f"{param_name}: límite superior fuera de rango permitido ({default_min} - {default_max}).",
           timeout_ms=2000
       )
       return  # ← DETIENE AQUÍ
   ```

**PASO 2-4**: Solo se ejecutan si PASO 1 pasó sin errores.

### Parte 2.3: Soporte para valores negativos

#### Flujo automático en NumpadDialog

**Ubicación**: `gui/components/numpad_modal.py`

El NumpadDialog ya detecta automáticamente si mostrar botones +/−:

```python
def open_numpad(self, line_edit, tag, param_name, field):
    # Obtener los límites de la variable
    min_val, max_val = self.config_manager.get_limits(tag)
    
    # Detectar si min < 0 → mostrar +/−
    allow_negative = min_val < 0
    
    dialog = NumpadDialog(self, 
                         initial_value="", 
                         title=f"Límite {field.upper()} \n {param_name}",
                         allow_negative=allow_negative)
```

#### Variables que permiten negativos

En `core/variables_map.py`:

```python
# Presión arterial: -300 a 300
0x06: {"limites": (-300, 300), "tag": "artPresCircAlarmHiLimData", ...}
0x07: {"limites": (-300, 300), "tag": "artPresCircAlarmLoLimData", ...}

# Presión venosa: -100 a 500
0x08: {"limites": (-100, 500), "tag": "venPresCircAlarmHiLimData", ...}
0x09: {"limites": (-100, 500), "tag": "venPresCircAlarmLoLimData", ...}

# PTM: -100 a 1000
0x0A: {"limites": (-100, 1000), "tag": "membPressAlarmHiLimData", ...}
0x0B: {"limites": (-100, 1000), "tag": "membPressAlarmLoLimData", ...}
```

**Resultado**: El NumpadDialog muestra botones +/− automáticamente para todas estas variables.

---

## Corrección 3: Temperatura sin cambios

### Verificación

**Archivo**: `core/variables_map.py` línea 200

```python
0x0C: {
    "name": "Temperatura",
    "label": "SP TEMP.",
    "type": "double",
    "rw": True,
    "unit": "°C",
    "limites": (35, 39.0),  # ← MANTIENE RANGO 35-39
    "tag": "dialyTempControlSetPoint",
    "nivel": "cian"
}
```

✓ **NO SE MODIFICÓ**: Rango se mantiene como (35, 39.0)

---

## Corrección 4: Logo CIATEQ interactivo

### Parte 4.1: Nueva clase LogoButton

**Ubicación**: `gui/appMainHemodialysis.py` (líneas 217-263)

```python
class LogoButton(QPushButton):
    """Botón plano para logo CIATEQ que maneja toque corto (salida) y largo (sin acción)."""
    
    def __init__(self, icon_path: str, close_callback=None, parent=None):
        super().__init__(parent)
        self.close_callback = close_callback
        self.press_time = None
        self.long_press_threshold = 800  # milisegundos
        
        # Timer para detectar toque largo
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._handle_long_press)
        
        # Configurar botón plano
        self.setFlat(True)                         # Sin fondo 3D
        self.setFocusPolicy(Qt.NoFocus)           # Sin foco visual
        self.setStyleSheet("border: none; padding: 0px;")
        
        # Cargar y escalar icono
        pixmap = QPixmap(icon_path).scaled(
            180, 120, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.setIcon(pixmap)
        self.setIconSize(pixmap.size())
        self.setFixedSize(180, 120)
```

#### Manejo de toques

```python
def mousePressEvent(self, event):
    """Registrar inicio del toque."""
    super().mousePressEvent(event)
    self.press_time = time.time()
    self.long_press_timer.start(self.long_press_threshold)

def mouseReleaseEvent(self, event):
    """Diferenciar entre toque corto y largo."""
    self.long_press_timer.stop()
    if self.press_time is not None:
        elapsed = (time.time() - self.press_time) * 1000  # convertir a ms
        if elapsed < self.long_press_threshold:
            # Toque corto: < 800ms
            self._handle_short_press()
    super().mouseReleaseEvent(event)

def _handle_short_press(self):
    """Toque corto: abrir diálogo de confirmación."""
    if self.close_callback:
        self.close_callback()

def _handle_long_press(self):
    """Toque largo: no hacer nada."""
    pass
```

#### Métodos QPushButton utilizados

✓ `setFlat(True)` — Botón sin borde 3D  
✓ `setFocusPolicy(Qt.NoFocus)` — Sin indicador de foco  
✓ `setStyleSheet()` — Sin borde, sin padding  
✓ `setIcon()` — Establecer icono  
✓ `setIconSize()` — Tamaño del icono  
✓ `setFixedSize()` — Tamaño fijo del botón  
✓ `mousePressEvent()` — Evento de inicio de toque  
✓ `mouseReleaseEvent()` — Evento de fin de toque  

**No utiliza**:
✗ `setTextInteractionFlags()` — QPushButton no tiene este método

#### Diagrama temporal

```
TOQUE CORTO:
├─ t=0ms:    mousePressEvent()
│            ├─ press_time = now()
│            └─ long_press_timer.start(800ms)
├─ t=500ms:  mouseReleaseEvent() [usuario suelta]
│            ├─ long_press_timer.stop()
│            ├─ elapsed = 500ms < 800ms ✓
│            └─ _handle_short_press() → callback
└─ Resultado: Se abre diálogo de salida

TOQUE LARGO:
├─ t=0ms:    mousePressEvent()
│            ├─ press_time = now()
│            └─ long_press_timer.start(800ms)
├─ t=800ms:  long_press_timer timeout
│            └─ _handle_long_press() [vacío]
├─ t=1000ms: mouseReleaseEvent() [usuario suelta]
│            ├─ long_press_timer.stop() [ya terminó]
│            ├─ elapsed = 1000ms >= 800ms
│            └─ NO se llama a _handle_short_press()
└─ Resultado: Sin acción, sin recuadro, sin selección
```

### Parte 4.2: Integración en HemodialysisHMI

**Ubicación**: `gui/appMainHemodialysis.py` (línea ~1054)

```python
header_layout = QHBoxLayout(header_container)
header_layout.setContentsMargins(2, 2, 2, 2)
header_layout.setSpacing(1)

# Logo CIATEQ: botón plano con toque corto para salir
logo1 = LogoButton(
    icon_path=resource_path("resources/images/logo_ciateq__.png"),
    close_callback=self._show_exit_confirmation,
    parent=self
)
header_layout.addWidget(logo1)

# Resto de elementos del header...
self.status_label = QLabel("RECONECTANDO")
header_layout.addWidget(self.status_label)
# ...
```

### Parte 4.3: Método _show_exit_confirmation

**Ubicación**: `gui/appMainHemodialysis.py` (línea 4217)

```python
def _show_exit_confirmation(self):
    """Muestra diálogo de confirmación para salir de la aplicación."""
    dialog = FloatingConfirmDialog(self)
    mensaje = "¿Desea salir de la aplicación?"
    reply = dialog.show_confirm(mensaje, accept_text="Sí", cancel_text="No")
    if reply:
        self.closeEvent(None)
```

**Flujo**:
1. Usuario toca logo con toque corto
2. `_handle_short_press()` → `_show_exit_confirmation()`
3. Diálogo flotante aparece
4. **Si "Sí"**: `closeEvent(None)` → cierra la app
5. **Si "No"**: Diálogo desaparece, app continúa

### Parte 4.4: Protección de closeEvent

**Ubicación**: `gui/appMainHemodialysis.py` (línea ~4242)

```python
def closeEvent(self, event):
    self.end_dialysis_session()
    logger.error("[INFO] closeEvent → performing shutdown...")
    self.shutdown()
    
    try:
        clean_close_path = get_runtime_data_path("var", "log", "cierre_limpio")
        with open(clean_close_path, "w") as f:
            f.write("")
        logger.info(f"Cierre limpio marcado en {clean_close_path}")
    except Exception as e:
        logger.error(f"No se pudo marcar cierre limpio: {e}")
    
    # ✓ Protección para event=None (cuando se llama desde el botón)
    if event:
        event.accept()
    QApplication.quit()
```

**Protección**:
- Cuando el usuario cierra normalmente (X de ventana): `event` es un QCloseEvent válido
- Cuando se llama desde el botón logo: `event=None`
- La protección `if event:` permite ambos casos

---

## Resumen de cambios

| Archivo | Líneas | Cambios |
|---------|--------|---------|
| `gui/configuration/alarm_screen_config.py` | 352-402 | Reemplazar método no existente con callback |
| `gui/configuration/alarm_screen_config.py` | 261-310 | Agregar nombre del parámetro a mensajes |
| `core/alarm_config_manager.py` | 87-93 | Nuevo método `get_parameter_name()` |
| `gui/appMainHemodialysis.py` | 217-263 | Nueva clase `LogoButton` (sin setTextInteractionFlags) |
| `gui/appMainHemodialysis.py` | 1054 | Reemplazar QLabel con LogoButton |
| `gui/appMainHemodialysis.py` | 4217-4222 | Nuevo método `_show_exit_confirmation()` |
| `gui/appMainHemodialysis.py` | 4242 | Proteger `closeEvent()` para event=None |

---

## Testing

### Validaciones implementadas
✓ Sintaxis Python compilada sin errores  
✓ Imports verificados  
✓ Variables_map: Temperatura (35, 39.0) sin cambios  
✓ Presión venosa: Soporta negativos (-100 a 500)  
✓ closeEvent: Protegido para event=None

### Pruebas recomendadas
1. Restaurar defaults sin error de cierre
2. Ingresar límite inválido → ver nombre del parámetro en mensaje
3. Ingresar presión venosa negativa (-50) → debe aceptar
4. Toque corto en logo (< 800ms) → abre diálogo
5. Toque largo en logo (> 800ms) → sin acción
6. Diálogo de salida: Sí → cierra app, No → continúa

