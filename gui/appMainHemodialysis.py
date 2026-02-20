# gui/appMainHemodialisis.py

# import os
# import sys
# import time
# import logging
# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtGui import QColor, QPixmap

# # === MÓDULOS ===
# from core.alarmas import SistemaAlarmas
# from core.variables_map import VARIABLES

# from connection.comunicacion_serial import ComunicacionSerial
# from gui.therapy.main_screen import mainScr
# from gui.therapy.dialysis_screen import dialysisScr
# from gui.service.options_screen import optionScr
# from gui.service.cleaning_screen import cleanScr
# from gui.therapy.alarms_screen import alarmsScr
# from gui.components.real_time_variables import monitorVariables
# from gui.components.tank_gauge import TankGauge
# from gui.components.conductivity_bar import ConductivityBar


# from gui.service.manual_mode_screen import mManualScr #Pantalla modo manual 
# from gui.service.test_panel_screen import testScr #Pantalla panel de pruebas 
# from gui.service.calibration_screen import ctrlCfgScr #pantalla calibracion
# from gui.service.network_config_screen import cfgRedScr # pantalla configuracion de red

# from gui.therapy.patient_config_screen import patienCfgScr
# from gui.therapy.therapy_config_screen import therapyCfgScr

# logger = logging.getLogger(__name__)

# #===============================================================================
# #======================CODIGO PARA ADJUNTAR LOGOS EN EJECUTABLE=================
# #===============================================================================

# def resource_path(relative_path):
#     """Devuelve la ruta correcta tanto en desarrollo como en .exe"""
#     try:
#         # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)
# #===============================================================================


# class HemodialysisHMI(QMainWindow):
#     #INDEX DE PANTALLAS 
#     INDEX_INICIO = 0   

#     def __init__(self):
#         super().__init__()

#         # === DETECCIÓN DE ENTORNO DE PRUEBAS ===
#         # import os
#         # en_pruebas = os.getenv('PYTEST_VERSION') or 'pytest' in sys.modules
    
#         # if en_pruebas:
#         #     logger.error("[INFO] Modo pruebas detectado → puerto serial desactivado")
#         #     self.serial = None
#         #     self.conectado = False
#         # else:
#         #     self.serial = ComunicacionSerial(callback=self.actualizar_valor)
#         #     self.conectado = self.serial.conectar()
#         #     if self.conectado:
#         #         self.serial.iniciar_lectura()
       
#         # 1. Crear estructura visual (ventana, label y stacked)
#         self.setup_ui()
#         self.actualizar_label_pantalla("Inicio", "#000000")     # <-------------cambio de color para en un futuro hacer temas 
#         self.setFixedSize(1920, 1080) # Tamaño resolución de monitor
#         self.setStyleSheet("background: #FCFCFC ;") ##090c33          <--------------------------- para consideracion de temas de colores 

#         # 2. Iniciar comunicación serial
#         #  === COMUNICACIÓN SERIAL ===    
#         self.valores = {}           
#         self.serial = ComunicacionSerial()
#         self.serial.data_received.connect(self.actualizar_valor)
#         # self.serial.conectar()
        
       

#         # # 3. Crear pantallas 

#         self.alarmas_activas = []      
#         nombres = [info["name"] for g in VARIABLES.values() for info in g.values()]
#         tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]
#         self.sistema_alarmas = SistemaAlarmas(
#             nombres=nombres,
#             tags=tags,
#             limites=[info.get("limites", (0, 100)) for g in VARIABLES.values() for info in g.values()],
#             niveles=[info.get("nivel", "cian") for g in VARIABLES.values() for info in g.values()],
#             tipos=["numerico" if info["type"] == "double" else "booleano" for g in VARIABLES.values() for info in g.values()],
#             trigger_booleano=[True] * len(tags)
#         )
     
#         # conecta las señales de alarma   
#         self.sistema_alarmas.cambio_alarma.connect(self.manejar_alarma)
#         self.sistema_alarmas.nuevo_evento.connect(self.registrar_evento)
#         self.sistema_alarmas.iniciar_monitoreo()
#         self.valores = {n: 0.0 for n in tags}   

#         self.pantalla_alarmas     = alarmsScr(
#             parent=self,
#             valores_dict=self.valores,          # opcional, pero ya lo tienes
#             sistema_alarmas=self.sistema_alarmas
#         )        
#         # Monitor de variables (también necesita sistema_alarmas)
#         self.pantalla_monitor_variables = monitorVariables(
#             parent=self,
#             valores_dict=self.valores,
#             sistema_alarmas=self.sistema_alarmas
#         )        


#          # 4. Crear pantallas (en orden lógico)
#         self.dialysis_scr    = dialysisScr(parent=self)
#         self.pantalla_modo_       = dialysisScr(parent=self)  # ← considera renombrar esta clase
#         self.pantalla_limpieza    = cleanScr(parent=self)
#         self.pantalla_ajustes     = optionScr(parent=self)
#         # Submenús de ajustes
#         self.pantalla_modo_manual   = mManualScr(parent=self)
#         self.pantalla_panel_pruebas = testScr(parent=self)
#         self.pantalla_calibracion   = ctrlCfgScr(parent=self)
#         self.pantalla_config_red    = cfgRedScr(parent=self)

#         # Submenu de dialisis 
#         self.pantalla_paciente = patienCfgScr(parent=self)
#         self.pantalla_configuracion_terapia = therapyCfgScr(parent=self)

#         # 5. Añadir TODAS al stacked (en el orden deseado)
#         self.stacked.addWidget(mainScr())                    # 0
#         self.stacked.addWidget(self.dialysis_scr)       # 1
#         self.stacked.addWidget(self.pantalla_modo_)          # 2
#         self.stacked.addWidget(self.pantalla_limpieza)       # 3
#         self.stacked.addWidget(self.pantalla_ajustes)        # 4
#         self.stacked.addWidget(self.pantalla_alarmas)        # 5  ← ahora sí está la correcta
#         self.stacked.addWidget(self.pantalla_modo_manual)    # 6
#         self.stacked.addWidget(self.pantalla_panel_pruebas)  # 7
#         self.stacked.addWidget(self.pantalla_calibracion)    # 8
#         self.stacked.addWidget(self.pantalla_config_red)     # 9
       
#         self.stacked.addWidget(self.pantalla_monitor_variables) # 10
#         self.stacked.addWidget(self.pantalla_paciente)       # 11
#         self.stacked.addWidget(self.pantalla_configuracion_terapia) 
        

        
#         # 7. Iniciar timers y metodos de actualizacion de etiquedas en header
#         self.refrescar_etiqueta_alarmas()
#         self.actualizar_estado()
        
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.actualizar_estado)
#         self.timer.start(500)

#         self.timer_reloj = QTimer(self)
#         self.timer_reloj.timeout.connect(self.actualizar_fecha_hora)
#         self.timer_reloj.start(1000)
#         self.actualizar_fecha_hora()    

#         self.serial.conectar()
#         self.serial.iniciar_lectura()  

#         self.left.hide()
#         self.right.hide()
#         #contenedores vacios para el inicio de la app
#         self.container_right.setStyleSheet("background: transparent")
#         self.container_left.setStyleSheet("background: transparent")

#         if "Inicio" in self.botones_nav: # DESACTIVACION DE BOTONES AL UNICIO DE LA APLICACIÓN.
#             self.botones_nav["Inicio"].setEnabled(False)
#             self.botones_nav["Inicio"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
#             self.botones_nav["Inicio\nTratamiento"].setEnabled(False)
#             self.botones_nav["Inicio\nTratamiento"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
        
#     #  === PANTALLAS ===
#     def pantalla_principal(self):
#         return mainScr()
    
#     # === SETUP UI ===
#     def setup_ui(self):
#         central = QWidget()
#         self.setCentralWidget(central)
#         self.layout = QGridLayout(central)
#         self.layout.setSpacing(0)
#         self.layout.setContentsMargins(0, 0, 0, 0)

#         self.layout.setColumnStretch(0,0) # COLUMNA 0 → IZQUIERDA
#         self.layout.setColumnStretch(1,1) # COLUMNA 1 → STACKED + NAV (parte 1/4)
#         self.layout.setColumnStretch(2,1) # COLUMNA 2 → STACKED + NAV (parte 2/4)
#         self.layout.setColumnStretch(3,1) # COLUMNA 3 → STACKED + NAV (parte 3/4)
#         self.layout.setColumnStretch(4,1) # COLUMNA 4 → STACKED + NAV (parte 4/4)
#         self.layout.setColumnStretch(5,0) # COLUMNA 5 → DERECHA


#         # =========================================================================================
#         #                                    MAIN STACKED
#         # =========================================================================================
       
#         self.stacked = QStackedWidget()
#         # self.stacked.setFixedSize(1536, 726)
#         self.stacked.addWidget(self.pantalla_principal())
       
#         self.layout.addWidget(self.stacked, 1, 1, 1, 4)

#         #================================================================
#         # =========================== HEADER 1920x177 ===================
#         #================================================================       
#         header_container = QWidget()
#         header_container.setFixedHeight(177)
#         header_container.setStyleSheet("background: #EBEBEB;") 

#         header = QHBoxLayout(header_container)
#         header.setContentsMargins(30, 20, 30, 20)
#         header.setSpacing(20)

        

#         # ESTADO (la única con fondo)       
#         self.lbl_estado = QLabel("Conectado")
#         self.lbl_estado.setFixedSize(260, 80)
#         self.lbl_estado.setAlignment(Qt.AlignCenter)
#         self.lbl_estado.setStyleSheet("""
#               QLabel { background: #10b981; color: #ffffff; padding: 10px; border-radius: 12px;
#                       font-weight: bold; font-size: 22px; }
#         """)
#         header.addWidget(self.lbl_estado)
        
#         self.lbl_alarmas = QLabel("Alarmas:")
#         self.lbl_pantalla_actual = QLabel("Inicio")
#         self.lbl_fecha_hora = QLabel("25/12/2025  14:37:22")
#         # Especifica el tamaño de la etiqueta, alineacion, color de letra, etc. y lo agrega al widget
#         for lbl in [self.lbl_alarmas, self.lbl_pantalla_actual, self.lbl_fecha_hora]:
#             lbl.setFixedSize(400, 80)
#             lbl.setAlignment(Qt.AlignCenter)
#             lbl.setStyleSheet("""
#                 QLabel { color: #0f172a; background: transparent;
#                         font-weight: bold; font-size: 25px; }
#             """)
#             header.addWidget(lbl)

#         header.addStretch()    

#         logo1 = QLabel()
#         logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
#         header.addWidget(logo1)
#         logo2 = QLabel()
#         logo2.setPixmap(QPixmap(resource_path("resources/images/Logo_secihti_.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
#         header.addWidget(logo2)
#         self.layout.addWidget(header_container, 0, 0, 1, 6) #


#         # ==================================================================== 
#         #                  GAUGES IZQUIERDA (PA + PV) 
#         # ====================================================================
#         self.container_left = QWidget() # CONTENEDOR FIJO SIEMPRE VISIBLE
#         self.container_left.setFixedSize(192, 903)
#         layout_cont_left = QVBoxLayout(self.container_left)
#         layout_cont_left.setContentsMargins(0, 0, 0, 0)

#         self.left = QWidget() # CONTENEDOR DE WIDGETS 
#         self.left.setFixedSize(192, 903)
#         left_layout = QVBoxLayout(self.left)
#         left_layout.setContentsMargins(0, 0, 0, 0)
#         left_layout.setSpacing(0)

#         self.gauge_art = TankGauge("Art", -100, 400, "mmHg", "#dc2626")
#         self.gauge_ven = TankGauge("Ven", -50, 400, "mmHg", "#1640f9")

#         self.gauge_art.setFixedSize(192, 451)
#         self.gauge_ven.setFixedSize(192, 452)

#         left_layout.addWidget(self.gauge_art)
#         left_layout.addWidget(self.gauge_ven)

#         layout_cont_left.addWidget(self.left)

#         self.layout.addWidget(self.container_left, 1, 0, 2, 1)      

        
#         # ==================================================================================
#         #                            GAUGE DERECHA (TEMPERATURA + CONDUCTIVIDAD)
#         # ==================================================================================
#         self.container_right = QWidget() # contenedor fijo
#         self.container_right.setFixedSize(192,903)
#         layout_cont_right = QVBoxLayout(self.container_right)
#         layout_cont_right.setContentsMargins(0, 0, 0, 0)


#         self.right = QWidget()
#         self.right.setFixedSize(192, 903)
#         right_layout = QVBoxLayout(self.right)
#         right_layout.setContentsMargins(0, 0, 0, 0)
#         right_layout.setSpacing(0)

#         self.gauge_tempDial = TankGauge("Temp.\nDial", 0 ,50, "°C","#A31A1A")
#         self.powbar = ConductivityBar()

#         self.gauge_tempDial.setFixedWidth(192)        
#         self.powbar.setFixedWidth(192)

#         right_layout.addWidget(self.gauge_tempDial, 1)
#         right_layout.addWidget(self.powbar, 1)

#         layout_cont_right.addWidget(self.right)
#         self.layout.addWidget(self.container_right, 1, 5, 2, 1)      

#         # ==================================================================================
#         #                           === NAVEGACIÓN INFERIOR ===
#         # ==================================================================================
    
#         nav = QWidget()
#         nav.setFixedSize(1536, 177)
#         nav.setStyleSheet("background:  #FCFCFC;") # #090c33 <------------------- aqui tambien se cambiaria para hacer un tema diferente
#         nav_layout = QHBoxLayout(nav)
#         nav_layout.setContentsMargins(40, 20, 40, 20)
#         nav_layout.setSpacing(10)

#         self.botones_nav = {} 

#         botones = [
#             ("Inicio", "#0f172a", self.mostrar_pantalla_principal), # index 0 1b10b9
#             ("Diálisis", "#0f172a", self.show_daialysis_scr), # index 1
#             ("Tipo de\nTratamiento", "#0f172a", self.mostrar_pantalla_modo), # indes 2   ====================================modificar el nombre de esta pantalla para que coincida con el de labview, que es la seleccion del modo de operación
#             ("Inicio\nTratamiento","#25AD37",self.iniciar_tratamiento_),
#             ("Limpieza", "#0f172a", self.mostrar_pantalla_limpieza), # index 3
#             ("Parámetros\n de sistema", "#0f172a", self.mostrar_pantalla_ajustes), # index 4
#             ("Alarmas", "#0f172a", self.mostrar_pantalla_alarmas), # index 5           
#             ("Salir", "#dc2626", self.close),
#         ]
        

#         for texto, color, func in botones:
#             btn = QPushButton(texto)
#             btn.setFixedHeight(110)
#             btn.setStyleSheet(f"""
#                 QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
#                               font-size: 24px; border-radius: 10px; /*border: 4px solid #1b10b9;*/ }}
#                 QPushButton:pressed {{ background: #334155; }}
#             """)
#             btn.clicked.connect(func)
#             nav_layout.addWidget(btn)

#             self.botones_nav[texto] = btn 

#         self.layout.addWidget(nav, 2, 1, 1, 4)
    
#     # ==================================================================================
#     #                               === NAVEGACIÓN ===
#     # ==================================================================================
#     def iniciar_tratamiento_(self): #<------ el boton se debe activar cuando se cumplan las condiciones iniciales, inicia el tratamiento.
#         pass

#     def mostrar_pantalla_principal(self):
#         self.stacked.setCurrentIndex(self.INDEX_INICIO)
#         self.actualizar_label_pantalla("Inicio", "#0A0A0A")
#         self.left.hide()
#         self.right.hide()

#     def show_daialysis_scr(self):       
#         self.stacked.setCurrentWidget(self.dialysis_scr)
#         if hasattr(self.dialysis_scr, "actualizar_valores"): # value_update
#             self.dialysis_scr.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Diálisis", "#0f172a")
#         self.left.show()
#         self.right.show()
#         if "Inicio" in self.botones_nav:
#             self.botones_nav["Inicio"].setEnabled(True)
#             self.botones_nav["Inicio"].setStyleSheet("""
#                 QPushButton { background: #1b10b9; color: #ffffff; font-weight: bold;
#                               font-size: 24px; border-radius: 10px;}
#                 QPushButton:pressed { background: #334155;}
#             """)

#     def mostrar_pantalla_modo(self):
#         self.stacked.setCurrentWidget(self.pantalla_modo_)
#         self.actualizar_label_pantalla("Tipo de Tratamiento", "#0f172a")
#         self.left.show()
#         self.right.show()
    
#     def mostrar_pantalla_limpieza(self):    
#         self.stacked.setCurrentWidget(self.pantalla_limpieza)
#         if hasattr(self.pantalla_limpieza, "actualizar_valores"):
#             self.pantalla_limpieza.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Limpieza", "#0f172a") 
#         self.left.show()
#         self.right.show()   
    
#     def mostrar_pantalla_ajustes(self): 
#         self.stacked.setCurrentWidget(self.pantalla_ajustes)
#         self.actualizar_label_pantalla("Configuración", "#0f172a")     
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_alarmas(self):
#         self.stacked.setCurrentWidget(self.pantalla_alarmas)
#         self.actualizar_label_pantalla("Alarmas", "#0f172a")
#         self.left.show()
#         self.right.show()
    
#     def mostrar_modo_manual(self):
#         self.stacked.setCurrentWidget(self.pantalla_modo_manual)
#         if hasattr(self.pantalla_modo_manual, "actualizar_valores"):
#             self.pantalla_modo_manual.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Modo Manual","#0f172a")
#         self.left.show()
#         self.right.show()
        
    
#     def mostrar_panel_pruebas(self):
#         self.stacked.setCurrentWidget(self.pantalla_panel_pruebas)
#         if hasattr(self.pantalla_panel_pruebas, "actualizar_valores"):
#             self.pantalla_panel_pruebas.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Panel de pruebas", "#0f172a")
#         self.left.show()
#         self.right.show()
        

#     def mostrar_calibracion(self):
#         self.stacked.setCurrentWidget(self.pantalla_calibracion)
#         if hasattr(self.pantalla_calibracion,"actualizar_valores"):
#             self.pantalla_calibracion.actualizar_valores(self.valores)    
#         self.actualizar_label_pantalla("Calibración", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_config_red(self):
#         self.stacked.setCurrentWidget(self.pantalla_config_red)
#         self.actualizar_label_pantalla("Configuración de red", "#0f172a")

#     def mostrar_monitor_variables(self):
#         self.stacked.setCurrentWidget(self.pantalla_monitor_variables)
#         self.actualizar_label_pantalla("Monitor de variables", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_paciente(self):
#         self.stacked.setCurrentWidget(self.pantalla_paciente)
#         if hasattr(self.pantalla_paciente, "actualizar_valores"):
#             self.pantalla_paciente.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Paciente", "#0f172a")
#         self.left.show()
#         self.right.show()

#     def mostrar_pantalla_cfg_terapia(self):
#         self.stacked.setCurrentWidget(self.pantalla_configuracion_terapia)
#         if hasattr(self.pantalla_configuracion_terapia, "actualizar_valores"):
#             self.pantalla_configuracion_terapia.actualizar_valores(self.valores)
#         self.actualizar_label_pantalla("Terapia", "#0f172a")
#         self.left.show()
#         self.right.show()
 
  
#     def actualizar_label_pantalla(self, texto, color_texto="#0f172a"):
#         self.lbl_pantalla_actual.setText(texto)       
#         self.lbl_pantalla_actual.setStyleSheet(f"color: {color_texto}; background: transparent; font-weight: bold; font-size: 30px;")


#     def actualizar_fecha_hora(self):
#         from datetime import datetime
#         texto = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
#         self.lbl_fecha_hora.setText(texto)


#     def actualizar_valor(self, tag: str, valor: float):
#         self.valores[tag] = valor
#         mapeo = {
#             "arterPresProcessData": self.gauge_art,
#             "venouPresProcessData": self.gauge_ven,
#             "dialyTempVariableData": self.gauge_tempDial,
#             "dialyCondVariableData": self.powbar,
#         }
#         if tag in mapeo:
#             mapeo[tag].setValue(valor)

#     def refrescar_etiqueta_alarmas(self):
#         """Actualiza la etiqueta de alarmas con la alarma activa de mayor prioridad"""
#         if not self.alarmas_activas:
#             self.lbl_alarmas.setText("")
#             self.lbl_alarmas.setStyleSheet("""
#                 QLabel { color: #ffffff; background: transparent;
#                          font-weight: bold; font-size: 25px; }
#             """)
#         else:
#             prioridad = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
#             alarma_mayor = max(self.alarmas_activas, key=lambda x: prioridad.get(x[2], 0))
#             nombre, valor, nivel = alarma_mayor

#             texto = nombre.upper()
#             if valor is not None:
#                 texto += f" {valor:.1f}"

#             colores = {
#                 "rojo": "#dc2626",
#                 "naranja": "#f97316",
#                 "amarillo": "#eab308",
#                 "cian": "#06b6d4"
#             }
#             color_fondo = colores.get(nivel, "#1e293b")

#             self.lbl_alarmas.setText(texto)
#             self.lbl_alarmas.setStyleSheet(f"""
#                 QLabel {{ 
#                     background: {color_fondo}; 
#                     color: #ffffff; 
#                     padding: 10px;
#                     border-radius: 12px;
#                     font-weight: bold; 
#                     font-size: 20px; 
#                 }}
#             """)

#     def manejar_alarma(self, idx, activada, valor, nombre, nivel, limite):
#         if activada:
#             if nombre not in [a[0] for a in self.alarmas_activas]:
#                 self.alarmas_activas.append((nombre, valor, nivel))
#         else:
#             self.alarmas_activas = [a for a in self.alarmas_activas if a[0] != nombre]
#         # actualiza la etiqueta
#         self.refrescar_etiqueta_alarmas()
#         self.actualizar_estado()  # parpadeo rojo

#     def actualizar_estado(self):
#         if not hasattr(self,'serial') or not self.serial or not self.serial.conectado:
#             texto, color = "RECONECTANDO...", "#f97316"
#         elif self.alarmas_activas:
#             texto = "ALARMA ACTIVA"
#             color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
#         else:
#             texto, color = "CONECTADO", "#10b981"
    
#         self.lbl_estado.setText(texto)
#         self.lbl_estado.setStyleSheet(f"""
#             QLabel {{ background: {color}; color: #ffffff; padding: 10px;
#                       border-radius: 12px; font-weight: bold; font-size: 22px; }}
#         """)
#         if self.stacked.count() > 0:
#             widget_actual = self.stacked.currentWidget()
#             if hasattr(widget_actual, "actualizar_valores"):
#                 widget_actual.actualizar_valores(self.valores)
      

       
    
#     def registrar_evento(self, evento, valor, hora):
#         logger.error(f"[EVENTO] {hora} → {evento}")

#     def __del__(self):
#         """Destructor: se llama cuando Python destruye el objeto"""
#         logger.error("[INFO] Destructor llamado → deteniendo hilos...")
#         self.detener_todo()
     
#     def detener_todo(self):
#         """Detiene TODO de forma segura y limpia referencias."""
#         logger.error("[INFO] Iniciando detención controlada.")

#         # 1. Detener Timers (si existen)
#         if hasattr(self, 'timer') and isinstance(self.timer, QTimer) and self.timer.isActive():
#             self.timer.stop()
#             logger.error("[INFO] Timer principal detenido.")
#         if hasattr(self, 'timer_reloj') and isinstance(self.timer_reloj, QTimer) and self.timer_reloj.isActive():
#             self.timer_reloj.stop()
#             logger.error("[INFO] Timer reloj detenido.")
    
#         # 2. Detener Alarmas (Alto riesgo de fallo si no está bien implementado)
#         if hasattr(self, 'sistema_alarmas') and self.sistema_alarmas:
#             try:
#                 # La función detener() es responsable de su propio hilo.               
#                 self.sistema_alarmas.detener()
#             except Exception as e:
#                 # Este bloque de código ya no debería dar el error 'NoneType'
#                 logger.error(f"[ERROR] Fallo al detener alarmas de forma limpia: {e}")            
#             # Limpieza la referencia
#             self.sistema_alarmas = None 
#             logger.error("[INFO] Referencia a Sistema de Alarmas nulada.")
    
#         # 3. Detener Serial (Debe ser la última operación de I/O)
#         if hasattr(self, 'serial') and self.serial:
#             try:
#                 # La función detener() es responsable de su propio hilo.
#                 self.serial.detener() # Llama a la versión corregida que cierra el puerto primero
#             except Exception as e:
#                 logger.error(f"[ERROR] Fallo al detener serial: {e}")            
#             # Limpieza defensiva de la referencia
#             self.serial = None
#             logger.error("[INFO] Referencia a Comunicación Serial nulada.")

#         # 4. Pausa de seguridad final
#         # Espera un momento para que los hilos terminen sus joins finales
#         time.sleep(0.1) 
#         logger.error("[INFO] Detención controlada finalizada.")


#     def closeEvent(self, event):
#         logger.error("[INFO] closeEvent → deteniendo todo...")        
#         # Bloquea el hilo principal para terminar los procesos de los hilos
#         self.detener_todo() 
#         # Aumentamos la pausa a 1.0 segundo. Esto es fundamental para darle al sistema operativo
#         # tiempo de liberar correctamente la memoria de los hilos C/C++ subyacentes (Qt/Serial).
#         time.sleep(1.0) 
        
#         event.accept()
#         QApplication.quit()


# # gui/appMainHemodialysis.py



import os
import sys
import time
import logging
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap

# === MODULES ===
from core.alarms import AlarmSystem
from core.variables_map import VARIABLES

from connection.serial_communication import SerialCommunication
from gui.therapy.main_screen import MainScreen
from gui.therapy.alarms_screen import AlarmsScreen
from gui.therapy.dialysis_screen import DialysisScreen
from gui.therapy.treatment_mode_screen import TreatmentModeScreen
from gui.service.options_screen import OptionsScreen
from gui.service.cleaning_screen import CleaningScreen
from gui.components.real_time_variables import RealTimeVariablesMonitor
from gui.components.tank_gauge import TankGauge
from gui.components.conductivity_bar import ConductivityBar

from gui.service.manual_mode_screen import ManualModeScreen
from gui.service.test_panel_screen import TestPanelScreen
from gui.service.calibration_screen import CalibrationScreen
from gui.service.network_config_screen import NetworkConfigScreen

from gui.therapy.patient_config_screen import PatientConfigScreen
from gui.therapy.therapy_config_screen import TherapyConfigScreen

logger = logging.getLogger(__name__)

#===============================================================================
#======================CODIGO PARA ADJUNTAR LOGOS EN EJECUTABLE=================
#===============================================================================
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class HemodialysisHMI(QMainWindow):
    # Screen indices
    INDEX_HOME = 0

    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.update_current_screen_label("Inicio", "#000000")
        self.setFixedSize(1920, 1080)
        self.setStyleSheet("background: #FCFCFC;")

        # Serial communication
        self.current_values = {}
        self.serial_comm = SerialCommunication()
        self.serial_comm.data_received.connect(self.update_value)

        # Alarm system
        self.active_alarms = []
        display_names = [info["name"] for g in VARIABLES.values() for info in g.values()]
        tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]

        self.alarm_system = AlarmSystem(
            display_names=display_names,                     # ← cambiado de names=
            tags=tags,
            limits=[info.get("limites", (0.0, 100.0)) for g in VARIABLES.values() for info in g.values()],
            severity_levels=[info.get("nivel", "cyan") for g in VARIABLES.values() for info in g.values()],
            types=["numeric" if info["type"] == "double" else "boolean" for g in VARIABLES.values() for info in g.values()],
            boolean_triggers=[True] * len(tags)
        )
        # handle for alarms and start monitoring
        self.alarm_system.alarm_changed.connect(self.handle_alarm)
        self.alarm_system.new_event.connect(self.log_event)
        self.alarm_system.start_monitoring()

        self.current_values = {tag: 0.0 for tag in tags}

        # Screens initialization
        self.alarms_screen = AlarmsScreen(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        self.real_time_var = RealTimeVariablesMonitor(
            parent=self,
            values_dict=self.current_values,
            alarm_system=self.alarm_system
        )

        # # Therapy & service screens        
        self.dialysis_screen = DialysisScreen(parent=self)
        self.treatment_mode_screen = TreatmentModeScreen(parent=self)  # ← revisar si debe ser distinta clase
        self.cleaning_screen = CleaningScreen(parent=self)
        self.options_screen = OptionsScreen(parent=self)
        
        # # Service sub-screens
        self.manual_mode_screen = ManualModeScreen(parent=self)
        self.test_panel_screen = TestPanelScreen(parent=self)
        self.calibration_screen = CalibrationScreen(parent=self)
        self.network_config_screen = NetworkConfigScreen(parent=self)
        

        # # Therapy sub-screens
        self.patient_config_screen = PatientConfigScreen(parent=self)
        self.therapy_config_screen = TherapyConfigScreen(parent=self)
     
        
        # Add all screens to stacked widget (order matters)
        self.screen_stack.addWidget(self._main_screen)                      # 0 - Home
        self.screen_stack.addWidget(self.dialysis_screen)              # 1   funciona
        self.screen_stack.addWidget(self.treatment_mode_screen)        # 2 funciona 
        self.screen_stack.addWidget(self.cleaning_screen)              # 3
        self.screen_stack.addWidget(self.options_screen)               # 4
        self.screen_stack.addWidget(self.alarms_screen)                # 5
        self.screen_stack.addWidget(self.manual_mode_screen)           # 6
        self.screen_stack.addWidget(self.test_panel_screen)            # 7
        self.screen_stack.addWidget(self.calibration_screen)           # 8
        self.screen_stack.addWidget(self.network_config_screen)        # 9
        self.screen_stack.addWidget(self.real_time_var)                # 10
        self.screen_stack.addWidget(self.patient_config_screen)        # 11
        self.screen_stack.addWidget(self.therapy_config_screen)        # 12

        # Header update timers
        self.refresh_alarms_label()
        self.update_connection_status()

        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self.update_connection_status)
        self.main_timer.start(500)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_date_time)
        self.clock_timer.start(1000)
        self.update_date_time()

        self.serial_comm.connect()
        self.serial_comm.start_reading()

        self.left_container.hide()
        self.right_container.hide()
        self.right_content.setStyleSheet("background: transparent")
        self.left_content.setStyleSheet("background: transparent")

        # self.right_content.show()
        # self.left_content.show()

        # Disable home buttons at startup
        if "Inicio" in self.navigation_buttons:
            self.navigation_buttons["Inicio"].setEnabled(False)
            self.navigation_buttons["Inicio"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
            self.navigation_buttons["Comenzar"].setEnabled(False)
            self.navigation_buttons["Comenzar"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")

    # def _main_screen(self):
        # return MainScreen()
    # ────────────────────────────────────────────────
    #                   UI Setup
    # ────────────────────────────────────────────────
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0) 

        self.main_layout.setColumnStretch(0,0) # COLUMNA 0 → IZQUIERDA
        self.main_layout.setColumnStretch(1,1) # COLUMNA 1 → STACKED + NAV (parte 1/4)
        self.main_layout.setColumnStretch(2,1) # COLUMNA 2 → STACKED + NAV (parte 2/4)
        self.main_layout.setColumnStretch(3,1) # COLUMNA 3 → STACKED + NAV (parte 3/4)
        self.main_layout.setColumnStretch(4,1) # COLUMNA 4 → STACKED + NAV (parte 4/4)
        self.main_layout.setColumnStretch(5,0) # COLUMNA 5 → DERECHA

        # =========================================================================================
        #                                    MAIN STACKED
        # =========================================================================================
        self.screen_stack = QStackedWidget()    
        self._main_screen = MainScreen()    
        self.screen_stack.addWidget(self._main_screen)
        self.main_layout.addWidget(self.screen_stack, 1, 1, 1, 4)

        # ── Header (1920 × 177) ──────────────────────────
        header_container = QWidget()
        header_container.setFixedHeight(177)
        header_container.setStyleSheet("background: #EBEBEB;")

        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(20)

        # Connection / alarm status
        self.status_label = QLabel("Conectado")
        self.status_label.setFixedSize(260, 80)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
               QLabel { background: #10b981; color: #ffffff; padding: 10px; border-radius: 12px;
                       font-weight: bold; font-size: 22px; }
        """)
        header_layout.addWidget(self.status_label)

        self.active_alarms_label = QLabel("Alarmas:")
        self.current_screen_label = QLabel("Inicio")
        self.date_time_label = QLabel("25/12/2025  14:37:22")

        for lbl in [self.active_alarms_label, self.current_screen_label, self.date_time_label]:
            lbl.setFixedSize(400, 80)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                QLabel { color: #0f172a; background: transparent;
                         font-weight: bold; font-size: 25px; }
            """)
            header_layout.addWidget(lbl)

        header_layout.addStretch()

        # Logos
        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo1)

        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("resources/images/Logo_secihti_.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo2)

        self.main_layout.addWidget(header_container, 0, 0, 1, 6)

        # ==================================================================== 
        #                  GAUGES IZQUIERDA (PA + PV) 
        # ====================================================================
        self.left_container = QWidget()
        self.left_container.setFixedSize(192, 903)
        left_layout_outer = QVBoxLayout(self.left_container)
        left_layout_outer.setContentsMargins(0, 0, 0, 0)

        self.left_content = QWidget()
        self.left_content.setFixedSize(192, 903)
        left_inner_layout = QVBoxLayout(self.left_content)
        left_inner_layout.setContentsMargins(0, 0, 0, 0)
        left_inner_layout.setSpacing(0)

        self.arterial_pressure_gauge = TankGauge("Art", -100, 400, "mmHg", "#dc2626")
        self.venous_pressure_gauge   = TankGauge("Ven",  -50, 400, "mmHg", "#1640f9")

        self.arterial_pressure_gauge.setFixedSize(192, 451)
        self.venous_pressure_gauge.setFixedSize(192, 452)

        left_inner_layout.addWidget(self.arterial_pressure_gauge)
        left_inner_layout.addWidget(self.venous_pressure_gauge)

        left_layout_outer.addWidget(self.left_content)
        self.main_layout.addWidget(self.left_container, 1, 0, 2, 1)

        # ── Right gauges (Temp + Conductivity) ───────────
        self.right_container = QWidget()
        self.right_container.setFixedSize(192, 903)
        right_outer_layout = QVBoxLayout(self.right_container)
        right_outer_layout.setContentsMargins(0, 0, 0, 0)

        self.right_content = QWidget()
        self.right_content.setFixedSize(192, 903)
        right_inner_layout = QVBoxLayout(self.right_content)
        right_inner_layout.setContentsMargins(0, 0, 0, 0)
        right_inner_layout.setSpacing(0)

        self.dialysate_temp_gauge = TankGauge("Temp.\nDial", 0, 50, "°C", "#A31A1A")
        self.conductivity_bar = ConductivityBar()

        self.dialysate_temp_gauge.setFixedWidth(192)
        self.conductivity_bar.setFixedWidth(192)

        right_inner_layout.addWidget(self.dialysate_temp_gauge, 1)
        right_inner_layout.addWidget(self.conductivity_bar, 1)

        right_outer_layout.addWidget(self.right_content)
        self.main_layout.addWidget(self.right_container, 1, 5, 2, 1)

        # ── Bottom navigation bar ────────────────────────
        nav_bar = QWidget()
        nav_bar.setFixedSize(1536, 177)
        nav_bar.setStyleSheet("background: #FCFCFC;")

        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        nav_layout.setSpacing(10)

        self.navigation_buttons = {}

        nav_items = [
            ("Inicio",              "#0f172a", self.show_home_screen),
            ("Diálisis",            "#0f172a", self.show_dialysis_screen),
            ("Tipo de\nTratamiento","#0f172a", self.show_treatment_mode_screen),   # antes "Tipo de Tratamiento"
            ("Comenzar", "#25AD37", self.start_treatment),
            ("Limpieza",            "#0f172a", self.show_cleaning_screen),
            ("Configuración", "#0f172a", self.show_options_screen),
            ("Alarmas",             "#0f172a", self.show_alarms_screen),
            ("Salir",               "#dc2626", self.close),
        ]

        for text, color, callback in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(110)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                               font-size: 24px; border-radius: 10px; }}
                QPushButton:pressed {{ background: #334155; }}
            """)            
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self.navigation_buttons[text] = btn

        self.main_layout.addWidget(nav_bar, 2, 1, 1, 4)

    # ────────────────────────────────────────────────
    #              Navigation Methods
    # ────────────────────────────────────────────────
    def start_treatment(self):
        # ← Implementar lógica de condiciones iniciales antes de iniciar
        pass

    def show_home_screen(self):
        self.screen_stack.setCurrentIndex(self.INDEX_HOME)
        self.update_current_screen_label("Inicio", "#0A0A0A")
        self.left_container.hide()
        self.right_container.hide()

    def show_dialysis_screen(self):
        self.screen_stack.setCurrentWidget(self.dialysis_screen)
        if hasattr(self.dialysis_screen, "update_values"):
            self.dialysis_screen.update_values(self.current_values)
        self.update_current_screen_label("Diálisis", "#0f172a")
        self.left_container.show()
        self.right_container.show()
        self.navigation_buttons["Inicio"].setEnabled(True)
        self.navigation_buttons["Inicio"].setStyleSheet("""
            QPushButton { background: #1b10b9; color: #ffffff; font-weight: bold;
                          font-size: 24px; border-radius: 10px;}
            QPushButton:pressed { background: #334155;}
        """)

    def show_treatment_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.treatment_mode_screen)
        self.update_current_screen_label("Modo de Tratamiento", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_cleaning_screen(self):
        self.screen_stack.setCurrentWidget(self.cleaning_screen)
        if hasattr(self.cleaning_screen, "update_values"):
            self.cleaning_screen.update_values(self.current_values)
        self.update_current_screen_label("Limpieza", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_options_screen(self):
        self.screen_stack.setCurrentWidget(self.options_screen)
        self.update_current_screen_label("Configuración", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_alarms_screen(self):
        self.screen_stack.setCurrentWidget(self.alarms_screen)
        self.update_current_screen_label("Alarmas", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_manual_mode_screen(self):
        self.screen_stack.setCurrentWidget(self.manual_mode_screen)
        if hasattr(self.manual_mode_screen, "update_values"):
            self.manual_mode_screen.update_values(self.current_values)
        self.update_current_screen_label("Modo Manual", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_test_panel_screen(self):
        self.screen_stack.setCurrentWidget(self.test_panel_screen)
        if hasattr(self.test_panel_screen, "update_values"):
            self.test_panel_screen.update_values(self.current_values)
        self.update_current_screen_label("Panel de Pruebas", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_calibration_screen(self):
        self.screen_stack.setCurrentWidget(self.calibration_screen)
        if hasattr(self.calibration_screen, "update_values"):
            self.calibration_screen.update_values(self.current_values)
        self.update_current_screen_label("Calibración", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_network_config_screen(self):
        self.screen_stack.setCurrentWidget(self.network_config_screen)
        self.update_current_screen_label("Configuración de Red", "#0f172a")

    def show_real_time_var_screen(self):
        self.screen_stack.setCurrentWidget(self.real_time_var)
        self.update_current_screen_label("Monitor de Variables", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_patient_config_screen(self):
        self.screen_stack.setCurrentWidget(self.patient_config_screen)
        if hasattr(self.patient_config_screen, "update_values"):
            self.patient_config_screen.update_values(self.current_values)
        self.update_current_screen_label("Paciente", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    def show_therapy_config_screen(self):
        self.screen_stack.setCurrentWidget(self.therapy_config_screen)
        if hasattr(self.therapy_config_screen, "update_values"):
            self.therapy_config_screen.update_values(self.current_values)
        self.update_current_screen_label("Terapia", "#0f172a")
        self.left_container.show()
        self.right_container.show()

    # ────────────────────────────────────────────────
    #              Utility Methods
    # ────────────────────────────────────────────────
    def update_current_screen_label(self, text, text_color="#0f172a"):
        self.current_screen_label.setText(text)
        self.current_screen_label.setStyleSheet(
            f"color: {text_color}; background: transparent; font-weight: bold; font-size: 30px;"
        )

    def update_date_time(self):
        from datetime import datetime
        self.date_time_label.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

    def update_value(self, tag: str, value: float):
        self.current_values[tag] = value

        gauge_mapping = {
            "arterPresProcessData":   self.arterial_pressure_gauge,
            "venouPresProcessData":   self.venous_pressure_gauge,
            "dialyTempVariableData":  self.dialysate_temp_gauge,
            "dialyCondVariableData":  self.conductivity_bar,
        }

        if tag in gauge_mapping:
            gauge_mapping[tag].setValue(value)

    def refresh_alarms_label(self):
        if not self.active_alarms:
            self.active_alarms_label.setText("")
            self.active_alarms_label.setStyleSheet("""
                QLabel { color: #ffffff; background: transparent;
                         font-weight: bold; font-size: 25px; }
            """)
        else:
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            name, value, level = top_alarm

            display_text = name.upper()
            if value is not None:
                display_text += f" {value:.1f}"

            color_map = {
                "rojo":    "#dc2626",
                "naranja": "#f97316",
                "amarillo":"#eab308",
                "cian":    "#06b6d4"
            }
            bg_color = color_map.get(level, "#1e293b")

            self.active_alarms_label.setText(display_text)
            self.active_alarms_label.setStyleSheet(f"""
                QLabel {{ background: {bg_color}; color: #ffffff; padding: 10px;
                          border-radius: 12px; font-weight: bold; font-size: 20px; }}
            """)

    def handle_alarm(self, idx, active, value, name, level, limit):
        if active:
            if name not in [a[0] for a in self.active_alarms]:
                self.active_alarms.append((name, value, level))
        else:
            self.active_alarms = [a for a in self.active_alarms if a[0] != name]

        self.refresh_alarms_label()
        self.update_connection_status()

    def update_connection_status(self):
        if not hasattr(self, 'serial_comm') or not self.serial_comm or not self.serial_comm.is_connected:
            text, color = "RECONECTANDO...", "#f97316"
        elif self.active_alarms:
            text = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            text, color = "CONECTADO", "#10b981"

        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{ background: {color}; color: #ffffff; padding: 10px;
                      border-radius: 12px; font-weight: bold; font-size: 22px; }}
        """)

        current_widget = self.screen_stack.currentWidget()
        if hasattr(current_widget, "update_values"):
            current_widget.update_values(self.current_values)

    def log_event(self, event, value, timestamp):
        logger.error(f"[EVENT] {timestamp} → {event}")

    def __del__(self):
        logger.error("[INFO] Destructor called → stopping threads...")
        self.shutdown()

    def shutdown(self):
        logger.error("[INFO] Initiating controlled shutdown.")

        # Stop timers
        if hasattr(self, 'main_timer') and isinstance(self.main_timer, QTimer) and self.main_timer.isActive():
            self.main_timer.stop()
            logger.error("[INFO] Timer principal detenido.")
        if hasattr(self, 'clock_timer') and isinstance(self.clock_timer,QTimer) and self.clock_timer.isActive():
            self.clock_timer.stop()
            logger.error("[INFO] Timer reloj detenido")

        # Stop alarm system
        if hasattr(self, 'alarm_system') and self.alarm_system:
            try:
                self.alarm_system.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop alarm system cleanly: {e}")
            self.alarm_system = None

        # Stop serial communication (most critical I/O)
        if hasattr(self, 'serial_comm') and self.serial_comm:
            try:
                self.serial_comm.stop()
            except Exception as e:
                logger.error(f"[ERROR] Failed to stop serial communication: {e}")
            self.serial_comm = None

        time.sleep(0.1)
        logger.error("[INFO] Controlled shutdown completed.")

    def closeEvent(self, event):
        logger.error("[INFO] closeEvent → performing shutdown...")
        self.shutdown()
        time.sleep(1.0)  # Give OS time to release resources
        event.accept()
        QApplication.quit()
