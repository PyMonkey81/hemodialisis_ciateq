# NIBP History Screen - Width Distribution Fix (Final)

## Problema
A escala 100% DPI, la cuadrícula quedaba corta dejando un hueco blanco antes del eje "lpm" (derecha). A 125% DPI la cuadrícula llegaba bien. El intento anterior de estirar la gráfica con stretch factors internos de pyqtgraph causó el problema.

## Solución
Cambiar la estructura del layout principal a 4 columnas en lugar de 2:
- Columnas 0-1: Gráfica (mitad izquierda, no se estira)
- Columnas 2-3: Vacías (reservan espacio, mismo stretch que 0-1)
- Filas 2-4: Tabla y pie en todas las 4 columnas

## Cambios Realizados

### 1. Layout Principal - 4 Columnas (línea 75)
```python
main.addLayout(header_layout, 0, 0, 1, 4)  # Encabezado en 4 columnas
```

### 2. Gráfica en Columnas 0-1 (línea 200)
```python
main.addWidget(plot_container, 1, 0, 1, 2)  # Columnas 0-1
main.addWidget(QWidget(), 1, 2, 1, 2)      # Columnas 2-3 vacías
```

### 3. Tabla y Pie en 4 Columnas (línea 205)
```python
main.addWidget(lbl_x_axis, 2, 0, 1, 4)   # "Minutos de Terapia"
main.addWidget(self.table, 3, 0, 1, 4)   # Tabla
main.addLayout(footer_layout, 4, 0, 1, 4) # Pie "Total: N"
```

### 4. Stretch Factors Iguales (línea 207)
```python
main.setColumnStretch(0, 1)  # Gráfica izq
main.setColumnStretch(1, 1)  # Gráfica dcha
main.setColumnStretch(2, 1)  # Vacío izq
main.setColumnStretch(3, 1)  # Vacío dcha
```

### 5. plot_widget SizePolicy (línea 82)
```python
self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
```
- **SIN** setMinimumWidth/setMaximumWidth fijos
- El ancho lo controlan las columnas 0-1 del grid

### 6. Configuración de Ejes Simplificada (línea 100-119)
```python
# Solo tickTextOffset, SIN autoExpandTextSpace
axis.setStyle(tickTextOffset=6)

# Anchos fijos escalados por DPI
for ax in (left, right, bottom):
    ax.setMinimumWidth(0)
    ax.setMaximumWidth(16777215)
    ax.setMinimumHeight(0)
    ax.setMaximumHeight(16777215)

left.setWidth(int(58 * dpi))
right.setWidth(int(46 * dpi))
bottom.setHeight(int(34 * dpi))

plot_item.vb.setMaximumWidth(16777215)

# Stretch factor solo en columna 1 (viewbox central)
lay = plot_item.layout
lay.setColumnStretchFactor(1, 100)
lay.setHorizontalSpacing(0)
```

### 7. Método _fit_axes() Limpio (línea 316)
```python
def _fit_axes(self):
    """Aplica anchos fijos según DPI sin métodos dinámicos."""
    dpi = max(self.logicalDpiX() / 96.0, 1.0)
    left = self.plot_item.getAxis("left")
    right = self.plot_item.getAxis("right")
    bottom = self.plot_item.getAxis("bottom")
    
    for ax in (left, right, bottom):
        ax.setMinimumWidth(0)
        ax.setMaximumWidth(16777215)
        ax.setMinimumHeight(0)
        ax.setMaximumHeight(16777215)
    
    left.setWidth(int(58 * dpi))
    right.setWidth(int(46 * dpi))
    bottom.setHeight(int(34 * dpi))
    
    lay = self.plot_item.layout
    lay.setColumnStretchFactor(1, 100)
    lay.setHorizontalSpacing(0)
    
    # Recalcular geometría del ViewBox de FC
    self.vb_hr.setGeometry(self.plot_item.vb.sceneBoundingRect())
    self.plot_item.update()
```

### 8. showEvent() - Copiar Geometría (línea 333)
```python
def showEvent(self, event):
    """Recalcula ejes al mostrar."""
    super().showEvent(event)
    self._fit_axes()
    # Copiar geometría del ViewBox de FC después de mostrar
    self.vb_hr.setGeometry(self.plot_item.vb.sceneBoundingRect())
```

## Qué NO Cambió
- ✓ Eje X: 0, 5, 10 … 55 minutos (correctamente distribuido)
- ✓ "Minutos de Terapia": entre gráfica y tabla (separado, no toca tabla)
- ✓ Colores: mmHg, lpm, Sistólica, Diastólica, FC
- ✓ Rangos Y: 40–200 mmHg (izq), 40–160 lpm (der)
- ✓ Leyenda: sin duplicados
- ✓ Datos y comportamiento de la gráfica
- ✓ Protocolo NIBP, Art, Temp, Cond

## Resultado Final

| Escala | Antes | Después |
|--------|-------|---------|
| 100% | Hueco blanco derecha | ✓ Cuadrícula pegada a lpm |
| 125% | OK | ✓ Cuadrícula pegada a lpm |

**A ambas escalas:** La cuadrícula ocupa solo la mitad izquierda del espacio disponible, su borde derecho queda pegado a los números del eje "lpm", y la tabla ocupa todo el ancho abajo.

## Razón Técnica
El layout principal ahora **controla** el ancho: 4 columnas con igual stretch (1 cada una). La gráfica solo crece hasta las columnas 0-1 (mitad del espacio útil). Las columnas 2-3 vacías **reservan** la otra mitad sin que la gráfica las ocupe.

Esto es más confiable que confiar en pyqtgraph para gestionar su ancho interno, que varía según DPI.
