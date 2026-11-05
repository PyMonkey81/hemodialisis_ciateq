# ✅ CAMBIO: Título del Teclado Muestra Nombre del Parámetro

## Problema Anterior

El título del teclado numérico mostraba tags técnicos internos:
- ❌ "Límite MIN / arterPresProcessData"
- ❌ "Límite MAX / dialyTempControlSetPoint"
- ❌ "Límite MIN / venouPresProcessData"

Esto no es amigable para el usuario operador.

---

## Solución Implementada

### Cambio 1: Lambda en `populate_variables()` (línea 199-200)

**Antes:**
```python
min_edit.clicked.connect(lambda c=False, e=min_edit, t=tag, f="min": self.open_numpad(e, t, f))
max_edit.clicked.connect(lambda c=False, e=max_edit, t=tag, f="max": self.open_numpad(e, t, f))
```

**Después:**
```python
min_edit.clicked.connect(lambda c=False, e=min_edit, t=tag, n=name, f="min": self.open_numpad(e, t, n, f))
max_edit.clicked.connect(lambda c=False, e=max_edit, t=tag, n=name, f="max": self.open_numpad(e, t, n, f))
```

Ahora cada lambda captura:
- `t=tag`: el tag real (ej. "arterPresProcessData") para búsqueda interna
- `n=name`: el nombre legible (ej. "Presión arterial en línea sanguínea") para mostrar

### Cambio 2: Firma de `open_numpad()` (línea 219)

**Antes:**
```python
def open_numpad(self, line_edit, tag, field):
    ...
    title=f"Límite {field.upper()} \n {tag}"
```

**Después:**
```python
def open_numpad(self, line_edit, tag, param_name, field):
    ...
    title=f"Límite {field.upper()} \n {param_name}"
```

Ahora:
- `tag`: sigue siendo usado para buscar límites y calcular `allow_negative`
- `param_name`: es el nuevo parámetro que contiene el nombre legible
- El título muestra `param_name` en lugar de `tag`

---

## Resultados Visibles

### Presión Arterial

| Antes | Después |
|-------|---------|
| "Límite MIN / arterPresProcessData" | "Límite MIN / Presión arterial en línea sanguínea" |
| "Límite MAX / arterPresProcessData" | "Límite MAX / Presión arterial en línea sanguínea" |

### Presión Venosa

| Antes | Después |
|-------|---------|
| "Límite MIN / venouPresProcessData" | "Límite MIN / Presión venosa en línea sanguínea" |
| "Límite MAX / venouPresProcessData" | "Límite MAX / Presión venosa en línea sanguínea" |

### Temperatura

| Antes | Después |
|-------|---------|
| "Límite MIN / dialyTempControlSetPoint" | "Límite MIN / Setpoint flujo de dializado" |
| "Límite MAX / dialyTempControlSetPoint" | "Límite MAX / Setpoint flujo de dializado" |

---

## Flujo de Ejecución

```
Usuario toca "Límite Inferior" de Presión Arterial (arterPresProcessData)
        ↓
Lambda captura:
  ├─ e=min_edit (widget del campo)
  ├─ t="arterPresProcessData" (tag)
  ├─ n="Presión arterial en línea sanguínea" (nombre)
  └─ f="min" (field)
        ↓
open_numpad(line_edit, tag="arterPresProcessData", param_name="Presión arterial en línea sanguínea", field="min")
        ↓
Búsqueda interna:
  ├─ get_limits("arterPresProcessData") → (-100, 400)
  ├─ allow_negative = (-100 < 0) = True
  └─ (tag sigue siendo necesario para búsqueda)
        ↓
Título del teclado:
  └─ f"Límite MIN \n Presión arterial en línea sanguínea" ✓
        ↓
Usuario ve un título legible
```

---

## Compatibilidad

- ✅ El tag sigue siendo usado internamente para búsqueda de límites
- ✅ La tecla +/− aparece correctamente según los límites
- ✅ Ningún cambio en `numpad_modal.py`
- ✅ Ningún cambio en otros teclados (flujo, heparina, tiempo)
- ✅ Ningún cambio en validaciones de guardado

---

## Cambios Estadísticos

```
gui/configuration/alarm_screen_config.py:
  - Cambio en 2 lambdas: +2 parámetros
  - Cambio en firma open_numpad(): +1 parámetro
  - Cambio en título: usar param_name

Total: +5 líneas, -4 líneas
Commit: 995f2ac
```

---

## Notas

- El nombre mostrado es `info["name"]`, que es el nombre completo descriptivo
- Si no hay nombre, usa `info["label"]` (etiqueta corta)
- Si tampoco hay etiqueta, usa el `tag` (fallback)
- La unidad NO se muestra en el título (se muestra en la columna de parámetro)

Ejemplo de nombres en variables_map:

```python
0x04: {
    0x02: {
        "name": "Presión arterial en línea sanguínea",      # ← Se muestra aquí
        "label": "P. ARTERIAL",                             # ← Se usa como fallback
        "tag": "arterPresProcessData",                      # ← Nunca aparece en el título
        "limites": (-100, 400),
    }
}
```

---

**Commit:** 995f2ac  
**Fecha:** 2026-11-05  
**Archivos modificados:** 1  
**Estado:** ✅ Completado y listo para pruebas
