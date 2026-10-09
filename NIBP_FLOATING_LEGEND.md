# NIBP History Screen - Floating Legend

## Cambio Realizado
Reemplazar la leyenda del layout del PlotItem por una leyenda flotante dentro de la cuadrícula.

## Antes (Leyenda en Layout)
```python
# Una sola leyenda para todas las curvas
legend = self.plot_item.addLegend(offset=(10, 10))
```
- La leyenda ocupaba espacio en el layout interno de pyqtgraph
- Afectaba la posición y tamaño de la cuadrícula
- Podía interferir con los bordes de la gráfica

## Después (Leyenda Flotante)
```python
# Leyenda flotante dentro de la cuadrícula
legend = pg.LegendItem(offset=(8, 8))
legend.setParentItem(self.plot_item.vb)
legend.addItem(self.curve_sys, "Sistólica")
legend.addItem(self.curve_dia, "Diastólica")
legend.addItem(self.curve_hr, "FC (lpm)")
legend.setBrush(pg.mkBrush(255, 255, 255, 230))
legend.setPen(pg.mkPen("#cbd5e1"))
```

### Detalles de la Leyenda Flotante
- **Tipo:** `pg.LegendItem` (gráfico, no layout)
- **Posición:** Offset (8, 8) desde la esquina superior derecha del ViewBox
- **Padre:** `self.plot_item.vb` (dentro de la cuadrícula, no en el layout)
- **Contenido:** 3 entradas sin duplicados
  - Sistólica (#dc2626)
  - Diastólica (#2563eb)
  - FC (lpm) (#15803d)
- **Apariencia:**
  - Fondo: Blanco con 90% opacidad (230/255)
  - Borde: Gris claro (#cbd5e1)
  - Sin celda en el grid, solo dentro del gráfico

## Ventajas
✓ No afecta el layout de la pantalla
✓ No ocupa espacio en el grid
✓ La cuadrícula cierra en los 4 bordes sin que la leyenda interfiera
✓ Posicionable dentro del gráfico
✓ Aspecto más profesional

## Resultado Visual

```
A 100% y 125%:
┌────────────────────────────────────┐
│ 200 ┐                              │
│     │    ●   ●  [Sistólica  ─]    │
│ 150 ├──────────  [Diastólica ─]   │
│     │  ●       ● [FC (lpm)  ─]    │
│ 100 ├─────────── ─────────────    │
│     │●         ●                  │
│  50 │   ●       ●                 │
│     └─────────────────────────────│
│  0   5  10 15 20 25 30            │
└────────────────────────────────────┘
```

**Características:**
- Leyenda flotante en la esquina superior derecha
- Fondo blanco semitransparente
- Borde gris suave
- Dentro de la cuadrícula, sin salirse
- Cuadrícula cerrada en los 4 bordes

## Qué No Cambió
- ✓ Ejes: izquierdo (mmHg) y inferior (minutos)
- ✓ Rangos: Y [40-200], X [0-programmed_therapy_minutes]
- ✓ Curvas: Sistólica, Diastólica, FC con sus colores
- ✓ Tabla, botón Cerrar, layout de la pantalla
- ✓ Grid: 4 columnas, 5 filas con stretch factors

## Líneas de Código
- **Antes:** 255 líneas (leyenda en layout)
- **Después:** 261 líneas (+6 por leyenda flotante)

## Fichero
- ✅ [`gui/therapy/nibp_history_screen.py`](C:\Users\miguel.espinoza\Documents\Hemodialisis\hemodialisis_ciateq\gui\therapy\nibp_history_screen.py) - 261 líneas, sintaxis OK
