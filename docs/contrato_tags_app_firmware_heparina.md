# Contrato de Tags App-Firmware

## Objetivo

Eliminar ambiguedad entre tiempo de terapia y tiempo de paro automatico de heparina, sin romper la logica actual de la aplicacion.

## Problema Detectado

Historicamente, los tags heparineTherapyHours y heparineTherapyMinutes se usaron para:

1. Duracion total de terapia.
2. Duracion de aplicacion de heparina.

Ese uso dual ya no es valido porque ahora la heparina debe poder terminar antes de la terapia.

Si firmware reutiliza heparineTherapyHours y heparineTherapyMinutes para paro de heparina, se rompe:

1. Fin automatico de terapia.
2. Temporizadores y vistas de terapia.
3. Calculo Kt/V basado en tiempo programado.
4. Flujos de limpieza que escriben duracion sobre esos tags.

## Definicion de Contrato (Nuevo)

### Regla principal

heparineTherapyHours y heparineTherapyMinutes quedan reservados EXCLUSIVAMENTE para tiempo total de terapia.

### Tabla de contrato (Viejo vs Nuevo)

| Concepto                       | Tags usados antes                                                       | Nuevo contrato                                                                                 | Responsable de control           |
| ------------------------------ | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------- |
| Tiempo total de terapia        | heparineTherapyHours, heparineTherapyMinutes                            | heparineTherapyHours, heparineTherapyMinutes                                                   | App + Firmware                   |
| Paro automatico bomba heparina | heparineTherapyHours, heparineTherapyMinutes (uso compartido historico) | heparineAutoStopHours, heparineAutoStopMinutes (local app) o nuevos tags dedicados en firmware | App (actual) / Firmware (futuro) |
| Estado de paro heparina        | heparinePumpsStopButton                                                 | heparinePumpsStopButton                                                                        | App/Firmware                     |

## Estado actual en App

1. La app ya separa el paro automatico de heparina en tags locales:
   - heparineAutoStopHours
   - heparineAutoStopMinutes
2. Estos tags locales NO se escriben al controlador.
3. El paro automatico se ejecuta con timer global (master timer) en runtime.
4. Regla clinica aplicada: tiempo heparina <= tiempo terapia - 30 minutos.

## Recomendacion para Firmware

### Opcion A (recomendada)

Crear tags dedicados en firmware para paro automatico de heparina:

1. heparineAutoStopHoursSetpoint
2. heparineAutoStopMinutesSetpoint

Mantener sin cambios:

1. heparineTherapyHours
2. heparineTherapyMinutes

### Opcion B (transitoria)

Si no hay cambio inmediato en firmware, mantener control de paro de heparina en app con tags locales, sin alterar semantica de terapia.

## Criterios de Aceptacion

1. Cambiar paro de heparina NO modifica tiempo total de terapia.
2. Fin de terapia ocurre exactamente en heparineTherapyHours/heparineTherapyMinutes.
3. Kt/V usa tiempo de terapia, no tiempo de heparina.
4. Bomba de heparina se detiene automaticamente cuando se cumple el tiempo configurado de heparina.
5. La regla de seguridad se cumple: paro de heparina como maximo cuando faltan 30 min para terminar terapia.

## Plan de Migracion Sugerido

1. Congelar contrato actual: terapia solo en heparineTherapyHours/heparineTherapyMinutes.
2. Definir y documentar nuevos registros Modbus para auto stop de heparina.
3. Actualizar mapa de variables y escritura serial para nuevos tags dedicados.
4. Mantener fallback local en app durante una version de transicion.
5. Validar con prueba de integracion en 3 escenarios:
   - Terapia 3:00, heparina 2:30.
   - Terapia 5:00, heparina 4:30.
   - Cambio de parametro en runtime sin afectar tiempo total de terapia.

## Nota de compatibilidad

Hasta que firmware exponga tags dedicados de heparina, no debe reinterpretar heparineTherapyHours/heparineTherapyMinutes para otro fin que no sea terapia total.
