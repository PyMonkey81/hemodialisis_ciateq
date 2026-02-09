#gui/therapy/therapyCfgScreen.py


# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QGridLayout, QFrame, QLineEdit, QButtonGroup # Importamos QButtonGroup
# )
# from PySide6.QtCore import Qt, Signal
# from PySide6.QtGui import QFont, QColor

# from gui.components.numpad_modal import NumpadDialog 
# from gui.components.time_numpad_modal import TimeNumpadDialog 
# from gui.components.ui_components import ClickableLineEdit 
# import time

# try:
#     from core.variables_map import VARIABLES 
# except ImportError:
#     VARIABLES = {0x01: {}, 0x02: {}} 

# class TempInput:
#     def __init__(self, valor):
#         self.valor = valor
#     def text(self):
#         return str(self.valor)
#     def clearFocus(self):
#         pass 
#     def setText(self, t):
#         pass


# class therapyCfgScr(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.parent = parent  
#         self.valores = parent.valores if parent else {} 
        
#         self.setFixedSize(1536, 726)  
#         self.setStyleSheet("background: #0f172a;") 
#         self.pending_treatment_mode_change_until_ms = None # Cuando se cambia un modo, se guarda el timestamp de hasta cuándo ignorar actualizaciones
#         self.commanded_mode_value = None
#         self.setup_ui()

#     def setup_ui(self):
#         self.setStyleSheet("""
#             background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                        stop:0 #1a2a4a, stop:1 #0f172a); 
#             color: #f8fafc; 
#         """)

#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(40, 30, 40, 30)
#         main_layout.setSpacing(25)

#         title = QLabel("Configuración de Terapia")
#         title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
#         title.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title)

#         sep1 = QFrame()
#         sep1.setFrameShape(QFrame.HLine)
#         sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
#         main_layout.addWidget(sep1)

#         # --- Sección de Selección de Tipo de Tratamiento ---
#         treatment_type_frame = QFrame()
#         treatment_type_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
#         treatment_type_layout = QVBoxLayout(treatment_type_frame)
#         treatment_type_layout.setSpacing(15)

#         lbl_treatment_type = QLabel("Seleccione Tipo de Tratamiento:")
#         lbl_treatment_type.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000;")
#         treatment_type_layout.addWidget(lbl_treatment_type)

#         btn_group_layout = QHBoxLayout()
#         btn_group_layout.setSpacing(20)

#         # Botones para seleccionar el tipo de tratamiento
#         self.btn_hemodialisis = QPushButton("Hemodiálisis")
#         self.btn_hemodiafiltracion = QPushButton("Hemodiafiltración")
#         self.btn_ultrafiltracion = QPushButton("Ultrafiltración")

#         # **BONUS:** Usa QButtonGroup para manejar la exclusividad (solo un botón chequeado a la vez)
#         self.treatment_button_group = QButtonGroup(self)
#         self.treatment_button_group.setExclusive(True) # ¡Esto es clave para la exclusividad!


#         treatment_buttons_info = [
#             (self.btn_hemodialisis, "treatmentModeSelection", 0.0),
#             (self.btn_hemodiafiltracion, "treatmentModeSelection", 1.0),
#             (self.btn_ultrafiltracion, "treatmentModeSelection", 2.0)
#         ]

#         self.style_btn_treatment_unchecked = """
#             QPushButton {
#                 background: #3b82f6; /* Azul brillante */
#                 color: white;
#                 font-size: 24px;
#                 font-weight: bold;
#                 border-radius: 10px;
#                 padding: 15px 25px;
#                 border: 2px solid #2563eb;
#             }
#             QPushButton:hover { background: #60a5fa; }
#             QPushButton:pressed { background: #1e40af; }
#         """
#         self.style_btn_treatment_checked = """
#             QPushButton { /* Estilo para el botón seleccionado */
#                 background: #22c55e; /* Verde */
#                 color: white;
#                 font-size: 24px;
#                 font-weight: bold;
#                 border-radius: 10px;
#                 padding: 15px 25px;
#                 border: 2px solid #16a34a;
#             }
#             QPushButton:hover { background: #22c55e; } /* No cambia color al pasar mouse si está checked */
#             QPushButton:pressed { background: #16a34a; }
#         """


#         for btn, tag, value in treatment_buttons_info:
#             btn.setStyleSheet(self.style_btn_treatment_unchecked)
#             btn.setCheckable(True) 
            
#             # **CORRECCIÓN AQUÍ:** Pasar el botón directamente al lambda
#             btn.toggled.connect(lambda checked_state, b=btn, t=tag, v=value: self._on_treatment_type_toggled(b, t, v, checked_state))
            
#             btn_group_layout.addWidget(btn)
#             self.treatment_button_group.addButton(btn) # Añadir el botón al QButtonGroup
        
#         treatment_type_layout.addLayout(btn_group_layout)
#         main_layout.addWidget(treatment_type_frame)

#         # --- Sección de Entradas de Parámetros ---
#         params_frame = QFrame()
#         params_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
#         params_layout = QGridLayout(params_frame)
#         params_layout.setSpacing(20)

#         # Estilo para los QLabel de los parámetros
#         style_label = "color: #000000; font-size: 22px; font-weight: bold;"
#         # Estilo para los ClickableLineEdit
#         style_input = """
#             ClickableLineEdit {
#                 font-family: Consolas, "Courier New", monospace;
#                 font-size: 24px;
#                 color: #000000;
#                 background: #e2e8f0; /* Gris claro */
#                 border: 2px solid #64748b;
#                 border-radius: 8px;
#                 padding: 5px;
#                 min-width: 100px;
#             }
#             ClickableLineEdit:focus {
#                 border: 2px solid #3b82f6;
#                 background: #ffffff;
#             }
#         """
        
#         # Dosis de Heparina
#         lbl_dosis_hep = QLabel("Dosis Heparina (UI):")
#         lbl_dosis_hep.setStyleSheet(style_label)
#         self.input_dosis_hep = ClickableLineEdit("0.0")
#         self.input_dosis_hep.setFixedSize(120, 50) 
#         self.input_dosis_hep.setAlignment(Qt.AlignCenter)
#         self.input_dosis_hep.setStyleSheet(style_input)
#         self.input_dosis_hep.setReadOnly(True) 
#         self.input_dosis_hep.clicked.connect(
#             lambda: self.open_numpad("heparineTherapyDosage", self.input_dosis_hep, "Dosis Heparina")
#         )
#         params_layout.addWidget(lbl_dosis_hep, 0, 0, Qt.AlignRight)
#         params_layout.addWidget(self.input_dosis_hep, 0, 1)

#         # Flujo de Sangre (Qb) - **Asumo tag de setpoint**
#         lbl_qb = QLabel("Flujo de Sangre (Qb, mL/min):")
#         lbl_qb.setStyleSheet(style_label)
#         self.input_qb = ClickableLineEdit("0.0")
#         self.input_qb.setFixedSize(120, 50)
#         self.input_qb.setAlignment(Qt.AlignCenter)
#         self.input_qb.setStyleSheet(style_input)
#         self.input_qb.setReadOnly(True)
#         self.input_qb.clicked.connect(
#             lambda: self.open_numpad("bloodFlowControlSetPoint", self.input_qb, "Flujo de Sangre (Qb)")
#         )
#         params_layout.addWidget(lbl_qb, 1, 0, Qt.AlignRight)
#         params_layout.addWidget(self.input_qb, 1, 1)
        
#         # Flujo de Dializante (Qd) - **Asumo tag de setpoint**
#         lbl_qd = QLabel("Flujo Dializante (Qd, mL/min):")
#         lbl_qd.setStyleSheet(style_label)
#         self.input_qd = ClickableLineEdit("0.0")
#         self.input_qd.setFixedSize(120, 50)
#         self.input_qd.setAlignment(Qt.AlignCenter)
#         self.input_qd.setStyleSheet(style_input)
#         self.input_qd.setReadOnly(True)
#         self.input_qd.clicked.connect(
#             lambda: self.open_numpad("dialyFlowControlSetPoint", self.input_qd, "Flujo Dializante (Qd)")
#         )
#         params_layout.addWidget(lbl_qd, 2, 0, Qt.AlignRight)
#         params_layout.addWidget(self.input_qd, 2, 1)

#         # Temperatura - **Asumo tag de setpoint**
#         lbl_temp = QLabel("Temperatura (°C):")
#         lbl_temp.setStyleSheet(style_label)
#         self.input_temp = ClickableLineEdit("0.0")
#         self.input_temp.setFixedSize(120, 50)
#         self.input_temp.setAlignment(Qt.AlignCenter)
#         self.input_temp.setStyleSheet(style_input)
#         self.input_temp.setReadOnly(True)
#         self.input_temp.clicked.connect(
#             lambda: self.open_numpad("dialyTempControlSetPoint", self.input_temp, "Temperatura")
#         )
#         params_layout.addWidget(lbl_temp, 0, 2, Qt.AlignRight) 
#         params_layout.addWidget(self.input_temp, 0, 3)

#         # Conductividad - **Asumo tag de setpoint**
#         lbl_cond = QLabel("Conductividad (mS/cm):")
#         lbl_cond.setStyleSheet(style_label)
#         self.input_cond = ClickableLineEdit("0.0")
#         self.input_cond.setFixedSize(120, 50)
#         self.input_cond.setAlignment(Qt.AlignCenter)
#         self.input_cond.setStyleSheet(style_input)
#         self.input_cond.setReadOnly(True)
#         self.input_cond.clicked.connect(
#             lambda: self.open_numpad("dialyCondControlSetPoint", self.input_cond, "Conductividad")
#         )
#         params_layout.addWidget(lbl_cond, 1, 2, Qt.AlignRight) 
#         params_layout.addWidget(self.input_cond, 1, 3)

#         # Sodio (Na+) - **Asumo tag de setpoint**
#         lbl_na = QLabel("Sodio (Na+, mmol/L):")
#         lbl_na.setStyleSheet(style_label)
#         self.input_na = ClickableLineEdit("0.0")
#         self.input_na.setFixedSize(120, 50)
#         self.input_na.setAlignment(Qt.AlignCenter)
#         self.input_na.setStyleSheet(style_input)
#         self.input_na.setReadOnly(True)
#         self.input_na.clicked.connect(
#             lambda: self.open_numpad("sodiumConcentrationSetPoint", self.input_na, "Sodio (Na+)")
#         )
#         params_layout.addWidget(lbl_na, 2, 2, Qt.AlignRight) 
#         params_layout.addWidget(self.input_na, 2, 3)

#         lbl_time_therapy = QLabel("T. Terapia (hh:mm)")
#         lbl_time_therapy.setStyleSheet(style_label)
#         self.input_t_therapy = ClickableLineEdit("00:00")
#         self.input_t_therapy.setFixedSize(120, 50)
#         self.input_t_therapy.setAlignment(Qt.AlignCenter)
#         self.input_t_therapy.setStyleSheet(style_input)
#         self.input_t_therapy.setReadOnly(True)
#         self.input_t_therapy.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_therapy,
#                 tag_hours="heparineTherapyHours", 
#                 tag_minutes="heparineTherapyMinutes",
#                 local_timer_id=None, # Este timer local es regido por este campo
#                 title="Tiempo de terapia"
#             )
#         )
#         hora = self.input_t_therapy.text()
#         print(f"{hora}")
#         params_layout.addWidget(lbl_time_therapy,3, 2)
#         params_layout.addWidget(self.input_t_therapy,3,3)



#         params_layout.setColumnStretch(0, 1)
#         params_layout.setColumnStretch(1, 0) 
#         params_layout.setColumnStretch(2, 1)
#         params_layout.setColumnStretch(3, 0) 
#         params_layout.setColumnStretch(4, 1) 

#         main_layout.addWidget(params_frame)

#         main_layout.addStretch(1) 

#         btn_back = QPushButton("Volver a Diálisis")
#         btn_back.setFixedSize(250, 60)
#         btn_back.setStyleSheet("""
#             QPushButton {
#                 background: #dc2626; 
#                 color: white;
#                 font-size: 20px;
#                 font-weight: bold;
#                 border-radius: 10px;
#                 padding: 10px;
#             }
#             QPushButton:hover { background: #b91c1c; }
#             QPushButton:pressed { background: #991b1b; }
#         """)
#         btn_back.clicked.connect(self.parent.mostrar_pantalla_dialisis)
#         main_layout.addWidget(btn_back, alignment=Qt.AlignRight)


#     # **CORRECCIÓN AQUÍ:** Ahora el método espera el botón como primer argumento
#     def _on_treatment_type_toggled(self, sender_btn: QPushButton, tag: str, value: float, checked: bool):
#         if checked:
#             sender_btn.setStyleSheet(self.style_btn_treatment_checked)
#             self.write_setpoint(tag, value) 
#             self.pending_treatment_mode_change_until_ms = time.monotonic() + 0.7 
#             self.commanded_mode_value = value
#             # Con QButtonGroup, ya no necesitas desmarcar los otros botones manualmente aquí.
#             # El grupo se encarga de la exclusividad.

#         else:
#             sender_btn.setStyleSheet(self.style_btn_treatment_unchecked)

#         # Consideración: si usas QButtonGroup, un botón checkable siempre estará checked
#         # a menos que actives la opción setExclusive(False) o lo desmarques manualmente.
#         # En tu caso, setExclusive(True) es lo correcto para que solo uno esté seleccionado.


#     def actualizar_valores(self, nuevos_valores):
#         self.valores = nuevos_valores
        
#         self.update_input_val(self.input_dosis_hep, "heparineTherapyDosage")
#         self.update_input_val(self.input_qb, "bloodFlowControlSetPoint") 
#         self.update_input_val(self.input_qd, "dialyFlowControlSetPoint") 
#         self.update_input_val(self.input_temp, "dialyTempControlSetPoint") 
#         self.update_input_val(self.input_cond, "dialyCondControlSetPoint") 
#         self.update_input_val(self.input_na, "sodiumConcentrationSetPoint")

#         in_input_t_therapy_hours = int(self.valores.get("heparineTherapyHours", 0)) 
#         in_input_t_therapy_minutes = int(self.valores.get("heparineTherapyMinutes", 0))
#         if not self.input_t_therapy.hasFocus():
#             self.input_t_therapy.setText(f"{in_input_t_therapy_hours:02d}:{in_input_t_therapy_minutes:02d}")

#         current_treatment_mode = self.valores.get("treatmentModeSelection", -1.0) 
#         current_time = time.monotonic()

#     # Si estamos esperando confirmación de un cambio de modo de tratamiento
#         if self.pending_treatment_mode_change_until_ms is not None:
#         # Opción 1: El dispositivo ya nos ha confirmado el cambio esperado
#             if current_treatment_mode == self.commanded_mode_value:
#             # ¡Confirmación recibida! Limpiamos el estado de pendiente
#                 self.pending_treatment_mode_change_until_ms = None
#                 self.commanded_mode_value = None
#             # No necesitamos hacer nada más aquí, el botón ya está optimísticamente marcado.
#                 return # Salimos, no actualizamos los botones en este ciclo
        
#         # Opción 2: Ha pasado el tiempo de espera y el dispositivo NO ha confirmado
#             elif current_time > self.pending_treatment_mode_change_until_ms:
#                 print("[ADVERTENCIA] Timeout esperando confirmación de cambio de modo de tratamiento. Revertiendo UI.")
#                 self.pending_treatment_mode_change_until_ms = None # Limpiamos el estado de pendiente
#                 self.commanded_mode_value = None
#             # Continuamos al bucle para que el UI se actualice con el valor REAL del dispositivo (el anterior)
        
#         # Opción 3: Todavía estamos esperando la confirmación y el timeout no ha pasado
#             else:
#             # Ignoramos la actualización de los botones en este ciclo para evitar el parpadeo
#                 return 
        
#         treatment_buttons_info = [
#             (self.btn_hemodialisis, 0.0), 
#             (self.btn_hemodiafiltracion, 1.0), 
#             (self.btn_ultrafiltracion, 2.0)
#         ]

#         # Iterar para sincronizar el estado de los botones con el valor actual
#         for btn, mode_value in treatment_buttons_info:
#             if current_treatment_mode == mode_value:
#                 if not btn.isChecked(): # Si debería estar marcado, pero no lo está
#                     btn.setChecked(True)
#                     btn.setStyleSheet(self.style_btn_treatment_checked) 
#             else: # Si no debería estar marcado
#                 if btn.isChecked(): # Si está marcado, pero no debería
#                     btn.setChecked(False)
#                     btn.setStyleSheet(self.style_btn_treatment_unchecked) 

#     def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
#         act_value = widget_input.text()
#         dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
#         if dialog.exec(): 
#             new_value = dialog.get_value() 
#             if new_value is not None: 
#                 widget_input.setText(str(new_value))            
#                 self.write_setpoint(tag, widget_input) 


#     def write_setpoint(self, tag, value_or_widget_input):
#         try:
#             valor = None
#             if isinstance(value_or_widget_input, (float, int)):
#                 valor = float(value_or_widget_input)
#                 source_info = f"direct value {valor}"
#                 widget_to_clear_focus = None 
#             elif isinstance(value_or_widget_input, (ClickableLineEdit, QLineEdit)):
#                 widget_input = value_or_widget_input
#                 texto = widget_input.text().replace(',', '.')
#                 if not texto:
#                     print(f"[INFO] Numpad input para {tag} estaba vacío, no se escribió.")
#                     return 
#                 valor = float(texto)
#                 source_info = f"from widget text '{texto}'"
#                 widget_to_clear_focus = widget_input
#             else:
#                 print(f"[ERROR] Tipo de valor inesperado para write_setpoint: {type(value_or_widget_input)}")
#                 return

#             print(f"[SETPOINT] Intentando escribir {tag} = {valor} ({source_info})")

#             target_group = -1
#             target_id = -1
#             found = False

#             for group_key, variables_in_group in VARIABLES.items():
#                 if isinstance(variables_in_group, dict):
#                     for var_id, info in variables_in_group.items():
#                         if info.get("tag") == tag:
#                             target_group = group_key
#                             target_id = var_id
#                             found = True
#                             break
#                 if found: break

#             if found and target_group != -1 and target_id != -1:
#                 if VARIABLES[target_group][target_id].get("rw", False):
#                     print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
#                     if self.parent and hasattr(self.parent, 'serial') and self.parent.serial.conectado:
#                         self.parent.serial.escribir_double(target_group, target_id, valor)
#                     else:
#                         print(f"[INFO] Serial no conectado o no disponible en parent. No se escribió: {tag}={valor}")
#                 else:
#                     print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map). No se escribió.")
#             else:
#                 print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'. No se escribió.")

#             if widget_to_clear_focus:
#                 widget_to_clear_focus.clearFocus()
#             else:
#                 self.setFocus() 

#         except ValueError:
#             if isinstance(value_or_widget_input, (ClickableLineEdit, QLineEdit)):
#                 print(f"[ERROR] Valor numérico inválido en input para {tag}: '{value_or_widget_input.text()}'. Revertiendo a valor actual.")
#                 val = self.valores.get(tag, 0.0)
#                 value_or_widget_input.setText(f"{val:.1f}") 
#                 value_or_widget_input.clearFocus()
#             else:
#                 print(f"[ERROR] Error de conversión a float para tag '{tag}' con valor '{value_or_widget_input}'.")
#         except Exception as e:
#             print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para '{tag}': {e}")


#     def update_input_val(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
#         value = self.valores.get(tag, 0.0)
#         if not widget.hasFocus():
#             widget.setText(f"{value:.{precision}f}")
    
#     def update_label_val(self, label: QLabel, tag: str, precision: int = 1):
#         value = self.valores.get(tag, 0.0)
#         label.setText(f"{value:.{precision}f}")

#     def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
#         """
#         1. Abre el TimeNumpadDialog con el valor actual del widget.
#         2. Al aceptar, actualiza el widget visual a "HH:MM".
#         3. Desglosa Horas y Minutos.
#         4. Si tiene tags, llama a escribir_setpoint para el PLC.
#         5. Si tiene local_timer_id, configura el QTimer correspondiente.
#         """
#         texto_actual = widget_input.text()
#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

#         if dialog.exec():
#             h, m = dialog.get_hours_minutes()
#             widget_input.setText(f"{h:02d}:{m:02d}")
            
#             # Calcular duración total en milisegundos
#             total_ms = (h * 3600 + m * 60) * 1000

#             # 1. Lógica para escribir a la Máquina de Hemodiálisis
#             if tag_hours and tag_minutes:
#                 print(f"[MH_WRITE] Enviando horas ({h}) al tag: {tag_hours}") # Máquina de hemodiálisis
#                 fake_widget_h = TempInput(h) 
#                 self.write_setpoint(tag_hours, fake_widget_h)

#                 print(f"[MH_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}") # Máquina de Hemodiálisis
#                 fake_widget_m = TempInput(m)
#                 self.write_setpoint(tag_minutes, fake_widget_m)
#             elif tag_hours or tag_minutes:
#                 print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

#             # 2. Lógica para configurar QTimer locales de la aplicación
#             if local_timer_id:
#                 state = self._local_timers_state[local_timer_id] # Obtiene la referencia al estado del timer
#                 state["duration_ms"] = total_ms # Guarda la duración total
                
#                 # ### RESETEAR LAS ETIQUETAS DE TIEMPO al configurar una nueva duración
#                 #if state["elapsed_lbl"]: state["elapsed_lbl"].setText("00:00")
#                 #if state["remaining_lbl"]: 
#                  #   state["remaining_lbl"].setText(f"{h:02d}:{m:02d}") # Muestra la duración configurada
#                 if state["elapsed_lbl"] is not None: 
#                     state["elapsed_lbl"].setText("00:00")
                
#                 if state["remaining_lbl"] is not None: 
#                     state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

#                 print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QGridLayout, QFrame, QLineEdit, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import time

from gui.components.numpad_modal import NumpadDialog 
from gui.components.time_numpad_modal import TimeNumpadDialog 
from gui.components.ui_components import ClickableLineEdit 

try:
    from core.variables_map import VARIABLES 
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}} 

# --- ELIMINAR LA CLASE TempInput ---
# Ya no necesitamos esta clase auxiliar.

class therapyCfgScr(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  
        self.valores = parent.valores if parent else {} 
        
        self.setFixedSize(1536, 726)  
        self.setStyleSheet("background: #0f172a;") 
        self.pending_treatment_mode_change_until_ms = None 
        self.commanded_mode_value = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #1a2a4a, stop:1 #0f172a); 
            color: #f8fafc; 
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        title = QLabel("Configuración de Terapia")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep1)

        # --- Sección de Selección de Tipo de Tratamiento ---
        treatment_type_frame = QFrame()
        treatment_type_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        treatment_type_layout = QVBoxLayout(treatment_type_frame)
        treatment_type_layout.setSpacing(15)

        lbl_treatment_type = QLabel("Seleccione Tipo de Tratamiento:")
        lbl_treatment_type.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000;")
        treatment_type_layout.addWidget(lbl_treatment_type)

        btn_group_layout = QHBoxLayout()
        btn_group_layout.setSpacing(20)

        # Botones para seleccionar el tipo de tratamiento
        self.btn_hemodialisis = QPushButton("Hemodiálisis")
        self.btn_hemodiafiltracion = QPushButton("Hemodiafiltración")
        self.btn_ultrafiltracion = QPushButton("Ultrafiltración")

        self.treatment_button_group = QButtonGroup(self)
        self.treatment_button_group.setExclusive(True) 


        treatment_buttons_info = [
            (self.btn_hemodialisis, "treatmentModeSelection", 0.0),
            (self.btn_hemodiafiltracion, "treatmentModeSelection", 1.0),
            (self.btn_ultrafiltracion, "treatmentModeSelection", 2.0)
        ]

        self.style_btn_treatment_unchecked = """
            QPushButton {
                background: #3b82f6; 
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px 25px;
                border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
            QPushButton:pressed { background: #1e40af; }
        """
        self.style_btn_treatment_checked = """
            QPushButton { 
                background: #22c55e; 
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px 25px;
                border: 2px solid #16a34a;
            }
            QPushButton:hover { background: #22c55e; } 
            QPushButton:pressed { background: #16a34a; }
        """

        for btn, tag, value in treatment_buttons_info:
            btn.setStyleSheet(self.style_btn_treatment_unchecked)
            btn.setCheckable(True) 
            btn.toggled.connect(lambda checked_state, b=btn, t=tag, v=value: self._on_treatment_type_toggled(b, t, v, checked_state))
            btn_group_layout.addWidget(btn)
            self.treatment_button_group.addButton(btn) 
        
        treatment_type_layout.addLayout(btn_group_layout)
        main_layout.addWidget(treatment_type_frame)

        # --- Sección de Entradas de Parámetros ---
        params_frame = QFrame()
        params_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        params_layout = QGridLayout(params_frame)
        params_layout.setSpacing(20)

        style_label = "color: #000000; font-size: 22px; font-weight: bold;"
        style_input = """
            ClickableLineEdit {
                font-family: Consolas, "Courier New", monospace;
                font-size: 24px;
                color: #000000;
                background: #e2e8f0; 
                border: 2px solid #64748b;
                border-radius: 8px;
                padding: 5px;
                min-width: 100px;
            }
            ClickableLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
            }
        """
        
        # Dosis de Heparina
        lbl_dosis_hep = QLabel("Dosis Heparina (UI):")
        lbl_dosis_hep.setStyleSheet(style_label)
        self.input_dosis_hep = ClickableLineEdit("0.0")
        self.input_dosis_hep.setFixedSize(120, 50) 
        self.input_dosis_hep.setAlignment(Qt.AlignCenter)
        self.input_dosis_hep.setStyleSheet(style_input)
        self.input_dosis_hep.setReadOnly(True) 
        self.input_dosis_hep.clicked.connect(
            lambda: self.open_numpad("heparineTherapyDosage", self.input_dosis_hep, "Dosis Heparina")
        )
        params_layout.addWidget(lbl_dosis_hep, 0, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_dosis_hep, 0, 1)

        # Flujo de Sangre (Qb) - **Asumo tag de setpoint**
        lbl_qb = QLabel("Flujo de Sangre (Qb, mL/min):")
        lbl_qb.setStyleSheet(style_label)
        self.input_qb = ClickableLineEdit("0.0")
        self.input_qb.setFixedSize(120, 50)
        self.input_qb.setAlignment(Qt.AlignCenter)
        self.input_qb.setStyleSheet(style_input)
        self.input_qb.setReadOnly(True)
        self.input_qb.clicked.connect(
            lambda: self.open_numpad("bloodFlowControlSetPoint", self.input_qb, "Flujo de Sangre (Qb)")
        )
        params_layout.addWidget(lbl_qb, 1, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_qb, 1, 1)
        
        # Flujo de Dializante (Qd) - **Asumo tag de setpoint**
        lbl_qd = QLabel("Flujo Dializante (Qd, mL/min):")
        lbl_qd.setStyleSheet(style_label)
        self.input_qd = ClickableLineEdit("0.0")
        self.input_qd.setFixedSize(120, 50)
        self.input_qd.setAlignment(Qt.AlignCenter)
        self.input_qd.setStyleSheet(style_input)
        self.input_qd.setReadOnly(True)
        self.input_qd.clicked.connect(
            lambda: self.open_numpad("dialyFlowControlSetPoint", self.input_qd, "Flujo Dializante (Qd)")
        )
        params_layout.addWidget(lbl_qd, 2, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_qd, 2, 1)

        # Temperatura - **Asumo tag de setpoint**
        lbl_temp = QLabel("Temperatura (°C):")
        lbl_temp.setStyleSheet(style_label)
        self.input_temp = ClickableLineEdit("0.0")
        self.input_temp.setFixedSize(120, 50)
        self.input_temp.setAlignment(Qt.AlignCenter)
        self.input_temp.setStyleSheet(style_input)
        self.input_temp.setReadOnly(True)
        self.input_temp.clicked.connect(
            lambda: self.open_numpad("dialyTempControlSetPoint", self.input_temp, "Temperatura")
        )
        params_layout.addWidget(lbl_temp, 0, 2, Qt.AlignRight) 
        params_layout.addWidget(self.input_temp, 0, 3)

        # Conductividad - **Asumo tag de setpoint**
        lbl_cond = QLabel("Conductividad (mS/cm):")
        lbl_cond.setStyleSheet(style_label)
        self.input_cond = ClickableLineEdit("0.0")
        self.input_cond.setFixedSize(120, 50)
        self.input_cond.setAlignment(Qt.AlignCenter)
        self.input_cond.setStyleSheet(style_input)
        self.input_cond.setReadOnly(True)
        self.input_cond.clicked.connect(
            lambda: self.open_numpad("dialyCondControlSetPoint", self.input_cond, "Conductividad")
        )
        params_layout.addWidget(lbl_cond, 1, 2, Qt.AlignRight) 
        params_layout.addWidget(self.input_cond, 1, 3)

        # Sodio (Na+) - **Asumo tag de setpoint**
        lbl_na = QLabel("Sodio (Na+, mmol/L):")
        lbl_na.setStyleSheet(style_label)
        self.input_na = ClickableLineEdit("0.0")
        self.input_na.setFixedSize(120, 50)
        self.input_na.setAlignment(Qt.AlignCenter)
        self.input_na.setStyleSheet(style_input)
        self.input_na.setReadOnly(True)
        self.input_na.clicked.connect(
            lambda: self.open_numpad("sodiumConcentrationSetPoint", self.input_na, "Sodio (Na+)")
        )
        params_layout.addWidget(lbl_na, 2, 2, Qt.AlignRight) 
        params_layout.addWidget(self.input_na, 2, 3)

        # Tiempo de Terapia (Horas y Minutos separados)
        lbl_time_therapy = QLabel("T. Terapia (hh:mm)")
        lbl_time_therapy.setStyleSheet(style_label)
        self.input_t_therapy = ClickableLineEdit("00:00")
        self.input_t_therapy.setFixedSize(120, 50)
        self.input_t_therapy.setAlignment(Qt.AlignCenter)
        self.input_t_therapy.setStyleSheet(style_input)
        self.input_t_therapy.setReadOnly(True)
        self.input_t_therapy.clicked.connect(
            lambda: self.open_time_numpad(
                self.input_t_therapy,
                tag_hours="heparineTherapyHours", # <<< ASUMO ESTOS TAGS PARA TIEMPO DE TERAPIA
                tag_minutes="heparineTherapyMinutes", # <<< ASUMO ESTOS TAGS PARA TIEMPO DE TERAPIA
                local_timer_id=None, 
                title="Tiempo de terapia"
            )
        )
        params_layout.addWidget(lbl_time_therapy,3, 2)
        params_layout.addWidget(self.input_t_therapy,3,3)


        params_layout.setColumnStretch(0, 1)
        params_layout.setColumnStretch(1, 0) 
        params_layout.setColumnStretch(2, 1)
        params_layout.setColumnStretch(3, 0) 
        params_layout.setColumnStretch(4, 1) 

        main_layout.addWidget(params_frame)

        main_layout.addStretch(1) 

        btn_back = QPushButton("Volver a Diálisis")
        btn_back.setFixedSize(250, 60)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #dc2626; 
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
        """)
        btn_back.clicked.connect(self.parent.mostrar_pantalla_dialisis)
        main_layout.addWidget(btn_back, alignment=Qt.AlignRight)


    def _on_treatment_type_toggled(self, sender_btn: QPushButton, tag: str, value: float, checked: bool):
        if checked:
            sender_btn.setStyleSheet(self.style_btn_treatment_checked)
            self.write_setpoint(tag, value) 
            self.pending_treatment_mode_change_until_ms = time.monotonic() + 0.7 
            self.commanded_mode_value = value
        else:
            sender_btn.setStyleSheet(self.style_btn_treatment_unchecked)


    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores
        
        self.update_input_val(self.input_dosis_hep, "heparineTherapyDosage")
        self.update_input_val(self.input_qb, "bloodFlowControlSetPoint") 
        self.update_input_val(self.input_qd, "dialyFlowControlSetPoint") 
        self.update_input_val(self.input_temp, "dialyTempControlSetPoint") 
        self.update_input_val(self.input_cond, "dialyCondControlSetPoint") 
        self.update_input_val(self.input_na, "sodiumConcentrationSetPoint")

        # --- CORRECCIÓN AQUÍ: Usar un método para el tiempo ---
        self.update_time_input_val(self.input_t_therapy, "heparineTherapyHours", "heparineTherapyMinutes")

        current_treatment_mode = self.valores.get("treatmentModeSelection", -1.0) 
        current_time = time.monotonic()

        if self.pending_treatment_mode_change_until_ms is not None:
            if current_treatment_mode == self.commanded_mode_value:
                self.pending_treatment_mode_change_until_ms = None
                self.commanded_mode_value = None
                return 
            elif current_time > self.pending_treatment_mode_change_until_ms:
                print("[ADVERTENCIA] Timeout esperando confirmación de cambio de modo de tratamiento. Revertiendo UI.")
                self.pending_treatment_mode_change_until_ms = None 
                self.commanded_mode_value = None
            else:
                return 
        
        treatment_buttons_info = [
            (self.btn_hemodialisis, 0.0), 
            (self.btn_hemodiafiltracion, 1.0), 
            (self.btn_ultrafiltracion, 2.0)
        ]

        for btn, mode_value in treatment_buttons_info:
            if current_treatment_mode == mode_value:
                if not btn.isChecked(): 
                    btn.setChecked(True)
                    btn.setStyleSheet(self.style_btn_treatment_checked) 
            else: 
                if btn.isChecked(): 
                    btn.setChecked(False)
                    btn.setStyleSheet(self.style_btn_treatment_unchecked) 

    def open_numpad(self, tag, widget_input, text_="Ingrese valor"):
        act_value = widget_input.text()
        dialog = NumpadDialog(self, initial_value=act_value, title=text_)        
        if dialog.exec(): 
            new_value = dialog.get_value() 
            if new_value is not None: 
                widget_input.setText(str(new_value))            
                self.write_setpoint(tag, widget_input) 


    def write_setpoint(self, tag, value_or_widget_input):
        """
        Método unificado para escribir setpoints.
        Puede recibir un valor numérico directo o un ClickableLineEdit.
        """
        try:
            valor = None
            if isinstance(value_or_widget_input, (float, int)): # Valor directo
                valor = float(value_or_widget_input)
                source_info = f"direct value {valor}"
                widget_to_clear_focus = None 
            elif isinstance(value_or_widget_input, (ClickableLineEdit, QLineEdit)): # Valor de un widget
                widget_input = value_or_widget_input
                texto = widget_input.text().replace(',', '.')
                if not texto:
                    print(f"[INFO] Numpad input para {tag} estaba vacío, no se escribió.")
                    return 
                valor = float(texto)
                source_info = f"from widget text '{texto}'"
                widget_to_clear_focus = widget_input
            else:
                print(f"[ERROR] Tipo de valor inesperado para write_setpoint: {type(value_or_widget_input)}")
                return

            print(f"[SETPOINT] Intentando escribir {tag} = {valor} ({source_info})")

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
                    # --- CORRECCIÓN IMPORTANTE: USAR self.parent ---
                    if self.parent and hasattr(self.parent, 'serial') and self.parent.serial.conectado:
                        self.parent.serial.escribir_double(target_group, target_id, valor)
                    else:
                        print(f"[INFO] Serial no conectado o no disponible en parent. No se escribió: {tag}={valor}")
                else:
                    print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map). No se escribió.")
            else:
                print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'. No se escribió.")

            if widget_to_clear_focus:
                widget_to_clear_focus.clearFocus()
            else:
                self.setFocus() 

        except ValueError:
            if isinstance(value_or_widget_input, (ClickableLineEdit, QLineEdit)):
                print(f"[ERROR] Valor numérico inválido en input para {tag}: '{value_or_widget_input.text()}'. Revertiendo a valor actual.")
                val = self.valores.get(tag, 0.0)
                value_or_widget_input.setText(f"{val:.1f}") 
                value_or_widget_input.clearFocus()
            else:
                print(f"[ERROR] Error de conversión a float para tag '{tag}' con valor '{value_or_widget_input}'.")
        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para '{tag}': {e}")


    def update_input_val(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        value = self.valores.get(tag, 0.0)
        if not widget.hasFocus():
            widget.setText(f"{value:.{precision}f}")
    
    def update_time_input_val(self, widget: ClickableLineEdit, tag_hours: str, tag_minutes: str):
        """
        Actualiza un ClickableLineEdit con formato HH:MM a partir de dos tags (horas y minutos).
        Solo actualiza si el widget no tiene el foco.
        """
        if not widget.hasFocus():
            hours = int(self.valores.get(tag_hours, 0))
            minutes = int(self.valores.get(tag_minutes, 0))
            widget.setText(f"{hours:02d}:{minutes:02d}")

    def update_label_val(self, label: QLabel, tag: str, precision: int = 1):
        value = self.valores.get(tag, 0.0)
        label.setText(f"{value:.{precision}f}")

    def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
        """
        1. Abre el TimeNumpadDialog con el valor actual del widget.
        2. Al aceptar, actualiza el widget visual a "HH:MM".
        3. Desglosa Horas y Minutos.
        4. Si tiene tags, llama a escribir_setpoint para el PLC.
        5. Si tiene local_timer_id, configura el QTimer correspondiente.
        """
        texto_actual = widget_input.text()
        dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

        if dialog.exec():
            h, m = dialog.get_hours_minutes()
            # Si el numpad devuelve None (ej. el usuario cerró sin aceptar), no actualizamos
            if h is not None and m is not None:
                widget_input.setText(f"{h:02d}:{m:02d}")
                
                # Calcular duración total en milisegundos (si es relevante para el timer local)
                total_ms = (h * 3600 + m * 60) * 1000

                # 1. Lógica para escribir a la Máquina de Hemodiálisis (ahora pasando float(h) y float(m))
                if tag_hours and tag_minutes:
                    print(f"[MH_WRITE] Enviando horas ({h}) al tag: {tag_hours}") 
                    self.write_setpoint(tag_hours, float(h)) # <-- PASAMOS FLOAT DIRECTAMENTE

                    print(f"[MH_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}") 
                    self.write_setpoint(tag_minutes, float(m)) # <-- PASAMOS FLOAT DIRECTAMENTE
                elif tag_hours or tag_minutes:
                    print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

                # 2. Lógica para configurar QTimer locales de la aplicación
                # (Esta parte de local_timer_id y _local_timers_state no está definida en la clase,
                # pero asumo que existe en tu implementación completa si la usas)
                if local_timer_id and hasattr(self, '_local_timers_state'):
                    state = self._local_timers_state[local_timer_id] 
                    state["duration_ms"] = total_ms 
                    
                    if state["elapsed_lbl"] is not None: 
                        state["elapsed_lbl"].setText("00:00")
                    
                    if state["remaining_lbl"] is not None: 
                        state["remaining_lbl"].setText(f"{h:02d}:{m:02d}")

                    print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")
            else:
                print("[INFO] Numpad de tiempo cerrado sin seleccionar un nuevo valor.")
