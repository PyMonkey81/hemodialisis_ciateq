# gui/service/comm_port_screen.py

import serial.tools.list_ports
from PySide6.QtWidgets import QFrame, QGridLayout, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox
from PySide6.QtCore import Signal, Qt
import json
from gui.components.floating_message import FloatingMessage
from utilities.platform_runtime import sanitize_port_for_platform, get_runtime_config_path, safe_json_load
import logging
logger = logging.getLogger(__name__)


CONFIG_FILE = get_runtime_config_path("sensor_comm_config.json")

class CommPortScreen(QWidget):
    config_changed = Signal(str, str, bool)  # id_sensor, puerto, habilitado

    def __init__(self, parent=None):
        super().__init__(parent)
        self._signal_block_depth = 0
        self.all_ports = self._get_filtered_ports()
        self._loaded_settings = self._load_settings()
        self.setObjectName("CommPortScreen")
        self.setStyleSheet("QWidget#CommPortScreen { background-color: #FCFCFC; }")

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.setup_ui()
        self._apply_loaded_settings_to_ui()
        
        # Señales de cambio de puerto
        self.cmb_main_port.currentIndexChanged.connect(lambda: self._handle_port_change('main'))
        self.cmb_cond_port.currentIndexChanged.connect(lambda: self._handle_port_change('cond'))
        self.cmb_mega_port.currentIndexChanged.connect(lambda: self._handle_port_change('mega'))
        self.cmb_bioz_port.currentIndexChanged.connect(lambda: self._handle_port_change('bioz'))
        self.cmb_led_port.currentIndexChanged.connect(lambda: self._handle_port_change('led'))

    def _get_filtered_ports(self):
        ports = ["Auto"]
        try:
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
            return ports
        except Exception as e:
            logger.error(f"Error obteniendo puertos: {e}")
            return ports

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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(7, 7, 7, 7)
        main_layout.setSpacing(10)
        # Título principal
        title = QLabel("Configuración de Puertos de Comunicación")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a; background: transparent;")

        main_layout.addWidget(title, alignment=Qt.AlignTop | Qt.AlignHCenter)


        layout = QGridLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(7, 7, 7, 7)

        # ─── CARD 1: CONTROL PRINCIPAL ───────────────────────────────────────
        control_card = QFrame()
        control_card.setObjectName("card")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(7)

        control_title = QLabel("Control Principal")
        control_title.setObjectName("card_title")
        control_title.setMinimumWidth(280)
        control_layout.addWidget(control_title)


        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)
        

        self.chk_main = QCheckBox("Habilitar")
        self.chk_main.setStyleSheet(chk_style)

        lbl_port_main = QLabel("Puerto:")
        lbl_port_main.setStyleSheet("font-size: 22px; color: #0f172a;")

        self.cmb_main_port = QComboBox()
        self.cmb_main_port.setStyleSheet(combo_style)

        ctrl_layout.addWidget(self.chk_main)
        ctrl_layout.addWidget(lbl_port_main)
        ctrl_layout.addWidget(self.cmb_main_port)
        ctrl_layout.addStretch()
        control_layout.addLayout(ctrl_layout)
        layout.addWidget(control_card, 1, 0, 1, 1)

        # ─── CARD 2: SENSOR CONDUCTIVIDAD HDM ────────────────────────────────
        sensor1_card = QFrame()
        sensor1_card.setObjectName("card")        
        sensor1_layout = QVBoxLayout(sensor1_card)
        sensor1_layout.setContentsMargins(10, 10, 10, 10)
        sensor1_layout.setSpacing(7)

        sensor1_title = QLabel("Sensor Conductividad (HDM)")
        sensor1_title.setObjectName("card_title")
        sensor1_title.setMinimumWidth(280)
        sensor1_layout.addWidget(sensor1_title)

        s1_layout = QHBoxLayout()
        s1_layout.setSpacing(10)

        self.chk_cond = QCheckBox("Habilitar")
        self.chk_cond.setStyleSheet(chk_style)

        lbl_port_cond = QLabel("Puerto:")
        lbl_port_cond.setStyleSheet("font-size: 22px; color: #0f172a;")

        self.cmb_cond_port = QComboBox()
        self.cmb_cond_port.setStyleSheet(combo_style)

        s1_layout.addWidget(self.chk_cond)
        s1_layout.addWidget(lbl_port_cond)
        s1_layout.addWidget(self.cmb_cond_port)
        s1_layout.addStretch()
        sensor1_layout.addLayout(s1_layout)
        layout.addWidget(sensor1_card, 1, 1, 1, 1)

        # ─── CARD 3: SENSOR CONDUCTIVIDAD MEGA ───────────────────────────────
        sensor2_card = QFrame()
        sensor2_card.setObjectName("card")
        sensor2_layout = QVBoxLayout(sensor2_card)
        sensor2_layout.setContentsMargins(10, 10, 10, 10)
        sensor2_layout.setSpacing(7)

        sensor2_title = QLabel("Sensor Conductividad (Mega)")
        sensor2_title.setObjectName("card_title")
        sensor2_title.setMinimumWidth(280)
        sensor2_layout.addWidget(sensor2_title)

        s2_layout = QHBoxLayout()
        s2_layout.setSpacing(10)

        self.chk_mega = QCheckBox("Habilitar")
        self.chk_mega.setStyleSheet(chk_style)

        lbl_port_mega = QLabel("Puerto:")
        lbl_port_mega.setStyleSheet("font-size: 22px; color: #0f172a;")

        self.cmb_mega_port = QComboBox()
        self.cmb_mega_port.setStyleSheet(combo_style)

        # sensor2_layout.addWidget(sensor2_title)
        s2_layout.addWidget(self.chk_mega)
        s2_layout.addWidget(lbl_port_mega)
        s2_layout.addWidget(self.cmb_mega_port)
        s2_layout.addStretch()
        sensor2_layout.addLayout(s2_layout)
        layout.addWidget(sensor2_card, 2, 0, 1, 1)

        # ─── CARD 4: SENSOR BIOIMPEDANCIA / UREA ─────────────────────────────
        sensor3_card = QFrame()
        sensor3_card.setObjectName("card")
        sensor3_layout = QVBoxLayout(sensor3_card)
        sensor3_layout.setContentsMargins(10, 10, 10, 10)
        sensor3_layout.setSpacing(7)

        sensor3_title = QLabel("Sensor Bioimpedancia / Urea")
        sensor3_title.setObjectName("card_title")
        sensor3_title.setMinimumWidth(280)
        sensor3_layout.addWidget(sensor3_title)

        s3_layout = QHBoxLayout()
        s3_layout.setSpacing(10)

        self.chk_bioz = QCheckBox("Habilitar")
        self.chk_bioz.setStyleSheet(chk_style)

        lbl_port_bioz = QLabel("Puerto:")
        lbl_port_bioz.setStyleSheet("font-size: 22px; color: #0f172a;")

        self.cmb_bioz_port = QComboBox()
        self.cmb_bioz_port.setStyleSheet(combo_style)

        # sensor3_layout.addWidget(sensor3_title)
        s3_layout.addWidget(self.chk_bioz)
        s3_layout.addWidget(lbl_port_bioz)
        s3_layout.addWidget(self.cmb_bioz_port)
        s3_layout.addStretch()
        sensor3_layout.addLayout(s3_layout)
        layout.addWidget(sensor3_card, 2, 1, 1, 1)


        # -------  Card de Barra LED (ocupa las 2 columnas)
        led_card = QFrame()
        led_card.setObjectName("card")
        led_layout = QVBoxLayout(led_card)
        led_layout.setContentsMargins(10, 10, 10, 10)
        led_layout.setSpacing(7)

        led_title = QLabel("Barra LED / Buzzer")
        led_title.setObjectName("card_title")
        led_title.setMinimumWidth(280)
        led_layout.addWidget(led_title)

        ld_layout = QHBoxLayout()
        ld_layout.setSpacing(10)

        self.chk_led = QCheckBox("Habilitar")
        self.chk_led.setStyleSheet(chk_style)

        lbl_port_led = QLabel("Puerto:")
        lbl_port_led.setStyleSheet("font-size: 22px; color: #0f172a;")

        self.cmb_led_port = QComboBox()
        self.cmb_led_port.setStyleSheet(combo_style)

        ld_layout.addWidget(self.chk_led)
        ld_layout.addWidget(lbl_port_led)
        ld_layout.addWidget(self.cmb_led_port)
        ld_layout.addStretch()
        led_layout.addLayout(ld_layout)

        layout.addWidget(led_card, 3, 0, 1, 1)

        # ─── BOTONES ─────────────────────────────────────────────────────────
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)
        buttons_layout.setAlignment(Qt.AlignCenter)

        btn_style = """
            QPushButton {
                background-color: #06298a;
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 12px 28px;
                border-radius: 10px;
                min-height: 70px;
                min-width: 220px;
            }
            QPushButton:hover { background-color: #1e293b; }
            QPushButton:pressed { background-color: #334155; }
        """

        self.btn_apply = QPushButton("Aplicar Cambios")
        self.btn_apply.setStyleSheet(btn_style)
        self.btn_apply.clicked.connect(self.apply_configurations)

        self.btn_refresh = QPushButton("Actualizar Puertos")
        self.btn_refresh.setStyleSheet(btn_style)
        self.btn_refresh.clicked.connect(self.refresh_ports)

        buttons_layout.addWidget(self.btn_apply)
        buttons_layout.addWidget(self.btn_refresh)
        layout.addLayout(buttons_layout, 3, 1, 1, 1)
        # layout.addStretch()

        # Llenar combos
        self.cmb_main_port.addItems(self.all_ports)
        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_mega_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)
        self.cmb_led_port.addItems(self.all_ports)    

        main_layout.addLayout(layout)
        main_layout.addStretch()

    def _handle_port_change(self, changed_sensor: str):
        self._block_signals(True)
        try:
            self._update_port_exclusion()
        finally:
            self._block_signals(False)
        logger.debug(f"Puerto cambiado: {changed_sensor}")

    def _block_signals(self, block: bool):
        # Permite llamadas anidadas sin desbloquear señales antes de tiempo.
        if block:
            self._signal_block_depth += 1
            if self._signal_block_depth == 1:
                self.cmb_main_port.blockSignals(True)
                self.cmb_cond_port.blockSignals(True)
                self.cmb_mega_port.blockSignals(True)
                self.cmb_bioz_port.blockSignals(True)
                self.cmb_led_port.blockSignals(True)
            return

        if self._signal_block_depth > 0:
            self._signal_block_depth -= 1

        if self._signal_block_depth == 0:
            self.cmb_main_port.blockSignals(False)
            self.cmb_cond_port.blockSignals(False)
            self.cmb_mega_port.blockSignals(False)
            self.cmb_bioz_port.blockSignals(False)
            self.cmb_led_port.blockSignals(False)

    def _update_port_exclusion(self):
        """Exclusión mutua entre los 5 combos"""
        main_port = self.cmb_main_port.currentText()
        cond_port = self.cmb_cond_port.currentText()
        mega_port  = self.cmb_mega_port.currentText()
        bioz_port = self.cmb_bioz_port.currentText()
        led_port = self.cmb_led_port.currentText()

        self._repopulate_combos()

        # Quitar el puerto seleccionado de los otros combos
        for port, combos in [
            (main_port, [self.cmb_cond_port, self.cmb_mega_port, self.cmb_bioz_port, self.cmb_led_port]),
            (cond_port, [self.cmb_main_port, self.cmb_mega_port, self.cmb_bioz_port, self.cmb_led_port]),
            (mega_port,  [self.cmb_main_port, self.cmb_cond_port, self.cmb_bioz_port, self.cmb_led_port]),
            (bioz_port, [self.cmb_main_port, self.cmb_cond_port, self.cmb_mega_port, self.cmb_led_port]),
            (led_port, [self.cmb_main_port, self.cmb_cond_port, self.cmb_mega_port, self.cmb_bioz_port]),
        ]:
            if port != "Auto":
                for combo in combos:
                    self._remove_port_from_combo(combo, port)

    def _repopulate_combos(self):
        current_main = self.cmb_main_port.currentText()
        current_cond = self.cmb_cond_port.currentText()
        current_mega  = self.cmb_mega_port.currentText()
        current_bioz = self.cmb_bioz_port.currentText()
        current_led = self.cmb_led_port.currentText()

        self._block_signals(True)
        try:
            for combo in [self.cmb_main_port, self.cmb_cond_port, self.cmb_mega_port, self.cmb_bioz_port, self.cmb_led_port]:
                combo.clear()
                combo.addItems(self.all_ports)

            if current_main in self.all_ports: self.cmb_main_port.setCurrentText(current_main)
            if current_cond in self.all_ports: self.cmb_cond_port.setCurrentText(current_cond)
            if current_mega  in self.all_ports: self.cmb_mega_port.setCurrentText(current_mega)
            if current_bioz in self.all_ports: self.cmb_bioz_port.setCurrentText(current_bioz)
            if current_led in self.all_ports: self.cmb_led_port.setCurrentText(current_led)
        finally:
            self._block_signals(False)

    def _remove_port_from_combo(self, combo: QComboBox, port_to_remove: str):
        index = combo.findText(port_to_remove)
        if index >= 0:
            combo.removeItem(index)

    def refresh_ports(self):
        try:
            current_main = self.cmb_main_port.currentText()
            current_cond = self.cmb_cond_port.currentText()
            current_mega  = self.cmb_mega_port.currentText()
            current_bioz = self.cmb_bioz_port.currentText()
            current_led = self.cmb_led_port.currentText()

            self.all_ports = self._get_filtered_ports()

            self._block_signals(True)
            try:
                for combo in [self.cmb_main_port, self.cmb_cond_port, self.cmb_mega_port, self.cmb_bioz_port, self.cmb_led_port]:
                    combo.clear()
                    combo.addItems(self.all_ports)

                self.cmb_main_port.setCurrentText(current_main if current_main in self.all_ports else "Auto")
                self.cmb_cond_port.setCurrentText(current_cond if current_cond in self.all_ports else "Auto")
                self.cmb_mega_port.setCurrentText(current_mega  if current_mega  in self.all_ports else "Auto")
                self.cmb_bioz_port.setCurrentText(current_bioz if current_bioz in self.all_ports else "Auto")
                self.cmb_led_port.setCurrentText(current_led if current_led in self.all_ports else "Auto")
            finally:
                self._block_signals(False)

            self._update_port_exclusion()
            self.show_info_message("Lista de puertos actualizada correctamente.", 3000)

        except Exception as e:
            logger.error(f"Error al refrescar puertos: {e}")
            self.show_warning_message(f"Error al actualizar puertos:\n{str(e)}", 5000)

    def _load_settings(self):
        default = {
            "main_control": {"port": "Auto", "enabled": False},
            "conductivity_sensor": {"port": "Auto", "enabled": False},      # HDM
            "mega_conductivity_sensor": {"port": "Auto", "enabled": False},  # Mega
            "bioz_urea_sensor": {"port": "Auto", "enabled": False},
            "led_controller": {"port": "Auto", "enabled": False},
        }
        if CONFIG_FILE.exists():
            try:
                settings = safe_json_load(CONFIG_FILE, {})
                if not isinstance(settings, dict):
                    raise ValueError("La configuración de puertos no es un objeto JSON válido.")
                merged = {**default, **settings}
                self._sanitize_platform_ports(merged)
                return merged
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
        return default

    def _sanitize_platform_ports(self, settings: dict):
        for sensor_key in ("main_control", "conductivity_sensor", "mega_conductivity_sensor", "bioz_urea_sensor", "led_controller"):
            sensor_cfg = settings.get(sensor_key, {})
            port_value = str(sensor_cfg.get("port", "Auto")).strip()
            sanitized = sanitize_port_for_platform(port_value)
            if sanitized != port_value:
                sensor_cfg["port"] = "Auto"
                settings[sensor_key] = sensor_cfg

    def _save_settings(self):
        settings = {
            "main_control": {
                "port": self.cmb_main_port.currentText(),
                "enabled": self.chk_main.isChecked()
            },
            "conductivity_sensor": {          # HDM18/19
                "port": self.cmb_cond_port.currentText(),
                "enabled": self.chk_cond.isChecked()
            },
            "mega_conductivity_sensor": {      # Arduino Mega
                "port": self.cmb_mega_port.currentText(),
                "enabled": self.chk_mega.isChecked()
            },
            "bioz_urea_sensor": {
                "port": self.cmb_bioz_port.currentText(),
                "enabled": self.chk_bioz.isChecked()
            },
            "led_controller": {
                "port": self.cmb_led_port.currentText(),
                "enabled": self.chk_led.isChecked()
            }
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with CONFIG_FILE.open('w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuración guardada en {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            self.show_error_message("No se pudo guardar la configuración.", 5000)

    def _apply_loaded_settings_to_ui(self):
        main = self._loaded_settings.get("main_control", {})
        cond = self._loaded_settings.get("conductivity_sensor", {})
        mega  = self._loaded_settings.get("mega_conductivity_sensor", {})
        bioz = self._loaded_settings.get("bioz_urea_sensor", {})
        led = self._loaded_settings.get("led_controller", {})
        
        self.cmb_main_port.setCurrentText(main.get("port", "Auto"))
        self.cmb_cond_port.setCurrentText(cond.get("port", "Auto"))
        self.cmb_mega_port.setCurrentText(mega.get("port", "Auto"))
        self.cmb_bioz_port.setCurrentText(bioz.get("port", "Auto"))
        self.cmb_led_port.setCurrentText(led.get("port", "Auto"))
        
        self.chk_main.setChecked(main.get("enabled", False))
        self.chk_cond.setChecked(cond.get("enabled", False))
        self.chk_mega.setChecked(mega.get("enabled", False))
        self.chk_bioz.setChecked(bioz.get("enabled", False))
        self.chk_led.setChecked(led.get("enabled", False))
        
        self._update_port_exclusion()

    def apply_configurations(self):
        self._save_settings()
        self.emit_current_configurations()
        self.show_success_message("Configuración de puertos guardada y aplicada correctamente.", 3000)

    def emit_current_configurations(self):
        self.config_changed.emit("MAIN_CONTROL", self.cmb_main_port.currentText(), self.chk_main.isChecked())
        self.config_changed.emit("CONDUCTIVITY", self.cmb_cond_port.currentText(), self.chk_cond.isChecked())       # HDM
        self.config_changed.emit("MEGA_CONDUCTIVITY", self.cmb_mega_port.currentText(), self.chk_mega.isChecked())  # mega
        self.config_changed.emit("BIOZ", self.cmb_bioz_port.currentText(), self.chk_bioz.isChecked())
        self.config_changed.emit("LED_CONTROLLER", self.cmb_led_port.currentText(), self.chk_led.isChecked())

    # ─── Mensajes flotantes (igual que antes) ─────────────────────────────
    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_floating_message(text, timeout_ms)

    def show_success_message(self, text: str, timeout_ms: int = 4000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_success_message(text, timeout_ms)

    def show_info_message(self, text: str, timeout_ms: int = 3800):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_info_message(text, timeout_ms)

    def show_warning_message(self, text: str, timeout_ms: int = 4500):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_warning_message(text, timeout_ms)
    
    def show_error_message(self, text: str, timeout_ms: int = 5000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_error_message(text, timeout_ms)


