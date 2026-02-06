#gui/service/ctrlCfgScreen.py
#Configuración de bajo nivel, calibración de sensores y
#  acceso al registro de errores técnicos. configuración de controladores de bombas
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque

from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit, DoubleToggleBox

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

try:
    from gui.components.LED import LED
    from gui.components.ToggleSwitch import ToggleSwitch
except ImportError:
    class LED(QWidget):
        def __init__(self): super().__init__(); self.state = 'off'
        def set_state(self, s): self.state = s
    class ToggleSwitch(QCheckBox):
        def __init__(self, width=60, height=30, active_color=None): super().__init__()


class ctrlCfgScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.valores = valores_dict if valores_dict is not None else {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1024, 600)
        # Fondo consistente con el global del main.py
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#fcfcfc"))
        self.setPalette(pal)

        self.toggles_by_tag = {}
        self.history_length = 600        

        nan_list = [np.nan] * self.history_length
        self.blood_flow_setpoint_y = deque(nan_list, maxlen=self.history_length)
        self.blood_flow_variable_y = deque(nan_list, maxlen=self.history_length)
        self.blood_flow_output_y   = deque(nan_list, maxlen=self.history_length)

        self.cond_setpoint_y = deque(nan_list, maxlen=self.history_length)
        self.cond_variable_y = deque(nan_list, maxlen=self.history_length)
        self.cond_output_y   = deque(nan_list, maxlen=self.history_length)

        self.ctd_setpoint_y = deque(nan_list, maxlen=self.history_length)
        self.ctd_variable_y = deque(nan_list, maxlen=self.history_length)
        self.ctd_output_y   = deque(nan_list, maxlen=self.history_length)
        self.x_relativa = np.arange(-self.history_length + 1, 1, dtype=np.float32)
        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ──────────────────────────────
        # Área de gráficos (hereda estilos globales)
        # ──────────────────────────────
        self.graphics_area = QWidget()
        self.graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid_graphics = QGridLayout(self.graphics_area)
        grid_graphics.setSpacing(15)
        grid_graphics.setContentsMargins(5, 5, 5, 5)

        tick_font = QFont()
        tick_font.setPixelSize(12)

        # Gráficos pyqtgraph – el fondo ya está en el global del main
        self.plot_cfs = pg.PlotWidget()
        self.plot_cfs.setBackground("#e0e0e0")
        self.plot_cfs.setTitle('<span style="font-size: 11pt; color: black;">Control de Flujo de Sangre</span>')
        self.plot_cfs.setLabel('left', '<span style="font-size: 9pt; color: black;">Flujo Qb / Salida (%)</span>')
        self.plot_cfs.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.plot_cfs.addLegend()


        self.curve_cfs_setpoint = self.plot_cfs.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint CFS")
        self.curve_cfs_variable = self.plot_cfs.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable CFS")
        self.curve_cfs_output   = self.plot_cfs.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida CFS (%)")

        grid_graphics.addWidget(self.plot_cfs, 0, 0)

        self.plot_cc = pg.PlotWidget()
        self.plot_cc.setBackground("#e0e0e0")
        self.plot_cc.setTitle('<span style="font-size: 11pt; color: black;">Control de Conductividad</span>')
        self.plot_cc.setLabel('left', '<span style="font-size: 9pt; color: black;">Conductividad (mS/cm)</span>')  # agrega unidad si quieres
        self.plot_cc.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.plot_cc.addLegend()

        self.curve_cc_setpoint = self.plot_cc.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Cond.")
        self.curve_cc_variable = self.plot_cc.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Cond.")
        self.curve_cc_output   = self.plot_cc.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida Cond. (%)")

        grid_graphics.addWidget(self.plot_cc, 1, 0)

        self.plot_ctd = pg.PlotWidget()
        self.plot_ctd.setBackground("#e0e0e0")        
        self.plot_ctd.setTitle('<span style="font-size: 11pt; color: black;">Control de Temperatura</span>')
        self.plot_ctd.setLabel('left', '<span style="font-size: 9pt; color: black;">Temperatura Dializante (°C)</span>')
        self.plot_ctd.setLabel('bottom', '<span style="font-size: 9pt; color: black;">Tiempo (s)</span>')
        self.plot_ctd.addLegend()

        self.curve_ctd_setpoint = self.plot_ctd.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Temp.")
        self.curve_ctd_variable = self.plot_ctd.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Temp.")
        self.curve_ctd_output   = self.plot_ctd.plot(pen=pg.mkPen(color=(255, 0, 0),   width=2), name="Salida Temp. (%)")

        for plot in [self.plot_cfs, self.plot_cc, self.plot_ctd]:
            plot.getAxis('bottom').setStyle(tickFont=tick_font)
            plot.getAxis('left').setStyle(tickFont=tick_font)
            # Opcional: más espacio para que no se sobrepongan
            plot.getAxis('bottom').setStyle(tickTextOffset=5)
            plot.getAxis('left').setStyle(tickTextOffset=5)

        grid_graphics.addWidget(self.plot_ctd, 2, 0)

        # ──────────────────────────────
        # Área de controles
        # ──────────────────────────────
        self.control_area = QWidget()
        self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid = QGridLayout(self.control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)

        #=====================================================================================
        # COLUMNA 1 ZONA DE TOGGLES DE HABILITACIÓN DE CONTROLES 
        #=====================================================================================

        hab_ctrl_modes_raw = [
            (0, 0, "bloodControlLoopEnable",  "Hab. CFS"),
            (1, 0, "bloodControlLoopMode",    "Hab. Modo CFS"),
            (2, 0, "dialyCondCtrlLoopEnable", "Hab. CC"),
            (3, 0, "dialyCondCtrlLoopMode",   "Hab. Modo CC"),
            (4, 0, "dialyTempCtrlLoopEnable", "Hab. CTD"),
            (5, 0, "dialyTempCtrlLoopMode",   "Hab. Modo CTD")
        ]

        current_grid_row = 0
        for i in range(0, len(hab_ctrl_modes_raw), 2):
            _, col, tag1, label1 = hab_ctrl_modes_raw[i]
            _, _,   tag2, label2 = hab_ctrl_modes_raw[i+1]

            double_tbox = DoubleToggleBox(label1, label2)
            grid.addWidget(double_tbox, current_grid_row, col, 2, 2)

            self.toggles_by_tag[tag1] = double_tbox.toggle1
            self.toggles_by_tag[tag2] = double_tbox.toggle2

            double_tbox.toggle1.toggled.connect(lambda checked, t=tag1: self._toggle_ctrl(t, checked))
            double_tbox.toggle2.toggled.connect(lambda checked, t=tag2: self._toggle_ctrl(t, checked))

            current_grid_row += 2
        #============================================================
        # Columnas de setpoints, variables, feedforward y ganancias
        #================================================================
        current_row = 0
        target_col = 3

        # CFS
        self.input_sp_cfs     = self.add_control_row(grid, current_row, target_col, "SetPoint CFS", "ml/min",   tag="bloodFlowControlSetPoint", numpad_title="Setpoint CFS (ml/min)")
        current_row += 1
        self.input_output_cfs = self.add_control_row(grid, current_row, target_col, "Salida CFS",    "%",       tag="bloodFlowControlOutput",   numpad_title="Salida CFS (%)")
        current_row += 1
        self.lbl_ind_var_cfs  = self.add_control_row(grid, current_row, target_col, "Variable CFS",  "ml/min",  is_input=False)
        current_row += 1

        # Conductividad
        self.input_sp_cond     = self.add_control_row(grid, current_row, target_col, "SetPoint Cond.", "mS/cm", tag="dialyCondControlSetPoint", numpad_title="Setpoint Conductividad (mS/cm)")
        current_row += 1
        self.input_output_cond = self.add_control_row(grid, current_row, target_col, "Salida Cond.",    "%",    tag="dialyCondControlOutput",   numpad_title="Salida Conductividad (%)")
        current_row += 1
        self.lbl_ind_var_cond  = self.add_control_row(grid, current_row, target_col, "Variable Cond.",  "mS/cm", is_input=False)
        current_row += 1

        # Temperatura
        self.input_sp_temp     = self.add_control_row(grid, current_row, target_col, "SetPoint Temp.", "°C", tag="dialyTempControlSetPoint", numpad_title="Setpoint Temperatura (°C)")
        current_row += 1
        self.input_output_temp = self.add_control_row(grid, current_row, target_col, "Salida Temp.",    "%",  tag="dialyTempControlOutput",   numpad_title="Salida Temperatura (%)")
        current_row += 1
        self.lbl_ind_var_temp  = self.add_control_row(grid, current_row, target_col, "Variable Temp.",  "°C", is_input=False)
        current_row += 1

        # Feedforward
        current_row_2 = 0
        target_col_2 = 6
        self.ind_rpm_bs     = self.add_control_row(grid, current_row_2, target_col_2, "Velocidad BS", "RPM",   is_input=None)
        current_row_2 += 1
        self.input_ffwd     = self.add_control_row(grid, current_row_2, target_col_2, "FFWD",         " ",     tag="bloodFlowFeedForwardGain", numpad_title="Ganancia FFWD")
        current_row_2 += 1
        self.input_lead_ffwd = self.add_control_row(grid, current_row_2, target_col_2, "Lead FFWD",    " ", tag="bloodFlowFeedForwardLead", numpad_title="Lead FFWD")

        # Ganancias PID
        current_row_3 = 0
        target_col_3 = 9

        self.input_kp_cfs   = self.add_control_row(grid, current_row_3, target_col_3, "CFS",  "kp", tag="bloodFlowControlPropGain",   numpad_title="CFS Kp Gain")
        current_row_3 += 1
        self.input_ki_cfs   = self.add_control_row(grid, current_row_3, target_col_3, "CFS",  "ki", tag="bloodFlowControlInteGain",   numpad_title="CFS ki Gain")
        current_row_3 += 1
        self.input_kd_cfs   = self.add_control_row(grid, current_row_3, target_col_3, "CFS",  "kd", tag="bloodFlowControlDeriGain",   numpad_title="CFS kd Gain")
        current_row_3 += 1

        self.input_kp_cond  = self.add_control_row(grid, current_row_3, target_col_3, "Cond.", "kp", tag="dialyCondControlPropGain",  numpad_title="Cond. Kp Gain")
        current_row_3 += 1
        self.input_ki_cond  = self.add_control_row(grid, current_row_3, target_col_3, "Cond.", "ki", tag="dialyCondControlInteGain",  numpad_title="Cond. ki Gain")
        current_row_3 += 1
        self.input_kd_cond  = self.add_control_row(grid, current_row_3, target_col_3, "Cond.", "kd", tag="dialyCondControlDeriGain",  numpad_title="Cond. kd Gain")
        current_row_3 += 1

        self.input_kp_temp  = self.add_control_row(grid, current_row_3, target_col_3, "Temp.", "kp", tag="dialyTempControlPropGain",  numpad_title="Temp. Kp Gain")
        current_row_3 += 1
        self.input_ki_temp  = self.add_control_row(grid, current_row_3, target_col_3, "Temp.", "ki", tag="dialyTempControlInteGain",  numpad_title="Temp. ki Gain")
        current_row_3 += 1
        self.input_kd_temp  = self.add_control_row(grid, current_row_3, target_col_3, "Temp.", "kd", tag="dialyTempControlDeriGain",  numpad_title="Temp. kd Gain")

        layout.addWidget(self.control_area,   0, 0)
        layout.addWidget(self.graphics_area,  0, 5)

    def _toggle_ctrl(self, tag_start_stop, activado):
        if activado:
            print(f"[CONTROL] Habilitado {tag_start_stop}")
            self.command_write(tag_start_stop, True)

        else:
            print(f"[CONTROL] Deshabilitado {tag_start_stop} (Triggering Stop {tag_start_stop})")
            self.command_write(tag_start_stop, False)

    def command_write(self, tag, state):
        print(f"[COMMAND] Usuario Cambió {tag} a {state}")
        address_ = -1
        if 0x01 in VARIABLES:
            for id_var, info in VARIABLES[0x01].items():
                if info.get("tag") == tag:
                    address_ = id_var
                    break

        if address_ != -1:
            if self.parent_window and hasattr(self.parent_window, 'serial') and self.parent_window.serial:
                try:
                    if self.parent_window.serial.conectado:
                        print(f" -> Enviando: Addr {address_} Val {state}")
                        self.parent_window.serial.escribir_booleano(address_, state)
                    else:
                        print(" -> Error: Serial no conectado")
                except AttributeError:
                    print(f"[INFO] Fallo en envío: Addr {address_} Val {state}")
            else:
                print(f"[INFO] Error no se completo la escritura: Addr {address_} Val {state}")
        else:
            print(f" -> Error: No se encontró ID para el tag '{tag}'")

    def write_setpoint(self, tag, widget_input):
        try:
            texto = widget_input.text().replace(',', '.')
            if not texto:                 
                current_value = self.valores.get(tag, 0.0)
                widget_input.setText(f"{current_value:.1f}") 
                return 
                
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
            
            widget_input.clearFocus()
            self.setFocus()

        except ValueError:
            print(f"[ERROR] Valor numérico inválido en input para {tag}: {widget_input.text()}")
            val = self.valores.get(tag, 0.0)
            widget_input.setText(f"{val:.1f}")
            widget_input.clearFocus()
        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
  

    def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
        act_value = widget_input.text()
        dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
        if dialog.exec(): 
            new_value = dialog.get_value() 
            widget_input.setText(str(new_value))            
            self.write_setpoint(tag, widget_input)

    def add_control_row(self, grid, row, start_col, label_text, unit_text, tag=None, numpad_title="", is_input=True, initial_value="0.0"):
        lbl = QLabel(label_text)
        # No setStyleSheet → hereda del global
        grid.addWidget(lbl, row, start_col)

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

    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores

        # Obtención de valores (sin cambios)
        setpoint_cfs = self.valores.get("bloodFlowControlSetPoint", 0.0)
        variable_cfs = self.valores.get("bloodFlowVariableData", 0.0)
        output_cfs_raw = self.valores.get("bloodFlowControlOutput", 0.0)
        output_cfs_percent = output_cfs_raw * 10 

        setpoint_cond = self.valores.get("dialyCondControlSetPoint", 0.0)
        variable_cond = self.valores.get("dialyCondVariableData", 0.0)
        output_cond_raw = self.valores.get("dialyCondControlOutput", 0.0)
        output_cc_percent = output_cond_raw / 5

        setpoint_ctd = self.valores.get("dialyTempControlSetPoint", 0.0)
        variable_ctd = self.valores.get("dialyTempVariableData", 0.0)
        output_ctd_raw = self.valores.get("dialyTempControlOutput", 0.0)
        output_ctd_percent = output_ctd_raw / 2

        # Append nuevo valor (deque maneja el shift circular automáticamente)
        self.blood_flow_setpoint_y.append(setpoint_cfs)
        self.blood_flow_variable_y.append(variable_cfs)
        self.blood_flow_output_y.append(output_cfs_percent)

        self.cond_setpoint_y.append(setpoint_cond)
        self.cond_variable_y.append(variable_cond)
        self.cond_output_y.append(output_cc_percent)

        self.ctd_setpoint_y.append(setpoint_ctd)
        self.ctd_variable_y.append(variable_ctd)
        self.ctd_output_y.append(output_ctd_percent)

        # Actualizar curvas directamente con list(deque) – pyqtgraph lo acepta
        self.curve_cfs_setpoint.setData(self.x_relativa, list(self.blood_flow_setpoint_y))
        self.curve_cfs_variable.setData(self.x_relativa, list(self.blood_flow_variable_y))
        self.curve_cfs_output.setData(self.x_relativa, list(self.blood_flow_output_y))

        self.curve_cc_setpoint.setData(self.x_relativa, list(self.cond_setpoint_y))
        self.curve_cc_variable.setData(self.x_relativa, list(self.cond_variable_y))
        self.curve_cc_output.setData(self.x_relativa, list(self.cond_output_y))

        self.curve_ctd_setpoint.setData(self.x_relativa, list(self.ctd_setpoint_y))
        self.curve_ctd_variable.setData(self.x_relativa, list(self.ctd_variable_y))
        self.curve_ctd_output.setData(self.x_relativa, list(self.ctd_output_y))
        # Rango fijo (sin cambios)
        self.plot_cfs.setXRange(-self.history_length + 1, 0)
        self.plot_cc.setXRange( -self.history_length + 1, 0)
        self.plot_ctd.setXRange( -self.history_length + 1, 0)

        self.update_input_val(self.input_sp_cfs, "bloodFlowControlSetPoint")
        self.update_input_val(self.input_output_cfs, "bloodFlowControlOutput")
        self.update_label_val(self.lbl_ind_var_cfs, "bloodFlowVariableData")

        self.update_input_val(self.input_sp_cond, "dialyCondControlSetPoint")
        self.update_input_val(self.input_output_cond, "dialyCondControlOutput")
        self.update_label_val(self.lbl_ind_var_cond, "dialyCondVariableData")

        self.update_input_val(self.input_sp_temp,"dialyTempControlSetPoint")
        self.update_input_val(self.input_output_temp,"dialyTempControlOutput")
        self.update_label_val(self.lbl_ind_var_temp,"dialyTempVariableData")

        self.update_label_val(self.ind_rpm_bs, "bloodSpeedVariableData")
        self.update_input_val(self.input_ffwd, "bloodFlowFeedForwardGain")
        self.update_input_val(self.input_lead_ffwd, "bloodFlowFeedForwardLead")

        self.update_input_val(self.input_kp_cfs, "bloodFlowControlPropGain")
        self.update_input_val(self.input_ki_cfs, "bloodFlowControlInteGain")
        self.update_input_val(self.input_kd_cfs, "bloodFlowControlDeriGain")

        self.update_input_val(self.input_kp_cond, "dialyCondControlPropGain")
        self.update_input_val(self.input_ki_cond, "dialyCondControlInteGain")
        self.update_input_val(self.input_kd_cond, "dialyCondControlDeriGain")

        self.update_input_val(self.input_kp_temp, "dialyTempControlPropGain")
        self.update_input_val(self.input_ki_temp, "dialyTempControlInteGain")
        self.update_input_val(self.input_kd_temp, "dialyTempControlDeriGain")

        
    
    def update_input_val(self, widget, tag, precision=1):
        """
        Actualiza un widget input si no tiene el foco del usuario.
        """
        value = self.valores.get(tag, 0.0)
        if not widget.hasFocus():
            widget.setText(f"{value:.{precision}f}")
    
    def update_label_val(self, label, tag, precision=1):
        """
        Actualiza un label indicador (siempre, ya que no tiene foco).
        """
        value = self.valores.get(tag, 0.0)
        label.setText(f"{value:.{precision}f}")

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()


        




