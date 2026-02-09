# gui/therapy/dialysisScreen.py

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque 

# from logic.ktv_calculator import CalculadoraKtV # Comentado si no se usa directamente aún

try:
    from logic.calculos import calculo_ptm
except ImportError:
    # Función dummy por si falla el import
    def calculo_ptm(a, b, c, d): return 0.0
try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

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
        self.parent = parent  # ← guardar referencia al padre
        self.valores = valores_dict if valores_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1024, 600) # Ajustado un poco para probar, Valores originales (1536, 726) es el tamaño del stacked

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#0f172a"))
        self.setPalette(p)     

        self.history_length = 600
        nan_list = [np.nan] * self.history_length
        self.ven_pressure_y = deque(nan_list, maxlen=self.history_length)
        self.art_pressure_y = deque(nan_list, maxlen=self.history_length)
        self.x_relativa = np.arange(-self.history_length + 1, 1, dtype=np.float32)


        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)   

        # ──────────────────────────────
        # Área de gráficos (hereda estilos globales)
        # ──────────────────────────────
        self.graphics_area = QWidget()
        self.graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.grid_graphics = QGridLayout(self.graphics_area) # <-- self.grid_graphics ahora está en self.graphics_area
        self.grid_graphics.setSpacing(15)
        self.grid_graphics.setContentsMargins(5, 5, 5, 5)
        
        tick_font = QFont()
        tick_font.setPixelSize(12)

        # Gráfica
        self.plot_pressure = pg.PlotWidget()
        self.plot_pressure.setBackground("#e0e0e0")
        self.plot_pressure.setTitle('<span style="font-size: 11pt; color: black;">Presión Ven vs. Art</span>')
        self.plot_pressure.setLabel('left', '<span style="font-size: 9pt; color: black;">Presión (mmHg)</span>')
        self.plot_pressure.setLabel('bottom','<span style="font-size: 9pt; color: #000000;">Tiempo (s)</span>')
        self.plot_pressure.addLegend()

        self.curve_ven_pressure = self.plot_pressure.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Presión Venosa")
        self.curve_art_pressure = self.plot_pressure.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Presión Arterial")
        
        self.plot_pressure.getAxis('bottom').setStyle(tickFont=tick_font)
        self.plot_pressure.getAxis('left').setStyle(tickFont=tick_font)
        self.plot_pressure.getAxis('bottom').setStyle(tickTextOffset=5)
        self.plot_pressure.getAxis('left').setStyle(tickTextOffset=5)

        self.grid_graphics.addWidget(self.plot_pressure, 0, 0, 1, 1) 
        layout.addWidget(self.graphics_area, 0, 0, 4, 1) # <-- ¡Esta es la línea corregida!


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
            ("INICIAR", "#21dc7b", self.start_treatment),
            ("PAUSAR", "#ad8413", self.pause_treatment),
            ("DETENER", "#DD2911", self.stop_treatment),
            ("MENÚ TERAPIA", "#0f172a", self.parent.mostrar_pantalla_cfg_terapia),
            ("MENÚ PACIENTE", "#0f172a",  self.parent.mostrar_pantalla_paciente),
            ("CEBADO", "#0f172a", self.start_priming),
        ]

        for i, (texto, color, func ) in enumerate(botones_config):
            btn = QPushButton(texto)
            btn.setFixedHeight(70) # Un poco más pequeños para asegurar ajuste
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                              font-size: 16px; border-radius: 15px; border: 3px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(func)
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

        self.ven_pressure_y.append(pv)
        self.art_pressure_y.append(pa)

        self.curve_ven_pressure.setData(self.x_relativa, list(self.ven_pressure_y))
        self.curve_art_pressure.setData(self.x_relativa, list(self.art_pressure_y))
        self.plot_pressure.setXRange(-self.history_length + 1, 0)

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
    
    def write_setpoint(self, tag, value):
        try:
            # Lógica para enviar el setpoint (treatmentModeSelection)
            texto = value 
            valor = float(texto)
            print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
            target_group = -1
            target_id = -1
            found = False
            
            for group_key, variables_in_group in VARIABLES.items():                
                if isinstance(variables_in_group, dict): 
                    for var_id, info in variables_in_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found: break 
            
            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial'):                      
                        self.parent_window.serial.escribir_double(target_group, target_id, valor)
                    else:
                        print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
                else:
                    print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
            else:
                print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")
            
            self.setFocus()

        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")

    def start_treatment(self):
        """Inicia el proceso de diálisis"""
        self.write_setpoint("treatmentModeSelection", 0.0) # Hemodialisis
        self.write_setpoint("treatmentModeSelection", 1.0) # Hemodiafiltracion
        self.write_setpoint("treatmentModeSelection", 2.0) # UltraFiltración

        

    def pause_treatment(self):
        """
        Docstring for pause_treatment
        
        :param self: pone en pausa el tratamiento
        """

    def stop_treatment(self):
        """
        Docstring for stop_treatment
        
        :param self: Detiene el tratamiento
        """
    def start_priming(self):
        """
        Docstring for start_priming
        
        :param self: iniciar cebado
        """

    
