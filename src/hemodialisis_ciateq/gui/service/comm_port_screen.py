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
    config_changed = Signal(str, str, bool)  # id_sensor/controlador, puerto, habilitado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_ports = self._get_filtered_ports()  # Obtener puertos iniciales
        self._loaded_settings = self._load_settings()  # Cargar configuraciones
        
        self.setup_ui()  # Configurar UI
        self._apply_loaded_settings_to_ui()  # Aplicar configuraciones cargadas
        
        # Conexión de señales de cambio de índice indexadas
        self.cmb_main_port.currentIndexChanged.connect(lambda: self._handle_port_change('main'))
        self.cmb_cond_port.currentIndexChanged.connect(lambda: self._handle_port_change('cond'))
        self.cmb_bioz_port.currentIndexChanged.connect(lambda: self._handle_port_change('bioz'))

    def _get_filtered_ports(self):
        """Obtiene y filtra los puertos COM disponibles."""
        ports = ["Auto"]  # Opción predeterminada
        try:
            for port in serial.tools.list_ports.comports():
                # Nota: Para el controlador principal dejamos que pasen todos o controlamos
                # la lista de forma global. No se excluye FTDI del sistema entero, pero
                # la exclusión mutua evitará que se pisen entre combos.
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
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a;")
        layout.addWidget(title)

        # ─── GRUPO 1: CONTROLADOR PRINCIPAL MÁQUINA ───────────────────────
        self.grp_main = QGroupBox("Controlador Principal (Máquina de Hemodiálisis)")
        self.grp_main.setStyleSheet("font-size: 26px; font-weight: 600; color: #0f172a;")
        lyt_main = QHBoxLayout(self.grp_main)
        lyt_main.setSpacing(15)
        
        self.chk_main = QCheckBox("Habilitar Comunicación")
        self.chk_main.setStyleSheet("""
            QCheckBox { color: #0f172a; font-size: 26px; spacing: 15px; }
            QCheckBox::indicator { width: 35px; height: 35px; }
        """)
        lbl_port_main = QLabel("Puerto:")
        lbl_port_main.setStyleSheet("font-size: 26px;")
        self.cmb_main_port = QComboBox()
        self.cmb_main_port.setStyleSheet("font-size: 26px; min-width: 180px;")
        
        lyt_main.addWidget(self.chk_main)
        lyt_main.addWidget(lbl_port_main)
        lyt_main.addWidget(self.cmb_main_port)
        lyt_main.addStretch()
        self.grp_main.setLayout(lyt_main)
        layout.addWidget(self.grp_main)

        # ─── GRUPO 2: SENSOR DE CONDUCTIVIDAD PATRÓN ─────────────────────
        self.grp_cond = QGroupBox("Sensor de Conductividad Patrón")
        self.grp_cond.setStyleSheet("font-size: 26px; font-weight: 600; color: #0f172a;")
        lyt_cond = QHBoxLayout(self.grp_cond)
        lyt_cond.setSpacing(15)
        self.chk_cond = QCheckBox("Habilitar Comunicación")
        self.chk_cond.setStyleSheet("""
            QCheckBox { color: #0f172a; font-size: 26px; spacing: 15px; }
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

        # ─── GRUPO 3: SENSOR BIOIMPEDANCIA / UREA ─────────────────────────
        self.grp_bioz = QGroupBox("Sensor Bioimpedancia / Urea")
        self.grp_bioz.setStyleSheet("font-size: 26px; font-weight: 600; color: #0f172a;")
        lyt_bioz = QHBoxLayout(self.grp_bioz)
        lyt_bioz.setSpacing(15)
        self.chk_bioz = QCheckBox("Habilitar Comunicación")
        self.chk_bioz.setStyleSheet("""
            QCheckBox { color: #0f172a; font-size: 26px; spacing: 15px; }
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

        # ─── CONTENEDOR BOTONES EN PARALELO (HORIZONTAL) ──────────────────
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignCenter)

        self.btn_apply = QPushButton("Aplicar Cambios")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                color: #ffffff;
                font-size: 26px;
                font-weight: bold;
                padding: 12px 30px;
                border-radius: 8px;
                min-height: 80px;
                min-width: 240px;
            }
            QPushButton:hover { background-color: #60a5fa; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        self.btn_apply.clicked.connect(self.apply_configurations)
        
        self.btn_refresh = QPushButton("Actualizar Puertos")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                color: #ffffff;
                font-size: 26px;
                font-weight: bold;
                padding: 12px 30px;
                border-radius: 8px;
                min-height: 80px;
                min-width: 240px;
            }
            QPushButton:hover { background-color: #60a5fa; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        self.btn_refresh.clicked.connect(self.refresh_ports)

        # Añadimos los botones horizontalmente al contenedor secundario
        buttons_layout.addWidget(self.btn_apply)
        buttons_layout.addWidget(self.btn_refresh)
        
        # Agregamos el layout de botones al contenedor principal de la pantalla
        layout.addLayout(buttons_layout)

        layout.addStretch()
        
        # Inicializar contenido de ComboBoxes
        self.cmb_main_port.addItems(self.all_ports)
        self.cmb_cond_port.addItems(self.all_ports)
        self.cmb_bioz_port.addItems(self.all_ports)

    def _handle_port_change(self, changed_sensor: str):
        """Maneja el cambio de puerto hecho por el usuario (evita recursión)"""
        self._block_signals(True)
        try:
            self._update_port_exclusion()
        finally:
            self._block_signals(False)

        logger.debug(f"Puerto cambiado manualmente por usuario: {changed_sensor}")

    def _block_signals(self, block: bool):
        """Bloquea o desbloquea las señales de los tres combobox para evitar bucles infinitos"""
        self.cmb_main_port.blockSignals(block)
        self.cmb_cond_port.blockSignals(block)
        self.cmb_bioz_port.blockSignals(block)

    def _update_port_exclusion(self):
        """Actualiza la exclusión mutua de puertos asignados entre los tres controladores"""
        main_port = self.cmb_main_port.currentText()
        cond_port = self.cmb_cond_port.currentText()
        bioz_port = self.cmb_bioz_port.currentText()

        # Guarda la selección actual y limpia/repuebla todo
        self._repopulate_combos()

        # Remueve puertos seleccionados de los combos contrarios (si no están en "Auto")
        if main_port != "Auto":
            self._remove_port_from_combo(self.cmb_cond_port, main_port)
            self._remove_port_from_combo(self.cmb_bioz_port, main_port)

        if cond_port != "Auto":
            self._remove_port_from_combo(self.cmb_main_port, cond_port)
            self._remove_port_from_combo(self.cmb_bioz_port, cond_port)

        if bioz_port != "Auto":
            self._remove_port_from_combo(self.cmb_main_port, bioz_port)
            self._remove_port_from_combo(self.cmb_cond_port, bioz_port)

    def _repopulate_combos(self):
        """Repuebla los tres combos sin disparar señales recursivas"""
        current_main = self.cmb_main_port.currentText()
        current_cond = self.cmb_cond_port.currentText()
        current_bioz = self.cmb_bioz_port.currentText()

        self._block_signals(True)
        try:
            self.cmb_main_port.clear()
            self.cmb_cond_port.clear()
            self.cmb_bioz_port.clear()

            self.cmb_main_port.addItems(self.all_ports)
            self.cmb_cond_port.addItems(self.all_ports)
            self.cmb_bioz_port.addItems(self.all_ports)

            if current_main in self.all_ports:
                self.cmb_main_port.setCurrentText(current_main)
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
        """Refresca la lista de puertos disponibles en el sistema operativo"""
        try:
            current_main = self.cmb_main_port.currentText()
            current_cond = self.cmb_cond_port.currentText()
            current_bioz = self.cmb_bioz_port.currentText()

            self.all_ports = self._get_filtered_ports()

            self._block_signals(True)
            try:
                self.cmb_main_port.clear()
                self.cmb_cond_port.clear()
                self.cmb_bioz_port.clear()

                self.cmb_main_port.addItems(self.all_ports)
                self.cmb_cond_port.addItems(self.all_ports)
                self.cmb_bioz_port.addItems(self.all_ports)

                # Restaurar selecciones
                self.cmb_main_port.setCurrentText(current_main if current_main in self.all_ports else "Auto")
                self.cmb_cond_port.setCurrentText(current_cond if current_cond in self.all_ports else "Auto")
                self.cmb_bioz_port.setCurrentText(current_bioz if current_bioz in self.all_ports else "Auto")
            finally:
                self._block_signals(False)

            self._update_port_exclusion()
            logger.info(f"Puertos actualizados dinámicamente. Encontrados: {len(self.all_ports)-1}")
            self.show_info_message("Lista de puertos actualizada correctamente.", 3000)

        except Exception as e:
            logger.error(f"Error al refrescar puertos: {e}")            
            self.show_warning_message(f"Error al actualizar puertos:\n{str(e)}", 5000)

    def _load_settings(self):
        default = {
            "main_control": {"port": "Auto", "enabled": False},
            "conductivity_sensor": {"port": "Auto", "enabled": False},
            "bioz_urea_sensor": {"port": "Auto", "enabled": False},
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Configuración cargada desde {CONFIG_FILE}")
                return {**default, **settings}
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
        logger.warning("Usando configuración por defecto")
        return default

    def _save_settings(self):
        settings = {
            "main_control": {"port": self.cmb_main_port.currentText(), "enabled": self.chk_main.isChecked()},
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
        main = self._loaded_settings.get("main_control", {})
        cond = self._loaded_settings.get("conductivity_sensor", {})
        bioz = self._loaded_settings.get("bioz_urea_sensor", {})
        
        self.cmb_main_port.setCurrentText(main.get("port", "Auto"))
        self.cmb_cond_port.setCurrentText(cond.get("port", "Auto"))
        self.cmb_bioz_port.setCurrentText(bioz.get("port", "Auto"))
        
        self.chk_main.setChecked(main.get("enabled", False))
        self.chk_cond.setChecked(cond.get("enabled", False))
        self.chk_bioz.setChecked(bioz.get("enabled", False))
        
        self._update_port_exclusion()

    def apply_configurations(self):
        self._save_settings()
        self.emit_current_configurations()
        self.show_success_message("Configuración de puertos guardada y aplicada correctamente.", 3000)

    def emit_current_configurations(self):
        self.config_changed.emit("MAIN_CONTROL", self.cmb_main_port.currentText(), self.chk_main.isChecked())
        self.config_changed.emit("CONDUCTIVITY", self.cmb_cond_port.currentText(), self.chk_cond.isChecked())
        self.config_changed.emit("BIOZ", self.cmb_bioz_port.currentText(), self.chk_bioz.isChecked())

    # ─── MÉTODOS DE MENSAJES FLOTANTES ─────────────────────────────────
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

