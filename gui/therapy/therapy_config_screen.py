# gui/therapy/therapy_config_screen.py
# Pantalla de configuración de parámetros de terapia (sin selección de modo)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, 
)
from PySide6.QtCore import Qt, Signal, QDateTime

import logging
from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.ui_components import ClickableLineEdit
from logic.calculos import convertir_flujo_a_ciclos, convertir_ciclos_a_flujo

logger = logging.getLogger(__name__)

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}


class TherapyConfigScreen(QWidget):
    """
    Pantalla de configuración de parámetros numéricos para la terapia.
    Solo inputs de heparina, flujos, temperatura, conductividad, sodio y duración.
    """
    valueChanged = Signal(str, float)  # Emite el tag y el nuevo valor



    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}

        self.setFixedSize(1536, 726)   # cambiar por sizepolicy
        self.setStyleSheet("background: #0f172a;")
        self.write_hold_off = {}
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
        logger.info("Configuracion de terapia (V1.0.0)")
        # Título
        title = QLabel("Configuración de Terapia")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #60a5fa;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #fcfcfc; max-height: 2px;")
        main_layout.addWidget(sep1)

        # ── Parámetros ───────────────────────────────────────────────────────
        params_frame = QFrame()
        params_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 25px;")
        params_layout = QGridLayout(params_frame)
        params_layout.setSpacing(20)

        label_style = "color: #000000; font-size: 22px; font-weight: bold;"
        input_style = """
            ClickableLineEdit {
                font-family: Consolas, "Courier New", monospace;
                font-size: 24px;
                color: #000000;
                background: #e2e8f0;
                border: 2px solid #64748b;
                border-radius: 8px;
                padding: 5px;
                min-width: 110px;
            }
            ClickableLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
            }
        """

        # Heparina
        lbl_heparin = QLabel("Dosis Heparina (UI):")
        lbl_heparin.setStyleSheet(label_style)
        self.input_heparin = ClickableLineEdit("0.0")
        self.input_heparin.setFixedSize(120, 50)
        self.input_heparin.setAlignment(Qt.AlignCenter)
        self.input_heparin.setStyleSheet(input_style)
        self.input_heparin.setReadOnly(True)
        self.input_heparin.clicked.connect(
            lambda: self.open_numpad("heparineTherapyDosage", self.input_heparin, "Dosis Heparina")
        )
        params_layout.addWidget(lbl_heparin, 0, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_heparin, 0, 1)

        # Flujo de Sangre (Qb)
        lbl_blood_flow = QLabel("Flujo de Sangre (Qb, mL/min):")
        lbl_blood_flow.setStyleSheet(label_style)
        self.input_blood_flow = ClickableLineEdit("0.0")
        self.input_blood_flow.setFixedSize(120, 50)
        self.input_blood_flow.setAlignment(Qt.AlignCenter)
        self.input_blood_flow.setStyleSheet(input_style)
        self.input_blood_flow.setReadOnly(True)
        self.input_blood_flow.clicked.connect(
            lambda: self.open_numpad("bloodFlowControlSetPoint", self.input_blood_flow, "Flujo de Sangre (Qb)")
        )
        params_layout.addWidget(lbl_blood_flow, 1, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_blood_flow, 1, 1)

        # Flujo Dializante (Qd)
        lbl_dialysate_flow = QLabel("Flujo Dializante (Qd, mL/min):")   # FLUJO DE CÁMARA DE BALANCE
        lbl_dialysate_flow.setStyleSheet(label_style)
        self.input_dialysate_flow = ClickableLineEdit("0.0")
        self.input_dialysate_flow.setFixedSize(120, 50)
        self.input_dialysate_flow.setAlignment(Qt.AlignCenter)
        self.input_dialysate_flow.setStyleSheet(input_style)
        self.input_dialysate_flow.setReadOnly(True)
        self.input_dialysate_flow.clicked.connect(self._handle_cb_flow_input)
        params_layout.addWidget(lbl_dialysate_flow, 2, 0, Qt.AlignRight)
        params_layout.addWidget(self.input_dialysate_flow, 2, 1)

        # Temperatura
        lbl_temperature = QLabel("Temperatura (°C):")
        lbl_temperature.setStyleSheet(label_style)
        self.input_temperature = ClickableLineEdit("0.0")
        self.input_temperature.setFixedSize(120, 50)
        self.input_temperature.setAlignment(Qt.AlignCenter)
        self.input_temperature.setStyleSheet(input_style)
        self.input_temperature.setReadOnly(True)
        self.input_temperature.clicked.connect(
            lambda: self.open_numpad("dialyTempControlSetPoint", self.input_temperature, "Temperatura")
        )
        params_layout.addWidget(lbl_temperature, 0, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_temperature, 0, 3)

        # Conductividad
        lbl_conductivity = QLabel("Conductividad (mS/cm):")
        lbl_conductivity.setStyleSheet(label_style)
        self.input_conductivity = ClickableLineEdit("0.0")
        self.input_conductivity.setFixedSize(120, 50)
        self.input_conductivity.setAlignment(Qt.AlignCenter)
        self.input_conductivity.setStyleSheet(input_style)
        self.input_conductivity.setReadOnly(True)
        self.input_conductivity.clicked.connect(
            lambda: self.open_numpad("dialyCondControlSetPoint", self.input_conductivity, "Conductividad")
        )
        params_layout.addWidget(lbl_conductivity, 1, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_conductivity, 1, 3)

        # Sodio (Na+)
        lbl_sodium = QLabel("Sodio (Na+, mmol/L):")
        lbl_sodium.setStyleSheet(label_style)
        self.input_sodium = ClickableLineEdit("0.0")
        self.input_sodium.setFixedSize(120, 50)
        self.input_sodium.setAlignment(Qt.AlignCenter)
        self.input_sodium.setStyleSheet(input_style)
        self.input_sodium.setReadOnly(True)
        self.input_sodium.clicked.connect(
            lambda: self.open_numpad("sodiumConcentrationSetPoint", self.input_sodium, "Sodio (Na+)")
        )
        params_layout.addWidget(lbl_sodium, 2, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_sodium, 2, 3)

        # Duración de Terapia (hh:mm)
        lbl_duration = QLabel("T. Terapia (hh:mm)")
        lbl_duration.setStyleSheet(label_style)
        self.input_duration = ClickableLineEdit("00:00")
        self.input_duration.setFixedSize(120, 50)
        self.input_duration.setAlignment(Qt.AlignCenter)
        self.input_duration.setStyleSheet(input_style)
        self.input_duration.setReadOnly(True)
        self.input_duration.clicked.connect(
            lambda: self.open_time_numpad(
                self.input_duration,
                tag_hours="heparineTherapyHours",
                tag_minutes="heparineTherapyMinutes",
                title="Tiempo de terapia"
            )
        )
        params_layout.addWidget(lbl_duration, 3, 2, Qt.AlignRight)
        params_layout.addWidget(self.input_duration, 3, 3)

        params_layout.setColumnStretch(0, 1)
        params_layout.setColumnStretch(1, 0)
        params_layout.setColumnStretch(2, 1)
        params_layout.setColumnStretch(3, 0)

        main_layout.addWidget(params_frame)
        main_layout.addStretch(1)

        # Botón Volver
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
        btn_back.clicked.connect(self.parent_window.show_dialysis_screen)
        main_layout.addWidget(btn_back, alignment=Qt.AlignRight)

    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
        current_text = input_widget.text()
        dialog = NumpadDialog(self, initial_value="", title=title)

        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                input_widget.setText(str(new_value))                            
                self._write_setpoint(tag, float(new_value))
                               
                if hasattr(input_widget, 'clearFocus'):
                    input_widget.clearFocus()
                self.setFocus()



    def open_time_numpad(self, input_widget: ClickableLineEdit,
                         tag_hours: str = None, tag_minutes: str = None,
                         title: str = "Config. Tiempo"):
        current_text = input_widget.text()
        # dialog = TimeNumpadDialog(self, initial_hh_mm=current_text, title=title)
        dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                input_widget.setText(f"{hours:02d}:{minutes:02d}")
                input_widget.clearFocus()  
                if tag_hours:
                    self.current_values[tag_hours] = float(hours)
                    self.parent_window.current_values[tag_hours] = float(hours)
                     

                if tag_minutes:
                    self.current_values[tag_minutes] = float(minutes)
                    self.parent_window.current_values[tag_minutes] = float(minutes)

                if tag_hours and tag_minutes:
                    self._write_setpoint(tag_hours, float(hours))
                    self._write_setpoint(tag_minutes, float(minutes))

    def _write_setpoint(self, tag: str, value: float):
        try:
            print(f"[SETPOINT] Escribiendo {tag} = {value}")

            target_group = -1
            target_id = -1
            found = False

            for group_key, vars_in_group in VARIABLES.items():
                if isinstance(vars_in_group, dict):
                    for var_id, info in vars_in_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found:
                    break

            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    if self.parent_window and hasattr(self.parent_window, 'serial_comm'):
                        if self.parent_window.serial_comm.is_connected:
                            self.parent_window.serial_comm.write_double(target_group, target_id, value)
                            self.valueChanged.emit(tag, float(value)) 
                            self.current_values[tag] = float(value)

                        else:
                            print(f"[INFO] Serial no conectado. Skip: {tag}={value}")
                    else:
                        print(f"[INFO] No hay serial_comm. Skip: {tag}={value}")
                else:
                    print(f"[WARNING] Variable '{tag}' no escribible (rw=False)")
            else:
                print(f"[ERROR] Tag '{tag}' no encontrado en variables map")

        except Exception as e:
            print(f"[ERROR] Fallo al escribir setpoint '{tag}': {e}")

    # def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
    #     if not widget.hasFocus():
    #         value = self.current_values.get(tag, 0.0)
    #         widget.setText(f"{value:.{precision}f}")


    def _update_time_display(self, widget: ClickableLineEdit, tag_hours: str, tag_minutes: str):
        if not widget.hasFocus():
            hours = int(self.current_values.get(tag_hours, 0))
            minutes = int(self.current_values.get(tag_minutes, 0))
            widget.setText(f"{hours:02d}:{minutes:02d}")

    def update_values(self, new_values: dict):
        """Actualiza solo los campos numéricos y de tiempo"""

        self.current_values = new_values
        current_ms = QDateTime.currentMSecsSinceEpoch()

        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_blood_flow, "bloodFlowControlSetPoint")
        self._update_input_display(self.input_temperature, "dialyTempControlSetPoint")
        self._update_input_display(self.input_conductivity, "dialyCondControlSetPoint")
        self._update_input_display(self.input_sodium, "sodiumConcentrationSetPoint")

        self._update_time_display(self.input_duration, "heparineTherapyHours", "heparineTherapyMinutes")
        tag_cb = "balanceChamberSetTiming"
        hold_time = self.write_hold_off.get(tag_cb, 0)

        if current_ms < hold_time:
            pass
        else:
            raw_cycles = self.current_values.get(tag_cb,0.0)
            try:
                if raw_cycles == 0:
                    flow_to_show = 0.0
                else:
                    flow_to_show = convertir_ciclos_a_flujo(raw_cycles)
                    if not self.input_dialysate_flow.hasFocus():
                        self.input_dialysate_flow.setText(f"{flow_to_show:.1f}")
            except Exception as e:
                self.input_dialysate_flow.setText("0.0")



    def _handle_cb_flow_input(self):
        """
        Maneja el input del usuario:
        1. Abre el numpad para pedir mL/min.
        2. Convierte mL/min -> Ciclos/timing.
        3. Escribe el valor en ciclos a la máquina.
        """
        # Obtenemos el texto actual del widget correcto
        current_text = self.input_dialysate_flow.text()

        dialog = NumpadDialog(self, initial_value="", title="Flujo Dializante (mL/min)")
        
        if dialog.exec():
            # El usuario ingresó un valor en mL/min (ej: 500)
            value_str = dialog.get_value()
            if not value_str:return 

            flow_ml_min = float(value_str)            

            self.input_dialysate_flow.setText(f"{flow_ml_min:.1f}")
            self.input_dialysate_flow.clearFocus()
            self.setFocus()
            
            try:
                cycles_value = convertir_flujo_a_ciclos(flow_ml_min)                               
                tag = "balanceChamberSetTiming"
                self._write_setpoint(tag, cycles_value)                               
                self.write_hold_off["balanceChamberSetTiming"] = QDateTime.currentMSecsSinceEpoch() + 3000
                
            except Exception as e:
                logger.error(f"Error convirtiendo flujo a ciclos: {e}")

    def _update_input_display(self, widget: ClickableLineEdit, tag_or_value, precision: int = 1):
        if widget.hasFocus():
            self.setFocus()
            return
        val_to_show = 0.0
        
        if isinstance(tag_or_value, str):
            # Es un tag, lo buscamos en el diccionario
            val_to_show = self.current_values.get(tag_or_value, 0.0)
        elif isinstance(tag_or_value, (int, float)):
            # Es un valor directo (útil si ya hiciste la conversión afuera)
            val_to_show = tag_or_value

        widget.setText(f"{val_to_show:.{precision}f}")


    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

 