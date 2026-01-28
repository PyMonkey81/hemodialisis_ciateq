# gui/service/mManualScr.py

# ... (tus imports siguen igual) ...
from gui.components.time_numpad_modal import TimeNumpadDialog # Asegúrate de importar esto

# ... (clases ClickableLineEdit, ValveCard, etc. siguen igual) ...

class mManualScr(QWidget):
    # ... (__init__ sigue igual) ...

    # ----------------------------------------------------------------------
    # CLASE AUXILIAR INTERNA
    # Sirve para "engañar" a escribir_setpoint simulando ser un QLineEdit
    # ----------------------------------------------------------------------
    class TempInput:
        def __init__(self, valor):
            self.valor = valor
        def text(self):
            return str(self.valor)
        def clearFocus(self):
            pass 
        def setText(self, t):
            pass

    def setup_ui(self):
        # ... (inicio de setup_ui sigue igual) ...
        
        # ==================================================================
        # EJEMPLO 1: TIEMPO DE TERAPIA (REEMPLAZANDO LO QUE TENÍAS)
        # ==================================================================
        # Antes tenías input_horas y input_mins separados. 
        # Ahora usamos uno solo para HH:MM.
        
        # TIEMPOS
        lbl_tiempo = QLabel("T. Terapia:")
        lbl_tiempo.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;")
        grid.addWidget(lbl_tiempo, 0, 10)

        self.input_tiempo_terapia = ClickableLineEdit("00:00")
        self.input_tiempo_terapia.setFixedSize(120, 35) 
        self.input_tiempo_terapia.setStyleSheet("""
            QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
                        font-weight: bold; border-radius: 5px; padding: 2px; }
        """)
        self.input_tiempo_terapia.setAlignment(Qt.AlignCenter)
        self.input_tiempo_terapia.setReadOnly(True)

        # CONEXIÓN GENÉRICA:
        # Le decimos: "Cuando hagas clic, abre el numpad. 
        # Si cambias el valor, manda las HORAS a 'heparineTherapyHours' 
        # y los MINUTOS a 'heparineTherapyMinutes'".
        self.input_tiempo_terapia.clicked.connect(
            lambda: self.open_time_numpad_split(
                self.input_tiempo_terapia, 
                tag_hours="heparineTherapyHours", 
                tag_minutes="heparineTherapyMinutes",
                title="Duración Terapia"
            )
        )
        
        grid.addWidget(self.input_tiempo_terapia, 0, 11, 1, 3) # Ocupa 3 columnas


        # ==================================================================
        # EJEMPLO 2: APLICANDO LO MISMO A 'Tiempo Op. BD' (B. Dializante)
        # ==================================================================
        # Buscamos donde defines self.lbl_tiempo_OpBD (Fila 3) y lo cambiamos:
        
        # ... (código de setup_ui anterior...) ...
        
        # FILA 3: B. DIALIZANTE
        # ... (toggles y etiquetas anteriores) ...
        
        lbl_e_tOpBD = QLabel("Tiempo Op.")
        lbl_e_tOpBD.setStyleSheet("color: #000000; font-size: 18px; font-weight: bold;")
        lbl_e_tOpBD.setFixedSize(100,35)
        grid.addWidget(lbl_e_tOpBD, 3, 4)

        # CAMBIO: Usamos ClickableLineEdit en lugar de QLineEdit normal
        self.lbl_tiempo_OpBD = ClickableLineEdit("00:00") 
        self.lbl_tiempo_OpBD.setStyleSheet("""
            QLineEdit { background: #ffffff; color: #000000; font-size: 18px; 
                        font-weight: bold; border-radius: 5px; padding: 2px; }
        """)
        self.lbl_tiempo_OpBD.setFixedSize(100,35)
        self.lbl_tiempo_OpBD.setAlignment(Qt.AlignCenter)
        self.lbl_tiempo_OpBD.setReadOnly(True)
        
        # CONEXIÓN GENÉRICA PARA ESTE CAMPO:
        # Aquí debes poner los TAGS reales que controlan el timer de la bomba de dializante.
        # Estoy inventando los nombres (ej: 'dialyserTimerHours'), cámbialos por los tuyos.
        self.lbl_tiempo_OpBD.clicked.connect(
            lambda: self.open_time_numpad_split(
                self.lbl_tiempo_OpBD, 
                tag_hours="dialyserTimerHours",    # <--- PON TU TAG DE HORAS AQUÍ
                tag_minutes="dialyserTimerMinutes", # <--- PON TU TAG DE MINUTOS AQUÍ
                title="Tiempo Op. Dializante"
            )
        )
        
        grid.addWidget(self.lbl_tiempo_OpBD,3,5)

        # ... (Repite esto para self.lbl_tiempo_opBUF en la fila 4, etc.) ...
        
        # ... (Resto de setup_ui) ...


    # ----------------------------------------------------------------------
    # TUS FUNCIONES EXISTENTES (escribir_setpoint, etc.) SE QUEDAN IGUAL
    # ----------------------------------------------------------------------
    # ... (manajer_bomba_doble, escribir_setpoint, etc.) ...


    # ----------------------------------------------------------------------
    # NUEVA FUNCIÓN GENÉRICA PARA MANEJAR TIEMPOS HH:MM
    # ----------------------------------------------------------------------
    def open_time_numpad_split(self, widget_input, tag_hours=None, tag_minutes=None, title="Config. Tiempo"):
        """
        1. Abre el TimeNumpadDialog con el valor actual del widget.
        2. Al aceptar, actualiza el widget visual a "HH:MM".
        3. Desglosa Horas y Minutos y llama a escribir_setpoint por separado para cada uno.
        """
        # 1. Obtener texto actual "HH:MM"
        texto_actual = widget_input.text()
        
        # Creamos el diálogo
        dialog = TimeNumpadDialog(self, initial_hh_mm=texto_actual, title=title)

        if dialog.exec():
            # 2. Obtener valores separados
            h, m = dialog.get_hours_minutes()
            
            # 3. Actualizar la interfaz visual (UI)
            widget_input.setText(f"{h:02d}:{m:02d}")

            # 4. Enviar al sistema (PLC/Backend)
            # Usamos la clase interna TempInput para simular un widget y reutilizar escribir_setpoint
            
            if tag_hours:
                print(f"[SPLIT] Enviando horas ({h}) al tag: {tag_hours}")
                fake_widget_h = self.TempInput(h) 
                self.escribir_setpoint(tag_hours, fake_widget_h)

            if tag_minutes:
                print(f"[SPLIT] Enviando minutos ({m}) al tag: {tag_minutes}")
                fake_widget_m = self.TempInput(m)
                self.escribir_setpoint(tag_minutes, fake_widget_m)

    # (La función open_time_numpad antigua ya no la necesitas si usas esta nueva versión split)
