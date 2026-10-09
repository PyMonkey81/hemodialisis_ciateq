# Fix: NIBP History Screen - Eje X y Disposición

## Problema Identificado

El eje inferior (bottom/X) quedó con ancho trabado tras aplicar `setWidth(None)` y `_updateWidth()` a todos los ejes (incluyendo bottom). Esto causó:
- Todas las etiquetas de minutos encimadas a la izquierda (se leía "2060")
- El título "Minutos de Terapia" dibujado fuera de la gráfica, encima del encabezado de la tabla
- No se distribuía el rango X (0..min_programados) correctamente en el ancho disponible

## Soluciones Implementadas

### 1. **Separar configuración del eje inferior** (línea ~95-120)

**ANTES:**
```python
for name in ("left", "bottom", "right"):
    axis.setWidth(None)
    axis._updateWidth()
```

**AHORA:**
```python
# Solo left y right: expansión automática de texto
for name in ("left", "right"):
    axis.setWidth(None)
    axis._updateWidth()

# Bottom: reparación específica
bottom = plot_item.getAxis("bottom")
bottom.fixedWidth = None
bottom.setMinimumWidth(0)
bottom.setMaximumWidth(16777215)
bottom.setStyle(autoExpandTextSpace=True, tickTextOffset=6)
bottom.setHeight(None)
bottom._updateHeight()
```

**Por qué:**
- `left` y `right` usan `setWidth(None)` para que se ajusten al ancho del texto (mmHg, lpm)
- `bottom` no puede usar `setWidth(None)` porque contiene múltiples marcas de minutos
- `bottom` necesita expandir horizontalmente para ocupar todo el ancho disponible
- `setMaximumWidth(16777215)` = infinito: permite que el eje se expanda sin restricciones

### 2. **Mover "Minutos de Terapia" a un QLabel** (línea ~95 y 220-223)

**ANTES:**
```python
plot_item.setLabel("bottom", "Minutos de Terapia", ...)  # Se dibuja fuera de la gráfica
```

**AHORA:**
```python
plot_item.setLabel("bottom", "", ...)  # Vacío en pyqtgraph
lbl_x_axis = QLabel("Minutos de Terapia")
lbl_x_axis.setStyleSheet("font-size: 13px; color: #0f172a; font-weight: normal;")
lbl_x_axis.setAlignment(Qt.AlignCenter)
main.addWidget(lbl_x_axis, 2, 0, 1, 2)  # Entre gráfica y tabla
```

**Grid Layout:**
- Fila 0: Encabezado (stretch=0)
- Fila 1: Gráfica (stretch=3, ocupa 60%)
- **Fila 2: Label "Minutos de Terapia" (stretch=0, auto)**
- Fila 3: Tabla (stretch=2, ocupa 40%)
- Fila 4: Footer (stretch=0)

### 3. **Actualizar `_fit_axes()` para excluir "bottom"** (línea ~299-305)

```python
def _fit_axes(self):
    """Recalcula el ancho de los ejes basado en el contenido del texto (solo left y right)."""
    for name in ("left", "right"):
        axis = self.plot_item.getAxis(name)
        axis.setWidth(None)
        axis._updateWidth()
    self.plot_item.update()
```

**Se ejecuta en:**
- `showEvent()`: Cuando se abre la pantalla
- `event(QEvent.ScreenChangeInternal)`: Al cambiar de monitor o escala DPI

### 4. **Rango X preservado**

El rango X sigue siendo `0..programmed_therapy_minutes` sin autoRange:
```python
plot_item.vb.setXRange(0, max(self.programmed_therapy_minutes, 1), padding=0)
```

Con terapia de 60 min, las marcas se distribuyen: **0, 15, 30, 45, 60** a lo largo del ancho disponible.

## Resultado a 100% y 125%

| Elemento | Ubicación |
|----------|-----------|
| **mmHg** | Dentro de la gráfica, eje izquierdo |
| **lpm** | Dentro de la gráfica, eje derecho |
| **Minutos de Terapia** | Centrado entre gráfica y tabla (NO sobre el encabezado) |
| **Eje X** | Ocupa todo el ancho de la gráfica, marcas distribuidas |
| **Tabla** | Debajo del label, sin solaparse con Art/Temp |
| **Leyenda** | Sin repeticiones (Sistólica, Diastólica, FC) |

## Cambios de Código

**Archivo:** `gui/therapy/nibp_history_screen.py`

1. **setup_ui()** (línea ~95-120):
   - Separar configuración de `left/right` vs `bottom`
   - Reparar eje inferior con parámetros específicos
   
2. **setup_ui()** (línea ~220-223):
   - Agregar QLabel con "Minutos de Terapia"
   - Insertar en grid entre gráfica y tabla
   
3. **setup_ui()** (línea ~237-241):
   - Actualizar índices de row en grid
   - Ajustar stretches de filas

4. **_fit_axes()** (línea ~299-305):
   - Cambiar loop de `("left", "bottom", "right")` a `("left", "right")`

## Validación

✅ Sin errores de sintaxis
✅ Colores no cambiados (mmHg rojo/azul, lpm verde)
✅ Datos no modificados
✅ Rango Y: 40–200 mmHg / 40–160 lpm (sin cambios)
✅ Rango X: 0–min_programados (sin autoRange)
