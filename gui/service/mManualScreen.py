# #gui/service/mManualScr.py
# #Ejecución del autotest de la máquina y visualización de resultados.
# #control manual de los elementos de actuadores, bombas, válvulas

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QDoubleValidator

from core.variables_map import VARIABLES, TVAR_TO_GROUP
from gui.components.LED import LED
from gui.components.ToggleSwitch import ToggleSwitch


class ValveCard(QFrame):
    def __init__(self, codigo, descripcion, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                border: 1px solid #334155;
                }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>{codigo}</b><br><span style='font-size:18px; color:#cbd5e1;'>{descripcion}</span>")
        lbl_info.setStyleSheet("color: #ffffff; font-size: 18px; border:none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=60, height=30)

        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(self.toggle)


class mManualScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        # Guarda la referencia
        self.parent_window = parent  
        self.valores = valores_dict if valores_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFixedSize(1536, 726)
        
        # Fondo
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#0f172a"))
        self.setPalette(p)

        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ==================================================================
        #          AREA 1: CONTROL DE BOMBAS
        # ==================================================================
       
        self.control_area = QWidget()
        self.control_area.setFixedSize(1300, 480) 
        grid = QGridLayout(self.control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)

        # Estilos comunes
        style_lbl = "color: #ffffff; font-size: 18px; font-weight: bold;"
        style_unit = "color: #94a3b8; font-size: 16px;"
        style_input = """
            QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
                        font-weight: bold; border-radius: 5px; padding: 2px; }
        """
        style_btn = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """        

        # ----------------------------------------------------------------------
        # FILA 0: BOMBA DE SANGRE
        # ----------------------------------------------------------------------
        lbl_sangre = QLabel("B. Sangre")
        lbl_sangre.setStyleSheet(style_lbl)
        grid.addWidget(lbl_sangre, 0, 0)

        self.toggle_sangre = ToggleSwitch(width=70, height=35)
        self.toggle_sangre.toggled.connect(
            lambda chk: self.manejar_bomba_doble("bloodPumpStartButton", "bloodPumpStopButton", chk)
        )
        grid.addWidget(self.toggle_sangre, 0, 1)

        btn_rev = QPushButton("REV")
        btn_rev.setFixedSize(60, 35)
        btn_rev.setStyleSheet(style_btn)
        btn_rev.pressed.connect(lambda: self.escribir_comando("bloodPumpREVButton", True))
        btn_rev.released.connect(lambda: self.escribir_comando("bloodPumpREVButton", False))
        
        btn_fwd = QPushButton("FWD")
        btn_fwd.setFixedSize(60, 35)
        btn_fwd.setStyleSheet(style_btn)
        btn_fwd.pressed.connect(lambda: self.escribir_comando("bloodPumpFWDButton", True))
        btn_fwd.released.connect(lambda: self.escribir_comando("bloodPumpFWDButton", False))

        grid.addWidget(btn_rev, 0, 2)
        grid.addWidget(btn_fwd, 0, 3)

        lbl_flujo = QLabel("Flujo:")
        lbl_flujo.setStyleSheet(style_lbl)
        grid.addWidget(lbl_flujo, 0, 4)

        self.input_flujo_sangre = QLineEdit("0")
        self.input_flujo_sangre.setFixedSize(80, 35)
        self.input_flujo_sangre.setAlignment(Qt.AlignCenter)
        self.input_flujo_sangre.setStyleSheet(style_input)
        self.input_flujo_sangre.setValidator(QDoubleValidator(0, 600, 1))
        self.input_flujo_sangre.editingFinished.connect(
            lambda: self.escribir_setpoint("bloodFlowControlSetPoint", self.input_flujo_sangre)
        )
        grid.addWidget(self.input_flujo_sangre, 0, 5)

        lbl_u1 = QLabel("ml/min")
        lbl_u1.setStyleSheet(style_unit)
        grid.addWidget(lbl_u1, 0, 6)

        lbl_vel = QLabel("Vel:")
        lbl_vel.setStyleSheet(style_lbl)
        grid.addWidget(lbl_vel, 0, 7)

        self.lbl_velocidad_val = QLabel("0")
        self.lbl_velocidad_val.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        grid.addWidget(self.lbl_velocidad_val, 0, 8)

        lbl_u2 = QLabel("rpm")
        lbl_u2.setStyleSheet(style_unit)
        grid.addWidget(lbl_u2, 0, 9)

        # TIEMPOS
        lbl_tiempo = QLabel("Tiempo Terapia:")
        lbl_tiempo.setStyleSheet(style_lbl)
        grid.addWidget(lbl_tiempo, 0, 10)

        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0,0,0,0)
        
        self.input_horas = QLineEdit("0")
        self.input_horas.setFixedSize(50, 35)
        self.input_horas.setStyleSheet(style_input)
        self.input_horas.editingFinished.connect(lambda: self.escribir_setpoint("heparineTherapyHours", self.input_horas))
        
        self.input_mins = QLineEdit("0")
        self.input_mins.setFixedSize(50, 35)
        self.input_mins.setStyleSheet(style_input)
        self.input_mins.editingFinished.connect(lambda: self.escribir_setpoint("heparineTherapyMinutes", self.input_mins))

        time_layout.addWidget(self.input_horas)
        time_layout.addWidget(QLabel("h"))
        time_layout.addWidget(self.input_mins)
        time_layout.addWidget(QLabel("m"))
        
        grid.addWidget(time_widget, 0, 11, 1, 3)

        # ----------------------------------------------------------------------
        # FILA 1: BOMBA DE HEPARINA
        # ----------------------------------------------------------------------
        lbl_bHeparina = QLabel("B. Heparina")
        lbl_bHeparina.setStyleSheet(style_lbl)
        grid.addWidget(lbl_bHeparina, 1, 0)

        self.toggle_heparina = ToggleSwitch(width=70, height=35)
        self.toggle_heparina.toggled.connect(lambda chk: self.manejar_bomba_doble("heparinePumpsStartButton", "heparinePumpsStopButton",chk))
        grid.addWidget(self.toggle_heparina, 1, 1)

        btn_homeHep = QPushButton("HOME")
        btn_homeHep.setFixedSize(70, 35)
        btn_homeHep.setStyleSheet(style_btn)
        btn_homeHep.pressed.connect(lambda: self.escribir_comando("heparinePumpHomePosition", True))
        btn_homeHep.released.connect(lambda: self.escribir_comando("heparinePumpHomePosition", False)) # Changed pressed to released for latching if needed
        
        btn_rev_hep = QPushButton("REV")
        btn_rev_hep.setFixedSize(70,35)
        btn_rev_hep.setStyleSheet(style_btn)
        btn_rev_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpREVButton",True))
        btn_rev_hep.released.connect(lambda: self.escribir_comando("heparinePumpREVButton", False))

        btn_pause_hep = QPushButton("PAUSE")
        btn_pause_hep.setFixedSize(70,35)
        btn_pause_hep.setStyleSheet(style_btn)
        btn_pause_hep.pressed.connect(lambda: self.escribir_comando("heparineOperPauseResume",True))
        btn_pause_hep.released.connect(lambda: self.escribir_comando("heparineOperPauseResume", False))

        btn_fwd_hep = QPushButton("FWD")
        btn_fwd_hep.setFixedSize(70,35)
        btn_fwd_hep.setStyleSheet(style_btn)
        btn_fwd_hep.pressed.connect(lambda: self.escribir_comando("heparinePumpFWDButton",True))
        btn_fwd_hep.released.connect(lambda: self.escribir_comando("heparinePumpFWDButton", False))

        grid.addWidget(btn_homeHep, 1, 2)
        grid.addWidget(btn_rev_hep, 1, 3)
        grid.addWidget(btn_pause_hep, 1, 4)
        grid.addWidget(btn_fwd_hep, 1, 5)

        lbl_indHeparina = QLabel("Heparina")
        lbl_indHeparina.setStyleSheet(style_lbl)
        grid.addWidget(lbl_indHeparina, 1,6)
        
        self.indHeparinaDosage = QLabel("0.0")
        self.indHeparinaDosage.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.indHeparinaDosage.setFixedSize(100,35)
        grid.addWidget(self.indHeparinaDosage,1,7)
        
        lbl_unit_hep = QLabel("ml")
        lbl_unit_hep.setStyleSheet(style_unit)
        lbl_unit_hep.setFixedSize(100,35)
        grid.addWidget(lbl_unit_hep,1,8)

        # ----------------------------------------------------------------------
        # FILA 2: B. DIALIZANTE
        # ----------------------------------------------------------------------
        lbl_dializante = QLabel("B. Dializante")
        lbl_dializante.setStyleSheet(style_lbl)
        grid.addWidget(lbl_dializante, 2, 0)

        self.toggle_dializante = ToggleSwitch(width=70, height=35)
        self.toggle_dializante.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyserPumpStartButton","dialyserPumpStopButton",chk))
        grid.addWidget(self.toggle_dializante, 2,1)

        self.lbl_indSDializante = QLabel("0.0")
        self.lbl_indSDializante.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_indSDializante.setFixedSize(100,35)
        grid.addWidget(self.lbl_indSDializante, 2,2)

        lbl_unit_indSdializante = QLabel("%")
        lbl_unit_indSdializante.setStyleSheet(style_unit)
        lbl_unit_indSdializante.setFixedSize(100,35)
        grid.addWidget(lbl_unit_indSdializante, 2, 3)

        lbl_e_tOpBD = QLabel("Tiempo Op.")
        lbl_e_tOpBD.setStyleSheet(style_lbl)
        lbl_e_tOpBD.setFixedSize(100,35)
        grid.addWidget(lbl_e_tOpBD, 2, 4)

        self.lbl_tiempo_OpBD = QLineEdit("00:00")
        self.lbl_tiempo_OpBD.setStyleSheet(style_input)
        self.lbl_tiempo_OpBD.setFixedSize(100,35)
        grid.addWidget(self.lbl_tiempo_OpBD,2,5)

        lbl_e_tRestBD = QLabel("T. Restante")
        lbl_e_tRestBD.setStyleSheet(style_lbl)
        lbl_e_tRestBD.setFixedSize(100,35)
        grid.addWidget(lbl_e_tRestBD,2,6)

        self.lbl_tiempo_RestBD = QLabel("00:00")
        self.lbl_tiempo_RestBD.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_tiempo_RestBD.setFixedSize(100,40)
        grid.addWidget(self.lbl_tiempo_RestBD,2,7)


        
         # ----------------------------------------------------------------------
        # FILA 3: B. Ultra Filtrado
        # ----------------------------------------------------------------------
        lbl_ultrafiltado = QLabel("B. UF")
        lbl_ultrafiltado.setStyleSheet(style_lbl)
        grid.addWidget(lbl_ultrafiltado,3,0)

        self.toggle_uf = ToggleSwitch(width=70, height=35)
        self.toggle_uf.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyUltraFPumpStartButt,dialyUltraFPumpStoptButt",chk))
        grid.addWidget(self.toggle_uf,3,1)

        self.lbl_indUF = QLabel("0.0")
        self.lbl_indUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_indUF.setFixedSize(100,35)
        grid.addWidget(self.lbl_indUF, 3, 2)

        lbl_unit_indUF = QLabel("L/h")
        lbl_unit_indUF.setStyleSheet(style_unit)
        lbl_unit_indUF.setFixedSize(100, 35)
        grid.addWidget(lbl_unit_indUF, 3,3)

        lbl_e_tOpBUF = QLabel("Tiempo Op.")
        lbl_e_tOpBUF.setStyleSheet(style_lbl)
        lbl_e_tOpBUF.setFixedSize(100, 35)
        grid.addWidget(lbl_e_tOpBUF, 3, 4)

        self.lbl_tiempo_opBUF = QLineEdit("00,00")
        self.lbl_tiempo_opBUF.setStyleSheet(style_input)
        self.lbl_tiempo_opBUF.setFixedSize(100, 35)
        grid.addWidget(self.lbl_tiempo_opBUF, 3, 5)

        lbl_e_tRestBUF = QLabel("T. Restante")
        lbl_e_tRestBUF.setStyleSheet(style_lbl)
        lbl_e_tRestBUF.setFixedSize(100, 35)
        grid.addWidget(lbl_e_tRestBUF, 3, 6)

        self.lbl_tiempo_RestBUF = QLabel("00:00")
        self.lbl_tiempo_RestBUF.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_tiempo_RestBUF.setFixedSize(100, 35)
        grid.addWidget(self.lbl_tiempo_RestBUF, 3, 7)

        # ----------------------------------------------------------------------
        # FILA 4: B. Bicarbonato Na+
        # ----------------------------------------------------------------------
        lbl_bicarbonato = QLabel("B. Na+")
        lbl_bicarbonato.setStyleSheet(style_lbl)
        lbl_bicarbonato.setFixedSize(100, 35)
        grid.addWidget(lbl_bicarbonato, 4, 0)

        self.toggle_Na = ToggleSwitch(width=70, height=35)
        self.toggle_Na.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyBicarbonPumpStartButt,dialyBicarbonPumpStopButt",chk))
        grid.addWidget(self.toggle_Na, 4, 1)

        self.lbl_indBNa = QLabel("0.0")
        self.lbl_indBNa.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_indBNa.setFixedSize(100, 35)
        grid.addWidget(self.lbl_indBNa, 4, 2)

        lbl_unit_indBNa = QLabel("%")
        lbl_unit_indBNa.setStyleSheet(style_unit)
        lbl_unit_indBNa.setFixedSize(100, 35)
        grid.addWidget(lbl_unit_indBNa, 4, 3)
                                                                                                                                                                                                                                                                         
        # ----------------------------------------------------------------------
        # FILA 5: B. Acido Citrico
        # ----------------------------------------------------------------------
        lbl_acidocitrico = QLabel("B. A. Citrico")
        lbl_acidocitrico.setStyleSheet(style_lbl)
        lbl_acidocitrico.setFixedSize(100, 35)
        grid.addWidget(lbl_acidocitrico, 5, 0)

        self.toggle_acidocitrico = ToggleSwitch(width=70, height=35)
        self.toggle_acidocitrico.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyCitricAcPumpStartButt,dialyCitricAcPumpStopButt",chk))
        grid.addWidget(self.toggle_acidocitrico, 5, 1)

        self.lbl_indBAC = QLabel("0.0")
        self.lbl_indBAC.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_indBAC.setFixedSize(100, 35)
        grid.addWidget(self.lbl_indBAC, 5, 2)

        lbl_unit_indBAC = QLabel("%")
        lbl_unit_indBAC.setStyleSheet(style_unit)
        lbl_unit_indBAC.setFixedSize(100, 35)
        grid.addWidget(lbl_unit_indBAC, 5, 3)

        # ----------------------------------------------------------------------
        # FILA 6: B. Purga de Aire
        # ----------------------------------------------------------------------
        lbl_purga = QLabel("B. Purga")
        lbl_purga.setStyleSheet(style_lbl)
        lbl_purga.setFixedSize(100, 35)
        grid.addWidget(lbl_purga, 6, 0)

        self.toggle_purga = ToggleSwitch(width=70, height=35)
        self.toggle_purga.toggled.connect(lambda chk: self.manejar_bomba_doble("dialyPurgePumpStartButt,dialyPurgePumpStopButt",chk))
        grid.addWidget(self.toggle_purga, 6, 1)

        self.lbl_indPurga = QLabel("0.0")
        self.lbl_indPurga.setStyleSheet("color: #22d3ee; font-size: 20px; font-weight: bold;")
        self.lbl_indPurga.setFixedSize(100, 35)
        grid.addWidget(self.lbl_indPurga, 6, 2)

        lbl_unit_indPurga = QLabel("%")
        lbl_unit_indPurga.setStyleSheet(style_unit)
        lbl_unit_indPurga.setFixedSize(100, 35)
        grid.addWidget(lbl_unit_indBAC, 6, 3)


        # ----------------------------------------------------------------------
        # FILAS 3 a 7: BOMBAS SIMPLES
        # ----------------------------------------------------------------------
        bombas_simples = [
            #(3, "B. UltraF", "dialyUltraFPumpStartButt", "dialyUltraFPumpStoptButt"), 
            #(4, "B. Bicarbonato", "dialyBicarbonPumpStartButt", "dialyBicarbonPumpStopButt"),
            #(5, "B. Acido Cítrico", "dialyCitricAcPumpStartButt", "dialyCitricAcPumpStopButt"),
            #(6, "B. Purga Aire", "dialyPurgePumpStartButt", "dialyPurgePumpStopButt"),
            (7, "C. Balance", "dialiserBalChambStrButt", "dialiserBalChambStpButt"),
        ]

        self.toggles_simples = {} 

        for row_idx, nombre, tag_start, tag_stop in bombas_simples:
            lbl = QLabel(nombre)
            lbl.setStyleSheet(style_lbl)
            grid.addWidget(lbl, row_idx, 0)

            toggle = ToggleSwitch(width=70, height=35)
            toggle.toggled.connect(
                lambda chk, ts=tag_start, tp=tag_stop: self.manejar_bomba_doble(ts, tp, chk)
            )
            self.toggles_simples[tag_start] = toggle
            grid.addWidget(toggle, row_idx, 1)

        # ----------------------------------------------------------------------
        # FILA 8: DOSIS HEPARINA (Input)
        # ----------------------------------------------------------------------
        lbl_dosis = QLabel("Dosis Hep.")
        lbl_dosis.setStyleSheet(style_lbl)
        grid.addWidget(lbl_dosis, 8, 0)

        self.input_dosis_hep = QLineEdit("0.0")
        self.input_dosis_hep.setFixedSize(100, 35)
        self.input_dosis_hep.setAlignment(Qt.AlignCenter)
        self.input_dosis_hep.setStyleSheet(style_input)
        self.input_dosis_hep.setValidator(QDoubleValidator(0.0, 50.0, 1))
        self.input_dosis_hep.editingFinished.connect(
            lambda: self.escribir_setpoint("heparineTherapyDosage", self.input_dosis_hep)
        )
        grid.addWidget(self.input_dosis_hep, 8, 1)

        lbl_udosis = QLabel("ml/h")
        lbl_udosis.setStyleSheet(style_unit)
        grid.addWidget(lbl_udosis, 8, 2)

        layout.addWidget(self.control_area, 0, 0)

        # ==================================================================
        #          AREA 2: INDICADORES LED
        # ==================================================================
        self.ind_area = QWidget()
        self.ind_area.setFixedSize(180,726)
        grid_ind_area = QGridLayout(self.ind_area)
        grid_ind_area.setSpacing(10)
        grid_ind_area.setContentsMargins(10, 10,10, 10)

        led_nombres = ["B. Sangre","B. Dializante","B. Heparina","B. UltraF","Purga de\n aire","C.Balance","A. sangre","C.Deaereación","Fin de\n ciclos","Protec.\n Resist.","S.Dializante","Nivel de\ntanque"]   
        self.leds = []
        for i, nombre in enumerate(led_nombres):
            lbl = QLabel(nombre)
            lbl.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid_ind_area.addWidget(lbl, i, 0)

            led = LED()
            led.setFixedSize(45, 45)
            grid_ind_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.leds.append(led)

        layout.addWidget(self.ind_area, 0, 1, 2, 1)

        # ==============================================================================================
        # AREA 3: VÁLVULAS
        # ==============================================================================================
        self.ctrl_valvulas = QWidget()
        self.ctrl_valvulas.setFixedSize(1300,240)
        layout_ctrl_valvulas = QHBoxLayout(self.ctrl_valvulas) 
        layout_ctrl_valvulas.setContentsMargins(0, 0, 0, 0)
        layout_ctrl_valvulas.setSpacing(10)
        
        self.container_mop = QFrame()
        self.container_mop.setFixedSize(110,240)
        self.container_mop.setStyleSheet("background-color: #0f172a; border-radius:8px; border: 2px solid #334155;")
        layout_mop = QVBoxLayout(self.container_mop) 
       
        lbl_modo = QLabel("Modo de \n Op.")
        lbl_modo.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 18px;")
        lbl_modo.setAlignment(Qt.AlignCenter)
        
        self.toggle_modo = ToggleSwitch(width=60, height=30, active_color="#facc15") 
        self.toggle_modo.toggled.connect(lambda checked: self.escribir_comando("dialyCircuitElementsOpSel", checked))

        layout_mop.addStretch()
        layout_mop.addWidget(lbl_modo)
        layout_mop.setSpacing(10)
        layout_mop.addWidget(self.toggle_modo, 0, Qt.AlignCenter)
        layout_mop.addStretch()
        
        layout_ctrl_valvulas.addWidget(self.container_mop)

        self.container_val = QWidget()
        grid_valvulas_area = QGridLayout(self.container_val)
        grid_valvulas_area.setContentsMargins(0, 0, 0, 0)
        grid_valvulas_area.setSpacing(10)
       
        valvulas_tag = [
            (0, 0, "dialyInputFilterCutButt", "SV_24 E. Filtro UF"),
            (0, 1, "dialyOutputFilterCutButt", "SV_25 S. Filtro UF"),
            (0, 2, "dialyBypassFilterButt", "SV_26 Bypass UF"),
            (0, 3, "dialyWaterInletValveButt", "SV_27 E. Agua"),
            (1, 0, "dialyRecirculatValveButt", "SV_39 Recirculación"),
            (1, 1, "dialyAirVentSepChambButt", "SV_43 Venteo CS Aire"),
            (1, 2, "dialyHotChambValveButt", "SV_50 C. Caliente"),
            (1, 3, "dialyWaterDrainValveButt", "SV_30 Drenaje"),
        ]
        self.valvulas_map = {}

        for r, c, tag, desc in valvulas_tag:
            parts = desc.split(" ",1)
            codigo = parts[0]
            texto = parts[1] if len(parts) > 1 else ""

            card = ValveCard(codigo, texto)
            self.valvulas_map[tag] = card
            grid_valvulas_area.addWidget(card, r, c)
            card.toggle.toggled.connect(lambda checked, t=tag: self.escribir_comando(t, checked))

        layout_ctrl_valvulas.addWidget(self.container_val)
        layout.addWidget(self.ctrl_valvulas, 1, 0)    

    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores
        
        # ACTUALIZAR LEDS (Tags verificados)
        variables_leds = [
            "bloodPumpStartButton",       
            "dialyserPumpStartButton",    
            "heparinePumpsStartButton",   
            "dialyUltraFPumpStartButt",   
            "dialyPurgePumpStartButt",    
            "dialiserBalChambStrButt",    
            "airBubbleInBloodDetected",   
            "dialyDeaerChamLevSwitch",    
            "dialyBalanceChambCycleEnd",  
            "watterTankHeaterProtect",    
            "bloodInDialyCircDetected",   
            "dialyTankHiLevelSwitch"      
        ]
        for i, led in enumerate(self.leds):
            if i < len(variables_leds):
                nombre_var = variables_leds[i]
                valor = self.valores.get(nombre_var, 0.0)
                estado = 'on' if valor > 0 else 'off'
                if led.state != estado:
                    led.set_state(estado)
        
        # ACTUALIZAR VÁLVULAS
        for tag, card in self.valvulas_map.items():
            val = self.valores.get(tag, 0.0)
            nuevo_estado = True if val > 0 else False
            if card.toggle.is_checked() != nuevo_estado:
                if hasattr(card.toggle, "setChecked"):
                    card.toggle.setChecked(nuevo_estado)
        
        # ACTUALIZAR INDICADORES NUMÉRICOS
        vel_sangre = self.valores.get("bloodSpeedVariableData", 0.0)
        self.lbl_velocidad_val.setText(f"{vel_sangre:.0f}")
        
        val_heparina = self.valores.get("heparineCurrentDosage", 0.0)
        self.indHeparinaDosage.setText(f"{val_heparina:.1f}")

        # ACTUALIZAR TOGGLES DE BOMBAS (CORREGIDO EL ERROR DE SINTAXIS)
        act_toogle_sangre = self.valores.get("bloodPumpStartButton", 0.0)
        if hasattr(self.toggle_sangre, "setChecked"):
            self.toggle_sangre.setChecked(act_toogle_sangre > 0)

        act_toogle_heparina = self.valores.get("heparinePumpsStartButton", 0.0)
        if hasattr(self.toggle_heparina, "setChecked"):
            self.toggle_heparina.setChecked(act_toogle_heparina > 0)

        act_toggle_dializante = self.valores.get("dialyserPumpStartButton", 0.0)
        if hasattr(self.toggle_dializante, "setChecked"):
            self.toggle_dializante.setChecked(act_toggle_dializante > 0)
        
        act_toggle_modo = self.valores.get("dialyCircuitElementsOpSel", 0.0)
        if hasattr(self.toggle_modo, "setChecked"):
            self.toggle_modo.setChecked(act_toggle_modo > 0)
        

        # 5. ACTUALIZAR TOGGLES SIMPLES
        for tag_start, toggle in self.toggles_simples.items():
            val = self.valores.get(tag_start, 0.0)
            if hasattr(toggle, "setChecked"):
                toggle.setChecked(val > 0)

        # 6. ACTUALIZAR INPUT DOSIS (Solo si no tiene foco)
        if hasattr(self, 'dosis_heparina_edit'):
            val_dosis = self.valores.get("heparineTherapyDosage", 0.0)
            if not self.dosis_heparina_edit.hasFocus():
                self.dosis_heparina_edit.setText(f"{val_dosis:.1f}")

    def manejar_bomba_doble(self, tag_start, tag_stop, activado):
        if activado:
            print(f"[BOMBA] Arrancando {tag_start}")
            self.escribir_comando(tag_start, True)
            self.escribir_comando(tag_stop, False) 
        else:
            print(f"[BOMBA] Deteniendo {tag_stop}")
            self.escribir_comando(tag_stop, True) 
            self.escribir_comando(tag_start, False)

    def escribir_setpoint(self, tag, widget_input):
        try:
            texto = widget_input.text().replace(',', '.')
            valor = float(texto)
            print(f"[SETPOINT] Escribiendo {tag} = {valor}")
            
            found = False
            for grupo in [0x02, 0x03, 0x04, 0x05, 0x06]:
                if grupo in VARIABLES:
                    for id_var, info in VARIABLES[grupo].items():
                        if info["tag"] == tag:
                            if self.parent_window and hasattr(self.parent_window, 'serial'):
                                self.parent_window.serial.escribir_double(id_var, valor)
                            found = True
                            break
                if found: break
            
            if not found:
                print(f"[ERROR] No se encontró ID para tag analógico {tag}")

        except ValueError:
            print("[ERROR] Valor numérico inválido")

    def escribir_comando(self, tag, estado):
        print(f"[COMANDO] Usuario cambió {tag} a {estado}")
        direccion = -1
        if 0x01 in VARIABLES:
            for id_var, info in VARIABLES[0x01].items():
                if info["tag"] == tag:
                    direccion = id_var
                    break
        
        if direccion != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial'):
                if self.parent_window.serial.conectado:
                    print(f" -> Enviando: Addr {direccion} Val {estado}")
                    self.parent_window.serial.escribir_booleano(direccion, estado)
                else:
                    print(" -> Error: Serial no conectado")
        else:
            print(f" -> Error: No se encontró ID para el tag '{tag}'")
