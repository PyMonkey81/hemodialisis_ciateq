# PATRONES ESPECÍFICOS DE FALLO IDENTIFICADOS

---

## PATRÓN 1: Truthiness Check en lugar de None Check

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~1500: `if qb:` → Omite valor 0.0
- appMainHemodialysis.py línea ~1505: `if temp:` → Omite valor 0°C
- appMainHemodialysis.py línea ~1510: `if cond:` → Omite valor 0 mS/cm
- appMainHemodialysis.py línea ~1530: `if heparin_enabled != 0:` → Redundante

### Código problema:
```python
qb = self.current_values.get("bloodFlowControlSetPoint")
if qb:  # MALO: 0.0 es falsy
    lines.append(f"Qb: {qb} mL/min")

# CORRECTO:
qb = self.current_values.get("bloodFlowControlSetPoint")
if qb is not None:  # Permite 0.0
    lines.append(f"Qb: {qb} mL/min")
```

### Impacto:
- Setpoint con valor 0 no aparece en confirmación
- Usuario desconoce parámetro crítico
- Posible error terapéutico

### Fixes:
```python
# Opción 1: None check
if value is not None:
    # use value

# Opción 2: Type check
if isinstance(value, (int, float)):
    # use value

# Opción 3: Safe getter
safe_int(value, default=0)
safe_float(value, default=0.0)
```

---

## PATRÓN 2: Excepciones genéricas sin logging

### Ubicaciones problemáticas:
- main.py línea 47: `except Exception as e: print(...)`
- main.py línea 74: `except Exception as e: print(...)`
- main.py línea 99: `except Exception: pass`
- appMainHemodialysis.py ~500: `except Exception as e: logger.error(...)`

### Código problema:
```python
try:
    data_path = get_runtime_data_path(*dir_parts)
    data_path.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: No se pudo crear {dir_parts}: {e}", file=sys.stderr)
    # PROBLEMA: print() no va a logs. Imposible auditar.
```

### Impacto:
- Fallos silenciosos
- No hay traza de auditoría
- Diagnóstico imposible post-mortem
- Incumplimiento regulatorio (ISO/IEC 62304)

### Fixes:
```python
import logging
logger = logging.getLogger(__name__)

try:
    data_path = get_runtime_data_path(*dir_parts)
    data_path.mkdir(parents=True, exist_ok=True)
except PermissionError as e:
    logger.error(f"Permisos insuficientes en {dir_parts}: {e}")
    raise  # O implementar fallback seguro
except FileNotFoundError as e:
    logger.error(f"Ruta no existe {dir_parts}: {e}")
    raise
except Exception as e:
    logger.critical(f"Error inesperado creando {dir_parts}: {e}", exc_info=True)
    raise
```

---

## PATRÓN 3: Inicialización sin validación post-construcción

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~450: `self.serial_comm = SerialCommunication()`
- appMainHemodialysis.py línea ~470: `self.bioz_urea_controller = BiozUreaController()`
- appMainHemodialysis.py línea ~490: `self.pattern_sensor = PatternConductivity()`
- appMainHemodialysis.py línea ~495: `self.mega_cond_sensor = MegaConductivitySensor()`

### Código problema:
```python
self.serial_comm = SerialCommunication()
self.serial_comm.data_received.connect(self.update_value)
# PROBLEMA: No validar si puerto se abrió. Si falla, continúa como si nada.
```

### Impacto:
- Aplicación "funciona" pero sin datos
- Sensores no envían datos
- Alarmas nunca se actualizan
- Usuario no sabe que falta conectividad

### Escenario de fallo:
```
1. Usuario inicia aplicación
2. Puerto COM/USB no disponible
3. SerialCommunication() = OK (objeto creado)
4. Puerto no se abre (lazy init)
5. Aplicación muestra "CONECTADA" pero no recibe datos
6. Alarmas no funcionan
7. Terapia comienza sin lecturas de sensores
8. EVENTO ADVERSO
```

### Fixes:
```python
class SafeSerialInit:
    def __init__(self):
        self.serial_comm = None
        try:
            self.serial_comm = SerialCommunication()
            self.serial_comm.data_received.connect(self.update_value)
            
            # Validar apertura de puerto
            if not self.serial_comm.is_connected:
                raise RuntimeError("Puerto serial no se pudo abrir")
                
            logger.info("SerialCommunication inicializado OK")
        except Exception as e:
            logger.critical(f"Fallo crítico en SerialCommunication: {e}", exc_info=True)
            self.show_critical_error("Sin conexión con hardware")
            # Opción: modo demo/testing, o fallar ruidosamente
            raise  # Fallar durante __init__
```

---

## PATRÓN 4: Acceso a None sin guards

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~800: `self.hardware_mapper.get_phase()` - sin check
- appMainHemodialysis.py línea ~2695: `self.current_process_status.setStyleSheet()` - sin check
- appMainHemodialysis.py línea ~2300: `self.filter_fill_start_time.secsTo()` - sin check

### Código problema:
```python
if hasattr(self, 'hardware_mapper') and self.hardware_mapper:
    new_phase = self.hardware_mapper.get_phase(status_code, treatment_mode)
    # PROBLEMA: hasattr() check, pero en la línea siguiente se asume no-None
    # Entre check y uso, otro thread puede poner a None (race condition)
```

### Impacto:
- AttributeError en acceso
- Crash con AttributeError/TypeError
- Intermitente (race condition)

### Escenario de fallo:
```
Thread 1:
  if hasattr(self, 'hardware_mapper') and self.hardware_mapper:
    <context switch>

Thread 2:
  self.hardware_mapper = None  # Reset

Thread 1:
  new_phase = self.hardware_mapper.get_phase()  # AttributeError
```

### Fixes:
```python
# Opción 1: Capturar en variable local
hardware_mapper = self.hardware_mapper
if hardware_mapper is not None:
    new_phase = hardware_mapper.get_phase(status_code, treatment_mode)

# Opción 2: Try/except
try:
    new_phase = self.hardware_mapper.get_phase(status_code, treatment_mode)
except (AttributeError, TypeError) as e:
    logger.error(f"hardware_mapper error: {e}")
    return  # Abort operation

# Opción 3: Garantizar inicialización
def __init__(self):
    self.hardware_mapper = HardwareStateMapper()
    assert self.hardware_mapper is not None  # Fail early if init failed
```

---

## PATRÓN 5: Boolean locks sin atomicidad

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~405: `self._timer_lock = False`
- appMainHemodialysis.py línea ~1230: `self._start_treatment_locked = False`

### Código problema:
```python
def _master_timer_tick(self):
    if self._timer_lock:      # READ
        return
    self._timer_lock = True    # WRITE
    try:
        # 100ms de código
    finally:
        self._timer_lock = False
```

### Impacto:
- Entre READ y WRITE, otro thread puede entrar
- Reentrancia de _master_timer_tick()
- Valores corruptos si loggers se escriben 2x simultáneamente

### Escenario de fallo:
```
Master Timer interval = 500ms
Code en _master_timer_tick = 1200ms (lento)

t=0: Tick 1 entra, lee _timer_lock=False, no entra (ok)
t=0: Tick 1 pone _timer_lock=True
t=500: Tick 2 entra, lee _timer_lock=True... espera, no: devuelve (ok con bool)
t=1200: Tick 1 termina, pone _timer_lock=False
t=1500: Tick 3 entra normalmente (ok)

PERO si otro thread cambia _timer_lock entre líneas:
t=0: Tick 1 lee _timer_lock=False
t=0.001: Tick 2 lee _timer_lock=False (!)
t=0.002: Tick 1 pone _timer_lock=True
t=0.003: Tick 2 pone _timer_lock=True
REENTRANCIA: ambos ejecutan código
```

### Fixes:
```python
from threading import Lock

class SafeTimer:
    def __init__(self):
        self._timer_lock = Lock()
    
    def _master_timer_tick(self):
        acquired = self._timer_lock.acquire(blocking=False)
        if not acquired:
            return  # Already running
        
        try:
            # ... código ...
        finally:
            self._timer_lock.release()

# O con QMutex:
from PySide6.QtCore import QMutex

class SafeTimerQt:
    def __init__(self):
        self._timer_lock = QMutex()
    
    def _master_timer_tick(self):
        if not self._timer_lock.tryLock():
            return
        
        try:
            # ... código ...
        finally:
            self._timer_lock.unlock()
```

---

## PATRÓN 6: Acceso a diccionarios sin tipos seguros

### Ubicaciones problemáticas:
- appMainHemodialysis.py ~1500: `int(self.current_values.get(...) or 0)`
- appMainHemodialysis.py ~1510: `float(uf_l_h)`
- appMainHemodialysis.py ~2710: `safe_int(config.get("interval_min", 15), 15)`

### Código problema:
```python
therapy_h = int(self.current_values.get("heparineTherapyHours", 0) or 0)
# Si get() retorna:
# - None: (None or 0) = 0, int(0) = 0 ✓
# - 0.0: (0.0 or 0) = 0, int(0) = 0 ✓
# - "abc": ("abc" or 0) = "abc", int("abc") = ERROR ✗
# - True: (True or 0) = True, int(True) = 1 ✓ (pero incorrecto tipo)

lines.append(f"UF: {float(uf_l_h):.2f} L/h")
# Si uf_l_h es None: float(None) = ERROR ✗
```

### Impacto:
- ValueError si valor es string inválido
- TypeError si valor es None
- Aplicación crash durante confirmación de terapia

### Escenario de fallo:
```
1. JSON config corrupted
2. Parse retorna {"ultraFilterPumpSpeed": "ERROR"} instead of 0.5
3. Línea float(uf_l_h) entra con "ERROR"
4. float("ERROR") raises ValueError
5. Excepción no capturada
6. Aplicación crash
```

### Fixes:
```python
# Ya existe safe_int, safe_float en utilities

from utilities.platform_runtime import safe_int, safe_float

therapy_h = safe_int(self.current_values.get("heparineTherapyHours"), 0)
therapy_m = safe_int(self.current_values.get("heparineTherapyMinutes"), 0)

uf_l_h = safe_float(self.current_values.get("ultraFilterPumpSpeed"), 0.0)
lines.append(f"UF: {uf_l_h:.2f} L/h")
```

---

## PATRÓN 7: Ciclos infinitos con QTimer.singleShot

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~1396-1410: Diálogo de filtro recursivo

### Código problema:
```python
def show_first_dialog():
    confirmed = dialog.show_confirm(...)
    if not confirmed:
        QTimer.singleShot(100, show_first_dialog)  # <-- RECURSIÓN
        return
    show_second_dialog()
```

### Impacto:
- Si usuario cancela indefinidamente, stack se llena
- CPU 100% de reintentosm
- Memoria crece con cada scheduledm timer
- Aplicación lenta/crash eventual

### Escenario de fallo:
```
Usuario olvida colocar filtro.
Usuario cancela diálogo 1000 veces en 100 segundos.
Stack profundidad = 1000 (limit típico 1000-10000)
Stack overflow → Segmentation fault
```

### Fixes:
```python
def show_first_dialog_with_limit(max_attempts=5, attempt=0):
    if attempt >= max_attempts:
        logger.error("Usuario canceló llenado de filtro después de 5 intentos")
        show_error_message("Llenado de filtro cancelado por usuario")
        return False
    
    confirmed = dialog.show_confirm(...)
    if not confirmed:
        QTimer.singleShot(100, lambda: show_first_dialog_with_limit(max_attempts, attempt + 1))
        return
    
    show_second_dialog()
    return True
```

---

## PATRÓN 8: Estado inconsistente entre threads

### Ubicaciones problemáticas:
- appMainHemodialysis.py línea ~1950: `_heparin_auto_stop_latched` puede no resetearse

### Código problema:
```python
def _update_heparin_auto_stop_timer(self):
    if elapsed_seconds >= auto_stop_seconds and not self._heparin_auto_stop_latched:
        self._write_boolean_command("heparineInfusionEnable", False)
        self._heparin_auto_stop_latched = True
        # PROBLEMA: Una vez True, NUNCA se resetea si usuario pausa/reanuda
```

### Impacto:
- Heparina se detiene pero no se reactiva en reanudación
- Paciente pierde protección anticoagulante
- Evento adverso: coágulo en máquina

### Escenario de fallo:
```
1. Terapia 240 min con heparina hasta min 210
2. Usuario pausa en min 200
3. Heparina aún activa (correcto)
4. Usuario reanuda en min 205
5. System ve elapsed=205, auto_stop=210, pero _heparin_auto_stop_latched=True
6. NO detiene heparina en min 210
7. Heparina continúa infundiéndose
8. EVENTO ADVERSO: sobredosis heparina
```

### Fixes:
```python
def _on_treatment_paused(self):
    """Pausar y RESETEAR la bandera de heparina"""
    logger.info("Tratamiento PAUSADO")
    self.is_treatment_running = False
    self._heparin_auto_stop_latched = False  # <-- AGREGAR
    self.ktv_controller.pause_measurement()

def _on_treatment_resumed(self):
    """Reanudar sin resetear (la bandera se controla en running)"""
    logger.info("Tratamiento REANUDADO")
    self.is_treatment_running = True
    self._heparin_auto_stop_latched = False  # <-- O acá también por seguridad
    self.ktv_controller.resume_measurement()

def _on_treatment_finished(self):
    """Finalizar y resetear"""
    logger.info("Tratamiento FINALIZADO")
    self.is_treatment_running = False
    self._heparin_auto_stop_latched = False  # <-- RESET
```

---

## RECOMENDACIONES POR PRIORIDAD

### INMEDIATO (hoy):
1. Usar safe_int/safe_float en todas las conversiones
2. Cambiar `if value:` a `if value is not None:`
3. Agregar logger.error() en todos los except genéricos
4. Reemplazar boolean locks con QMutex

### CORTO PLAZO (1-2 días):
1. Validar puerto serial al inicio
2. Agregar health check de dependencias
3. Implementar estado único/sincronizado con locks
4. Resetear banderas de estado en transiciones

### LARGO PLAZO (1-2 semanas):
1. Tests unitarios para cada patrón
2. Code review automático (pylint/flake8/mypy)
3. Type hints en todas las funciones
4. Documentación de invariantes de estado
