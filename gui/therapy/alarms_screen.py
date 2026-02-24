# gui/therapy/alarms_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame,
    QPushButton, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont

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
        self.values = values_dict if values_dict is not None else {}
        self.alarm_system = alarm_system

        self.setFixedSize(1536, 726)

        # Cache de alarmas activas.
        # Clave: nombre de la alarma
        # Valor: diccionario { 'value': float, 'level': str, 'time': str, 'acked': bool }
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
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18) # Reducido un poco el espaciado

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
                color: white;
                font-size: 22px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background: #C9302C; }
            QPushButton:pressed { background: #B22B29; }
            QPushButton:disabled { background: #CCCCCC; color: #999999; }
        """)
        self.btn_ack_all.clicked.connect(self.acknowledge_all_alarms)
        
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.btn_ack_all, alignment=Qt.AlignRight)
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

        reply = QMessageBox.question(
            self, "Confirmar Reconocimiento",
            f"¿Reconocer {unacked_count} alarma(s) activa(s) y silenciar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            changed = False
            for name, data in self.active_alarms.items():
                if not data['acked']:
                    data['acked'] = True
                    changed = True
            
            if changed:
                self._update_active_alarms_display()
                self.update_ack_button_state()

                if self.parent_window and hasattr(self.parent_window, 'led_bar') and self.parent_window.led_bar:
                    # Envia solo el comando de silencio, manteniendo el último comando de LED.
                    self.parent_window.led_bar.send_state(self.parent_window.led_bar.CMD_SILENCE)
                    self._append_to_history("Comando de SILENCIO enviado al buzzer", None, "info", QTime.currentTime().toString("hh:mm:ss"))
            
                
                self._append_to_history("Operador reconoció alarmas activas", None, "info", QTime.currentTime().toString("hh:mm:ss"))
                QMessageBox.information(self, "Listo", f"{unacked_count} alarma(s) reconocida(s).")
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
        # Ordenar: No reconocidas primero, luego por severidad (más alta primero)
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




# # gui/therapy/alarms_screen.py

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame,
#     QPushButton, QScrollArea, QMessageBox
# )
# from PySide6.QtCore import Qt, QTime
# from PySide6.QtGui import QFont

# class AlarmsScreen(QWidget):
#     """
#     Pantalla dedicada para alarmas activas e historial de eventos.
#     Maneja el reconocimiento (ACK) sin borrar alarmas persistentes.
#     """

#     def __init__(self, parent=None, values_dict=None, alarm_system=None):
#         super().__init__(parent)
#         self.setStyleSheet("background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI';")

#         self.values = values_dict if values_dict is not None else {}
#         self.alarm_system = alarm_system

#         self.setFixedSize(1536, 726)

#         # Cache de alarmas activas.
#         # Clave: nombre de la alarma
#         # Valor: diccionario { 'value': float, 'level': str, 'time': str, 'acked': bool }
#         self.active_alarms = {}

#         self.setup_ui()

#         if self.alarm_system:
#             self.alarm_system.alarm_changed.connect(self.on_alarm_changed)
#             self._sync_initial_state()
#         else:
#             print("Warning: alarm_system not available in AlarmsScreen")

#     def setup_ui(self):
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(40, 30, 40, 30)
#         layout.setSpacing(24)

#         # Título
#         title = QLabel("ALARMAS Y EVENTOS DEL SISTEMA")
#         title.setStyleSheet("font-size: 42px; font-weight: bold; color: #f87171;")
#         title.setAlignment(Qt.AlignCenter)
#         layout.addWidget(title)

#         # Sección Alarmas Activas
#         lbl_active = QLabel("ALARMAS ACTIVAS")
#         lbl_active.setStyleSheet("font-size: 32px; font-weight: bold; color: #ef4444; margin-top: 20px;")
#         layout.addWidget(lbl_active)

#         self.active_alarms_display = QTextEdit()
#         self.active_alarms_display.setReadOnly(True)
#         # Usamos CSS para dar formato, pero el contenido será HTML rico
#         self.active_alarms_display.setStyleSheet("""
#             QTextEdit {
#                 background: #1e293b;
#                 border: 2px solid #7f1d1d;
#                 border-radius: 10px;
#                 padding: 10px;
#             }
#         """)
#         self.active_alarms_display.setMinimumHeight(250)
#         layout.addWidget(self.active_alarms_display)

#         # Botón Reconocer
#         self.btn_ack_all = QPushButton("RECONOCER (SILENCIAR)")
#         self.btn_ack_all.setFixedSize(320, 60)
#         self.btn_ack_all.setStyleSheet("""
#             QPushButton {
#                 background: #dc2626; color: white; font-size: 22px; font-weight: bold; border-radius: 12px;
#             }
#             QPushButton:hover { background: #b91c1c; }
#             QPushButton:pressed { background: #991b1b; }
#         """)
#         self.btn_ack_all.clicked.connect(self.acknowledge_all_alarms)
        
#         # Contenedor para alinear el botón a la derecha
#         btn_layout = QVBoxLayout()
#         btn_layout.addWidget(self.btn_ack_all, alignment=Qt.AlignRight)
#         layout.addLayout(btn_layout)

#         # Sección Historial
#         lbl_history = QLabel("HISTORIAL DE EVENTOS")
#         lbl_history.setStyleSheet("font-size: 26px; font-weight: bold; color: #94a3b8; margin-top: 20px;")
#         layout.addWidget(lbl_history)

#         self.history_display = QTextEdit()
#         self.history_display.setReadOnly(True)
#         self.history_display.setStyleSheet("background: #0f172a; color: #cbd5e1; font-family: Consolas; font-size: 16px; border: 1px solid #334155;")
#         layout.addWidget(self.history_display)

#         # Estado inicial
#         self._update_active_alarms_display()

#     def _sync_initial_state(self):
#         """Sincroniza el estado inicial al abrir la pantalla."""
#         if not hasattr(self.alarm_system, 'active_alarms_list'): 
#             # Asumiendo que alarm_system tiene una forma de saber cuáles están activas actualmente
#             # Si no, usamos previous_states como en tu código original
#             for i, active in enumerate(self.alarm_system.previous_states):
#                 if active:
#                     name = self.alarm_system.display_names[i]
#                     level = self.alarm_system.severity_levels[i]
#                     # Si ya estaba en nuestra lista local, mantenemos su estado (ej. acked)
#                     # Si no, la agregamos como nueva
#                     if name not in self.active_alarms:
#                         self.active_alarms[name] = {
#                             'value': 0.0, # Valor dummy si no tenemos el real inmediato
#                             'level': level,
#                             'time': QTime.currentTime().toString("hh:mm:ss"),
#                             'acked': False
#                         }
#             self._update_active_alarms_display()

#     def on_alarm_changed(self, idx, is_active, value, name, level, limits):
#         """Maneja la señal cuando una alarma se activa o desactiva físicamente."""
#         current_time = QTime.currentTime().toString("hh:mm:ss")

#         if is_active:
#             # Si la alarma se activa (o se actualiza valor)
#             # Si ya existía y estaba reconocida, la mantenemos reconocida o la reseteamos?
#             # Usualmente si la condición persiste, se actualiza el valor pero se mantiene el ACK.
#             # Si la alarma se fue y volvió, es una NUEVA alarma (acked = False).
            
#             if name in self.active_alarms:
#                 # Solo actualizamos valor, mantenemos estado ACK y hora original
#                 self.active_alarms[name]['value'] = value
#             else:
#                 # Nueva alarma
#                 self.active_alarms[name] = {
#                     'value': value,
#                     'level': level,
#                     'time': current_time,
#                     'acked': False
#                 }
#                 # Opcional: Reproducir sonido aquí
            
#             self._append_to_history(f"ACTIVADA: {name}", value, level, current_time)

#         else:
#             # La condición física desapareció -> Borramos la alarma de la lista visual
#             if name in self.active_alarms:
#                 del self.active_alarms[name]
#                 self._append_to_history(f"NORMALIZADA: {name}", value, "info", current_time)

#         self._update_active_alarms_display()

#     def acknowledge_all_alarms(self):
#         """
#         Marca todas las alarmas actuales como 'Reconocidas' (ACK).
#         NO las borra. Solo cambian visualmente para indicar que el operador las vio.
#         """
#         if not self.active_alarms:
#             return

#         changed = False
#         for name in self.active_alarms:
#             if not self.active_alarms[name]['acked']:
#                 self.active_alarms[name]['acked'] = True
#                 changed = True
        
#         if changed:
#             self._update_active_alarms_display()
#             # Aquí deberías enviar señal para silenciar buzzer si existe
#             # if self.parent(): self.parent().silence_buzzer()
            
#             self._append_to_history("Operador reconoció alarmas activas", None, "info", QTime.currentTime().toString("hh:mm:ss"))

#     def _update_active_alarms_display(self):
#         """Regenera el HTML de la lista de alarmas activas."""
#         if not self.active_alarms:
#             self.active_alarms_display.setHtml(
#                 '<div style="text-align:center; color:#94a3b8; font-size:24px; margin-top:20px;">'
#                 'SISTEMA NORMAL - SIN ALARMAS</div>'
#             )
#             return

#         html = ""
#         # Ordenar: No reconocidas primero, luego por severidad
#         priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
        
#         sorted_alarms = sorted(
#             self.active_alarms.items(),
#             key=lambda item: (
#                 not item[1]['acked'],  # False (0) va antes que True (1), así que 'not' invierte: True(No ack) primero
#                 priority_map.get(item[1]['level'], 0)
#             ),
#             reverse=True
#         )

#         for name, data in sorted_alarms:
#             level = data['level']
#             acked = data['acked']
#             time_str = data['time']
#             val = f"{data['value']:.1f}" if data['value'] is not None else "--"

#             # Colores base
#             colors = {
#                 "rojo": "#ef4444", "naranja": "#f97316", 
#                 "amarillo": "#eab308", "cian": "#06b6d4"
#             }
#             base_color = colors.get(level, "#cbd5e1")

#             # Estilo visual diferente para ACK vs NO-ACK
#             if acked:
#                 # Alarma Reconocida: Texto más oscuro, quizás icono de check, fondo normal
#                 bg_style = "background-color: #334155;" # Gris oscuro
#                 status_icon = "✔ ACK"
#                 text_color = "#94a3b8" # Gris claro (atenuado)
#                 border_color = "#475569"
#             else:
#                 # Alarma NO Reconocida: Fondo brillante o borde fuerte, texto alerta
#                 bg_style = f"background-color: {base_color}22;" # Color base muy transparente
#                 status_icon = "⚠️ ACTIVA"
#                 text_color = base_color # Color vivo
#                 border_color = base_color

#             # Construcción de la tarjeta HTML para la alarma
#             html += f"""
#             <div style="border: 2px solid {border_color}; border-radius: 8px; margin-bottom: 8px; padding: 8px; {bg_style}">
#                 <table width="100%">
#                     <tr>
#                         <td width="15%" style="color:{text_color}; font-weight:bold; font-size:18px;">{time_str}</td>
#                         <td width="55%" style="color:{text_color}; font-weight:bold; font-size:22px;">{name}</td>
#                         <td width="15%" style="color:#e2e8f0; font-size:22px; text-align:right;">{val}</td>
#                         <td width="15%" style="color:{text_color}; font-weight:bold; text-align:right; font-size:16px;">{status_icon}</td>
#                     </tr>
#                 </table>
#             </div>
#             """

#         self.active_alarms_display.setHtml(html)

#     def _append_to_history(self, text, value, level, time_str):
#         colors = {"rojo": "#f87171", "naranja": "#fb923c", "amarillo": "#fbbf24", "cian": "#22d3ee", "info": "#94a3b8"}
#         color = colors.get(level, "#cbd5e1")
#         val_str = f" [{value:.1f}]" if value is not None else ""
        
#         self.history_display.append(
#             f'<span style="color:#64748b;">{time_str}</span> '
#             f'<span style="color:{color}; font-weight:bold;">{text}{val_str}</span>'
#         )

#     def update_values(self, values_dict):
#         self.values = values_dict



# # gui/therapy/alarms_screen.py
# # Dedicated screen for active alarms + event/history log
# # Stacked index: 5 ("Alarmas")

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame,
#     QPushButton, QScrollArea, QMessageBox
# )
# from PySide6.QtCore import Qt, QTime
# from PySide6.QtGui import QFont

# from core.variables_map import VARIABLES


# class AlarmsScreen(QWidget):
#     """
#     Screen displaying currently active alarms and full event history.
#     Connects to AlarmSystem signals for real-time updates.
#     """

#     def __init__(self, parent=None, values_dict=None, alarm_system=None):
#         super().__init__(parent)
#         self.setStyleSheet("background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI';")

#         # References
#         self.values = values_dict if values_dict is not None else {}
#         self.alarm_system = alarm_system

#         self.setFixedSize(1536, 726)

#         # Active alarms cache: name → (value, severity_level, activation_time)
#         self.active_alarms = {}

#         self.setup_ui()

#         # Connect signals and sync initial state
#         if self.alarm_system:
#             print("AlarmsScreen: alarm_system found. Known alarm count:",
#                   len(getattr(self.alarm_system, 'display_names', [])))

#             self.alarm_system.alarm_changed.connect(self.on_alarm_changed)
#             self.alarm_system.new_event.connect(self.on_new_event)

#             # Critical: Sync current alarm states on initialization
#             self._sync_initial_state()
#         else:
#             print("Warning: alarm_system not available in AlarmsScreen")

#     def setup_ui(self):
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(40, 30, 40, 30)
#         layout.setSpacing(24)

#         # Title
#         title = QLabel("ALARMAS Y EVENTOS DEL SISTEMA")
#         title.setStyleSheet("font-size: 42px; font-weight: bold; color: #f87171;")
#         title.setAlignment(Qt.AlignCenter)
#         layout.addWidget(title)

#         sep1 = QFrame()
#         sep1.setFrameShape(QFrame.HLine)
#         sep1.setStyleSheet("background: #475569; max-height: 2px;")
#         layout.addWidget(sep1)

#         # Active Alarms Section
#         lbl_active = QLabel("ALARMAS ACTIVAS")
#         lbl_active.setStyleSheet("""
#             font-size: 32px; 
#             font-weight: bold; 
#             color: #ef4444; 
#             background: transparent;
#             padding: 8px 0;
#         """)
#         layout.addWidget(lbl_active)

#         self.active_alarms_display = QTextEdit()
#         self.active_alarms_display.setReadOnly(True)
#         self.active_alarms_display.setStyleSheet("""
#             QTextEdit {
#                 background: #1e293b;
#                 color: #fef2f2;
#                 font-family: Consolas, 'Courier New', monospace;
#                 font-size: 20px;
#                 border: 2px solid #7f1d1d;
#                 border-radius: 10px;
#                 padding: 16px;
#             }
#         """)
#         self.active_alarms_display.setMinimumHeight(220)
#         layout.addWidget(self.active_alarms_display)

#         # Acknowledge All Button
#         btn_ack_all = QPushButton("RECONOCER TODAS")
#         btn_ack_all.setFixedSize(320, 60)
#         btn_ack_all.setStyleSheet("""
#             QPushButton {
#                 background: #dc2626;
#                 color: white;
#                 font-size: 22px;
#                 font-weight: bold;
#                 border-radius: 12px;
#             }
#             QPushButton:hover { background: #b91c1c; }
#             QPushButton:pressed { background: #991b1b; }
#             QPushButton:disabled { background: #334155; color: #64748b; }
#         """)
#         btn_ack_all.clicked.connect(self.acknowledge_all_alarms)
#         layout.addWidget(btn_ack_all, alignment=Qt.AlignRight)

#         sep2 = QFrame()
#         sep2.setFrameShape(QFrame.HLine)
#         sep2.setStyleSheet("background: #475569; max-height: 2px;")
#         layout.addWidget(sep2)

#         # Event History Section
#         lbl_history = QLabel("HISTORIAL COMPLETO")
#         lbl_history.setStyleSheet("""
#             font-size: 26px; 
#             font-weight: bold; 
#             color: #94a3b8;
#         """)
#         layout.addWidget(lbl_history)

#         self.history_display = QTextEdit()
#         self.history_display.setReadOnly(True)
#         self.history_display.setStyleSheet("""
#             QTextEdit {
#                 background: #0f172a;
#                 color: #cbd5e1;
#                 font-family: Consolas, monospace;
#                 font-size: 17px;
#                 border: none;
#                 padding: 8px;
#             }
#         """)

#         scroll_area = QScrollArea()
#         scroll_area.setWidget(self.history_display)
#         scroll_area.setWidgetResizable(True)
#         scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
#         scroll_area.setMinimumHeight(280)
#         layout.addWidget(scroll_area)

#         # Initial message
#         self._update_active_alarms_display()
#         self.history_display.append(
#             f'<span style="color:#64748b;">[Sistema iniciado — {QTime.currentTime().toString("hh:mm:ss")}]</span>'
#         )

#     def _sync_initial_state(self):
#         """Read current alarm states from AlarmSystem and populate active_alarms."""
#         if not all(hasattr(self.alarm_system, attr) for attr in 
#                    ['display_names', 'previous_states', 'severity_levels']):
#             print("AlarmsScreen: alarm_system missing expected attributes "
#                   "(display_names, previous_states, severity_levels)")
#             return

#         current_time = QTime.currentTime().toString("hh:mm:ss")
#         loaded_count = 0

#         for i, name in enumerate(self.alarm_system.display_names):
#             if i < len(self.alarm_system.previous_states) and self.alarm_system.previous_states[i]:
#                 level = (self.alarm_system.severity_levels[i] 
#                          if i < len(self.alarm_system.severity_levels) else "info")
#                 value = None  # Could fetch from self.values if tag is mapped
#                 self.active_alarms[name] = (value, level, current_time)
#                 loaded_count += 1

#         print(f"AlarmsScreen: initial sync → {loaded_count} active alarms loaded")
#         self._update_active_alarms_display()

#     def on_alarm_changed(self, idx, is_active, value, name, level, limits):
#         current_time = QTime.currentTime().toString("hh:mm:ss")

#         if is_active:
#             self.active_alarms[name] = (value, level, current_time)
#         else:
#             self.active_alarms.pop(name, None)

#         self._update_active_alarms_display()
#         self._append_to_history(name, value, level, is_active, current_time)

#     def on_new_event(self, event_msg, value, timestamp):
#         self._append_to_history(event_msg, value, "info", True, timestamp)

#     def _update_active_alarms_display(self):
#         if not self.active_alarms:
#             html = '<center><span style="color:#94a3b8; font-size:20px;">Ninguna alarma activa en este momento</span></center>'
#         else:
#             priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
#             sorted_alarms = sorted(
#                 self.active_alarms.items(),
#                 key=lambda item: priority_map.get(item[1][1], 0),
#                 reverse=True
#             )

#             lines = []
#             for name, (value, level, time_str) in sorted_alarms:
#                 color_map = {
#                     "rojo": "#f87171",
#                     "naranja": "#fb923c",
#                     "amarillo": "#fbbf24",
#                     "cian": "#22d3ee",
#                     "info": "#94a3b8"
#                 }
#                 color = color_map.get(level, "#cbd5e1")

#                 value_str = f"  {value:.1f}" if value is not None else ""
#                 line = (
#                     f'<span style="color:{color}; font-weight:bold; font-size:21px;">'
#                     f'[{time_str}]  {name.upper()}{value_str}</span>'
#                     f'<span style="color:#64748b; font-size:18px;">  — {level.upper()}</span>'
#                 )
#                 lines.append(line)

#             html = "<br>".join(lines)

#         self.active_alarms_display.setHtml(html)

#     def _append_to_history(self, text, value, level, is_active, time_str):
#         color_map = {
#             "rojo": "#f87171",
#             "naranja": "#fb923c",
#             "amarillo": "#fbbf24",
#             "cian": "#22d3ee",
#             "info": "#94a3b8"
#         }
#         color = color_map.get(level, "#94a3b8")

#         if level == "info":
#             status = ""
#             value_str = ""
#         else:
#             status = "ACTIVADA" if is_active else "DESACTIVADA"
#             value_str = f" ({value:.1f})" if value is not None and value != 0 else ""

#         line = (
#             f'<span style="color:#64748b;">[{time_str}]</span> '
#             f'<span style="color:{color}; font-weight:bold;">'
#             f'{status} {text}{value_str}</span>'
#         )

#         self.history_display.append(line)
#         self.history_display.verticalScrollBar().setValue(
#             self.history_display.verticalScrollBar().maximum()
#         )

#     def acknowledge_all_alarms(self):
#         if not self.active_alarms:
#             QMessageBox.information(self, "Información", "No hay alarmas activas.")
#             return

#         reply = QMessageBox.question(
#             self, "Confirmar",
#             "¿Reconocer TODAS las alarmas activas?",
#             QMessageBox.Yes | QMessageBox.No, QMessageBox.No
#         )

#         if reply == QMessageBox.Yes:
#             self.active_alarms.clear()
#             self._update_active_alarms_display()
#             current_time = QTime.currentTime().toString("hh:mm:ss")
#             self._append_to_history(
#                 "Todas las alarmas reconocidas por el usuario",
#                 None, "info", True, current_time
#             )
#             QMessageBox.information(self, "Listo", "Alarmas reconocidas.")

#     def update_values(self, values_dict):
#         """Compatibility method called from main window."""
#         self.values = values_dict
#         # Not directly used here, but kept for interface consistency

#     # Note: The write_setpoint method seems unrelated to alarms screen.
#     #       If it's not used here, consider moving it to a more appropriate screen
#     #       (e.g. therapy_config_screen or options_screen).
#     #       For now, it's kept commented out or removed unless you confirm it's needed.