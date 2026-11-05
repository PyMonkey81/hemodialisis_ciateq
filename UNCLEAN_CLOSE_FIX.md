# ✅ FIX: Detección de Cierre No Limpio y Detención de Terapia/Limpieza

## Problema

Si la aplicación se muere o se cierra de forma abrupta con terapia o limpieza en progreso:
- Al reiniciar, se engancha automáticamente a la terapia/limpieza que sigue en el controlador
- No hay forma de detenerla
- El usuario debe forzar apagado o usar hardware para parar

## Solución

Marcar cierre limpio al cerrar normalmente. Al arrancar:
- Si existe marca: borrarla (cierre limpio previo)
- Si NO existe marca: hay cierre abrupto → detener terapia/limpieza según estado

---

## Implementación

### 1. Marcar Cierre Limpio en closeEvent

```python
def closeEvent(self, event):
    # ... cierre normal ...
    
    # Crear marca de cierre limpio
    clean_close_path = get_runtime_data_path("var", "log", "cierre_limpio")
    with open(clean_close_path, "w") as f:
        f.write("")
    
    event.accept()
    QApplication.quit()
```

**Ubicación:** `gui/appMainHemodialysis.py:4045-4056`

### 2. Detectar Cierre No Limpio al Arrancar

Nuevo método `_check_and_handle_unclean_close()`:

```python
def _check_and_handle_unclean_close(self):
    """Ejecuta una sola vez al obtener primingProcessStatus"""
    if self._checked_unclean_close:
        return
    self._checked_unclean_close = True
    
    # 1. Buscar marca de cierre limpio
    clean_close_path = get_runtime_data_path("var", "log", "cierre_limpio")
    if os.path.exists(clean_close_path):
        os.remove(clean_close_path)  # Borrar marca
        return  # No hacer nada más
    
    # 2. No hay marca: es cierre no limpio
    priming_status = int(self.current_values.get("primingProcessStatus", 0))
    treatment_mode = int(self.current_values.get("treatmentModeSelection", 0))
    
    # 3. Decidir si detener según estado
    if priming_status in (14, 15) and treatment_mode != 3:
        # Terapia en progreso
        self.treatment_controller.stop_treatment()
        should_stop = True
    
    elif treatment_mode == 3 and priming_status == 6:
        # Limpieza en progreso
        self._write_setpoint("dialyStartDialysisButt", 0.0)
        self._write_setpoint("dialyStopDialysisButt", 1.0)
        should_stop = True
    
    else:
        # Estados 1, 2-13, 16: no hacer nada
        should_stop = False
    
    # 4. Mostrar mensaje si se detuvo algo
    if should_stop:
        msg = "La aplicación se cerró de forma inesperada. El proceso en curso se detuvo. Hay que iniciarlo de nuevo."
        self.show_operator_message(msg)
```

**Ubicación:** `gui/appMainHemodialysis.py:4059-4113`

### 3. Llamar una Sola Vez en update_value

Se llama desde `update_value()` cuando llega `primingProcessStatus`:

```python
if tag == "primingProcessStatus":
    # Verificar cierre no limpio solo una vez
    self._check_and_handle_unclean_close()
    # ... resto de la lógica ...
```

**Ubicación:** `gui/appMainHemodialysis.py:2927-2928`

---

## Flujo de Ejecución

### Cierre Normal

```
Usuario cierra la app
    ↓
closeEvent()
    ├─ end_dialysis_session()
    ├─ shutdown()
    ├─ Crear archivo "cierre_limpio" ✓
    └─ QApplication.quit()
```

### Arranque Después de Cierre Normal

```
App inicia
    ↓
SerialCommunication abre puerto
    ↓
Recibe primingProcessStatus
    ↓
update_value() → _check_and_handle_unclean_close()
    ├─ Detecta archivo "cierre_limpio" ✓
    ├─ Borra archivo
    └─ Retorna sin hacer nada ✓
```

### Arranque Después de Cierre Abrupto (Terapia en Estado 14)

```
App muere con terapia en progreso
    ↓
No se crea archivo "cierre_limpio" ✗
    ↓
App reinicia
    ↓
Recibe primingProcessStatus = 14
    ↓
update_value() → _check_and_handle_unclean_close()
    ├─ No detecta archivo ✗
    ├─ Verifica estado:
    │   ├─ priming_status = 14
    │   ├─ treatment_mode = 0 (Hemodiálisis, no 3)
    │   └─ Condición cumplida: SÍ DETENER
    ├─ Llama treatment_controller.stop_treatment() ✓
    ├─ Muestra mensaje al usuario ✓
    └─ _checked_unclean_close = True (no vuelve a hacer esto)
```

### Arranque Después de Cierre Abrupto (Limpieza)

```
App muere con limpieza en progreso
    ↓
No se crea archivo "cierre_limpio" ✗
    ↓
App reinicia
    ↓
Recibe primingProcessStatus = 6, treatmentModeSelection = 3
    ↓
update_value() → _check_and_handle_unclean_close()
    ├─ No detecta archivo ✗
    ├─ Verifica estado:
    │   ├─ priming_status = 6
    │   ├─ treatment_mode = 3
    │   └─ Condición cumplida: SÍ DETENER
    ├─ Envía dialyStartDialysisButt = 0.0
    ├─ Envía dialyStopDialysisButt = 1.0
    ├─ Muestra mensaje al usuario ✓
    └─ _checked_unclean_close = True (no vuelve a hacer esto)
```

---

## Decisión de Parada Según Estado

| priming_ProcessStatus | treatmentModeSelection | Acción |
|------------------------|----------------------|--------|
| 14, 15 | 0 (Hemodiálisis) | ✅ Detener terapia |
| 14, 15 | 1 (Hemodiafiltración) | ✅ Detener terapia |
| 14, 15 | 2 (Ultrafiltración) | ✅ Detener terapia |
| 14, 15 | 3 (Limpieza) | ❌ No parar (terapia no está en progreso) |
| 6 | 3 (Limpieza) | ✅ Detener limpieza |
| 6 | 0, 1, 2 | ❌ No parar |
| 1, 2-5, 7-13, 16 | Cualquiera | ❌ No parar (estado ocioso/intermedio) |

---

## Tests Sin Hardware

**Archivo:** `tests/test_unclean_close_detection.py`

### Clases de Tests

1. **TestUncleanCloseDetection** (3 tests)
   - Crear archivo de marca
   - Detectar y borrar marca
   - No existe marca = cierre abrupto

2. **TestUncleanCloseHandling** (10 tests)
   - Estado 14 + modo != 3 → SÍ parar
   - Estado 15 + modo != 3 → SÍ parar
   - Estado 14 + modo 3 → NO parar (no cumple condición)
   - Estado 6 + modo 3 → SÍ parar
   - Estado 1, 2, 13, 16 → NO parar
   - Estado 6 + modo 0 → NO parar
   - Estado 7 + modo 3 → NO parar

3. **TestUncleanCloseFlow** (4 tests)
   - Flujo cierre limpio: marca + arranque = no parar
   - Flujo cierre abrupto (terapia): sin marca + estado 14 = SÍ parar
   - Flujo cierre abrupto (limpieza): sin marca + estado 6 + modo 3 = SÍ parar
   - Flujo cierre abrupto (ocioso): sin marca + estado 1 = NO parar

### Resultados

```
Ran 17 tests in 0.014s
OK ✅
```

---

## Archivos Modificados

### `gui/appMainHemodialysis.py`
- Línea ~53: Importar `get_runtime_data_path`
- Línea ~287: Agregar `_checked_unclean_close = False` en `__init__`
- Línea ~4059-4113: Nuevo método `_check_and_handle_unclean_close()`
- Línea ~4045-4056: Modificar `closeEvent()` para crear marca
- Línea ~2927-2928: Llamar `_check_and_handle_unclean_close()` en `update_value()`

### `tests/test_unclean_close_detection.py`
- Nuevo archivo con 17 tests

---

## Comportamiento Esperado

### Cierre Normal (Usuario cierra la app)
- ✅ Se crea archivo `cierre_limpio`
- ✅ Al reiniciar, se detecta y se borra
- ✅ No hay parada automática

### Cierre Abrupto con Terapia
- ❌ No se crea archivo (app muere)
- ✅ Al reiniciar, se detecta ausencia
- ✅ Se verifica `primingProcessStatus = 14` y `treatmentModeSelection != 3`
- ✅ Se llama `stop_treatment()`
- ✅ Se muestra mensaje al usuario

### Cierre Abrupto con Limpieza
- ❌ No se crea archivo (app muere)
- ✅ Al reiniciar, se detecta ausencia
- ✅ Se verifica `treatmentModeSelection = 3` y `primingProcessStatus = 6`
- ✅ Se envían comandos de detener limpieza
- ✅ Se muestra mensaje al usuario

### Cierre Abrupto pero Sin Terapia/Limpieza
- ❌ No se crea archivo (app muere)
- ✅ Al reiniciar, se detecta ausencia
- ✅ Se verifica estado: no cumple condiciones
- ✅ No se hace parada
- ✅ No se muestra mensaje

---

## Mensaje al Usuario

Si se detiene algo:

```
"La aplicación se cerró de forma inesperada. El proceso en curso se detuvo. 
Hay que iniciarlo de nuevo."
```

---

## Commit

```
Commit: 56016f2

fix: si la aplicación no cerró limpio, detiene la terapia o la limpieza al volver a abrir

- Marcar cierre limpio en closeEvent()
- Detectar en _check_and_handle_unclean_close() (una sola vez)
- Parar terapia si priming_status = 14/15 y mode != 3
- Parar limpieza si mode = 3 y priming_status = 6
- Mensaje al usuario si se detiene algo
- 17 tests: todos pasan
```

---

## Validaciones

- ✅ Sintaxis validada: `py_compile` exitoso
- ✅ Tests: 17/17 pasan
- ✅ Sin cambios no autorizados (no revierte dialysis_screenV2 ni alarmas)
- ✅ Sin push a repositorio

---

**Status:** ✅ Completado  
**Pruebas:** 17/17 pasan  
**Fechas de marca:** `get_runtime_data_path("var", "log", "cierre_limpio")`
