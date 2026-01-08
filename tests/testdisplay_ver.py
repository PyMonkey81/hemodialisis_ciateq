# gui/appMainHemodialisis.py
# VERSIÓN FINAL – 1920x1080 – TODO AL MILÍMETRO – SIN TRASLAPES

import os
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
from gui.components.PowerBar import ConductivityBar
from resources.variables_map_respaldo import VARIABLES


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class HemodialisisHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1920, 1080)  # ← RESOLUCIÓN EXACTA
        self.setStyleSheet("background: #f1f5f9;")
        self.valores = {}
        self.alarmas_activas = []

        # Serial y alarmas
        self.serial = ComunicacionSerial(callback=self.actualizar_valor)
        self.conectado = self.serial.conectar()
        if self.conectado:
            self.serial.iniciar_lectura()

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
        QTimer(self).timeout.connect(self.actualizar_estado)
        QTimer(self).start(500)
        QTimer(self).timeout.connect(self.actualizar_fecha_hora)
        QTimer(self).start(1000)
        self.actualizar_fecha_hora()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # === HEADER 1920x177 ===
        header = QHBoxLayout()
        header.setContentsMargins(20, 20, 20, 20)
        header.setSpacing(15)

        self.lbl_estado = QLabel("CONECTADO")
        self.lbl_alarmas = QLabel("ALARMAS: 0")
        self.lbl_pantalla_actual = QLabel("INICIO")
        self.lbl_fecha_hora = QLabel()

        for lbl, color in [(self.lbl_estado, "#10b981"), (self.lbl_alarmas, "#1e293b"),
                           (self.lbl_pantalla_actual, "#3a5bed"), (self.lbl_fecha_hora, "#1e293b")]:
            lbl.setStyleSheet(f"""
                QLabel {{ background: {color}; color: #ffffff; padding: 14px 25px;
                          border: 3px solid #1e293b; border-radius: 12px;
                          font-weight: bold; font-size: 18px; min-width: 180px; }}
            """)
            lbl.setAlignment(Qt.AlignCenter)
            header.addWidget(lbl)

        header.addStretch()

        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("resources/images/logo_ciateq.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("resources/images/Seciht.png")).scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo1)
        header.addWidget(logo2)

        layout.addLayout(header, 0, 0, 1, 6)  # 6 columnas

        # === GAUGES IZQUIERDA (PA + PV) → 192x451.5 cada uno (total 192x903) ===
        left = QWidget()
        left.setFixedSize(192, 903)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.gauge_art = TankGauge("Presión\nArterial", -100, 400, "mmHg", "#dc2626")
        self.gauge_ven = TankGauge("Presión\nVenosa", -50, 400, "mmHg", "#f97316")
        self.gauge_art.setFixedSize(192, 451)
        self.gauge_ven.setFixedSize(192, 452)
        left_layout.addWidget(self.gauge_art)
        left_layout.addWidget(self.gauge_ven)
        layout.addWidget(left, 1, 0, 2, 1)

        # === MAIN STACKED 1536x726 ===
        self.stacked = QStackedWidget()
        self.stacked.setFixedSize(1536, 726)
        self.stacked.addWidget(self.pantalla_principal())
        layout.addWidget(self.stacked, 1, 1, 1, 4)

        # === CONDUCTIVIDAD 192x903 ===
        right = QWidget()
        right.setFixedSize(192, 903)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.powbar = ConductivityBar()
        self.powbar.setFixedSize(192, 903)
        right_layout.addWidget(self.powbar)
        layout.addWidget(right, 1, 5, 2, 1)

        # === NAVEGACIÓN 1536x177 ===
        nav = QWidget()
        nav.setFixedSize(1536, 177)
        nav.setStyleSheet("background: #ffffff;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        nav_layout.setSpacing(30)

        botones = [
            ("INICIO", "#1b10b9", self.mostrar_pantalla_principal),
            ("DIÁLISIS", "#1b10b9", self.mostrar_pantalla_dialisis),
            ("LIMPIEZA", "#1b10b9", lambda: print("LIMPIEZA")),
            ("AJUSTES", "#1b10b9", lambda: print("AJUSTES")),
            ("ALARMAS", "#1b10b9", lambda: print("ALARMAS")),
            ("SALIR", "#dc2626", self.close),
        ]

        for texto, color, func in botones:
            btn = QPushButton(texto)
            btn.setFixedHeight(110)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; color: white; font-weight: bold;
                              font-size: 24px; border-radius: 20px; border: 4px solid #1e293b; }}
                QPushButton:pressed {{ background: #334155; }}
            """)
            btn.clicked.connect(func)
            nav_layout.addWidget(btn)

        layout.addWidget(nav, 2, 1, 1, 4)

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

    def actualizar_label_pantalla(self, texto, color):
        self.lbl_pantalla_actual.setText(texto)
        self.lbl_pantalla_actual.setStyleSheet(f"""
            QLabel {{ background: {color}; color: white; padding: 14px 25px;
                      border: 3px solid #1e293b; border-radius: 12px;
                      font-weight: bold; font-size: 18px; min-width: 180px; }}
        """)

    def actualizar_fecha_hora(self):
        from datetime import datetime
        self.lbl_fecha_hora.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

    def actualizar_valor(self, nombre: str, valor: float):
        self.valores[nombre] = valor
        mapeo = {
            "Presión Arterial": self.gauge_art,
            "Presión Venosa": self.gauge_ven,
            "Conductividad medida": self.powbar,
        }
        if nombre in mapeo:
            mapeo[nombre].setValue(valor)

        if self.stacked.currentIndex() == 1 and self.stacked.count() > 1:
            self.stacked.widget(1).actualizar_valores(self.valores)

    def actualizar_estado(self):
        if not self.serial.conectado:
            texto, color = "RECONECTANDO...", "#f97316"
        elif self.alarmas_activas:
            texto = "ALARMA ACTIVA"
            color = "#dc2626" if int(time.time()) % 2 == 0 else "#991b1b"
        else:
            texto, color = "CONECTADO", "#10b981"
        self.lbl_estado.setText(texto)
        self.lbl_estado.setStyleSheet(f"""
            QLabel {{ background: {color}; color: white; padding: 14px 25px;
                      border: 3px solid #1e293b; border-radius: 12px;
                      font-weight: bold; font-size: 18px; min-width: 180px; }}
        """)

    def closeEvent(self, event):
        print("[INFO] Cerrando...")
        if hasattr(self, 'serial') and self.serial:
            self.serial.detener()
        if hasattr(self, 'sistema_alarmas') and self.sistema_alarmas:
            self.sistema_alarmas.detener()
        event.accept()