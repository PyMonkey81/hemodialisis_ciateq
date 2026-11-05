# Visualización del Teclado Numérico - Implementación de Signo Menos

## Escenario 1: `allow_negative=False` (Flujo de Sangre, Heparina, etc.)

```
┌─────────────────────────────────────────────────┐
│  Límite Superior: Flujo de Sangre (ml/min)      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────────────────────────────┐     │
│  │                  550                    │     │
│  └────────────────────────────────────────┘     │
│                                                 │
│  ┌─────────┬─────────┬─────────┐               │
│  │    1    │    2    │    3    │               │
│  └─────────┴─────────┴─────────┘               │
│  ┌─────────┬─────────┬─────────┐               │
│  │    4    │    5    │    6    │               │
│  └─────────┴─────────┴─────────┘               │
│  ┌─────────┬─────────┬─────────┐               │
│  │    7    │    8    │    9    │               │
│  └─────────┴─────────┴─────────┘               │
│  ┌─────────┬─────────┬─────────┐               │
│  │    .    │    0    │    ⌫    │  ✓ SIN SIGNO │
│  └─────────┴─────────┴─────────┘               │
│                                                 │
│  ┌─────────┬─────────────────────┐             │
│  │ CANCELAR│      ACEPTAR        │             │
│  └─────────┴─────────────────────┘             │
│                                                 │
│  Min: 0, Max: 600 → allow_negative=False       │
└─────────────────────────────────────────────────┘
```

**Comportamiento:**
- Presionar `.` agrega punto decimal
- Presionar números agrega dígitos
- Si intenta presionar `-`, no hace nada (rechazado)
- No hay botón +/−

---

## Escenario 2: `allow_negative=True` (Presión Arterial, Venosa)

### A. Teclado Inicial (Vacío)

```
┌─────────────────────────────────────────────────┐
│  Límite Inferior: Presión Arterial (mmHg)       │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────────────────────────────┐     │
│  │                                         │     │
│  └────────────────────────────────────────┘     │
│                                                 │
│  ┌─────────┬─────────┬─────────┐               │
│  │    1    │    2    │    3    │               │
│  └─────────┴─────────┴─────────┘               │
│  ┌─────────┬─────────┬─────────┐               │
│  │    4    │    5    │    6    │               │
│  └─────────┴─────────┴─────────┘               │
│  ┌─────────┬─────────┬─────────┐               │
│  │    7    │    8    │    9    │               │
│  └─────────┴─────────┴─────────┐               │
│  ┌─────────┬─────────┬─────────┬─────────┐     │
│  │   +/−   │    .    │    0    │    ⌫    │     │
│  └─────────┴─────────┴─────────┴─────────┘     │
│     NEW!   (replace .)                          │
│                                                 │
│  ┌─────────┬─────────────────────┐             │
│  │ CANCELAR│      ACEPTAR        │             │
│  └─────────┴─────────────────────┘             │
│                                                 │
│  Min: -100, Max: 400 → allow_negative=True      │
└─────────────────────────────────────────────────┘
```

### B. Usuario Presiona +/− (Vacío → "-")

```
┌─────────────────────────────────────────────────┐
│  Display: "-"                                   │
│  ┌────────────────────────────────────────┐     │
│  │  -                                      │     │
│  └────────────────────────────────────────┘     │
│                                                 │
│  [+/−] [.] [0] [⌫]                              │
│                                                 │
│  Estado: Vacío con signo (esperando dígitos)    │
└─────────────────────────────────────────────────┘
```

### C. Usuario Ingresa "-40.5"

Secuencia:
1. Presiona +/− → Display: "-"
2. Presiona 4 → Display: "-4"
3. Presiona 0 → Display: "-40"
4. Presiona . → Display: "-40."
5. Presiona 5 → Display: "-40.5"

```
┌─────────────────────────────────────────────────┐
│  Display: "-40.5"                               │
│  ┌────────────────────────────────────────┐     │
│  │  -40.5                                  │     │
│  └────────────────────────────────────────┘     │
│                                                 │
│  [+/−] [.] [0] [⌫]  ← Presionar +/− lo cambia  │
│                                                 │
│  Si presiona +/− ahora:                         │
│  Display cambia a: "40.5"                       │
│                                                 │
│  Si presiona +/− nuevamente:                    │
│  Display vuelve a: "-40.5"                      │
│                                                 │
│  get_value() → -40.5 (float)                    │
└─────────────────────────────────────────────────┘
```

### D. Usuario Presiona ACEPTAR

```
get_value() para "-40.5":
  1. Text: "-40.5"
  2. No está vacío ✓
  3. No es "-" ✓
  4. No es "." ✓
  5. No es "-." ✓
  6. No contiene "--" ✓
  7. Contiene punto → float("-40.5") = -40.5
  
Resultado: ACEPTA el diálogo, retorna -40.5
```

---

## Validación de Valores Inválidos

### Casos Rechazados (get_value() retorna None)

```
Input       │ Razón                    │ Acción
────────────┼──────────────────────────┼─────────────────────
""          │ Vacío                    │ get_value() = None
"-"         │ Solo signo               │ get_value() = None
"."         │ Solo punto               │ get_value() = None
"-."        │ Signo + punto sin dígito │ get_value() = None
"--"        │ Múltiples signos         │ get_value() = None
"1--2"      │ Signos en medio          │ IMPEDIDO por _add_digit()
"1.2.3"     │ Múltiples puntos         │ IMPEDIDO por _add_digit()
```

Cuando el usuario presiona ACEPTAR con un valor rechazado:
- `_on_accept_clicked()` llama a `get_value()`
- Si retorna `None`, **no cierra el diálogo**
- El usuario ve el teclado abierto y puede seguir editando o cancelar

---

## Casos Aceptados (get_value() retorna número)

```
Input       │ Tipo          │ Valor retornado
────────────┼───────────────┼──────────────────
"42"        │ int           │ 42
"-42"       │ int           │ -42
"3.14"      │ float         │ 3.14
"-3.14"     │ float         │ -3.14
"0"         │ int           │ 0
"-0"        │ int           │ 0 (Python maneja esto)
"0.0"       │ float         │ 0.0
"-0.5"      │ float         │ -0.5
```

---

## Configuración Automática por Variable

```python
# En gui/configuration/alarm_screen_config.py

def open_numpad(self, line_edit, tag, field):
    # Obtener límites de variables_map
    min_val, max_val = self.config_manager.get_limits(tag)
    
    # Decisión automática
    allow_negative = (min_val < 0)
    
    dialog = NumpadDialog(
        self,
        initial_value="",
        title=f"Límite {field.upper()} \n {tag}",
        allow_negative=allow_negative
    )
```

### Tabla de Decisión

```
Variable                │ Min  │ Max │ allow_negative
────────────────────────┼──────┼─────┼──────────────
Flujo Sanguíneo (SP)    │  0   │ 600 │ False
Flujo Sanguíneo (Calc)  │  0   │ 600 │ False
Flujo Dializante        │  0   │ 800 │ False
Ultrafiltración         │  0   │  3  │ False
Heparina (Dosis)        │  0   │ 100 │ False
Heparina (Bolo)         │  0   │ 10  │ False
Temperatura (mín)       │ 33   │ 42  │ False
Temperatura (máx)       │ 33   │ 42  │ False
Presión Arterial        │-100  │ 400 │ True  ← +/−
Presión Venosa          │ -50  │ 300 │ True  ← +/−
```

---

## Flujo de Guardado con Validación

```
Usuario presiona "Guardar Cambios"
        ↓
Para cada variable numérica:
        ├─ Leer min_v, max_v del UI
        ├─ Validación 1: min_v < max_v
        │   └─ Si falla: Advertencia, NO guarda
        │
        ├─ Validación 2: min_v en limites permitidos
        │   ├─ default_min, default_max = variables_map
        │   ├─ Si min_v < default_min o min_v > default_max
        │   └─ Si falla: Advertencia específica, NO guarda
        │
        ├─ Validación 3: max_v en limites permitidos
        │   ├─ default_min, default_max = variables_map
        │   ├─ Si max_v < default_min o max_v > default_max
        │   └─ Si falla: Advertencia específica, NO guarda
        │
        └─ Todo OK: Guardar en config
        
Guardadas todas las variables
        ↓
Mensaje de éxito
```

### Ejemplo de Validación

Presión Arterial (límites permitidos: -100 a 400):

```
Usuario intenta guardar:
├─ Límite inferior: -150  ← FUERA DE RANGO
├─ Límite superior: 300
│
Resultado:
└─ Advertencia: "Límite inferior fuera de rango permitido (-100 - 400)."
   → No guarda el archivo
   → El usuario puede corregir o cancelar
```

---

## Cambios en el Layout

### Antes (4 botones en fila 3)
```
1 2 3       Fila 0
4 5 6       Fila 1
7 8 9       Fila 2
. 0 ⌫       Fila 3 (3 botones)
```

### Después con allow_negative=False
```
1 2 3       Fila 0
4 5 6       Fila 1
7 8 9       Fila 2
. 0 ⌫       Fila 3 (3 botones, SIN CAMBIO)
```

### Después con allow_negative=True
```
1 2 3           Fila 0
4 5 6           Fila 1
7 8 9           Fila 2
+/− . 0 ⌫       Fila 3 (4 botones, punto movido)
```

**Ventaja:** El punto se mueve pero no encima ninguna tecla, todas mantienen su tamaño (90x90).

---

## Resumen de Cambios

```
NumpadDialog:
✓ Parámetro allow_negative añadido (defecto: False)
✓ Layout dinámico: +/− solo si allow_negative=True
✓ Botón +/− ocupa columna 0, punto en columna 1
✓ _add_digit('-') rechaza si allow_negative=False
✓ _toggle_sign() pone/quita signo al inicio
✓ get_value() rechaza valores inválidos (retorna None)
✓ _on_accept_clicked() valida antes de cerrar

AlarmScreenConfig:
✓ Detección automática: allow_negative = (min < 0)
✓ Validación al guardar: valores en limites permitidos
✓ Advertencias descriptivas si hay errores
✓ No guarda si hay valores inválidos

Ningún cambio:
✓ Terapia, heparina, limpieza, calibración, manual
✓ Teclado de tiempo
✓ Serial, perfiles, conexiones
✓ Resto del código
```

**Implementación:** `442d2c6`  
**Documentación:** `NUMPAD_NEGATIVE_IMPLEMENTATION.md`  
**Fecha:** 2026-11-05 10:10:08
