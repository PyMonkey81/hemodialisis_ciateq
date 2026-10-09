# NIBP History Screen - Cleanup Fix

## Problema
Después de los cambios anteriores, apareció un rectángulo negro a la derecha de la gráfica. Era un widget vacío agregado a las columnas 2-3 del grid que pyqtgraph pintaba de negro.

## Solución
Eliminar el widget vacío y simplificar la configuración:

1. **Quitar widget vacío en columnas 2-3**
   - ❌ `main.addWidget(QWidget(), 1, 2, 1, 2)` → Eliminado
   - ✓ Las columnas 2-3 ahora son espacio puro del grid con stretch
   - ✓ El fondo blanco de `NibpHistoryScreen` es visible en ese espacio

2. **Simplificar ViewBox de FC**
   ```python
   self.vb_hr.setBackgroundColor(None)  # Más directo que (0, 0, 0, 0)
   ```
   - ✓ `self.vb_hr` permanece dentro de `self.plot_widget`
   - ✓ NO se agrega a ninguna columna del grid
   - ✓ Solo actualiza su geometría en `_fit_axes()`

3. **Simplificar configuración de ejes**
   ```python
   # Solo fijar ancho del eje derecho (el que muestra "lpm")
   dpi = max(self.logicalDpiX() / 96.0, 1.0)
   plot_item.getAxis("right").setWidth(int(46 * dpi))
   ```
   - ✓ Eliminadas configuraciones redundantes de left, bottom, viewbox
   - ✓ Eliminados setMinimumWidth/setMaximumWidth
   - ✓ Eliminado stretch factor interno de pyqtgraph

4. **Simplificar _fit_axes()**
   ```python
   def _fit_axes(self):
       """Actualiza la geometría del ViewBox de FC cuando cambia el tamaño."""
       self.vb_hr.setGeometry(self.plot_item.vb.sceneBoundingRect())
   ```
   - ✓ Solo actualiza geometría de ViewBox de FC
   - ✓ Se llama en showEvent() y al cambiar pantalla

## Cambios de Código

### Línea 106-108: Simplificar configuración de ejes
```python
# Fijar ancho del eje derecho según DPI
dpi = max(self.logicalDpiX() / 96.0, 1.0)
plot_item.getAxis("right").setWidth(int(46 * dpi))
```

### Línea 130: Cambiar fondo de ViewBox
```python
self.vb_hr.setBackgroundColor(None)  # Transparente: quita el fondo
```

### Línea 223-226: Eliminar widget vacío
```python
# ─── LAYOUT CON 4 COLUMNAS ────────────────────────────────────
# Gráfica en columnas 0-1 (mitad izquierda)
main.addWidget(plot_container, 1, 0, 1, 2)
# Columnas 2-3 vacías: no hay widget, solo espacio del grid con stretch
# (se eliminó main.addWidget(QWidget(), 1, 2, 1, 2))
```

### Línea 300-311: Simplificar _fit_axes()
```python
def _fit_axes(self):
    """Actualiza la geometría del ViewBox de FC cuando cambia el tamaño."""
    self.vb_hr.setGeometry(self.plot_item.vb.sceneBoundingRect())

def showEvent(self, event):
    """Recalcula geometría del ViewBox de FC al mostrar la pantalla."""
    super().showEvent(event)
    self._fit_axes()

def event(self, event):
    """Detecta cambio de pantalla (escala DPI) y actualiza ViewBox de FC."""
    if event.type() == QEvent.ScreenChangeInternal:
        self._fit_axes()
    return super().event(event)
```

## Resultado Final

| Escala | Resultado |
|--------|-----------|
| 100% | ✅ Gráfica a la izquierda, fondo blanco a la derecha, sin rectángulo negro |
| 125% | ✅ Gráfica a la izquierda, fondo blanco a la derecha, sin rectángulo negro |

**Estructura visual:**
```
┌─────────────────────────────────────────────────────────┐
│                  Encabezado (4 columnas)                │
├──────────────────────────┬──────────────────────────────┤
│  Gráfica                 │  Espacio blanco              │
│  (columnas 0-1)          │  (columnas 2-3)              │
├──────────────────────────┴──────────────────────────────┤
│  "Minutos de Terapia" (4 columnas)                      │
├─────────────────────────────────────────────────────────┤
│  Tabla (4 columnas)                                     │
├─────────────────────────────────────────────────────────┤
│  Total: N mediciones (4 columnas)                       │
└─────────────────────────────────────────────────────────┘
```

## Qué No Cambió
- ✓ Eje X, datos, colores, rangos
- ✓ "Minutos de Terapia" entre gráfica y tabla
- ✓ Protocolo NIBP, Art, Temp, Cond
- ✓ Leyenda sin duplicados
- ✓ Tabla completa
