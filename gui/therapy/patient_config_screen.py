# gui/therapy/patient_config_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFormLayout,
    QGroupBox, QListWidget, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from gui.components.numpad_modal import NumpadDialog
from gui.components.keyboard_modal import KeyboardDialog


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

        # Mini base de datos en memoria
        self.patients_db = {}
        self._load_test_patients()

        # Establecemos un tamaño fijo para la ventana principal,
        # pero el contenido interior será desplazable si no cabe.
        self.setFixedSize(1536, 726)
        self.setup_ui()

    def _load_test_patients(self):
        """Pacientes de prueba para demo"""
        test_patients = [
            {
                "patient_id": "P001",
                "patient_name": "Juan Pérez López",
                "gender": "M",
                "age": 58,
                "height_cm": 170.0,
                "dry_weight_kg": 68.5,
                "pre_dialysis_weight_kg": 73.2,
            },
            {
                "patient_id": "P002",
                "patient_name": "María González Ramírez",
                "gender": "F",
                "age": 65,
                "height_cm": 158.0,
                "dry_weight_kg": 55.0,
                "pre_dialysis_weight_kg": 59.8,
            },
            {
                "patient_id": "P003",
                "patient_name": "Carlos Ramírez Torres",
                "gender": "M",
                "age": 42,
                "height_cm": 175.0,
                "dry_weight_kg": 82.0,
                "pre_dialysis_weight_kg": 87.5,
            }
        ]
        for p in test_patients:
            self.patients_db[p["patient_id"]] = p

    def setup_ui(self):
        # Estilos para la ventana contenedora (el QWidget principal)
        # self.setStyleSheet("""
        #     background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        #                                stop:0 #e0e7ff, stop:1 #c7d2fe);
        #     border-radius: 15px;
        # """)
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
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # 3. Creamos un QWidget contenedor para todo el contenido desplazable
        content_widget = QWidget()
        # Creamos un QVBoxLayout para este widget de contenido
        content_layout = QVBoxLayout(content_widget)
        # Aquí van los márgenes y espaciados de todo el contenido
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(20)
        
        # --- AHORA AÑADIMOS TODOS LOS COMPONENTES DE LA UI A 'content_layout' ---

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
                    QMessageBox.warning(self, "Valor Inválido", 
                                        f"El valor '{new_value_as_str}' no es válido para este campo o está incompleto.")
                    return # No actualizar si la validación falla
            else: # No hay validador, aceptar el texto directamente
                input_widget.setText(new_value_as_str) # Asegurarse de que sea string para QLineEdit

            # --- Guardar en current_values (después de la validación exitosa y de actualizar el widget) ---
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

    # def open_touch_input(self, field_key: str, input_widget, mode: str = 'numeric'):
    #     """
    #     Abre el diálogo táctil adecuado según el modo.
    #     Actualiza widget y current_values al aceptar.
    #     """
    #     current_text = input_widget.text().strip() if hasattr(input_widget, 'text') else ""

    #     title_map = {
    #         "patient_id": "ID del paciente",
    #         "patient_name": "Nombre completo",
    #         "age": "Edad (años)",
    #         "height_cm": "Altura en cm",
    #         "dry_weight_kg": "Peso seco (kg)",
    #         "pre_dialysis_weight_kg": "Peso actual pre-diálisis (kg)"
    #     }
    #     title = title_map.get(field_key, "Ingrese valor")

    #     # Asegurarse de que el QLineEdit que estamos editando NO esté en readOnly
    #     # para que el validador funcione correctamente al salir del diálogo.
    #     # No, mejor no hacer esto, ya que queremos que solo se edite con el teclado virtual.
    #     # El validador se aplicará cuando se intente establecer el texto.

    #     if mode == 'numeric':
    #         dialog = NumpadDialog(self, initial_value=current_text, title=title)
    #     else: # mode == 'text'
    #         dialog = KeyboardDialog(self, initial_text=current_text, title=title)

    #     if dialog.exec(): # Si el usuario presiona "ACEPTAR"
    #         new_value = dialog.get_value()
    #         if new_value is not None:
    #             validator = input_widget.validator()
    #             if mode == 'numeric':
    #                 try:
    #                     formatted = f"{float(new_value):.1f}" if '.' in str(new_value) else str(int(new_value))
    #                 except: 
    #                     formatted = str(new_value)
    #                 input_widget.setText(formatted)
    #             else:
    #                 input_widget.setText(new_value)

            
    #         # Aplicar validación del QLineEdit
            
    #         # if validator:
    #         #     state, value, pos = validator.validate(new_value, 0)
    #         #     if state == QDoubleValidator.Acceptable or state == QIntValidator.Acceptable:
    #         #         input_widget.setText(new_value)
    #         #     else:
    #         #         QMessageBox.warning(self, "Valor Inválido", f"El valor '{new_value}' no es válido para este campo.")
    #         #         return # No actualizar si la validación falla
    #         # else: # No hay validador, aceptar el texto directamente
    #         #     input_widget.setText(new_value)

    #         # --- Actualizar current_values (lo que se pasa entre pantallas) ---
    #         patient_key = f"patient_{field_key}"
    #         if mode == 'numeric':
    #             try:
    #                 # Intentar convertir a float, si falla, dejar 0.0
    #                 self.current_values[patient_key] = float(input_widget.text()) 
    #             except ValueError:
    #                 self.current_values[patient_key] = 0.0
    #         else:
    #             self.current_values[patient_key] = input_widget.text().strip()

    #         print(f"[PatientConfig] {patient_key} → {self.current_values.get(patient_key)}")

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
        # Para nuevo paciente: primero pedir ID con teclado
        dialog = KeyboardDialog(self, title="Ingrese ID del nuevo paciente")
        if dialog.exec():
            pid = dialog.get_value().strip().upper()
            if not pid:
                QMessageBox.warning(self, "Error", "El ID no puede estar vacío.")
                return
            if pid in self.patients_db:
                QMessageBox.warning(self, "Error", f"El ID '{pid}' ya existe. Por favor, elija otro.")
                return

            new_patient = {
                "patient_id": pid,
                "patient_name": "",
                "gender": "",
                "age": 0,
                "height_cm": 0.0,
                "dry_weight_kg": 0.0,
                "pre_dialysis_weight_kg": 0.0,
            }
            self.patients_db[pid] = new_patient
            self._refresh_patient_list()

            # Seleccionar automáticamente el nuevo paciente en la lista
            for i in range(self.patient_list.count()):
                if self.patient_list.item(i).text().startswith(pid):
                    self.patient_list.setCurrentRow(i)
                    self._load_selected_patient(self.patient_list.item(i))
                    break

    def _populate_form(self, patient):
        for key, widget in self.fields.items():
            if key == "gender":
                idx = 0
                g = patient.get("gender", "")
                if g == "M": idx = 1
                elif g == "F": idx = 2
                widget.setCurrentIndex(idx)
            else:
                value = patient.get(key)
                widget.setText(str(value) if value is not None else "")

    def _save_patient(self):
        data = {}
        for key, widget in self.fields.items():
            if key == "gender":
                text = widget.currentText()
                data[key] = "M" if "Masculino" in text else "F" if "Femenino" in text else ""
            else:
                text = widget.text().strip()
                if key == "age":
                    data[key] = int(text) if text.isdigit() else 0
                elif key in ["height_cm", "dry_weight_kg", "pre_dialysis_weight_kg"]:
                    try:
                        data[key] = float(text)
                    except ValueError: # Capturar error si el float está mal
                        data[key] = 0.0
                else:
                    data[key] = text

        # Validaciones más robustas
        if not data.get("patient_id"):
            QMessageBox.warning(self, "Error", "ID del paciente es obligatorio.")
            return
        if not data.get("patient_name"):
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return
        if data.get("gender") not in ["M", "F"]:
            QMessageBox.warning(self, "Error", "Seleccione el género.")
            return
        if data.get("age", 0) < 18:
            QMessageBox.warning(self, "Error", "La edad debe ser al menos 18 años.")
            return
        if not (100.0 <= data.get("height_cm", 0.0) <= 250.0):
             QMessageBox.warning(self, "Error", "La altura debe estar entre 100 y 250 cm.")
             return
        if not (30.0 <= data.get("dry_weight_kg", 0.0) <= 150.0):
             QMessageBox.warning(self, "Error", "El peso seco debe estar entre 30 y 150 kg.")
             return
        if not (30.0 <= data.get("pre_dialysis_weight_kg", 0.0) <= 200.0):
             QMessageBox.warning(self, "Error", "El peso pre-diálisis debe estar entre 30 y 200 kg.")
             return


        # Calcular UF goal
        pre_weight = data.get("pre_dialysis_weight_kg", 0.0)
        dry_weight = data.get("dry_weight_kg", 0.0)
        uf_goal = max(0.0, pre_weight - dry_weight) # Asegurarse de que no sea negativo
        data["uf_goal_liters"] = round(uf_goal, 2) # Redondear a 2 decimales

        # Guardar en DB
        self.patients_db[data["patient_id"]] = data

        # Guardar en current_values (solo campos relevantes que se usarán en otras pantallas)
        key_map = {
            "patient_id": "patient_id",
            "patient_name": "patient_name",
            "gender": "patient_gender",
            "age": "patient_age",
            "height_cm": "patient_height_cm",
            "dry_weight_kg": "patient_dry_weight_kg",
            "pre_dialysis_weight_kg": "patient_pre_weight_kg",
            "uf_goal_liters": "uf_goal_liters"
        }
        for db_key, cv_key in key_map.items():
            if db_key in data:
                self.current_values[cv_key] = data[db_key]

        self._refresh_patient_list()
        QMessageBox.information(self, "Guardado",
                                f"Paciente '{data['patient_name']}' guardado correctamente.\n"
                                f"Objetivo de Ultrafiltración (UF goal): {data['uf_goal_liters']:.2f} L")

        # Opcional: actualizar otras pantallas si es necesario (ej. pantalla de diálisis)
        # Esto depende de cómo estés gestionando la navegación y el paso de datos
        # entre tus diferentes pantallas principales.
        if hasattr(self.parent_window, 'dialysis_screen'):
            self.parent_window.dialysis_screen.update_values(self.current_values)




# # gui/therapy/patient_config_screen.py

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
#     QComboBox, QPushButton, QMessageBox, QFormLayout,
#     QGroupBox, QListWidget, QSizePolicy, QScrollArea
# )
# from PySide6.QtCore import Qt 
# from PySide6.QtGui import QDoubleValidator, QIntValidator

# # Importa ambos diálogos
# from gui.components.numpad_modal import NumpadDialog
# from gui.components.keyboard_modal import KeyboardDialog


# class PatientConfigScreen(QWidget):
#     """
#     Pantalla de configuración de paciente con entrada táctil.
#     - Teclado QWERTY para texto (ID, nombre)
#     - Numpad para valores numéricos
#     - Mini DB en memoria con pacientes de prueba
#     """

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.current_values = parent.current_values if parent else {}

#         # Mini base de datos en memoria
#         self.patients_db = {}
#         self._load_test_patients()

#         self.setFixedSize(1536, 726)
#         self.setup_ui()

#     def _load_test_patients(self):
#         """Pacientes de prueba para demo"""
#         test_patients = [
#             {
#                 "patient_id": "P001",
#                 "patient_name": "Juan Pérez López",
#                 "gender": "M",
#                 "age": 58,
#                 "height_cm": 170.0,
#                 "dry_weight_kg": 68.5,
#                 "pre_dialysis_weight_kg": 73.2,
#             },
#             {
#                 "patient_id": "P002",
#                 "patient_name": "María González Ramírez",
#                 "gender": "F",
#                 "age": 65,
#                 "height_cm": 158.0,
#                 "dry_weight_kg": 55.0,
#                 "pre_dialysis_weight_kg": 59.8,
#             },
#             {
#                 "patient_id": "P003",
#                 "patient_name": "Carlos Ramírez Torres",
#                 "gender": "M",
#                 "age": 42,
#                 "height_cm": 175.0,
#                 "dry_weight_kg": 82.0,
#                 "pre_dialysis_weight_kg": 87.5,
#             }
#         ]
#         for p in test_patients:
#             self.patients_db[p["patient_id"]] = p

#     def setup_ui(self):
#         self.setStyleSheet("""
#             background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
#                                        stop:0 #e0e7ff, stop:1 #c7d2fe);
#             border-radius: 15px;
#         """)

#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(0, 0, 0, 0) 
#         # main_layout.setSpacing(20)

#         scroll_area = QScrollArea()
#         scroll_area.setWidgetResizable(True) # ¡Crucial!
#         scroll_area.setStyleSheet("border: none; background: transparent;")

#         content_widget = QWidget()
#         content_layout = QVBoxLayout(content_widget)
#         content_layout.setContentsMargins(40, 30, 40, 30)
#         content_layout.setSpacing(20)

#         # Título
#         title = QLabel("Configuración del Paciente")
#         title.setStyleSheet("font-size: 42px; font-weight: bold; color: #1e40af;")
#         title.setAlignment(Qt.AlignCenter)
#         content_layout.addWidget(title)

#         # Selector de paciente
#         selector_group = QGroupBox("Seleccionar o crear paciente")
#         selector_layout = QVBoxLayout()
#         # selector_layout.setContentsMargins(20, 20, 20, 20)  # ← Aumenta espacio interno
#         # selector_layout.setSpacing(15)
#         selector_group.setLayout(selector_layout)
#         content_layout.addWidget(selector_group)

#         self.patient_list = QListWidget()
#         self.patient_list.setStyleSheet("font-size: 22px;")  # ← Tamaño de fuente más grande
#         self.patient_list.setMinimumHeight(300)               # ← Altura mínima para que se vea bien
#         self.patient_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # ← IMPORTANTE
#         self._refresh_patient_list()
#         self.patient_list.itemClicked.connect(self._load_selected_patient)
#         selector_layout.addWidget(self.patient_list, stretch=1)  # ← stretch=1 para que se expanda

#         btn_new = QPushButton("Nuevo Paciente")
#         btn_new.setFixedHeight(60)
#         btn_new.setStyleSheet("font-size: 26px; background: #10b981; color: white;")
#         btn_new.clicked.connect(self._open_new_patient_dialog)
#         selector_layout.addWidget(btn_new)

#         selector_group.setLayout(selector_layout)

#         scroll_area = QScrollArea()
#         scroll_area.setWidget(selector_group)
#         scroll_area.setWidgetResizable(True)
#         scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
#         scroll_area.setMinimumHeight(240) # Ajustado altura

#         main_layout.addWidget(scroll_area)  # ← También stretch aquí  

#         selector_group.setLayout(selector_layout)
#         main_layout.addWidget(selector_group)

#         # Formulario
#         self.form_group = QGroupBox("Datos del paciente")
#         self.form_layout = QFormLayout()
#         self.form_layout.setLabelAlignment(Qt.AlignRight)
#         self.form_layout.setFormAlignment(Qt.AlignLeft)
#         self.form_layout.setSpacing(12)

#         self.fields = {}

        


#         def add_field(label_text, key, default="", validator=None, input_mode='numeric'):
#             label = QLabel(label_text)
#             label.setStyleSheet("font-size: 22px; color: #1e293b;")
#             if key == "gender":
#                 widget = QComboBox()
#                 widget.addItems(["", "Masculino (M)", "Femenino (F)"])
#                 widget.setStyleSheet("font-size: 22px; padding: 8px;")
#             else:
#                 widget = QLineEdit(default)
#                 widget.setStyleSheet("font-size: 22px; padding: 8px;")
#                 if validator:
#                     widget.setValidator(validator)

#             self.form_layout.addRow(label, widget)
#             self.fields[key] = widget

#             # Conectar clic para abrir input táctil (excepto gender)
#             if key != "gender":
#                 widget.mousePressEvent = lambda e, k=key, w=widget, m=input_mode: \
#                     self.open_touch_input(k, w, mode=m)

#         add_field("ID Paciente:", "patient_id", input_mode='text')
#         add_field("Nombre completo:", "patient_name", input_mode='text')
#         add_field("Género:", "gender")
#         add_field("Edad (años):", "age", validator=QIntValidator(18, 100))
#         add_field("Altura (cm):", "height_cm", validator=QDoubleValidator(100.0, 250.0, 1))
#         add_field("Peso seco (kg):", "dry_weight_kg", validator=QDoubleValidator(30.0, 150.0, 1))
#         add_field("Peso pre-diálisis (kg):", "pre_dialysis_weight_kg", validator=QDoubleValidator(30.0, 150.0, 1))

#         self.form_group.setLayout(self.form_layout)
#         self.form_group.hide()
#         main_layout.addWidget(self.form_group)

#         # Botón guardar
#         btn_layout = QHBoxLayout()
#         self.btn_save = QPushButton("Guardar y Seleccionar")
#         self.btn_save.setFixedSize(320, 70)
#         self.btn_save.setStyleSheet("font-size: 26px; background: #3b82f6; color: white; font-weight: bold;")
#         self.btn_save.clicked.connect(self._save_patient)
#         self.btn_save.setEnabled(False)
#         btn_layout.addStretch()
#         btn_layout.addWidget(self.btn_save)
#         main_layout.addLayout(btn_layout)
#         main_layout.addStretch()

#     def open_touch_input(self, field_key: str, input_widget, mode: str = 'numeric'):
#         """
#         Abre el diálogo táctil adecuado según el modo.
#         Actualiza widget y current_values al aceptar.
#         """
#         current_text = input_widget.text().strip() if hasattr(input_widget, 'text') else ""

#         title_map = {
#             "patient_id": "ID del paciente",
#             "patient_name": "Nombre completo",
#             "age": "Edad (años)",
#             "height_cm": "Altura en cm",
#             "dry_weight_kg": "Peso seco (kg)",
#             "pre_dialysis_weight_kg": "Peso actual pre-diálisis (kg)"
#         }
#         title = title_map.get(field_key, "Ingrese valor")

#         if mode == 'numeric':
#             dialog = NumpadDialog(self, initial_value=current_text, title=title)
#         else:
#             dialog = KeyboardDialog(self, initial_text=current_text, title=title)

#         if dialog.exec():
#             new_value = dialog.get_value()
#             if new_value is not None:

#                 # Actualizar widget visual
#                 if mode == 'numeric':
#                     try:
#                         formatted = f"{float(new_value):.1f}" if '.' in str(new_value) else str(int(new_value))
#                     except:
#                         formatted = str(new_value)
#                     input_widget.setText(formatted)
#                 else:
#                     input_widget.setText(new_value)

#                 # Guardar en current_values
#                 patient_key = f"patient_{field_key}"
#                 if mode == 'numeric':
#                     try:
#                         self.current_values[patient_key] = float(new_value)
#                     except:
#                         self.current_values[patient_key] = 0.0
#                 else:
#                     self.current_values[patient_key] = new_value.strip()

#                 print(f"[PatientConfig] {patient_key} → {self.current_values[patient_key]}")

#     def _refresh_patient_list(self):
#         self.patient_list.clear()
#         for pid, data in self.patients_db.items():
#             self.patient_list.addItem(f"{pid} - {data.get('patient_name', 'Sin nombre')}")

#     def _load_selected_patient(self, item):
#         pid = item.text().split(" - ")[0]
#         patient = self.patients_db.get(pid)
#         if patient:
#             self._populate_form(patient)
#             self.form_group.show()
#             self.btn_save.setEnabled(True)

#     def _open_new_patient_dialog(self):
#         # Para nuevo paciente: primero pedir ID con teclado
#         dialog = KeyboardDialog(self, title="Ingrese ID del nuevo paciente")
#         if dialog.exec():
#             pid = dialog.get_value().strip().upper()
#             if not pid or pid in self.patients_db:
#                 QMessageBox.warning(self, "Error", "ID inválido o ya existe.")
#                 return

#             new_patient = {
#                 "patient_id": pid,
#                 "patient_name": "",
#                 "gender": "",
#                 "age": 0,
#                 "height_cm": 0.0,
#                 "dry_weight_kg": 0.0,
#                 "pre_dialysis_weight_kg": 0.0,
#             }
#             self.patients_db[pid] = new_patient
#             self._refresh_patient_list()

#             # Seleccionar automáticamente
#             for i in range(self.patient_list.count()):
#                 if self.patient_list.item(i).text().startswith(pid):
#                     self.patient_list.setCurrentRow(i)
#                     self._load_selected_patient(self.patient_list.item(i))
#                     break

#     def _populate_form(self, patient):
#         for key, widget in self.fields.items():
#             if key == "gender":
#                 idx = 0
#                 g = patient.get("gender", "")
#                 if g == "M": idx = 1
#                 elif g == "F": idx = 2
#                 widget.setCurrentIndex(idx)
#             else:
#                 value = patient.get(key, "")
#                 widget.setText(str(value) if value else "")

#     def _save_patient(self):
#         data = {}
#         for key, widget in self.fields.items():
#             if key == "gender":
#                 text = widget.currentText()
#                 data[key] = "M" if "Masculino" in text else "F" if "Femenino" in text else ""
#             else:
#                 text = widget.text().strip()
#                 if key == "age":
#                     data[key] = int(text) if text.isdigit() else 0
#                 elif key in ["height_cm", "dry_weight_kg", "pre_dialysis_weight_kg"]:
#                     try:
#                         data[key] = float(text)
#                     except:
#                         data[key] = 0.0
#                 else:
#                     data[key] = text

#         # Validaciones mínimas
#         if not data.get("patient_id"):
#             QMessageBox.warning(self, "Error", "ID del paciente es obligatorio.")
#             return
#         if not data.get("patient_name"):
#             QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
#             return
#         if data.get("gender") not in ["M", "F"]:
#             QMessageBox.warning(self, "Error", "Seleccione el género.")
#             return
#         if data.get("dry_weight_kg", 0) <= 0:
#             QMessageBox.warning(self, "Error", "Peso seco debe ser mayor a 0.")
#             return

#         # Calcular UF goal
#         pre = data.get("pre_dialysis_weight_kg", 0)
#         dry = data.get("dry_weight_kg", 0)
#         uf_goal = max(0.0, pre - dry)
#         data["uf_goal_liters"] = uf_goal

#         # Guardar en DB
#         self.patients_db[data["patient_id"]] = data

#         # Guardar en current_values (solo campos relevantes)
#         key_map = {
#             "patient_id": "patient_id",
#             "patient_name": "patient_name",
#             "gender": "patient_gender",
#             "age": "patient_age",
#             "height_cm": "patient_height_cm",
#             "dry_weight_kg": "patient_dry_weight_kg",
#             "pre_dialysis_weight_kg": "patient_pre_weight_kg",
#             "uf_goal_liters": "uf_goal_liters"
#         }
#         for db_key, cv_key in key_map.items():
#             if db_key in data:
#                 self.current_values[cv_key] = data[db_key]

#         self._refresh_patient_list()
#         QMessageBox.information(self, "Guardado", 
#                                 f"Paciente guardado.\nUF goal: {uf_goal:.2f} L")

#         # Opcional: actualizar otras pantallas
#         if hasattr(self.parent_window, 'dialysis_screen'):
#             self.parent_window.dialysis_screen.update_values(self.current_values) 
