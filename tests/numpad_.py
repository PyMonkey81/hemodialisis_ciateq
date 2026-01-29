# # gui/service/mManualScr.py

# # ... (tus imports siguen igual) ...
# from gui.components.time_numpad_modal import TimeNumpadDialog # Asegúrate de importar esto

# # ... (clases ClickableLineEdit, ValveCard, etc. siguen igual) ...

# class mManualScr(QWidget):
#     # ... (__init__ sigue igual) ...

#     # ----------------------------------------------------------------------
#     # CLASE AUXILIAR INTERNA
#     # Sirve para "engañar" a escribir_setpoint simulando ser un QLineEdit
#     # ----------------------------------------------------------------------
#     class TempInput:
#         def __init__(self, valor):
#             self.valor = valor
#         def text(self):
#             return str(self.valor)
#         def clearFocus(self):
#             pass 
#         def setText(self, t):
#             pass

#     def setup_ui(self):
#         # ... (inicio de setup_ui sigue igual) ...
        
#         # ==================================================================
#         # EJEMPLO 1: TIEMPO DE TERAPIA (REEMPLAZANDO LO QUE TENÍAS)
#         # ==================================================================
#         # Antes tenías input_horas y input_mins separados. 
#         # Ahora usamos uno solo para HH:MM.
        
#         # TIEMPOS
#         lbl_tiempo = QLabel("T. Terapia:")
#         lbl_tiempo.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;")
#         grid.addWidget(lbl_tiempo, 0, 10)

#         self.input_tiempo_terapia = ClickableLineEdit("00:00")
#         self.input_tiempo_terapia.setFixedSize(120, 35) 
#         self.input_tiempo_terapia.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
#                         font-weight: bold; border-radius: 5px; padding: 2px; }
#         """)
#         self.input_tiempo_terapia.setAlignment(Qt.AlignCenter)
#         self.input_tiempo_terapia.setReadOnly(True)

#         # CONEXIÓN GENÉRICA:
#         # Le decimos: "Cuando hagas clic, abre el numpad. 
#         # Si cambias el valor, manda las HORAS a 'heparineTherapyHours' 
#         # y los MINUTOS a 'heparineTherapyMinutes'".
#         self.input_tiempo_terapia.clicked.connect(
#             lambda: self.open_time_numpad_split(
#                 self.input_tiempo_terapia, 
#                 tag_hours="heparineTherapyHours", 
#                 tag_minutes="heparineTherapyMinutes",
#                 title="Duración Terapia"
#             )
#         )
        
#         grid.addWidget(self.input_tiempo_terapia, 0, 11, 1, 3) # Ocupa 3 columnas


#         # ==================================================================
#         # EJEMPLO 2: APLICANDO LO MISMO A 'Tiempo Op. BD' (B. Dializante)
#         # ==================================================================
#         # Buscamos donde defines self.lbl_tiempo_OpBD (Fila 3) y lo cambiamos:
        
#         # ... (código de setup_ui anterior...) ...
        
#         # FILA 3: B. DIALIZANTE
#         # ... (toggles y etiquetas anteriores) ...
        
#         lbl_e_tOpBD = QLabel("Tiempo Op.")
#         lbl_e_tOpBD.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;")
#         lbl_e_tOpBD.setFixedSize(100,35)
#         grid.addWidget(lbl_e_tOpBD, 3, 4)

#         # CAMBIO: Usamos ClickableLineEdit en lugar de QLineEdit normal
#         self.lbl_tiempo_OpBD = ClickableLineEdit("00:00") 
#         self.lbl_tiempo_OpBD.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
#                         font-weight: bold; border-radius: 5px; padding: 2px; }
#         """)
#         self.lbl_tiempo_OpBD.setFixedSize(100,35)
#         self.lbl_tiempo_OpBD.setAlignment(Qt.AlignCenter)
#         self.lbl_tiempo_OpBD.setReadOnly(True)
        
#         # CONEXIÓN GENÉRICA PARA ESTE CAMPO:
#         # Aquí debes poner los TAGS reales que controlan el timer de la bomba de dializante.
#         # Estoy inventando los nombres (ej: 'dialyserTimerHours'), cámbialos por los tuyos.
#         self.lbl_tiempo_OpBD.clicked.connect(
#             lambda: self.open_time_numpad_split(
#                 self.lbl_tiempo_OpBD, 
#                 tag_hours="dialyserTimerHours",    # <--- PON TU TAG DE HORAS AQUÍ
#                 tag_minutes="dialyserTimerMinutes", # <--- PON TU TAG DE MINUTOS AQUÍ
#                 title="Tiempo Op. Dializante"
#             )
#         )
        
#         grid.addWidget(self.lbl_tiempo_OpBD,3,5)

#         # ... (Repite esto para self.lbl_tiempo_opBUF en la fila 4, etc.) ...
        
#         # ... (Resto de setup_ui) ...


#     # ----------------------------------------------------------------------
#     # TUS FUNCIONES EXISTENTES (escribir_setpoint, etc.) SE QUEDAN IGUAL
#     # ----------------------------------------------------------------------
#     # ... (manajer_bomba_doble, escribir_setpoint, etc.) ...


#     # ----------------------------------------------------------------------
#     # NUEVA FUNCIÓN GENÉRICA PARA MANEJAR TIEMPOS HH:MM
#     # ----------------------------------------------------------------------
#     def open_time_numpad_split(self, widget_input, tag_hours=None, tag_minutes=None, title="Config. Tiempo"):
#         """
#         1. Abre el TimeNumpadDialog con el valor actual del widget.
#         2. Al aceptar, actualiza el widget visual a "HH:MM".
#         3. Desglosa Horas y Minutos y llama a escribir_setpoint por separado para cada uno.
#         """
#         # 1. Obtener texto actual "HH:MM"
#         texto_actual = widget_input.text()
        
#         # Creamos el diálogo
#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

#         if dialog.exec():
#             # 2. Obtener valores separados
#             h, m = dialog.get_hours_minutes()
            
#             # 3. Actualizar la interfaz visual (UI)
#             widget_input.setText(f"{h:02d}:{m:02d}")

#             # 4. Enviar al sistema (PLC/Backend)
#             # Usamos la clase interna TempInput para simular un widget y reutilizar escribir_setpoint
            
#             if tag_hours:
#                 print(f"[SPLIT] Enviando horas ({h}) al tag: {tag_hours}")
#                 fake_widget_h = self.TempInput(h) 
#                 self.escribir_setpoint(tag_hours, fake_widget_h)

#             if tag_minutes:
#                 print(f"[SPLIT] Enviando minutos ({m}) al tag: {tag_minutes}")
#                 fake_widget_m = self.TempInput(m)
#                 self.escribir_setpoint(tag_minutes, fake_widget_m)

#     # (La función open_time_numpad antigua ya no la necesitas si usas esta nueva versión split)



#         # ... (código anterior de input_t_BloodPump) ...
#         self.input_t_BloodPump.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_BloodPump,
#                 tag_hours=None,        # No envía a PLC
#                 tag_minutes=None,      # No envía a PLC
#                 local_timer_id="op_pb", # Identificador para timer local
#                 title="Tiempo de operación de bomba de sangre"
#             )
#         )
#         grid.addWidget(self.input_t_BloodPump, 0, 11, 1, 3)


#         # ... (Cerca de donde está input_t_therapy) ...
        
#         # FILA 2: DOSIS HEPARINA (Input)
#         # ... (lbl_dosis, input_dosis_hep, lbl_udosis_hep, etc.) ...

#         # T. Terapia (que va al PLC)
#         lbl_t_therapy = QLabel("T. Terapia")
#         lbl_t_therapy.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_therapy, 2, 9)

#         self.input_t_therapy = ClickableLineEdit("00:00")
#         self.input_t_therapy.setFixedSize(120, 35)
#         self.input_t_therapy.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px;
#                         font-weight: bold; border-radius: 5px; padding: 2px;}
#         """)
#         self.input_t_therapy.setAlignment(Qt.AlignCenter)
#         self.input_t_therapy.setReadOnly(True)

#         self.input_t_therapy.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_therapy,
#                 tag_hours="heparineTherapyHours", 
#                 tag_minutes="heparineTherapyMinutes",
#                 local_timer_id=None, # No es un timer local de app
#                 title="Tiempo de terapia"
#             )
#         )
#         grid.addWidget(self.input_t_therapy, 2, 10) # <--- Ocupa solo la columna 10


#         # --- NUEVO: T. Op. Heparina (Timer de operación manual de bomba) ---
#         lbl_t_op_ph = QLabel("T. Op. Bh:") # "Tiempo Op. Bomba Heparina"
#         lbl_t_op_ph.setStyleSheet(style_lbl)
#         grid.addWidget(lbl_t_op_ph, 2, 11)

#         self.input_t_HeparinPump = ClickableLineEdit("00:00")
#         self.input_t_HeparinPump.setFixedSize(120, 35)
#         self.input_t_HeparinPump.setStyleSheet("""
#             QLineEdit { background: #ffffff; color: #000000; font-size: 18px;
#                         font-weight: bold; border-radius: 5px; padding: 2px;}
#         """)
#         self.input_t_HeparinPump.setAlignment(Qt.AlignCenter)
#         self.input_t_HeparinPump.setReadOnly(True)

#         self.input_t_HeparinPump.clicked.connect(
#             lambda: self.open_time_numpad(
#                 self.input_t_HeparinPump,
#                 tag_hours=None,
#                 tag_minutes=None,
#                 local_timer_id="op_ph", # Identificador para timer local
#                 title="Tiempo de operación bomba heparina"
#             )
#         )
#         grid.addWidget(self.input_t_HeparinPump, 2, 12, 1, 2) # Ocupa columnas 12 y 13 para ajustarse



#     def open_time_numpad(self, widget_input, tag_hours=None, tag_minutes=None, local_timer_id=None, title="Config. Tiempo"):
#         """
#         1. Abre el TimeNumpadDialog con el valor actual del widget.
#         2. Al aceptar, actualiza el widget visual a "HH:MM".
#         3. Desglosa Horas y Minutos.
#         4. Si tiene tags, llama a escribir_setpoint para el PLC.
#         5. Si tiene local_timer_id, configura el QTimer correspondiente.
#         """
#         texto_actual = widget_input.text()
#         dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

#         if dialog.exec():
#             h, m = dialog.get_hours_minutes()
#             widget_input.setText(f"{h:02d}:{m:02d}")
            
#             # Calcular duración total en milisegundos
#             total_ms = (h * 3600 + m * 60) * 1000

#             # 1. Lógica para escribir al PLC (si se proporcionaron tags)
#             if tag_hours and tag_minutes:
#                 print(f"[PLC_WRITE] Enviando horas ({h}) al tag: {tag_hours}")
#                 fake_widget_h = TempInput(h) 
#                 self.escribir_setpoint(tag_hours, fake_widget_h)

#                 print(f"[PLC_WRITE] Enviando minutos ({m}) al tag: {tag_minutes}")
#                 fake_widget_m = TempInput(m)
#                 self.escribir_setpoint(tag_minutes, fake_widget_m)
#             elif tag_hours or tag_minutes: # Solo como aviso, esto no debería pasar si la lógica es correcta
#                 print(f"[WARNING] Se proporcionó un solo tag de tiempo (H:{tag_hours}, M:{tag_minutes}) para escribir al PLC. Se necesita ambos para escribir.")

#             # 2. Lógica para configurar QTimer locales de la aplicación
#             if local_timer_id:
#                 timer_attr_name = f"timer_{local_timer_id}" # Ej: "timer_op_pb"
#                 total_ms_attr_name = f"_total_ms_{local_timer_id}" # Ej: "_total_ms_op_pb"
                
#                 # Acceder al QTimer y a la variable de duración usando getattr/setattr
#                 timer_obj = getattr(self, timer_attr_name)
#                 setattr(self, total_ms_attr_name, total_ms) # Guardar la duración total

#                 print(f"[APP_TIMER] {local_timer_id} configurado con {h:02d}:{m:02d} ({total_ms} ms)")
                
#                 # Opcional: Mostrar algún feedback de que el timer está listo
#                 # widget_input.setStyleSheet(style_input + "border: 2px solid green;") 



#     def manejar_bomba_doble(self, tag_start, tag_stop, activado, timer_id=None):
#         if activado:
#             print(f"[BOMBA] Arrancando {tag_start}")
#             self.escribir_comando(tag_start, True)
#             self.escribir_comando(tag_stop, False) 
            
#             # --- NUEVO: Iniciar timer si existe y se configuró un tiempo ---
#             if timer_id:
#                 timer_obj = getattr(self, f"timer_{timer_id}")
#                 total_ms_duration = getattr(self, f"_total_ms_{timer_id}")
                
#                 if total_ms_duration > 0:
#                     timer_obj.start(total_ms_duration)
#                     print(f"[APP_TIMER] Iniciando timer '{timer_id}' por {total_ms_duration} ms.")
#                 else:
#                     print(f"[APP_TIMER] Advertencia: Timer '{timer_id}' no tiene duración establecida (0 ms). No se inició.")

#         else: # Bomba desactivada
#             print(f"[BOMBA] Deteniendo {tag_start} (Triggering Stop {tag_stop})")
#             self.escribir_comando(tag_stop, True) 
#             self.escribir_comando(tag_start, False)
            
#             # --- NUEVO: Detener timer si está corriendo ---
#             if timer_id:
#                 timer_obj = getattr(self, f"timer_{timer_id}")
#                 if timer_obj.isActive():
#                     timer_obj.stop()
#                     print(f"[APP_TIMER] Deteniendo timer '{timer_id}'.")
