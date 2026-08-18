from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.state_manager import TreatmentPhase
from gui.theme_manager import ThemeManager
from logic.conductivity_profile import ConductivityProfile, ProfileType


class ConductivityProfileScreen(QWidget):
    profile_saved = Signal()

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}
        self._phase = TreatmentPhase.IDLE
        self._selected_index = 0
        self._slider_values = [14.0, 14.0, 14.0, 14.0, 14.0, 14.0]
        self._setup_ui()

    def _setup_ui(self):
        baseline = ThemeManager.get_therapy_config_baseline() or {}
        colors = baseline.get("colors", {})

        self.style_primary_btn = """
            QPushButton {
                background: %s;
                color: #ffffff;
                font-weight: bold;
                font-size: 20px;
                border-radius: 12px;
                border: 3px solid %s;
                min-height: 56px;
                padding: 6px 12px;
            }
            QPushButton:pressed {
                background: #334155;
            }
        """ % (colors.get("button_enabled_bg", "#39ec21"), colors.get("button_border", "#1e293b"))

        self.style_secondary_btn = """
            QPushButton {
                background: #0f172a;
                color: #ffffff;
                font-weight: bold;
                font-size: 18px;
                border-radius: 12px;
                border: 2px solid #1e293b;
                min-height: 52px;
                padding: 6px 12px;
            }
            QPushButton:pressed {
                background: #334155;
            }
        """

        self.style_toggle_btn = """
            QPushButton {
                background: #f1f5f9;
                color: #0f172a;
                font-weight: 600;
                font-size: 18px;
                border-radius: 10px;
                border: 2px solid #94a3b8;
                min-height: 52px;
                padding: 8px 10px;
            }
            QPushButton:checked {
                background: #0f766e;
                color: #ffffff;
                border: 2px solid #134e4a;
            }
            QPushButton:pressed {
                background: #115e59;
                color: #ffffff;
            }
        """

        card_style = """
            QFrame#Card {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        self.lbl_therapy_time = QLabel("Tiempo de terapia: 00:00 (0 min)")
        self.lbl_therapy_time.setStyleSheet("font-size: 22px; font-weight: 600; color: #1e3a8a;")
        self.lbl_therapy_time.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_therapy_time)

        self.top_card = self._build_top_card(card_style)
        main_layout.addWidget(self.top_card)

        self.main_card = self._build_main_card(card_style)
        main_layout.addWidget(self.main_card)

        self._setup_modes()
        self._set_selected_slider(0)
        self._slider_values = [self._get_conductivity_setpoint()] * 6
        for idx, slider in enumerate(self.slider_widgets):
            slider.setValue(int(round(self._slider_values[idx] * 10.0)))
        self._update_selected_value_label()
        self.refresh_from_parent()

    def _build_top_card(self, card_style: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(card_style)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(18)

        self.lbl_selected_value = QLabel("14.00 mS/cm")
        self.lbl_selected_value.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #0f172a;"
        )
        self.lbl_selected_value.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.lbl_selected_value, 1)

        self.btn_accept = QPushButton("Aceptar")
        self.btn_accept.setStyleSheet(self.style_primary_btn)
        self.btn_accept.clicked.connect(self._on_save_profile)
        card_layout.addWidget(self.btn_accept)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setStyleSheet(self.style_secondary_btn)
        self.btn_cancel.clicked.connect(self._on_cancel_profile)
        card_layout.addWidget(self.btn_cancel)

        self.btn_save = self.btn_accept
        self.btn_back = self.btn_cancel
        return card

    def _build_main_card(self, card_style: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(card_style)
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(18)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(18)
        left_panel.setContentsMargins(0, 0, 0, 0)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedWidth(90)
        self.btn_plus.setMinimumHeight(90)
        self.btn_plus.setStyleSheet(
            "QPushButton { background: #0f172a; color: #ffffff; font-size: 42px; font-weight: bold; border-radius: 14px; }"
            "QPushButton:pressed { background: #334155; }"
        )
        self.btn_plus.clicked.connect(self._on_plus_clicked)

        self.btn_minus = QPushButton("-")
        self.btn_minus.setFixedWidth(90)
        self.btn_minus.setMinimumHeight(90)
        self.btn_minus.setStyleSheet(
            "QPushButton { background: #0f172a; color: #ffffff; font-size: 42px; font-weight: bold; border-radius: 14px; }"
            "QPushButton:pressed { background: #334155; }"
        )
        self.btn_minus.clicked.connect(self._on_minus_clicked)

        self.btn_adjust = QPushButton("Ajuste")
        self.btn_adjust.setFixedWidth(90)
        self.btn_adjust.setMinimumHeight(90)
        self.btn_adjust.setStyleSheet(
            "QPushButton { background: #0f766e; color: #ffffff; font-size: 18px; font-weight: bold; border-radius: 12px; }"
            "QPushButton:pressed { background: #115e59; }"
        )
        self.btn_adjust.clicked.connect(self._on_adjust_clicked)

        left_panel.addStretch(1)
        left_panel.addWidget(self.btn_plus)
        left_panel.addWidget(self.btn_minus)
        left_panel.addSpacing(10)
        left_panel.addWidget(self.btn_adjust)
        left_panel.addStretch(1)

        main_layout.addLayout(left_panel)

        self.slider_frame = QFrame()
        self.slider_frame.setStyleSheet("background: transparent;")
        self.slider_layout = QHBoxLayout(self.slider_frame)
        self.slider_layout.setSpacing(8)
        self.slider_layout.setContentsMargins(8, 8, 8, 8)

        self.slider_widgets = []
        self.slider_labels = []
        for index in range(6):
            column = QVBoxLayout()
            column.setSpacing(10)
            slider = QSlider(Qt.Vertical)
            slider.setRange(120, 160)
            slider.setSingleStep(1)
            slider.setPageStep(1)
            slider.setTickPosition(QSlider.NoTicks)
            slider.setMinimumHeight(220)
            slider.setMinimumWidth(78)
            slider.setStyleSheet(self._slider_style(False))
            slider.valueChanged.connect(lambda value, idx=index: self._on_slider_value_changed(idx, value))
            slider.sliderPressed.connect(lambda idx=index: self._set_selected_slider(idx))
            slider.mouseReleaseEvent = lambda event, idx=index: self._on_slider_release(idx, event)

            label = QLabel(f"{index + 1}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
            label.setMinimumHeight(18)

            column.addWidget(slider, 1, Qt.AlignHCenter)       
            column.addWidget(label)
            self.slider_layout.addLayout(column)
            self.slider_widgets.append(slider)
            self.slider_labels.append(label)

        main_layout.addWidget(self.slider_frame, 1)

        self.type_button_group = QButtonGroup(self)
        self.type_button_group.setExclusive(True)

        mode_panel = QVBoxLayout()
        mode_panel.setSpacing(12)
        mode_panel.setContentsMargins(0, 0, 0, 0)

        self.btn_type_none = QPushButton("Sin\nperfil")
        self.btn_type_linear = QPushButton("Lineal")
        self.btn_type_exp = QPushButton("Exp")
        self.btn_type_step = QPushButton("Escalón")

        for btn in [self.btn_type_none, self.btn_type_linear, self.btn_type_exp, self.btn_type_step]:
            btn.setCheckable(True)
            btn.setStyleSheet(self.style_toggle_btn)
            self.type_button_group.addButton(btn)
            mode_panel.addWidget(btn)

        self.btn_type_none.setChecked(True)
        main_layout.addLayout(mode_panel)

        return card

    def _slider_style(self, selected: bool) -> str:
        accent = "#14b8a6" if selected else "#2dd4bf"
        empty = "#dfe7ee"
        border = "#0f766e" if selected else "#cbd5e1"
    
        return (
            "QSlider { background: transparent; min-height: 220px; }"
            "QSlider::groove:vertical { background: transparent; width: 42px; border-radius: 7px; }"
            "QSlider::sub-page:vertical { background: %s; border-radius: 2px; }"   # ← ahora el vacío
            "QSlider::add-page:vertical { background: %s; border-radius: 2px; }"   # ← ahora el color (verde)
            "QSlider::handle:vertical { background: transparent; width: 0px; height: 0px; border: none; }"
            "QSlider { border: %s solid %s; border-radius: 14px; padding: 2px; }"
        ) % (empty, accent, "3px" if selected else "2px", border)

    def _setup_modes(self):
        self.type_button_group.buttonToggled.connect(self._on_profile_type_changed)

    def _selected_type(self) -> ProfileType:
        if self.btn_type_linear.isChecked():
            return ProfileType.LINEAR
        if self.btn_type_step.isChecked():
            return ProfileType.STEP
        if self.btn_type_exp.isChecked():
            return ProfileType.CUSTOM
        return ProfileType.NONE

    def _set_selected_slider(self, index: int):
        self._selected_index = max(0, min(5, index))
        for i, slider in enumerate(self.slider_widgets):
            slider.setStyleSheet(self._slider_style(i == self._selected_index))
        self._update_selected_value_label()

    def _on_slider_release(self, index: int, event):
        self._set_selected_slider(index)
        if event is not None:
            event.accept()

    def _on_slider_value_changed(self, index: int, value: int):
        self._slider_values[index] = value / 10.0
        self._set_selected_slider(index)
        self._update_selected_value_label()

    def _on_plus_clicked(self):
        if not self.slider_widgets:
            return
        current = self._slider_values[self._selected_index] * 10.0
        next_value = min(160.0, current + 1.0)
        self.slider_widgets[self._selected_index].setValue(int(round(next_value)))

    def _on_minus_clicked(self):
        if not self.slider_widgets:
            return
        current = self._slider_values[self._selected_index] * 10.0
        next_value = max(120.0, current - 1.0)
        self.slider_widgets[self._selected_index].setValue(int(round(next_value)))

    def _update_selected_value_label(self):
        value = self._slider_values[self._selected_index]
        self.lbl_selected_value.setText(f"{value:.2f} mS/cm")

    def _on_profile_type_changed(self):
        self._update_selected_value_label()

    def _get_conductivity_setpoint(self) -> float:
        """Obtiene el setpoint de conductividad actual (dialyCondControlSetPoint)."""
        try:
            value = self.current_values.get("dialyCondControlSetPoint")
            if value is None:
                # Fallback por si viene con otro nombre
                value = self.current_values.get("dialyCondControlSetpoint")
        
            if value is not None:
                return self._clamp_value(float(value))
        except (TypeError, ValueError):
            pass
    
        return 14.0  # valor por defecto seguro

    def _clamp_value(self, value: float) -> float:
        return max(12.0, min(16.0, float(value)))

    def _on_cancel_profile(self):
        self.refresh_from_parent()
        self._on_back()

    def _on_back(self):
        if self.parent_window and hasattr(self.parent_window, "show_therapy_config_screen"):
            self.parent_window.show_therapy_config_screen()

    def _on_save_profile(self):
        profile_type = self._selected_type()
        therapy_duration_min = self._therapy_duration_min_from_values()

        values = self._slider_values[:]
        profile = ConductivityProfile(
            enabled=(profile_type != ProfileType.NONE),
            profile_type=profile_type,
            therapy_duration_min=therapy_duration_min,
            start_conductivity=float(values[0]),
            end_conductivity=float(values[-1]),
            step_high=float(max(values[0], values[-1])),
            step_low=float(min(values[0], values[-1])),
            step_change_at_percent=50.0,
        )

        if self.parent_window and hasattr(self.parent_window, "set_conductivity_profile"):
            ok = self.parent_window.set_conductivity_profile(profile, show_message=True)
            if ok:
                self.profile_saved.emit()
                self._on_back()

    def _therapy_duration_min_from_values(self) -> int:
        hours = int(self.current_values.get("heparineTherapyHours", 0) or 0)
        minutes = int(self.current_values.get("heparineTherapyMinutes", 0) or 0)
        return max(1, (hours * 60) + minutes)

    def refresh_from_parent(self):
        self._update_therapy_time_label()

        if not self.parent_window or not hasattr(self.parent_window, "conductivity_profile"):
            setpoint = self._get_conductivity_setpoint()
            self._slider_values = [setpoint] * 6
            self.btn_type_none.setChecked(True)
            for idx, slider in enumerate(self.slider_widgets):
                slider.setValue(int(round(self._slider_values[idx] * 10.0)))
            self._set_selected_slider(self._selected_index)
            self._update_selected_value_label()
            return

        profile: ConductivityProfile = self.parent_window.conductivity_profile

        if not profile.enabled or profile.profile_type == ProfileType.NONE:
            self.btn_type_none.setChecked(True)
            setpoint = self._get_conductivity_setpoint()
            self._slider_values = [setpoint] * 6
        elif profile.profile_type == ProfileType.LINEAR:
            self.btn_type_linear.setChecked(True)
            self._slider_values = self._generate_linear_profile_from_values(
                float(profile.start_conductivity), float(profile.end_conductivity)
            )
        elif profile.profile_type == ProfileType.STEP:
            self.btn_type_step.setChecked(True)
            high = float(profile.step_high if profile.step_high else profile.start_conductivity)
            low = float(profile.step_low if profile.step_low else profile.end_conductivity)
            self._slider_values = self._generate_step_from_ends(high, low)
        else:
            self.btn_type_exp.setChecked(True)
            self._slider_values = self._generate_exp_profile_from_values(
                float(profile.start_conductivity), float(profile.end_conductivity)
            )

        for idx, slider in enumerate(self.slider_widgets):
            slider.setValue(int(round(self._slider_values[idx] * 10.0)))

        self._set_selected_slider(self._selected_index)
        self._update_selected_value_label()

    def _generate_linear_profile_from_values(self, start: float, end: float):
        values = []
        for i in range(6):
            progress = i / 5.0
            values.append(start + (end - start) * progress)
        return [self._clamp_value(v) for v in values]

    def _generate_exp_profile_from_values(self, start: float, end: float):
        return self._calculate_decay_curve(start, end)

    def _update_therapy_time_label(self):
        hours = int(self.current_values.get("heparineTherapyHours", 0) or 0)
        minutes = int(self.current_values.get("heparineTherapyMinutes", 0) or 0)
        total_min = (hours * 60) + minutes
        self.lbl_therapy_time.setText(f"Tiempo de terapia: {hours:02d}:{minutes:02d} ({total_min} min)")

    def update_values(self, new_values: dict):
        self.current_values = new_values
        self._update_therapy_time_label()

    def update_state(self, phase: TreatmentPhase):
        self._phase = phase
        disabled = phase in (TreatmentPhase.CLEANING, TreatmentPhase.ERROR)

        for widget in [
            self.btn_accept,
            self.btn_cancel,
            self.btn_plus,
            self.btn_minus,
            self.btn_adjust,
            self.btn_type_none,
            self.btn_type_linear,
            self.btn_type_exp,
            self.btn_type_step,
        ]:
            widget.setEnabled(not disabled)   

        for slider in self.slider_widgets:
            slider.setEnabled(not disabled)


    def _on_adjust_clicked(self):
        """Recalcula las barras según el tipo de perfil actual."""
        profile_type = self._selected_type()

        if profile_type == ProfileType.NONE:
            # Sin perfil → todas las barras al setpoint de conductividad
            sp = self._get_conductivity_setpoint()
            self._slider_values = [sp] * 6
        else:
            start = float(self._slider_values[0])
            end = float(self._slider_values[-1])

            if profile_type == ProfileType.LINEAR:
                self._slider_values = self._generate_linear_from_ends(start, end)
            elif profile_type == ProfileType.CUSTOM:  # Exp
                self._slider_values = self._generate_exp_from_ends(start, end)
            elif profile_type == ProfileType.STEP:
                self._slider_values = self._generate_step_from_ends(start, end)

        for idx, slider in enumerate(self.slider_widgets):
            slider.blockSignals(True)
            slider.setValue(int(round(self._slider_values[idx] * 10.0)))
            slider.blockSignals(False)

        self._set_selected_slider(self._selected_index)
        self._update_selected_value_label()


    def _generate_linear_from_ends(self, start: float, end: float):
        values = []
        for i in range(6):
            progress = i / 5.0
            values.append(start + (end - start) * progress)
        return [self._clamp_value(v) for v in values]
  
    def _generate_exp_from_ends(self, start: float, end: float):
        return self._calculate_decay_curve(start, end)

    def _generate_step_from_ends(self, start: float, end: float):
        """
        Escalón alternado:
        Alto - Bajo - Alto - Bajo - Alto - Bajo
        """
        return [
            self._clamp_value(start),  # 1 Alto
            self._clamp_value(end),    # 2 Bajo
            self._clamp_value(start),  # 3 Alto
            self._clamp_value(end),    # 4 Bajo
            self._clamp_value(start),  # 5 Alto
            self._clamp_value(end),    # 6 Bajo
        ]
    
    def _calculate_decay_curve(self, start: float, end: float):
        values = []
        k = 3.0  # Factor de curvatura (mayor número = caída más pronunciada)
        for i in range(6):
            progress = i / 5.0            
            # Fórmula real de decaimiento exponencial mapeada de 0 a 1
            normalized = (1.0 - math.exp(-k * progress)) / (1.0 - math.exp(-k))            
            values.append(start + (end - start) * normalized)
            
        return [self._clamp_value(v) for v in values]

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_from_parent()
