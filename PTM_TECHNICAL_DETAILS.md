# Detalles Técnicos: Sincronización de Límites de Presión

## 1. Estructura de Datos en variables_map.py

### Grupo 0x06 (Calibración - Presiones)
Direcciones 0x00-0x05: Lecturas del dispositivo
- 0x00: heparCalibFactorData (Factor calibración heparina)
- 0x01: dialyUFilPresProcessData (Presión ultrafiltrado)
- 0x02: dialyBChamPresProcessData (Presión cámara balance)
- 0x03: bloodArteryPressureData (Presión arterial - LECTURA)
- 0x04: bloodVenousPressureData (Presión venosa - LECTURA)
- 0x05: dialyCycleOperationCount (Contador ciclos)

Direcciones 0x06-0x0B: Setpoints de límites de alarma (ESCRITURA)
- 0x06: artPresCircAlarmHiLimData (Límite ALTO presión arterial) [-300, 300]
- 0x07: artPresCircAlarmLoLimData (Límite BAJO presión arterial) [-300, 300]
- 0x08: venPresCircAlarmHiLimData (Límite ALTO presión venosa) [-100, 500]
- 0x09: venPresCircAlarmLoLimData (Límite BAJO presión venosa) [-100, 500]
- 0x0A: membPressAlarmHiLimData (Límite ALTO PTM) [-100, 1000]
- 0x0B: membPressAlarmLoLimData (Límite BAJO PTM) [-100, 1000]

### Grupo LOCAL (Variables Locales)
No se sincroniza con el dispositivo, solo existe en memoria
- 0x00: CALC_PTM (Presión transmembrana calculada) [-100, 1000]

## 2. Ciclo de Vida del Cálculo de PTM

### Fase 1: Inicialización
```
Aplicación inicia
  → current_values["CALC_PTM"] = 0.0 (valor por defecto)
  → alarm_system inicia monitoreo de CALC_PTM
```

### Fase 2: Recepción de Datos
```
SerialCommunication recibe lectura analógica
  → Emite signal: data_received("bloodArteryPressureData", 120.0)
  → Emite signal: data_received("bloodVenousPressureData", 60.0)
  → Emite signal: data_received("dialyPresIFProcessData", 10.0)
  → Emite signal: data_received("dialyPresOFProcessData", 15.0)
```

### Fase 3: Procesamiento en update_value()
```
Signal conectado a: HemodialysisHMI.update_value()
  
Para cada presión recibida:
  1. Guardar en current_values[tag]
  2. Verificar si es uno de los 4 tags de presión
  3. Si es presión:
     a. Recuperar las 4 presiones de current_values
     b. Llamar: ptm_value = calculo_ptm(pd_ef, pd_sf, pa, pv)
     c. Guardar: current_values["CALC_PTM"] = ptm_value
     d. Actualizar alarma: alarm_system.update_value_by_tag("CALC_PTM", ptm_value)
  4. Actualizar alarma para el tag original
```

### Fase 4: Monitoreo de Alarmas
```
AlarmSystem continuamente:
  → Lee current_values["CALC_PTM"]
  → Obtiene límites: [membPressAlarmLoLimData, membPressAlarmHiLimData]
  → Si CALC_PTM < LoLim o > HiLim → ALARMA
  → Genera evento si sobrepasa umbral configurado
```

## 3. Ciclo de Escritura de Límites (Guardar Configuración)

### Usuario interactúa con AlarmScreenConfig
```
Usuario abre pantalla de alarmas
  → Ve límites actuales para:
      - bloodArteryPressureData
      - bloodVenousPressureData
      - CALC_PTM
  → Modifica uno o más límites
  → Presiona botón "Guardar"
```

### save_configuration() se ejecuta
```
Ubicación: gui/configuration/alarm_screen_config.py

Para cada tag en self.inputs:
  1. Validar nuevo valor
  2. Comparar con límites permitidos del mapa
  3. Si válido:
     - config_manager.set_limits(tag, min_val, max_val)
     - config_manager.set_severity(tag, level)
     
4. config_manager.save_config()  # Guarda en QSettings
5. Llamar: self._write_pressure_limits_to_device()
```

### _write_pressure_limits_to_device() escribe en dispositivo
```
For each pressure type:
  1. art_min, art_max = config_manager.get_limits("bloodArteryPressureData")
     write_setpoint_callback("artPresCircAlarmLoLimData", art_min)
     write_setpoint_callback("artPresCircAlarmHiLimData", art_max)
     
  2. ven_min, ven_max = config_manager.get_limits("bloodVenousPressureData")
     write_setpoint_callback("venPresCircAlarmLoLimData", ven_min)
     write_setpoint_callback("venPresCircAlarmHiLimData", ven_max)
     
  3. ptm_min, ptm_max = config_manager.get_limits("CALC_PTM")
     write_setpoint_callback("membPressAlarmLoLimData", ptm_min)
     write_setpoint_callback("membPressAlarmHiLimData", ptm_max)
```

### _write_setpoint() en appMainHemodialysis
```
Para cada (tag, value):
  1. Resolver tag → (group, address) en VARIABLES_MAP
  2. Validar que sea escribible (rw=True)
  3. serial_comm.write_double(group, address, value)
  4. Persistir localmente: _persist_therapy_config_tag(tag, value)
```

## 4. Sincronización al Conectar

### Detección de Conexión
```
Ubicación: HemodialysisHMI.update_connection_status()

Cada tick (~500ms):
  - current_is_connected = serial_comm.is_connected
  - Si cambió de False → True:
      - _sync_state_with_hardware()
      - _set_ui_connected_state(True)
      - _write_pressure_limits_on_connection()  ← Agregado
```

### _write_pressure_limits_on_connection()
```
if not serial_comm.is_connected:
    return  # No conectado, salir silenciosamente

try:
    # Recuperar límites guardados (o defaults si no hay guardados)
    art_min, art_max = config_manager.get_limits("bloodArteryPressureData")
    ven_min, ven_max = config_manager.get_limits("bloodVenousPressureData")
    ptm_min, ptm_max = config_manager.get_limits("CALC_PTM")
    
    # Escribir cada uno
    _write_setpoint("artPresCircAlarmLoLimData", art_min)
    _write_setpoint("artPresCircAlarmHiLimData", art_max)
    _write_setpoint("venPresCircAlarmLoLimData", ven_min)
    _write_setpoint("venPresCircAlarmHiLimData", ven_max)
    _write_setpoint("membPressAlarmLoLimData", ptm_min)
    _write_setpoint("membPressAlarmHiLimData", ptm_max)
    
    logger.info("Límites sincronizados al conectar")
    
except Exception as e:
    logger.warning(f"Error sincronizando: {e}")
    # No bloquea el resto de la aplicación
```

## 5. Valores Persistentes

### AlarmConfigManager.get_limits(tag)
```python
def get_limits(self, tag: str) -> Tuple[float, float]:
    # Intenta obtener de QSettings (guardado por usuario)
    limits_dict = self.settings.value(self.KEY_LIMITS, {})
    if tag in limits_dict:
        return limits_dict[tag]  # Usa valores guardados
    
    # Si no está guardado, usa defaults del mapa
    return self.get_default_limits_from_variables_map(tag)
```

### Garantías de Consistencia
1. **Antes de guardar**: Valores están en QSettings
2. **Al guardar**: Se sincronizan con dispositivo si está conectado
3. **Al desconectar**: Valores permanecen en QSettings
4. **Al conectar**: Se restauran automáticamente en dispositivo
5. **Si dispositivo se reinicia**: Próxima conexión restaura limites

## 6. Manejo de Errores

### Caso: Dispositivo desconectado
```
Usuario guarda → save_configuration()
  → _write_pressure_limits_to_device()
    → write_setpoint_callback() → _write_setpoint()
      → if not serial_comm.is_connected:
            logger.warning("No se puede escribir setpoint")
            return  # Falla silenciosa

Resultado: Guardado local OK, escritura device ignorada
           Valores se escribirán cuando se reconecte
```

### Caso: Error en cálculo de PTM
```
calculo_ptm() recibe None:
  → logger.warning("PTM: Valor nulo")
  → return 0.0  # Devuelve 0 en lugar de fallar

Resultado: CALC_PTM = 0.0, alarma verifica si está en rango
```

### Caso: Validación de límites falla
```
Usuario intenta guardar límite fuera de rango:
  → save_configuration() valida
  → if min_v < default_min or min_v > default_max:
        show_warning_message("Fuera de rango")
        return  # No guarda

Resultado: Límites no se modifican, se muestra error al usuario
```

## 7. Integración con Alarmas

### AlarmSystem.update_value_by_tag(tag, value)
```
Llamado desde update_value():
  1. alarm_system.update_value_by_tag(tag, value)  # Presión original
  2. alarm_system.update_value_by_tag("CALC_PTM", ptm_value)  # PTM

Internamente:
  for alarm in self.alarms:
      if alarm.monitored_tag == tag:
          alarm.update_value(value)
          if value out of limits:
              alarm.trigger()
```

### Alarma de PTM
```
Tipo: Alarma por rango
Tag monitoreado: "CALC_PTM"
Límites obtenidos de: membPressAlarmLoLimData y membPressAlarmHiLimData
Nivel de severidad: "rojo" (crítico)

Condición de alarma:
  CALC_PTM < membPressAlarmLoLimData  OR  CALC_PTM > membPressAlarmHiLimData
  
Acciones al disparar:
  - Buzzer suena
  - Barra LED roja
  - Evento registrado
  - Notificación en UI
```

## 8. Performance y Overhead

### Cálculo de PTM
```
Frecuencia: Cada vez que llega UNA de las 4 presiones
Típicamente: ~2 veces por segundo (500ms entre lecturas)
Operaciones:
  - 4 lookups en dictionary: current_values.get()
  - 1 cálculo aritmético simple
  - 1 update en dictionary: current_values["CALC_PTM"]
  - 1 llamada a alarm_system.update_value_by_tag()
Tiempo estimado: <1ms

Impacto: Negligible
```

### Escritura de Límites
```
Frecuencia: Solo al guardar configuración o al conectar
Operaciones por escritura:
  - Serial write (~50ms por dato si se envían seguidos)
  - Total: 6 variables * 50ms ≈ 300ms (no bloqueante, background)

Impacto: No perceptible al usuario
```

## 9. Testing Recomendado

### Test 1: Cálculo de PTM
```python
from logic.calculos import calculo_ptm

# Caso normal
ptm = calculo_ptm(10.0, 15.0, 120.0, 60.0)
assert -100 <= ptm <= 1000

# Caso límite bajo
ptm = calculo_ptm(10.0, 15.0, 0.0, 0.0)
assert ptm >= -100  # Clamped al mínimo

# Caso límite alto
ptm = calculo_ptm(10.0, 15.0, 1000.0, 1000.0)
assert ptm <= 1000  # Clamped al máximo

# Caso con None
ptm = calculo_ptm(10.0, 15.0, None, 60.0)
assert ptm == 0.0  # Devuelve 0 si falta dato
```

### Test 2: Guardado de Límites
```python
# Usuario abre pantalla
alarm_screen = AlarmScreenConfig(config_manager, parent=app)

# Modifica límites
alarm_screen.inputs["bloodArteryPressureData"]["min"].setText("100")
alarm_screen.inputs["bloodArteryPressureData"]["max"].setText("180")

# Guarda
alarm_screen.save_configuration()

# Verifica que se guardó
min_v, max_v = config_manager.get_limits("bloodArteryPressureData")
assert min_v == 100.0
assert max_v == 180.0
```

### Test 3: Sincronización al Conectar
```python
# Simular conexión
mock_serial.is_connected = True
app.serial_comm = mock_serial

# Trigger connection status update
app.update_connection_status()

# Verificar que se escribieron los setpoints
assert mock_serial.write_double.call_count >= 6  # 6 calls mínimo

# Verificar que se escribieron los valores correctos
calls = mock_serial.write_double.call_args_list
for group, address, value in calls:
    assert group == 0x06  # Grupo de calibración
    assert address >= 0x06 and address <= 0x0B  # Direcciones correctas
```

---

## Conclusión

La implementación permite:
1. Leer presiones del dispositivo en tiempo real
2. Calcular PTM automáticamente en memoria
3. Monitorear alarmas de PTM sin GUI abierta
4. Guardar límites de presión configurados
5. Sincronizar automáticamente al conectar
6. Mantener consistencia entre UI y dispositivo
7. Fallar gracefully si no hay conexión serial

Todo con cambios mínimos y quirúrgicos, sin modificar el protocolo Modbus ni el tamaño de las tramas.
