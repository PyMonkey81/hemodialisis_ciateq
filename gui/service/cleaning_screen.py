# gui/service/cleaning_screen.py
# Cleaning / Disinfection screen (stacked index 3)


"""
Módulo para la pantalla de control del ciclo de limpieza y desinfección.

"""

from PySide6.QtWidgets import (
     QMessageBox, QWidget, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, Signal
import logging
import json
import os
from logic.calculos import convertir_flujo_a_ciclos 
from gui.components.floating_confirm import FloatingConfirmDialog

logger = logging.getLogger(__name__)

# Definimos la ruta del archivo de configuración (igual que en la otra pantalla)
# Es crucial que esta ruta sea la misma que la de cleanning_config_screen.py
CONFIG_FILE_PATH = "config/cleaning_config.json" 


class CleaningScreen(QWidget):
    request_setpoint_change = Signal(str, float)
    request_boolean_change = Signal(str, bool)
    cleaning_active_changed = Signal(bool) # NUEVO: Señal para comunicar el estado de limpieza

    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_values = values_dict if values_dict is not None else {}

        self.cleaning_in_progress = False
        self.mid_pause_done = False # NUEVO: Para controlar la pausa intermedia en limpieza larga
        # self.timer_started = False
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #0f172a;")

        self.current_phase = "Esperando condiciones..."
        self.total_time_seconds = 0
        self.remaining_time_seconds = 0        
        self.selected_mode = None # Almacena el modo seleccionado (0.0 o 1.0)

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)

        self.setup_ui() 
        self._load_initial_config_on_startup() 
        

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(30)

        title_label = QLabel("Limpieza / Desinfección")
        title_label.setStyleSheet("color: #cbd5e1; font-size: 52px; font-weight: bold; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # ── Frame para Selección de Modo ─────────────────────────────────────────
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #fcfcfc; border-radius: 10px; padding: 15px;")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setSpacing(20)

        self.btn_mode_group = QButtonGroup(self)
        self.btn_mode_group.setExclusive(True)

        self.btn_short = QPushButton("Desinfección Química Corta")
        self.btn_long = QPushButton("Desinfección Química Larga")

        self.style_unchecked = """
            QPushButton {
                background: #3b82f6; color: white; font-size: 24px; font-weight: bold;
                border-radius: 12px; padding: 15px; border: 2px solid #2563eb;
            }
            QPushButton:hover { background: #60a5fa; }
        """
        self.style_checked = """
            QPushButton {
                background: #22c55e; color: white; font-size: 24px; font-weight: bold;
                border-radius: 12px; padding: 15px; border: 2px solid #16a34a;
            }
        """

        for btn, mode_val in [(self.btn_short, 0.0), (self.btn_long, 1.0)]:
            btn.setStyleSheet(self.style_unchecked)
            btn.setCheckable(True)
            btn.toggled.connect(lambda checked, b=btn, val=mode_val: self._on_mode_toggled(b, val, checked))
            mode_layout.addWidget(btn)
            self.btn_mode_group.addButton(btn)

        main_layout.addWidget(mode_frame)

        # ── Current Phase / Status ───────────────────────────────────────────────
        self.phase_label = QLabel(self.current_phase)
        self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold; background: transparent; min-height: 60px;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.phase_label)

        # ── Progress Bar ─────────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m seg")
        self.progress_bar.setFixedHeight(60)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b; border: 2px solid #475569; border-radius: 10px;
                text-align: center; color: #ffffff; font-size: 24px; font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # ── Remaining Time ───────────────────────────────────────────────────────
        self.time_label = QLabel("Tiempo configurado: --:--")
        self.time_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
        self.time_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.time_label)

        self.temp_label = QLabel("Temperatura configurada: 0.0 °C")
        self.temp_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.temp_label)

        self.flow_label = QLabel("Flujo configurado: 0.0 ml/min")
        self.flow_label.setStyleSheet("color: #cbd5e1; font-size: 28px; font-weight: bold; background: transparent;")
        self.flow_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.flow_label)

        main_layout.addStretch()

        # ── Start / Stop Buttons ───────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("Iniciar")
        self.start_button.setFixedSize(300, 100)
        self.start_button.setEnabled(False)  
        self.start_button.setProperty("base_color", "#047857")         
        self.start_button.setStyleSheet("""
            QPushButton {
                background: #047857; color: white; font-size: 38px; font-weight: bold;
                border: none; border-radius: 16px; padding: 10px;
            }
            QPushButton:hover { background: #065f46; }
            QPushButton:pressed { background: #064e3b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        self.start_button.clicked.connect(self._start_cleaning)
        button_layout.addWidget(self.start_button)

        # === Botón de Detener Limpieza ===
        self.stop_button = QPushButton("Detener")
        self.stop_button.setFixedSize(300, 100)
        self.stop_button.setEnabled(False) # Inicialmente deshabilitado
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: #dc2626; color: white; font-size: 38px; font-weight: bold;
                border: none; border-radius: 16px; padding: 10px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        self.stop_button.clicked.connect(self._stop_cleaning)
        button_layout.addWidget(self.stop_button)
        # ========================================

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Initial UI state
        self.phase_label.setText("Esperando estado listo...")
        self.progress_bar.setValue(0)
        self.progress_timer.stop()

    def _handle_cb_flow_input(self, value: float):
        if value is None: return 
        flow_ml_min = value 
        print(f"Valor de flujo recibido para conversión: {flow_ml_min} ml/min")

        try: 
            cycles_value = convertir_flujo_a_ciclos(flow_ml_min)
            tag = "balanceChamberSetTiming"
            self.on_user_input_setpoint(tag, cycles_value)
            print(f"Flujo enviado correctamente: {cycles_value}")

        except Exception as e:
            logger.error(f"Error al convertir flujo en ciclos máquina: {e}")

    def _load_initial_config_on_startup(self):
        """
        Carga la última configuración guardada al iniciar la pantalla
        y simula la selección del botón correspondiente.
        """
        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error al cargar configuración inicial desde JSON: {e}")
        
        saved_mode_value = config_data.get("last_active_mode_value", 0.0)
        
        # --- Inicializar todas las variables por defecto ---
        hours = 0
        minutes = 15
        temp = 35.0
        flow = 100.0 # Valor por defecto para flujo
        # ----------------------------------------------------

        mode_config = config_data.get("modes", {}).get(str(saved_mode_value))
        if mode_config:
            hours = mode_config.get("time_hours", 0)
            minutes = mode_config.get("time_minutes", 15)
            temp = mode_config.get("mode_temp", 35.0)
            flow = mode_config.get("mode_flow", 100.0) # Obtener flow, con valor por defecto
            
        self.time_label.setText(f"Tiempo configurado: {hours:02d}:{minutes:02d}")
        self.temp_label.setText(f"Temperatura configurada: {temp:.1f} °C")
        self.flow_label.setText(f"Flujo configurado: {flow:.1f} ml/min")
        

        # Simular el clic en el botón correcto para cargar el tiempo
        if saved_mode_value == 0.0:
            self.btn_short.setChecked(True) # Esto activará _on_mode_toggled
        elif saved_mode_value == 1.0:
            self.btn_long.setChecked(True) # Esto activará _on_mode_toggled
        else:
             self.btn_short.setChecked(True) # Si el valor no es válido, por defecto el corto


    def _on_mode_toggled(self, button, mode_value, checked):
        """Maneja la selección del modo, carga el JSON y envía los tags"""
        if checked:
            button.setStyleSheet(self.style_checked)
            self.selected_mode = mode_value
            self._load_mode_specific_configuration(mode_value) # Carga la configuración específica del modo
        else:
            button.setStyleSheet(self.style_unchecked)

    def _load_mode_specific_configuration(self, mode_value: float):
        """
        Carga el tiempo desde JSON para el modo específico,
        actualiza la UI y envía los tags al controlador.
        """
        # --- Inicializar todas las variables por defecto ---
        hours, minutes = 0, 15 # Valores por defecto (15 min)
        _temp = 35.0 
        _flow = 100.0 # Valor por defecto para flujo
        # ----------------------------------------------------

        config_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error al leer JSON de limpieza para modo {mode_value}: {e}")

        # Intentar obtener la configuración para el modo específico
        mode_config = config_data.get("modes", {}).get(str(mode_value))
        print(f"Configuración cargada para modo {mode_value}: {mode_config}")
        if mode_config:
            hours = mode_config.get("time_hours", 0)
            minutes = mode_config.get("time_minutes", 15)
            _temp = mode_config.get("mode_temp", 35.0)
            _flow = mode_config.get("mode_flow", 100.0)
        
        # Calcular total en segundos
        self.total_time_seconds = (hours * 3600) + (minutes * 60)
        self.remaining_time_seconds = self.total_time_seconds
        
        # Escribir los valores solicitados al controlador
        self.on_user_input_setpoint("heparineTherapyHours", float(hours))
        self.on_user_input_setpoint("heparineTherapyMinutes", float(minutes))
        self.on_user_input_setpoint("dialyTempControlSetPoint", float(_temp))
        self._handle_cb_flow_input(_flow)
        # Actualizar UI
        self.time_label.setText(f"Tiempo configurado: {hours:02d}:{minutes:02d}")
        self.temp_label.setText(f"Temperatura configurada: {_temp:.1f} °C")
        self.flow_label.setText(f"Flujo configurado: {_flow:.1f} ml/min")
        self.progress_bar.setMaximum(self.total_time_seconds)
        self.progress_bar.setValue(0)
        logger.info(f"Modo {mode_value} cargado. Tiempo: {hours}h {minutes}m. Escrito a controlador.")

    def _start_cleaning(self):
        """Inicia el ciclo de limpieza (envía comandos)"""
        if self.selected_mode is None:
            self.parent_window.show_warning_message("Seleccione un modo de desinfección", 2000)
            return
        
        self._load_mode_specific_configuration(self.selected_mode) # Asegura que la configuración esté cargada
        self.cleaning_in_progress = True
        self.mid_pause_done = False # Reiniciar el estado de la pausa intermedia
        self.cleaning_active_changed.emit(True)

        try:
            self.on_user_input_setpoint("treatmentModeSelection", 3.0)
            self.on_user_boolean_command("dialyStartDialysisButt", True)
            self.on_user_boolean_command("dialyStopDialysisButt", False)
        
            self.parent_window.show_info_message("Iniciando ciclo de limpieza...", 1000)
        
            self.current_phase = "Preparando sistema..."
            self.phase_label.setText(self.current_phase)
            self.phase_label.setStyleSheet("color: #facc15; font-size: 32px; font-weight: bold;")  # Amarillo

            self.start_button.setEnabled(False)
            self.start_button.setText("En proceso...")
            self.stop_button.setEnabled(True)
        
        except Exception as e:
            logger.error(f"Error al iniciar limpieza: {e}")
            self.parent_window.show_error_message(f"Error: {e}", 2000)



    def _stop_cleaning(self):
        """Detiene el ciclo de limpieza de forma manual."""
        logger.info("Deteniendo ciclo de limpieza manualmente.")
        # Se llama a reset_ui() que también establece cleaning_in_progress = False
        self.reset_ui() # CAMBIO: Llama a reset_ui() para reiniciar todo
        self.cleaning_active_changed.emit(False) # NUEVO: Emitir que la limpieza ha terminado

        try:
            # Enviar comandos para detener la operación
            self.on_user_boolean_command("dialyStartDialysisButt", False)  
            self.on_user_boolean_command("dialyStopDialysisButt", True)   
            self.parent_window.show_info_message("Cerrando sesión de limpieza...", 2000)
           
        except Exception as e:
            logger.error(f"Error al enviar comando de parada de limpieza: {e}") 

        self.current_phase = "Limpieza detenida por el usuario."
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #ef4444; font-size: 32px; font-weight: bold;") # Color rojo para detenido

        # Estos botones también se manejan en reset_ui(), pero aquí los confirmamos
        self.start_button.setText("Iniciar")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False) 

        logger.info("Ciclo de limpieza detenido y UI actualizada.")

  
    def reset_ui(self):
        """Reinicia la UI a estado inicial (esperando configuración)."""
        self.cleaning_in_progress = False
        self.progress_timer.stop()
        # self.timer_started = False
        self.mid_pause_done = False

        self.current_phase = "Esperando modo de limpieza..."
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")

        self.progress_bar.setValue(0)
        self.time_label.setText("Tiempo configurado: --:--")
        self.temp_label.setText("Temperatura configurada: 0.0 °C")
        self.flow_label.setText("Flujo configurado: 0.0 ml/min")

        # Botones
        self.start_button.setEnabled(False)
        self.start_button.setText("Iniciar")
        self.stop_button.setEnabled(False)

        # Reconectar señal del botón Iniciar
        try:
            self.start_button.clicked.disconnect()
        except TypeError:
            pass
        self.start_button.clicked.connect(self._start_cleaning)

        # Recargar última configuración guardada
        # self._load_initial_config_on_startup()
        self._load_mode_specific_configuration(self.selected_mode)

        logger.info("UI de limpieza reiniciada a estado inicial.")


    # def _update_progress(self):
    #     """Actualiza el progreso cada segundo"""
    #     if self.remaining_time_seconds > 0:
    #         self.remaining_time_seconds -= 1
    #         self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
    #         self._update_time_display()

    #         # === PAUSA EN LA MITAD DEL CICLO ===
    #         half_time = self.total_time_seconds // 2

    #         if (not self.mid_pause_done and 
    #             self.remaining_time_seconds <= half_time):
                
    #             self._pause_for_line_change()
    #             return  # Salimos para no seguir descontando hasta que continúe

    #     else:
    #         self.progress_timer.stop()
    #         self._finish_cleaning()

    def _update_progress(self):
        """Actualiza el progreso cada segundo"""
        if not self.cleaning_in_progress:
            return

        if self.remaining_time_seconds > 0:
            self.remaining_time_seconds -= 1
            self.progress_bar.setValue(self.total_time_seconds - self.remaining_time_seconds)
            self._update_time_display()

            # Pausa intermedia
            half_time = self.total_time_seconds // 2
            if (not self.mid_pause_done and 
                self.remaining_time_seconds <= half_time):            
                self._pause_for_line_change()
                return  #no seguir descontando
        else:
            self.progress_timer.stop()
            self._finish_cleaning()


    def _pause_for_line_change(self):
        """Pausa el proceso en la mitad para cambiar la línea"""
        self.mid_pause_done = True
        self.progress_timer.stop()   # Pausamos el timer

        self.current_phase = "Pausa: Cambiar línea"
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #f59e0b; font-size: 34px; font-weight: bold;")  # Naranja

        # Detener proceso en la máquina
        self.on_user_boolean_command("dialyStartDialysisButt", False)
        self.on_user_boolean_command("dialyStopDialysisButt", True)

        message = "Por favor, cambie la línea y luego presione Continuar para reanudar la limpieza."
        accept_text = "Continuar..."
        cancel_text = "Cancelar"
        # Mostrar confirmación
        if self._confirm_message(message, accept_text, cancel_text):
            self._resume_cleaning()        
        else:
            # Si cancela, detenemos todo
            self._stop_cleaning()
    

    def _confirm_message(self, message: str, accept_text: str, cancel_text: str) -> bool:
        """Muestra un mensaje de confirmación flotante y devuelve True si se acepta."""
        dialog = FloatingConfirmDialog(self)
        return dialog.show_confirm(message, accept_text=accept_text, cancel_text=cancel_text)
        
    def _update_time_display(self):
        """Format and display remaining time."""
        minutes = self.remaining_time_seconds // 60
        seconds = self.remaining_time_seconds % 60
        self.time_label.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

    def _resume_cleaning(self):
        """Reanuda el proceso después de cambiar la línea"""
        self.on_user_boolean_command("dialyStartDialysisButt", True)
        self.on_user_boolean_command("dialyStopDialysisButt", False)

        self.current_phase = "Desinfección química en curso..."
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #22c55e; font-size: 32px; font-weight: bold;")

        self.progress_timer.start(1000)  # Reanudar timer
        logger.info(f"Limpieza reanudada - Tiempo restante: {self.remaining_time_seconds} seg")

        

    def _finish_cleaning(self):
        """Handle cycle completion."""
        self.cleaning_in_progress = False
        self.cleaning_active_changed.emit(False) # NUEVO: Emitir que la limpieza ha terminado

        self.current_phase = "Limpieza completada"
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
        self.time_label.setText("Tiempo restante: 00:00")
        self.progress_bar.setValue(self.total_time_seconds) # Asegura que la barra llega al 100%
        
        try:                       
            self.on_user_boolean_command("dialyStartDialysisButt", False) # Asegurarse de que start está en False
            self.on_user_boolean_command("dialyStopDialysisButt", True) # Comando para detener la operación
            self.parent_window.show_info_message("Ciclo de limpieza completado.", 3000)
        except Exception as e:
            logger.error(f"Error al finalizar ciclo de limpieza: {e}")

        self.start_button.setText("Reiniciar")
        self.start_button.setEnabled(True) # Habilitar reiniciar
        self.stop_button.setEnabled(False) # Deshabilitar detener

        try:
            self.start_button.clicked.disconnect()
        except TypeError:
            pass
        self.start_button.clicked.connect(self.reset_ui)
        
    def update_values(self, new_values: dict):
        """Recibe actualizaciones desde el main window"""
        self.current_values = new_values
    
        treatment_mode = new_values.get("treatmentModeSelection", 0.0)
        priming_status = int(new_values.get("primingProcessStatus", 0))

        self.update_buttons_state(treatment_mode_selection=treatment_mode)

        # === LÓGICA CLAVE: Iniciar conteo solo cuando llegue al estado 7 ===
        if (self.cleaning_in_progress and 
            priming_status == 6 and 
            not self.progress_timer.isActive()):        
            self._start_progress_timer()
    
    def _start_progress_timer(self):
        """Inicia o reanuda el temporizador de progreso.
    
        IMPORTANTE: No reinicia el tiempo restante si ya se hizo la pausa intermedia.
        """
        # Solo resetear el tiempo la PRIMERA vez (inicio del ciclo)
        if not self.mid_pause_done:
            self.remaining_time_seconds = self.total_time_seconds
            self.progress_bar.setValue(0)
            logger.info(f"Iniciando temporizador desde cero: {self.total_time_seconds} segundos")
        else:
            logger.info(f"Reanudando temporizador - Tiempo restante: {self.remaining_time_seconds} segundos")

        # Configurar barra de progreso
        self.progress_bar.setMaximum(self.total_time_seconds)
    
        # Actualizar fase
        self.current_phase = "Desinfección química en curso..."
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #22c55e; font-size: 32px; font-weight: bold;")

        # Iniciar timer
        if not self.progress_timer.isActive():
            self.progress_timer.start(1000)
    
        self._update_time_display()
    
        logger.info(f"Temporizador iniciado (mid_pause_done={self.mid_pause_done})")
    def _start_progress_timer(self):
        """Inicia o reanuda el temporizador de progreso."""
        if not self.mid_pause_done:
            # Primera vez: iniciar desde el tiempo total
            self.remaining_time_seconds = self.total_time_seconds
            self.progress_bar.setValue(0)
            logger.info(f"Iniciando temporizador desde cero: {self.total_time_seconds} segundos")
        else:
            # Reanudando después de pausa
            logger.info(f"Reanudando temporizador - Tiempo restante: {self.remaining_time_seconds} seg")

        self.progress_bar.setMaximum(self.total_time_seconds)
    
        self.current_phase = "Desinfección química en curso..."
        self.phase_label.setText(self.current_phase)
        self.phase_label.setStyleSheet("color: #22c55e; font-size: 32px; font-weight: bold;")

        if not self.progress_timer.isActive():
            self.progress_timer.start(1000)
    
        self._update_time_display()
    
        logger.info(f"Temporizador {'iniciado' if not self.mid_pause_done else 'reanudado'} (mid_pause_done={self.mid_pause_done})")

    # def _start_progress_timer(self):
    #     """Inicia el temporizador y barra de progreso cuando el sistema está listo (estado 7)"""

    #     if not self.timer_started:
    #         self.remaining_time_seconds = self.total_time_seconds
    #         self.progress_bar.setValue(0)
    #         self.timer_started = True

    #     self.remaining_time_seconds = self.total_time_seconds
    #     self.progress_bar.setMaximum(self.total_time_seconds)
    #     self.progress_bar.setValue(0)
    
    #     self.current_phase = "Desinfección química en curso..."
    #     self.phase_label.setText(self.current_phase)
    #     self.phase_label.setStyleSheet("color: #22c55e; font-size: 32px; font-weight: bold;")  # Verde

    #     self.progress_timer.start(1000)  
    #     self._update_time_display()
    
    #     logger.info("Temporizador de limpieza iniciado (estado 6 alcanzado)")

    def update_buttons_state(self, treatment_mode_selection: float):
        """
        Habilita o deshabilita el botón de limpieza basado en el modo de tratamiento (treatmentModeSelection).
        """
 
        if self.cleaning_in_progress:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.start_button.setText("En proceso...")
            return

        style_disabled = """
            QPushButton {
                background: #334155; color: #64748b;
                font-size: 38px; font-weight: bold; border: none;
                border-radius: 16px; padding: 10px;
            }
        """
        def set_enabled_style(btn):
            color = btn.property("base_color")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: white;
                    font-size: 38px; font-weight: bold; border: none;
                    border-radius: 16px; padding: 10px;
                }}
                QPushButton:hover {{ background: #065f46; }}
                QPushButton:pressed {{ background: #064e3b; }}
            """)

        if treatment_mode_selection == 3.0:
            if not self.start_button.isEnabled():
                self.start_button.setEnabled(True)
                set_enabled_style(self.start_button)
                self.start_button.setText("Iniciar")
                self.stop_button.setEnabled(False) 
                
                self.current_phase = "Sistema listo para limpieza"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;")
        else: # Si el modo no es limpieza (3.0)
            if self.start_button.isEnabled() and self.start_button.text() != "Reiniciar":
                self.start_button.setEnabled(False)
                self.start_button.setStyleSheet(style_disabled)
                self.stop_button.setEnabled(False) 
                
                self.current_phase = f"Esperando modo limpieza (Actual: {treatment_mode_selection})"
                self.phase_label.setText(self.current_phase)
                self.phase_label.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;")
            elif self.start_button.text() == "Reiniciar":
                self.start_button.setEnabled(True)
                set_enabled_style(self.start_button)
                self.stop_button.setEnabled(False)

    def on_user_boolean_command(self, tag, state):
        self.request_boolean_change.emit(tag, state)

    def on_user_input_setpoint(self, tag, value):
        self.request_setpoint_change.emit(tag, value)
