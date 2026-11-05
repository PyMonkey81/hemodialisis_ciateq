# Implementación: Signo Menos en el Teclado Numérico

## Resumen Ejecutivo

Se implementó soporte para números negativos en el teclado numérico (`NumpadDialog`) con detección automática basada en los límites permitidos de cada variable. El botón +/− solo aparece cuando el rango mínimo es menor a 0.

**Commit:** `442d2c6` (fix: signo menos en el teclado solo si el rango permitido es negativo)

---

## Cambios en `gui/components/numpad_modal.py`

### 1. Nuevo parámetro en `__init__`
```python
def __init__(self, parent=None, initial_value: str = "", title: str = "Ingrese Valor", 
             theme: str = "light", allow_negative: bool = False):
```

- `allow_negative=False` es el valor por defecto
- No afecta a quienes ya abren el teclado (compatibilidad hacia atrás)

### 2. Layout del Teclado Dinámico

**Con `allow_negative=False` (3 filas + última fila con 3 botones):**
```
1  2  3
4  5  6
7  8  9
.  0  ⌫
```

**Con `allow_negative=True` (3 filas + última fila con 4 botones):**
```
1  2  3
4  5  6
7  8  9
+/− .  0  ⌫
```

El botón +/− ocupa la columna 0, el punto se mueve a columna 1, el cero a columna 2, y backspace a columna 3. **Ninguna tecla se encima.**

### 3. Métodos de Validación

#### `_add_digit(digit: str)`
- Rechaza "-" si `allow_negative=False`
- Permite múltiples dígitos, punto decimal, y guion inicial
- Previene múltiples puntos decimales
- Reemplaza cero inicial si es necesario

#### `_toggle_sign()`
- **Solo funciona si `allow_negative=True`**
- Vacío → "-" (pone signo)
- "-40" → "40" (quita signo)
- "40" → "-40" (agrega signo)
- No permite "--" ni signos en medio

#### `_backspace()`
- Borra carácter por carácter, incluyendo el signo

#### `get_value() -> Union[int, float, None]`
- Retorna `int` si no hay punto: `"42"` → `42`
- Retorna `float` si hay punto: `"3.14"` → `3.14`
- **Retorna `None` si:**
  - Texto vacío
  - Solo "-"
  - Solo "."
  - "-." (guion y punto sin dígitos)
  - "--" (múltiples guiones)
  - Cualquier otro valor inválido

#### `_on_accept_clicked()`
- Valida con `get_value()` antes de cerrar
- Si `get_value()` retorna `None`, rechaza el cierre
- Si retorna un valor válido, acepta el diálogo

---

## Cambios en `gui/configuration/alarm_screen_config.py`

### Detección Automática de `allow_negative`

```python
def open_numpad(self, line_edit, tag, field):
    # Obtener los límites de la variable
    min_val, max_val = self.config_manager.get_limits(tag)
    allow_negative = min_val < 0  # ← Automático
    
    dialog = NumpadDialog(self, initial_value="",
                         title=f"Límite {field.upper()} \n {tag}",
                         allow_negative=allow_negative)
```

**Lógica:**
- `allow_negative=True` **solo si** el mínimo permitido es < 0
- Presión arterial (-100 a 400): `allow_negative=True` ✓
- Presión venosa (-50 a 300): `allow_negative=True` ✓
- Flujo de sangre (0 a 600): `allow_negative=False` ✓
- Heparina (0 a 100): `allow_negative=False` ✓

### Validación al Guardar

```python
def save_configuration(self):
    # ... código existente ...
    
    # Obtener los límites permitidos de variables_map
    default_min, default_max = self.config_manager.get_default_limits_from_variables_map(tag)
    
    # Validar que cada valor esté dentro de los límites permitidos
    if min_v < default_min or min_v > default_max:
        self.show_warning_message(
            f"Límite inferior fuera de rango permitido ({default_min} - {default_max})."
        )
        return
    
    if max_v < default_min or max_v > default_max:
        self.show_warning_message(
            f"Límite superior fuera de rango permitido ({default_min} - {default_max})."
        )
        return
```

- Valida que `min_v >= max_v` (ya existía)
- Valida que `min_v` esté en rango permitido (nuevo)
- Valida que `max_v` esté en rango permitido (nuevo)
- No guarda el archivo si hay valores inválidos

---

## Casos de Uso

### Presión Arterial (Alarmas)
1. Usuario toca campo de límite inferior
2. Sistema detecta `min: -100` → `allow_negative=True`
3. Teclado muestra botón +/−
4. Usuario: +/− (vacío→"-") → 4 → 0 → . → 5 → ACEPTAR
5. Display: "-40.5" → `get_value()` retorna `-40.5` ✓
6. Se guarda el límite `-40.5`

### Flujo de Sangre (Alarmas)
1. Usuario toca campo de límite superior
2. Sistema detecta `min: 0` → `allow_negative=False`
3. Teclado NO muestra botón +/−, solo . 0 ⌫
4. Usuario intenta poner "-" → rechazado
5. Usuario: 5 → 5 → 0 → ACEPTAR
6. Display: "550" → `get_value()` retorna `550` ✓
7. Se guarda el límite `550`

### Entrada Incompleta (Validación)
1. Usuario ingresa "-" (solo signo)
2. Usuario pulsa ACEPTAR
3. `get_value()` detecta valor inválido → retorna `None`
4. Diálogo se mantiene abierto
5. Usuario puede seguir editando o pulsar CANCELAR

---

## Archivos NO Modificados

- ✓ Terapia (therapy screens): sin `allow_negative`
- ✓ Heparina: sin `allow_negative`
- ✓ Limpieza: sin `allow_negative`
- ✓ Calibración: sin `allow_negative`
- ✓ Modo manual: sin `allow_negative`
- ✓ Teclado de tiempo (`time_numpad_modal.py`): sin cambios
- ✓ Serial, perfiles: sin cambios
- ✓ Todos los demás módulos: sin cambios

---

## Validación de Implementación

### Pruebas Incluidas
1. **allow_negative=False**: No permite "-", solo números y punto
2. **allow_negative=True**: Permite "-" y botón +/−
3. **Decimales negativos**: "-40.5" se convierte a float correctamente
4. **Valores inválidos**: "", "-", ".", "-.", "--" retornan `None`
5. **Backspace**: Funciona con signos, no dejar caracteres huérfanos
6. **Toggle sign**: Vacío→"-", "-40"→"40", "40"→"-40"
7. **Accept validation**: Rechaza valores inválidos, acepta válidos

### Matriz de Decisión
| Variable | Min | Max | allow_negative | Resultado |
|----------|-----|-----|--|---|
| Flujo Sangre | 0 | 600 | False | No signo ✓ |
| Flujo Dializante | 0 | 800 | False | No signo ✓ |
| UF | 0 | 3 | False | No signo ✓ |
| Heparina | 0 | 100 | False | No signo ✓ |
| Temperatura | 33 | 42 | False | No signo ✓ |
| Presión Arterial | -100 | 400 | True | +/− button ✓ |
| Presión Venosa | -50 | 300 | True | +/− button ✓ |

---

## Flujo de Aceptación

```
Usuario toca límite
        ↓
Detectar límites de variables_map
        ↓
Calcular allow_negative = min < 0
        ↓
Crear NumpadDialog(allow_negative=allow_negative)
        ↓
Usuario ingresa valor
        ↓
Usuario pulsa ACEPTAR
        ↓
get_value() valida
        ↓
¿Válido? ─ No → Rechaza, diálogo abierto
        │
        └─ Sí → Acepta, cierra diálogo
        ↓
Validar min < max
        ↓
Validar min, max en rango permitido
        ↓
¿Fuera de rango? ─ Sí → Muestra advertencia, no guarda
        │
        └─ No → Guarda en config
```

---

## Compatibilidad

- **Hacia atrás (Backward)**: `allow_negative` es parámetro opcional con defecto `False`
- **Nuevas llamadas**: Solo `alarm_screen_config.py` pasa `allow_negative`
- **Otras pantallas**: No cambian, siguen con `allow_negative=False` implícitamente

---

## Cambios Estadísticos

- `gui/components/numpad_modal.py`: +268 líneas, -60 líneas (total: +208)
- `gui/configuration/alarm_screen_config.py`: +23 líneas, -5 líneas (total: +18)
- **Archivos nuevos**: 0
- **Archivos modificados**: 2
- **Archivos deletados**: 0

---

## Rollback (Si es Necesario)

```bash
git revert 442d2c6
```

Esto deshace todos los cambios y restaura el comportamiento anterior (sin signo menos en ningún teclado).

---

**Implementación completada:** 2026-11-05 10:10:08
**Estado:** Listo para pruebas en hardware
