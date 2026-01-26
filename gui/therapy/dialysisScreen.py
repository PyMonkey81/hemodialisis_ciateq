# gui/therapy/dialysisScreen.py

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

# from logic.ktv_calculator import CalculadoraKtV # Comentado si no se usa directamente aún

try:
    from logic.calculos import calculo_ptm
except ImportError:
    # Función dummy por si falla el import
    def calculo_ptm(a, b, c, d): return 0.0
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
    def __init__(self, tag_name, value="0.0", units="", es_critico=False):
        super().__init__()              
        self.setFixedHeight(90)        
        self.tag_frame = QFrame()
    
        fondo = "#fffd96" if es_critico else "#ffffff"      
        
        # OJO: background-color del frame necesita selector específico o afectará a los labels hijos si no se cuida
        self.tag_frame.setStyleSheet(f"""
            QFrame {{
                background-color : {fondo};
                border: 2px solid #000000;
                border-radius: 10px;                     
            }}
        """)        
        # Layout principal del widget (necesario para contener el frame)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.tag_frame)

        # Layout dentro del frame
        frame_layout = QVBoxLayout(self.tag_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5) # Márgenes internos un poco más pequeños
        frame_layout.setSpacing(2)

        tag_text = f"{tag_name} ({units})" if units else tag_name
        
        # Título + unidad 
        self.lbl_tag_units = QLabel(tag_text)
        self.lbl_tag_units.setAlignment(Qt.AlignCenter)        
        self.lbl_tag_units.setStyleSheet("border: none; color: #333333; font-weight: bold; font-size: 20px;")
        
        # Valor grande
        self.lbl_value = QLabel(str(value))
        self.lbl_value.setAlignment(Qt.AlignCenter)       
        font_value = QFont("Arial", 24, QFont.Bold)
        self.lbl_value.setFont(font_value)
        self.lbl_value.setStyleSheet("border: none; color: #0078d7;")
        
        frame_layout.addWidget(self.lbl_tag_units)
        frame_layout.addWidget(self.lbl_value)

    def setValor(self, value):
        if isinstance(value, (int, float)):
            texto = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
        else:
            texto = str(value)
        self.lbl_value.setText(texto)


class dialysisScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        self.valores = valores_dict if valores_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1024, 600) # Ajustado un poco para probar, Valores originales (1536, 726) es el tamaño del stacked

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#0f172a"))
        self.setPalette(p)     

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)

        # === GRÁFICO IZQUIERDA ===
        if QTCHARTS_DISPONIBLE:
            chart = QChart()
            chart.setTitle("Presiones y UF")
            chart.setBackgroundBrush(QColor("#1e293b"))
            chart.setTitleBrush(QColor("#ffffff"))
            graf = QChartView(chart)
            # graf.setFixedSize(500, 300) # Dejar flexible a veces es mejor
            graf.setMinimumSize(400, 300)
        else:
            graf = QLabel("GRÁFICO\nDESACTIVADO")
            graf.setStyleSheet("background: #1e293b; color: #64748b; font-size: 24px;")
            graf.setAlignment(Qt.AlignCenter)
            graf.setMinimumSize(400, 300)

        layout.addWidget(graf, 0, 0, 4, 1) # Ocupa 4 filas

        #==========================================================================================
        # ============================= ÁREA DE BOTONES ===========================================
        #==========================================================================================
        botones_area = QFrame()
        # botones_area.setFixedSize(500, 380) # Mejor usar mínimos o sizePolicy
        botones_area.setMinimumWidth(400)
        botones_area.setStyleSheet("background: #FCFCFC; border-radius: 10px; border: 4px solid #1e293b;") 
        
        bl = QGridLayout(botones_area)
        bl.setSpacing(15)
        bl.setContentsMargins(20, 20, 20, 20)

        botones_config = [
            ("PAUSAR /\n REANUDAR", "#21dc7b"),
            ("SILENCIAR\n ALARMA", "#0f172a"),
            ("RESTABLECER\n ALARMA", "#0f172a"),
            ("BOLOS\n SALINO", "#0f172a"),
            ("MENÚ UF", "#0f172a"),
            ("HEPARINA", "#0f172a"),
        ]

        for i, (texto, color) in enumerate(botones_config):
            btn = QPushButton(texto)
            btn.setFixedHeight(70) # Un poco más pequeños para asegurar ajuste
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                              font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            row = i // 2
            col = i % 2
            bl.addWidget(btn, row, col)

        layout.addWidget(botones_area, 4, 0, 4, 1) # Ocupa las siguientes 4 filas

        # === VALORES DERECHA ===       
        self.pa = ValorSimple("Art", "0", "mmHg", es_critico=True)             #presión arterial
        self.pv = ValorSimple("Ven", "0", "mmHg", es_critico=True)             #presión venosa
        self.ptm = ValorSimple("PTM", "0", "mmHg", es_critico=True)            #presión transmembrana
        self.t_restante = ValorSimple("T. Restante", "00:00", "h:min")         #Tiempo restante de tratamiento
        self.t_transcurrido = ValorSimple("Tiempo UF", "00:00", "h:min")       #Tiempo transcurrido de tratamiento
        self.uf_objetivo = ValorSimple("UF Objetivo", "0.00", "L")             #Objetivo de ultra filtración
        self.uf_total = ValorSimple("UF Total", "0.00", "L")                   #Ultrafiltración total
        self.uf_tasa = ValorSimple("Tasa UF", "0", "mL/h")                     #Tasa de ultrafiltración
        self.conductividad = ValorSimple("Cond.", "0.0", "mS/cm")              #Valor medido de conductividad
        self.fsangre = ValorSimple("Qb", "0", "mL/min")                        #Flujo de sangre
        self.flujo_dial = ValorSimple("Qd", "0", "mL/min")                     #Flujo de dializante
        self.temp = ValorSimple("Temp.", "0.0", "°C")                          #Temperatura de dializante
        self.na = ValorSimple("Na+", "0.0", "mmol/L")                          #bicarbonato
        self.ktv = ValorSimple("Kt/V", "0.00", "")                             #Valor calculado de kt/V

        # Colocación en la grilla (Fila, Columna)
        # Columna 1 y 2 (la 0 es el gráfico/botones)
        
        layout.addWidget(self.pa, 0, 1)
        layout.addWidget(self.t_restante, 0, 2)
        
        layout.addWidget(self.pv, 1, 1)
        layout.addWidget(self.t_transcurrido, 1, 2)
        
        layout.addWidget(self.ptm, 2, 1)
        layout.addWidget(self.uf_objetivo, 2, 2)
        
        layout.addWidget(self.conductividad, 3, 1)
        layout.addWidget(self.uf_total, 3, 2)
        
        layout.addWidget(self.fsangre, 4, 1)
        layout.addWidget(self.uf_tasa, 4, 2)
        
        layout.addWidget(self.flujo_dial, 5, 1)
        layout.addWidget(self.na, 5, 2)
        
        layout.addWidget(self.temp, 6, 1)
        layout.addWidget(self.ktv, 6, 2) # Puse el KtV al lado de temp para aprovechar espacio

        # Espaciadores al final si sobran filas
        empty = QWidget()
        layout.addWidget(empty, 7, 1)


    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores

        pd_ef = self.valores.get("dialyPresIFProcessData", 0.0)  #Presión de dializante a la entrada del filtro
        pd_sf = self.valores.get("dialyPresOFProcessData", 0.0)  #Presión de dializante a la salida del filtro
        pa = self.valores.get("bloodArteryPressureData", 0.0)    #Presión Arterial
        pv = self.valores.get("bloodVenousPressureData", 0.0)    #Presión venosa

        # Calculamos PTM
        try:
            ptm_calculado = calculo_ptm(pd_ef, pd_sf, pa, pv)
        except Exception:
            ptm_calculado = 0.0

        clave_ptm = "CALC_PTM" 
        self.valores[clave_ptm] = ptm_calculado

        ktv_val = 0.00 
        self.ktv.setValor(ktv_val)

        # Mapeo de widgets
        mapeo = {
            "bloodArteryPressureData": self.pa,
            "bloodVenousPressureData": self.pv,
            
            # Usar la clave "CALC_PTM" 
            "CALC_PTM": self.ptm, 
            
            "dialyCondVariableData": self.conductividad,
            "bloodSpeedVariableData": self.fsangre,
            "dialyFlowControlOutput": self.flujo_dial,             
            "dialyTempIFProcessData": self.temp,
            "ultraFilterPumpSpeed": self.uf_tasa,
            
            # Asegúrate que estas claves existan en tu diccionario de entrada
            "UF Total": self.uf_total, 
            
            # REVISAR: ¿La heparina es realmente el objetivo de UF? 
            # Si no, cambia la clave o el widget.
            "heparineTherapyDosage": self.uf_objetivo, 
        }
        
        for tag, widget in mapeo.items():
            val = self.valores.get(tag, 0.0)
            widget.setValor(val)
