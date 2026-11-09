# Implementación de Control de Límites de Presión y Cálculo de PTM

## Resumen de Cambios

Se han realizado cambios para permitir que los límites de alarma de presión arterial, venosa y transmembrana (PTM) se escriban y sincronicen entre la aplicación y el dispositivo hardware.

## Cambios por Archivo

### 1. `core/variables_map.py`

#### Cambio 1: Agregar grupo LOCAL con CALC_PTM
```
Ubicación: Final del diccionario VARIABLES (después de 0x0C)
Nuevo grupo:
  "LOCAL": {
      0x00: {"name": "Presión transmembrana", "label": "PTM", "type": "double", 
             "rw": False, "unit": "mmHg", "limites": (-100, 1000), 
             "tag": "CALC_PTM", "nivel": "rojo"}
  }
```
- Grupo LOCAL: No se sincroniza por serial, solo existe en memoria
- CALC_PTM: Variable calculada (rw=False) que se actualiza continuamente
- Los límites (-100, 1000) mmHg definen el rango permitido
- Nivel "rojo" indica alarma crítica

#### Cambio 2: Actualizar TVAR_TO_GROUP
```
Agregado:
  "LOCAL": "Variables Locales"
  0x0C: "Sensores Mega"  (actualización de etiqueta)
```
- Permite que el sistema de UI identifique el grupo LOCAL

#### Notas sobre 0x06:
- Los 6 tags de presión ya estaban presentes en direcciones 0x06-0x0B:
  - 0x06: artPresCircAlarmHiLimData  (Límite alto presión arterial)
  - 0x07: artPresCircAlarmLoLimData  (Límite bajo presión arterial)
  - 0x08: venPresCircAlarmHiLimData  (Límite alto presión venosa)
  - 0x09: venPresCircAlarmLoLimData  (Límite bajo presión venosa)
  - 0x0A: membPressAlarmHiLimData    (Límite alto PTM)
  - 0x0B: membPressAlarmLoLimData    (Límite bajo PTM)
- Unidad: "" (vacía, se mandan en mmHg tal cual)
- Nivel: "rojo" (alarmas críticas)
- ANALOG_MAP NO fue modificado (mantiene tamaño de 71 variables)

---

### 2. `gui/appMainHemodialysis.py`

#### Cambio 1: Agregar importación de calculo_ptm
```python
from logic.calculos import (
    ...
    calculo_ptm,  # Agregado
)
```

#### Cambio 2: Implementar cálculo de PTM automático en update_value()
Ubicación: Función `update_value()` (línea ~2878)
```python
# 2.5 Calcular PTM si cualquiera de las cuatro presiones cambió
if tag in ("dialyPresIFProcessData", "dialyPresOFProcessData", 
           "bloodArteryPressureData", "bloodVenousPressureData"):
    pd_ef = self.current_values.get("dialyPresIFProcessData")
    pd_sf = self.current_values.get("dialyPresOFProcessData")
    pa = self.current_values.get("bloodArteryPressureData")
    pv = self.current_values.get("bloodVenousPressureData")
    
    ptm_value = calculo_ptm(pd_ef, pd_sf, pa, pv)
    self.current_values["CALC_PTM"] = ptm_value
    logger.debug(f"[PTM-CALC] Updated: {ptm_value:.1f} mmHg (from {tag}={value})")
    
    # Actualizar alarma para CALC_PTM también
    if self.alarm_system:
        self.alarm_system.update_value_by_tag("CALC_PTM", ptm_value)
```
- Se ejecuta CADA VEZ que llega cualquiera de las 4 lecturas de presión
- Calcula PTM y la almacena en `current_values["CALC_PTM"]`
- Actualiza el sistema de alarmas con el nuevo valor de PTM
- La alarma de PTM sigue "viva" incluso si no está abierta la pantalla de diálisis

#### Cambio 3: Agregar método _write_pressure_limits_on_connection()
Ubicación: Después de `_write_setpoint()` (línea ~3648)
```python
def _write_pressure_limits_on_connection(self):
    """Escribe los límites de presión arterial, venosa y PTM al dispositivo cuando se conecta."""
    if not self.serial_comm or not self.serial_comm.is_connected:
        return
    
    try:
        # Presión arterial
        art_min, art_max = self.config_manager.get_limits("bloodArteryPressureData")
        self._write_setpoint("artPresCircAlarmLoLimData", art_min)
        self._write_setpoint("artPresCircAlarmHiLimData", art_max)
        
        # Presión venosa
        ven_min, ven_max = self.config_manager.get_limits("bloodVenousPressureData")
        self._write_setpoint("venPresCircAlarmLoLimData", ven_min)
        self._write_setpoint("venPresCircAlarmHiLimData", ven_max)
        
        # PTM
        ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")
        self._write_setpoint("membPressAlarmLoLimData", ptm_min)
        self._write_setpoint("membPressAlarmHiLimData", ptm_max)
        
        logger.info("Límites de presión sincronizados con dispositivo al conectar")
    except Exception as e:
        logger.warning(f"No se pudo sincronizar límites de presión al conectar: {e}")
```
- Se ejecuta cuando la conexión serial se establece (`is_connected` pasa de False a True)
- Sincroniza los 6 límites desde AlarmConfigManager al dispositivo
- Los valores vienen de lo guardado localmente o los defaults de variables_map
- Si el serial no está conectado, no escribe nada

#### Cambio 4: Activar sincronización en update_connection_status()
Ubicación: Función `update_connection_status()` (línea ~3420)
```python
if current_is_connected:
    self._connection_just_established_ticks = 3
    # Escribir límites de presión al dispositivo cuando se establece la conexión
    self._write_pressure_limits_on_connection()
```
- Cuando se detecta que la conexión pasó de desconectado a conectado
- Se llama automáticamente a `_write_pressure_limits_on_connection()`

#### Cambio 5: Pasar callback a AlarmScreenConfig
Ubicación: Instanciación de `AlarmScreenConfig` (línea ~542)
```python
self.alarm_config_limits_screen = AlarmScreenConfig(
    config_manager=self.config_manager,
    parent=self,
    write_setpoint_callback=self._write_setpoint  # Agregado
)
```
- Pasa la referencia a `_write_setpoint` para que la pantalla de alarmas pueda escribir

---

### 3. `gui/configuration/alarm_screen_config.py`

#### Cambio 1: Agregar parámetro write_setpoint_callback en __init__
```python
def __init__(self, config_manager: AlarmConfigManager, parent=None, write_setpoint_callback=None):
    super().__init__(parent)
    self.config_manager = config_manager
    self.write_setpoint_callback = write_setpoint_callback  # Callback para escribir
```
- Acepta una función callback para escribir setpoints al dispositivo
- Si es None, solo guarda los valores localmente

#### Cambio 2: Llamar a _write_pressure_limits_to_device() en save_configuration()
Ubicación: Función `save_configuration()` (línea ~264)
```python
self.config_manager.save_config()

# Escribir límites de presión arterial, venosa y PTM al dispositivo si está conectado
self._write_pressure_limits_to_device()

self.show_success_message("Configuración de alarmas guardada correctamente.", timeout_ms=2000)
```
- Se ejecuta DESPUÉS de guardar localmente
- Sincroniza con el dispositivo si está disponible

#### Cambio 3: Implementar _write_pressure_limits_to_device()
Ubicación: Nueva función (línea ~304)
```python
def _write_pressure_limits_to_device(self):
    """Escribe los límites de presión arterial, venosa y PTM al dispositivo si está conectado."""
    if not self.write_setpoint_callback:
        return  # No hay forma de escribir, solo guardar localmente
    
    try:
        # Presión arterial
        art_min, art_max = self.config_manager.get_limits("bloodArteryPressureData")
        self.write_setpoint_callback("artPresCircAlarmLoLimData", art_min)
        self.write_setpoint_callback("artPresCircAlarmHiLimData", art_max)
        
        # Presión venosa
        ven_min, ven_max = self.config_manager.get_limits("bloodVenousPressureData")
        self.write_setpoint_callback("venPresCircAlarmLoLimData", ven_min)
        self.write_setpoint_callback("venPresCircAlarmHiLimData", ven_max)
        
        # PTM
        ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")
        self.write_setpoint_callback("membPressAlarmLoLimData", ptm_min)
        self.write_setpoint_callback("membPressAlarmHiLimData", ptm_max)
        
        logger.info("Límites de presión escritos al dispositivo correctamente")
    except Exception as e:
        logger.warning(f"No se pudo escribir límites de presión al dispositivo: {e}")
```
- Recupera los límites actuales del AlarmConfigManager
- Escribe cada uno usando la callback proporcionada
- Si el dispositivo no está conectado, _write_setpoint() manejará el error silenciosamente

---

## Flujo de Datos

### Escritura de Límites (Usuario → Dispositivo)

1. **Usuario configura en la pantalla de alarmas**
   - Ingresa nuevos límites en AlarmScreenConfig
   - Presiona "Guardar"

2. **save_configuration() en AlarmScreenConfig**
   - Valida los valores
   - Llama a `config_manager.set_limits(tag, min, max)`
   - Guarda en QSettings localmente

3. **_write_pressure_limits_to_device()**
   - Recupera los límites guardados con `config_manager.get_limits()`
   - Llama a `write_setpoint_callback()` para cada una de las 6 variables
   - Envía por serial si está conectado

4. **_write_setpoint() en appMainHemodialysis.py**
   - Valida que la variable sea escribible (rw=True)
   - Llama a `serial_comm.write_double(group, address, value)`
   - El dispositivo recibe y almacena los límites

### Lectura y Cálculo de PTM (Dispositivo → Aplicación)

1. **Dispositivo envía presiones**
   - dialyPresIFProcessData (presión entrada filtro)
   - dialyPresOFProcessData (presión salida filtro)
   - bloodArteryPressureData (presión arterial)
   - bloodVenousPressureData (presión venosa)

2. **SerialCommunication emite data_received signal**
   - Envía (tag, value) para cada variable

3. **update_value() recibe la actualización**
   - Guarda el valor en `current_values[tag]`
   - Si el tag es uno de los 4 de presión:
     - Recupera los 4 valores de `current_values`
     - Llama a `calculo_ptm(pd_ef, pd_sf, pa, pv)`
     - Guarda en `current_values["CALC_PTM"]`
     - Actualiza alarmas con el nuevo PTM

4. **Sistema de alarmas monitorea CALC_PTM**
   - Compara CALC_PTM con los límites en membPressAlarmLoLimData/HiLimData
   - Si está fuera de rango, genera alarma

### Sincronización al Conectar (Dispositivo ← Aplicación)

1. **update_connection_status() detecta conexión**
   - El flag `is_connected` cambia de False a True

2. **_write_pressure_limits_on_connection()**
   - Recupera los 6 límites del AlarmConfigManager
   - Llama a `_write_setpoint()` para cada uno
   - Los límites guardados localmente se sincronizan con el dispositivo

3. **Garantía de consistencia**
   - Si el usuario había guardado límites antes de desconectarse
   - Al reconectar, se restauran automáticamente en el dispositivo
   - Si nunca se guardaron, se usan los defaults de variables_map

---

## Consideraciones de Diseño

### No se modifica la trama de comunicación
- ANALOG_MAP sigue teniendo exactamente 71 variables
- Los 6 tags de presión están en las direcciones 0x06-0x0B (ya existían)
- El protocolo Modbus NO cambió

### Conversión de unidades
- Todos los límites se envían en mmHg (sin conversión)
- El dispositivo los almacena tal cual

### Protección de datos
- Si el serial no está conectado:
  - Los valores se guardan localmente
  - Se escriben automáticamente cuando se reconecta
  - No se pierden los límites configurados

### Alarmas funcionan sin GUI
- El cálculo de PTM ocurre en `update_value()`
- Funciona incluso si no está abierta la pantalla de diálisis
- El sistema de alarmas monitorea CALC_PTM continuamente

### Tags especiales
- CALC_PTM: Variable local (no existe en dispositivo)
- Los 6 límites: Variables en dispositivo (escritura permitida)

---

## Validación Realizada

- [x] CALC_PTM agregado correctamente en grupo LOCAL
- [x] Los 6 tags de presión presentes en direcciones 0x06-0x0B
- [x] Límites correctos para cada tag
- [x] ANALOG_MAP no modificado (71 entradas)
- [x] Sintaxis de Python validada en todos los archivos
- [x] Integraciones y callbacks correctas

---

## Rollback (si es necesario)

Para revertir los cambios:
1. Revertir grupo LOCAL de variables_map.py
2. Comentar los bloques de cálculo de PTM en appMainHemodialysis.py
3. Remover los métodos de escritura de límites
4. Restaurar instanciación de AlarmScreenConfig sin callback
