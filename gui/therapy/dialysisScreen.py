# # gui/therapy/dialysisScreen.py

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from logic.ktv_calculator import CalculadoraKtV

try:
    from logic.calculos import calculo_ptm
except ImportError:
    # Función dummy por si falla el import para que no cierre la app
    def calculo_ptm(a, b, c, d): return 0.0

from core.variables_map import VARIABLES, TVAR_TO_GROUP

# === IMPORT SEGURO DE QTCHARTS ===
try:
    from PySide6.QtCharts import QChart, QChartView
    QTCHARTS_DISPONIBLE = True
except Exception as e:
    print(f"[INFO] QtCharts no disponible: {e}")
    QTCHARTS_DISPONIBLE = False
    QChart = None
    QChartView = None


class ValorSimple(QWidget):
    def __init__(self, titulo, valor="0.0", unidad="", es_critico=False):
        super().__init__()
        self.setFixedHeight(80)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")  #   <------------------ camio de color para tema
        lbl_titulo.setMinimumWidth(180)
        layout.addWidget(lbl_titulo)

        fondo = "#fffbeb" if es_critico else "#ffffff"
        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setStyleSheet(f"""
            background: {fondo};
            color: #000000;
            font-size: 44px;
            font-weight: bold;
            border-radius: 12px;
            border: 4px solid #1e293b;
            padding: 8px 16px;
        """)
        self.lbl_valor.setMinimumWidth(160)
        self.lbl_valor.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_valor)

        lbl_unidad = QLabel(unidad)
        lbl_unidad.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;") # <--------- cambio de color para tema
        layout.addWidget(lbl_unidad)
        layout.addStretch()

    def setValor(self, valor):
        # Manejo seguro de tipos
        if isinstance(valor, (float, int)):
            texto = f"{valor:.2f}"
        else:
            texto = str(valor)
        self.lbl_valor.setText(texto)


class dialysisScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        # Guardamos la referencia
        self.valores = valores_dict if valores_dict is not None else {}

        # Permitir que se expanda al tamaño del stacked
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1536, 726)

        # Fondo 
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#00594c")) #  #0f172a"
        self.setPalette(p)
        
        # --- CAMBIO 1: Eliminamos el QTimer interno ---
        # La actualización vendrá impulsada por el Main Window
        
        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(26, 15, 26, 15)

        # === GRÁFICO IZQUIERDA ===
        if QTCHARTS_DISPONIBLE:
            chart = QChart()
            chart.setTitle("Presiones y UF")
            chart.setBackgroundBrush(QColor("#1e293b"))
            chart.setTitleBrush(QColor("#ffffff")) # Título blanco para que se vea
            graf = QChartView(chart)
            graf.setFixedSize(500, 300)
        else:
            graf = QLabel("GRÁFICO\nDESACTIVADO")
            graf.setStyleSheet("background: #1e293b; color: #64748b; font-size: 24px;")
            graf.setAlignment(Qt.AlignCenter)
            graf.setFixedSize(500, 300)

        layout.addWidget(graf, 0, 0, 3, 1)
        #==========================================================================================
        # ============================= ÁREA DE BOTONES ===========================================
        #==========================================================================================
        botones_area = QFrame()
        botones_area.setFixedSize(500, 380)
        botones_area.setStyleSheet("background: #ffffff; border-radius: 10px; border: 4px solid #1e293b;")
        bl = QGridLayout(botones_area)
        bl.setSpacing(18)
        bl.setContentsMargins(25, 25, 25, 25)

        botones_config = [
            ("PAUSAR /\n REANUDAR", "#21dc7b"),
            ("SILENCIAR\n ALARMA", "#103db9"),
            ("RESTABLECER\n ALARMA", "#103db9"),
            ("BOLOS\n SALINO", "#103db9"),
            ("MENÚ UF", "#103db9"),
            ("ACCESO HEPARINA", "#103db9"),
        ]

        for i, (texto, color) in enumerate(botones_config):
            btn = QPushButton(texto)
            btn.setFixedHeight(80)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                              font-size: 19px; border-radius: 18px; border: 3px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            row = i // 2
            col = i % 2
            bl.addWidget(btn, row, col)

        layout.addWidget(botones_area, 5, 0, 5, 1)

        # === VALORES DERECHA ===
        self.pa = ValorSimple("P. Arterial (PA)", "0", "mmHg", es_critico=True)
        self.pv = ValorSimple("P. Venosa (PV)", "0", "mmHg", es_critico=True)
        self.ptm = ValorSimple("PTM", "0", "mmHg", es_critico=True)
        self.t_restante = ValorSimple("T. Restante", "00:00", "h:min")
        self.t_transcurrido = ValorSimple("Tiempo UF", "00:00", "h:min")
        self.uf_objetivo = ValorSimple("UF Objetivo", "0.00", "L")
        self.uf_total = ValorSimple("UF Total", "0.00", "L")
        self.uf_tasa = ValorSimple("Tasa UF", "0", "mL/h")
        self.conductividad = ValorSimple("Conductividad", "0.0", "mS/cm")
        self.fsangre = ValorSimple("Flujo Sangre", "0", "mL/min")
        self.flujo_dial = ValorSimple("Flujo Dializante", "0", "mL/min")
        self.temp = ValorSimple("Temperatura", "0.0", "°C")
        self.na = ValorSimple("Na+", "0.0", "mmol/L")
        self.ktv = ValorSimple("Kt/V", "0.00", "")

        layout.addWidget(self.pa, 0, 1);            layout.addWidget(self.t_restante, 0, 2)
        layout.addWidget(self.pv, 1, 1);            layout.addWidget(self.t_transcurrido, 1, 2)
        layout.addWidget(self.ptm, 2, 1);           layout.addWidget(self.uf_objetivo, 2, 2)
        layout.addWidget(self.conductividad, 3, 1); layout.addWidget(self.uf_total, 3, 2)
        layout.addWidget(self.fsangre, 4, 1);       layout.addWidget(self.uf_tasa, 4, 2)
        layout.addWidget(self.flujo_dial, 5, 1);    layout.addWidget(self.na, 5, 2)
        layout.addWidget(self.temp, 6, 1);          layout.addWidget(self.ktv, 7, 1)

        for i in range(8, 11):
            empty = QWidget()
            empty.setFixedHeight(80)
            layout.addWidget(empty, i, 1)
            layout.addWidget(empty, i, 2)

    # --- CAMBIO 2: Renombrado a actualizar_valores para coincidir con el Main ---
    def actualizar_valores(self, nuevos_valores):
        # Actualizamos la referencia local
        self.valores = nuevos_valores

        # === CAMBIO 3: Protección contra NoneTypes en cálculos ===
        # Usamos 0.0 como default si la llave no existe o el diccionario está vacío
        pd_ef = self.valores.get("dialyPresIFProcessData", 0.0)
        pd_sf = self.valores.get("dialyPresOFProcessData", 0.0)
        pa = self.valores.get("bloodArteryPressureData", 0.0)
        pv = self.valores.get("bloodVenousPressureData", 0.0)



        # Calculamos PTM seguro
        try:
            ptm_calculado = calculo_ptm(pd_ef, pd_sf, pa, pv)
        except Exception:
            ptm_calculado = 0.0

        clave_ptm = "CALC_PTM" 
        self.valores[clave_ptm] = ptm_calculado

        # self.ktv.setValor(CalculadoraKtV())
        ktv_val = 0.00 
        # Mapeo de widgets
        mapeo = {
            "bloodArteryPressureData": self.pa,
            "bloodVenousPressureData": self.pv,
            "Presión Transmembrana": self.ptm,
            "dialyCondVariableData": self.conductividad,
            "bloodSpeedVariableData": self.fsangre,
            "dialyFlowControlOutput": self.flujo_dial,             
            "dialyTempIFProcessData": self.temp,
            "ultraFilterPumpSpeed": self.uf_tasa,
            "UF Total": self.uf_total,
            "heparineTherapyDosage": self.uf_objetivo,
        }
        
        self.ktv.setValor(ktv_val)

        for tag, widget in mapeo.items():
            # Busamos por TAG. Si no existe, devuelve 0.0
            val = self.valores.get(tag, 0.0)
            widget.setValor(val)
