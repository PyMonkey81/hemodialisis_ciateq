#gui/service/pPruebasScreen


import logging
from PySide6.QtWidgets import QWidget, QFrame,QVBoxLayout, QGridLayout,QHBoxLayout, QLabel, QPushButton, QMessageBox,QSizePolicy
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor, QFont
from core.variables_map import VARIABLES
from gui.components.LED import LED
from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit, DoubleToggleBox
from gui.components.ui_components import LabeledParameterWidget, LabeledTimeInput
from logic.calculos import (
    convertir_flujo_a_ciclos,
    convertir_ciclos_a_flujo,
    convertir_litros_h_a_ml_min,
    convertir_ml_min_a_litros_h,
    calculo_ptm
)
import pyqtgraph as pg 
import numpy as np 
from collections import deque 


logger = logging.getLogger(__name__)


class testScr(QWidget):
    """
    Pantalla de pruebas de funcionamiento de máquina de hemodiálisis
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent_window = parent
        self.valores = parent.valores if parent else {}

        self._write_hold_off = {}

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#0f172a"))
        self.setPalette(p)     

        self.history_length = 600
        nan_list = [np.nan] * self.history_length
        self.temp_dialysate_EF_y = deque(nan_list, maxlen=self.history_length)
        self.temp_dialysate_SF_y = deque(nan_list, maxlen=self.history_length)
        self.temp_tank_y         = deque(nan_list, maxlen=self.history_length)

        self.cond_ef_y = deque(nan_list, maxlen=self.history_length)
        self.cond_sf_y = deque(nan_list, maxlen=self.history_length)
        self.x_relativa = np.arange(-self.history_length + 1, 1, dtype=np.float32)

        self.setup_ui()
        logger.info("Módulo de control de pruebas inicializado (v1.0.0)")
    
    def setup_ui(self):
        """
        Intefaz de pruebas de máquina
        """
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        style_lbl = "color: #000000; font-size: 18px; font-weight: bold;"
        style_lbl_indicator = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        style_btn = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """
        style_unit = "color: #94a3b8; font-size: 16px;"
        style_input = """
            background: #FFFFE5; color: #000000; font-size: 18px; font-weight: bold;
            border: 2px solid #000000; border-radius: 5px; padding: 4px;
        """


        #=============================================================
        # CONTROL AREA 0 
        #==============================================================

        self.control_area = QWidget(self)
        self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid = QGridLayout(self.control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)

        lbl_io_flow_cb = QLabel("QCb(ml/min)")
        lbl_io_flow_cb.setStyleSheet(style_lbl)
        lbl_io_flow_cb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_io_flow_cb, 0,0,1, 2)

        self.io_flow_cb = ClickableLineEdit("0.0")
        self.io_flow_cb.setStyleSheet(style_input)
        self.io_flow_cb.setAlignment(Qt.AlignCenter)
        self.io_flow_cb.setReadOnly(True)
        self.io_flow_cb.clicked.connect(self._handle_flow_cb_input)               
        grid.addWidget(self.io_flow_cb, 0,2)

        lbl_io_flow_blood = QLabel("Qb (ml/min)")
        lbl_io_flow_blood.setStyleSheet(style_lbl)
        lbl_io_flow_blood.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_io_flow_blood, 1, 0, 1, 2)

        self.io_flow_blood = ClickableLineEdit("0.0")
        self.io_flow_blood.setStyleSheet(style_input)
        self.io_flow_blood.setAlignment(Qt.AlignCenter)
        self.io_flow_blood.setReadOnly(True)
        self.io_flow_blood.clicked.connect(
            lambda: self.open_numpad("bloodFlowControlSetPoint", self.io_flow_blood, "Flujo de sangre(ml/min)")
        )  
        grid.addWidget(self.io_flow_blood, 1, 2)

        lbl_io_flow_uf = QLabel("UF (ml/min)")
        lbl_io_flow_uf.setStyleSheet(style_lbl)
        lbl_io_flow_uf.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_io_flow_uf, 2, 0, 1, 2)

        self.io_flow_uf = ClickableLineEdit("0.0")
        self.io_flow_uf.setStyleSheet(style_input)
        self.io_flow_uf.setAlignment(Qt.AlignCenter)
        self.io_flow_uf.setReadOnly(True)
        self.io_flow_uf.clicked.connect(self._handle_flow_uf_input)
        grid.addWidget(self.io_flow_uf,2,2)

        lbl_io_cond = QLabel("Cond. (mS/cm)")
        lbl_io_cond.setStyleSheet(style_lbl)
        lbl_io_cond.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_io_cond, 3, 0, 1, 2)

        self.io_sp_cond = ClickableLineEdit("0.0")
        self.io_sp_cond.setStyleSheet(style_input)
        self.io_sp_cond.setAlignment(Qt.AlignCenter)
        self.io_sp_cond.setReadOnly(True)
        self.io_sp_cond.clicked.connect(
            lambda: self.open_numpad("dialyCondControlSetPoint", self.io_sp_cond, "Conductividad (mS/cm)")
        )
        grid.addWidget(self.io_sp_cond,3,2)

        lbl_io_temp = QLabel("Temp. D. (°C)")
        lbl_io_temp.setStyleSheet(style_lbl)
        lbl_io_temp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_io_temp, 4, 0, 1, 2 )

        self.io_sp_temp = ClickableLineEdit("0.0")
        self.io_sp_temp.setStyleSheet(style_input)
        self.io_sp_temp.setAlignment(Qt.AlignCenter)
        self.io_sp_temp.setReadOnly(True)
        self.io_sp_temp.clicked.connect(
            lambda: self.open_numpad("dialyTempControlSetPoint", self.io_sp_temp, "Temperatura (°C)")
        )
        grid.addWidget(self.io_sp_temp,4,2)

        lbl_cycles_act = QLabel("No. Ciclos CB:")
        lbl_cycles_act.setStyleSheet(style_lbl)
        lbl_cycles_act.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_cycles_act, 0, 3)

        self.ind_cycles_chamber = QLabel("0")
        self.ind_cycles_chamber.setFixedWidth(100)
        self.ind_cycles_chamber.setStyleSheet(style_lbl_indicator)
        self.ind_cycles_chamber.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.ind_cycles_chamber, 0, 4)

        lbl_temp_dialysate_ef = QLabel("T. Dial. EF (°C)")
        lbl_temp_dialysate_ef.setStyleSheet(style_lbl)
        lbl_temp_dialysate_ef.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_temp_dialysate_ef, 0, 6)

        self.l_temp_dialysate_ef = QLabel("0.0")
        self.l_temp_dialysate_ef.setStyleSheet(style_lbl_indicator)
        self.l_temp_dialysate_ef.setFixedSize(100, 35)
        self.l_temp_dialysate_ef.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.l_temp_dialysate_ef, 0, 7)

        lbl_temp_dialysate_sf = QLabel("T. Dial. SF (°C)")
        lbl_temp_dialysate_sf.setStyleSheet(style_lbl)
        lbl_temp_dialysate_sf.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_temp_dialysate_sf, 1, 6)

        self.l_temp_dialysate_sf = QLabel("0.0")
        self.l_temp_dialysate_sf.setStyleSheet(style_lbl_indicator)
        self.l_temp_dialysate_sf.setFixedSize(100, 35)
        self.l_temp_dialysate_sf.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.l_temp_dialysate_sf, 1, 7)


        lbl_temp_tank = QLabel("T.Tanque (°C)")
        lbl_temp_tank.setStyleSheet(style_lbl)
        lbl_temp_tank.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_temp_tank, 2, 6)

        self.l_temp_tank = QLabel("0.0")
        self.l_temp_tank.setStyleSheet(style_lbl_indicator)
        self.l_temp_tank.setFixedSize(100, 35)
        self.l_temp_tank.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.l_temp_tank, 2, 7)

        lbl_cond_ef = QLabel("Cond. EF")
        lbl_cond_ef.setStyleSheet(style_lbl)
        # lbl_cond_ef.setFixedSize(100, 35)
        lbl_cond_ef.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_cond_ef, 3,6)

        self.l_cond_ef = QLabel("0.0")
        self.l_cond_ef.setStyleSheet(style_lbl_indicator)
        self.l_cond_ef.setFixedSize(100, 35)
        self.l_cond_ef.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.l_cond_ef, 3, 7)

        lbl_cond_sf = QLabel("Cond. SF")
        lbl_cond_sf.setStyleSheet(style_lbl)
        # lbl_cond_ef.setFixedSize(100, 35)
        lbl_cond_sf.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl_cond_sf, 4,6)

        self.l_cond_sf = QLabel("0.0")
        self.l_cond_sf.setStyleSheet(style_lbl_indicator)
        self.l_cond_sf.setFixedSize(100, 35)
        self.l_cond_sf.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.l_cond_sf, 4, 7)

        #============================================================
        # CONTROL AREA BOTTON
        #============================================================
        self.control_area_botton = QWidget()
        self.control_area_botton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid_control_botton = QGridLayout(self.control_area_botton)
        grid_control_botton.setSpacing(15)
        grid_control_botton.setContentsMargins(5, 5, 5, 5)

        current_row = 0
        target_col = 0
        self.output_ptm = self.add_control_row(grid_control_botton, current_row, target_col,"PTM", "mmHg", is_input=False)

        target_col += 3
        self.output_peristaltic_flow = self.add_control_row(grid_control_botton, current_row, target_col, "Qb", "ml/min", is_input=False)

        target_col += 3
        self.output_pt3 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-3", "psi", is_input=False)

        target_col += 3
        self.output_pt4 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-4", "psi", is_input=False)

        target_col += 3
        self.output_pt5 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-5", "psi", is_input=False)

        target_col += 3
        self.output_pt7 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-7", "psi", is_input=False)

        target_col += 3
        self.output_pt8 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-8", "mmHg", is_input=False)

        current_row = 1
        target_col = 0
        self.output_pt1 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-1", "mmHg", is_input=False)

        target_col += 3
        self.output_pt2 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-2", "mmHg", is_input=False)
        
        target_col += 3
        self.output_pt9 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-9", "mmHg", is_input=False)

        target_col += 3
        self.output_pt10 = self.add_control_row(grid_control_botton, current_row, target_col, "PT-10", "mmHg", is_input=False)

        target_col += 3
        btn_to_controler = QPushButton("Controlador")
        btn_to_controler.setStyleSheet(style_btn)  
        btn_to_controler.setFixedSize(200, 70)
        btn_to_controler.clicked.connect(self.parent_window.mostrar_calibracion)
        grid_control_botton.addWidget(btn_to_controler, 1, target_col )

        target_col +=3
        btn_to_ctrl_manual = QPushButton("Op. Manual")
        btn_to_ctrl_manual.setStyleSheet(style_btn)  
        btn_to_ctrl_manual.setFixedSize(200, 70)
        btn_to_ctrl_manual.clicked.connect(self.parent_window.mostrar_modo_manual)
        grid_control_botton.addWidget(btn_to_ctrl_manual, 1, target_col )

        target_col += 3


        #=============================================================
        # GRAPHICS AREA 
        #==============================================================
        self.graphics_area = QWidget()
        self.graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid_graphics = QGridLayout(self.graphics_area)
        grid_graphics.setSpacing(15)
        grid_graphics.setContentsMargins(5, 5, 5, 5)

        tick_font = QFont()
        tick_font.setPixelSize(12)
        
        self.plot_temp = pg.PlotWidget()
        self.plot_temp.setBackground("#e0e0e0")
        self.plot_temp.setTitle('<span style="font-size: 11pt; color: black;">Temperatura</span>')
        self.plot_temp.setLabel('left', '<span style="font-size: 9pt; color: black;">Temperatura (°C)</span>')
        self.plot_temp.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.plot_temp.addLegend()

        self.curve_temp_dialysate_ef = self.plot_temp.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Temp. Dializante EF")
        self.curve_temp_dialysate_sf = self.plot_temp.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Temp. Dializante SF")
        self.curve_temp_tank         = self.plot_temp.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), name="Temp. Tanque")

        grid_graphics.addWidget(self.plot_temp, 0, 0)

        self.plot_cond = pg.PlotWidget()
        self.plot_cond.setBackground("#e0e0e0")
        self.plot_cond.setTitle('<span style="font-size: 11pt; color: black;">Conductividad</span>')
        self.plot_cond.setLabel('left', '<span style="font-size: 9pt; color: black;">Conductividad(mS/cm)</span>')
        self.plot_cond.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.plot_cond.addLegend()

        self.curve_cond_ef = self.plot_cond.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Conductividad EF")
        self.curve_cond_sf = self.plot_cond.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Conductividad SF")

        grid_graphics.addWidget(self.plot_cond, 1, 0)

        for plot in [self.plot_cond, self.plot_temp]:
            plot.getAxis('bottom').setStyle(tickFont=tick_font)
            plot.getAxis('left').setStyle(tickFont=tick_font)
            plot.getAxis('bottom').setStyle(tickTextOffset=5)
            plot.getAxis('left').setStyle(tickTextOffset=5)
        

        #======================================================
        # INDICADORES VISUALES LED
        #=====================================================

        self.led_area = QWidget(self)
        self.led_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid_led_area = QGridLayout(self.led_area)
        grid_led_area.setSpacing(10)
        grid_led_area.setContentsMargins(5, 5, 5, 5)

        led_names = [
            "LS Tanque", "C. Deareación","Aire en S.", "P. Aire","S. Dial."
        ]

        led_tags = [
            "dialyTankHiLevelSwitch", "dialyDeaerChamLevSwitch", "airBubbleInBloodDetected", 
            "dialyPurgePumpStartButt", "bloodInDialyCircDetected"
        ]

        self.leds = []

        for i, name in enumerate(led_names):
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: bold;")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid_led_area.addWidget(lbl, i, 0)
            led = LED(self.led_area)
            led.setFixedSize(45, 45)
            grid_led_area.addWidget(led, i, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.leds.append((led, led_tags[i]))

        
        layout.addWidget(self.control_area, 0, 0, 1, 2)
        layout.addWidget(self.graphics_area, 0, 2, 1,1)
        layout.addWidget(self.led_area, 0, 3, 1, 1)
        layout.addWidget(self.control_area_botton, 1,0, 1, 4)


    def escribir_setpoint(self, tag, value=None, widget_input=None):
        """REQ-SW-015: Escritura segura de setpoints."""
        try:
            if value is not None:
                valor = float(value)
                texto = str(valor)
            elif widget_input is not None:
                if isinstance(widget_input, LabeledParameterWidget):
                    texto = widget_input.get_value()
                elif isinstance(widget_input, LabeledTimeInput):
                    texto = widget_input.get_time_value()
                elif hasattr(widget_input, 'text'):
                    texto = widget_input.text()
                else:
                    logger.error(f"Tipo de widget desconocido para '{tag}'")
                    QMessageBox.critical(self, "Error", f"Tipo desconocido para '{tag}'")
                    return

                texto = texto.replace(',', '.')
                if not texto:
                    current_value = self.valores.get(tag, 0.0)
                    if widget_input and hasattr(widget_input, 'set_value'):
                        widget_input.set_value(current_value)
                    return
                valor = float(texto)
            else:
                logger.error(f"Sin valor ni widget para '{tag}'")
                return

            logger.info(f"Intentando escribir setpoint {tag} = {valor}")

            target_group = target_id = -1
            found = False
            for group_key, vars_group in VARIABLES.items():
                if isinstance(vars_group, dict):
                    for var_id, info in vars_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found: break

            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:
                        if self.parent_window.serial.conectado:
                            self.parent_window.serial.escribir_double(target_group, target_id, valor)
                            logger.info(f"Setpoint escrito: {tag} = {valor}")
                        else:
                            logger.warning("Serial no conectado")
                            QMessageBox.warning(self, "Comunicación", "Serial no conectado")
                    else:
                        logger.warning("Serial no disponible")
                else:
                    logger.warning(f"Tag '{tag}' es de solo lectura")
                    QMessageBox.warning(self, "Error", f"'{tag}' es de solo lectura")
            else:
                logger.error(f"Tag '{tag}' no encontrado en mapa de variables")
                QMessageBox.critical(self, "Error", f"Tag '{tag}' no encontrado")

            if widget_input and hasattr(widget_input, 'clearFocus'):
                widget_input.clearFocus()

        except ValueError:
            display_text = str(value) if value is not None else texto
            logger.error(f"Valor inválido para {tag}: {display_text}")
            QMessageBox.warning(self, "Error", f"Valor inválido para {tag}")
        except Exception as e:
            logger.error(f"Error crítico al escribir {tag}: {e}")
            QMessageBox.critical(self, "Error Crítico", f"Error al escribir {tag}: {e}")
    
    def open_numpad(self, tag, widget_input, title="Ingrese valor"):
        """Abre numpad para valores decimales (REQ-SW-010)."""
        if isinstance(widget_input, LabeledParameterWidget):
            act_value = widget_input.get_value()
        else:
            act_value = widget_input.text()

        dialog = NumpadDialog(self, initial_value=act_value, title=title)
        if dialog.exec():
            new_value = dialog.get_value()
            if isinstance(widget_input, LabeledParameterWidget):
                widget_input.set_value(new_value)
            else:
                widget_input.setText(str(new_value))
            self.escribir_setpoint(tag, widget_input=widget_input)

            current_ts = QDateTime.currentMSecsSinceEpoch()
            self._write_hold_off[tag] = current_ts + 3000

    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores
        current_time = QDateTime.currentMSecsSinceEpoch()


        # LEDS 
        for led, tag in self.leds:
            valor = self.valores.get(tag, 0.0)
            if tag == "dialyTankHiLevelSwitch":
                led.set_state("off" if valor > 0 else 'in')
            else:
                led.set_state('on' if valor > 0 else 'off')


        if "balanceChamberSetTiming" not in self._write_hold_off or \
           current_time >= self._write_hold_off["balanceChamberSetTiming"]:
            cycle_val = self.valores.get("balanceChamberSetTiming", 0.0)
            try:
                calc_flow = convertir_ciclos_a_flujo(cycle_val)
                self.update_input_val(self.io_flow_cb, "balanceChamberSetTiming",
                                     precision=1, display_value=calc_flow)
            except Exception as e:
                logger.error(f"Error conversión flujo CB: {e}")
                self.update_input_val(self.io_flow_cb, "balanceChamberSetTiming",
                                     precision=1, display_value=0.0)
                
        # Ultra Filtración: ml/min → L/h
        if "ultraFilterPumpSpeed" not in self._write_hold_off or \
           current_time >= self._write_hold_off["ultraFilterPumpSpeed"]:
            uf_ml_min = self.valores.get("ultraFilterPumpSpeed", 0.0)
            try:
                calc_lh = convertir_ml_min_a_litros_h(uf_ml_min)
                self.update_input_val(self.io_flow_uf, "ultraFilterPumpSpeed",
                                     precision=1, display_value=calc_lh)
            except Exception as e:
                logger.error(f"Error conversión flujo UF: {e}")
                self.update_input_val(self.io_flow_uf, "ultraFilterPumpSpeed",
                                     precision=1, display_value=0.0)
        
        self.update_input_val(self.io_flow_blood, "bloodFlowControlSetPoint")
        
        self.update_input_val(self.io_sp_temp, "dialyTempControlSetPoint") #setpoint temperatura 
        self.update_label_val(self.ind_cycles_chamber, "balanceChamberCycleCount")
        
        self.update_label_val(self.l_cond_ef, "dialyConductIFProcessData")
        self.update_label_val(self.l_cond_sf, "dialyConductOFProcessData")

        pd_ef = self.valores.get("dialyPresIFProcessData", 0.0) # p dializante ef
        pd_sf = self.valores.get("dialyPresOFProcessData",0.0)
        pa = self.valores.get("bloodArteryPressureData", 0.0)
        pv = self.valores.get("bloodVenousPressureData", 0.0)

        try:
            ptm_calculado = calculo_ptm(pd_ef, pd_sf, pa, pv)
        except Exception:
            ptm_calculado = 0.0

        clave_ptm = "CALC_PTM" 
        self.valores[clave_ptm] = ptm_calculado
        

        self.update_label_val(self.output_peristaltic_flow, "bloodFlowVariableData")
        self.update_label_val(self.output_pt1, "dialyPFilPmpPresProcessData")
        self.update_label_val(self.output_pt2, "dialyTankPresProcessData")

        #GUARDAR EN ARCHIVO PARA HACER GRAFICAS DE DESVIACIONES, GENERAR REPORTE 
        self.update_label_val(self.output_pt3, "dialyLinePresProcessData") # pt3
        self.update_label_val(self.output_pt4,"dialyPresIFProcessData") # pt4
        self.update_label_val(self.output_pt5, "dialyPresOFProcessData") # pt5
        self.update_label_val(self.output_pt7, "dialyBChamPresProcessData") # pt7
        self.update_label_val(self.output_pt8, "bloodArteryPressureData") # pt8
        self.update_label_val(self.output_pt9, "bloodVenousPressureData") # pt9
        self.update_label_val(self.output_pt10, "dialyPFilPmpPresProcessData") #pt10
        self.update_label_val(self.l_temp_dialysate_ef, "dialyTempIFProcessData")
        self.update_label_val(self.l_temp_dialysate_sf, "dialyTempOFProcessData")
        self.update_label_val(self.l_temp_tank, "dialyTempControlOutput") # temperatura tanque 
        self.update_input_val(self.io_sp_cond, "dialyCondControlSetPoint") #Setpoint conductuvidad
        setpoint_cond = self.valores.get("dialyCondControlSetPoint", 0.0)
        output_cond_raw = self.valores.get("dialyCondControlOutput", 0.0) #ESTE NO
        output_cc_percent = output_cond_raw / 5
        setpoint_ctd = self.valores.get("dialyTempControlSetPoint", 0.0)
        output_ctd_raw = self.valores.get("dialyTempControlOutput", 0.0)# ESTE NO
        output_ctd_percent = output_ctd_raw / 2
        self.update_label_val(self.output_ptm, "CALC_PTM")



        
        temp_dialysate_ef = self.valores.get("dialyTempIFProcessData", 0.0)
        temp_dialysate_sf = self.valores.get("dialyTempOFProcessData", 0.0)
        temp_tank = self.valores.get("dialyTempControlOutput", 0.0)

        cond_ef = self.valores.get("dialyConductIFProcessData", 0.0)
        cond_sf = self.valores.get("dialyConductOFProcessData", 0.0)

        self.temp_dialysate_EF_y.append(temp_dialysate_ef)
        self.temp_dialysate_SF_y.append(temp_dialysate_sf)
        self.temp_tank_y.append(temp_tank)

        self.cond_ef_y.append(cond_ef)
        self.cond_sf_y.append(cond_sf)

        self.curve_temp_dialysate_ef.setData(self.x_relativa, list(self.temp_dialysate_EF_y))
        self.curve_temp_dialysate_sf.setData(self.x_relativa, list(self.temp_dialysate_SF_y))
        self.curve_temp_tank.setData(self.x_relativa, list(self.temp_tank_y))

        self.curve_cond_ef.setData(self.x_relativa, list(self.cond_ef_y))
        self.curve_cond_sf.setData(self.x_relativa, list(self.cond_sf_y))

        self.plot_temp.setXRange(-self.history_length + 1, 0)
        self.plot_cond.setXRange(-self.history_length + 1, 0)

    def add_control_row(self, grid, row, start_col, label_text, unit_text, tag=None, numpad_title="", is_input=True, initial_value="0.0"):
        lbl = QLabel(label_text)
        # No setStyleSheet → hereda del global
        grid.addWidget(lbl, row, start_col)
        style_lbl_indicator = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        if is_input is True:
            widget_central = ClickableLineEdit(initial_value)
            widget_central.setReadOnly(True)
            widget_central.setStyleSheet("""
                background: #FFFFE5;
                color: #000000;
                border: 2px solid #000000;
                border-radius: 6px;
                padding: 4px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 20px;
                font-weight: bold;
            """)
            
            widget_central.clicked.connect(lambda: self.open_numpad(tag, widget_central, numpad_title))
            # No setStyleSheet → hereda del global (QLineEdit, ClickableLineEdit)
        elif is_input is False:
            widget_central = QLabel(initial_value)
            widget_central.setStyleSheet(style_lbl_indicator)
            # Para las variables destacadas (cyan con borde) → usamos propiedad o clase
            widget_central.setProperty("class", "highlighted")  # o setObjectName("highlight")
        else:
            # Para casos como Velocidad BS (solo lectura, sin input)
            widget_central = QLabel(initial_value)
            widget_central.setProperty("class", "unit")  # o estilo más pequeño si lo defines en global

        widget_central.setFixedSize(80, 35)
        widget_central.setAlignment(Qt.AlignCenter)
        grid.addWidget(widget_central, row, start_col + 1)

        lbl_unit = QLabel(unit_text)
        lbl_unit.setProperty("class", "unit")  # hereda estilo unit del global
        grid.addWidget(lbl_unit, row, start_col + 2)

        return widget_central

    def update_input_val(self, widget, tag, precision=1, display_value=None):
        """Actualiza valor en interfaz con hold-off."""
        current_time = QDateTime.currentMSecsSinceEpoch()
        hold_until = self._write_hold_off.get(tag, 0)

        if current_time < hold_until:
            return

        value = display_value if display_value is not None else self.valores.get(tag, 0.0)

        if isinstance(widget, LabeledParameterWidget):
            widget.set_value(value)
        elif hasattr(widget, "setText"):
            if hasattr(widget, "hasFocus") and widget.hasFocus():
                return
            widget.setText(f"{value:.{precision}f}")
        else:
            logger.error(f"Widget no soportado para tag '{tag}'")

    def update_label_val(self, label_widget, tag, precision=1):
        """Actualiza indicadores de solo lectura."""
        value = self.valores.get(tag, 0.0)
        if isinstance(label_widget, LabeledParameterWidget):
            label_widget.set_value(value)
        elif hasattr(label_widget, 'setText'):
            label_widget.setText(f"{value:.{precision}f}")
        else:
            logger.error(f"Widget no soportado para tag '{tag}'")

    def _handle_flow_cb_input(self):
        """Input flujo Cámara Balance (ml/min → ciclos)."""
        current_text = self.io_flow_cb.text()
        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo CB (ml/min)")
        if dialog.exec():
            new_value = dialog.get_value()
            self.io_flow_cb.setText(str(new_value))
            try:
                ciclos = convertir_flujo_a_ciclos(new_value)
                self.escribir_setpoint("balanceChamberSetTiming", value=ciclos)
                self._write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error flujo CB: {e}")

    def _handle_flow_uf_input(self):
        """Input flujo Ultra Filtración (L/h → ml/min)."""
        current_text = self.io_flow_uf.text()
        dialog = NumpadDialog(self, initial_value=current_text, title="Flujo UF (L/h)")
        if dialog.exec():
            new_value = dialog.get_value()
            self.io_flow_uf.setText(str(new_value))
            try:
                ml_min = convertir_litros_h_a_ml_min(new_value)
                self.escribir_setpoint("ultraFilterPumpSpeed", value=ml_min)
                self._write_hold_off["ultraFilterPumpSpeed"] = QDateTime.currentMSecsSinceEpoch() + 3000
            except Exception as e:
                logger.error(f"Error flujo UF: {e}")