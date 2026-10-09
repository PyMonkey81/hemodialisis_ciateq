# Fix: NIBP History Screen - Espaciado de Ejes con DPI-aware

## Problema Identificado

A 100% escala: Hueco blanco entre el borde de la cuadrícula y los números del eje derecho (lpm).  
A 125% escala: El recuadro toca correctamente los números del eje derecho.

**Causa:** `setWidth(None)` / `_updateWidth()` hacía que el eje derecho reservara un ancho variable según la escala DPI.

## Solución Implementada

### 1. **Eliminar autoExpandTextSpace y métodos dinámicos** (línea ~95-107)

**ANTES:**
```python
axis.setStyle(autoExpandTextSpace=True, tickTextOffset=6)
axis.setWidth(None)
axis.setHeight(None)
axis._updateWidth()
axis._updateHeight()
```

**AHORA:**
```python
axis.setStyle(tickTextOffset=6)  # Sin autoExpandTextSpace
# Sin setWidth/setHeight/updates dinámicos
```

### 2. **Anchos fijos según DPI** (línea ~108-131)

```python
dpi = max(self.logicalDpiX() / 96.0, 1.0)

# Configurar limites de flexibilidad
for ax in (left, right, bottom, plot_item.vb):
    ax.setMinimumWidth(0)
    ax.setMaximumWidth(16777215)    # Infinito
    ax.setMinimumHeight(0)
    ax.setMaximumHeight(16777215)   # Infinito

# Anchos fijos escalados por DPI
left.setWidth(int(58 * dpi))        # Eje izquierdo: ~58px a 100%, ~72px a 125%
right.setWidth(int(46 * dpi))       # Eje derecho:  ~46px a 100%, ~57px a 125%
bottom.setHeight(int(34 * dpi))     # Eje inferior: ~34px a 100%, ~42px a 125%
```

**Valores en pixels:**
- **100% (DPI=1.0):** left=58px, right=46px, bottom=34px
- **125% (DPI=1.25):** left=72px, right=57px, bottom=42px

### 3. **Stretch factors del layout** (línea ~133-137)

```python
lay = plot_item.layout
lay.setColumnStretchFactor(0, 0)    # Columna 0 (eje izquierdo): sin estiramiento
lay.setColumnStretchFactor(1, 100)  # Columna 1 (viewbox): ocupa TODO el espacio disponible
lay.setColumnStretchFactor(2, 0)    # Columna 2 (eje derecho): sin estiramiento
lay.setHorizontalSpacing(0)         # Sin espacio entre columnas
```

**Resultado:**
```
[Eje izq] [<<<< VIEWBOX (todo el espacio disponible) >>>>] [Eje der]
  58px                                                        46px
```

### 4. **Recalcular geometría de ViewBoxes** (línea ~138-140)

```python
self.plot_item.vb.setGeometry(self.plot_item.vb.geometry())  # Aplica nuevo layout
self.vb_hr.setGeometry(self.plot_item.vb.sceneBoundingRect())  # FC se ajusta al viewbox
self.plot_item.update()
```

### 5. **Aplicar en dos momentos** (línea ~300-340)

#### `setup_ui()` (primera vez que se dibuja)
- Calcula `dpi` una sola vez
- Establece anchos fijos y stretch factors

#### `_fit_axes()` (se llama desde `showEvent()` y `event()`)
- Recalcula `dpi` por si la pantalla cambió (125% → 100%, cambio de monitor)
- Reaplica anchos y stretch factors

## Resultado a 100% y 125%

| Escala | Eje Izq | Viewbox (Cuadrícula) | Eje Der | Resultado |
|--------|---------|---------------------|---------|-----------|
| 100%   | 58px    | Todo disponible      | 46px    | ✓ Cuadrícula pegada a "lpm" sin hueco |
| 125%   | 72px    | Todo disponible      | 57px    | ✓ Cuadrícula pegada a "lpm" sin hueco |

## Cambios de Código

**Archivo:** `gui/therapy/nibp_history_screen.py`

1. **setup_ui()** (línea ~95-140):
   - Eliminar `autoExpandTextSpace` del loop general
   - Eliminar `setWidth(None)`, `setHeight(None)`, `_updateWidth()`, `_updateHeight()`
   - Agregar cálculo de DPI y anchos fijos
   - Configurar stretch factors del layout

2. **_fit_axes()** (línea ~308-334):
   - Calcular DPI dinámicamente
   - Reaplica los mismos anchos y stretch factors
   - Recalcula geometría de ViewBoxes

## Garantías

✅ Sin errores de sintaxis  
✅ Eje X no cambiado (0, 5, 10 ... 55 minutos bien distribuidos)  
✅ "Minutos de Terapia" sigue entre gráfica y tabla  
✅ Sin cambios en colores, datos, rangos Y ni protocolo NIBP  
✅ A 100% y 125%: cuadrícula pegada al eje derecho sin franja blanca  
✅ Art, Temp, Cond no afectados (están en otra pantalla)
