# ✅ CORRECCIÓN: Tecla Menos en Alarmas (Tag Real)

## Problema Identificado

La implementación anterior no funcionaba porque:

```python
# ❌ INCORRECTO (antes)
min_edit.clicked.connect(lambda c=False, e=min_edit, t=label_short, f="min": self.open_numpad(e, t, f))
```

Se estaba pasando `label_short` ("P. ARTERIAL") en lugar del `tag` real ("arterPresProcessData"). 

Cuando `open_numpad` intentaba buscar los límites:
```python
min_val, max_val = self.config_manager.get_limits(tag)  # tag = "P. ARTERIAL" ❌
```

No encontraba nada, porque los límites están indexados por tag en variables_map:
```python
# core/variables_map.py
0x04: {
    0x02: {"tag": "arterPresProcessData", "limites": (-100, 400), ...},
}
```

Resultado: `allow_negative` quedaba `False` y no mostraba la tecla +/−.

---

## Solución Implementada

### 1. Cambio en `alarm_screen_config.py` (línea ~204-205)

**Antes:**
```python
min_edit.clicked.connect(lambda c=False, e=min_edit, t=label_short, f="min": self.open_numpad(e, t, f))
max_edit.clicked.connect(lambda c=False, e=max_edit, t=label_short, f="max": self.open_numpad(e, t, f))
```

**Después:**
```python
min_edit.clicked.connect(lambda c=False, e=min_edit, t=tag, f="min": self.open_numpad(e, t, f))
max_edit.clicked.connect(lambda c=False, e=max_edit, t=tag, f="max": self.open_numpad(e, t, f))
```

Ahora pasa `tag` (la variable local que contiene "arterPresProcessData") en lugar de `label_short`.

### 2. Ajuste de Ancho en `numpad_modal.py` (después del keypad_layout)

**Agregado:**
```python
main_layout.addLayout(keypad_layout)

# Ajustar ancho del diálogo según el número de columnas
if self.allow_negative:
    # 4 columnas: +/−, ., 0, ⌫
    self.setMinimumWidth(420)
else:
    # 3 columnas: ., 0, ⌫
    self.setMinimumWidth(330)
```

Esto asegura que:
- Con 3 botones en la última fila: ancho 330px
- Con 4 botones en la última fila: ancho 420px
- Los botones de 90x90px caben sin encimarsa

---

## Flujo Corregido

```
Usuario toca "Límite Inferior" de Presión Arterial
        ↓
populate_variables() obtiene tag="arterPresProcessData"
        ↓
min_edit.clicked → open_numpad(line_edit, tag="arterPresProcessData", "min")
        ↓
open_numpad():
  ├─ min_val, max_val = self.config_manager.get_limits("arterPresProcessData")
  │                                                      ↑
  │                                          Ahora encuentra (-100, 400)
  ├─ allow_negative = (-100 < 0) = True
  └─ NumpadDialog(allow_negative=True)
        ↓
        Dialog con 4 botones: [+/−] [.] [0] [⌫]
        ↓
Usuario ingresa "-40.5"
        ↓
get_value() retorna -40.5
        ↓
Usuario pulsa ACEPTAR
        ↓
Dialog cierra, line_edit muestra "-40.5"
```

---

## Validaciones Incluidas

### En `open_numpad()`
```python
min_val, max_val = self.config_manager.get_limits(tag)
allow_negative = min_val < 0  # ← Usa el tag correcto ahora
```

### En `save_configuration()`
```python
# Obtener límites permitidos
default_min, default_max = self.config_manager.get_default_limits_from_variables_map(tag)

# Validar rango
if min_v < default_min or min_v > default_max:
    self.show_warning_message(f"Límite inferior fuera de rango permitido ({default_min} - {default_max}).")
    return
```

---

## Matriz de Verificación

| Variable | Tag | Min | Max | allow_negative | Tecla +/− |
|----------|-----|-----|-----|--|---|
| Presión Arterial | arterPresProcessData | -100 | 400 | True | ✅ SÍ |
| Presión Venosa | venouPresProcessData | -50 | 300 | True | ✅ SÍ |
| Flujo Sangre | bloodFlowControlSetPoint | 0 | 600 | False | ❌ NO |
| Heparina Dosis | heparineTherapyDosage | 0 | 50 | False | ❌ NO |
| Temperatura | | 33 | 42 | False | ❌ NO |

---

## Cambios Estadísticos

```
gui/components/numpad_modal.py:
  + setMinimumWidth() dinámico: 7 líneas

gui/configuration/alarm_screen_config.py:
  - Cambio de label_short → tag: 2 líneas

Total: +8 líneas, -2 líneas
Commit: 078e9c1
```

---

## Prueba Manual (Paso a Paso)

### Caso 1: Presión Arterial (con negativos)

1. Configuración → Alarmas
2. Buscar "Presión Arterial en línea sanguínea"
3. Tocar campo "Límite Inferior"
4. **Debe aparecer teclado con 4 botones en la última fila: +/− . 0 ⌫**
5. Presionar: +/− → 4 → 0 → . → 5
6. Display: "-40.5"
7. Presionar ACEPTAR
8. Campo ahora muestra "-40.5"
9. Guardar cambios
10. Verificar que se guardó correctamente

### Caso 2: Flujo de Sangre (sin negativos)

1. Configuración → Alarmas
2. Buscar "Flujo Sanguíneo"
3. Tocar campo "Límite Superior"
4. **Debe aparecer teclado con 3 botones en la última fila: . 0 ⌫** (sin +/−)
5. Intentar presionar "-" (no hace nada, es rechazado)
6. Presionar: 5 → 5 → 0
7. Display: "550"
8. Presionar ACEPTAR
9. Guardar cambios

### Caso 3: Valor Inválido (Presión Arterial)

1. Abrir teclado de Presión Arterial
2. Presionar +/− (display: "-")
3. Presionar ACEPTAR
4. **Diálogo permanece abierto** (get_value() rechazó None)
5. Usuario puede seguir editando o presionar CANCELAR

---

## Retrocompatibilidad

- ✅ El parámetro `allow_negative` sigue siendo `False` por defecto
- ✅ Todas las pantallas que no usan alarmas no se ven afectadas
- ✅ El teclado de tiempo no cambia
- ✅ Terapia, heparina, limpieza, calibración no tienen cambios

---

## Reversibilidad

Si fuera necesario revertir solo este cambio:

```bash
git revert 078e9c1
```

Aunque esto también revertiría el cambio anterior (442d2c6), por lo que conviene usar:

```bash
git revert 442d2c6 078e9c1
```

Para revertir ambos commits de una vez.

---

**Commit:** 078e9c1  
**Fecha:** 2026-11-05  
**Archivos modificados:** 2  
**Estado:** ✅ Listo para pruebas
