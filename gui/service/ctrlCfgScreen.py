#gui/service/ctrlCfgScreen.py
#Configuración de bajo nivel, calibración de sensores y
#  acceso al registro de errores técnicos. configuración de controladores de bombas

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import pyqtgraph as pg
from collections import deque
import numpy as np



from gui.components.numpad_modal import NumpadDialog
from gui.components.ui_components import ClickableLineEdit, ToggleBox, DoubleToggleBox

try: 
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}} # mock vacio

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
        # self.setStyleSheet("background: #0f172a;")

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#fcfcfc"))
        self.setPalette(p)

        self.toggles_by_tag = {} 

        self.history_length = 600  # ~10 min a 1 Hz
        
        # Buffers circulares con NumPy (fijos, predecibles, sin realloc)
        self.blood_flow_setpoint_y   = np.full(self.history_length, np.nan, dtype=np.float32)
        self.blood_flow_variable_y   = np.full(self.history_length, np.nan, dtype=np.float32)
        self.blood_flow_output_y     = np.full(self.history_length, np.nan, dtype=np.float32)

        self.cond_setpoint_y         = np.full(self.history_length, np.nan, dtype=np.float32)
        self.cond_variable_y         = np.full(self.history_length, np.nan, dtype=np.float32)
        self.cond_output_y           = np.full(self.history_length, np.nan, dtype=np.float32)

        self.ctd_setpoint_y          = np.full(self.history_length, np.nan, dtype=np.float32)
        self.ctd_variable_y          = np.full(self.history_length, np.nan, dtype=np.float32)
        self.ctd_output_y            = np.full(self.history_length, np.nan, dtype=np.float32)

        # Índice circular (avanza con cada nuevo dato)
        self.plot_idx = 0

        # X relativa fija (se genera una vez) → [-599, -598, ..., 0] para history=600
        self.x_relativa = np.arange(-self.history_length + 1, 1, dtype=np.float32)

        self.setup_ui()
    
    def setup_ui(self):
        
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Estilos de etiquetas
        style_lbl = "color: #000000; font-size: 18px; font-weight: bold; "
        style_lbl_ = "color: #22d3ee; font-size: 20px; font-weight: bold;border: 2px solid #000000; border-radius: 5px; padding: 2px;"
        style_unit = "color: #94a3b8; font-size: 16px;"
        style_input = """
            QLineEdit { background: #FFFFE5; color: #000000; font-size: 18px; 
                        font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px; }
        """
        style_btn = """
            QPushButton { background: #3b82f6; color: #ffffff; border-radius: 8px; font-weight: bold; }
            QPushButton:pressed { background: #1e40af; }
        """    
        #============================================================================
        #=======================AREA DE GRAFICOS=====================================
        #============================================================================

        self.graphics_area = QWidget()
        # self.graphics_area.setMinimumSize(400, 726)
        self.graphics_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        grid_graphics = QGridLayout(self.graphics_area)
        grid_graphics.setSpacing(15)
        grid_graphics.setContentsMargins(5, 5, 5, 5)

        self.plot_cfs = pg.PlotWidget()
        self.plot_cfs.setBackground("#e0e0e0")
        self.plot_cfs.setTitle("CFS: Control de Flujo de Sangre", color="#000000", size="12pt")
        self.plot_cfs.setLabel('left', "Flujo Qb/ Salida (%)", color="#000000", size="10pt")
        self.plot_cfs.setLabel('bottom', "Tiempo (s)", color="#000000", size="10pt")
        self.plot_cfs.addLegend() 

        self.curve_cfs_setpoint = self.plot_cfs.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint CFS")
        self.curve_cfs_variable = self.plot_cfs.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable CFS")
        self.curve_cfs_output = self.plot_cfs.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), name="Salida CFS (%)")

        grid_graphics.addWidget(self.plot_cfs, 0, 0) 

        self.plot_cc = pg.PlotWidget()
        self.plot_cc.setBackground("#e0e0e0")
        self.plot_cc.setTitle("Control de Conductividad", color= "#000000", size="12pt")
        self.plot_cc.setLabel('left', "Conductividad", color="#000000", size="10pt")
        self.plot_cc.setLabel('bottom', "Tiempo (s)", color="#000000", size="10pt")
        self.plot_cc.addLegend()

        self.curve_cc_setpoint = self.plot_cc.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Cond.")
        self.curve_cc_variable = self.plot_cc.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Cond.")
        self.curve_cc_output = self.plot_cc.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), name="Salida Cond. (%)")

        grid_graphics.addWidget(self.plot_cc, 1, 0)

        self.plot_ctd = pg.PlotWidget()
        self.plot_ctd.setBackground("#e0e0e0")
        self.plot_ctd.setTitle("Control de Temperatura", color= "#000000", size="12pt")
        self.plot_ctd.setLabel('left', "Temperatura Dializante", color="#000000", size="10pt")
        self.plot_ctd.setLabel('bottom', "Tiempo (s)", color="#000000", size="10pt")
        self.plot_ctd.addLegend()

        self.curve_ctd_setpoint = self.plot_ctd.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), name="Setpoint Temp.")
        self.curve_ctd_variable = self.plot_ctd.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable Temp.")
        self.curve_ctd_output = self.plot_ctd.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), name="Salida Temp. (%)")
    
        grid_graphics.addWidget(self.plot_ctd, 2, 0)

        #============================================================================
        #=======================AREA DE CONTROLES====================================
        #============================================================================
        self.control_area = QWidget()
        # self.control_area.setMinimumSize(1080,300)
        self.control_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        grid = QGridLayout(self.control_area)
        grid.setSpacing(15)
        grid.setContentsMargins(5, 5, 5, 5)


        #=====================================================================================
        # COLUMNA 1 ZONA DE TOGGLES DE HABILITACIÓN DE CONTROLES 
        #=====================================================================================


        hab_ctrl_modes_raw = [
            (0, 0,"bloodControlLoopEnable", "Hab. CFS" ),
            (1, 0,"bloodControlLoopMode", "Hab. Modo CFS"),
            (2, 0, "dialyCondCtrlLoopEnable", "Hab. CC"),
            (3, 0, "dialyCondCtrlLoopMode", "Hab. Modo CC"),
            (4, 0, "dialyTempCtrlLoopEnable", "Hab. CTD" ),
            (5, 0, "dialyTempCtrlLoopMode", "Hab. Modo CTD")            
        ]
        
        current_grid_row = 0 # Para controlar la fila en el grid

        # Iterar de 2 en 2 para crear los DoubleToggleBox
        for i in range(0, len(hab_ctrl_modes_raw), 2):
            # Asumiendo que siempre hay pares completos
            row1, col1, tag1, label1 = hab_ctrl_modes_raw[i]
            row2, col2, tag2, label2 = hab_ctrl_modes_raw[i+1]

            # Crear el DoubleToggleBox
            double_tbox = DoubleToggleBox(label1, label2)
            
            # Añadir al grid (ocupará 2 filas en el grid, si current_grid_row está bien manejado)
            # Usamos la 'row' del primer elemento del par para la posición, y 'col1'
            grid.addWidget(double_tbox, current_grid_row, col1, 2, 2) # Ocupa 2 filas y 2 columnas

            # Guardar las referencias a los toggles individuales en el diccionario principal
            self.toggles_by_tag[tag1] = double_tbox.toggle1
            self.toggles_by_tag[tag2] = double_tbox.toggle2
            
            # Conectar las señales de los toggles
            double_tbox.toggle1.toggled.connect(lambda checked, t=tag1: self._toggle_ctrl(t, checked))
            double_tbox.toggle2.toggled.connect(lambda checked, t=tag2: self._toggle_ctrl(t, checked))
            
            current_grid_row += 2 # Avanzamos dos filas para el siguiente DoubleToggleBox


        
        #=====================================================================================
        # COLUMNA 2 ZONA DE SETPOINTS 
        #=====================================================================================
        current_row = 0
        target_col = 3 

                # --- SECCIÓN CFS ---
        self.input_sp_cfs =  self.add_control_row(
            grid, current_row, target_col, 
            "SetPoint CFS", "ml/min", 
            tag="bloodFlowControlSetPoint", numpad_title="Setpoint CFS (ml/min)"
        )
        
        current_row += 1        
        
        
        self.input_output_cfs = self.add_control_row(
            grid, current_row, target_col, 
            "Salida CFS", "%", 
            tag="bloodFlowControlOutput", numpad_title="Salida CFS (%)"
        )
        current_row += 1

        self.lbl_ind_var_cfs = self.add_control_row(
            grid, current_row, target_col, 
            "Variable CFS", "ml/min", 
            is_input=False 
        )
        current_row += 1
       
        # --- SECCIÓN CONDUCTIVIDAD ---
        self.input_sp_cond = self.add_control_row(
            grid, current_row, target_col, 
            "SetPoint Cond.", "mS/cm", 
            tag="dialyCondControlSetPoint", numpad_title="Setpoint Conductividad (mS/cm)"
        )
        current_row += 1

        self.input_output_cond = self.add_control_row(
            grid, current_row, target_col, 
            "Salida Cond.", "%", 
            tag="dialyCondControlOutput", numpad_title="Salida Conductividad (%)"
        )
        current_row += 1

        self.lbl_ind_var_cond = self.add_control_row(
            grid, current_row, target_col, 
            "Variable Cond.", "mS/cm", 
            is_input=False
        )  
        current_row += 1

        # --- SECCIÓN TEMPERATURA ---
        self.input_sp_temp = self.add_control_row(
            grid, current_row, target_col, 
            "SetPoint Temp.", "°C", 
            tag="dialyTempControlSetPoint", numpad_title="Setpoint Temperatura (°C)"
        )
        current_row += 1

        self.input_output_temp = self.add_control_row(
            grid, current_row, target_col, 
            "Salida Temp.", "%", 
            tag="dialyTempControlOutput", numpad_title="Salida Temperatura (%)"
        )
        current_row += 1

        self.lbl_ind_var_temp = self.add_control_row(
            grid, current_row, target_col, 
            "Variable Temp.", "°C", 
            is_input=False
        )
        current_row += 1


        



        layout.addWidget(self.control_area, 0, 0)
        layout.addWidget(self.graphics_area, 0, 5)



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

        except ValueError:
            print(f"[ERROR] Valor numérico inválido en input para {tag}: {widget_input.text()}")
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
        """
        Crea una fila estandarizada:
            [Col N] Label  |  [Col N+1] Widget  |  [Col N+2] Unidad
        
        Args:
            grid (QGridLayout): El layout donde se insertarán los widgets.
            row (int): La fila del grid.
            start_col (int): La columna donde comienza la etiqueta (Label).
            ... los demás parámetros ...
        """
        
        # Estilos
        style_lbl = "color: #000000; font-size: 18px; font-weight: bold;"
        style_input = """
            QLineEdit { background: #FFFFE5; color: #000000; font-size: 18px; 
                        font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px; }
        """
        style_unit = "color: #94a3b8; font-size: 16px;"
        style_lbl_ind = "color: #22d3ee; font-size: 20px; font-weight: bold; border: 2px solid #000000; border-radius: 5px; padding: 2px;"

        # 1. Etiqueta Descriptiva (En la columna inicial)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(style_lbl)
        grid.addWidget(lbl, row, start_col) 

        # 2. Widget Central (En la columna inicial + 1)
        widget_central = None
        
        if is_input:
            widget_central = ClickableLineEdit(initial_value)
            widget_central.setReadOnly(True)
            # Nota importante en lambda: t=tag, w=widget_central, etc. para capturar valores por defecto
            widget_central.clicked.connect(
                lambda t=tag, w=widget_central, title=numpad_title: self.open_numpad(t, w, title)
            )
            widget_central.setStyleSheet(style_input)
        else:
            widget_central = QLabel(initial_value)
            widget_central.setStyleSheet(style_lbl_ind)
        
        widget_central.setFixedSize(80, 35)
        widget_central.setAlignment(Qt.AlignCenter)
        grid.addWidget(widget_central, row, start_col + 1)

        # 3. Unidad (En la columna inicial + 2)
        lbl_unit = QLabel(unit_text)
        lbl_unit.setStyleSheet(style_unit)
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

        # Escribir en posición actual (circular)
        idx = self.plot_idx

        self.blood_flow_setpoint_y[idx]   = setpoint_cfs
        self.blood_flow_variable_y[idx]   = variable_cfs
        self.blood_flow_output_y[idx]     = output_cfs_percent

        self.cond_setpoint_y[idx]         = setpoint_cond
        self.cond_variable_y[idx]         = variable_cond
        self.cond_output_y[idx]           = output_cc_percent

        self.ctd_setpoint_y[idx]          = setpoint_ctd
        self.ctd_variable_y[idx]          = variable_ctd
        self.ctd_output_y[idx]            = output_ctd_percent

        # Avanzar índice circular
        self.plot_idx = (self.plot_idx + 1) % self.history_length

        # Para graficar: usamos np.roll para "mover" el array de forma que el último dato quede al final (derecha)
        # np.roll es eficiente (casi sin copia)
        roll_amount = -self.plot_idx   # negativo para que el idx actual vaya al final
        y_setpoint_cfs_rolled   = np.roll(self.blood_flow_setpoint_y, roll_amount)
        y_variable_cfs_rolled   = np.roll(self.blood_flow_variable_y, roll_amount)
        y_output_cfs_rolled     = np.roll(self.blood_flow_output_y, roll_amount)

        # Repite para cond y ctd (o haz una función helper si prefieres)
        y_setpoint_cond_rolled  = np.roll(self.cond_setpoint_y, roll_amount)
        y_variable_cond_rolled  = np.roll(self.cond_variable_y, roll_amount)
        y_output_cond_rolled    = np.roll(self.cond_output_y, roll_amount)

        y_setpoint_ctd_rolled   = np.roll(self.ctd_setpoint_y, roll_amount)
        y_variable_ctd_rolled   = np.roll(self.ctd_variable_y, roll_amount)
        y_output_ctd_rolled     = np.roll(self.ctd_output_y, roll_amount)

        # Actualizar curvas (pyqtgraph ama NumPy → muy rápido)
        self.curve_cfs_setpoint.setData(self.x_relativa, y_setpoint_cfs_rolled)
        self.curve_cfs_variable.setData(self.x_relativa, y_variable_cfs_rolled)
        self.curve_cfs_output.setData(  self.x_relativa, y_output_cfs_rolled)

        self.curve_cc_setpoint.setData( self.x_relativa, y_setpoint_cond_rolled)
        self.curve_cc_variable.setData(self.x_relativa, y_variable_cond_rolled)
        self.curve_cc_output.setData(   self.x_relativa, y_output_cond_rolled)

        self.curve_ctd_setpoint.setData( self.x_relativa, y_setpoint_ctd_rolled)
        self.curve_ctd_variable.setData(self.x_relativa, y_variable_ctd_rolled)
        self.curve_ctd_output.setData(  self.x_relativa, y_output_ctd_rolled)

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


        




