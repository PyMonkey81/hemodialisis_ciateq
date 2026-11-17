# Logs Esperados - Cierre de Registros en Timeout

## Ejemplo de Ejecución Completa

### Fase 1: Terapia en Progreso

```
INFO:core.treatment_controller:Timer de terapia iniciado (hardware en RUNNING)
INFO:gui.appMainHemodialysis:Mostrando 'TERAPIA FINALIZADA' porque fue pausada por timeout
...
(update_therapy_times se ejecuta cada segundo)
...
```

### Fase 2: Timeout Detectado

```
INFO:core.treatment_controller:Tiempo de terapia completado - Pausando en bypass
INFO:core.treatment_controller:Cerrando registros de terapia - Tiempo transcurrido: 3600s
```

### Fase 3: Cierre de Registros

```
INFO:core.treatment_controller:KTV finalized_delivered_dose ejecutado
INFO:core.treatment_controller:KTV final report guardado
INFO:core.treatment_controller:KTV abort ejecutado
INFO:core.treatment_controller:Sesión de tratamiento registrada
INFO:core.treatment_controller:Treatment logger cerrado
INFO:core.treatment_controller:Registros de terapia cerrados - Hardware permanece en PAUSED
```

### Fase 4: Pantalla del Usuario

```
INFO:gui.appMainHemodialysis:Mostrando 'TERAPIA FINALIZADA'
```

### Fase 5: Hardware a IDLE

```
INFO:gui.appMainHemodialysis:Hardware confirmó fin de tratamiento → Registrando historial
DEBUG:gui.appMainHemodialysis:Saltando registro: registros ya cerrados por timeout
DEBUG:gui.appMainHemodialysis:Timer de terapia detenido tras transición a IDLE
```

---

## Escenario: Reanudación tras Timeout

```
# Usuario presiona "Reanudar"
INFO:core.treatment_controller:=== INTENTO DE INICIO DE TRATAMIENTO ===
INFO:core.treatment_controller:Terapia iniciada correctamente
# (Nota: NO envía dialyModeOperationStart porque therapy_records_closed=True)
```

---

## Escenario: Finalizar Terapia

```
INFO:core.treatment_controller:Terapia finalizada completamente
# (Limpió banderas: bypass_pause_sent, therapy_finished_by_time, therapy_records_closed)
```

---

## Escenario: Doble Cierre (Protección)

```
# Primera llamada
INFO:core.treatment_controller:Cerrando registros de terapia - Tiempo transcurrido: 3600s
...
# Segunda llamada (si ocurriera)
DEBUG:core.treatment_controller:Registros de terapia ya cerrados, ignorando llamada duplicada
```

---

## Logs Detallados por Componente

### TreatmentController

#### Inicialización
```
# En __init__:
# self.therapy_records_closed = False (silent, solo código)
```

#### Inicio de Terapia
```
INFO: "=== INTENTO DE INICIO DE TRATAMIENTO ==="
INFO: "Terapia iniciada correctamente"
```

#### Timeout Detectado
```
INFO: "Tiempo de terapia completado - Pausando en bypass"
INFO: "Cerrando registros de terapia - Tiempo transcurrido: XXXs"
INFO: "KTV finalized_delivered_dose ejecutado"
INFO: "KTV final report guardado"
INFO: "KTV abort ejecutado"
INFO: "Sesión de tratamiento registrada"
INFO: "Treatment logger cerrado"
INFO: "Registros de terapia cerrados - Hardware permanece en PAUSED"
```

#### Reanudación
```
INFO: "=== INTENTO DE INICIO DE TRATAMIENTO ==="
# (Sin enviar dialyModeOperationStart)
INFO: "Terapia iniciada correctamente"
```

#### Finalizar Terapia
```
INFO: "Terapia finalizada completamente"
```

#### Protección contra Duplicados
```
DEBUG: "Registros de terapia ya cerrados, ignorando llamada duplicada"
```

### appMainHemodialysis

#### Transición a IDLE
```
INFO: "Hardware confirmó fin de tratamiento → Registrando historial"

# Opción A: Registros no cerrados por timeout
DEBUG: "Historial de tratamiento registrado"
DEBUG: "Timer de terapia detenido tras transición a IDLE"

# Opción B: Registros ya cerrados por timeout
DEBUG: "Saltando registro: registros ya cerrados por timeout"
DEBUG: "Timer de terapia detenido tras transición a IDLE"
```

---

## Formato de Logs Esperado

Todos los logs incluyen:
- **Timestamp**: `2026-11-17 10:15:45,123`
- **Level**: `INFO`, `DEBUG`, `WARNING`, `ERROR`
- **Logger Name**: `core.treatment_controller`, `gui.appMainHemodialysis`
- **Mensaje**: Descripción clara en español

Ejemplo:
```
2026-11-17 10:15:45,123 - INFO - core.treatment_controller - Tiempo de terapia completado - Pausando en bypass
2026-11-17 10:15:45,124 - INFO - core.treatment_controller - Cerrando registros de terapia - Tiempo transcurrido: 3600s
2026-11-17 10:15:45,125 - INFO - core.treatment_controller - KTV finalized_delivered_dose ejecutado
```

---

## Debugging con Logs

### Verificar que el Timeout Se Detectó
Buscar en logs:
```
"Tiempo de terapia completado"  ✓ Detectado correctamente
```

### Verificar que Se Cierra una Sola Vez
Buscar en logs:
```
"Registros de terapia ya cerrados"  → Indica segunda llamada (protección activa)
```

### Verificar que KTV Se Guardó
Buscar en logs:
```
"KTV final report guardado"  ✓ Reporte guardado
```

### Verificar que No Duplica en IDLE
Buscar en logs:
```
"Saltando registro: registros ya cerrados por timeout"  ✓ No duplicó
```

### Verificar que No Envió Comando en Reanudación
Buscar que NO aparezca:
```
"dialyModeOperationStart" cuando therapy_records_closed=True
```

---

## Troubleshooting

### Síntoma: Reporte KTV duplicado
**Verificar logs:**
- ¿Aparece "KTV final report guardado" dos veces?
- ¿Aparece "Registros de terapia ya cerrados"?

**Solución:**
- Verificar que `therapy_records_closed` se pone en True correctamente
- Verificar que `stop_therapy_timer()` respeta la bandera

### Síntoma: Sesión registrada dos veces
**Verificar logs:**
- ¿Aparece "Sesión de tratamiento registrada" dos veces?
- ¿Aparece "Saltando registro" en IDLE?

**Solución:**
- Verificar que la condición en IDLE se evalúa correctamente
- Verificar acceso a `therapy_records_closed`

### Síntoma: Logger cerrado dos veces
**Verificar logs:**
- ¿Error al cerrar logger?
- ¿Aparecen dos llamadas a close()?

**Solución:**
- Verificar que la verificación en IDLE previene doble cierre
- Revisar manejo de excepciones

---

## Configuración de Logging (Referencia)

```python
import logging

# Para ver DEBUG también:
logging.basicConfig(level=logging.DEBUG)

# Para guardar en archivo:
logging.basicConfig(
    level=logging.INFO,
    filename='tratamiento.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
```

---

## Checklist de Logs Esperados

Cuando reloj llega a 0:
- [ ] "Tiempo de terapia completado - Pausando en bypass"
- [ ] "Cerrando registros de terapia - Tiempo transcurrido: XXXs"
- [ ] "KTV finalized_delivered_dose ejecutado"
- [ ] "KTV final report guardado"
- [ ] "KTV abort ejecutado"
- [ ] "Sesión de tratamiento registrada"
- [ ] "Treatment logger cerrado"
- [ ] "Registros de terapia cerrados - Hardware permanece en PAUSED"

Cuando hardware pasa a IDLE:
- [ ] "Hardware confirmó fin de tratamiento → Registrando historial"
- [ ] "Saltando registro: registros ya cerrados por timeout" (Opción B)
- [ ] "Timer de terapia detenido tras transición a IDLE"

Cuando usuario reanuda:
- [ ] "=== INTENTO DE INICIO DE TRATAMIENTO ==="
- [ ] "Terapia iniciada correctamente"
- [ ] (NO debe aparecer: dialyModeOperationStart)

