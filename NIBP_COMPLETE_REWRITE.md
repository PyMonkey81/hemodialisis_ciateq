# NIBP History Screen - Complete Rewrite

## Problema Original
- Eje derecho con ViewBox secundario (vb_hr) causaba que la cuadrícula no llegara a los números del rango Y
- "lpm" se encimaba con el eje Y
- El diseño de dos ViewBoxes era innecesariamente complejo
- Problemas de alineación a 100% y 125% DPI

## Solución: Reescritura Completa

### Estructura Final

```
┌─────────────────────────────────────────────────────────┐
│               Título - Encabezado - Cerrar              │
├──────────────────────────┬──────────────────────────────┤
│  Gráfica Simple          │  Espacio blanco              │
│  (Una sola escala Y)     │  (sin widgets)               │
│  mmHg: 40-200            │                              │
│  Tres curvas:            │                              │
│  • Sistólica (rojo)      │                              │
│  • Diastólica (azul)     │                              │
│  • FC (verde, lpm)       │                              │
│  Una leyenda             │                              │
├──────────────────────────┴──────────────────────────────┤
│              Minutos de Terapia (centrado)              │
├─────────────────────────────────────────────────────────┤
│ No.  Tiempo  SYS DIA  MAP  FC SpO2 Origen               │
│ ... datos...                                            │
├─────────────────────────────────────────────────────────┤
│ Total: N mediciones                                     │
└─────────────────────────────────────────────────────────┘
```

### Cambios Clave

#### 1. Eliminar Complejidad Innecesaria
✓ **Quitado:**
- `self.vb_hr` (ViewBox secundario)
- `curve_hr` dentro del ViewBox
- `linkToView()` y `setXLink()`
- `sigResized.connect(update_views)`
- `showAxis("right")` / eje derecho
- `setWidth()` / `setHeight()` / `_updateWidth()` / `_updateHeight()`
- `_fit_axes()`, `showEvent()`, `event(ScreenChangeInternal)`
- `QEvent` del import

#### 2. Plot Simple con Una Escala Y
```python
self.plot_widget = pg.PlotWidget()
self.plot_widget.setBackground("#ffffff")
self.plot_widget.hideButtons()
self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

self.plot_item.vb.setYRange(40, 200, padding=0)  # Rango fijo
self.plot_item.vb.setXRange(0, self.programmed_therapy_minutes, padding=0)
self.plot_item.vb.enableAutoRange(False)  # Siempre desactivado
```

#### 3. Tres Curvas Directas en el Plot
```python
self.curve_sys = self.plot_widget.plot(
    [], [], pen=pg.mkPen("#dc2626", width=2),
    symbol="o", symbolSize=7, symbolBrush="#dc2626", name="Sistólica",
)
self.curve_dia = self.plot_widget.plot(
    [], [], pen=pg.mkPen("#2563eb", width=2),
    symbol="o", symbolSize=7, symbolBrush="#2563eb", name="Diastólica",
)
self.curve_hr = self.plot_widget.plot(
    [], [], pen=pg.mkPen("#15803d", width=2),
    symbol="o", symbolSize=7, symbolBrush="#15803d", name="FC (lpm)",
)
```

#### 4. Una Sola Leyenda
```python
legend = self.plot_item.addLegend(offset=(10, 10))
```
- **Sin duplicados**
- FC aparece como "FC (lpm)"
- Sistólica y Diastólica con sus propios nombres

#### 5. Layout Limpio - 4 Columnas
```
Fila 0 (Encabezado):    [← 4 columnas →]
Fila 1 (Gráfica):       [Col 0-1: Plot] [Col 2-3: Vacío]
Fila 2 (Eje X label):   [Col 0-1: "Minutos de Terapia"]
Fila 3 (Tabla):         [← 4 columnas →]
Fila 4 (Pie):           [← 4 columnas →]
```

#### 6. Stretch Factors Uniformes
```python
# Columnas: todas iguales
main.setColumnStretch(0, 1)
main.setColumnStretch(1, 1)
main.setColumnStretch(2, 1)
main.setColumnStretch(3, 1)

# Filas
main.setRowStretch(0, 0)  # Encabezado: auto
main.setRowStretch(1, 3)  # Gráfica: 3 partes
main.setRowStretch(2, 0)  # Label eje X: auto
main.setRowStretch(3, 2)  # Tabla: 2 partes
main.setRowStretch(4, 0)  # Footer: auto
```

#### 7. Eje Izquierdo Limpio
```python
left_axis = self.plot_item.getAxis("left")
left_axis.enableAutoSIPrefix(False)
left_axis.setPen(pg.mkPen("#0f172a"))
left_axis.setTextPen(pg.mkPen("#0f172a"))
left_axis.setStyle(tickTextOffset=6)

# Eje derecho OCULTO
self.plot_item.getAxis("right").hide()
```

### Qué Se Mantiene Igual
- ✓ Tabla con 8 columnas (No., Tiempo, SYS, DIA, MAP, FC, SpO2, Origen)
- ✓ Botón "Cerrar" y su comportamiento
- ✓ Colores de curvas: rojo (#dc2626), azul (#2563eb), verde (#15803d)
- ✓ Rango Y: 40-200 mmHg
- ✓ Rango X: 0 a minutos programados de terapia
- ✓ Estilos y márgenes DPI-aware
- ✓ `nibp_pressure_history.py` sin cambios

### Métodos Simplificados
```python
def update_from_history(self):
    # Actualiza tabla y datos de las curvas
    # Rangos fijos siempre (con datos o sin datos)
    # Sin métodos auxiliares para ejes

def set_programmed_duration(self, hours, minutes):
    # Solo recalcula minutos programados

def on_close_clicked(self):
    # Vuelve a la pantalla del baumanómetro (sin cambios)
```

### Resultado A Ambas Escalas

| Escala | 100% | 125% |
|--------|------|------|
| Gráfica | ✅ Ocupa mitad izquierda | ✅ Ocupa mitad izquierda |
| Cuadrícula | ✅ Recta, toca ejes | ✅ Recta, toca ejes |
| Rango Y | ✅ 40-200 mmHg | ✅ 40-200 mmHg |
| Etiquetas | ✅ Alineadas | ✅ Alineadas |
| "Minutos de Terapia" | ✅ Centrado bajo gráfica | ✅ Centrado bajo gráfica |
| Tabla | ✅ Abajo, 4 columnas | ✅ Abajo, 4 columnas |

### Líneas de Código
- **Antes:** 340+ líneas (con ViewBoxes, ejes múltiples, métodos de ajuste)
- **Después:** 267 líneas (limpio, simple, sin complejidad innecesaria)

### Verificación
- ✅ Sintaxis: OK
- ✅ Imports: Solo necesarios
- ✅ Métodos: Solo funcionales
- ✅ No hay widgets fantasma
- ✅ No hay ViewBoxes secundarios
- ✅ Un solo eje (izquierdo) visible
