# tests/test_display.py
import sys
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QFont, QPixmap, QPen

# === MÓDULOS ===
from core.alarmas import SistemaAlarmas
from connection.comunicacion_serial import ComunicacionSerial
from gui.therapy.mainScreen import mainScr
from gui.therapy.dialysisScreen import dialysisScr

from gui.components.rVariables import VentanaVariables
from gui.components.TankGaugeW import TankGauge
from core.variables_map import VARIABLES, TVAR_TO_GROUP

# ================================================================
# HMI PRINCIPAL → CORREGIDO
# ================================================================
class HemodialisisHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CIATEQ A.C. - Máquina de Hemodiálisis")
        self.setGeometry(100, 100, 1280, 720)
        self.setStyleSheet("background: #f1f5f9;")

        self.valores = {}
        self.alarmas_activas = []

        

        # === COMUNICACIÓN SERIAL ===
        self.serial = ComunicacionSerial(callback=self.actualizar_valor)
        self.conectado = self.serial.conectar()
        if self.conectado:
            self.serial.iniciar_lectura()

        # === ALARMAS AUTOMÁTICAS ===
        nombres, limites, niveles, tipos, trigger_bool = [], [], [], [], []
        for g, vars_dict in VARIABLES.items():
            for info in vars_dict.values():
                nombres.append(info["name"])
                niveles.append(info.get("nivel", "cian"))
                if info["type"] == "double":
                    tipos.append("numerico")
                    limites.append(info.get("limites", (0, 100)))
                    trigger_bool.append(True)
                else:
                    tipos.append("booleano")
                    limites.append((0, 1))
                    trigger_bool.append(True)

        self.sistema_alarmas = SistemaAlarmas(
            nombres=nombres, limites=limites, niveles=niveles,
            tipos=tipos, trigger_booleano=trigger_bool,
            on_alarma=self.manejar_alarma, on_registro=self.registrar_evento
        )
        self.valores = {n: 0.0 for n in nombres}

        self.setup_ui()
        #self.lbl_pantalla_actual = self.crear_etiqueta_header("INICIO", "#3a5bed")
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_estado)
        self.timer.start(500)

        # === TIMER PARA HORA Y FECHA ACTUALES
        self.timer_reloj = QTimer()
        self.timer_reloj.timeout.connect(self.actualizar_fecha_hora)
        self.timer_reloj.start(1000)  # cada segundo  # Cadea segun se actualiza la hora 

        # inicio de actualización de la hora 
        self.actualizar_fecha_hora()

    
    # ================================================================
    # FUNCIÓN AUXILIAR PARA CREAR ETIQUETAS DEL HEADER (va aquí)
    # ================================================================
    def crear_etiqueta_header(self, texto, color_fondo, color_texto="white"):
        label = QLabel(texto)
        label.setAlignment(Qt.AlignCenter)    
        label.setStyleSheet(f"""
            QLabel {{
                background: {color_fondo};
                color: {color_texto};
                padding: 14px 20px;
                border: 3px solid #1e293b;
                border-radius: 16px;
                font-weight: bold;
                font-size: 15px;
                min-height: 30px;
                min-width: 200px;     /* ← ancho mínimo */
                max-width: 250px;     /* ← ancho máximo */
            }}
        """)
        return label
        

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)

        # Header
        header = QHBoxLayout()
        header.setSpacing(15)
        header.setContentsMargins(15, 10, 15, 10)

        # Izquierda: Estado y alarmas
        self.lbl_estado = self.crear_etiqueta_header("INICIANDO...", "#f97316")      # naranja fuerte
        self.lbl_alarmas = self.crear_etiqueta_header("ALARMAS: 0", "#1e293b")       # azul oscuro
        self.lbl_pantalla_actual = self.crear_etiqueta_header("INICIO", "#3a5bed")  # 

        header.addWidget(self.lbl_estado)
        header.addWidget(self.lbl_alarmas)
        header.addWidget(self.lbl_pantalla_actual)

        header.addStretch()  # ← Empuja todo lo siguiente al extremo derecho

        # === DERECHA: Fecha/Hora + Logos ===

        # Fecha y hora actual (se actualiza cada segundo)
        self.lbl_fecha_hora = self.crear_etiqueta_header("00/00/0000\n00:00:00", "#1e293b", "white")
        
        header.addWidget(self.lbl_fecha_hora)

        # Logo CIATEQ
        logo_ciateq = QLabel()
        pixmap_ciateq = QPixmap("resources/images/logo_ciateq.png").scaled(
            120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        logo_ciateq.setPixmap(pixmap_ciateq)
        #logo_ciateq.setToolTip("CIATEQ A.C.")
        header.addWidget(logo_ciateq)

        # Logo Secretaría / SECIHT
        logo_seciht = QLabel()
        pixmap_seciht = QPixmap("resources/images/Seciht.png").scaled(
            120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        logo_seciht.setPixmap(pixmap_seciht)
        #logo_seciht.setToolTip("Secretaría de Salud")
        header.addWidget(logo_seciht)


        header.addWidget(QLabel("Máquina de Hemodiálisis\nCIATEQ A.C. - Versión 1.2"), alignment=Qt.AlignRight)
        layout.addLayout(header, 0, 0, 1, 5)

        # Gauges
        self.gauge_art = TankGauge("Presión \nArterial", -100, 400, "mmHg", "#dc2626")
        self.gauge_ven = TankGauge("Presión \nVenosa", -50, 300, "mmHg", "#f97316")
        self.gauge_cond = TankGauge("Conductividad", 12, 16, "mS/cm", "#8b5cf6")

        # Stacked
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.pantalla_principal())   # índice 0
        self.stacked.addWidget(self.pantalla_dialisis())    # índice 1

        # === NAVEGACIÓN UNIFICADA===
        nav = QHBoxLayout()
        nav.setSpacing(20)
        nav.setContentsMargins(20, 10 ,20,10)

        # ==== contenedor para centrar y distribuir los botones  de navegación
        btn_container = QWidget()
        btn_container_layout = QHBoxLayout(btn_container)
        btn_container_layout.setSpacing(30)

        # ==== BOTONES DE NAVEGACION PRINCIPAL ====

        btn_vars = QPushButton("MONITOR DE VARIABLES")
        btn_vars.setStyleSheet("background: #7c3aed; color: white; padding: 15px; font-weight: bold; border-radius: 10px;")
        btn_vars.setFixedHeight(70)
        btn_container_layout.addWidget(btn_vars, stretch=1)
        btn_vars.clicked.connect(self.mostrar_variables)
        

        btn_iniScr = QPushButton("INICIO")
        btn_iniScr.setStyleSheet("background: #10b981; color: white; padding: 15px; font-weight: bold; border-radius: 10px;")
        btn_iniScr.setFixedHeight(70)
        btn_container_layout.addWidget(btn_iniScr, stretch=1)
        btn_iniScr.clicked.connect(self.mostrar_pantalla_principal)
        

        btn_dialisis = QPushButton("DIÁLISIS")
        btn_dialisis.setStyleSheet("background: #10b981; color: white; padding: 15px; font-weight: bold; border-radius: 10px;")
        btn_dialisis.setFixedHeight(70)
        btn_container_layout.addWidget(btn_dialisis, stretch=1)
        btn_dialisis.clicked.connect(self.mostrar_pantalla_dialisis)
       

        # ===Expandir el contenedor de los botones de navegacion ===
        btn_container_layout.addStretch()
        nav.addStretch(1)
        nav.addWidget(btn_container, alignment=Qt.AlignCenter)
        nav.addStretch(1)

        # Layout final
        layout.addWidget(self.gauge_art, 1, 0, 3, 1)   
        layout.addWidget(self.gauge_ven, 4, 0, 1, 1)
        layout.addWidget(self.gauge_cond, 1, 4, 6, 1)
        layout.addWidget(self.stacked, 1, 1, 7, 3)
        layout.addLayout(nav, 8, 0, 1, 5)  # ← 

    def actualizar_label_pantalla(self, texto, color_fondo):
        self.lbl_pantalla_actual.setText(texto)
        # Crea un label temporal solo para extraer el estilo
        temp = self.crear_etiqueta_header("X", color_fondo)
        self.lbl_pantalla_actual.setStyleSheet(temp.styleSheet())


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()    # sale de pantalla completa
        elif event.key() == Qt.Key_F11:
            self.showFullScreen()


    def actualizar_fecha_hora(self):
        from datetime import datetime
        ahora = datetime.now()
        texto = ahora.strftime("%d/%m/%Y\n%H:%M:%S")
        self.lbl_fecha_hora.setText(texto)

    # === PANTALLAS ===
    def pantalla_principal(self):
        return mainScr()
    
    def pantalla_dialisis(self):
        return dialysisScr()
    
    # ================================================================
    #                 MOSTRAR PANTALLAS
    # ================================================================   

    def mostrar_pantalla_principal(self):
        self.stacked.setCurrentIndex(0)
        self.actualizar_label_pantalla("INICIO", "#3a5bed")

    def mostrar_pantalla_dialisis(self):
        self.stacked.setCurrentIndex(1)
        self.actualizar_label_pantalla("DIÁLISIS", "#10b981")
        pantalla = self.stacked.widget(1)
        if hasattr(pantalla, "actualizar_valores"):
            pantalla.actualizar_valores(self.valores)
            

    def mostrar_variables(self):
        self.ventana = VentanaVariables(parent=self, valores_dict=self.valores, sistema_alarmas=self.sistema_alarmas)
        self.ventana.show()
        self.actualizar_label_pantalla("MONITOR DE VARIABLES", "#7c3aed")

    def actualizar_valor(self, nombre: str, valor: float):
        self.valores[nombre] = valor

        mapeo = {
            "Presión Arterial": self.gauge_art,
            "Presión Venosa": self.gauge_ven,
            "Conductividad medida": self.gauge_cond,  # ← debe coincidir con el nombre en variables_map
        }
        if nombre in mapeo:
            mapeo[nombre].setValue(valor)

        if nombre in self.sistema_alarmas.nombres:
            idx = self.sistema_alarmas.nombres.index(nombre)
            self.sistema_alarmas.actualizar_valor(idx, valor)
        #Actualiza los valores en la pantalla de dialisis
        if self.stacked.currentIndex() == 1:
            pantalla = self.stacked.widget(1)
            if hasattr(pantalla, "actualizar_valores"):
                pantalla.actualizar_valores(self.valores)


    # === ALARMAS Y ESTADO ===
    def manejar_alarma(self, idx, activada, valor, nombre, nivel, limite):
        if activada and nombre not in [a[0] for a in self.alarmas_activas]:
            self.alarmas_activas.append((nombre, valor, nivel))
            print(f"ALARM: {nombre} = {valor}")
        elif not activada:
            self.alarmas_activas = [a for a in self.alarmas_activas if a[0] != nombre]
        self.lbl_alarmas.setText(f"ALARMAS: {len(self.alarmas_activas)}")
        self.actualizar_estado()

    def registrar_evento(self, evento, valor, hora):
        print(f"[EVENTO] {hora} → {evento}")

    def actualizar_estado(self):
        if not self.serial.conectado:
            texto = "RECONECTANDO..."
            color = "#f97316"  # naranja fijo
            parpadeo = False

        elif self.alarmas_activas:
            texto = "ALARMA ACTIVA"
    # Parpadeo más elegante (1 vez por segundo)
            if int(time.time()) % 2 == 0:
                color = "#dc2626"
            else:
                color = "#991b1b"   # rojo muy oscuro
            parpadeo = True

        else:
            texto = "CONECTADO"
            color = "#10b981"  # verde fijo
            parpadeo = False

        # Aplicar texto y estilo manteniendo el diseño perfecto
        self.lbl_estado.setText(texto)
        temp = self.crear_etiqueta_header("TEST", color)
        self.lbl_estado.setStyleSheet(temp.styleSheet())

    def closeEvent(self, event):
        self.serial.detener()
        self.sistema_alarmas.detener()
        event.accept()


# ================================================================
# EJECUTAR
# ================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HemodialisisHMI()
    window.show()
    sys.exit(app.exec())