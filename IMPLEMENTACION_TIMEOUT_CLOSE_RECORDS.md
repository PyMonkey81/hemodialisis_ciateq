# Implementación: Cierre de Registros en Timeout de Terapia

## Resumen Ejecutivo

Cuando el reloj de terapia llega a cero en bypass (estado 14), la aplicación ahora:
1. Pausa la terapia UNA SOLA VEZ (estado 15 - PAUSED)
2. Cierra los registros de terapia inmediatamente: KTV, sesión y loggers
3. La máquina permanece en pausa; no detiene cebado ni limpia pantalla KTV
4. Evita guardar reportes duplicados cuando el hardware transiciona a IDLE

## Cambios Realizados

### 1. `core/treatment_controller.py`

#### Nuevas banderas en `__init__`:
```python
# Bandera para evitar cerrar registros dos veces en timeout
self.therapy_records_closed = False
```

#### Método nuevo: `close_therapy_records_on_timeout()`

Ejecutado cuando el reloj llega a cero, en el orden especificado:

1. **Toma tiempo transcurrido** antes de cualquier limpieza
   - Usa `self.get_elapsed_seconds()`
   
2. **Finaliza dosis entregada y guarda reporte Kt/V**
   - `ktv_controller.finalize_delivered_dose()`
   - `KTVScreen.save_final_report()`
   
3. **Aborta medición en curso** (SIN `reset_screen_data`)
   - `ktv_controller.abort("Terapia cerrada por tiempo")`
   - La pantalla conserva el último Kt/V
   
4. **Registra sesión de tratamiento**
   - `register_treatment_session()`
   - Deja `current_treatment_start` en `None`
   
5. **Cierra treatment_logger**
   - `treatment_logger.close()`
   - Lo deja en `None`
   - **NO toca** el logger de limpieza
   
6. **Guarda NibpPressureHistory** si tiene método
   - Verifica si existe método `save()`
   - Si no existe, se queda en memoria
   - Se limpia automáticamente al iniciar próxima terapia
   
7. **TreatmentPhase NO cambia**
   - Hardware permanece en PAUSED (estado 15)

**Protección:**
- Bandera `therapy_records_closed` evita ejecución duplicada
- Registra cambios en logs

#### Cambios en `prepare_new_treatment_session()`:
```python
self.therapy_records_closed = False  # Permitir nuevo cierre en próxima terapia
```

#### Cambios en `start_treatment()`:
```python
# Si registros ya fueron cerrados por timeout, NO enviar dialyModeOperationStart
if not self.therapy_records_closed:
    self.main._write_boolean_command("dialyModeOperationStart", True)
```
- Cuando se reanuda después de timeout, la pausa queda para maniobras
- Nueva sesión comienza solo después de que hardware salga de pausa

#### Cambios en `update_therapy_times()`:
```python
if not self.bypass_pause_sent:
    logger.info("Tiempo de terapia completado - Pausando en bypass")
    self.bypass_pause_sent = True
    self.therapy_finished_by_time = True
    self.pause_treatment()
    # Cerrar registros de terapia UNA SOLA VEZ
    self.close_therapy_records_on_timeout()
```

#### Cambios en `stop_therapy_timer()`:
```python
# NO guardar otro reporte vacío si ya se cerró por timeout
if not self.therapy_records_closed:
    self.main.KTVScreen.save_final_report()
```

#### Cambios en `end_therapy()`:
```python
# Limpiar banderas
self.therapy_finished_by_time = False
self.bypass_pause_sent = False
self.therapy_records_closed = False  # Permitir nuevo cierre si se reinicia
```

---

### 2. `gui/appMainHemodialysis.py`

#### Cambios en transición a IDLE (línea ~3330):

```python
# === REGISTRO DE HISTORIAL AL FINALIZAR TRATAMIENTO ===
if new_phase == TreatmentPhase.IDLE and old_phase in (...):
    logger.info("Hardware confirmó fin de tratamiento → Registrando historial")
    
    treatment_controller = getattr(self, 'treatment_controller', None)
    # Solo registrar si registros no fueron ya cerrados por timeout
    if treatment_controller and not treatment_controller.therapy_records_closed:
        if hasattr(self, 'register_treatment_session'):
            self.register_treatment_session()
            logger.debug("Historial de tratamiento registrado")
    else:
        logger.debug("Saltando registro: registros ya cerrados por timeout")
    
    # Cerrar logger solo si no fue ya cerrado por timeout
    if treatment_controller and not treatment_controller.therapy_records_closed:
        if hasattr(self, 'treatment_logger') and self.treatment_logger:
            self.treatment_logger.close()
            self.treatment_logger = None
    
    if treatment_controller is not None:
        treatment_controller.stop_therapy_timer()
        logger.debug("Timer de terapia detenido tras transición a IDLE")
```

**Lógica:**
- Si `therapy_records_closed` es verdadera, salta el registro y cierre de logger
- Siempre llama a `stop_therapy_timer()` (que a su vez verifica la bandera)
- Evita guardar reportes duplicados

---

## Comportamiento del Sistema

### Escenario 1: Timeout en Bypass (Estado 14)
1. `update_therapy_times()` detecta `remaining <= 0` en RUNNING
2. Llama a `pause_treatment()` → estado pasa a PAUSED (15)
3. Llama a `close_therapy_records_on_timeout()` → guarda KTV, sesión, cierra loggers
4. `therapy_records_closed = True`
5. Pantalla muestra "TERAPIA FINALIZADA" y conserva último Kt/V
6. Hardware sigue en pausa; cebado y bomba siguen funcionando

### Escenario 2: Reanudación después de Timeout
1. Usuario presiona "Reanudar"
2. `start_treatment()` NO envía `dialyModeOperationStart` porque `therapy_records_closed = True`
3. La pausa permanece para maniobras clínicas
4. No se abre nuevo CSV ni se crean nuevos registros

### Escenario 3: "Finalizar Terapia" (End)
1. `end_therapy()` apaga terapia, cebado y flujo
2. Limpia `therapy_finished_by_time`, `bypass_pause_sent`, `therapy_records_closed`
3. Permite nueva sesión tras salir de pausa

### Escenario 4: Hardware a IDLE después de Timeout
1. Si `therapy_records_closed = True`, salta registro en IDLE
2. `stop_therapy_timer()` NO guarda otro reporte KTV vacío
3. No duplica sesión de tratamiento

---

## Protecciones Implementadas

| Situación | Protección |
|-----------|-----------|
| Doble cierre por timeout | `therapy_records_closed` bandera |
| Reporte KTV duplicado en IDLE | Verifica bandera en IDLE |
| Sesión registrada dos veces | Verifica bandera en IDLE |
| Logger cerrado dos veces | Verifica bandera en IDLE |
| Reanudar abre nueva sesión | NO envía `dialyModeOperationStart` si bandera es verdadera |
| Pantalla KTV se borra | No llama a `reset_screen_data()` en abort por timeout |

---

## Validación Realizada

✅ Sintaxis Python verificada (`py_compile`)
✅ Lógica de banderas coherente
✅ Protecciones contra duplicados activas
✅ Logs informativos en cada paso
✅ Hardware permanece en pausa

---

## Notas de Integración

1. **NibpPressureHistory**: Sin método de guardado actualmente
   - Se queda en memoria durante pausa
   - Se limpia automáticamente al siguiente `prepare_new_treatment_session()`
   - Código preparado para futuros métodos de persistencia

2. **Pantalla KTV**: Conserva último valor
   - `reset_screen_data()` NO se llama en timeout
   - Usuario ve el Kt/V final mientras está en pausa
   - Se limpia al iniciar nueva terapia

3. **Logs de Limpieza**: NO se cierran
   - Solo se cierra `treatment_logger`
   - Logger de limpieza sigue operativo en pausa

