from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
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
        self._setup_ui()

    def _setup_ui(self):
        baseline = ThemeManager.get_therapy_config_baseline() or {}
        colors = baseline.get("colors", {})

        self.style_primary_btn = """
            QPushButton {
                background: %s;
                color: #ffffff;
                font-weight: bold;
                font-size: 22px;
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
                font-size: 20px;
                border-radius: 12px;
                border: 2px solid #1e293b;
                min-height: 52px;
                padding: 6px 12px;
            }
            QPushButton:pressed {
                background: #334155;
            }
        """

        self.style_danger_btn = """
            QPushButton {
                background: #dc2626;
                color: #ffffff;
                font-weight: bold;
                font-size: 20px;
                border-radius: 12px;
                border: 2px solid #7f1d1d;
                min-height: 52px;
                padding: 6px 12px;
            }
            QPushButton:pressed {
                background: #991b1b;
            }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        title = QLabel("Perfil de Conductividad")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #0f172a;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        self.lbl_therapy_time = QLabel("Tiempo de terapia: 00:00 (0 min)")
        self.lbl_therapy_time.setStyleSheet("font-size: 24px; font-weight: 600; color: #1e3a8a;")
        self.lbl_therapy_time.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_therapy_time)

        content = QFrame()
        content.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 14px; }"
        )
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 18, 20, 18)
        content_layout.setSpacing(14)

        profile_header = QLabel("Selecciona el tipo de perfil")
        profile_header.setStyleSheet("font-size: 24px; color: #0f172a; font-weight: bold;")
        content_layout.addWidget(profile_header)

        self.radio_group = QButtonGroup(self)
        self.radio_none = QRadioButton("Sin perfil (conductividad constante)")
        self.radio_linear = QRadioButton("Lineal (perfil 1)")
        self.radio_step = QRadioButton("Escalón (perfil 2)")
        self.radio_custom = QRadioButton("Personalizado / Por definir (perfil 3)")

        for rb in [self.radio_none, self.radio_linear, self.radio_step, self.radio_custom]:
            rb.setStyleSheet("font-size: 22px; color: #334155;")
            self.radio_group.addButton(rb)
            content_layout.addWidget(rb)

        self.radio_none.setChecked(True)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(12)

        self.start_spin = self._make_cond_spin(14.0)
        self.end_spin = self._make_cond_spin(13.5)
        self.step_high_spin = self._make_cond_spin(14.2)
        self.step_low_spin = self._make_cond_spin(13.6)

        self.step_change_spin = QSpinBox()
        self.step_change_spin.setRange(0, 100)
        self.step_change_spin.setValue(50)
        self.step_change_spin.setSuffix(" %")
        self.step_change_spin.setStyleSheet(
            "font-size: 22px; color: #0f172a; background: #f1f5f9; border: 1px solid #94a3b8; border-radius: 8px;"
        )

        form_layout.addWidget(self._lbl("Conductividad inicial (mS/cm):"), 0, 0)
        form_layout.addWidget(self.start_spin, 0, 1)
        form_layout.addWidget(self._lbl("Conductividad final (mS/cm):"), 1, 0)
        form_layout.addWidget(self.end_spin, 1, 1)

        form_layout.addWidget(self._lbl("Escalón alto (mS/cm):"), 2, 0)
        form_layout.addWidget(self.step_high_spin, 2, 1)
        form_layout.addWidget(self._lbl("Escalón bajo (mS/cm):"), 3, 0)
        form_layout.addWidget(self.step_low_spin, 3, 1)
        form_layout.addWidget(self._lbl("Cambio de escalón (% tiempo):"), 4, 0)
        form_layout.addWidget(self.step_change_spin, 4, 1)

        content_layout.addLayout(form_layout)

        self.custom_placeholder = QLabel(
            "TODO: Perfil personalizado pendiente.\n"
            "Espacio reservado para futura configuración y gráfica de receta."
        )
        self.custom_placeholder.setStyleSheet(
            "background: #eff6ff; color: #1e3a8a; border: 1px dashed #93c5fd; border-radius: 10px;"
            "font-size: 20px; padding: 12px;"
        )
        self.custom_placeholder.setWordWrap(True)
        content_layout.addWidget(self.custom_placeholder)

        self.graph_placeholder = QLabel("Espacio reservado para gráfica del perfil")
        self.graph_placeholder.setAlignment(Qt.AlignCenter)
        self.graph_placeholder.setMinimumHeight(130)
        self.graph_placeholder.setStyleSheet(
            "background: #f8fafc; color: #64748b; border: 1px dashed #cbd5e1; border-radius: 10px; font-size: 18px;"
        )
        content_layout.addWidget(self.graph_placeholder)

        notes_label = self._lbl("Notas")
        content_layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Comentarios opcionales para la receta...")
        self.notes_edit.setMaximumHeight(90)
        self.notes_edit.setStyleSheet(
            "font-size: 19px; color: #0f172a; background: #f8fafc; border: 1px solid #94a3b8; border-radius: 10px;"
        )
        content_layout.addWidget(self.notes_edit)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.btn_disable = QPushButton("Cancelar / Desactivar perfil")
        self.btn_disable.setStyleSheet(self.style_danger_btn)
        self.btn_disable.clicked.connect(self._on_disable_profile)

        self.btn_back = QPushButton("Volver")
        self.btn_back.setStyleSheet(self.style_secondary_btn)
        self.btn_back.clicked.connect(self._on_back)

        self.btn_save = QPushButton("Aceptar / Guardar")
        self.btn_save.setStyleSheet(self.style_primary_btn)
        self.btn_save.clicked.connect(self._on_save_profile)

        buttons.addWidget(self.btn_disable)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_back)
        buttons.addWidget(self.btn_save)

        content_layout.addLayout(buttons)
        main_layout.addWidget(content, 1)

        self.radio_group.buttonToggled.connect(self._update_form_visibility)
        self._update_form_visibility()
        self.refresh_from_parent()

    def _lbl(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 22px; color: #334155; font-weight: 600;")
        return label

    def _make_cond_spin(self, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(2)
        spin.setRange(12.0, 16.0)
        spin.setSingleStep(0.1)
        spin.setValue(value)
        spin.setStyleSheet(
            "font-size: 22px; color: #0f172a; background: #f1f5f9; border: 1px solid #94a3b8; border-radius: 8px;"
        )
        return spin

    def _selected_type(self) -> ProfileType:
        if self.radio_linear.isChecked():
            return ProfileType.LINEAR
        if self.radio_step.isChecked():
            return ProfileType.STEP
        if self.radio_custom.isChecked():
            return ProfileType.CUSTOM
        return ProfileType.NONE

    def _update_form_visibility(self):
        selected = self._selected_type()

        is_linear = selected == ProfileType.LINEAR
        is_step = selected == ProfileType.STEP
        is_custom = selected == ProfileType.CUSTOM

        self.end_spin.setEnabled(is_linear)

        self.step_high_spin.setEnabled(is_step)
        self.step_low_spin.setEnabled(is_step)
        self.step_change_spin.setEnabled(is_step)

        self.custom_placeholder.setVisible(is_custom)

    def _on_back(self):
        if self.parent_window and hasattr(self.parent_window, "show_therapy_config_screen"):
            self.parent_window.show_therapy_config_screen()

    def _on_disable_profile(self):
        if self.parent_window and hasattr(self.parent_window, "disable_conductivity_profile"):
            self.parent_window.disable_conductivity_profile(show_message=True)
            self.profile_saved.emit()
            self._on_back()

    def _on_save_profile(self):
        profile_type = self._selected_type()
        therapy_duration_min = self._therapy_duration_min_from_values()

        profile = ConductivityProfile(
            enabled=(profile_type != ProfileType.NONE),
            profile_type=profile_type,
            therapy_duration_min=therapy_duration_min,
            start_conductivity=float(self.start_spin.value()),
            end_conductivity=float(self.end_spin.value()),
            step_high=float(self.step_high_spin.value()),
            step_low=float(self.step_low_spin.value()),
            step_change_at_percent=float(self.step_change_spin.value()),
            notes=self.notes_edit.toPlainText().strip(),
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
            return

        profile: ConductivityProfile = self.parent_window.conductivity_profile

        if not profile.enabled or profile.profile_type == ProfileType.NONE:
            self.radio_none.setChecked(True)
        elif profile.profile_type == ProfileType.LINEAR:
            self.radio_linear.setChecked(True)
        elif profile.profile_type == ProfileType.STEP:
            self.radio_step.setChecked(True)
        else:
            self.radio_custom.setChecked(True)

        self.start_spin.setValue(float(profile.start_conductivity))
        self.end_spin.setValue(float(profile.end_conductivity))
        self.step_high_spin.setValue(float(profile.step_high))
        self.step_low_spin.setValue(float(profile.step_low))
        self.step_change_spin.setValue(int(profile.step_change_at_percent))
        self.notes_edit.setPlainText(profile.notes or "")

        self._update_form_visibility()

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

        self.btn_save.setEnabled(not disabled)
        self.btn_save.setStyleSheet(self.style_primary_btn if not disabled else self.style_secondary_btn)

        for widget in [
            self.radio_none,
            self.radio_linear,
            self.radio_step,
            self.radio_custom,
            self.start_spin,
            self.end_spin,
            self.step_high_spin,
            self.step_low_spin,
            self.step_change_spin,
            self.notes_edit,
        ]:
            widget.setEnabled(not disabled)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_from_parent()
