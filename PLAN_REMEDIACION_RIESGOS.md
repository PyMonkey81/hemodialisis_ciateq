# MATRIZ DE RIESGOS Y PLAN DE REMEDIACIÓN

---

## TABLA RESUMEN: 25 PROBLEMAS IDENTIFICADOS

| ID | Archivo | Línea | Tipo | Severidad | Impacto | Estado | Priority |
|----|---------|-------|------|-----------|---------|--------|----------|
| 1 | main.py | 47-57 | I/O sin validación | CRÍTICA | App sin logs | Todo | P0 |
| 2 | main.py | 62-81 | Excepción genérica | CRÍTICA | Logging falla | Todo | P0 |
| 3 | main.py | 92-111 | Excepción genérica | ALTA | UI escalada incorrecta | Todo | P1 |
| 4 | appMain | ~450 | I/O sin validación | CRÍTICA | Sin conectividad serial | Todo | P0 |
| 5 | appMain | ~470 | Init sin validación | ALTA | BioZ no funciona | Todo | P1 |
| 6 | appMain | ~470 | Init sin validación | MEDIA | Conductividad inconsistente | Todo | P2 |
| 7 | appMain | ~540 | Config JSON | MEDIA | Valores default inseguros | Todo | P2 |
| 8 | appMain | ~780 | Estado inconsistente | CRÍTICA | Máquina desincronizada | Todo | P0 |
| 9 | appMain | ~1100 | None check | CRÍTICA | Crash en get_phase() | Todo | P0 |
| 10 | appMain | ~1230 | Lock Boolean | MEDIA | Doble-click fallo | Todo | P2 |
| 11 | appMain | ~1395 | Ciclo infinito | MEDIA | Stack overflow | Todo | P2 |
| 12 | appMain | ~1500 | Truthiness check | ALTA | Omite valor 0.0 | Todo | P1 |
| 13 | appMain | ~1540 | int() sin validación | ALTA | ValueError | Todo | P1 |
| 14 | appMain | ~1540 | float() sin validación | ALTA | TypeError | Todo | P1 |
| 15 | appMain | ~1950 | Estado latched | ALTA | Heparina no reactiva | Todo | P1 |
| 16 | appMain | ~2300 | None check | MEDIA | Race condition | Todo | P2 |
| 17 | appMain | ~2395 | Exception handling | MEDIA | Log saturado | Todo | P2 |
| 18 | appMain | ~2418 | Lock Boolean | MEDIA | Reentrancia timer | Todo | P2 |
| 19 | appMain | ~2470 | Widget access | MEDIA | currentWidget None | Todo | P2 |
| 20 | appMain | ~3700 | Destructor | MEDIA | Crash cleanup | Todo | P2 |
| 21 | appMain | ~600 | Resource leak | MEDIA | CSV sin cerrar | Todo | P2 |
| 22 | appMain | ~450 | Race condition | ALTA | Update_value concurrent | Todo | P1 |
| 23 | appMain | ~330 | Chain init | CRÍTICA | KTV sin BioZ | Todo | P0 |
| 24 | appMain | ~380 | Lazy init | ALTA | Puerto nunca se abre | Todo | P1 |
| 25 | appMain | ~2695 | Widget None | MEDIA | setStyleSheet crash | Todo | P2 |

---

## CLASIFICACIÓN POR SEVERIDAD

### P0 (CRÍTICA) - 7 items
Deben correggirse ANTES de cualquier deployment en pacientes.

| ID | Descripción | Línea | Fix Complexity |
|----|-------------|-------|-----------------|
| 1 | App sin capacidad de logging | main.py:47 | Media |
| 2 | Logging falla silenciosamente | main.py:62 | Media |
| 4 | Sin conectividad serial | appMain:450 | Alta |
| 8 | Estado desincronizado | appMain:780 | Alta |
| 9 | hardware_mapper None | appMain:1100 | Media |
| 23 | KtvController sin BioZ | appMain:330 | Media |

### P1 (ALTA) - 10 items
Deben correggirse en el sprint actual.

| ID | Descripción | Línea | Fix Complexity |
|----|-------------|-------|-----------------|
| 3 | UI escalada incorrecta | main.py:92 | Baja |
| 5 | BioZ no funciona | appMain:470 | Media |
| 7 | Config JSON | appMain:540 | Media |
| 12 | Omite valor 0.0 | appMain:1500 | Baja |
| 13 | int() sin validación | appMain:1540 | Baja |
| 14 | float() sin validación | appMain:1540 | Baja |
| 15 | Heparina no reactiva | appMain:1950 | Media |
| 22 | Race condition update_value | appMain:450 | Alta |
| 24 | Puerto nunca se abre | appMain:380 | Media |

### P2 (MEDIA) - 8 items
Deben correggirse en sprint siguiente.

| ID | Descripción | Línea | Fix Complexity |
|----|-------------|-------|-----------------|
| 6 | Conductividad inconsistente | appMain:470 | Media |
| 10 | Boolean lock | appMain:1230 | Baja |
| 11 | Ciclo infinito | appMain:1395 | Baja |
| 16 | Race condition | appMain:2300 | Media |
| 17 | Log saturado | appMain:2395 | Baja |
| 18 | Boolean lock timer | appMain:2418 | Baja |
| 19 | Widget None access | appMain:2470 | Baja |
| 20 | Destructor crash | appMain:3700 | Baja |
| 21 | CSV leak | appMain:600 | Media |
| 25 | setStyleSheet crash | appMain:2695 | Baja |

---

## PLAN DE REMEDIACIÓN SPRINT 1

### Task 1: Validación de I/O Crítica (3 horas)
- [ ] Añadir try/except específicos para creación de directorios (main.py:47)
- [ ] Implementar fallback a memoria si creación falla
- [ ] Verificar que logging funciona antes de continuar
- Archivos: main.py, logging setup
- Riesgo reducido de: 1, 2

### Task 2: Validación de Puerto Serial (4 horas)
- [ ] Implementar SerialCommunication.is_ready() check
- [ ] Validar puerto abierto al init
- [ ] Mostrar error modal si puerto falla
- [ ] Implementar modo demo/testing
- Archivos: connection/serial_communication.py, appMainHemodialysis.py
- Riesgo reducido de: 4, 24

### Task 3: Sincronización de Estado (5 horas)
- [ ] Introducir QMutex para acceso a current_values
- [ ] Centralizar todas las escritas de estado en StateManager
- [ ] Validar invariantes de estado después de cada cambio
- [ ] Loguear todas las transiciones de estado
- Archivos: core/state_manager.py, appMainHemodialysis.py
- Riesgo reducido de: 8, 23

### Task 4: Validación de Tipos (3 horas)
- [ ] Reemplazar todos los int() con safe_int()
- [ ] Reemplazar todos los float() con safe_float()
- [ ] Cambiar `if value:` a `if value is not None:`
- [ ] Ejecutar find/replace regex
- Archivos: appMainHemodialysis.py (todas las lineas de conversion)
- Riesgo reducido de: 12, 13, 14

### Task 5: Hardware Mapper Null Check (2 horas)
- [ ] Validar hardware_mapper no es None en __init__
- [ ] Agregar guards en todos los accesos a hardware_mapper
- [ ] Loguear si hardware_mapper es None
- Archivos: appMainHemodialysis.py línea ~1100
- Riesgo reducido de: 9

---

## PLAN DE REMEDIACIÓN SPRINT 2

### Task 6: Threading & Locks (5 horas)
- [ ] Reemplazar boolean locks con QMutex
- [ ] Usar QMutex en _master_timer_tick
- [ ] Usar QMutex en _start_treatment_locked
- [ ] Implementar test de reentrancia
- Archivos: appMainHemodialysis.py
- Riesgo reducido de: 10, 18, 22

### Task 7: Estados Latched (3 horas)
- [ ] Resetear _heparin_auto_stop_latched en pausar/reanudar
- [ ] Agregar tests de caso de pausar/reanudar
- [ ] Loguear transiciones de heparina
- Archivos: appMainHemodialysis.py línea ~1950
- Riesgo reducido de: 15

### Task 8: Ciclos Infinitos (2 horas)
- [ ] Limitar reintentos en show_first_dialog()
- [ ] Agregar max_attempts=5
- [ ] Mostrar error después de 5 cancelaciones
- Archivos: appMainHemodialysis.py línea ~1395
- Riesgo reducido de: 11

### Task 9: Gestión de Recursos (4 horas)
- [ ] Implementar context manager para CSV loggers
- [ ] Implementar cleanup() explícito
- [ ] Reemplazar __del__() con cleanup() calls
- [ ] Validar archivos se cierren en QApplication.aboutToQuit
- Archivos: utilities/csv_logger.py, appMainHemodialysis.py
- Riesgo reducido de: 20, 21

### Task 10: Verificación de Sensores (4 horas)
- [ ] Implementar health check para BioZ
- [ ] Implementar health check para PatternConductivity
- [ ] Implementar health check para MegaConductivitySensor
- [ ] Mostrar WARNING en UI si sensor falla
- [ ] Permitir continuar sin sensor (con flag)
- Archivos: connection/bioz_urea_controller.py, etc.
- Riesgo reducido de: 5, 6

---

## CHECKLIST DE VERIFICACIÓN POR FIX

### Para cada fix, validar:
```
[ ] Código compilado sin warnings
[ ] Unidad testeada (si existe test)
[ ] Logging agregado apropiadamente
[ ] Documentación actualizada
[ ] Reviewed por segundo desarrollador
[ ] No introduce nueva deuda técnica
[ ] Sigue estándares del proyecto
```

---

## ESTIMACIÓN DE ESFUERZO

### Por Severidad:
- **P0 items**: 24 horas = 3 días de trabajo
- **P1 items**: 18 horas = 2.25 días de trabajo
- **P2 items**: 20 horas = 2.5 días de trabajo
- **Total**: 62 horas = ~8 días de trabajo en 1 persona

### Timeline recomendado:
- **Semana 1**: Sprint 1 (P0 + inicio P1)
- **Semana 2**: Sprint 1 (final) + Sprint 2 (inicio)
- **Semana 3**: Sprint 2 (final) + Verificación

---

## CRITERIOS DE ACEPTACIÓN

Para cada fix, se acepta cuando:

1. **Code Review pasado** - Otro desarrollador aprueba
2. **Tests pasan** - Suite de tests completa
3. **Logging funciona** - Eventos se registran en logs
4. **No regresiones** - Funcionalidad existente no afectada
5. **Documentado** - Docstring y commit message claros
6. **Verificado en HW** - Test en máquina real si aplica

---

## RIESGOS RESIDUALES

Después de remediación:

| Risk | Probabilidad | Impacto | Mitigación |
|------|-------------|---------|-----------|
| Port desconexión durante terapia | Media | Alto | Implementar reconnect automático |
| JSON config corrupted en disco | Baja | Medio | Validar schema, usar defaults |
| Sensor falla durante terapia | Baja | Alto | Mostrar alerta, permitir continue |
| Timer reentra si lag > interval | Baja | Medio | QMutex + timeout |
| Estado inconsistente si lag alto | Muy Baja | Alto | Locks eliminan issue |

---

## MÉTRICAS DE ÉXITO

Después de remediación:

1. **0 crashes** durante 48 horas de testing
2. **100% logs** registrados en archivo (0 eventos perdidos)
3. **0 race conditions** detectadas por Valgrind/ThreadSanitizer
4. **100% validación** de entrada en métodos críticos
5. **<5 reintentosm** en ciclos infinitos (limitado)
6. **<1% CPU** idle (no spinning loops)

---

## CONTACTS Y RESPONSABILIDADES

| Componente | Owner | Reviewer |
|-----------|-------|----------|
| main.py | Dev1 | Dev2 |
| appMainHemodialysis.py | Dev1, Dev2 | Dev3 |
| connection/* | Dev2 | Dev1 |
| core/state_manager.py | Dev1 | Dev2, QA |
| utilities/* | Dev1 | Dev2 |

---

## NOTAS FINALES

- Este análisis se basa en inspección estática de código
- Se recomienda análisis dinámico con debugger y profiler
- Pruebas de stress test después de cada remediación
- Actualizar este documento después de cada sprint completado
- Agregar tests automatizados para prevenir regresiones
