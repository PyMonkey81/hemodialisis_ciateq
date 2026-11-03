# gui/therapy/patient_config_screen.py

"""
Módulo para la configuración y gestión de perfiles de paciente.

"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QGridLayout,
    QGroupBox, QListWidget, QSizePolicy, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from gui.components.numpad_modal import NumpadDialog
from gui.components.keyboard_modal import KeyboardDialog
from gui.components.floating_confirm import FloatingConfirmDialog   
from gui.components.floating_message import FloatingMessage
from core.variables_map import VARIABLES
import json
from pathlib import Path
from utilities.platform_runtime import get_runtime_config_path, safe_json_load
import logging
logger = logging.getLogger(__name__)

PATIENTS_CONFIG_FILE = get_runtime_config_path("patients.json")

class PatientConfigScreen(QWidget):
    """
    Pantalla de configuración de paciente con entrada táctil.
    - Teclado QWERTY para texto (ID, nombre)
    - Numpad para valores numéricos
    - Mini DB en memoria con pacientes de prueba
    UI con GridLayout 4 columnas, lista fija 200px, sin scroll.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = parent.current_values if parent else {}

        self.patients_db = {}
        self.selected_patient_id = None
        
        self._load_patients_from_file()
        if not self.patients_db:
            self._load_test_patients()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_ui()

    def _load_patients_from_file(self):
        """Carga pacientes desde archivo JSON"""
        if not PATIENTS_CONFIG_FILE.exists():
            logger.info("No se encontró archivo de pacientes. Se usarán datos de prueba.")
            return

        try:
            data = safe_json_load(PATIENTS_CONFIG_FILE, {})
            if not isinstance(data, dict):
                raise ValueError("El archivo de pacientes no contiene un objeto JSON válido.")
            self.patients_db = data
            logger.info(f"Se cargaron {len(self.patients_db)} pacientes desde {PATIENTS_CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error al cargar pacientes desde JSON: {e}")
            self.patients_db = {}
    
    def _save_patients_to_file(self):
        """Guarda todos los pacientes en JSON"""
        try:
            PATIENTS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with PATIENTS_CONFIG_FILE.open('w', encoding='utf-8') as f:
                json.dump(self.patients_db, f, indent=4, ensure_ascii=False)
            logger.info(f"Pacientes guardados correctamente ({len(self.patients_db)})")
        except Exception as e:
            logger.error(f"Error al guardar pacientes en JSON: {e}")

    def _load_test_patients(self):
        """Pacientes de prueba para demo"""
        test_patients = [
            {
                "patient_id": "P001",
                "patient_name": "Juan Pérez López",
                "patient_gender": 1,
                "patient_age": 58,
                "patient_height_cm": 170.0,
                "patient_dry_weight_kg": 68.5,
                "patient_pre_weight_kg": 73.2,
                "patient_nss": "",
                "patient_access_type": "Fístula AV (FAV)",
                "patient_blood_type": "O+",
                "patient_dialyzer": "F8HPS (1.8 m²)",
                "patient_diagnosis": "ERC Estadio 5",
                "patient_physician": "",
                "patient_allergies": "Ninguna conocida",
                "uf_goal_liters": 4.7,
            },
            {
                "patient_id": "P002",
                "patient_name": "María González Ramírez",
                "patient_gender": 2,
                "patient_age": 65,
                "patient_height_cm": 158.0,
                "patient_dry_weight_kg": 55.0,
                "patient_pre_weight_kg": 59.8,
                "patient_nss": "",
                "patient_access_type": "Fístula AV (FAV)",
                "patient_blood_type": "O+",
                "patient_dialyzer": "F8HPS (1.8 m²)",
                "patient_diagnosis": "ERC Estadio 5",
                "patient_physician": "",
                "patient_allergies": "Ninguna conocida",
                "uf_goal_liters": 4.8,
            },
            {
                "patient_id": "P003",
                "patient_name": "Carlos Ramírez Torres",
                "patient_gender": 1,
                "patient_age": 42,
                "patient_height_cm": 175.0,
                "patient_dry_weight_kg": 82.0,
                "patient_pre_weight_kg": 87.5,
                "patient_nss": "",
                "patient_access_type": "Fístula AV (FAV)",
                "patient_blood_type": "O+",
                "patient_dialyzer": "F8HPS (1.8 m²)",
                "patient_diagnosis": "ERC Estadio 5",
                "patient_physician": "",
                "patient_allergies": "Ninguna conocida",
                "uf_goal_liters": 5.5,
            }
        ]
        for p in test_patients:
            self.patients_db[p["patient_id"]] = p

    def setup_ui(self):
        """Construye la UI con el nuevo layout: sin scroll, grid 4 columnas."""
        self.setStyleSheet("background-color: #fcfcfc; border-radius: 15px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # 1. Título centrado
        title = QLabel("Expediente y Configuración Clínica del Paciente")
        title.setStyleSheet("font-size: 34px; font-weight: bold; color: #0f172a;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 2. Selector group
        selector_group = QGroupBox("Seleccionar o registrar paciente")
        selector_group.setStyleSheet("""
            QGroupBox {
                font-size: 26px; font-weight: bold; color: #2563eb;
                border: 2px solid #cbd5e1; border-radius: 10px;
                background-color: #ffffff;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
        """)
        selector_layout = QVBoxLayout(selector_group)
        selector_layout.setContentsMargins(20, 20, 20, 20)
        selector_layout.setSpacing(15)

        list_and_buttons = QHBoxLayout()
        
        self.patient_list = QListWidget()
        self.patient_list.setFixedHeight(200)
        self.patient_list.setStyleSheet("color: #0f172a; font-size: 24px; background-color: #ffffff; border: 1px solid #e2e8f0;")
        self._refresh_patient_list()
        self.patient_list.itemClicked.connect(self._load_selected_patient)
        list_and_buttons.addWidget(self.patient_list)

        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)

        btn_new = QPushButton("Nuevo\nPaciente")
        btn_new.setFixedSize(210, 78)
        btn_new.setStyleSheet("""
            QPushButton {
                font-size: 24px; background: #10b981; color: white;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """)
        btn_new.clicked.connect(self._open_new_patient_dialog)
        buttons_layout.addWidget(btn_new)

        self.btn_delete = QPushButton("Eliminar\nPaciente")
        self.btn_delete.setFixedSize(210, 78)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                font-size: 24px; background: #dc2626; color: white;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
            QPushButton:disabled { background: #94a3b8; color: #cbd5e1; }
        """)
        self.btn_delete.clicked.connect(self._delete_selected_patient)
        self.btn_delete.setEnabled(False)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addStretch()

        list_and_buttons.addLayout(buttons_layout)
        selector_layout.addLayout(list_and_buttons)
        main_layout.addWidget(selector_group)

        # 3. Clinical data group with GridLayout
        self.form_group = QGroupBox("Datos Clínicos, Antropométricos y Prescripción Base")
        self.form_group.setStyleSheet("""
            QGroupBox {
                font-size: 26px; font-weight: bold; color: #2563eb;
                border: 2px solid #cbd5e1; border-radius: 10px;
                background-color: #ffffff;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            QLineEdit, QComboBox {
                border: 1px solid #cbd5e1; border-radius: 4px;
                padding: 6px; background-color: white; color: #0f172a;
                font-size: 24px;
            }
            QLineEdit:disabled, QComboBox:disabled {
                background-color: #f1f5f9; color: #94a3b8;
            }
        """)

        grid = QGridLayout(self.form_group)
        grid.setSpacing(12)
        grid.setContentsMargins(20, 20, 20, 20)

        self.fields = {}

        def add_grid_field(row, col, label_text, field_key, field_type, col_span=1):
            """Helper para agregar un campo al grid. col_span permite ocupar 2 columnas."""
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")

            if field_type == "combo":
                widget = QComboBox()
                widget.setStyleSheet("font-size: 24px;")
                if field_key == "gender":
                    widget.addItems(["", "Masculino (M)", "Femenino (F)"])
                elif field_key == "access_type":
                    widget.addItems(["Fístula AV (FAV)", "Catéter Perm-Cath", "Catéter Temporal (Mahurkar)", "Injerto Vascular (PTFE)"])
                elif field_key == "blood_type":
                    widget.addItems(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-", "No especificado"])
            else:
                widget = QLineEdit()
                widget.setStyleSheet("font-size: 24px;")
                widget.setReadOnly(True)
                if field_type == "numeric":
                    if field_key == "age":
                        widget.setValidator(QIntValidator(18, 100))
                    elif field_key == "height_cm":
                        widget.setValidator(QDoubleValidator(100.0, 250.0, 1))
                    elif field_key == "dry_weight_kg":
                        widget.setValidator(QDoubleValidator(30.0, 150.0, 1))
                    elif field_key == "pre_weight_kg":
                        widget.setValidator(QDoubleValidator(30.0, 200.0, 1))
                
                widget.mousePressEvent = lambda e, k=field_key, w=widget, ft=field_type: \
                    self.open_touch_input(k, w, mode='numeric' if ft == 'numeric' else 'text')

            self.fields[field_key] = widget
            grid.addWidget(label, row, col)
            grid.addWidget(widget, row, col + 1, 1, col_span)

        # Row 0: ID, N.S.S., Género, Edad
        add_grid_field(0, 0, "ID", "patient_id", "text")
        add_grid_field(0, 2, "N.S.S.", "patient_nss", "text")
        
        # Row 0, col 4-5: género
        label_g = QLabel("Género")
        label_g.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_g = QComboBox()
        widget_g.setStyleSheet("font-size: 24px;")
        widget_g.addItems(["", "Masculino (M)", "Femenino (F)"])
        self.fields["gender"] = widget_g
        grid.addWidget(label_g, 0, 4)
        grid.addWidget(widget_g, 0, 5)
        
        # Edad
        label_a = QLabel("Edad")
        label_a.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_a = QLineEdit()
        widget_a.setStyleSheet("font-size: 24px;")
        widget_a.setReadOnly(True)
        widget_a.setValidator(QIntValidator(18, 100))
        widget_a.mousePressEvent = lambda e, k="age", w=widget_a: \
            self.open_touch_input(k, w, mode='numeric')
        self.fields["age"] = widget_a
        grid.addWidget(label_a, 0, 6)
        grid.addWidget(widget_a, 0, 7)

        # Row 1: Nombre (2 cols), Altura, Peso seco
        label_n = QLabel("Nombre")
        label_n.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_n = QLineEdit()
        widget_n.setStyleSheet("font-size: 24px;")
        widget_n.setReadOnly(True)
        widget_n.mousePressEvent = lambda e, k="patient_name", w=widget_n: \
            self.open_touch_input(k, w, mode='text')
        self.fields["patient_name"] = widget_n
        grid.addWidget(label_n, 1, 0)
        grid.addWidget(widget_n, 1, 1, 1, 3)  # spans 2 columns

        label_h = QLabel("Altura (cm)")
        label_h.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_h = QLineEdit()
        widget_h.setStyleSheet("font-size: 24px;")
        widget_h.setReadOnly(True)
        widget_h.setValidator(QDoubleValidator(100.0, 250.0, 1))
        widget_h.mousePressEvent = lambda e, k="height_cm", w=widget_h: \
            self.open_touch_input(k, w, mode='numeric')
        self.fields["height_cm"] = widget_h
        grid.addWidget(label_h, 1, 4)
        grid.addWidget(widget_h, 1, 5)

        label_ds = QLabel("Peso seco (kg)")
        label_ds.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_ds = QLineEdit()
        widget_ds.setStyleSheet("font-size: 24px;")
        widget_ds.setReadOnly(True)
        widget_ds.setValidator(QDoubleValidator(30.0, 150.0, 1))
        widget_ds.mousePressEvent = lambda e, k="dry_weight_kg", w=widget_ds: \
            self.open_touch_input(k, w, mode='numeric')
        self.fields["dry_weight_kg"] = widget_ds
        grid.addWidget(label_ds, 1, 6)
        grid.addWidget(widget_ds, 1, 7)

        # Row 2: Peso pre, Acceso, Grupo, Filtro
        label_pp = QLabel("Peso pre (kg)")
        label_pp.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_pp = QLineEdit()
        widget_pp.setStyleSheet("font-size: 24px;")
        widget_pp.setReadOnly(True)
        widget_pp.setValidator(QDoubleValidator(30.0, 200.0, 1))
        widget_pp.mousePressEvent = lambda e, k="pre_weight_kg", w=widget_pp: \
            self.open_touch_input(k, w, mode='numeric')
        self.fields["pre_weight_kg"] = widget_pp
        grid.addWidget(label_pp, 2, 0)
        grid.addWidget(widget_pp, 2, 1)

        label_acc = QLabel("Acceso")
        label_acc.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_acc = QComboBox()
        widget_acc.setStyleSheet("font-size: 24px;")
        widget_acc.addItems(["Fístula AV (FAV)", "Catéter Perm-Cath", "Catéter Temporal (Mahurkar)", "Injerto Vascular (PTFE)"])
        self.fields["access_type"] = widget_acc
        grid.addWidget(label_acc, 2, 2)
        grid.addWidget(widget_acc, 2, 3)

        label_bg = QLabel("Grupo")
        label_bg.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_bg = QComboBox()
        widget_bg.setStyleSheet("font-size: 24px;")
        widget_bg.addItems(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-", "No especificado"])
        self.fields["blood_type"] = widget_bg
        grid.addWidget(label_bg, 2, 4)
        grid.addWidget(widget_bg, 2, 5)

        label_f = QLabel("Filtro")
        label_f.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_f = QLineEdit()
        widget_f.setStyleSheet("font-size: 24px;")
        widget_f.setReadOnly(True)
        widget_f.mousePressEvent = lambda e, k="dialyzer", w=widget_f: \
            self.open_touch_input(k, w, mode='text')
        self.fields["dialyzer"] = widget_f
        grid.addWidget(label_f, 2, 6)
        grid.addWidget(widget_f, 2, 7)

        # Row 3: Diagnóstico (2 cols), Médico (2 cols)
        label_diag = QLabel("Diagnóstico")
        label_diag.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_diag = QLineEdit()
        widget_diag.setStyleSheet("font-size: 24px;")
        widget_diag.setReadOnly(True)
        widget_diag.mousePressEvent = lambda e, k="diagnosis", w=widget_diag: \
            self.open_touch_input(k, w, mode='text')
        self.fields["diagnosis"] = widget_diag
        grid.addWidget(label_diag, 3, 0)
        grid.addWidget(widget_diag, 3, 1, 1, 3)  # spans 2 columns

        label_phys = QLabel("Médico")
        label_phys.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_phys = QLineEdit()
        widget_phys.setStyleSheet("font-size: 24px;")
        widget_phys.setReadOnly(True)
        widget_phys.mousePressEvent = lambda e, k="physician", w=widget_phys: \
            self.open_touch_input(k, w, mode='text')
        self.fields["physician"] = widget_phys
        grid.addWidget(label_phys, 3, 4)
        grid.addWidget(widget_phys, 3, 5, 1, 3)  # spans 2 columns

        # Row 4: Alergias (4 cols)
        label_allerg = QLabel("Alergias")
        label_allerg.setStyleSheet("font-size: 24px; color: #475569; font-weight: 600;")
        widget_allerg = QLineEdit()
        widget_allerg.setStyleSheet("font-size: 24px;")
        widget_allerg.setReadOnly(True)
        widget_allerg.mousePressEvent = lambda e, k="allergies", w=widget_allerg: \
            self.open_touch_input(k, w, mode='text')
        self.fields["allergies"] = widget_allerg
        grid.addWidget(label_allerg, 4, 0)
        grid.addWidget(widget_allerg, 4, 1, 1, 7)  # spans 4 columns

        main_layout.addWidget(self.form_group)
        self.form_group.setEnabled(False)

        # 4. Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("Guardar y Seleccionar")
        self.btn_save.setFixedSize(320, 52)
        self.btn_save.setStyleSheet("""
            QPushButton {
                font-size: 16px; background: #2563eb; color: white;
                font-weight: bold; border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:pressed { background: #1e40af; }
            QPushButton:disabled { background: #94a3b8; color: #cbd5e1; }
        """)
        self.btn_save.clicked.connect(self._save_patient)
        self.btn_save.setEnabled(False)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        main_layout.addStretch()

    def open_touch_input(self, field_key: str, input_widget, mode: str = 'numeric'):
        """Abre el diálogo táctil adecuado según el modo."""
        current_text = input_widget.text().strip() if hasattr(input_widget, 'text') else ""

        title_map = {
            "patient_id": "ID del paciente",
            "patient_nss": "N.S.S.",
            "patient_name": "Nombre completo",
            "age": "Edad (años)",
            "height_cm": "Altura en cm",
            "dry_weight_kg": "Peso seco (kg)",
            "pre_weight_kg": "Peso actual pre-diálisis (kg)",
            "diagnosis": "Diagnóstico",
            "physician": "Médico",
            "allergies": "Alergias",
            "dialyzer": "Filtro",
        }
        title = title_map.get(field_key, "Ingrese valor")

        if mode == 'numeric':
            dialog = NumpadDialog(self, title=title)
        else:
            dialog = KeyboardDialog(self, initial_text=current_text, title=title)

        if dialog.exec():
            new_raw_value = dialog.get_value()
            new_value_as_str = str(new_raw_value)
            
            validator = input_widget.validator()
            if validator:
                state, _, _ = validator.validate(new_value_as_str, 0)
                if state == QDoubleValidator.Acceptable or state == QIntValidator.Acceptable:
                    input_widget.setText(new_value_as_str)
                else:
                    self.show_info_message(f"El valor '{new_value_as_str}' no es válido.", 2000)
                    return
            else:
                input_widget.setText(new_value_as_str)

    def _delete_selected_patient(self):
        """Elimina el paciente seleccionado."""
        current_item = self.patient_list.currentItem()
        if not current_item:
            self.show_warning_message("Seleccione un paciente para eliminar.", 2000)
            return

        pid = current_item.text().split(" - ")[0]
        patient_name = self.patients_db.get(pid, {}).get("patient_name", pid)

        message = f"¿Estás seguro de eliminar al paciente?\n\nID: {pid}\nNombre: {patient_name}\n\nEsta acción no se puede deshacer."

        if self._confirm_message(message, "Sí, Eliminar", "Cancelar"):
            if pid in self.patients_db:
                del self.patients_db[pid]
                self._save_patients_to_file()
                self._refresh_patient_list()

                self.form_group.setEnabled(False)
                self.btn_save.setEnabled(False)
                self.btn_delete.setEnabled(False)
                self._clear_form()

                self.show_success_message(f"Paciente {pid} eliminado correctamente.", 2000)
                logger.info(f"Paciente eliminado: {pid} - {patient_name}")

    def _confirm_message(self, message: str, accept_text: str, cancel_text: str) -> bool:
        """Muestra un mensaje de confirmación flotante."""
        dialog = FloatingConfirmDialog(self)
        return dialog.show_confirm(message, accept_text=accept_text, cancel_text=cancel_text)

    def _refresh_patient_list(self):
        self.patient_list.clear()
        for pid, data in self.patients_db.items():
            access = data.get('patient_access_type', '')
            access_str = f" ({access})" if access else ""
            self.patient_list.addItem(f"{pid} - {data.get('patient_name', 'Sin nombre')}{access_str}")

    def _load_selected_patient(self, item):
        pid = item.text().split(" - ")[0]
        patient = self.patients_db.get(pid)
        if patient:
            self.selected_patient_id = pid
            self._populate_form(patient)
            self.form_group.setEnabled(True)
            self.btn_save.setEnabled(True)
            self.btn_delete.setEnabled(True)

    def _open_new_patient_dialog(self):
        dialog = KeyboardDialog(self, title="Ingrese ID del nuevo paciente")
        if dialog.exec():
            pid = dialog.get_value().strip().upper()
            if not pid:
                self.show_warning_message("Intento de crear paciente con ID vacío.")
                return
            if pid in self.patients_db:
                self.show_warning_message(f"El ID '{pid}' ya existe.", 2000)
                return

            new_patient = {
                "patient_id": pid,
                "patient_name": "",
                "patient_gender": 0,
                "patient_age": 0,
                "patient_height_cm": 0.0,
                "patient_dry_weight_kg": 0.0,
                "patient_pre_weight_kg": 0.0,
                "patient_nss": "",
                "patient_access_type": "Fístula AV (FAV)",
                "patient_blood_type": "O+",
                "patient_dialyzer": "F8HPS (1.8 m²)",
                "patient_diagnosis": "ERC Estadio 5",
                "patient_physician": "",
                "patient_allergies": "Ninguna conocida",
                "uf_goal_liters": 0.0,
            }
            self.patients_db[pid] = new_patient
            self._save_patients_to_file()
            self._refresh_patient_list()

            # Seleccionar el nuevo paciente
            for i in range(self.patient_list.count()):
                if pid in self.patient_list.item(i).text():
                    self.patient_list.setCurrentItem(self.patient_list.item(i))
                    self._load_selected_patient(self.patient_list.item(i))
                    break

    def _populate_form(self, patient: dict):
        """Rellena el formulario con datos del paciente."""
        field_mapping = {
            "patient_id": "patient_id",
            "patient_nss": "patient_nss",
            "gender": "patient_gender",
            "age": "patient_age",
            "patient_name": "patient_name",
            "height_cm": "patient_height_cm",
            "dry_weight_kg": "patient_dry_weight_kg",
            "pre_weight_kg": "patient_pre_weight_kg",
            "access_type": "patient_access_type",
            "blood_type": "patient_blood_type",
            "dialyzer": "patient_dialyzer",
            "diagnosis": "patient_diagnosis",
            "physician": "patient_physician",
            "allergies": "patient_allergies",
        }

        for field_key, patient_key in field_mapping.items():
            if field_key not in self.fields:
                continue

            widget = self.fields[field_key]
            value = patient.get(patient_key)

            if isinstance(widget, QComboBox):
                if field_key == "gender":
                    if value == 1:
                        widget.setCurrentIndex(1)
                    elif value == 2:
                        widget.setCurrentIndex(2)
                    else:
                        widget.setCurrentIndex(0)
                elif field_key == "blood_type":
                    widget.setCurrentText(str(value) if value else "O+")
                elif field_key == "access_type":
                    widget.setCurrentText(str(value) if value else "Fístula AV (FAV)")
            else:
                widget.setText(str(value) if value else "")

    def _clear_form(self):
        """Limpia todos los campos del formulario."""
        for widget in self.fields.values():
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.setText("")

    def _save_patient(self):
        """Guarda el paciente actual."""
        if not self.selected_patient_id:
            self.show_warning_message("No hay paciente seleccionado.", 2000)
            return

        data = {}
        field_mapping = {
            "patient_id": "patient_id",
            "patient_nss": "patient_nss",
            "gender": "patient_gender",
            "age": "patient_age",
            "patient_name": "patient_name",
            "height_cm": "patient_height_cm",
            "dry_weight_kg": "patient_dry_weight_kg",
            "pre_weight_kg": "patient_pre_weight_kg",
            "access_type": "patient_access_type",
            "blood_type": "patient_blood_type",
            "dialyzer": "patient_dialyzer",
            "diagnosis": "patient_diagnosis",
            "physician": "patient_physician",
            "allergies": "patient_allergies",
        }

        for field_key, patient_key in field_mapping.items():
            if field_key not in self.fields:
                continue

            widget = self.fields[field_key]

            if isinstance(widget, QComboBox):
                if field_key == "gender":
                    idx = widget.currentIndex()
                    data[patient_key] = 1 if idx == 1 else 2 if idx == 2 else 0
                else:
                    data[patient_key] = widget.currentText()
            else:
                text = widget.text().strip()
                if field_key in ["age"]:
                    try:
                        data[patient_key] = int(text) if text else 0
                    except ValueError:
                        data[patient_key] = 0
                elif field_key in ["height_cm", "dry_weight_kg", "pre_weight_kg"]:
                    try:
                        data[patient_key] = float(text) if text else 0.0
                    except ValueError:
                        data[patient_key] = 0.0
                else:
                    data[patient_key] = text

        # Validations
        if not data.get("patient_id"):
            self.show_warning_message("ID del paciente es obligatorio.", 2000)
            return
        if not data.get("patient_name"):
            self.show_warning_message("El nombre es obligatorio.", 2000)
            return
        if data.get("patient_gender") not in [1, 2]:
            self.show_warning_message("Seleccione el género.", 2000)
            return

        # Calculate UF goal
        pre_weight = data.get("patient_pre_weight_kg", 0.0)
        dry_weight = data.get("patient_dry_weight_kg", 0.0)
        uf_goal = max(0.0, pre_weight - dry_weight)
        data["uf_goal_liters"] = round(uf_goal, 2)

        # Merge with existing patient data
        self.patients_db[self.selected_patient_id].update(data)
        self._save_patients_to_file()

        # Save to current_values
        for key, value in data.items():
            self.current_values[key] = value
        self.current_values["uf_goal_liters"] = data["uf_goal_liters"]

        self._refresh_patient_list()
        self.show_success_message(f"Paciente guardado. UF Goal: {data['uf_goal_liters']:.2f} L", 2000)

        if hasattr(self.parent_window, 'dialysis_screen'):
            self.parent_window.dialysis_screen.update_values(self.current_values)

    def show_floating_message(self, text: str, timeout_ms: int = 3800):
        """Mensaje genérico flotante."""
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_floating_message(text, timeout_ms)

    def show_success_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_success_message(text, timeout_ms)

    def show_info_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_info_message(text, timeout_ms)

    def show_warning_message(self, text: str, timeout_ms: int = 2000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_warning_message(text, timeout_ms)

    def show_error_message(self, text: str, timeout_ms: int = 3000):
        if not hasattr(self, '_floating_msg') or self._floating_msg is None:
            self._floating_msg = FloatingMessage(self)
        self._floating_msg.show_error_message(text, timeout_ms)
