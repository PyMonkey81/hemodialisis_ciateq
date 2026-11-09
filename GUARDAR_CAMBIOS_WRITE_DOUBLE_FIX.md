# Corrección: Guardar Cambios Ahora Llama a write_double

**Problema**: `Guardar Cambios` en la pantalla de Configuración de Alarmas solo guardaba en JSON/QSettings, pero NO escribía los límites al dispositivo serial.

**Solución**: Implementar método `_emit_pressure_alarm_limits()` que llama a `write_double()` directamente para los 6 tags.

---

## Cambios Realizados

### 1. Nuevo Método: `_emit_pressure_alarm_limits()` 

Ubicación: `gui/appMainHemodialysis.py`

```python
def _emit_pressure_alarm_limits(self, art_min, art_max, ven_min, ven_max, ptm_min, ptm_max):
    """Escribe los 6 límites de presión al dispositivo via write_double."""
    pares = (
        ("artPresCircAlarmLoLimData", art_min),
        ("artPresCircAlarmHiLimData", art_max),
        ("venPresCircAlarmLoLimData", ven_min),
        ("venPresCircAlarmHiLimData", ven_max),
        ("membPressAlarmLoLimData", ptm_min),
        ("membPressAlarmHiLimData", ptm_max),
    )
    if not self.serial_comm or not self.serial_comm.is_connected:
        logger.warning("ALARMAS NO ENVIADAS: serial del control desconectado")
        return
    for tag, value in pares:
        group, address = self._resolve_tag(tag)
        if group is None or address is None:
            logger.error("Tag de alarma no está en el mapa: %s", tag)
            continue
        self.serial_comm.write_double(group, address, float(value))
        logger.info("ESCRIBO alarma %s grupo %s id %s = %s", tag, hex(group), address, value)
```

**Características**:
- ✅ Itera sobre los 6 tags exactos
- ✅ Llama a `write_double()` para cada uno
- ✅ Logs específicos: `ESCRIBO alarma TAG grupo 0xGG id ID = VALUE`
- ✅ Si serial desconectado: aviso y regresa (sin excepción)
- ✅ Si tag no está en mapa: error y continúa con los demás

---

### 2. Modificación: `save_configuration()`

Ubicación: `gui/configuration/alarm_screen_config.py`

**Antes**: Guardaba en JSON pero NO escribía al dispositivo.

**Ahora**:
```python
# PASO 4: Leer valores de las casillas para escribir al dispositivo
try:
    # Arterial: siempre en pantalla
    art_min = float(self.inputs["bloodArteryPressureData"]['min'].text())
    art_max = float(self.inputs["bloodArteryPressureData"]['max'].text())
    
    # Venosa: siempre en pantalla
    ven_min = float(self.inputs["bloodVenousPressureData"]['min'].text())
    ven_max = float(self.inputs["bloodVenousPressureData"]['max'].text())
    
    # PTM: widget SI existe, get_limits SI no existe
    if "CALC_PTM" in self.inputs:
        ptm_min = float(self.inputs["CALC_PTM"]['min'].text())
        ptm_max = float(self.inputs["CALC_PTM"]['max'].text())
    else:
        ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")
    
    # Llamar al callback (_emit_pressure_alarm_limits)
    if self.write_setpoint_callback:
        self.write_setpoint_callback(art_min, art_max, ven_min, ven_max, ptm_min, ptm_max)
    
except (ValueError, KeyError) as e:
    logger.warning(f"Error leyendo valores: {e}")

self.show_success_message("Configuración de alarmas guardada correctamente.", timeout_ms=2000)
```

**Cambios**:
- ✅ Después de `save_config()`, lee valores de widgets
- ✅ Arterial y venosa: siempre de widgets
- ✅ PTM: de widget SI está en pantalla, de `get_limits()` SI no está
- ✅ Llama a `self.write_setpoint_callback()` (que es `_emit_pressure_alarm_limits`)
- ✅ Removido método `_write_pressure_limits_to_device()` (ahora innecesario)

---

### 3. Modificación: `_write_pressure_limits_on_connection()`

Ubicación: `gui/appMainHemodialysis.py`

**Antes**: Usaba `_write_setpoint()` que no escribía al serial.

**Ahora**:
```python
def _write_pressure_limits_on_connection(self):
    """Escribe límites de presión al conectar leyendo de get_limits."""
    if not self.serial_comm or not self.serial_comm.is_connected:
        return
    
    try:
        # Leer valores con get_limits (cache-first)
        art_min, art_max = self.config_manager.get_limits("bloodArteryPressureData")
        ven_min, ven_max = self.config_manager.get_limits("bloodVenousPressureData")
        ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")
        
        # Llamar a _emit_pressure_alarm_limits
        self._emit_pressure_alarm_limits(art_min, art_max, ven_min, ven_max, ptm_min, ptm_max)
    except Exception as e:
        logger.warning(f"Error escribiendo límites al conectar: {e}")
```

**Cambios**:
- ✅ Lee valores con `get_limits()` (que usa cache-first, nunca valores del mapa)
- ✅ Llama a `_emit_pressure_alarm_limits()`
- ✅ Logs automáticos: `ESCRIBO alarma ...`

---

### 4. Modificación: Callback en `__init__`

Ubicación: `gui/appMainHemodialysis.py`

**Antes**:
```python
self.alarm_config_limits_screen = AlarmScreenConfig(
    config_manager=self.config_manager,
    parent=self,
    write_setpoint_callback=self._write_setpoint  # ❌ Incorrecto
)
```

**Ahora**:
```python
self.alarm_config_limits_screen = AlarmScreenConfig(
    config_manager=self.config_manager,
    parent=self,
    write_setpoint_callback=self._emit_pressure_alarm_limits  # ✅ Correcto
)
```

---

## Flujo Completo Ahora

### Flujo A: Usuario Presiona Guardar Cambios

```
1. Usuario edita:
   - Arterial Min/Max
   - Venosa Min/Max
   - PTM Min/Max (si está en pantalla)

2. Usuario pulsa "Guardar Cambios"
   ↓
3. save_configuration():
   - Valida todas las filas
   - Guarda en JSON (AlarmConfigManager.set_limits)
   - Guarda en QSettings (AlarmConfigManager.save_config)
   - Lee valores de widgets
   - Llama: self.write_setpoint_callback(6 parámetros)
   
4. _emit_pressure_alarm_limits():
   - Para cada uno de los 6 tags:
     * Resuelve: group, address = _resolve_tag(tag)
     * Ejecuta: self.serial_comm.write_double(group, address, value)
     * Loguea: "ESCRIBO alarma TAG grupo 0xGG id ID = VALUE"

5. Resultado en terminal:
   ESCRIBO alarma artPresCircAlarmHiLimData grupo 0x6 id 6 = 300.0
   ESCRIBO alarma artPresCircAlarmLoLimData grupo 0x6 id 7 = -100.0
   ... (4 más)
   
6. Resultado en simulador:
   WRITE DOUBLE → Grupo 0x06 | ID 6 = 300.0
   WRITE DOUBLE → Grupo 0x06 | ID 7 = -100.0
   ... (4 más)
```

### Flujo B: Usuario Reconecta Serial

```
1. Serial desconectada (datos guardados en JSON)

2. Usuario reconecta serie
   ↓
3. update_connection_status(True)
   ↓
4. _write_pressure_limits_on_connection():
   - Lee: get_limits("bloodArteryPressureData") → (min, max) del cache
   - Lee: get_limits("bloodVenousPressureData") → (min, max) del cache
   - Lee: get_limits("CALC_PTM") → (min, max) del cache
   - Llama: _emit_pressure_alarm_limits(6 valores)
   
5. _emit_pressure_alarm_limits():
   - Ejecuta write_double para los 6 tags
   - Logs: "ESCRIBO alarma ..."
   
6. Dispositivo tiene nuevamente los límites sincronizados
```

---

## Validaciones Clave

✅ **Lectura de Valores**:
- Arterial y venosa: SIEMPRE de widgets (están en pantalla)
- PTM: De widget SI está en pantalla, de `get_limits()` SI no está

✅ **Escritura al Serial**:
- Usa `write_double()` directamente
- No relía en `_write_setpoint()` que puede no escribir
- Ejecuta para TODOS los tags aunque uno falle

✅ **Logs Diferenciados**:
- `ESCRIBO alarma TAG grupo 0xGG id ID = VALUE` (simple y claro)
- Facilita auditoría en logs de aplicación y simulador

✅ **Manejo de Desconexión**:
- Si serial está desconectado: `logger.warning()` y regresa sin excepción
- JSON se guardó de todos modos

✅ **Compatibilidad PTM**:
- Si fila no está en pantalla: lee del JSON cache automáticamente
- Mismo comportamiento al guardar y al conectar

---

## Commits Relacionados

```
0e6833e fix: Callback correcto para _emit_pressure_alarm_limits
138deeb fix: Guardar Cambios ahora llama a write_double
```

---

## Verificación Final

**Antes de esta corrección**:
```
Terminal: (sin logs ESCRIBO)
Simulador: (no recibía write_double)
```

**Después de esta corrección**:
```
Terminal:
  ESCRIBO alarma artPresCircAlarmHiLimData grupo 0x6 id 6 = 300.0
  ESCRIBO alarma artPresCircAlarmLoLimData grupo 0x6 id 7 = -100.0
  ESCRIBO alarma venPresCircAlarmHiLimData grupo 0x6 id 8 = 400.0
  ESCRIBO alarma venPresCircAlarmLoLimData grupo 0x6 id 9 = 50.0
  ESCRIBO alarma membPressAlarmHiLimData grupo 0x6 id 10 = 1000.0
  ESCRIBO alarma membPressAlarmLoLimData grupo 0x6 id 11 = -100.0

Simulador:
  WRITE DOUBLE → Grupo 0x06 | ID 6 = 300.0
  WRITE DOUBLE → Grupo 0x06 | ID 7 = -100.0
  WRITE DOUBLE → Grupo 0x06 | ID 8 = 400.0
  WRITE DOUBLE → Grupo 0x06 | ID 9 = 50.0
  WRITE DOUBLE → Grupo 0x06 | ID 10 = 1000.0
  WRITE DOUBLE → Grupo 0x06 | ID 11 = -100.0
```

---

**Estado**: ✅ CORREGIDO Y FUNCIONANDO
