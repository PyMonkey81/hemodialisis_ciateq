#gui/service/ctrlCfgScreen.py
#Configuración de bajo nivel, calibración de sensores y
#  acceso al registro de errores técnicos. configuración de controladores de bombas

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import pyqtgraph as pg
from collections import deque


from gui.components.numpad_modal import NumpadDialog

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


class ClickableLineEdit(QLineEdit):
    clicked = Signal() # Señal 
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ToggleBox(QFrame):
    def __init__(self, label, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #fcfcfc;
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl_info = QLabel(f"<b>{label}</b>")
        lbl_info.setStyleSheet("color: #000000; font-size: 18px; border:none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.toggle = ToggleSwitch(width=60, height=30)

        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(self.toggle)



class DoubleToggleBox(QFrame):
    def __init__(self, label1_text, label2_text, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8; /* Un fondo ligeramente diferente para destacar */
                border-radius: 8px;
                border: 1px solid #334155;
            }
        """)
        self.setFixedHeight(120) # Ajusta la altura si es necesario para acomodar dos filas

        # Layout principal de la DoubleToggleBox (vertical)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5) # Menos espacio vertical entre las filas

        # --- Primera Fila: Label 1 y Toggle 1 ---
        row1_layout = QHBoxLayout()
        lbl1 = QLabel(f"<b>{label1_text}</b>")
        lbl1.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl1.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle1 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row1_layout.addWidget(lbl1)
        row1_layout.addStretch()
        row1_layout.addWidget(self.toggle1)
        main_layout.addLayout(row1_layout)

        # --- Segunda Fila: Label 2 y Toggle 2 ---
        row2_layout = QHBoxLayout()
        lbl2 = QLabel(f"<b>{label2_text}</b>")
        lbl2.setStyleSheet("color: #000000; font-size: 16px; border:none; background: transparent;")
        lbl2.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.toggle2 = ToggleSwitch(width=60, height=30) # Almacenar como atributo

        row2_layout.addWidget(lbl2)
        row2_layout.addStretch()
        row2_layout.addWidget(self.toggle2)
        main_layout.addLayout(row2_layout)



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

        self.blood_flow_history_length = 600 # Número de puntos a mostrar (ej. 10 minutos a 1 actualiz/seg = 600 puntos)
                                              # Ajusta este valor según cuántos segundos/puntos quieras ver en pantalla.
        self.blood_flow_x = deque(maxlen=self.blood_flow_history_length)
        self.blood_flow_setpoint_y = deque(maxlen=self.blood_flow_history_length)
        self.blood_flow_variable_y = deque(maxlen=self.blood_flow_history_length)
        self.blood_flow_output_y = deque(maxlen=self.blood_flow_history_length)
        self.blood_flow_time_counter = 0 # Contador que siempre aumenta

        self.cond_history_length = 600
        self.cond_x = deque(maxlen=self.cond_history_length)
        self.cond_setpoint_y = deque(maxlen=self.cond_history_length)
        self.cond_variable_y = deque(maxlen=self.cond_history_length)
        self.cond_output_y = deque(maxlen=self.cond_history_length)
        #self.cond_time_counter = 0

        self.ctd_history_length = 600
        self.ctd_x = deque(maxlen=self.ctd_history_length)
        self.ctd_setpoint_y = deque(maxlen=self.ctd_history_length)
        self.ctd_variable_y = deque(maxlen=self.ctd_history_length)
        self.ctd_output_y = deque(maxlen=self.ctd_history_length)

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
        # Curva para Variable CFS
        self.curve_cfs_variable = self.plot_cfs.plot(pen=pg.mkPen(color=(0, 150, 0), width=2), name="Variable CFS")
        # Curva para Salida CFS
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
        # COLUMNA 2 ZONA DE SETPOINTS KP, KD, KI DE CONTOLES
        #=====================================================================================




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

    def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
        act_value = widget_input.text()
        dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
        if dialog.exec(): 
            new_value = dialog.get_value() 
            widget_input.setText(str(new_value))            
            self.escribir_setpoint(tag, widget_input)

    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores

        # --- Actualizar datos de la gráfica CFS, Cond. y Temperatura ---
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


        # Añadir nuevos datos al historial
        self.blood_flow_x.append(self.blood_flow_time_counter)
        self.blood_flow_setpoint_y.append(setpoint_cfs)
        self.blood_flow_variable_y.append(variable_cfs)
        self.blood_flow_output_y.append(output_cfs_percent)
        
        self.blood_flow_time_counter += 1

        self.cond_x.append(self.blood_flow_time_counter)
        self.cond_setpoint_y.append(setpoint_cond)
        self.cond_variable_y.append(variable_cond)
        self.cond_output_y.append(output_cc_percent)

        self.ctd_x.append(self.blood_flow_time_counter)
        self.ctd_setpoint_y.append(setpoint_ctd)
        self.ctd_variable_y.append(variable_ctd)
        self.ctd_output_y.append(output_ctd_percent)


        # Actualizar las curvas de la gráfica
        self.curve_cfs_setpoint.setData(list(self.blood_flow_x), list(self.blood_flow_setpoint_y))
        self.curve_cfs_variable.setData(list(self.blood_flow_x), list(self.blood_flow_variable_y))
        self.curve_cfs_output.setData(list(self.blood_flow_x), list(self.blood_flow_output_y))

        self.curve_cc_setpoint.setData(list(self.cond_x), list(self.cond_setpoint_y))
        self.curve_cc_variable.setData(list(self.cond_x), list(self.cond_variable_y))
        self.curve_cc_output.setData(list(self.cond_x), list(self.cond_output_y))

        self.curve_ctd_setpoint.setData(list(self.ctd_x), list(self.ctd_setpoint_y))
        self.curve_ctd_variable.setData(list(self.ctd_x), list(self.ctd_variable_y))
        self.curve_ctd_output.setData(list(self.ctd_x), list(self.ctd_output_y))

        # --- APLICAR SCROLLING AL EJE X ---
        # Definir el rango visible del eje X
        # El máximo será el contador actual
        current_x_max = self.blood_flow_time_counter 
        # El mínimo será el máximo menos la longitud del historial.
        # Aseguramos que no vaya por debajo de 0 al inicio.
        current_x_min = max(0, current_x_max - self.blood_flow_history_length)
        
        self.plot_cfs.setXRange(current_x_min, current_x_max)
        self.plot_cc.setXRange(current_x_min, current_x_max)
        self.plot_ctd.setXRange(current_x_min, current_x_max)





