# gui/therapy/alarms_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame, QLineEdit, QSizePolicy,
    QPushButton, QScrollArea, QMessageBox, QDialog, QDialogButtonBox, QGroupBox,QFormLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont, QDoubleValidator, QTextOption
from gui.components.ui_components import LabeledParameterWidget, ClickableLineEdit
from gui.components.numpad_modal import NumpadDialog
from gui.configuration.alarm_limits import AlarmLimitsManager





class AlarmLimitsConfigDialog(QDialog):
    """
    Diálogo para configurar los límites de alarma (inferior y superior)
    de las variables críticas de la máquina de hemodiálisis.
    Usa teclado numérico táctil y botón de restaurar por defecto.
    """
    def __init__(self, parent=None, current_values=None, limits_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Límites de Alarma")
        self.setMinimumSize(680, 720)  # un poco más ancho por el botón extra

        self.current_values = current_values or {}
        self.limits_manager = limits_manager

        if not self.limits_manager:
            raise ValueError("Se requiere pasar un AlarmLimitsManager válido")

        self.inputs = {}          # tag → (min_edit, max_edit)
        self.variables = []

        self.setup_variables()
        self.setup_ui()

    def setup_variables(self):
        self.variables = [
            {
                "tag": "dialyCondVariableData",
                "name": "Conductividad medida",
                "unit": "mS/cm",
                "decimals": 2,
                "hint": "Rango típico: 13.0 – 15.0 mS/cm"
            },
            {
                "tag": "dialyTempVariableData",
                "name": "Temperatura medida",
                "unit": "°C",
                "decimals": 1,
                "hint": "Rango típico: 35.5 – 38.0 °C"
            },
            {
                "tag": "bloodFlowVariableData",
                "name": "Flujo de sangre calculado",
                "unit": "ml/min",
                "decimals": 0,
                "hint": "Rango típico: 200 – 450 ml/min"
            },
            {
                "tag": "arterPresProcessData",
                "name": "Presión arterial (línea sangre)",
                "unit": "mmHg",
                "decimals": 0,
                "hint": "Rango típico: -100 a +300 mmHg"
            },
            {
                "tag": "venouPresProcessData",
                "name": "Presión venosa (línea sangre)",
                "unit": "mmHg",
                "decimals": 0,
                "hint": "Rango típico: 0 – 350 mmHg"
            },
        ]
        
    def create_numpad_opener(self, edit_widget: ClickableLineEdit, decimals: int, tag: str, field: str):
        """Crea una función que abre el numpad sin problemas con argumentos de señal"""
        def opener(checked=False):  # ignora el argumento 'checked' que envía Qt
            self.open_numpad(edit_widget, decimals, tag, field)
        return opener
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # Título
        title = QLabel("Límites de alarma - Seguridad del paciente")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #c0392b; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        desc = QLabel("Toque los campos para ingresar valores. Use 'Restaurar' para volver a valores por defecto.")
        desc.setStyleSheet("font-size: 14px; color: #555; text-align: center;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        main_layout.addSpacing(15)

        # Grupo de parámetros
        group = QGroupBox("Parámetros configurables")
        group_layout = QFormLayout()
        group_layout.setLabelAlignment(Qt.AlignRight)
        group_layout.setFormAlignment(Qt.AlignLeft)
        group_layout.setSpacing(14)

        for var in self.variables:
            tag = var["tag"]
            decimals = var["decimals"]

            # Valor actual
            current_val = self.current_values.get(tag)
            current_str = f"{current_val:.{decimals}f}" if current_val is not None else "—"

            # Límites actuales
            min_val, max_val = self.limits_manager.get_limits(tag)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)

            lbl_current = QLabel(f"Actual: {current_str}")
            lbl_current.setStyleSheet("color: #444; min-width: 130px; font-size: 14px;")

            # Campo Inferior
            min_edit = ClickableLineEdit(f"{min_val:.{decimals}f}")
            min_edit.setAlignment(Qt.AlignCenter)
            min_edit.setFixedWidth(120)
            min_edit.setStyleSheet("""
                QLineEdit {
                    background: #f8fafc;
                    border: 2px solid #cbd5e1;
                    border-radius: 8px;
                    font-size: 18px;
                    padding: 8px;
                }
            """)
            # min_edit.clicked.connect(lambda checked=False, e=min_edit, d=decimals, t=tag, f="min": self.open_numpad(e, d, t, f))
            min_edit.clicked.connect(self.create_numpad_opener(min_edit, decimals, tag, "min"))

            sep = QLabel(" – ")
            sep.setStyleSheet("color: #64748b; font-size: 16px;")

            # Campo Superior
            max_edit = ClickableLineEdit(f"{max_val:.{decimals}f}")
            max_edit.setAlignment(Qt.AlignCenter)
            max_edit.setFixedWidth(120)
            max_edit.setStyleSheet("""
                QLineEdit {
                    background: #f8fafc;
                    border: 2px solid #cbd5e1;
                    border-radius: 8px;
                    font-size: 18px;
                    padding: 8px;
                }
            """)
            # max_edit.clicked.connect(lambda checked=False, e=max_edit, d=decimals, t=tag, f="max": self.open_numpad(e, d, t, f))
            max_edit.clicked.connect(self.create_numpad_opener(max_edit, decimals, tag, "max")
)

            # Botón Restaurar por defecto
            restore_btn = QPushButton("Restaurar")
            restore_btn.setFixedSize(100, 45)
            restore_btn.setStyleSheet("""
                QPushButton {
                    background: #f59e0b;
                    color: #ffffff;
                    font-size: 14px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover { background: #d97706; }
                QPushButton:pressed { background: #b45309; }
            """)
            # restore_btn.clicked.connect(self.create_numpad_opener())
            restore_btn.clicked.connect(lambda _, t=tag, m=min_edit, M=max_edit, d=decimals: self.restore_defaults(t, m, M, d))

            row_layout.addWidget(lbl_current)
            row_layout.addWidget(min_edit)
            row_layout.addWidget(sep)
            row_layout.addWidget(max_edit)
            row_layout.addWidget(restore_btn)
            row_layout.addStretch()

            lbl_name = QLabel(f"{var['name']} ({var['unit']})")
            lbl_name.setStyleSheet("font-weight: bold; font-size: 16px; min-width: 280px;")

            hint_lbl = QLabel(var["hint"])
            hint_lbl.setStyleSheet("color: #64748b; font-size: 13px;")

            group_layout.addRow(lbl_name, row_layout)
            group_layout.addRow("", hint_lbl)

            self.inputs[tag] = (min_edit, max_edit)

        group.setLayout(group_layout)
        main_layout.addWidget(group)

        main_layout.addStretch()

        # Botones principales
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.validate_and_save)
        button_box.rejected.connect(self.reject)

        save_btn = button_box.button(QDialogButtonBox.Save)
        save_btn.setText("Guardar cambios")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #22c55e; color: #ffffff; font-size: 18px; padding: 12px;
                min-width: 180px; border-radius: 8px;
            }
            QPushButton:hover { background: #16a34a; }
        """)

        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444; color: #ffffff; font-size: 18px; padding: 12px;
                min-width: 140px; border-radius: 8px;
            }
            QPushButton:hover { background: #dc2626; }
        """)

        main_layout.addWidget(button_box, alignment=Qt.AlignRight)

    def open_numpad(self, line_edit: ClickableLineEdit, decimals: int, tag: str, field: str):
        current_text = line_edit.text().strip()
        dialog = NumpadDialog(
            parent=self,
            initial_value=current_text,
            title=f"Ingrese límite {field.upper()} para {tag}"
        )
        if dialog.exec() == QDialog.Accepted:
            value = dialog.get_value()
            if isinstance(value, float):
                formatted = f"{value:.{decimals}f}"
            else:
                formatted = str(value)
            line_edit.setText(formatted)
    
 

    def restore_defaults(self, tag: str, min_edit: ClickableLineEdit, max_edit: ClickableLineEdit, decimals: int):
        """
        Restaura los límites por defecto para esta variable específica.
        """
        if hasattr(self.limits_manager, 'defaults') and tag in self.limits_manager.defaults:
            def_min, def_max = self.limits_manager.defaults[tag]
            min_edit.setText(f"{def_min:.{decimals}f}")
            max_edit.setText(f"{def_max:.{decimals}f}")
            QMessageBox.information(
                self,
                "Restaurado",
                f"Límites de {tag} restaurados a valores por defecto:\n"
                f"Min: {def_min}   Max: {def_max}"
            )
        else:
            QMessageBox.warning(
                self,
                "Sin valores por defecto",
                f"No se encontraron valores por defecto para {tag}.\n"
                "Los límites actuales se mantienen."
            )

    def validate_and_save(self):
        errors = []

        for var in self.variables:
            tag = var["tag"]
            min_edit, max_edit = self.inputs[tag]

            try:
                min_v = float(min_edit.text())
                max_v = float(max_edit.text())
            except ValueError:
                errors.append(f"{var['name']}: ingrese valores numéricos válidos")
                continue

            if min_v >= max_v:
                errors.append(f"{var['name']}: límite inferior debe ser menor que el superior")

            if min_v < -1000 or max_v > 1000:
                errors.append(f"{var['name']}: valores fuera de rango razonable (±1000)")

        if errors:
            QMessageBox.warning(
                self,
                "Errores detectados",
                "No se pueden guardar los cambios:\n\n• " + "\n• ".join(errors) +
                "\n\nCorrija los valores indicados."
            )
            return

        # Guardar
        for var in self.variables:
            tag = var["tag"]
            min_edit, max_edit = self.inputs[tag]
            min_v = float(min_edit.text())
            max_v = float(max_edit.text())

            try:
                self.limits_manager.set_limits(tag, min_v, max_v)
            except ValueError as e:
                QMessageBox.critical(self, "Error al guardar", str(e))
                return

        QMessageBox.information(
            self,
            "Guardado exitoso",
            "Límites de alarma actualizados.\nLos cambios se aplican inmediatamente."
        )
        self.accept()
        

class AlarmsScreen(QWidget):
    """
    Pantalla dedicada para alarmas activas e historial de eventos.
    Maneja el reconocimiento (ACK) sin borrar alarmas persistentes.
    Estilo de "Equipo Médico" con fondos claros.
    """

    def __init__(self, parent=None, values_dict=None, alarm_system=None):
        super().__init__(parent)
        # --- ESTILOS GENERALES DE LA PANTALLA ---

        self.setStyleSheet("background: #F8F8FA; color: #333333; font-family: 'Segoe UI';")
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}
        self.alarm_system = alarm_system

        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.active_alarms = {}

        self.setup_ui()

        if self.alarm_system:
            print("AlarmsScreen: alarm_system found. Known alarm count:",
                  len(getattr(self.alarm_system, 'display_names', [])))
            self.alarm_system.alarm_changed.connect(self.on_alarm_changed)
            self.alarm_system.new_event.connect(self.on_new_event) # Conectar on_new_event
            self._sync_initial_state()
        else:
            print("Warning: alarm_system not available in AlarmsScreen")

       

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # ── Estilo scrollbar más ancho y visible ────────────────
        self.setStyleSheet(self.styleSheet() + """
            QScrollBar:vertical {
                border: none;
                background: #e0e0e5;
                width: 34px;               /* <--- aquí cambias el ancho */
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5) # Reducido un poco el espaciado

        # Título
        title = QLabel("ALARMAS Y EVENTOS DEL SISTEMA")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #E74C3C;") # Rojo fuerte
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #CCCCCC; max-height: 1px;") # Separador sutil
        layout.addWidget(sep1)

        # Sección Alarmas Activas
        lbl_active = QLabel("ALARMAS ACTIVAS")
        lbl_active.setStyleSheet("font-size: 32px; font-weight: bold; color: #3F88C5; margin-top: 15px;") # Azul profesional
        layout.addWidget(lbl_active)

        self.active_alarms_display = QTextEdit()
        self.active_alarms_display.setReadOnly(True)
        self.active_alarms_display.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF; /* Blanco puro */
                color: #333333; /* Gris oscuro para el texto */
                font-family: Consolas, 'Courier New', monospace;
                font-size: 20px;
                border: 2px solid #D9534F; /* Borde rojo suave */
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.active_alarms_display.setMinimumHeight(220)
        layout.addWidget(self.active_alarms_display)

        # Botón Reconocer
        self.btn_ack_all = QPushButton("RECONOCER (SILENCIAR)")
        self.btn_ack_all.setFixedSize(320, 60)
        self.btn_ack_all.setStyleSheet("""
            QPushButton {
                background: #D9534F; /* Rojo suave */
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background: #C9302C; }
            QPushButton:pressed { background: #B22B29; }
            QPushButton:disabled { background: #CCCCCC; color: #999999; }
        """)
        self.btn_ack_all.clicked.connect(self.acknowledge_all_alarms)

        self.btn_config_limits = QPushButton("Configuración")
        self.btn_config_limits.setFixedSize(320, 60)
        self.btn_config_limits.setStyleSheet("""
            QPushButton {
                background: #3498DB; /* Azul Suave */
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background: #2980B9; }
            QPushButton:pressed { background: #1F6C8C; }
        """)
        self.btn_config_limits.clicked.connect(self.open_variable_configuration)


        
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.btn_ack_all, alignment=Qt.AlignRight)
        btn_layout.addWidget(self.btn_config_limits, alignment=Qt.AlignRight)
        layout.addLayout(btn_layout)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #CCCCCC; max-height: 1px;") # Separador sutil
        layout.addWidget(sep2)

        # Sección Historial
        lbl_history = QLabel("HISTORIAL DE EVENTOS")
        lbl_history.setStyleSheet("font-size: 26px; font-weight: bold; color: #3F88C5; margin-top: 15px;") # Azul profesional
        layout.addWidget(lbl_history)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setUndoRedoEnabled(False)

        self.history_display.setLineWrapMode(QTextEdit.WidgetWidth)          # wrap al ancho del widget
        self.history_display.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)  # corta en espacios cuando pueda, si no → en cualquier 
        self.history_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.history_display.setWordWrap(True)
        self.history_display.setStyleSheet("""
            QTextEdit {
                background: #F0F2F5; /* Fondo ligeramente gris para diferenciar del principal */
                color: #333333; /* Texto gris oscuro */
                font-family: Consolas, monospace;
                font-size: 17px;
                border: 1px solid #CCCCCC; /* Borde sutil */
                border-radius: 5px;
                padding: 8px;
            }
        """)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.history_display)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setMinimumHeight(240) # Ajustado altura
        layout.addWidget(scroll_area)

        # Mensaje inicial (ahora más claro)
        self._update_active_alarms_display()
        self.history_display.append(
            f'<span style="color:#607D8B;">[Sistema iniciado — {QTime.currentTime().toString("hh:mm:ss")}]</span>'
        )

    def _sync_initial_state(self):
        """Sincroniza el estado inicial al abrir la pantalla."""
        if not self.alarm_system:
            return

        current_time = QTime.currentTime().toString("hh:mm:ss")
        loaded_count = 0

        # Iterar sobre las alarmas conocidas del AlarmSystem
        for i, name in enumerate(self.alarm_system.display_names):
            # Asegurarse de que el índice sea válido para previous_states y severity_levels
            if i < len(self.alarm_system.previous_states) and self.alarm_system.previous_states[i]:
                level = (self.alarm_system.severity_levels[i] 
                         if i < len(self.alarm_system.severity_levels) else "info")
                
                # Asignar un valor dummy, o buscar el valor real si tienes el tag mapeado
                # (Para obtener el valor real necesitarías el tag de la alarma y buscarlo en self.values)
                value = None 
                
                # Si la alarma ya existía en nuestro diccionario, no la reseteamos a "no reconocida"
                if name not in self.active_alarms:
                    self.active_alarms[name] = {
                        'value': value,
                        'level': level,
                        'time': current_time, # La hora de cuando se cargó en la GUI
                        'acked': False
                    }
                    loaded_count += 1
                else:
                    # Si ya está, actualizamos el valor y la hora, pero mantenemos acked
                    self.active_alarms[name]['value'] = value
                    self.active_alarms[name]['time'] = current_time

        print(f"AlarmsScreen: initial sync → {loaded_count} newly active alarms loaded")
        self._update_active_alarms_display()
        self.update_ack_button_state()

    def on_alarm_changed(self, idx, is_active, value, name, level, limits):
        """Maneja la señal cuando una alarma se activa o desactiva físicamente."""
        current_time = QTime.currentTime().toString("hh:mm:ss")

        if is_active:
            # Si la alarma se activa
            if name in self.active_alarms:
                # Si ya estaba activa, solo actualizamos el valor y la hora.
                # Mantenemos 'acked' en su estado actual (si ya fue reconocida, sigue reconocida).
                self.active_alarms[name]['value'] = value
                self.active_alarms[name]['time'] = current_time # Actualiza el tiempo de la última detección
            else:
                # Es una alarma nueva, o se fue y volvió -> la agregamos como NO reconocida
                self.active_alarms[name] = {
                    'value': value,
                    'level': level,
                    'time': current_time,
                    'acked': False
                }
            self._append_to_history(f"ACTIVADA: {name}", value, level, current_time)

        else:
            # La condición física desapareció -> Borramos la alarma de la lista
            if name in self.active_alarms:
                del self.active_alarms[name]
                self._append_to_history(f"NORMALIZADA: {name}", value, "info", current_time)

        self._update_active_alarms_display()
        self.update_ack_button_state()

    def on_new_event(self, event_msg, value, timestamp):
        """Maneja los eventos generales del AlarmSystem para el historial."""
        # Se asume que event_msg ya contiene el tipo (ACTIVADA/DESACTIVADA) y el nombre
        # Y que timestamp viene ya formateado
        self._append_to_history(event_msg, value, "info", timestamp) # Usamos "info" para eventos generales

    def acknowledge_all_alarms(self):
        """
        Marca todas las alarmas NO reconocidas actualmente como 'Reconocidas' (ACK).
        No las borra. Solo cambia su estado visual.
        """
        if not self.active_alarms:
            QMessageBox.information(self, "Información", "No hay alarmas activas para reconocer.")
            return

        unacked_count = sum(1 for data in self.active_alarms.values() if not data['acked'])
        if unacked_count == 0:
            QMessageBox.information(self, "Información", "Todas las alarmas activas ya están reconocidas.")
            return

        # reply = QMessageBox.question(
        #     self, "Confirmar Reconocimiento",
        #     f"¿Reconocer {unacked_count} alarma(s) activa(s) y silenciar?",
        #     QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        # )
          # 1. Creamos la instancia manual del MessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Reconocimiento")
        msg_box.setText(f"¿Reconocer {unacked_count} alarma(s) activa(s) y silenciar?")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        # 2. APLICAMOS EL ESTILO (CSS)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b; /* Fondo de la ventana oscuro */
                color: #ffffff;            /* Texto del QMessageBox (principal) */
            }
            QLabel {
                color: #ffffff;            /* Asegura que el texto del mensaje sea blanco */
                background-color: #2b2b2b; /* <-- ¡Añadido! Fondo del QLabel explícitamente oscuro */
                padding: 5px;              /* Opcional: un pequeño padding para que el texto no se pegue al borde */
            }
            QPushButton {
                background-color: #4CAF50; /* Color de fondo del botón (Verde ejemplo) */
                color: #ffffff;              /* Color del texto del botón */
                border-radius: 5px;        /* Bordes redondeados */
                padding: 5px 15px;         /* Relleno para hacerlo más grande */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049; /* Color al pasar el mouse por encima */
            }
            QPushButton:pressed {
                background-color: #3e8e41; /* Color al presionar */
            }
        """)


        reply = msg_box.exec()

        if reply == QMessageBox.Yes:
            changed = False
            for name, data in self.active_alarms.items():
                if not data['acked']:
                    data['acked'] = True
                    changed = True   

            if changed:
                self._update_active_alarms_display()
                self.update_ack_button_state()

                # === NUEVA LÓGICA DE SILENCIO ===
                if self.parent_window and hasattr(self.parent_window, 'led_bar'):
                    self.parent_window.buzzer_silenced_by_user = True
                    self.parent_window.update_led_bar_state()   # ← fuerza envío inmediato

                self._append_to_history("Operador reconoció alarmas activas y silenció buzzer", 
                                      None, "info", QTime.currentTime().toString("hh:mm:ss"))
                QMessageBox.information(self, "Listo", f"{unacked_count} alarma(s) reconocida(s). Buzzer silenciado.")
        else:
            QMessageBox.information(self, "Cancelado", "Reconocimiento de alarmas cancelado.")

    def _update_active_alarms_display(self):
        """Regenera el HTML de la lista de alarmas activas con la nueva estética."""
        if not self.active_alarms:
            self.active_alarms_display.setHtml(
                '<div style="text-align:center; color:#607D8B; font-size:24px; margin-top:20px;">'
                'SISTEMA EN ÓPTIMAS CONDICIONES - SIN ALARMAS ACTIVAS</div>'
            )
            return

        html = ""
        # Ordenar: No reconocidas primero, luego por severidad 
        priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
        
        sorted_alarms = sorted(
            self.active_alarms.items(),
            key=lambda item: (
                not item[1]['acked'],  # Las False (no reconocidas) van primero
                priority_map.get(item[1]['level'], 0) # Luego por prioridad de severidad
            ),
            reverse=True # Para que el más grave o no reconocido esté arriba
        )

        for name, data in sorted_alarms:
            level = data['level']
            acked = data['acked']
            time_str = data['time']
            val = f"{data['value']:.1f}" if data['value'] is not None else "N/D" # N/D para No Disponible

            # Colores base para alarmas (no reconocidas)
            colors = {
                "rojo": "#E74C3C",    # Rojo fuerte
                "naranja": "#F39C12", # Naranja
                "amarillo": "#FBC02D",# Amarillo
                "cian": "#3498DB",    # Azul vibrante
                "info": "#607D8B"     # Gris azulado para info
            }
            base_color = colors.get(level, "#333333") # Default texto oscuro

            # Estilo visual diferente para ACK vs NO-ACK
            if acked:
                # Alarma Reconocida: Fondo claro, texto atenuado, borde sutil
                bg_style = "background-color: #E0E0E0;" # Gris claro
                status_icon = "✔ Reconocida"
                text_color = "#757575" # Gris medio, atenuado
                border_color = "#BDBDBD" # Borde gris más oscuro
            else:
                # Alarma NO Reconocida: Fondo ligeramente resaltado, texto vivo, borde fuerte
                bg_style = f"background-color: {base_color}1A;" # Un 10% de opacidad del color base
                status_icon = "⚠️ ACTIVA"
                text_color = base_color # Color vivo
                border_color = base_color # Borde con color de la alarma

            # Construcción de la tarjeta HTML para la alarma
            # Aseguramos el tamaño de fuente dentro del HTML
            html += f"""
            <div style="border: 2px solid {border_color}; border-radius: 8px; margin-bottom: 8px; padding: 10px; {bg_style}">
                <table width="100%" style="border-collapse: collapse;">
                    <tr>
                        <td width="15%" style="color:{text_color}; font-weight:bold; font-size:18px; padding: 2px;">{time_str}</td>
                        <td width="55%" style="color:{text_color}; font-weight:bold; font-size:22px; padding: 2px;">{name}</td>
                        <td width="15%" style="color:#333333; font-size:22px; text-align:right; padding: 2px;">{val}</td>
                        <td width="15%" style="color:{text_color}; font-weight:bold; text-align:right; font-size:16px; padding: 2px;">{status_icon}</td>
                    </tr>
                </table>
            </div>
            """

        self.active_alarms_display.setHtml(html)

    def _append_to_history(self, text, value, level, time_str):
        """Agrega un evento al historial con el nuevo esquema de colores."""
        colors = {
            "rojo": "#E74C3C", "naranja": "#F39C12", "amarillo": "#FBC02D", 
            "cian": "#3498DB", "info": "#607D8B"
        }
        color = colors.get(level, "#333333") # Default a gris oscuro

        val_str = f" [{value:.1f}]" if value is not None else ""
        
        self.history_display.append(
            f'<span style="color:#607D8B; font-size:17px;">[{time_str}]</span> '
            f'<span style="color:{color}; font-weight:bold; font-size:17px;">{text}{val_str}</span>'
        )
        self.history_display.verticalScrollBar().setValue(
            self.history_display.verticalScrollBar().maximum()
        )
    
    def update_ack_button_state(self):
        """Habilita/Deshabilita el botón de reconocimiento si hay alarmas no reconocidas."""
        if any(not data['acked'] for data in self.active_alarms.values()):
            self.btn_ack_all.setEnabled(True)
        else:
            self.btn_ack_all.setEnabled(False)

    def update_values(self, values_dict):
        """Método de compatibilidad. No usado directamente aquí."""
        self.values = values_dict

    def silence_buzzer_only(self):
        """Silencia el buzzer SIN tocar el estado de los LEDs (útil desde otras pantallas)."""
        if not self._last_buzzer_silence_state_sent:
            self.command_queue.put(self.CMD_SILENCE)
            self._last_buzzer_silence_state_sent = True

    def open_variable_configuration(self):
        dialog = AlarmLimitsConfigDialog(
            self,
            current_values=self.values,
            limits_manager=self.limits_manager   
            )
        dialog.exec_()

