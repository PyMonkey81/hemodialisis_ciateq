# gui/appMainHemodialisis.py


import sys
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap

# === MÓDULOS ===
from core.alarmas import SistemaAlarmas
from connection.comunicacion_serial import ComunicacionSerial
from gui.therapy.mainScreen import mainScr
from gui.therapy.dialysisScreen import dialysisScr
from gui.components.rVariables import VentanaVariables
from gui.components.TankGaugeW import TankGauge
from resources.variables_map_respaldo import VARIABLES


class HemodialisisHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f1f5f9;")
        self.valores = {}
        self.alarmas_activas = []

        # === COMUNICACIÓN SERIAL ===
        self.serial = ComunicacionSerial(callback=self.actualizar_valor)
        self.conectado = self.serial.conectar()
        if self.conectado:
            self.serial.iniciar_lectura()

        # === ALARMAS ===
        nombres = [info["name"] for g in VARIABLES.values() for info in g.values()]
        self.sistema_alarmas = SistemaAlarmas(
            nombres=nombres,
            limites=[info.get("limites", (0, 100)) for g in VARIABLES.values() for info in g.values()],
            niveles=[info.get("nivel", "cian") for g in VARIABLES.values() for info in g.values()],
            tipos=["numerico" if info["type"] == "double" else "booleano" for g in VARIABLES.values() for info in g.values()],
            trigger_booleano=[True] * len(nombres),
            on_alarma=self.manejar_alarma,
            on_registro=self.registrar_evento
        )
        self.valores = {n: 0.0 for n in nombres}

        self.setup_ui()

        self.actualizar_label_pantalla("INICIO", "#3a5bed")
        self.actualizar_estado()

        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_estado)
        self.timer.start(500)

        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_fecha_hora)
        self.timer_reloj.start(1000)
        self.actualizar_fecha_hora()

    # === ESTILOS HEADER ===
    def crear_etiqueta_header(self, texto, color_fondo):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{ background: {color_fondo}; color: white; padding: 14px 20px;
                      border: 3px solid #1e293b; border-radius: 16px;
                      font-weight: bold; font-size: 15px; }}
        """)
        return lbl

    def aplicar_estilo_header(self, label, texto, color_fondo):
        label.setText(texto)
        label.setStyleSheet(f"""
            QLabel {{ background: {color_fondo}; color: white; padding: 14px 20px;
                      border: 3px solid #1e293b; border-radius: 16px;
                      font-weight: bold; font-size: 15px; }}
        """)

    # === PANTALLAS ===
    def pantalla_principal(self):
        return mainScr()

    def pantalla_dialisis(self):
        return dialysisScr()

    # === SETUP UI – TU DISTRIBUCIÓN PERFECTA ===
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # === HEADER ===
        header = QHBoxLayout()
        header.setContentsMargins(20, 20, 20, 20)
        header.setSpacing(15)

        self.lbl_estado = self.crear_etiqueta_header("CONECTADO", "#10b981")
        self.lbl_alarmas = self.crear_etiqueta_header("ALARMAS: 0", "#1e293b")
        self.lbl_pantalla_actual = self.crear_etiqueta_header("INICIO", "#3a5bed")
        self.lbl_fecha_hora = self.crear_etiqueta_header("00/00/0000\n00:00:00", "#1e293b")

        header.addWidget(self.lbl_estado)
        header.addWidget(self.lbl_alarmas)
        header.addWidget(self.lbl_pantalla_actual)
        header.addStretch()
        header.addWidget(self.lbl_fecha_hora)

        logo1 = QLabel()
        logo1.setPixmap(QPixmap("resources/images/logo_ciateq.png").scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo2 = QLabel()
        logo2.setPixmap(QPixmap("resources/images/Seciht.png").scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo1)
        header.addWidget(logo2)

        layout.addLayout(header, 0, 0, 1, 5)

        # === GAUGES IZQUIERDA (PA + PV) ===
        self.gauge_art = TankGauge("Presión\nArterial", -100, 400, "mmHg", "#dc2626")
        self.gauge_ven = TankGauge("Presión\nVenosa", -50, 300, "mmHg", "#f97316")
        left = QVBoxLayout()
        left.addWidget(self.gauge_art)
        left.addWidget(self.gauge_ven)
        left.setSpacing(20)
        left.setContentsMargins(20, 20, 20, 20)
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setStyleSheet("background: #f1f5f9;")
        layout.addWidget(left_widget, 1, 0)

        # === MAIN STACKED ===
        self.stacked = QStackedWidget()
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stacked.addWidget(self.pantalla_principal())
        # === ESTO ES LA CLAVE (FORZAR TAMAÑO MÍNIMO) ===
        self.stacked.setMinimumSize(1536, 726)
        # O mejor aún: forzar tamaño fijo lógico
        self.stacked.setFixedSize(1536, 726)
        layout.addWidget(self.stacked, 1, 1, 1, 3)

        # === GAUGE CONDUCTIVIDAD DERECHA ===
        self.gauge_cond = TankGauge("Conductividad", 12, 16, "mS/cm", "#8b5cf6")
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.gauge_cond)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right.setStyleSheet("background: #f1f5f9;")
        layout.addWidget(right, 1, 4)

        # === NAVEGACIÓN INFERIOR ===
        nav_container = QWidget()
        nav_container.setFixedHeight(177)
        nav_container.setStyleSheet("background: #ffffff;")  #fondo blanco 

        nav = QHBoxLayout(nav_container)
        nav.setContentsMargins(60, 30, 60, 30)
        nav.setSpacing(40)

        botones = [# color de botones igual 
            ("INICIO", "#107bb9", self.mostrar_pantalla_principal),
            ("DIÁLISIS", "#107bb9", self.mostrar_pantalla_dialisis),
            ("MONITOR", "#107bb9", self.mostrar_variables),
            ("AJUSTES", "#107bb9", lambda: print("AJUSTES")),
            ("SALIR", "#dc2626", QApplication.quit),
        ]

        for texto, color, func in botones:
            btn = QPushButton(texto)
            btn.setFixedHeight(100)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: white; font-weight: bold;
                              font-size: 22px; border-radius: 20px; border: 4px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(func)
            nav.addWidget(btn)

        layout.addWidget(nav_container, 2, 1, 1, 3)

    # === NAVEGACIÓN ===
    def mostrar_pantalla_principal(self):
        self.stacked.setCurrentIndex(0)
        self.actualizar_label_pantalla("INICIO", "#3a5bed")

    def mostrar_pantalla_dialisis(self):
        if self.stacked.count() == 1:
            pantalla = dialysisScr()
            self.stacked.addWidget(pantalla)
            if hasattr(pantalla, "actualizar_valores"):
                pantalla.actualizar_valores(self.valores)
        self.stacked.setCurrentIndex(1)
        self.actualizar_label_pantalla("DIÁLISIS", "#10b981")

    def mostrar_variables(self):
        self.ventana = VentanaVariables(parent=self, valores_dict=self.valores, sistema_alarmas=self.sistema_alarmas)
        self.ventana.show()
        self.actualizar_label_pantalla("MONITOR DE VARIABLES", "#7c3aed")

    def actualizar_label_pantalla(self, texto, color):
        self.aplicar_estilo_header(self.lbl_pantalla_actual, texto, color)

    def actualizar_fecha_hora(self):
        from datetime import datetime
        self.lbl_fecha_hora.setText(datetime.now().strftime("%d/%m/%Y\n%H:%M:%S"))

    def actualizar_valor(self, nombre: str, valor: float):
        self.valores[nombre] = valor
        mapeo = {
            "Presión Arterial": self.gauge_art,
            "Presión Venosa": self.gauge_ven,
            "Conductividad medida": self.gauge_cond,
        }
        if nombre in mapeo:
            mapeo[nombre].setValue(valor)

        if self.stacked.currentIndex() == 1 and self.stacked.count() > 1:
            pantalla = self.stacked.widget(1)
            if hasattr(pantalla, "actualizar_valores"):
                pantalla.actualizar_valores(self.valores)

    def manejar_alarma(self, idx, activada, valor, nombre, nivel, limite):
        if activada and nombre not in [a[0] for a in self.alarmas_activas]:
            self.alarmas_activas.append((nombre, valor, nivel))
        elif not activada:
            self.alarmas_activas = [a for a in self.alarmas_activas if a[0] != nombre]
        self.aplicar_estilo_header(self.lbl_alarmas, f"ALARMAS: {len(self.alarmas_activas)}", "#1e293b")
        self.actualizar_estado()

    def actualizar_estado(self):
        if not self.serial.conectado:
            texto, color = "RECONECTANDO...", "#f97316"
        elif self.alarmas_activas:
            texto = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            texto, color = "CONECTADO", "#10b981"
        self.aplicar_estilo_header(self.lbl_estado, texto, color)

    def registrar_evento(self, evento, valor, hora):
        print(f"[EVENTO] {hora} → {evento}")

    def closeEvent(self, event):
        self.serial.detener()
        self.sistema_alarmas.detener()
        event.accept()