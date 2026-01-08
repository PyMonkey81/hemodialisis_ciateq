# gui/appMainHemodialisis.py

import os
import sys
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap

# === MÓDULOS ===
from core.alarmas import SistemaAlarmas
from core.variables_map import VARIABLES

from connection.comunicacion_serial import ComunicacionSerial
from gui.therapy.mainScreen import mainScr
from gui.therapy.dialysisScreen import dialysisScr
from gui.service.optionScreen import optionScr
from gui.service.cleanScreen import cleanScr
from gui.therapy.alarmsScreen import alarmsScr
from gui.components.rVariables import monitorVariables
from gui.components.TankGaugeW import TankGauge
from gui.components.PowerBar import ConductivityBar


from gui.service.mManualScreen import mManualScr #Pantalla modo manual 
from gui.service.pPruebasScreen import pPruebasScr #Pantalla panel de pruebas 
from gui.service.ctrlCfgScreen import ctrlCfgScr #pantalla calibracion
from gui.service.cfgRedScreen import cfgRedScr # pantalla configuracion de red


#===============================================================================
#======================CODIGO PARA ADJUNTAR LOGOS EN EJECUTABLE=================
#===============================================================================

def resource_path(relative_path):
    """Devuelve la ruta correcta tanto en desarrollo como en .exe"""
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
#===============================================================================


class HemodialisisHMI(QMainWindow):
    #INDEX DE PANTALLAS 
    INDEX_INICIO = 0   

    def __init__(self):
        super().__init__()

        # === DETECCIÓN DE ENTORNO DE PRUEBAS ===
        # import os
        # en_pruebas = os.getenv('PYTEST_VERSION') or 'pytest' in sys.modules
    
        # if en_pruebas:
        #     print("[INFO] Modo pruebas detectado → puerto serial desactivado")
        #     self.serial = None
        #     self.conectado = False
        # else:
        #     self.serial = ComunicacionSerial(callback=self.actualizar_valor)
        #     self.conectado = self.serial.conectar()
        #     if self.conectado:
        #         self.serial.iniciar_lectura()
       
        # 1. Crear estructura visual (ventana, label y stacked)
        self.setup_ui()
        self.actualizar_label_pantalla("Inicio", "#ffffff")
        self.setFixedSize(1920, 1080) # Tamaño resolución de monitor
        self.setStyleSheet("background: #090c33;")

        # 2. Iniciar comunicación serial
        #  === COMUNICACIÓN SERIAL ===    
        self.valores = {}           
        self.serial = ComunicacionSerial()
        self.serial.data_received.connect(self.actualizar_valor)
        # self.serial.conectar()
        
        # 3. Crear pantallas 
        #crear instancias de los menús principales        
        self.pantalla_dialisis = dialysisScr(parent=self)
        self.pantalla_modo_ = dialysisScr(parent=self) # HACER PANTALLA PARA ESTE SUBMENU, DONDE SE SELECCIONA EL MODO DE OPERACION O FILOSOFIA DE OPERACION 
        self.pantalla_limpieza = cleanScr(parent=self)
        self.pantalla_ajustes = optionScr(parent=self)
        self.pantalla_alarmas = alarmsScr(parent=self)

        # CREAR INSTANCIAS DE SUBMENÚS DE AJUSTES
        self.pantalla_modo_manual = mManualScr(parent=self)
        self.pantalla_panel_pruebas = pPruebasScr(parent=self)
        self.pantalla_calibracion = ctrlCfgScr(parent=self)
        self.pantalla_config_red = cfgRedScr(parent=self)       
         
        # 4. Añadir las pantallas al Stacked creado (VACIO) 
        # añadir estancias fijas
        self.stacked.addWidget(mainScr())
        self.stacked.addWidget(self.pantalla_dialisis)
        self.stacked.addWidget(self.pantalla_modo_)# este es un cambio, modificar el nombre de la pantalla 
        self.stacked.addWidget(self.pantalla_limpieza)
        self.stacked.addWidget(self.pantalla_ajustes)
        self.stacked.addWidget(self.pantalla_alarmas)        
        self.stacked.addWidget(self.pantalla_modo_manual) # submenús de ajustes 4
        self.stacked.addWidget(self.pantalla_panel_pruebas)
        self.stacked.addWidget(self.pantalla_calibracion)
        self.stacked.addWidget(self.pantalla_config_red)
        
        # 5. Configurar alarmas
        self.alarmas_activas = []      
        nombres = [info["name"] for g in VARIABLES.values() for info in g.values()]
        tags = [info["tag"] for g in VARIABLES.values() for info in g.values()]
        self.sistema_alarmas = SistemaAlarmas(
            nombres=nombres,
            tags=tags,
            limites=[info.get("limites", (0, 100)) for g in VARIABLES.values() for info in g.values()],
            niveles=[info.get("nivel", "cian") for g in VARIABLES.values() for info in g.values()],
            tipos=["numerico" if info["type"] == "double" else "booleano" for g in VARIABLES.values() for info in g.values()],
            trigger_booleano=[True] * len(tags)
        )
     
        # conecta las señales de alarma   
        self.sistema_alarmas.cambio_alarma.connect(self.manejar_alarma)
        self.sistema_alarmas.nuevo_evento.connect(self.registrar_evento)

        self.valores = {n: 0.0 for n in tags}       
        
        # 6. Añadir monitor de variables al stacket, solo hasta que se conecta al sistema de alarmas
        self.pantalla_monitor_variables = monitorVariables(parent=self, 
                                                   valores_dict=self.valores, 
                                                   sistema_alarmas=self.sistema_alarmas)       

        self.stacked.addWidget(self.pantalla_monitor_variables)
        
        # 7. Iniciar timers y metodos de actualizacion de etiquedas en header
        self.refrescar_etiqueta_alarmas()
        self.actualizar_estado()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_estado)
        self.timer.start(500)

        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_fecha_hora)
        self.timer_reloj.start(1000)
        self.actualizar_fecha_hora()    

        self.serial.conectar()
        self.serial.iniciar_lectura()  

        self.left.hide()
        self.right.hide()
        #contenedores vacios para el inicio de la app
        self.container_right.setStyleSheet("background: transparent")
        self.container_left.setStyleSheet("background: transparent")

        if "Inicio" in self.botones_nav:
            self.botones_nav["Inicio"].setEnabled(False)
            self.botones_nav["Inicio"].setStyleSheet("background: #334155; color: #94a3b8; font-weight: bold; font-size: 24px; border-radius: 10px")
        
    #  === PANTALLAS ===
    def pantalla_principal(self):
        return mainScr()
    
    # === SETUP UI ===
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.setColumnStretch(0, 0)   # COLUMNA 0 → IZQUIERDA
                                # Contenido: Gauges PA + PV (192×903)
                                # Fijo → stretch = 0

        layout.setColumnStretch(1, 1)   # COLUMNA 1 → STACKED + NAV (parte 1/4)
        layout.setColumnStretch(2, 1)   # COLUMNA 2 → STACKED + NAV (parte 2/4)
        layout.setColumnStretch(3, 1)   # COLUMNA 3 → STACKED + NAV (parte 3/4)
        layout.setColumnStretch(4, 1)   # COLUMNA 4 → STACKED + NAV (parte 4/4)
                                # → Estas 4 columnas = 1536 px
                                # En fila 1: STACKED (1536×726)
                                # En fila 2: NAV (1536×177)
                                # Ambas ocupan exactamente las mismas columnas → perfecto alineado

        layout.setColumnStretch(5, 0)   # COLUMNA 5 → DERECHA
                                # Contenido: Temperatura + ConductivityBar (192×903)
                                # Fijo → stretch = 0

        # =========================================================================================
        #                                    MAIN STACKED
        # =========================================================================================
       
        self.stacked = QStackedWidget()
        self.stacked.setFixedSize(1536, 726)
        self.stacked.addWidget(self.pantalla_principal())
       
        layout.addWidget(self.stacked, 1, 1, 1, 4)

        #================================================================
        # =========================== HEADER 1920x177 ===================
        #================================================================       
        header_container = QWidget()
        header_container.setFixedHeight(177)
        header_container.setStyleSheet("background: #090c33;")  # color de header 1f2c45
        header = QHBoxLayout(header_container)
        header.setContentsMargins(30, 20, 30, 20)
        header.setSpacing(20)

        # ESTADO (la única con fondo)
        self.lbl_estado = QLabel("Conectado")
        self.lbl_estado.setFixedSize(260, 80)
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setStyleSheet("""
            QLabel { background: #10b981; color: #ffffff; padding: 10px; border-radius: 12px;
                     font-weight: bold; font-size: 22px; }
        """)
        header.addWidget(self.lbl_estado)

        # 
        self.lbl_alarmas = QLabel("Alarmas:")
        self.lbl_pantalla_actual = QLabel("Inicio")
        self.lbl_fecha_hora = QLabel("25/12/2025  14:37:22")
        # Especifica el tamaño de la etiqueta, alineacion, color de letra, etc. y lo agrega al widget
        for lbl in [self.lbl_alarmas, self.lbl_pantalla_actual, self.lbl_fecha_hora]:
            lbl.setFixedSize(400, 80)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                QLabel { color: #ffffff; background: transparent;
                        font-weight: bold; font-size: 25px; }
            """)
            header.addWidget(lbl)

        header.addStretch()    

        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq__.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo1)
        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("resources/images/Logo_secihti_.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo2)
        layout.addWidget(header_container, 0, 0, 1, 6) #


        # ==================================================================== 
        #                  GAUGES IZQUIERDA (PA + PV) 
        # ====================================================================
        self.container_left = QWidget() # CONTENEDOR FIJO SIEMPRE VISIBLE
        self.container_left.setFixedSize(192, 903)
        layout_cont_left = QVBoxLayout(self.container_left)
        layout_cont_left.setContentsMargins(0, 0, 0, 0)

        self.left = QWidget() # CONTENEDOR DE WIDGETS 
        self.left.setFixedSize(192, 903)
        left_layout = QVBoxLayout(self.left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.gauge_art = TankGauge("Presión\nArterial", -100, 400, "mmHg", "#dc2626")
        self.gauge_ven = TankGauge("Presión\nVenosa", -50, 400, "mmHg", "#1640f9")
        self.gauge_art.setFixedSize(192, 451)
        self.gauge_ven.setFixedSize(192, 452)
        left_layout.addWidget(self.gauge_art)
        left_layout.addWidget(self.gauge_ven)

        layout_cont_left.addWidget(self.left)

        layout.addWidget(self.container_left, 1, 0, 2, 1)      

        
        # ==================================================================================
        #                            GAUGE DERECHA (TEMPERATURA + CONDUCTIVIDAD)
        # ==================================================================================
        self.container_right = QWidget() # contenedor fijo
        self.container_right.setFixedSize(192,903)
        layout_cont_right = QVBoxLayout(self.container_right)
        layout_cont_right.setContentsMargins(0, 0, 0, 0)


        self.right = QWidget()
        self.right.setFixedSize(192, 903)
        right_layout = QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.gauge_tempDial = TankGauge("Temperatura\nDializante", 0 ,50, "°C","#A31A1A")
        self.powbar = ConductivityBar()
        self.gauge_tempDial.setFixedWidth(192)        
        self.powbar.setFixedWidth(192)
        right_layout.addWidget(self.gauge_tempDial, 1)
        right_layout.addWidget(self.powbar, 1)

        layout_cont_right.addWidget(self.right)
        layout.addWidget(self.container_right, 1, 5, 2, 1)      

        # ==================================================================================
        #                           === NAVEGACIÓN INFERIOR ===
        # ==================================================================================
    
        nav = QWidget()
        nav.setFixedSize(1536, 177)
        nav.setStyleSheet("background: #090c33;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        nav_layout.setSpacing(10)

        self.botones_nav = {} 

        botones = [
            ("Inicio", "#1b10b9", self.mostrar_pantalla_principal), # index 0
            ("Diálisis", "#1b10b9", self.mostrar_pantalla_dialisis), # index 1
            ("Tipo de\nTratamiento", "#1B10B9", self.mostrar_pantalla_modo), # indes 2   ====================================modificar el nombre de esta pantalla para que coincida con el de labview, que es la seleccion del modo de operación
            ("Limpieza", "#1b10b9", self.mostrar_pantalla_limpieza), # index 3
            ("Parámetros\n de sistema", "#1b10b9", self.mostrar_pantalla_ajustes), # index 4
            ("Alarmas", "#1b10b9", self.mostrar_pantalla_alarmas), # index 5           
            ("Salir", "#dc2626", self.close),
        ]
        

        for texto, color, func in botones:
            btn = QPushButton(texto)
            btn.setFixedHeight(110)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: #ffffff; font-weight: bold;
                              font-size: 24px; border-radius: 10px; /*border: 4px solid #1b10b9;*/ }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(func)
            nav_layout.addWidget(btn)

            self.botones_nav[texto] = btn 

        layout.addWidget(nav, 2, 1, 1, 4)
    
    # ==================================================================================
    #                               === NAVEGACIÓN ===
    # ==================================================================================
   
    def mostrar_pantalla_principal(self):
        self.stacked.setCurrentIndex(self.INDEX_INICIO)
        self.actualizar_label_pantalla("Inicio", "#ffffff")
        self.left.hide()
        self.right.hide()

    def mostrar_pantalla_dialisis(self):       
        self.stacked.setCurrentWidget(self.pantalla_dialisis)
        if hasattr(self.pantalla_dialisis, "actualizar_valores"):
            self.pantalla_dialisis.actualizar_valores(self.valores)
        self.actualizar_label_pantalla("Diálisis", "#ffffff")
        self.left.show()
        self.right.show()
        if "Inicio" in self.botones_nav:
            self.botones_nav["Inicio"].setEnabled(True)
            self.botones_nav["Inicio"].setStyleSheet("""
                QPushButton { background: #1b10b9; color: #ffffff; font-weight: bold;
                              font-size: 24px; border-radius: 10px;}
                QPushButton:pressed { background: #334155;}
            """)

    def mostrar_pantalla_modo(self):
        self.stacked.setCurrentWidget(self.pantalla_modo_)
    
    def mostrar_pantalla_limpieza(self):    
        self.stacked.setCurrentWidget(self.pantalla_limpieza)
        self.actualizar_label_pantalla("Limpieza", "#ffffff") 
        self.left.show()
        self.right.show()   
    
    def mostrar_pantalla_ajustes(self): 
        self.stacked.setCurrentWidget(self.pantalla_ajustes)
        self.actualizar_label_pantalla("Configuración", "#ffffff")     
        self.left.show()
        self.right.show()

    def mostrar_pantalla_alarmas(self):
        self.stacked.setCurrentWidget(self.pantalla_alarmas)
        self.actualizar_label_pantalla("Alarmas", "#ffffff")
        self.left.show()
        self.right.show()
    
    def mostrar_modo_manual(self):
        self.stacked.setCurrentWidget(self.pantalla_modo_manual)
        if hasattr(self.pantalla_modo_manual, "actualizar_valores"):
            self.pantalla_modo_manual.actualizar_valores(self.valores)
        self.actualizar_label_pantalla("Modo Manual","#ffffff")
        
    
    def mostrar_panel_pruebas(self):
        self.stacked.setCurrentWidget(self.pantalla_panel_pruebas)
        self.actualizar_label_pantalla("Panel de pruebas", "#ffffff")
        

    def mostrar_calibracion(self):
        self.stacked.setCurrentWidget(self.pantalla_calibracion)
        self.actualizar_label_pantalla("Calibración", "#ffffff")

    def mostrar_config_red(self):
        self.stacked.setCurrentWidget(self.pantalla_config_red)
        self.actualizar_label_pantalla("Configuración de red", "#ffffff")

    def mostrar_monitor_variables(self):
        self.stacked.setCurrentWidget(self.pantalla_monitor_variables)
        self.actualizar_label_pantalla("Monitor de variables", "#ffffff")
 
  
    def actualizar_label_pantalla(self, texto, color_texto="#ffffff"):
        self.lbl_pantalla_actual.setText(texto)       
        self.lbl_pantalla_actual.setStyleSheet(f"color: {color_texto}; background: transparent; font-weight: bold; font-size: 30px;")


    def actualizar_fecha_hora(self):
        from datetime import datetime
        texto = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        self.lbl_fecha_hora.setText(texto)


    def actualizar_valor(self, tag: str, valor: float):
        self.valores[tag] = valor
        mapeo = {
            "arterPresProcessData": self.gauge_art,
            "venouPresProcessData": self.gauge_ven,
            "dialyTempVariableData": self.gauge_tempDial,
            "dialyCondVariableData": self.powbar,
        }
        if tag in mapeo:
            mapeo[tag].setValue(valor)

        # try:
        #     if self.stacked.count() > 0:
        #         widget_actual = self.stacked.currentWidget()
        #         if hasattr(widget_actual, "actualizar_valores"):
        #             widget_actual.actualizar_valores(self.valores)
        # except: pass

 

    def refrescar_etiqueta_alarmas(self):
        """Actualiza la etiqueta de alarmas con la alarma activa de mayor prioridad"""
        if not self.alarmas_activas:
            self.lbl_alarmas.setText("")
            self.lbl_alarmas.setStyleSheet("""
                QLabel { color: #ffffff; background: transparent;
                         font-weight: bold; font-size: 25px; }
            """)
        else:
            prioridad = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            alarma_mayor = max(self.alarmas_activas, key=lambda x: prioridad.get(x[2], 0))
            nombre, valor, nivel = alarma_mayor

            texto = nombre.upper()
            if valor is not None:
                texto += f" {valor:.1f}"

            colores = {
                "rojo": "#dc2626",
                "naranja": "#f97316",
                "amarillo": "#eab308",
                "cian": "#06b6d4"
            }
            color_fondo = colores.get(nivel, "#1e293b")

            self.lbl_alarmas.setText(texto)
            self.lbl_alarmas.setStyleSheet(f"""
                QLabel {{ 
                    background: {color_fondo}; 
                    color: #ffffff; 
                    padding: 10px;
                    border-radius: 12px;
                    font-weight: bold; 
                    font-size: 20px; 
                }}
            """)

    def manejar_alarma(self, idx, activada, valor, nombre, nivel, limite):
        if activada:
            if nombre not in [a[0] for a in self.alarmas_activas]:
                self.alarmas_activas.append((nombre, valor, nivel))
        else:
            self.alarmas_activas = [a for a in self.alarmas_activas if a[0] != nombre]
        # actualiza la etiqueta
        self.refrescar_etiqueta_alarmas()
        self.actualizar_estado()  # parpadeo rojo

    def actualizar_estado(self):
        if not hasattr(self,'serial') or not self.serial or not self.serial.conectado:
            texto, color = "RECONECTANDO...", "#f97316"
        elif self.alarmas_activas:
            texto = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            texto, color = "CONECTADO", "#10b981"
    
        self.lbl_estado.setText(texto)
        self.lbl_estado.setStyleSheet(f"""
            QLabel {{ background: {color}; color: #ffffff; padding: 10px;
                      border-radius: 12px; font-weight: bold; font-size: 22px; }}
        """)
        if self.stacked.count() > 0:
            widget_actual = self.stacked.currentWidget()
            if hasattr(widget_actual, "actualizar_valores"):
                widget_actual.actualizar_valores(self.valores)
      

       
    
    def registrar_evento(self, evento, valor, hora):
        print(f"[EVENTO] {hora} → {evento}")

    def __del__(self):
        """Destructor: se llama cuando Python destruye el objeto"""
        print("[INFO] Destructor llamado → deteniendo hilos...")
        self.detener_todo()
     
    def detener_todo(self):
        """Detiene TODO de forma segura y limpia referencias."""
        print("[INFO] Iniciando detención controlada.")

        # 1. Detener Timers (si existen)
        if hasattr(self, 'timer') and isinstance(self.timer, QTimer) and self.timer.isActive():
            self.timer.stop()
            print("[INFO] Timer principal detenido.")
        if hasattr(self, 'timer_reloj') and isinstance(self.timer_reloj, QTimer) and self.timer_reloj.isActive():
            self.timer_reloj.stop()
            print("[INFO] Timer reloj detenido.")
    
        # 2. Detener Alarmas (Alto riesgo de fallo si no está bien implementado)
        if hasattr(self, 'sistema_alarmas') and self.sistema_alarmas:
            try:
                # La función detener() es responsable de su propio hilo.               
                self.sistema_alarmas.detener()
            except Exception as e:
                # Este bloque de código ya no debería dar el error 'NoneType'
                print(f"[ERROR] Fallo al detener alarmas de forma limpia: {e}")            
            # Limpieza la referencia
            self.sistema_alarmas = None 
            print("[INFO] Referencia a Sistema de Alarmas nulada.")
    
        # 3. Detener Serial (Debe ser la última operación de I/O)
        if hasattr(self, 'serial') and self.serial:
            try:
                # La función detener() es responsable de su propio hilo.
                self.serial.detener() # Llama a la versión corregida que cierra el puerto primero
            except Exception as e:
                print(f"[ERROR] Fallo al detener serial: {e}")            
            # Limpieza defensiva de la referencia
            self.serial = None
            print("[INFO] Referencia a Comunicación Serial nulada.")

        # 4. Pausa de seguridad final
        # Espera un momento para que los hilos terminen sus joins finales
        time.sleep(0.1) 
        print("[INFO] Detención controlada finalizada.")


    def closeEvent(self, event):
        print("[INFO] closeEvent → deteniendo todo...")        
        # Bloquea el hilo principal para terminar los procesos de los hilos
        self.detener_todo() 
        # Aumentamos la pausa a 1.0 segundo. Esto es fundamental para darle al sistema operativo
        # tiempo de liberar correctamente la memoria de los hilos C/C++ subyacentes (Qt/Serial).
        time.sleep(1.0) 
        
        event.accept()
        QApplication.quit()