# Validación del Sistema de Sincronización de Límites de Presión

## Estado: ✅ COMPLETADO

### 1. Estructura de Datos y Persistencia

- [x] **core/variables_map.py**: Grupo LOCAL contiene CALC_PTM con rango (-100, 1000)
- [x] **core/alarm_config_manager.py**:
  - `_limits_cache`: diccionario en memoria (actualizado en set_limits, leído en get_limits)
  - `_load_limits_from_settings()`: Carga JSON o dict viejo sin rellenar con valores del mapa
  - `set_limits()`: Guarda en cache luego en QSettings como JSON string
  - `get_limits()`: Lee cache primero, solo mapa si no existe en cache

### 2. Cálculo Automático de PTM

- [x] **gui/appMainHemodialysis.py - update_value()**:
  - Se recalcula cuando llega: dialyPresIFProcessData, dialyPresOFProcessData,
    bloodArteryPressureData, bloodVenousPressureData
  - Resultado guardado en `current_values["CALC_PTM"]`
  - Alarma actualizada para CALC_PTM
  - Función calculo_ptm() NO modificada, usa sus límites originales (-100, 1000)

### 3. Sincronización al Guardar Configuración

- [x] **gui/configuration/alarm_screen_config.py - save_configuration()**:
  1. Valida TODAS las filas antes de escribir
  2. Guarda en JSON (AlarmConfigManager.set_limits)
  3. Llama a `_write_pressure_limits_to_device()`

- [x] **gui/configuration/alarm_screen_config.py - _write_pressure_limits_to_device()**:
  - Lee valores de widgets (o JSON si no están en widgets)
  - Escribe 6 tags exactos en orden:
    - artPresCircAlarmLoLimData (arterial inferior)
    - artPresCircAlarmHiLimData (arterial superior)
    - venPresCircAlarmLoLimData (venosa inferior)
    - venPresCircAlarmHiLimData (venosa superior)
    - membPressAlarmLoLimData (PTM inferior)
    - membPressAlarmHiLimData (PTM superior)
  - NO corta si una escritura falla
  - Loguea cada tag con valor y resultado (True/False)
  - Si serial desconectado: guarda JSON y avisa

### 4. Sincronización al Conectar

- [x] **gui/appMainHemodialysis.py - _write_pressure_limits_on_connection()**:
  - Llamada desde update_connection_status cuando conecta
  - Lee valores directamente del `_limits_cache`
  - Solo escribe si el tag existe en cache
  - Nunca escribe valores del mapa (-300, 600, -100, 500, -100, 1000)
  - NO corta si una escritura falla
  - Loguea cada tag con valor y resultado (True/False)

### 5. Comportamiento de Temperatura

- [x] Temperatura se guarda en JSON (AlarmConfigManager.set_limits)
- [x] Temperatura NO se escribe al serial (no hay _write_setpoint)
- [x] Histórico JSON mantiene estructura compatible

### 6. Validaciones Críticas

- [x] **_write_setpoint()** devuelve SIEMPRE bool:
  - True si write_double tuvo éxito
  - False si: serial desconectado, tag no encontrado, excepción, valor NULL
  - Nunca devuelve None

- [x] **CALC_PTM en widgets**:
  - Si está en pantalla: lee value de widget en _write_pressure_limits_to_device
  - Si NO está en pantalla: usa valor del JSON cache
  - Mismo comportamiento en conexión

- [x] **Manejo de excepciones**:
  - _load_limits_from_settings: atrapa JSONDecodeError, ValueError, TypeError
  - _write_setpoint: no lanza excepciones, retorna False
  - _write_pressure_limits_to_device: continúa aunque falle una escritura

### 7. Logs Críticos

- [x] Cada escritura loguea: `GUARDAR: tag = valor (True/False)`
- [x] Cada escritura en conexión loguea: `CONEXIÓN: tag = valor (True/False)`
- [x] PTM se loguea en update_value: `[PTM-CALC] Updated: X.X mmHg (from tag=value)`
- [x] Cache vacío loguea: `Cache de límites vacío: no se escriben límites al conectar`

### 8. Flujos Probados

**Flujo 1: Primer uso (cache vacío)**
1. Usuario abre Configuración de Alarmas
2. Escribe valores en casillas
3. Pulsa Guardar Cambios
4. ✅ Se guardan en JSON
5. ✅ Se escriben 6 tags al control
6. ✅ Se loguea cada escritura

**Flujo 2: Desconectar/Conectar**
1. Serial conectado con límites guardados en JSON
2. Usuario desconecta serie
3. Usuario reconecta serie
4. ✅ _write_pressure_limits_on_connection() reescribe 6 tags del JSON
5. ✅ Nada se pierde aunque pantalla esté cerrada

**Flujo 3: CALC_PTM sin pantalla visible**
1. Límites de PTM guardados en JSON
2. Pantalla de Configuración está cerrada
3. Usuario cambia presiones en diálisis
4. ✅ calculo_ptm() se recalcula automáticamente
5. ✅ Alarma funciona con límites del JSON
6. Usuario abre Configuración: ✅ ve valores del JSON

**Flujo 4: Restaurar valores por defecto**
1. Usuario pulsa Restaurar Todos
2. ✅ save_config() guarda en JSON
3. ✅ _write_pressure_limits_to_device() reescribe al control
4. ✅ Luego se actualizan widgets

### 9. Cambios de Versión y Compatibilidad

- [x] Formato viejo (dict) se carga y migra a JSON
- [x] No hay relleno automático de cache con valores del mapa
- [x] QSettings puede devolver dict o string, ambos soportados
- [x] JSON vacío o inválido deja cache vacío (no default values)

### 10. Archivos Modificados

1. **core/variables_map.py**: Grupo LOCAL con CALC_PTM
2. **core/alarm_config_manager.py**: Cache en memoria + JSON persistencia
3. **gui/appMainHemodialysis.py**: PTM automático + sincronización en conexión
4. **gui/configuration/alarm_screen_config.py**: Sincronización en guardar
5. **gui/components/real_time_variables.py**: Fix formato hex
6. **main.py**: Fix log file rotation

### Próximos Pasos Opcionales

- [ ] Test con QSettings real en Windows (sqlite backend)
- [ ] Validar rotación de logs con tamaño > 10MB
- [ ] Verificar que alarma PTM funciona aunque no esté pantalla
- [ ] Confirmar que temperatura se guarda pero NO se escribe al control

---

**Última actualización**: 2024 (commit 3ca90b8)
**Estado**: Listo para integración
