# Corrección: Leer SOLO del Cache, No del Mapa

**Problema**: `_write_pressure_limits_on_connection()` usaba `get_limits()` que devolvía valores del mapa (-300, 600, -100, 500, -100, 1000) cuando la fila no estaba guardada. Esto causaba que se enviaran esos valores al dispositivo sin intención.

**Solución**: 
1. Leer SOLO del `_limits_cache` directamente
2. Si una fila no está en cache, NO escribir ese tag
3. En `save_configuration()`, si PTM no está en pantalla, no enviar PTM

---

## Cambio 1: `_write_pressure_limits_on_connection()`

**Antes** (❌ Incorrecto):
```python
# Usaba get_limits() que devolvía mapa si no estaba guardado
art_min, art_max = self.config_manager.get_limits("bloodArteryPressureData")  # ← Devuelve -300, 600
ven_min, ven_max = self.config_manager.get_limits("bloodVenousPressureData")  # ← Devuelve -100, 500
ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")                 # ← Devuelve -100, 1000
```

**Ahora** (✅ Correcto):
```python
cache = self.config_manager._limits_cache

# Solo arterial si está guardada
if "bloodArteryPressureData" in cache:
    art_min, art_max = cache["bloodArteryPressureData"]
    # escribir arterial

# Solo venosa si está guardada
if "bloodVenousPressureData" in cache:
    ven_min, ven_max = cache["bloodVenousPressureData"]
    # escribir venosa

# Solo PTM si está guardada
if "CALC_PTM" in cache:
    ptm_min, ptm_max = cache["CALC_PTM"]
    # escribir PTM
```

**Ventaja**: Solo escribe lo que fue guardado explícitamente. Nunca envia valores por defecto del mapa.

---

## Cambio 2: `save_configuration()`

**Antes** (Ambiguo):
```python
# PTM: si está en pantalla, leer de widget; si no, leer de get_limits
if "CALC_PTM" in self.inputs:
    ptm_min = float(self.inputs["CALC_PTM"]['min'].text())
    ptm_max = float(self.inputs["CALC_PTM"]['max'].text())
else:
    ptm_min, ptm_max = self.config_manager.get_limits("CALC_PTM")  # ← Devuelve -100, 1000

self.write_setpoint_callback(art_min, art_max, ven_min, ven_max, ptm_min, ptm_max)
```

**Ahora** (Claro):
```python
# PTM: si está en pantalla, leer de widget; si no, no escribir
if "CALC_PTM" in self.inputs:
    ptm_min = float(self.inputs["CALC_PTM"]['min'].text())
    ptm_max = float(self.inputs["CALC_PTM"]['max'].text())
else:
    ptm_min = 0
    ptm_max = 0  # ← Los 0 se ignoran

self.write_setpoint_callback(art_min, art_max, ven_min, ven_max, ptm_min, ptm_max)
```

**Ventaja**: Si PTM no está en pantalla, se envia 0 (que se ignora en `_emit_pressure_alarm_limits`).

---

## Cómo `_emit_pressure_alarm_limits()` Usa los Parámetros

```python
def _emit_pressure_alarm_limits(self, art_min, art_max, ven_min, ven_max, ptm_min, ptm_max):
    pares = (
        ("artPresCircAlarmLoLimData", art_min),   # Escribe si art_min != 0
        ("artPresCircAlarmHiLimData", art_max),   # Escribe si art_max != 0
        ("venPresCircAlarmLoLimData", ven_min),   # Escribe si ven_min != 0
        ("venPresCircAlarmHiLimData", ven_max),   # Escribe si ven_max != 0
        ("membPressAlarmLoLimData", ptm_min),     # Escribe si ptm_min != 0
        ("membPressAlarmHiLimData", ptm_max),     # Escribe si ptm_max != 0
    )
    for tag, value in pares:
        if value != 0:  # ← Los 0 no se escriben
            self.serial_comm.write_double(...)
```

---

## Ejemplo Práctico

**Caso**: Usuario edita en Configuración de Alarmas:
- Arterial: -20, 200
- Venosa: -80, 200
- PTM: (no está en pantalla)

**Presiona Guardar Cambios:**

```
1. save_configuration():
   art_min = -20, art_max = 200
   ven_min = -80, ven_max = 200
   ptm_min = 0, ptm_max = 0 (porque no está en pantalla)
   
2. Llama: _emit_pressure_alarm_limits(-20, 200, -80, 200, 0, 0)

3. _emit_pressure_alarm_limits() itera sobre 6 tags:
   - artPresCircAlarmLoLimData = -20 ← Escribe (!=0)
   - artPresCircAlarmHiLimData = 200 ← Escribe (!=0)
   - venPresCircAlarmLoLimData = -80 ← Escribe (!=0)
   - venPresCircAlarmHiLimData = 200 ← Escribe (!=0)
   - membPressAlarmLoLimData = 0 ← NO escribe (=0)
   - membPressAlarmHiLimData = 0 ← NO escribe (=0)

4. Terminal muestra:
   ESCRIBO alarma artPresCircAlarmLoLimData grupo 0x6 id 7 = -20
   ESCRIBO alarma artPresCircAlarmHiLimData grupo 0x6 id 6 = 200
   ESCRIBO alarma venPresCircAlarmLoLimData grupo 0x6 id 9 = -80
   ESCRIBO alarma venPresCircAlarmHiLimData grupo 0x6 id 8 = 200

5. Simulador muestra:
   WRITE DOUBLE → Grupo 0x06 | ID 7 = -20
   WRITE DOUBLE → Grupo 0x06 | ID 6 = 200
   WRITE DOUBLE → Grupo 0x06 | ID 9 = -80
   WRITE DOUBLE → Grupo 0x06 | ID 8 = 200
```

---

## Flujo al Reconectar Serial

**Caso**: Usuario reconecta serie (cache tiene arterial y venosa, pero no PTM)

```
1. update_connection_status(True)

2. _write_pressure_limits_on_connection():
   cache = {
       "bloodArteryPressureData": (-20, 200),
       "bloodVenousPressureData": (-80, 200),
       # CALC_PTM no está
   }
   
3. Lee del cache:
   - "bloodArteryPressureData" en cache? SÍ → escribe
   - "bloodVenousPressureData" en cache? SÍ → escribe
   - "CALC_PTM" en cache? NO → no escribe

4. Terminal:
   ESCRIBO alarma artPresCircAlarmLoLimData grupo 0x6 id 7 = -20
   ESCRIBO alarma artPresCircAlarmHiLimData grupo 0x6 id 6 = 200
   ESCRIBO alarma venPresCircAlarmLoLimData grupo 0x6 id 9 = -80
   ESCRIBO alarma venPresCircAlarmHiLimData grupo 0x6 id 8 = 200
   (Sin PTM porque no está en cache)
```

---

## Caso: Serial Desconectado

**Cuando presionas Guardar Cambios y serial NO está conectado:**

```
1. save_configuration() lee valores
2. Llama: _emit_pressure_alarm_limits(...)
3. _emit_pressure_alarm_limits() verifica:
   if not self.serial_comm or not self.serial_comm.is_connected:
       logger.warning("ALARMAS NO ENVIADAS: serial del control desconectado")
       return

4. Terminal muestra:
   ALARMAS NO ENVIADAS: serial del control desconectado

5. JSON ya fue guardado en PASO 3, así que no hay pérdida de datos
```

---

## Commits

```
e04f666 fix: Leer solo del cache en _write_pressure_limits_on_connection, no usar get_limits
```

---

**Estado**: ✅ **CORREGIDO**

Ahora:
- ✅ No se envían valores del mapa por defecto
- ✅ Solo se escribe lo que está guardado en cache
- ✅ PTM se omite si no está en pantalla y no está guardado
- ✅ Temperatura NO se escribe (no tiene tags)
