# gui/service/comm_port_screen.py

import serial.tools.list_ports
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox, QMessageBox
from PySide6.QtCore import Signal, Qt
import json
import os 
from hemodialisis_ciateq.gui.components.floating_message import FloatingMessage
import logging
logger = logging.getLogger(__name__)


CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "sensor_comm_config.json")

class CommPortScreen(QWidget):
    config_changed = Signal(str, str, bool)  # id_sensor, puerto, habilitado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_ports = self._get_filtered_ports()  # Obtener puertos iniciales
        self._loaded_settings = self._load_settings()  # Cargar configuraciones
        self.setup_ui()  # Configurar UI
        self._apply_loaded_settings_to_ui()  # Aplicar configuraciones cargadas
        self.cmb_cond_port.currentIndexChanged.connect(lambda: self._handle_port_change('cond'))
        self.cmb_bioz_port.currentIndexChanged.connect(lambda: self._handle_port_change('bioz'))

    def _get_filtered_ports(self):
        """Obtiene y filtra los puertos COM disponibles, excluyendo FTDI."""
        ports = ["Auto"]  # Opción predeterminada
        try:
            for port in serial.tools.list_ports.comports():
                if port.manufacturer and "FTDI" in port.manufacturer.upper():
                    logger.debug(f"Puerto FTDI excluido: {port.device}")
                    continue
                ports.append(port.device)
            return ports
        except Exception as e:
            logger.error(f"Error obteniendo puertos: {e}")
            return ports  # Retorna al menos ["Auto"]

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Configuración de Puertos de Comunicación")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e3a8a;")
        layout.addWidget(title)

        self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
        self.grp_cond.setStyleSheet("font-size: 26px; font-weight: 600;")
        lyt_cond = QHBoxLayout(self.grp_cond)
        lyt_cond.setSpacing(15)
        self.chk_cond = QCheckBox("Habilitar Comunicación")
        self.chk_cond.setStyleSheet("""
            QCheckBox { color: #000000; font-size: 26px; spacing: 15px; }
            QCheckBox::indicator { width: 35px; height: 35px; }
        """)
        lbl_port_cond = QLabel("Puerto:")
        lbl_port_cond.setStyleSheet("font-size: 26px;")
        self.cmb_cond_port = QComboBox()
        self.cmb_cond_port.setStyleSheet("font-size: 26px; min-width: 180px;")
        lyt_cond.addWidget(self.chk_cond)
        lyt_cond.addWidget(lbl_port_cond)
        lyt_cond.addWidget(self.cmb_cond_port)
        lyt_cond.addStretch()
        self.grp_cond.setLayout(lyt_cond)
        layout.addWidget(self.grp_cond)

        self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
        self.grp_bioz.setStyleSheet("font-size: 26px; font-weight: 600;")
        lyt_bioz = QHBoxLayout(self.grp_bioz)
        lyt_bioz.setSpacing(15)
        self.chk_bioz = QCheckBox("Habilitar Comunicación")
        self.chk_bioz.setStyleSheet("""
            QCheckBox { color: #000000; font-size: 26px; spacing: 15px; }
            QCheckBox::indicator { width: 35px; height: 35px; }
        """)
        lbl_port_bioz = QLabel("Puerto:")
        lbl_port_bioz.setStyleSheet("font-size: 26px;")
        self.cmb_bioz_port = QComboBox()
        self.cmb_bioz_port.setStyleSheet("font-size: 26px; min-width: 180px;")
        lyt_bioz.addWidget(self.chk_bioz)
        lyt_bioz.addWidget(lbl_port_bioz)
        lyt_bioz.addWidget(self.cmb_bioz_port)
        lyt_bioz.addStretch()
        self.grp_bioz.setLayout(lyt_bioz)
        layout.addWidget(self.grp_bioz)

        self.btn_apply = QPushButton("Aplicar Cambios")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-size: 26px;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover { background-color: #60a5fa; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        self.btn_apply.clicked.connect(self.apply_configurations)
        layout.addWidget(self.btn_apply, alignment=Qt.AlignCenter)

        self.btn_refresh = QPushButton("Actualizar Puertos")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;  /* Verde para diferenciar de Aplicar */
                color: white;
                font-size: 26px;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                min-height: 80px;
            }
            QPushButton:hover { background-color: #16a34a; }
            QPushButton:pressed { background-color: #15803d; }
        """)
        self.btn_refresh.clicked.connect(self.refresh_ports)  # Conectar al método refresh_ports
        layout.addWidget(self.btn_refresh, alignment=Qt.AlignCenter)

        layout.addStretch()
        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)

    def _handle_port_change(self, changed_sensor: str):
        """Maneja el cambio de puerto hecho por el usuario (evita recursión)"""
        # Bloqueamos las señales temporalmente para evitar recursión
        self._block_signals(True)
        try:
            self._update_port_exclusion()
        finally:
            self._block_signals(False)

        logger.debug(f"Puerto cambiado manualmente por usuario: {changed_sensor}")

    def _block_signals(self, block: bool):
        """Bloquea o desbloquea las señales de los combobox para evitar recursión"""
        self.cmb_cond_port.blockSignals(block)
        self.cmb_bioz_port.blockSignals(block)

    def _update_port_exclusion(self):
        """Actualiza la exclusión mutua entre los dos puertos"""
        cond_port = self.cmb_cond_port.currentText()
        bioz_port = self.cmb_bioz_port.currentText()

        # Guardamos la selección actual antes de repoblar
        self._repopulate_combos()

        # Aplicamos exclusión
        if cond_port != "Auto":
            self._remove_port_from_combo(self.cmb_bioz_port, cond_port)

        if bioz_port != "Auto":
            self._remove_port_from_combo(self.cmb_cond_port, bioz_port)

    def _repopulate_combos(self):
        """Repuebla ambos combos sin disparar señales (usando blockSignals)"""
        current_cond = self.cmb_cond_port.currentText()
        current_bioz = self.cmb_bioz_port.currentText()

        self._block_signals(True)        # ← Bloqueamos aquí también
        try:
            self.cmb_cond_port.clear()
            self.cmb_bioz_port.clear()

            self.cmb_cond_port.addItems(self.all_ports)
            self.cmb_bioz_port.addItems(self.all_ports)

            if current_cond in self.all_ports:
                self.cmb_cond_port.setCurrentText(current_cond)
            if current_bioz in self.all_ports:
                self.cmb_bioz_port.setCurrentText(current_bioz)
        finally:
            self._block_signals(False)

    def _remove_port_from_combo(self, combo: QComboBox, port_to_remove: str):
        """Elimina un puerto de un combo de forma segura"""
        index = combo.findText(port_to_remove)
        if index >= 0:
            combo.removeItem(index)

    def refresh_ports(self):
        """Refresca la lista de puertos disponibles"""
        try:
            # Guardamos selecciones actuales
            current_cond = self.cmb_cond_port.currentText()
            current_bioz = self.cmb_bioz_port.currentText()

            # Obtenemos nueva lista de puertos
            self.all_ports = self._get_filtered_ports()

            # Bloqueamos señales antes de modificar todo
            self._block_signals(True)
            try:
                self.cmb_cond_port.clear()
                self.cmb_bioz_port.clear()

                self.cmb_cond_port.addItems(self.all_ports)
                self.cmb_bioz_port.addItems(self.all_ports)

                # Restauramos selecciones si aún existen
                if current_cond in self.all_ports:
                    self.cmb_cond_port.setCurrentText(current_cond)
                else:
                    self.cmb_cond_port.setCurrentText("Auto")

                if current_bioz in self.all_ports:
                    self.cmb_bioz_port.setCurrentText(current_bioz)
                else:
                    self.cmb_bioz_port.setCurrentText("Auto")

            finally:
                self._block_signals(False)

            self._update_port_exclusion()

            logger.info(f"Puertos actualizados. Total: {len(self.all_ports)-1} puertos físicos.")
            
            self.show_info_message("Lista de puertos actualizada correctamente.", 3000)

        except Exception as e:
            logger.error(f"Error al refrescar puertos: {e}")            
            self.show_warning_message(f"Error al actualizar puertos:\n{str(e)}", 5000)

   

    def _load_settings(self):
        default = {
            "conductivity_sensor": {"port": "Auto", "enabled": False},
            "bioz_urea_sensor": {"port": "Auto", "enabled": False},
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Configuración cargada desde {CONFIG_FILE}")
                return {**default, **settings}  # Mergea con default
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
        logger.warning("Usando configuración por defecto")
        return default

    def _save_settings(self):
        settings = {
            "conductivity_sensor": {"port": self.cmb_cond_port.currentText(), "enabled": self.chk_cond.isChecked()},
            "bioz_urea_sensor": {"port": self.cmb_bioz_port.currentText(), "enabled": self.chk_bioz.isChecked()}
        }
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuración guardada en {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            self.show_error_message("No se pudo guardar la configuración.", 5000)

    def _apply_loaded_settings_to_ui(self):
        cond = self._loaded_settings.get("conductivity_sensor", {})
        bioz = self._loaded_settings.get("bioz_urea_sensor", {})
        self.cmb_cond_port.setCurrentText(cond.get("port", "Auto"))
        self.cmb_bioz_port.setCurrentText(bioz.get("port", "Auto"))
        self.chk_cond.setChecked(cond.get("enabled", False))
        self.chk_bioz.setChecked(bioz.get("enabled", False))
        self._update_port_exclusion()

    def apply_configurations(self):
        self._save_settings()
        self.emit_current_configurations()
        self.show_success_message(
            "Configuración de puertos guardada y aplicada correctamente.",3000)

    def emit_current_configurations(self):
        self.config_changed.emit("CONDUCTIVITY", self.cmb_cond_port.currentText(), self.chk_cond.isChecked())
        self.config_changed.emit("BIOZ", self.cmb_bioz_port.currentText(), self.chk_bioz.isChecked())

    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        """Método genérico (recomendado)"""
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        
        self._floating_msg.show_floating_message(text, timeout_ms)

    # Métodos específicos (más semánticos)
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
