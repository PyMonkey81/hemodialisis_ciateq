# ANÁLISIS EXHAUSTIVO DE PUNTOS DE QUIEBRE CRÍTICOS
## main.py y gui/appMainHemodialysis.py

---

## 1. EXCEPCIONES NO MANEJADAS E INCOMPLETAS

### CRÍTICA: main.py (líneas 40-57) - Creación de directorios sin validación
```
LINEA: 47-57
ARCHIVO: main.py

for dir_parts in REQUIRED_DATA_DIRS:
    try:
        data_path = get_runtime_data_path(*dir_parts)
        data_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: No se pudo crear {dir_parts}: {e}", file=sys.stderr)
```

**PROBLEMA**: El bloque except() captura la excepción pero solo imprime en stderr sin registrar.
**RIESGO**: Si la creación falla y la ruta es crítica (logs/, var/log/), la aplicación no podrá escribir logs ni datos.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: Sistema de archivos corrupto, permisos insuficientes, disco lleno.
**FIX**: Registrar en logger y hacer failover a memoria si es necesario. Fallar ruidosamente si es path crítico.

---

### CRÍTICA: main.py (líneas 62-81) - Handler de logs sin validación
```
LINEA: 62-81
ARCHIVO: main.py

try:
    handler = RotatingFileHandler(...)
    # ... setup ...
except Exception as e:
    print(f"Error configurando logging: {e}", file=sys.stderr)
    handler = logging.StreamHandler()
    # ... fallback setup ...
```

**PROBLEMA**: Si logging falla, el programa continúa pero sin poder registrar errores críticos posteriores.
**RIESGO**: Errores silenciosos en operación; no hay auditoría de fallos médicos.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: Inicialización de logger falla por any reason → ningún error posterior se registra.
**FIX**: Assert que logging funciona antes de continuar. Fallar ruidosamente si setup=fallido.

---

### ALTA: main.py (líneas 92-111) - detect_screen_size() captura genérica
```
LINEA: 92-111
ARCHIVO: main.py

def detect_screen_size() -> tuple[int, int]:
    try:
        screen_instance = QGuiApplication.primaryScreen()
        if screen_instance is not None:
            geometry = screen_instance.availableGeometry()
            return geometry.width(), geometry.height()
    except Exception:
        pass
    return 1920, 1080
```

**PROBLEMA**: Excepto ANY pero retorna valor hardcoded sin log de qué falló.
**RIESGO**: Pantalla escalada incorrectamente si Qt no puede obtener geometría. UI rota.
**SEVERIDAD**: ALTA
**ESCENARIO**: Qt sin display, servidor headless, Xvfb mock → retorna 1920x1080 pero real es diferente.
**FIX**: Logger.warning() antes del return. Retornar tamaño detectado parcialmente.

---

### CRÍTICA: appMainHemodialysis.py (línea ~450) - Inicialización serie sin validate
```
LINEA: ~450
ARCHIVO: gui/appMainHemodialysis.py

self.serial_comm = SerialCommunication()
self.serial_comm.data_received.connect(self.update_value)
```

**PROBLEMA**: SerialCommunication() se instantia pero NO se valida si puertos están disponibles.
**RIESGO**: Dispositivo médico sin conexión → sin datos de sensores → alarmas nunca se actualizan.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: Puerto COM no existe, driver USB desconectado, permiso denegado.
**FIX**: Verificar puerto disponible. Si falla, mostrar ERROR CRÍTICO y entrar en modo demo/testing.

---

### ALTA: appMainHemodialysis.py (línea ~470) - BiozUreaController sin error check
```
LINEA: ~470
ARCHIVO: gui/appMainHemodialysis.py

self.bioz_urea_controller = BiozUreaController()
self.bioz_urea_controller.data_received.connect(self.update_value) 
self.bioz_urea_controller.start()
```

**PROBLEMA**: start() llamado sin validar si inicialización tuvo éxito.
**RIESGO**: Thread muere silenciosamente, Kt/V nunca se calcula, paciente no recibe terapia completa.
**SEVERIDAD**: ALTA
**ESCENARIO**: Puerto BioZ no disponible, inicialización Modbus falla.
**FIX**: Capturar excepción en start(). Mostrar WARNING en UI. Permitir continuar sin BioZ.

---

### MEDIA: appMainHemodialysis.py (línea ~540) - Carga de config JSON sin validación
```
LINEA: ~540
ARCHIVO: gui/appMainHemodialysis.py

self._load_therapy_config_json()
```

**PROBLEMA**: safe_json_load() puede retornar {} vacío sin indicar que archivo no existe o es inválido.
**RIESGO**: Terapia inicia sin configuración → valores por defecto potencialmente inseguros.
**SEVERIDAD**: MEDIA
**ESCENARIO**: archivo JSON corrupto, permisos lectura denegados.
**FIX**: Loguear si carga falla. Mergear con defaults explícitamente y avisar al usuario.

---

## 2. OPERACIONES DE I/O SIN VALIDACIÓN

### CRÍTICA: appMainHemodialysis.py - Acceso a atributos QWidget sin verificación
```
LINEA: 2699-2730 (multiple places)
ARCHIVO: gui/appMainHemodialysis.py

if hasattr(self.current_process_status, 'setStyleSheet'):
    self.current_process_status.setStyleSheet(...)
```

**PROBLEMA**: Múltiples accesos a QWidget properties sin null check.
**RIESGO**: Si widget no se inicializó (ej. setup_ui() falló parcialmente), crash con AttributeError.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: Excepto en setup_ui() que no se completa → atributo None → crash en update_value().
**FIX**: Validar todos los QWidget en __init__. Assert o logger.error() si None.

---

### ALTA: appMainHemodialysis.py (línea ~1500) - Acceso a dictionary sin validación
```
LINEA: 1500-1600
ARCHIVO: gui/appMainHemodialysis.py

qb = self.current_values.get("bloodFlowControlSetPoint")
if qb:
    lines.append(f"Qb: {qb} mL/min")

temp = self.current_values.get("dialyTempControlSetPoint")
if temp:
    lines.append(f"Temperatura: {temp}°C")
```

**PROBLEMA**: Se obtiene valor, se verifica truthiness, pero 0.0 es falsy → se omite.
**RIESGO**: Si valor es 0, línea no aparece en diálogo. Usuario no ve setpoint.
**SEVERIDAD**: ALTA
**ESCENARIO**: Setpoint configurado a 0 por error → no aparece en confirmación.
**FIX**: Cambiar `if qb:` a `if qb is not None:`. Validar tipos explícitamente.

---

### MEDIA: appMainHemodialysis.py (línea ~2395) - gauge.setValue() sin null check
```
LINEA: 2395-2407
ARCHIVO: gui/appMainHemodialysis.py

for tag, gauge in gauge_mapping.items():
    if gauge is not None:
        value = self.current_values.get(tag, 0.0)
        try:
            gauge.setValue(value)
        except Exception as e:
            logger.error(f"Error actualizando gauge {tag}: {e}")
```

**PROBLEMA**: gauge.setValue() capturada pero si falla repetidamente, logging se satura.
**RIESGO**: Log saturado con errores → información crítica oculta.
**SEVERIDAD**: MEDIA
**ESCENARIO**: gauge.setValue() falla 60 veces/min (master_timer). Log size explota.
**FIX**: Limitar logging. Usar contador de errores. Si 5+ fallos, disable gauge y log una sola vez.

---

## 3. INICIALIZACIONES FALLIDAS DE DEPENDENCIAS

### CRÍTICA: appMainHemodialysis.py (línea ~330-360) - Orden de inicialización frágil
```
LINEA: 330-360
ARCHIVO: gui/appMainHemodialysis.py

self.current_values = {}
# ... initialize current_values keys ...

self.bioz_urea_controller = BiozUreaController()
# ...
self.ktv_controller = KtvController(self)

self.ktv_controller.set_dependencies(
    main_window=self,
    bioz_urea_controller=self.bioz_urea_controller,
    ...
)
```

**PROBLEMA**: Si BiozUreaController() falla silenciosamente, ktv_controller recibe None.
**RIESGO**: KtvController.set_dependencies() no valida. Crash en primera llamada a bioz.send_command().
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: BiozUreaController constructor levanta excepción no capturada → program crash.
**FIX**: Wrap cada inicialización en try/except. Verify=not None. Fallar ruidosamente.

---

### ALTA: appMainHemodialysis.py (línea ~380) - SerialComm conexión diferida
```
LINEA: ~380
ARCHIVO: gui/appMainHemodialysis.py

self.serial_comm = SerialCommunication()
self.serial_comm.data_received.connect(self.update_value)
# No se valida si puerto abierto aquí
```

**PROBLEMA**: Conexión es lazy (se abre cuando se llama a send()). Si nunca se llama send(), nunca se abre.
**RIESGO**: Setpoints no se escriben. Máquina no recibe comandos. No hay feedback de error.
**SEVERIDAD**: ALTA
**ESCENARIO**: Primer send() falla silenciosamente. Usuario cree que setpoint se escribió.
**FIX**: Forzar apertura en __init__ de SerialComm. Validar puerto disponible immediatamente.

---

### MEDIA: appMainHemodialysis.py (línea ~470) - PatternConductivity sin estado check
```
LINEA: ~470
ARCHIVO: gui/appMainHemodialysis.py

self.pattern_sensor = PatternConductivity()
self.pattern_sensor.data_received.connect(self.on_pattern_data)
self.pattern_sensor.start()

self.mega_cond_sensor = MegaConductivitySensor()
self.mega_cond_sensor.data_received.connect(self.on_mega_cond_data)
self.mega_cond_sensor.start_reading()
```

**PROBLEMA**: Dos sensores de conductividad. Si uno falla, no hay indicación. Ambos escriben a current_values.
**RIESGO**: Race condition si ambos actualizan conductividad simultáneamente. Valores inconsistentes.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Ambos threads escriben conductividad sin lock → condividad fluctúa sin motivo físico.
**FIX**: Usar lock si ambos sensores activos. Preferir uno. Si ambos, validar consistencia.

---

## 4. ACCESO A ATRIBUTOS/DICCIONARIOS QUE PODRÍAN NO EXISTIR

### CRÍTICA: appMainHemodialysis.py (línea ~1100) - hardware_mapper puede ser None
```
LINEA: ~1100
ARCHIVO: gui/appMainHemodialysis.py

if hasattr(self, "hardware_mapper") and self.hardware_mapper is None:
    return

new_phase = self.hardware_mapper.get_phase(status_code, treatment_mode)
```

**PROBLEMA**: hasattr() retorna True, pero if self.hardware_mapper is None no valida after.
**RIESGO**: Si hardware_mapper es None, crash en get_phase().
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: hardware_mapper no se inicializa → crash en _update_header_during_filter_fill().
**FIX**: Cambiar lógica a `if not self.hardware_mapper: return` o inicializar siempre.

---

### ALTA: appMainHemodialysis.py (línea ~1540) - Acceso a diccionario sin None check
```
LINEA: 1540-1550
ARCHIVO: gui/appMainHemodialysis.py

therapy_h = int(self.current_values.get("heparineTherapyHours", 0) or 0)
therapy_m = int(self.current_values.get("heparineTherapyMinutes", 0) or 0)
```

**PROBLEMA**: `or 0` no maneja None correctamente. Si get() retorna None, `None or 0` = 0, ok.
Pero si retorna 0.0, `0.0 or 0` = 0, ok. Si retorna string "0", `"0" or 0` = "0", crash en int("0").
**RIESGO**: Conversion error si valor es string.
**SEVERIDAD**: ALTA
**ESCENARIO**: JSON load retorna "0" en lugar de número → int() falla.
**FIX**: Usar safe_int() (que ya existe en utilities).

---

### MEDIA: appMainHemodialysis.py (línea ~2470) - screen_stack widget access
```
LINEA: 2470
ARCHIVO: gui/appMainHemodialysis.py

if self.screen_stack.currentWidget() == self.maintenance_screen:
    self.timer_manager._update_maintenance_screen()
```

**PROBLEMA**: currentWidget() puede retornar None si screen_stack vacío.
**RIESGO**: Comparación None == self.maintenance_screen es False (ok), pero si se llama método en None, crash.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Screen stack no inicializado. currentWidget() = None.
**FIX**: Cambiar a `if self.screen_stack.currentWidget() is not None and ...`

---

## 5. OPERACIONES DE THREADING SIN SINCRONIZACIÓN

### ALTA: appMainHemodialysis.py (línea ~360-370) - Múltiples threads sin lock
```
LINEA: ~360-370
ARCHIVO: gui/appMainHemodialysis.py

self.bioz_urea_controller.data_received.connect(self.update_value) 
self.serial_comm.data_received.connect(self.update_value)
self.pattern_sensor.data_received.connect(self.on_pattern_data)
self.mega_cond_sensor.data_received.connect(self.on_mega_cond_data)
```

**PROBLEMA**: update_value() puede ser llamada simultáneamente desde múltiples threads.
current_values es dict (no thread-safe).
**RIESGO**: Race condition en update_value(). Valores corruptos.
**SEVERIDAD**: ALTA
**ESCENARIO**: BioZ y SerialComm actualizan current_values["dialyCondControlSetPoint"] al mismo tiempo.
**FIX**: Usar QMutex o lock en update_value(). O usar QThread.queuedConnection para serializar.

---

### MEDIA: appMainHemodialysis.py (línea ~2418) - Timer lock es boolean, no mutex
```
LINEA: 2418
ARCHIVO: gui/appMainHemodialysis.py

if self._timer_lock:
    return
self._timer_lock = True
try:
    # ... código ...
finally:
    self._timer_lock = False
```

**PROBLEMA**: Boolean lock no es atomic. Entre check y set, otro thread puede entrar.
**RIESGO**: Si master_timer se ejecuta muy rápido, ambos threads entran → reentrancia.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Dos ticks de master_timer solapan → _master_timer_tick() se ejecuta en paralelo.
**FIX**: Usar QMutex en lugar de boolean. O usar @functools.lru_cache(maxsize=1) para garantizar single execution.

---

### MEDIA: appMainHemodialysis.py (línea ~1230) - _start_treatment_locked boolean
```
LINEA: 1230
ARCHIVO: gui/appMainHemodialysis.py

if getattr(self, '_start_treatment_locked', False):
    return
self._start_treatment_locked = True
try:
    # ...
finally:
    self._start_treatment_locked = False
```

**PROBLEMA**: Mismo problema que _timer_lock. Boolean lock entre threads no es seguro.
**RIESGO**: start_treatment() puede ejecutarse 2 veces si usuario hace doble-click rápido.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Doble-click en "Iniciar Tratamiento". Ambos calls son simultáneos.
**FIX**: Usar QMutex o eliminar el lock si Qt ya lo maneja (signals son queued por defecto).

---

## 6. REFERENCIAS NULAS/NONE

### CRÍTICA: appMainHemodialysis.py (línea ~450) - Chaining de None
```
LINEA: ~450
ARCHIVO: gui/appMainHemodialysis.py

def __init__(self):
    # ...
    self.treatment_controller = TreatmentController(self)
    # No validar si TreatmentController() retorna None o falla
```

**PROBLEMA**: Si TreatmentController() falla, self.treatment_controller = None.
Luego en _master_timer_tick(), se llama self.treatment_controller.update_therapy_times() → AttributeError.
**RIESGO**: Crash en next master_timer tick.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: TreatmentController() constructor levanta excepción no manejada.
**FIX**: Wrap en try/except. Inicializar a None y validar before use.

---

### MEDIA: appMainHemodialysis.py (línea ~2300) - filter_fill_start_time puede ser None
```
LINEA: 2300
ARCHIVO: gui/appMainHemodialysis.py

if not self.filter_fill_waiting or self.filter_fill_start_time is None:
    return

elapsed = self.filter_fill_start_time.secsTo(QDateTime.currentDateTime())
```

**PROBLEMA**: Check es `self.filter_fill_start_time is None` pero en otra línea, se llama .secsTo() sin re-check.
**RIESGO**: Si entre check y uso, otro thread pone a None, crash.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Thread A chequea None=False. Thread B pone a None. Thread A llama secsTo() → crash.
**FIX**: Capturar en variable local. Validar una sola vez.

---

## 7. CONVERSIONES DE TIPO PELIGROSAS

### ALTA: appMainHemodialysis.py (línea ~1540) - float() sin validación
```
LINEA: 1540
ARCHIVO: gui/appMainHemodialysis.py

lines.append(f"UF: {float(uf_l_h):.2f} L/h")
```

**PROBLEMA**: uf_l_h puede ser None, string inválido, etc. float() lanzará excepción.
**RIESGO**: Si uf_l_h = None, crash con TypeError.
**SEVERIDAD**: ALTA
**ESCENARIO**: current_values["ultraFilterPumpSpeed"] no inicializado → None → float() crash.
**FIX**: Usar `safe_float(uf_l_h, 0.0)`.

---

### MEDIA: appMainHemodialysis.py (línea ~1500) - int() con None
```
LINEA: 1500
ARCHIVO: gui/appMainHemodialysis.py

therapy_h = int(self.current_values.get("heparineTherapyHours", 0) or 0)
```

**PROBLEMA**: Aunque tiene `or 0` fallback, si get() retorna string no-numérico, int() crash.
**RIESGO**: JSON parsing retorna "abc" → int("abc") → crash.
**SEVERIDAD**: MEDIA
**ESCENARIO**: JSON file corrupted, retorna string en lugar de número.
**FIX**: Usar try/except o safe_int(). Validar JSON schema en load.

---

### MEDIA: appMainHemodialysis.py (línea ~2295) - .secsTo() sin None check
```
LINEA: 2295
ARCHIVO: gui/appMainHemodialysis.py

elapsed = self.filter_fill_start_time.secsTo(QDateTime.currentDateTime())
if elapsed < self.MIN_FILTER_FILL_WAIT_SECONDS:
```

**PROBLEMA**: Si filter_fill_start_time es None, .secsTo() crash.
**RIESGO**: Race condition con thread que pone a None entre check y uso.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Véase sección 6 (referencias nulas).
**FIX**: Validar no-None antes de usar.

---

## 8. CICLOS INFINITOS POTENCIALES

### MEDIA: appMainHemodialysis.py (línea ~1396-1410) - Diálogo recursivo
```
LINEA: 1396-1410
ARCHIVO: gui/appMainHemodialysis.py

def show_first_dialog():
    confirmed = dialog.show_confirm(...)
    if not confirmed:
        QTimer.singleShot(100, show_first_dialog)  # <-- Recursión
        return
    show_second_dialog()
```

**PROBLEMA**: QTimer.singleShot() que llama a show_first_dialog() puede crear ciclo infinito.
Si usuario siempre cancela, se reintenta cada 100ms indefinidamente.
**RIESGO**: Stack overflow si reintento > 1000 veces. CPU 100%.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Usuario cancela el diálogo de "colocar filtro" 1000 veces.
**FIX**: Limitar reintentosm ej. max=5. Si usuario cancela 5 veces, fallar con error.

---

### MEDIA: appMainHemodialysis.py (línea ~2418) - master_timer puede reentradar
```
LINEA: 2418
ARCHIVO: gui/appMainHemodialysis.py

def _master_timer_tick(self):
    if self._timer_lock:
        return
    self._timer_lock = True
    try:
        # ... código que tarda MUCHO ...
    finally:
        self._timer_lock = False
```

**PROBLEMA**: Si código dentro tardarMore que interval (500ms), ticks se solapan.
Timer tick siguiente entra antes de que el anterior termine → _timer_lock quizá no haya sido puesto a False.
**RIESGO**: Condición de carrera. Race condition.
**SEVERIDAD**: MEDIA
**ESCENARIO**: _master_timer_tick() tarda 1000ms. Timer interval es 500ms. Ticks solapan.
**FIX**: Usar QTimer.stop() durante tick. O aumentar interval si tarda mucho.

---

## 9. PROBLEMAS DE ESTADO Y SINCRONIZACIÓN

### CRÍTICA: appMainHemodialysis.py (línea ~780) - Estados inconsistentes
```
LINEA: ~780
ARCHIVO: gui/appMainHemodialysis.py

def _sync_state_with_hardware(self):
    # Múltiples llamadas a set_phase() desde diferentes contextos
    self.state.set_phase(new_phase, reason)
    self.screen_state_manager.update_all_screens(new_phase)
```

**PROBLEMA**: set_phase() puede ser llamada desde:
- serial_comm (update_value)
- master_timer
- treatment_controller
- user UI click
Sin coordinación → inconsistencia de estado.
**RIESGO**: Máquina en RUNNING pero UI muestra IDLE. Terapia desincronizada.
**SEVERIDAD**: CRÍTICA
**ESCENARIO**: Serial recibe status=14 (RUNNING). Thread master_timer lo cambia a READY. UI muestra READY pero hardware está RUNNING.
**FIX**: State debe ser single source of truth. Todas las escritas deben ir a través de state_manager con locks.

---

### ALTA: appMainHemodialysis.py (línea ~1950) - heparin_auto_stop_latched puede no resetearse
```
LINEA: ~1950
ARCHIVO: gui/appMainHemodialysis.py

if elapsed_seconds >= auto_stop_seconds and not self._heparin_auto_stop_latched:
    # Enviar comando
    self._write_boolean_command(...)
    self._heparin_auto_stop_latched = True
```

**PROBLEMA**: Una vez que _heparin_auto_stop_latched = True, NUNCA se resetea si usuario pausa/reanuda.
**RIESGO**: Si usuario pausa y reanuda, heparina NO se reactiva.
**SEVERIDAD**: ALTA
**ESCENARIO**: Terapia 240min. Heparina configura para parar a los 210min. Usuario pausa a 200min. Reanuda. Heparina ya no se reactiva.
**FIX**: Resetear _heparin_auto_stop_latched cuando fase cambia a NO-RUNNING.

---

## 10. GESTIÓN DE RECURSOS Y LIMPIEZA

### MEDIA: appMainHemodialysis.py (línea ~3700) - __del__() sin validación
```
LINEA: ~3700
ARCHIVO: gui/appMainHemodialysis.py

def __del__(self):
    logger.error("[INFO] Destructor called ...")
    # Intentar parar threads
```

**PROBLEMA**: __del__() puede ser llamado en cualquier momento. Si logger ya fue destruído, crash.
**RIESGO**: Excepto durante cleanup. Aplicación crash no limpio.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Aplicación cierra. __del__() intenta loguear. Logger ya destruído.
**FIX**: No hacer logging en __del__(). Usar try/except. Mejor: implementar cleanup() explícito.

---

### MEDIA: appMainHemodialysis.py - CSV loggers sin cierre
```
LINEA: ~600 (initialization)
ARCHIVO: gui/appMainHemodialysis.py

self.treatment_logger = None
self.cleaning_logger = None
```

**PROBLEMA**: Si aplicación crash durante terapia, archivos CSV quedan abiertos.
**RIESGO**: Archivos corruptos. Datos perdidos.
**SEVERIDAD**: MEDIA
**ESCENARIO**: Puerto serie desconectado → crash → CSV no cerrado.
**FIX**: Implementar context manager o weakref callback para garantizar close().

---

## RESUMEN: TOP 5 CRÍTICAS

1. **CRÍTICA**: Inicialización serial sin validación (línea ~450, appMainHemodialysis.py)
2. **CRÍTICA**: hardware_mapper puede ser None (línea ~1100, appMainHemodialysis.py)
3. **CRÍTICA**: Estado desincronizado (múltiples threads escriben state sin locks)
4. **CRÍTICA**: Creación directorios logs sin failover (línea 47-57, main.py)
5. **CRÍTICA**: Inicialización KtvController sin validar BiozUreaController (línea ~330-360)

---

## RECOMENDACIONES INMEDIATAS

1. Agregar validación de estado al inicio de cada método crítico
2. Usar QMutex para acceso a current_values
3. Implementar early failover si puerto serial no abre
4. Validar todas las referencias a QWidget properties
5. Usar safe_int() y safe_float() en TODOS los casts
6. Loguear excepciones, nunca silenciarlas con `except Exception: pass`
7. Implementar health check thread que valida estado cada N segundos
8. Agregar assertions en __init__ para dependencias críticas
