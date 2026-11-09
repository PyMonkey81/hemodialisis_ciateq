# Arquitectura del Sistema de Sincronización de Límites de Presión

## Visión General

El sistema implementa una **sincronización bidireccional automática** de límites de presión (arterial, venosa y transmembrana) entre la interfaz de usuario y el dispositivo de hemodiálisis. Los límites se persisten como JSON en QSettings y se recalcula la PTM automáticamente en tiempo real.

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO (GUI)                            │
├─────────────────────────────────────────────────────────────┤
│  Pantalla de Configuración de Alarmas                      │
│  - Arterial (Min/Max)                                      │
│  - Venosa (Min/Max)                                        │
│  - PTM Calculada (Min/Max) [si está visible]              │
│  - Temperatura [no se escribe al serial]                   │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
             ┌────────────────────────────┐
             │  AlarmConfigManager        │
             │  ────────────────────────  │
             │  _limits_cache: dict       │  ← JSON en memoria
             │  set_limits()              │
             │  get_limits()              │
             │  _load_limits_from_settings│
             └────────────────────────────┘
                          ↓ ↑
             ┌────────────────────────────┐
             │  QSettings (persistence)   │
             │  ────────────────────────  │
             │  alarms/limits: JSON       │ ← Guardado en Windows registry
             └────────────────────────────┘
                          ↓
             ┌────────────────────────────┐
             │  appMainHemodialysis       │
             │  ────────────────────────  │
             │  _write_setpoint()         │ → Serial (6 tags)
             │  _write_pressure_limits    │
             │  _on_connection()          │
             └────────────────────────────┘
                          ↓
             ┌────────────────────────────┐
             │  SerialCommunication       │
             │  ────────────────────────  │
             │  write_double(group,addr,v)│
             └────────────────────────────┘
                          ↓
             ┌────────────────────────────┐
             │  DISPOSITIVO DE HEMODIÁLISIS│
             │  ────────────────────────  │
             │  0x06: artPresCircAlarmHi  │
             │  0x07: artPresCircAlarmLo  │
             │  0x08: venPresCircAlarmHi  │
             │  0x09: venPresCircAlarmLo  │
             │  0x0A: membPressAlarmHi    │
             │  0x0B: membPressAlarmLo    │
             └────────────────────────────┘
```

## Componentes Clave

### 1. AlarmConfigManager (core/alarm_config_manager.py)

**Responsabilidad**: Persistencia y caché de límites en memoria

```python
class AlarmConfigManager:
    def __init__(self):
        self.KEY_LIMITS = "alarms/limits"  # JSON string
        self._limits_cache = {}             # Dict en memoria
        self._load_limits_from_settings()   # Carga viejo dict O nuevo JSON
    
    def _load_limits_from_settings(self):
        """Carga JSON o dict viejo (migración automática)"""
        raw = self.settings.value(self.KEY_LIMITS, "")
        if isinstance(raw, dict):
            self._limits_cache = dict(raw)  # Formato viejo
        elif isinstance(raw, str) and raw.strip():
            self._limits_cache = dict(json.loads(raw))  # JSON nuevo
        else:
            self._limits_cache = {}  # Vacío (SIN rellenar con mapa)
    
    def set_limits(self, tag: str, min_val: float, max_val: float):
        """Actualiza cache en memoria, luego guarda JSON en QSettings"""
        self._limits_cache[tag] = (min_val, max_val)
        json_str = json.dumps(self._limits_cache)
        self.settings.setValue(self.KEY_LIMITS, json_str)
    
    def get_limits(self, tag: str) -> tuple:
        """Lee cache primero, mapa solo si no existe en cache"""
        if tag in self._limits_cache:
            return self._limits_cache[tag]  # ← Cache-first
        # Solo si no existe en cache:
        default_min, default_max = self.get_default_limits_from_variables_map(tag)
        return (default_min, default_max)
```

**Ventajas del caché en memoria**:
- ✅ Evita que QSettings en Windows pierda datos en cada lectura
- ✅ Consultas rápidas sin I/O
- ✅ Sincronización automática: set_limits() actualiza cache Y QSettings
- ✅ Nunca rellena con valores del mapa (evita -300, 600, etc al serial)

### 2. Cálculo Automático de PTM (gui/appMainHemodialysis.py)

**Responsabilidad**: Calcular PTM cada vez que llega cualquiera de 4 presiones

```python
def update_value(self, tag: str, value: float):
    # ... código existente ...
    
    # Si llega CUALQUIERA de estas 4 presiones:
    if tag in ("dialyPresIFProcessData", "dialyPresOFProcessData", 
               "bloodArteryPressureData", "bloodVenousPressureData"):
        
        # Recolectar todas las 4 desde current_values
        pd_ef = self.current_values.get("dialyPresIFProcessData")
        pd_sf = self.current_values.get("dialyPresOFProcessData")
        pa = self.current_values.get("bloodArteryPressureData")
        pv = self.current_values.get("bloodVenousPressureData")
        
        # Recalcular PTM (función NO modificada)
        ptm_value = calculo_ptm(pd_ef, pd_sf, pa, pv)
        
        # Guardar en current_values
        self.current_values["CALC_PTM"] = ptm_value
        
        # Actualizar alarma (usa límites del JSON cache automáticamente)
        if self.alarm_system:
            self.alarm_system.update_value_by_tag("CALC_PTM", ptm_value)
        
        logger.debug(f"[PTM-CALC] Updated: {ptm_value:.1f} mmHg (from {tag}={value})")
```

**Características**:
- ✅ Se ejecuta AUNQUE la pantalla de Configuración esté cerrada
- ✅ Usa la función calculo_ptm() original (sin cambios de fórmula)
- ✅ Resultado se guarda en current_values["CALC_PTM"]
- ✅ Alarma se actualiza automáticamente
- ✅ Logs detallados con tag origen y valor calculado

### 3. Sincronización al Guardar (gui/configuration/alarm_screen_config.py)

**Responsabilidad**: Guardar valores de usuario y escribir al dispositivo

```python
def save_configuration(self):
    """4-paso: validar → guardar → QSettings → escribir al serial"""
    
    # PASO 1: Validar TODAS las filas
    for tag, widgets in self.inputs.items():
        if widgets.get('type') == "double":
            min_v = float(widgets['min'].text())
            max_v = float(widgets['max'].text())
            
            # Validación 1: min < max
            if min_v >= max_v:
                self.show_warning_message("...")
                return  # ← SALIR sin guardar
            
            # Validación 2: dentro de rango del mapa
            default_min, default_max = self.config_manager.get_default_limits_from_variables_map(tag)
            if min_v < default_min or min_v > default_max:
                self.show_warning_message("...")
                return  # ← SALIR sin guardar
    
    # PASO 2: Si todo validó, guardar en cache + QSettings
    for tag, widgets in self.inputs.items():
        level = widgets['level'].currentText()
        self.config_manager.set_severity(tag, level)
        
        if widgets.get('type') == "double":
            min_v = float(widgets['min'].text())
            max_v = float(widgets['max'].text())
            self.config_manager.set_limits(tag, min_v, max_v)  # ← Cache + JSON
    
    # PASO 3: Persistencia en QSettings
    self.config_manager.save_config()
    
    # PASO 4: Escribir 6 tags al dispositivo
    self._write_pressure_limits_to_device()
```

### 4. Escritura al Dispositivo - Guardar (alarm_screen_config.py)

**Responsabilidad**: Escribir 6 tags exactos, con lectura inteligente

```python
def _write_pressure_limits_to_device(self):
    """Escribe 6 tags al control.
    Lee de widgets si están en pantalla, sino del JSON cache."""
    
    if not self.write_setpoint_callback:
        return  # No conectado
    
    results = []
    
    # ARTERIAL: lee widgets (siempre en pantalla)
    art_min = float(self.inputs["bloodArteryPressureData"]['min'].text())
    art_max = float(self.inputs["bloodArteryPressureData"]['max'].text())
    r1 = self.write_setpoint_callback("artPresCircAlarmLoLimData", art_min)
    r2 = self.write_setpoint_callback("artPresCircAlarmHiLimData", art_max)
    logger.info(f"GUARDAR: artPresCircAlarmLoLimData = {art_min} ({r1})")
    logger.info(f"GUARDAR: artPresCircAlarmHiLimData = {art_max} ({r2})")
    results.append(r1 and r2)
    
    # VENOSA: lee widgets (siempre en pantalla)
    ven_min = float(self.inputs["bloodVenousPressureData"]['min'].text())
    ven_max = float(self.inputs["bloodVenousPressureData"]['max'].text())
    r1 = self.write_setpoint_callback("venPresCircAlarmLoLimData", ven_min)
    r2 = self.write_setpoint_callback("venPresCircAlarmHiLimData", ven_max)
    logger.info(f"GUARDAR: venPresCircAlarmLoLimData = {ven_min} ({r1})")
    logger.info(f"GUARDAR: venPresCircAlarmHiLimData = {ven_max} ({r2})")
    results.append(r1 and r2)
    
    # PTM: inteligente (widget SI existe, JSON SI no existe)
    if "CALC_PTM" in self.inputs:
        # Pantalla abierta: leer del widget
        ptm_min = float(self.inputs["CALC_PTM"]['min'].text())
        ptm_max = float(self.inputs["CALC_PTM"]['max'].text())
        r1 = self.write_setpoint_callback("membPressAlarmLoLimData", ptm_min)
        r2 = self.write_setpoint_callback("membPressAlarmHiLimData", ptm_max)
        logger.info(f"GUARDAR: membPressAlarmLoLimData = {ptm_min} ({r1})")
        logger.info(f"GUARDAR: membPressAlarmHiLimData = {ptm_max} ({r2})")
        results.append(r1 and r2)
    else:
        # Pantalla cerrada: leer del JSON
        ptm_min, ptm_max = self.config_manager._limits_cache["CALC_PTM"]
        r1 = self.write_setpoint_callback("membPressAlarmLoLimData", ptm_min)
        r2 = self.write_setpoint_callback("membPressAlarmHiLimData", ptm_max)
        logger.info(f"GUARDAR: membPressAlarmLoLimData = {ptm_min} ({r1}) [desde JSON]")
        logger.info(f"GUARDAR: membPressAlarmHiLimData = {ptm_max} ({r2}) [desde JSON]")
        results.append(r1 and r2)
    
    # Analizar: si alguno falló, avisar pero SIN cortar las otras escrituras
    all_written = all(results) if results else False
    
    if not all_written:
        self.show_warning_message(
            "Los límites quedaron guardados en la interfaz, "
            "pero no se enviaron al control.",
            timeout_ms=3000
        )
```

**Características críticas**:
- ✅ Valida TODO antes de escribir nada
- ✅ NO corta si una escritura falla (continúa las 6)
- ✅ Logs detallados: `GUARDAR: tag = valor (True/False)`
- ✅ Lee inteligentemente: widgets SI existe, JSON SI no
- ✅ Si serial desconectado: guarda JSON igual, avisa al usuario

### 5. Sincronización al Conectar (appMainHemodialysis.py)

**Responsabilidad**: Reescribir límites cuando se reconecta el dispositivo

```python
def _write_pressure_limits_on_connection(self):
    """Llamada desde update_connection_status cuando conecta.
    Lee cache directamente, escribe 6 tags."""
    
    if not self.serial_comm or not self.serial_comm.is_connected:
        return
    
    limits_cache = self.config_manager._limits_cache
    
    if not limits_cache:
        logger.info("Cache de límites vacío: no se escriben límites al conectar")
        return
    
    results = []
    
    # ARTERIAL (si existe en cache)
    if "bloodArteryPressureData" in limits_cache:
        art_min, art_max = limits_cache["bloodArteryPressureData"]
        r1 = self._write_setpoint("artPresCircAlarmLoLimData", art_min)
        r2 = self._write_setpoint("artPresCircAlarmHiLimData", art_max)
        logger.info(f"CONEXIÓN: artPresCircAlarmLoLimData = {art_min} ({r1})")
        logger.info(f"CONEXIÓN: artPresCircAlarmHiLimData = {art_max} ({r2})")
        results.append(r1 and r2)
    
    # VENOSA (si existe en cache)
    if "bloodVenousPressureData" in limits_cache:
        ven_min, ven_max = limits_cache["bloodVenousPressureData"]
        r1 = self._write_setpoint("venPresCircAlarmLoLimData", ven_min)
        r2 = self._write_setpoint("venPresCircAlarmHiLimData", ven_max)
        logger.info(f"CONEXIÓN: venPresCircAlarmLoLimData = {ven_min} ({r1})")
        logger.info(f"CONEXIÓN: venPresCircAlarmHiLimData = {ven_max} ({r2})")
        results.append(r1 and r2)
    
    # PTM (si existe en cache)
    if "CALC_PTM" in limits_cache:
        ptm_min, ptm_max = limits_cache["CALC_PTM"]
        r1 = self._write_setpoint("membPressAlarmLoLimData", ptm_min)
        r2 = self._write_setpoint("membPressAlarmHiLimData", ptm_max)
        logger.info(f"CONEXIÓN: membPressAlarmLoLimData = {ptm_min} ({r1})")
        logger.info(f"CONEXIÓN: membPressAlarmHiLimData = {ptm_max} ({r2})")
        results.append(r1 and r2)
    
    all_written = all(results) if results else False
    
    if not all_written:
        logger.warning("Algunos límites no se escribieron al reconectar")
```

**Características**:
- ✅ Lee directamente del cache (NO llama get_limits)
- ✅ Solo escribe si el tag existe en cache (nunca manda defaults)
- ✅ NO corta si una falla
- ✅ Logs diferenciados: `CONEXIÓN: ...` vs `GUARDAR: ...`
- ✅ Mantiene alarmas en sincronía aunque GUI esté cerrada

## Flujos de Datos

### Flujo A: Primer Uso (Cache Vacío)

```
Usuario abre Configuración
    ↓
Lee valores del mapa (get_limits → mapa)
    ↓
Usuario edita casillas
    ↓
Usuario pulsa Guardar Cambios
    ↓
save_configuration():
  1. Valida
  2. set_limits() → cache + JSON
  3. save_config() → QSettings
  4. _write_pressure_limits_to_device() → serial (6 tags)
    ↓
Logs: GUARDAR: artPresCircAlarmLoLimData = X (True)
```

### Flujo B: Desconectar/Reconectar

```
Serial conectado (cache lleno con JSON)
    ↓
Usuario desconecta serie
    ↓
update_connection_status(False)
    ↓
Serial se reconecta
    ↓
update_connection_status(True)
    ↓
_write_pressure_limits_on_connection():
  Leer cache JSON
  Escribir 6 tags al serial
    ↓
Logs: CONEXIÓN: artPresCircAlarmLoLimData = X (True)
```

### Flujo C: PTM Automático (Sin GUI Abierta)

```
Serial envía presión arterial
    ↓
update_value("bloodArteryPressureData", X)
    ↓
Detecta: es una de las 4 presiones triguer
    ↓
calculo_ptm(pd_ef, pd_sf, pa, pv) → PTM_VALUE
    ↓
current_values["CALC_PTM"] = PTM_VALUE
    ↓
alarm_system.update_value_by_tag("CALC_PTM", PTM_VALUE)
    ↓
Alarma compara PTM_VALUE contra límites del cache
    ↓
Log: [PTM-CALC] Updated: X.X mmHg (from bloodArteryPressureData=Y)
```

## Mapeo de Tags al Dispositivo

| Concepto | Tag UI | Tag Dispositivo (0x06 group) | Dirección |
|----------|--------|------------------------------|-----------|
| Arterial Superior | bloodArteryPressureData max | artPresCircAlarmHiLimData | 0x06 |
| Arterial Inferior | bloodArteryPressureData min | artPresCircAlarmLoLimData | 0x07 |
| Venosa Superior | bloodVenousPressureData max | venPresCircAlarmHiLimData | 0x08 |
| Venosa Inferior | bloodVenousPressureData min | venPresCircAlarmLoLimData | 0x09 |
| PTM Superior | CALC_PTM max | membPressAlarmHiLimData | 0x0A |
| PTM Inferior | CALC_PTM min | membPressAlarmLoLimData | 0x0B |

## JSON Persistencia

### Formato QSettings

```python
{
  "alarms/enabled_tags": [list of tags],
  "alarms/limits": "{\"bloodArteryPressureData\": [-300, 600], \"bloodVenousPressureData\": [-100, 500], \"CALC_PTM\": [-100, 1000], ...}",  # ← JSON STRING
  "alarms/severity": {...}
}
```

### Carga al Iniciar

```python
raw = self.settings.value(self.KEY_LIMITS, "")

# Formato viejo (dict) → copiar
if isinstance(raw, dict):
    self._limits_cache = dict(raw)

# Formato nuevo (JSON string) → parsear
elif isinstance(raw, str) and raw.strip():
    try:
        loaded = json.loads(raw)
        self._limits_cache = dict(loaded) if isinstance(loaded, dict) else {}
    except (json.JSONDecodeError, ValueError, TypeError):
        self._limits_cache = {}  # ← Vacío, SIN rellenar
else:
    self._limits_cache = {}
```

## Manejo de Errores y Excepciones

### _write_setpoint() - Retorno de Bool

```python
def _write_setpoint(self, tag: str, value: float) -> bool:
    # LOCAL tag
    if tag in LOCAL_SETPOINT_TAGS:
        # ... guardar en local ...
        return False  # ← Local no se escribe al serial
    
    # No conectado
    if not self.serial_comm or not self.serial_comm.is_connected:
        logger.warning(f"No se puede escribir setpoint '{tag}': serial desconectado")
        return False  # ← Error: desconectado
    
    # Tag no encontrado
    try:
        group, address = self._resolve_tag(tag)
        if group is None or address is None:
            logger.warning(f"Tag '{tag}' no encontrado en VARIABLES")
            return False  # ← Error: tag no existe
    
    # Write success
    self.serial_comm.write_double(group, address, value)
    logger.info(f"SETPOINT [DBL]: {tag} = {value}")
    return True  # ← Éxito
    
    # Excepción
    except Exception as e:
        logger.error(f"Error escribiendo setpoint '{tag}': {e}")
        return False  # ← Error: excepción
```

**Garantía**: NUNCA devuelve None

### Lectura de JSON con Validación

```python
try:
    raw = self.settings.value(self.KEY_LIMITS, "")
    
    if isinstance(raw, dict):
        self._limits_cache = dict(raw)
    elif isinstance(raw, str) and raw.strip():
        loaded = json.loads(raw)  # ← Puede lanzar JSONDecodeError
        self._limits_cache = dict(loaded) if isinstance(loaded, dict) else {}
    else:
        self._limits_cache = {}

except (json.JSONDecodeError, ValueError, TypeError) as e:
    # ← Atrapa todos los errores posibles
    logger.error(f"Error cargando límites: {e}")
    self._limits_cache = {}  # ← Vacío (seguro)
```

## Notas de Implementación

1. **Cache-First Design**: Siempre leer cache primero evita que QSettings en Windows pierda datos

2. **JSON Serialización**: Los strings JSON son más robustos que dicts en QSettings en Windows

3. **Sin Auto-fill de Mapa**: El cache nunca se rellena con valores del mapa evita enviar hardcoded -300, 600 al dispositivo

4. **Temperatura Guardada pero NO Escrita**: Se persiste en JSON junto con presiones para compatibilidad, pero no se manda al serial

5. **Validación Exhaustiva**: Antes de guardar NADA, se validan todas las filas

6. **No Corta Escrituras**: Aunque falle una escritura, las demás se ejecutan para máxima sincronización

7. **Logs Diferenciados**: GUARDAR vs CONEXIÓN permiten auditar cada punto de sincronización

8. **PTM Automático Siempre**: Aunque no esté la pantalla, PTM se recalcula y alarma funciona

---

**Última actualización**: 2024 (commit f1bcab6)
**Versión**: 1.0 Estable
