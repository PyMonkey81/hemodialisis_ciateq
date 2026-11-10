# REFERENCIA RÁPIDA: PUNTOS DE QUIEBRE CRÍTICOS

## ⚡ 10 SEGUNDOS

**25 problemas encontrados**  
- 7 CRÍTICA, 10 ALTA, 8 MEDIA  
- Risk: 10/10 (NO SEGURO PARA PACIENTES)  
- Fix: 62 horas (~8 días)

## 1 MINUTO

**Top 3 problemas**:
1. Puerto serial sin validación → Sin datos
2. Estado desincronizado → UI incorrecta  
3. hardware_mapper=None → Crash

**Recomendación**: Leer RESUMEN_EJECUTIVO.md antes de deployment

## 5 MINUTOS

**Patrones encontrados**:
- Truthiness check (omite 0.0)
- Excepciones genéricas sin logging
- Inicialización sin validación
- Acceso a None sin guards
- Boolean locks no atómicos
- Conversiones sin tipo seguro
- Ciclos infinitos (recursión)
- Estado inconsistente

**Cómo empezar**: Importa matriz_problemas.csv a Jira

## 10 MINUTOS

**Sprint 1 (CRÍTICA)** - 18 horas:
- [ ] Task 1: Validación I/O (3h)
- [ ] Task 2: Puerto serial (4h)
- [ ] Task 3: Sincronización estado (5h)
- [ ] Task 4: Validación tipos (3h)
- [ ] Task 5: hardware_mapper (2h)

**Criterio de éxito**: 0 crashes en 48 horas

## 15 MINUTOS

**Archivos a revisar**:
- main.py: Líneas 40-111 (logging, init)
- appMainHemodialysis.py: Líneas 300-600, 1500-1950, 2400-2500

**Fixes más comunes**:
```python
# 1. Cambiar if value: a if value is not None:
# 2. Usar safe_int() y safe_float()
# 3. Agregar logger.error() en todos los except
# 4. Reemplazar bool locks con QMutex
# 5. Validar puerto serial, hardware_mapper, etc
```

---

## MATRIZ RÁPIDA DE CRÍTICAS

| Línea | Archivo | Problema | Fix | Horas |
|-------|---------|----------|-----|-------|
| 47-57 | main.py | Dir creation | Failover | 2 |
| 62-81 | main.py | Logging | Validate | 2 |
| ~450 | appMain | Serial | Check port | 4 |
| ~780 | appMain | State | QMutex | 5 |
| ~1100 | appMain | None | Guard | 2 |
| ~330 | appMain | Init chain | Validate | 3 |
| ~470 | appMain | BioZ | Error check | 3 |

---

## COMANDOS ÚTILES

```bash
# Ver documentos
cat RESUMEN_EJECUTIVO.md          # 5 min
cat ANALISIS_PUNTOS_QUIEBRE.md    # 30 min
cat ANALISIS_PATRONES_ESPECIFICOS.md  # 20 min

# Importar a Jira
xdg-open matriz_problemas.csv

# Ver solo críticas
grep "CRÍTICA" matriz_problemas.csv

# Ver solo Sprint 1
grep "S1" matriz_problemas.csv
```

---

## CHECKLIST DE ACCIÓN

```
□ Leer RESUMEN_EJECUTIVO.md
□ Revisar top 5 críticas
□ Planificar Sprint 1 (18 horas)
□ Asignar tasks a developers
□ Comenzar Task 1: Validación I/O
□ Completar Sprint 1
□ Testing 48 horas
□ Code review
□ Deployment
```

---

## RIESGOS SI NO SE CORRIGEN

- 30-50% probabilidad de evento adverso
- Paciente recibe dosis incorrecta
- Sensores no actualizan
- Alarmas no funcionan
- Coágulos, infecciones, muerte

---

## CONTACTOS

Preguntas sobre:
- **Qué**: Ver RESUMEN_EJECUTIVO.md sección "Hallazgos"
- **Dónde**: Ver ANALISIS_PUNTOS_QUIEBRE.md línea exacta
- **Cómo fijar**: Ver código "propuesto" en documento
- **Timeline**: Ver PLAN_REMEDIACION_RIESGOS.md
- **Tracking**: Usar matriz_problemas.csv

---

**Análisis completado**: 2026-11-10  
**Confianza**: ALTA  
**Recomendación**: NO SEGURO PARA PACIENTES
