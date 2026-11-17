# Diagrama de Flujo: Cierre de Registros en Timeout

## Flujo Completo del Sistema

```
TERAPIA EN PROGRESS (RUNNING)
│
├─ update_therapy_times() se ejecuta periódicamente
│  │
│  ├─ Calcula: remaining = total_therapy_seconds - current_elapsed
│  │
│  ├─ ¿remaining <= 0?
│  │  │  ¿bypass_pause_sent == False?
│  │  │  │  ¿status_code == 14 (BYPASS)?
│  │  │  │  │
│  │  │  │  YES → Tiempo completado en bypass
│  │  │  │  │
│  │  │  │  ├─ SET: bypass_pause_sent = True
│  │  │  │  ├─ SET: therapy_finished_by_time = True
│  │  │  │  │
│  │  │  │  ├─ CALL: pause_treatment()
│  │  │  │  │  │
│  │  │  │  │  ├─ Calcula tiempo transcurrido
│  │  │  │  │  ├─ Envia: dialyModeOperationPause = True
│  │  │  │  │  ├─ Estado: RUNNING → PAUSED (hardware estado 15)
│  │  │  │  │  └─ Muestra: "Terapia finalizada"
│  │  │  │  │
│  │  │  │  ├─ CALL: close_therapy_records_on_timeout()
│  │  │  │  │  │
│  │  │  │  │  ├─ ¿therapy_records_closed == True?
│  │  │  │  │  │  YES → Retorna (ya fue cerrado)
│  │  │  │  │  │
│  │  │  │  │  ├─ SET: therapy_records_closed = True
│  │  │  │  │  │
│  │  │  │  │  ├─ 1. TOMA TIEMPO: elapsed_seconds = get_elapsed_seconds()
│  │  │  │  │  │
│  │  │  │  │  ├─ 2. KTV FINALIZADO
│  │  │  │  │  │  ├─ CALL: ktv_controller.finalize_delivered_dose()
│  │  │  │  │  │  └─ CALL: KTVScreen.save_final_report()
│  │  │  │  │  │
│  │  │  │  │  ├─ 3. ABORTA MEDICIÓN (sin reset_screen_data)
│  │  │  │  │  │  └─ CALL: ktv_controller.abort("Terapia cerrada por tiempo")
│  │  │  │  │  │
│  │  │  │  │  ├─ 4. REGISTRA SESIÓN
│  │  │  │  │  │  ├─ CALL: register_treatment_session()
│  │  │  │  │  │  └─ SET: current_treatment_start = None
│  │  │  │  │  │
│  │  │  │  │  ├─ 5. CIERRA LOGGER
│  │  │  │  │  │  └─ CALL: treatment_logger.close()
│  │  │  │  │  │
│  │  │  │  │  ├─ 6. GUARDA NIBP (si existe método)
│  │  │  │  │  │  └─ CALL: nibp_pressure_history.save() (si existe)
│  │  │  │  │  │
│  │  │  │  │  └─ 7. TreatmentPhase NO CAMBIA
│  │  │  │  │
│  │  │  │  └─ RETORNA a update_therapy_times
│  │  │  │
│  │  │  NO → Continua sin hacer nada
│  │  │
│  │  └─ Actualiza displays del tiempo
│  │
│  └─ Continua esperando próxima llamada
│
└─ Hardware transiciona a IDLE (fin de terapia)
   │
   ├─ appMainHemodialysis.py detecta: new_phase == IDLE
   │  │
   │  ├─ ¿treatment_controller.therapy_records_closed == True?
   │  │  │
   │  │  YES → Registros ya fueron cerrados en timeout
   │  │  │
   │  │  ├─ SALTA: register_treatment_session()
   │  │  ├─ SALTA: treatment_logger.close()
   │  │  └─ Log: "Saltando registro: registros ya cerrados por timeout"
   │  │
   │  NO → Primera vez que se cierra (no fue timeout)
   │  │
   │  ├─ LLAMA: register_treatment_session()
   │  ├─ LLAMA: treatment_logger.close()
   │  └─ Log: "Historial de tratamiento registrado"
   │
   └─ LLAMA SIEMPRE: treatment_controller.stop_therapy_timer()
      │
      ├─ ¿treatment_controller.therapy_records_closed == True?
      │  │
      │  YES → Registros ya cerrados, NO guardar otro reporte
      │  │
      │  ├─ SALTA: KTVScreen.save_final_report()
      │  └─ Limpia datos internos
      │
      NO → Registros no cerrados, guardar reporte
      │
      └─ LLAMA: KTVScreen.save_final_report()
         └─ Limpia datos internos
```

## Escenarios Especiales

### Escenario A: Reanudación después de Timeout

```
Estado PAUSED (después de timeout con therapy_records_closed=True)
│
├─ Usuario presiona "Reanudar"
│  │
│  └─ CALL: start_treatment()
│     │
│     ├─ ¿therapy_records_closed == True?
│     │  │
│     │  YES → NO enviar dialyModeOperationStart
│     │  │
│     │  ├─ SALTA: _write_boolean_command("dialyModeOperationStart", True)
│     │  └─ La pausa permanece para maniobras
│     │
│     NO → Enviar comando normalmente
│     │
│     └─ LLAMA: _write_boolean_command("dialyModeOperationStart", True)
│
└─ Hardware permanece en PAUSED para maniobras clínicas
   └─ Usuario puede ejecutar procedimientos antes de continuar
```

### Escenario B: Finalizar Terapia (End)

```
Estado PAUSED (después de timeout)
│
├─ Usuario presiona "Finalizar Terapia"
│  │
│  └─ CALL: treatment_controller.end_therapy()
│     │
│     ├─ LLAMA: _write_boolean_command("dialyModeOperationStop", True)
│     ├─ LLAMA: _write_boolean_command("dialyModeOperationStart", False)
│     ├─ LLAMA: _write_boolean_command("dialyStopDialysisButt", True)
│     ├─ LLAMA: _write_boolean_command("dialyStartDialysisButt", False)
│     │
│     ├─ LIMPIA BANDERAS:
│     │  ├─ therapy_finished_by_time = False
│     │  ├─ bypass_pause_sent = False
│     │  └─ therapy_records_closed = False ← Permite nueva terapia
│     │
│     ├─ LLAMA: _reset_session_counters(reset_total=True)
│     │
│     └─ Cierra loggers si aún están abiertos
│
└─ Sistema listo para nueva sesión de terapia
   └─ prepare_new_treatment_session() limpiará therapy_records_closed de nuevo
```

## Estados y Transiciones

```
                     ┌─────────────────┐
                     │     IDLE        │
                     └────────┬────────┘
                              │
                              │ Inicio de terapia
                              ▼
                     ┌─────────────────┐
                     │    RUNNING      │
                     └────────┬────────┘
                              │
                    ┌─────────┴──────────┐
                    │ Tiempo = 0 en      │
                    │ bypass (estado 14) │
                    └─────────┬──────────┘
                              │
              ┌───────────────┴───────────────┐
              │ pause_treatment()             │
              │ + close_therapy_records...()  │
              ▼                               │
       ┌─────────────────┐                   │
       │  PAUSED (15)    │◄──────────────────┘
       │therapy_records_ │
       │closed = True    │
       └────────┬────────┘
                │
       ┌────────┴────────┐
       │                 │
       │ Reanudar        │ Finalizar Terapia
       │ (NO envía       │ (end_therapy)
       │  comando)       │
       │                 │
       ▼                 ▼
   PAUSED         end_therapy():
   (maniobras)    - Apaga todo
                  - Limpia banderas
                  - therapy_records_closed = False
                              │
                              ▼
                       IDLE (lista nueva sesión)
```

## Protecciones Contra Duplicados

```
Punto 1: close_therapy_records_on_timeout()
┌────────────────────────────────────────────┐
│ if self.therapy_records_closed:            │
│     logger.debug("Ya cerrado...")          │
│     return  # ← PROTECCIÓN 1               │
│ self.therapy_records_closed = True         │
└────────────────────────────────────────────┘

Punto 2: appMainHemodialysis en IDLE
┌────────────────────────────────────────────┐
│ if NOT treatment_controller.               │
│        therapy_records_closed:             │
│     register_treatment_session()           │
│     treatment_logger.close()               │
│ else:                                      │
│     logger.debug("Saltando...")  # ← P2   │
└────────────────────────────────────────────┘

Punto 3: stop_therapy_timer()
┌────────────────────────────────────────────┐
│ if NOT self.therapy_records_closed:        │
│     KTVScreen.save_final_report()          │
│ # else: salta sin guardar  # ← P3         │
└────────────────────────────────────────────┘
```

## Checklist de Comportamiento

- [x] Cuando reloj llega a 0 en RUNNING, pausa UNA SOLA VEZ
- [x] Después de pausar, cierra registros UNA SOLA VEZ
- [x] Pantalla muestra "TERAPIA FINALIZADA"
- [x] Pantalla KTV conserva último valor
- [x] Logger de tratamiento se cierra
- [x] Sesión se registra
- [x] Machine permanece en PAUSED
- [x] Cebado y bombas siguen funcionando
- [x] Cuando se reanuda, NO abre nueva sesión
- [x] Cuando hardware llega a IDLE, NO registra de nuevo
- [x] Cuando usuario finaliza terapia, limpia banderas
- [x] Nueva terapia puede iniciarse normalmente

