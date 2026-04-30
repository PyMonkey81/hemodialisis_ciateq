# gui/therapy/patient_config_screen.py

"""
Módulo para la configuración y gestión de perfiles de paciente.

Este módulo define la clase `PatientConfigScreen`, una interfaz de usuario
completa para ingresar, seleccionar y modificar los datos demográficos y clínicos
de los pacientes que serán tratados con la máquina de hemodiálisis. Está diseñada
específicamente para pantallas táctiles, integrando teclados numéricos y alfabéticos
virtuales.

Características clave:
----------------------
- **Base de Datos en Memoria:** Mantiene una pequeña base de datos de pacientes de prueba
  en memoria (`self.patients_db`) para demostración y facilidad de uso.
- **Interacción Táctil:** Todos los campos de entrada de datos se gestionan mediante
  diálogos modales de teclado numérico (`NumpadDialog`) o teclado QWERTY (`KeyboardDialog`),
  optimizados para interfaces táctiles.
- **Selección y Creación de Pacientes:** Permite seleccionar un paciente existente
  de una lista o crear un nuevo perfil de paciente.
- **Validación de Datos:** Incluye validaciones en tiempo real y al guardar,
  asegurando que los datos ingresados cumplan con los formatos y rangos esperados
  (ej. rangos de edad, peso, etc., posiblemente usando `VARIABLES` del sistema).
- **Cálculo de UF Objetivo:** Calcula automáticamente el objetivo de ultrafiltración
  basado en la diferencia entre el peso pre-diálisis y el peso seco del paciente.
- **Integración con el Sistema:** Actualiza el diccionario `current_values` del
  `HemodialysisHMI` principal con los datos del paciente seleccionado/modificado,
  haciéndolos disponibles para otras pantallas y la lógica de control.
- **Diseño Responsive:** Utiliza un `QScrollArea` para asegurar que todo el
  contenido sea accesible en diferentes resoluciones de pantalla, especialmente
  útil si hay muchos campos o la pantalla es pequeña.

Clase principal:
----------------
- `PatientConfigScreen`: Widget principal que contiene la lógica y la interfaz
  para la gestión de pacientes.

Dependencias:
-------------
- `PySide6`: Para la construcción de la interfaz gráfica de usuario.
- `gui.components.numpad_modal.NumpadDialog`: Diálogo para la entrada de números.
- `gui.components.keyboard_modal.KeyboardDialog`: Diálogo para la entrada de texto.
- `gui.components.ui_components.show_dark_message`: Función para mostrar mensajes de alerta/información.
- `core.variables_map.VARIABLES`: usado para definir rangos de validación
  y mapeo de datos con el controlador.
"""


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFormLayout,
    QGroupBox, QListWidget, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from gui.components.numpad_modal import NumpadDialog
from gui.components.keyboard_modal import KeyboardDialog
from gui.components.ui_components import show_dark_message
from core.variables_map import VARIABLES


class PatientConfigScreen(QWidget):
    """
    Pantalla de configuración de paciente con entrada táctil.
    - Teclado QWERTY para texto (ID, nombre)
    - Numpad para valores numéricos
    - Mini DB en memoria con pacientes de prueba
    Todo el contenido de la pantalla es desplazable (scrollable).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = parent.current_values if parent else {}

        self.patients_db = {}
        self._load_test_patients()

        self.setFixedSize(1536, 726)
        self.setup_ui()

    def _load_test_patients(self):
        """Pacientes de prueba para demo"""
        test_patients = [
            {
                "patient_id": "P001",
                "patient_name": "Juan Pérez López",
                "patient_gender": 1,  # 1 = Hombre
                "patient_age": 58,
                "patient_height_cm": 170.0,
                "patient_dry_weight_kg": 68.5,
                "patient_pre_weight_kg": 73.2,
                "uf_goal_liters": 4.7,  # Calculado de prueba
            },
            {
                "patient_id": "P002",
                "patient_name": "María González Ramírez",
                "patient_gender": 2,  # 2 = Mujer
                "patient_age": 65,
                "patient_height_cm": 158.0,
                "patient_dry_weight_kg": 55.0,
                "patient_pre_weight_kg": 59.8,
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
                "uf_goal_liters": 5.5,
            }
        ]
        for p in test_patients:
            self.patients_db[p["patient_id"]] = p

    def setup_ui(self):
        # Estilos para la ventana contenedora (el QWidget principal)

        self.setStyleSheet("""
            background-color: #fcfcfc; /* Nuevo color de fondo */
            border-radius: 15px;
        """)

        # 1. Layout principal de la pantalla, que contendrá el QScrollArea
        # Margenes a 0 porque el QScrollArea ocupará todo
        main_window_layout = QVBoxLayout(self)
        main_window_layout.setContentsMargins(0, 0, 0, 0)
        main_window_layout.setSpacing(0)

        # 2. Creamos el QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # IMPORTANTE: Permite que el widget interno se redimensione
        # scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #e0e0e5;
                width: 34px;
                margin: 0px 0px 0px 0px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical {
                background: #8a8a9c;
                min-height: 60px;
                border-radius: 14px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b6b7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 3. Creamos un QWidget contenedor para todo el contenido desplazable
        content_widget = QWidget()
        # Creamos un QVBoxLayout para este widget de contenido
        content_layout = QVBoxLayout(content_widget)
        # Aquí van los márgenes y espaciados de todo el contenido
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(20)
        
        # Título
        title = QLabel("Configuración del Paciente")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #1e40af;")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        # Selector de paciente
        selector_group = QGroupBox("Seleccionar o crear paciente")
        # Estilo para el QGroupBox
        selector_group.setStyleSheet("""
            QGroupBox {
                font-size: 26px;
                font-weight: bold;
                color: #1e40af;
                border: 2px solid #a78bfa;
                border-radius: 10px;
                margin-top: 10px; /* Espacio para el título */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Posiciona el título en el centro superior */
                padding: 0 10px;
                background-color: #e0e7ff; /* Fondo para el título */
                border-radius: 5px;
            }
        """)
        selector_layout = QVBoxLayout()
        selector_layout.setContentsMargins(20, 20, 20, 20)
        selector_layout.setSpacing(15)

        self.patient_list = QListWidget()
        self.patient_list.setStyleSheet("font-size: 22px; padding: 5px; border-radius: 8px; background-color: #fcfcfc;")
        self.patient_list.setMinimumHeight(200) # Una altura mínima para que se vea bien la lista
        self.patient_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._refresh_patient_list()
        self.patient_list.itemClicked.connect(self._load_selected_patient)
        selector_layout.addWidget(self.patient_list)

        btn_new = QPushButton("Nuevo Paciente")
        btn_new.setFixedHeight(60)
        btn_new.setStyleSheet("""
            QPushButton {
                font-size: 26px;
                background: #10b981;
                color: white;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """)
        btn_new.clicked.connect(self._open_new_patient_dialog)
        selector_layout.addWidget(btn_new)

        selector_group.setLayout(selector_layout)
        content_layout.addWidget(selector_group) # Añadimos al layout de contenido

        # Formulario de datos del paciente
        self.form_group = QGroupBox("Datos del paciente")
        # Estilo para el QGroupBox del formulario
        self.form_group.setStyleSheet("""
            QGroupBox {
                font-size: 26px;
                font-weight: bold;
                color: #1e40af;
                border: 2px solid #a78bfa;
                border-radius: 10px;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #e0e7ff;
                border-radius: 5px;
            }
            QLineEdit, QComboBox {
                border: 1px solid #9ca3af;
                border-radius: 5px;
                padding: 8px;
                background-color: #fcfcfc;
            }
        """)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignLeft)
        self.form_layout.setSpacing(12)

        self.fields = {}

        def add_field(label_text, key, default="", validator=None, input_mode='numeric'):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 22px; color: #1e293b;")
            if key == "gender":
                widget = QComboBox()
                widget.addItems(["", "Masculino (M)", "Femenino (F)"])
                widget.setStyleSheet("font-size: 22px; padding: 8px;")
            else:
                widget = QLineEdit(default)
                widget.setStyleSheet("font-size: 22px; padding: 8px;")
                if validator:
                    widget.setValidator(validator)
                # Asegurar que el QLineEdit no sea editable por teclado físico
                widget.setReadOnly(True) 

            self.form_layout.addRow(label, widget)
            self.fields[key] = widget

            # Conectar clic para abrir input táctil (excepto gender)
            if key != "gender":
                widget.mousePressEvent = lambda e, k=key, w=widget, m=input_mode: \
                    self.open_touch_input(k, w, mode=m)

        add_field("ID Paciente:", "patient_id", input_mode='text')
        add_field("Nombre completo:", "patient_name", input_mode='text')
        add_field("Género:", "gender")
        add_field("Edad (años):", "age", validator=QIntValidator(18, 100))
        add_field("Altura (cm):", "height_cm", validator=QDoubleValidator(100.0, 250.0, 1))
        add_field("Peso seco (kg):", "dry_weight_kg", validator=QDoubleValidator(30.0, 150.0, 1))
        add_field("Peso pre-diálisis (kg):", "pre_dialysis_weight_kg", validator=QDoubleValidator(30.0, 200.0, 1)) # Aumentado max weight

        self.form_group.setLayout(self.form_layout)
        self.form_group.hide() # Inicialmente oculto
        content_layout.addWidget(self.form_group) # Añadimos al layout de contenido

        # Botón guardar y stretch al final
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar y Seleccionar")
        self.btn_save.setFixedSize(320, 70)
        self.btn_save.setStyleSheet("""
            QPushButton {
                font-size: 26px;
                background: #3b82f6;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:pressed { background: #1d4ed8; }
            QPushButton:disabled { background: #94a3b8; }
        """)
        self.btn_save.clicked.connect(self._save_patient)
        self.btn_save.setEnabled(False) # Deshabilitado hasta que se seleccione/cree un paciente
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        content_layout.addLayout(btn_layout)
        content_layout.addStretch() # Empuja el contenido hacia arriba

        # 4. Establecer el widget de contenido en el QScrollArea
        scroll_area.setWidget(content_widget)
        
        # 5. Añadir el QScrollArea al layout principal de la ventana
        main_window_layout.addWidget(scroll_area)

    def open_touch_input(self, field_key: str, input_widget, mode: str = 'numeric'):
        """
        Abre el diálogo táctil adecuado según el modo.
        Actualiza widget y current_values al aceptar.

        """


        current_text = input_widget.text().strip() if hasattr(input_widget, 'text') else ""

        title_map = {
            "patient_id": "ID del paciente",
            "patient_name": "Nombre completo",
            "age": "Edad (años)",
            "height_cm": "Altura en cm",
            "dry_weight_kg": "Peso seco (kg)",
            "pre_dialysis_weight_kg": "Peso actual pre-diálisis (kg)"
        }
        title = title_map.get(field_key, "Ingrese valor")

        if mode == 'numeric':
            dialog = NumpadDialog(self, initial_value=current_text, title=title)
        else: # mode == 'text'
            dialog = KeyboardDialog(self, initial_text=current_text, title=title)

        if dialog.exec(): # Si el usuario presiona "ACEPTAR"
            new_raw_value = dialog.get_value() # Esto puede ser float o str
            
            # --- Convertir a string para la validación y visualización en QLineEdit ---
            new_value_as_str = str(new_raw_value) 
            
            # Aplicar validación del QLineEdit
            validator = input_widget.validator()
            if validator:
                # El validate() espera una string, no un float
                state, _, _ = validator.validate(new_value_as_str, 0) 
                
                # Queremos que sea Acceptable, no solo Intermediate (que podría ser un '.' o un '-')
                if state == QDoubleValidator.Acceptable or state == QIntValidator.Acceptable:
                    input_widget.setText(new_value_as_str) # Actualiza el QLineEdit con la string válida
                else:
                    show_dark_message(self, "Valor Inválido", 
                                        f"El valor '{new_value_as_str}' no es válido para este campo o está incompleto.",
                                        icon=QMessageBox.warning)
                    
                    return # No actualizar si la validación falla
            else: # No hay validador, aceptar el texto directamente
                input_widget.setText(new_value_as_str) # Asegurarse de que sea string para QLineEdit

        
            patient_key = f"patient_{field_key}"
            if mode == 'numeric':
                try:
                    # Usamos el texto del widget, que ya está validado, y lo convertimos a float
                    self.current_values[patient_key] = float(input_widget.text()) 
                except ValueError:
                    # Esto debería ser raro si el validador ya pasó
                    self.current_values[patient_key] = 0.0 
            else:
                self.current_values[patient_key] = input_widget.text().strip()

            print(f"[PatientConfig] {patient_key} → {self.current_values.get(patient_key)}")

    def _refresh_patient_list(self):
        self.patient_list.clear()
        for pid, data in self.patients_db.items():
            self.patient_list.addItem(f"{pid} - {data.get('patient_name', 'Sin nombre')}")

    def _load_selected_patient(self, item):
        pid = item.text().split(" - ")[0]
        patient = self.patients_db.get(pid)
        if patient:
            self._populate_form(patient)
            self.form_group.show()
            self.btn_save.setEnabled(True)

    def _open_new_patient_dialog(self):

        dialog = KeyboardDialog(self, title="Ingrese ID del nuevo paciente")
        if dialog.exec():
            pid = dialog.get_value().strip().upper()
            if not pid:
                show_dark_message(self, "Error", "El ID no puede estar vacío.",icon=QMessageBox.warning)
                return
            if pid in self.patients_db:
                show_dark_message(self, "Error", f"El ID '{pid}' ya existe.",icon=QMessageBox.warning)
                return

            new_patient = {
                "patient_id": pid,
                "patient_name": "",
                "patient_gender": 0,
                "patient_age": 0,
                "patient_height_cm": 0.0,
                "patient_dry_weight_kg": 0.0,
                "patient_pre_weight_kg": 0.0,
                "uf_goal_liters": 0.0,
            }
            self.patients_db[pid] = new_patient
            self._refresh_patient_list()

            # Seleccionar automáticamente
            for i in range(self.patient_list.count()):
                if self.patient_list.item(i).text().startswith(pid):
                    self.patient_list.setCurrentRow(i)
                    self._load_selected_patient(self.patient_list.item(i))
                    break

    def _populate_form(self, patient):
        for key, widget in self.fields.items():
            if key == "gender":
                idx = 0
                g = patient.get("patient_gender", 0)  # clave real en la DB
                if g == 1: idx = 1
                elif g == 2: idx = 2
                widget.setCurrentIndex(idx)
            else:
                # Usamos la clave real que está en el diccionario patient
                real_key = {
                    "patient_id": "patient_id",
                    "patient_name": "patient_name",
                    "age": "patient_age",
                    "height_cm": "patient_height_cm",
                    "dry_weight_kg": "patient_dry_weight_kg",
                    "pre_dialysis_weight_kg": "patient_pre_weight_kg",
                }.get(key, key)  # fallback

                value = patient.get(real_key)
                widget.setText(str(value) if value is not None else "")

    def _save_patient(self):
        data = {}              
        # Mapeo de campos del formulario a claves del mapa VARIABLES (0x08)
        field_to_tag = {
            "patient_id": "patient_id",
            "patient_name": "patient_name",
            "gender": "patient_gender",
            "age": "patient_age",
            "height_cm": "patient_height_cm",
            "dry_weight_kg": "patient_dry_weight_kg",
            "pre_dialysis_weight_kg": "patient_pre_weight_kg",
        }

        for field_key, widget in self.fields.items():
            tag = field_to_tag.get(field_key)
            if not tag:
                continue  # Ignorar si no está mapeado

            if field_key == "gender":
                text = widget.currentText()
                data[tag] = 1 if "Masculino" in text else 2 if "Femenino" in text else 0
            else:
                text = widget.text().strip()
                if field_key == "age":
                    try:
                        data[tag] = int(text)
                    except ValueError:
                        data[tag] = 0
                elif field_key in ["height_cm", "dry_weight_kg", "pre_dialysis_weight_kg"]:
                    try:
                        data[tag] = float(text)
                    except ValueError:
                        data[tag] = 0.0
                else:
                    data[tag] = text

        # Validaciones
        if not data.get("patient_id"):
            show_dark_message(self, "Error", "ID del paciente es obligatorio.",icon=QMessageBox.warning)
            return
        if not data.get("patient_name"):
            show_dark_message(self, "Error", "El nombre es obligatorio.",icon=QMessageBox.warning)
            return
        if data.get("patient_gender") not in [1, 2]:
            show_dark_message(self, "Error", "Seleccione el género.",icon=QMessageBox.warning)
            return

        # Validaciones de rango usando el mapa
        patient_map = VARIABLES.get(0x08, {})
        for var in patient_map.values():
            tag = var["tag"]
            if tag in data:
                limites = var.get("limites")
                if limites and isinstance(limites, tuple):
                    min_val, max_val = limites
                    value = data[tag]
                    if isinstance(value, (int, float)) and not (min_val <= value <= max_val):
                        show_dark_message(
                            self,
                            "Error",
                            f"{var['label']} debe estar entre {min_val} y {max_val} {var['unit']}.",
                            icon=QMessageBox.Warning
                        )

        # Calcular UF goal
        pre_weight = data.get("patient_pre_weight_kg", 0.0)  # nota: clave corregida
        dry_weight = data.get("patient_dry_weight_kg", 0.0)
        uf_goal = max(0.0, pre_weight - dry_weight)
        data["uf_goal_liters"] = round(uf_goal, 2)

        # Guardar en DB
        self.patients_db[data["patient_id"]] = data

        # Guardar en current_values (claves exactas del mapa)
        for tag in ["patient_id", "patient_name", "patient_gender", "patient_age", 
                    "patient_height_cm", "patient_dry_weight_kg", 
                    "patient_pre_weight_kg", "uf_goal_liters"]:
            if tag in data:
                self.current_values[tag] = data[tag]
                print(f"[SAVE] Guardado {tag} = {data[tag]}")  # Debug

        self._refresh_patient_list()
        
        show_dark_message(
            self,
            "Guardado Exitoso",
            f"Paciente '{data.get('patient_name', '—')}' guardado correctamente."
            f"Objetivo de Ultrafiltración: {data['uf_goal_liters']:.2f} L",
            icon=QMessageBox.Information
            )


        if hasattr(self.parent_window, 'dialysis_screen'):
            self.parent_window.dialysis_screen.update_values(self.current_values)

    # def update_values(self, new_values: dict):
    #     """Esta pantalla solo ingresa datos, no monitorea en tiempo real. Solo mergea si llegan datos del paciente."""
    #     if not new_values:
    #         return
    #     self.current_values.update(new_values)


    #     print("[PatientConfig] current_values actualizado")    

    def _map_gender_to_int(self, value):
        """Convierte strings comunes de género a 1/2"""
        if isinstance(value, (int, float)):
            v = int(value)
            return v if v in (1, 2) else 0

        v = str(value).strip().upper()
        if v in ("M", "MASCULINO", "HOMBRE", "1"):
            return 1
        if v in ("F", "FEMENINO", "MUJER", "2"):
            return 2
        return 0
    
    def _queue_patient_writes_if_needed(self):
        """Ejemplo: preparar writes Modbus para campos rw=True"""
        writes = []

        if "patient_id" in self.values and self.values["patient_id"] != self.patient["id"]:
            writes.append((0x08, 0x00, self.patient["id"]))         

        if "patient_name" in self.values and self.values["patient_name"] != self.patient["name"]:
            writes.append((0x08, 0x01, self.patient["name"]))

        # Género: ya es int 1/2
        if self.patient["gender"] != 0:
            writes.append((0x08, 0x02, self.patient["gender"]))

        # UF goal 
        if abs(self.patient["uf_goal_liters"] - self.values.get("uf_goal_liters", 0.0)) > 0.01:
            writes.append((0x08, 0x07, self.patient["uf_goal_liters"]))

        if writes:
            print("[INFO] Pendientes de escritura a máquina:", writes)
