# gui/therapy/heparin_config_screenV2.py

from PySide6.QtWidgets import (
    QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QEvent

from gui.components.numpad_modal import NumpadDialog
from gui.components.time_numpad_modal import TimeNumpadDialog
from gui.components.floating_confirm import FloatingConfirmDialog
from gui.components.ui_components import ClickableLineEdit
from core.state_manager import TreatmentPhase
from utilities.platform_runtime import safe_float

import logging
logger = logging.getLogger(__name__)


HEPARIN_AUTO_STOP_HOURS_TAG = "heparineAutoStopHours"
HEPARIN_AUTO_STOP_MINUTES_TAG = "heparineAutoStopMinutes"
HEPARIN_BOLUS_EPSILON_ML = 0.01


class PushbuttonEvent(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(Qt.NoFocus)

    def event(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            self.setDown(True)
            self.pressed.emit()
            return True
        if event.type() in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            self.setDown(False)
            self.released.emit()
            return True
        return super().event(event)


class HeparinConfigScreen(QWidget):
    valueChanged = Signal(str, float)
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.heparin_pause_latched = False
        self._selected_flujo_index = 1
        self._selected_heparin_flow_index = 1
        self._selected_syringe_index = 0

        
        self.setup_ui()


    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)

        # ==================== ESTILOS ====================
        button_style = """
            QPushButton { 
                background: #06298a; 
                color: #ffffff; 
                border-radius: 20px; 
                font-weight: bold; 
                font-size: 18px;
            }
            QPushButton:pressed { background: #1e40af; }
        """

        label_style = "font-size: 26px; color: #334155; font-weight: 600;"
        input_style = """
            ClickableLineEdit {
                font-family: Consolas, "Courier New", monospace;
                font-size: 24px;
                color: #000000;
                background: #e2e8f0;
                border: 2px solid #64748b;
                border-radius: 8px;
                padding: 5px;
                min-width: 120px;
            }
            ClickableLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
            }
        """

        combo_style = """
            QComboBox {
                font-size: 24px;
                min-width: 180px;
                color: #0f172a;
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            /* Estilo para la lista que se despliega */
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #cbd5e1;
                selection-color: #0f172a;
                border: 1px solid #cbd5e1;
            }
            """

        # ===================== CARDS =====================

        # 1. Bolo
        bolus_card = QFrame()
        bolus_card.setObjectName("card")
        bolus_layout = QVBoxLayout(bolus_card)
        bolus_layout.setContentsMargins(20, 20, 20, 20)
        bolus_layout.setSpacing(18)

        title = QLabel("PARÁMETROS DE BOLO")
        title.setObjectName("card_title")
        bolus_layout.addWidget(title)

        # Volumen bolo
        h = QHBoxLayout()
        bolus_label = QLabel("Vol. Bolo Heparina (ml):")
        bolus_label.setStyleSheet(label_style)        
        h.addWidget(bolus_label)
        self.input_bolus = ClickableLineEdit("0.0")
        self.input_bolus.setFixedSize(130, 52)
        self.input_bolus.setAlignment(Qt.AlignCenter)
        self.input_bolus.setStyleSheet(input_style)
        self.input_bolus.setReadOnly(True)
        self.input_bolus.clicked.connect(
            lambda: self.open_numpad("heparineBolusQuantity", self.input_bolus, "Bolo (ml)")
        )
        h.addWidget(self.input_bolus)        

        btn_apply_bolus = QPushButton("APLICAR\n BOLO")
        btn_apply_bolus.setFixedHeight(60)
        btn_apply_bolus.setStyleSheet(button_style)
        btn_apply_bolus.clicked.connect(self.apply_bolus)
        h.addWidget(btn_apply_bolus)
        bolus_layout.addLayout(h)

#======================no hay flujo de bolo de heparina, por ahora se comenta el combo de flujo========================
        # Flujo bolo
        # h = QHBoxLayout()
        # flujo_label = QLabel("Flujo Bolo Heparina (ml/h):")
        # flujo_label.setStyleSheet(label_style)
        # h.addWidget(flujo_label)
        # self.flow_combo = QComboBox()
        # self.flow_combo.addItems(["1.0", "2.0", "3.0", "4.0"])
        # self.flow_combo.setStyleSheet(combo_style)
        # self.flow_combo.currentIndexChanged.connect(self._on_bolus_flow_changed)
        # h.addWidget(self.flow_combo)
        # bolus_layout.addLayout(h)
        bolus_layout.addStretch(1)  # para centrar verticalmente los campos

        layout.addWidget(bolus_card, 0, 0)

        # 2. Controles de bomba
        ctrls_card = QFrame()
        ctrls_card.setObjectName("card")
        ctrls_layout = QVBoxLayout(ctrls_card)
        ctrls_layout.setContentsMargins(20, 20, 20, 20)
        ctrls_layout.setSpacing(18)

        title = QLabel("CONTROLES BOMBA HEPARINA")
        title.setObjectName("card_title")
        ctrls_layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        for text, tag, is_toggle in [
            ("HOME", "heparinePumpHomePosition", False),
            ("REV", "heparinePumpREVButton", False),
            ("FWD", "heparinePumpFWDButton", False),
        ]:
            btn = PushbuttonEvent(text, self)
            btn.setFixedSize(150, 75)
            btn.setStyleSheet(button_style)
            if is_toggle:
                btn.pressed.connect(lambda t=tag: self.on_user_boolean_command(t, True))
            else:
                btn.pressed.connect(lambda t=tag: self.on_user_boolean_command(t, True))
                btn.released.connect(lambda t=tag: self.on_user_boolean_command(t, False))
            buttons_layout.addWidget(btn)

        self.btn_pause_hep = PushbuttonEvent("PAUSE", self)
        self.btn_pause_hep.setFixedSize(150, 75)
        self.btn_pause_hep.setStyleSheet(button_style)
        self.btn_pause_hep.pressed.connect(self._toggle_heparin_pause_resume)
        buttons_layout.addWidget(self.btn_pause_hep)

        ctrls_layout.addLayout(buttons_layout)
        ctrls_layout.addStretch(1)   # para centrar verticalmente los botones

        layout.addWidget(ctrls_card, 1, 0)

        # 3. Parámetros de Heparina (Card grande)
        # ===================== CARD GRANDE: PARÁMETROS DE HEPARINA =====================
        heparin_card = QFrame()
        heparin_card.setObjectName("card")
        heparin_layout = QVBoxLayout(heparin_card)
        heparin_layout.setContentsMargins(20, 20, 20, 20)
        heparin_layout.setSpacing(20)

        title = QLabel("PARÁMETROS DE HEPARINA")
        title.setObjectName("card_title")
        heparin_layout.addWidget(title)

        # Campos
        fields = [
            ("Vol. Dosis Heparina (ml):", "heparineTherapyDosage", "input_heparin"),
            ("Flujo Heparina (ml/h):", None, "heparin_flow_combo"), 
            ("Tamaño de Jeringa:", None, "syringe_combo"),
            ("Vol. Heparina en Jeringa (ml):", "heparineSyringeVolume", "input_vol_hep"),
            ("Tiempo Heparina (hh:mm):", None, "input_heparin_auto_stop"),
        ]

        for label_text, tag, widget_name in fields:
            h = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumHeight(50)   # consistencia
            h.addWidget(lbl)



            if "input_" in widget_name:
                w = ClickableLineEdit("0.0" if "auto_stop" not in widget_name else "00:00")
                w.setFixedSize(130, 52)
                w.setAlignment(Qt.AlignCenter)
                w.setStyleSheet(input_style)
                w.setReadOnly(True)
                
                if "auto_stop" in widget_name:
                    w.clicked.connect(
                        lambda wd=w: self.open_time_numpad(
                            wd, HEPARIN_AUTO_STOP_HOURS_TAG, 
                            HEPARIN_AUTO_STOP_MINUTES_TAG, "Paro automático heparina"
                        )
                    )
                else:
                    title_map = {
                        "input_heparin": "Dosis Heparina",
                        "input_vol_hep": "Vol. Heparina en Jeringa"
                    }
                    w.clicked.connect(
                        lambda t=tag, wd=w, tit=title_map.get(widget_name, ""): 
                        self.open_numpad(t, wd, tit)
                    )
                setattr(self, widget_name, w)

            elif widget_name == "heparin_flow_combo":
                w = QComboBox()
                w.addItems(["1.0", "2.0", "3.0", "4.0"])
                w.setStyleSheet(combo_style)
                w.currentIndexChanged.connect(self._on_flow_hep_changed)
                setattr(self, widget_name, w)

            elif widget_name == "syringe_combo":
                w = QComboBox()
                w.addItems(["10 ml", "20 ml", "30 ml", "50 ml"])
                w.setStyleSheet(combo_style)
                w.currentIndexChanged.connect(self._on_syringe_changed)
                setattr(self, widget_name, w)

            h.addWidget(w)
            heparin_layout.addLayout(h)

        # ← ESTO ES LO QUE ARREGLA QUE TODO SUBA ARRIBA
        heparin_layout.addStretch(1)

        layout.addWidget(heparin_card, 0, 1, 2, 1)

        # Distribución del grid principal
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)

#================================FALTA DEFINIR SI HABRÁ FLUJO DE HEPARINA O NO, POR AHORA SE COMENTA EL MÉTODO========================================
    # def _on_bolus_flow_changed(self, index):
    #     self._selected_flujo_index = index

    #     if hasattr(self, "combo_flujo") and self.combo_flujo is not None:
    #         flujo_value = float(self.combo_flujo.currentText())
    #         self.current_values["dialyHeparineBolusFlow"] = flujo_value
    #         if self.parent_window and hasattr(self.parent_window, "current_values"):
    #             self.parent_window.current_values["dialyHeparineBolusFlow"] = flujo_value
    #         self.on_user_input_setpoint("dialyHeparineBolusFlow", flujo_value)



    def _on_flow_hep_changed(self, index):  
        self._selected_heparin_flow_index = index
        if hasattr(self, "heparin_flow_combo") and self.heparin_flow_combo is not None:
            flujo_value = float(self.heparin_flow_combo.currentText())
            self.current_values["heparineTherapyFlow"] = flujo_value
            if self.parent_window and hasattr(self.parent_window, "current_values"):
                self.parent_window.current_values["heparineTherapyFlow"] = flujo_value
            self.on_user_input_setpoint("heparineTherapyFlow", flujo_value)


    def _on_syringe_changed(self, index):
        self._selected_syringe_index = index
        if hasattr(self, "syringe_combo") and self.syringe_combo is not None:
            syringe_text = self.syringe_combo.currentText() # Ejemplo: "10 ml"
            
            try:
                # Extraemos solo el número (limpiamos el " ml")
                # split()[0] toma "10" de "10 ml", "20" de "20 ml" etc
                syringe_value = float(syringe_text.split()[0])
            except (ValueError, IndexError):
                syringe_value = 0.0
                logger.error(f"Error convirtiendo tamaño de jeringa: {syringe_text}")

            self.current_values["heparineSyringeSize"] = syringe_value
            
            if self.parent_window and hasattr(self.parent_window, "current_values"):
                self.parent_window.current_values["heparineSyringeSize"] = syringe_value
            
            # enviamos un float, no un string
            self.on_user_input_setpoint("heparineSyringeSize", syringe_value)


    # def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
    #     dialog = NumpadDialog(self, initial_value="", title=title)
    #     if dialog.exec():
    #         new_value = dialog.get_value()
    #         if new_value is not None:
    #             float_val = float(new_value)
    #             input_widget.setText(str(new_value))
    #             self.current_values[tag] = float_val
    #             if self.parent_window and hasattr(self.parent_window, "current_values"):
    #                 self.parent_window.current_values[tag] = float_val
    #             self.on_user_input_setpoint(tag, float_val)
    #             if hasattr(input_widget, 'clearFocus'):
    #                 input_widget.clearFocus()
    #             self.setFocus()


    def open_numpad(self, tag: str, input_widget: ClickableLineEdit, title: str):
        dialog = NumpadDialog(self, initial_value="", title=title)
        if dialog.exec():
            new_value = dialog.get_value()
            if new_value is not None:
                float_val = float(new_value)
                
                # --- LÓGICA ESPECIAL PARA EL VOLUMEN DE JERINGA ---
                if tag == "heparineSyringeVolume":
                    if not self._validate_syringe_fill_volume(float_val):
                        return
                    syringe_max_vol = self._syringe_max_volume_ml()
                    self.on_user_input_setpoint("heparineSyringeSize", syringe_max_vol)
                    logger.info("Tamaño de jeringa seleccionado: %.2f ml", syringe_max_vol)

                # Actualizar UI y Diccionarios
                input_widget.setText(f"{float_val:.1f}")
                self.current_values[tag] = float_val
                
                if self.parent_window and hasattr(self.parent_window, "current_values"):
                    self.parent_window.current_values[tag] = float_val
                
                # Escribir al puerto (enviar setpoint)
                self.on_user_input_setpoint(tag, float_val)
                print(f"Setpoint enviado: {tag} = {float_val}")

                # --- EJECUTAR BOLO SI ES EL TAG DE JERINGA ---
                if tag == "heparineSyringeVolume":
                    self._adjust_syringe_volume()
                    logger.info("Ajuste de volumen de jeringa enviado: %.2f ml", float_val)

                if hasattr(input_widget, 'clearFocus'):
                    input_widget.clearFocus()
                self.setFocus()


    def open_time_numpad(self, input_widget: ClickableLineEdit,
                         tag_hours: str = None, tag_minutes: str = None,
                         title: str = "Config. Tiempo"):
        dialog = TimeNumpadDialog(self, initial_hh_mm="", title=title)

        if dialog.exec():
            hours, minutes = dialog.get_hours_minutes()
            if hours is not None and minutes is not None:
                if (
                    tag_hours == HEPARIN_AUTO_STOP_HOURS_TAG
                    and tag_minutes == HEPARIN_AUTO_STOP_MINUTES_TAG
                ):
                    hours, minutes = self._coerce_heparin_auto_stop_time(hours, minutes)

                input_widget.setText(f"{hours:02d}:{minutes:02d}")
                input_widget.clearFocus()  
                if tag_hours:
                    self.current_values[tag_hours] = float(hours)
                    if self.parent_window and hasattr(self.parent_window, "current_values"):
                        self.parent_window.current_values[tag_hours] = float(hours)
                if tag_minutes:
                    self.current_values[tag_minutes] = float(minutes)
                    if self.parent_window and hasattr(self.parent_window, "current_values"):
                        self.parent_window.current_values[tag_minutes] = float(minutes)
                if tag_hours and tag_minutes:
                    self.on_user_input_setpoint(tag_hours, float(hours))
                    self.on_user_input_setpoint(tag_minutes, float(minutes))

    def _coerce_heparin_auto_stop_time(self, hours: int, minutes: int) -> tuple[int, int]:
        requested_minutes = max(0, (int(hours) * 60) + int(minutes))

        therapy_hours = int(self.current_values.get("heparineTherapyHours", 0) or 0)
        therapy_minutes = int(self.current_values.get("heparineTherapyMinutes", 0) or 0)
        therapy_total_minutes = (therapy_hours * 60) + therapy_minutes
        max_allowed_minutes = max(0, therapy_total_minutes - 30)

        clamped_minutes = min(requested_minutes, max_allowed_minutes)
        if requested_minutes != clamped_minutes:
            max_h = max_allowed_minutes // 60
            max_m = max_allowed_minutes % 60
            msg = (
                f"Tiempo de heparina limitado a {max_h:02d}:{max_m:02d} "
                "(terapia menos 30 minutos)."
            )
            logger.warning(msg)
            if self.parent_window and hasattr(self.parent_window, "show_warning_message"):
                self.parent_window.show_warning_message(msg, 4000)

        return clamped_minutes // 60, clamped_minutes % 60

    def _toggle_heparin_pause_resume(self):
        """Alterna PAUSE/CONTINUAR para la bomba de heparina con comando latch."""
        self.heparin_pause_latched = not self.heparin_pause_latched
        self.on_user_boolean_command("heparineOperPauseResume", self.heparin_pause_latched)

        if hasattr(self, "btn_pause_hep") and self.btn_pause_hep is not None:
            self.btn_pause_hep.setText("CONT.." if self.heparin_pause_latched else "PAUSE")

        logger.info(
            f"Heparina pause/resume latch -> {self.heparin_pause_latched}"
        )

    
    def _update_input_display(self, widget: ClickableLineEdit, tag: str, precision: int = 1):
        if widget.hasFocus():
            return
        value = self.current_values.get(tag, 0.0)
        widget.setText(f"{value:.{precision}f}")

    def update_values(self, new_values: dict):
        self.current_values = new_values
        self._update_input_display(self.input_heparin, "heparineTherapyDosage")
        self._update_input_display(self.input_bolus, "heparineBolusQuantity")
        auto_h = int(self.current_values.get(HEPARIN_AUTO_STOP_HOURS_TAG, 0) or 0)
        auto_m = int(self.current_values.get(HEPARIN_AUTO_STOP_MINUTES_TAG, 0) or 0)
        self.input_heparin_auto_stop.setText(f"{auto_h:02d}:{auto_m:02d}")

        variables_to_update = {
            "heparineSyringeSize": self.syringe_combo,
            "heparineSyringeVolume": self.input_vol_hep
        }

        for tag, widget in variables_to_update.items():
            if tag in new_values:
                value = new_values[tag]
                if isinstance(widget, QComboBox):
                    # Para combobox, buscar el índice que coincide con el valor
                    index = widget.findText(f"{value:.1f}")
                    if index != -1:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, ClickableLineEdit):
                    widget.setText(f"{value:.1f}")

    def _syringe_max_volume_ml(self) -> float:
        try:
            return float(self.syringe_combo.currentText().split()[0])
        except (AttributeError, IndexError, ValueError):
            return safe_float(self.current_values.get("heparineSyringeSize"), 0.0)

    def _validate_syringe_fill_volume(self, fill_volume: float) -> bool:
        if fill_volume < 0:
            logger.warning("Volumen de jeringa bloqueado: valor negativo (volumen=%.2f ml)", fill_volume)
            self._show_bolus_message("El volumen en jeringa no puede ser negativo.")
            return False

        max_volume = self._syringe_max_volume_ml()
        if max_volume > 0 and fill_volume > max_volume + HEPARIN_BOLUS_EPSILON_ML:
            logger.warning(
                "Volumen de jeringa bloqueado: excede capacidad (volumen=%.2f ml, tamaño=%.2f ml)",
                fill_volume,
                max_volume,
            )
            self._show_bolus_message(
                "El volumen de heparina no puede ser mayor que el tamaño de la jeringa.\n"
                f"Volumen capturado: {fill_volume:.2f} ml\n"
                f"Tamaño de jeringa: {max_volume:.0f} ml"
            )
            return False

        return True

    def _heparin_remaining_ml(self) -> tuple[float, float, float]:
        syringe_volume = safe_float(self.current_values.get("heparineSyringeVolume"), 0.0)
        current_dosage = safe_float(self.current_values.get("heparineCurrentDosage"), 0.0)
        return syringe_volume - current_dosage, syringe_volume, current_dosage

    def _show_bolus_message(self, message: str):
        parent = self.parent_window if self.parent_window is not None else self
        dialog = FloatingConfirmDialog(parent)
        dialog.show_confirm(message, accept_text="Aceptar", cancel_text="Cerrar")

    def _can_apply_bolus(self) -> bool:
        bolus_quantity = safe_float(self.current_values.get("heparineBolusQuantity"), 0.0)
        remaining, syringe_volume, current_dosage = self._heparin_remaining_ml()

        if bolus_quantity <= 0:
            logger.info("Bolo bloqueado: volumen inválido (bolo=%.2f ml)", bolus_quantity)
            self._show_bolus_message("El volumen de bolo debe ser mayor que 0 ml.")
            return False

        if remaining <= HEPARIN_BOLUS_EPSILON_ML:
            logger.info(
                "Bolo bloqueado: heparina agotada (jeringa=%.2f ml, dosificado=%.2f ml, restante=%.2f ml)",
                syringe_volume,
                current_dosage,
                remaining,
            )
            self._show_bolus_message(
                "La heparina se ha agotado.\n"
                f"Volumen en jeringa: {syringe_volume:.2f} ml\n"
                f"Dosificado: {current_dosage:.2f} ml\n"
                "Restante: 0.00 ml"
            )
            return False

        if bolus_quantity > remaining + HEPARIN_BOLUS_EPSILON_ML:
            logger.info(
                "Bolo bloqueado: volumen insuficiente (bolo=%.2f ml, restante=%.2f ml, jeringa=%.2f ml)",
                bolus_quantity,
                remaining,
                syringe_volume,
            )
            self._show_bolus_message(
                "No hay heparina suficiente para este bolo.\n"
                f"Bolo solicitado: {bolus_quantity:.2f} ml\n"
                f"Restante en jeringa: {remaining:.2f} ml\n"
                f"Volumen en jeringa: {syringe_volume:.2f} ml"
            )
            return False

        return True

    def apply_bolus(self):
        if not self._can_apply_bolus():
            return
        self.on_user_boolean_command("heparinApplyBolusDose", True)

    def _adjust_syringe_volume(self):
        # Firmware: el mismo bit avanza el driver al volumen de jeringa.
        # No es un bolo clínico; no validar heparineBolusQuantity.
        self.on_user_boolean_command("heparinApplyBolusDose", True)        

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)

    def update_state(self, phase: TreatmentPhase):
        enabled = phase not in (TreatmentPhase.CLEANING, TreatmentPhase.ERROR)
        self.input_heparin.setEnabled(enabled)
        self.input_bolus.setEnabled(enabled)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()


        
        # Fila 0
           # Abajo Izquierda (debajo de bolo)
        
        # Aquí puedes poner un placeholder para tus futuros controles
        # future_frame = QFrame()
        # # future_frame.setStyleSheet(...)
        # content_layout.addWidget(future_frame, 1, 1) # Abajo Derecha (debajo de params)

   
