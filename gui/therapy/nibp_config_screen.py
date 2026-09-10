# gui/therapy/nibp_config_screen.py

"""
Pantalla clínica de configuración y lectura del baumanómetro PAR NIBP2020 UP.


"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QComboBox, QCheckBox, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
import json
import logging

from utilities.platform_runtime import get_runtime_config_path, safe_json_load

logger = logging.getLogger(__name__)

NIBP_CONFIG_FILE = get_runtime_config_path("nibp_config.json")
NIBP_DEFAULT_CONFIG = {
    "enabled": False,
    "port": "Auto",
    "baudrate": 19200,
    "patient_mode": "adult",
    "method": 2,
    "start_pressure_mmhg": 160,
    "auto_during_therapy": False,
    "interval_min": 15,
    "spo2_enabled": False,
}

METHOD_LABELS = {
    1: "1 - Deflación",
    2: "2 - IMT (inflado)",
    3: "3 - Deflación adaptativa",
}
START_PRESSURE_OPTIONS_MMHG = [80, 100, 120, 140, 160, 180, 200, 220, 240, 280]
INTERVAL_OPTIONS_MIN = [5, 10, 15, 30, 60]


class NibpConfigScreen(QWidget):
    """Pantalla de configuración clínica del NIBP2020 UP (sin manejo de puerto/enable)."""

    settings_applied = Signal(dict)
    measure_now_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._config = self._load_config()

        self.setObjectName("NibpConfigScreen")
        self.setStyleSheet("QWidget#NibpConfigScreen { background-color: #FCFCFC; }")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setup_ui()
        self._apply_config_to_ui()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------
    def _load_config(self) -> dict:
        loaded = safe_json_load(NIBP_CONFIG_FILE, {})
        if not isinstance(loaded, dict):
            loaded = {}
        return {**NIBP_DEFAULT_CONFIG, **loaded}

    def _save_config(self):
        NIBP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with NIBP_CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.info(f"[NIBP] Configuración clínica guardada en {NIBP_CONFIG_FILE}")
        except Exception as e:
            logger.error(f"[NIBP] Error guardando configuración clínica: {e}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def setup_ui(self):
        combo_style = """
            QComboBox {
                font-size: 22px;
                min-width: 200px;
                color: #0f172a;
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #cbd5e1;
                selection-color: #0f172a;
                border: 1px solid #cbd5e1;
            }
        """
        chk_style = """
            QCheckBox { color: #0f172a; font-size: 20px; background: transparent; }
            QCheckBox::indicator { width: 28px; height: 28px; border: 2px solid #334155; border-radius: 4px; }
            QCheckBox::indicator:checked { background-color: #0f172a; }
        """
        btn_style = """
            QPushButton {
                background-color: #06298a;
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 12px 28px;
                border-radius: 10px;
                min-height: 70px;
            }
            QPushButton:hover { background-color: #1e293b; }
            QPushButton:pressed { background-color: #334155; }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(7, 7, 7, 7)
        main_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        title = QLabel("Baumanómetro PAR NIBP2020 UP")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_close.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(self.btn_close)
        main_layout.addLayout(header_layout)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setContentsMargins(7, 7, 7, 7)

        # ─── CARD 1: LECTURA ACTUAL (ocupa 2 columnas) ───────────────────────
        reading_card = QFrame()
        reading_card.setObjectName("card")
        reading_layout = QVBoxLayout(reading_card)
        reading_layout.setContentsMargins(10, 10, 10, 10)
        reading_layout.setSpacing(7)

        reading_title = QLabel("Lectura actual")
        reading_title.setObjectName("card_title")
        reading_layout.addWidget(reading_title)

        values_row = QHBoxLayout()
        values_row.setSpacing(20)
        self.lbl_sys = self._make_value_label("SYS", "—")
        self.lbl_dia = self._make_value_label("DIA", "—")
        self.lbl_map = self._make_value_label("MAP", "—")
        self.lbl_hr = self._make_value_label("FC", "—")
        for lbl in (self.lbl_sys, self.lbl_dia, self.lbl_map, self.lbl_hr):
            values_row.addWidget(lbl)
        values_row.addStretch()
        reading_layout.addLayout(values_row)

        self.lbl_cuff = QLabel("Manguito: — mmHg")
        self.lbl_cuff.setStyleSheet("font-size: 22px; color: #0f172a;")
        reading_layout.addWidget(self.lbl_cuff)

        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setStyleSheet("font-size: 20px; color: #475569;")
        reading_layout.addWidget(self.lbl_status)

        hint_label = QLabel("Colocar el manguito en el brazo contrario a la fístula.")
        hint_label.setStyleSheet("font-size: 16px; color: #64748b;")
        reading_layout.addWidget(hint_label)

        grid.addWidget(reading_card, 0, 0, 1, 2)

        # ─── CARD 2: PACIENTE ─────────────────────────────────────────────
        patient_card = QFrame()
        patient_card.setObjectName("card")
        patient_layout = QVBoxLayout(patient_card)
        patient_layout.setContentsMargins(10, 10, 10, 10)
        patient_layout.setSpacing(7)

        patient_title = QLabel("Paciente")
        patient_title.setObjectName("card_title")
        patient_layout.addWidget(patient_title)

        self.cmb_patient_mode = QComboBox()
        self.cmb_patient_mode.setStyleSheet(combo_style)
        self.cmb_patient_mode.addItem("Adulto", "adult")
        self.cmb_patient_mode.addItem("Neonatal", "neonatal")
        patient_layout.addWidget(self.cmb_patient_mode)

        grid.addWidget(patient_card, 1, 0, 1, 1)

        # ─── CARD 3: MÉTODO ───────────────────────────────────────────────
        method_card = QFrame()
        method_card.setObjectName("card")
        method_layout = QVBoxLayout(method_card)
        method_layout.setContentsMargins(10, 10, 10, 10)
        method_layout.setSpacing(7)

        method_title = QLabel("Método")
        method_title.setObjectName("card_title")
        method_layout.addWidget(method_title)

        self.cmb_method = QComboBox()
        self.cmb_method.setStyleSheet(combo_style)
        for code, label in METHOD_LABELS.items():
            self.cmb_method.addItem(label, code)
        method_layout.addWidget(self.cmb_method)

        grid.addWidget(method_card, 1, 1, 1, 1)

        # ─── CARD 4: PRESIÓN DE ARRANQUE ──────────────────────────────────
        pressure_card = QFrame()
        pressure_card.setObjectName("card")
        pressure_layout = QVBoxLayout(pressure_card)
        pressure_layout.setContentsMargins(10, 10, 10, 10)
        pressure_layout.setSpacing(7)

        pressure_title = QLabel("Presión de arranque")
        pressure_title.setObjectName("card_title")
        pressure_layout.addWidget(pressure_title)

        self.cmb_start_pressure = QComboBox()
        self.cmb_start_pressure.setStyleSheet(combo_style)
        for pressure in START_PRESSURE_OPTIONS_MMHG:
            self.cmb_start_pressure.addItem(f"{pressure} mmHg", pressure)
        pressure_layout.addWidget(self.cmb_start_pressure)

        grid.addWidget(pressure_card, 2, 0, 1, 1)

        # ─── CARD 5: AUTOMÁTICA (solo persistir) ──────────────────────────
        auto_card = QFrame()
        auto_card.setObjectName("card")
        auto_layout = QVBoxLayout(auto_card)
        auto_layout.setContentsMargins(10, 10, 10, 10)
        auto_layout.setSpacing(7)

        auto_title = QLabel("Automática")
        auto_title.setObjectName("card_title")
        auto_layout.addWidget(auto_title)

        self.chk_auto = QCheckBox("Automática durante la terapia")
        self.chk_auto.setStyleSheet(chk_style)
        auto_layout.addWidget(self.chk_auto)

        interval_row = QHBoxLayout()
        interval_row.setSpacing(10)
        lbl_interval = QLabel("Intervalo:")
        lbl_interval.setStyleSheet("font-size: 22px; color: #0f172a;")
        self.cmb_interval = QComboBox()
        self.cmb_interval.setStyleSheet(combo_style)
        for minutes in INTERVAL_OPTIONS_MIN:
            self.cmb_interval.addItem(f"{minutes} min", minutes)
        interval_row.addWidget(lbl_interval)
        interval_row.addWidget(self.cmb_interval)
        interval_row.addStretch()
        auto_layout.addLayout(interval_row)

        auto_hint = QLabel("Se activará cuando la terapia esté en RUNNING (próxima entrega).")
        auto_hint.setStyleSheet("font-size: 16px; color: #64748b;")
        auto_hint.setWordWrap(True)
        auto_layout.addWidget(auto_hint)

        grid.addWidget(auto_card, 2, 1, 1, 1)

        # ─── CARD 6: ACCIONES ─────────────────────────────────────────────
        actions_card = QFrame()
        actions_card.setObjectName("card")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(10, 10, 10, 10)
        actions_layout.setSpacing(7)

        actions_title = QLabel("Acciones")
        actions_title.setObjectName("card_title")
        actions_layout.addWidget(actions_title)

        self.chk_spo2 = QCheckBox("SpO2")
        self.chk_spo2.setStyleSheet(chk_style)
        actions_layout.addWidget(self.chk_spo2)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)

        self.btn_measure_now = QPushButton("Medir ahora")
        self.btn_measure_now.setStyleSheet(btn_style)
        self.btn_measure_now.clicked.connect(self.measure_now_requested.emit)

        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setStyleSheet(btn_style)
        self.btn_apply.clicked.connect(self._on_apply_clicked)

        self.btn_reset = QPushButton("Reset módulo")
        self.btn_reset.setStyleSheet(btn_style)
        self.btn_reset.clicked.connect(self.reset_requested.emit)

        buttons_row.addWidget(self.btn_measure_now)
        buttons_row.addWidget(self.btn_apply)
        buttons_row.addWidget(self.btn_reset)
        actions_layout.addLayout(buttons_row)

        grid.addWidget(actions_card, 3, 0, 1, 2)

        main_layout.addLayout(grid)
        main_layout.addStretch()

    def _make_value_label(self, name: str, value: str) -> QLabel:
        label = QLabel(f"{name}: {value}")
        label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0f172a;")
        return label

    # ------------------------------------------------------------------
    # Config <-> UI
    # ------------------------------------------------------------------
    def _apply_config_to_ui(self):
        patient_mode = self._config.get("patient_mode", "adult")
        index = self.cmb_patient_mode.findData(patient_mode)
        self.cmb_patient_mode.setCurrentIndex(index if index >= 0 else 0)

        method = self._config.get("method", 2)
        index = self.cmb_method.findData(method)
        self.cmb_method.setCurrentIndex(index if index >= 0 else 1)

        start_pressure = self._config.get("start_pressure_mmhg", 160)
        index = self.cmb_start_pressure.findData(start_pressure)
        self.cmb_start_pressure.setCurrentIndex(index if index >= 0 else 0)

        self.chk_auto.setChecked(bool(self._config.get("auto_during_therapy", False)))

        interval = self._config.get("interval_min", 15)
        index = self.cmb_interval.findData(interval)
        self.cmb_interval.setCurrentIndex(index if index >= 0 else 0)

        self.chk_spo2.setChecked(bool(self._config.get("spo2_enabled", False)))

    def _on_apply_clicked(self):
        # NO cambia enabled/port: eso solo lo edita CommPortScreen.
        self._config["patient_mode"] = self.cmb_patient_mode.currentData()
        self._config["method"] = self.cmb_method.currentData()
        self._config["start_pressure_mmhg"] = self.cmb_start_pressure.currentData()
        self._config["auto_during_therapy"] = self.chk_auto.isChecked()
        self._config["interval_min"] = self.cmb_interval.currentData()
        self._config["spo2_enabled"] = self.chk_spo2.isChecked()

        self._save_config()
        self.settings_applied.emit(dict(self._config))

    def _on_close_clicked(self):
        if self.parent_window and hasattr(self.parent_window, "show_dialysis_screen"):
            self.parent_window.show_dialysis_screen()

    # ------------------------------------------------------------------
    # Slots públicos (conectados por el composition root a NibpParCommunication)
    # ------------------------------------------------------------------
    def update_connection(self, connected: bool, port: str):
        self.lbl_status.setText(f"Conectado ({port})" if connected else "Desconectado")

    def update_error(self, error_code: str, error_text: str):
        self.lbl_status.setText(f"Error {error_code}: {error_text}")

    def update_measurement(self, sys_mmhg: int, dia_mmhg: int, map_mmhg: int, hr_bpm: int):
        self.lbl_sys.setText(f"SYS: {sys_mmhg if sys_mmhg >= 0 else '—'}")
        self.lbl_dia.setText(f"DIA: {dia_mmhg if dia_mmhg >= 0 else '—'}")
        self.lbl_map.setText(f"MAP: {map_mmhg if map_mmhg >= 0 else '—'}")
        self.lbl_hr.setText(f"FC: {hr_bpm if hr_bpm >= 0 else '—'}")

    def update_cuff(self, mmhg: int, caution: int, status: int):
        self.lbl_cuff.setText(f"Manguito: {mmhg} mmHg")
