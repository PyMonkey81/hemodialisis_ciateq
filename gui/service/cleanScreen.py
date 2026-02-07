# gui/service/cleanScreen.py
# Control de los ciclos de desinfección (química y térmica) y enjuague.

# stacked index 4
# from PySide6.QtWidgets import *
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QColor

# class cleanScr(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.parent = parent  # ← guardar referencia al padre
#         self.valores = parent.valores if parent else {}

#         self.setFixedSize(1536, 726)  # ← tamaño exacto del stacked
#         self.setStyleSheet("background: #0f172a;")

#         self.setup_ui()

#     def setup_ui(self):
#         layout = QGridLayout(self)
#         layout.setContentsMargins(50, 50, 50, 50)
#         layout.setSpacing(20)

#         titulo = QLabel("LIMPIEZA")
#         titulo.setStyleSheet("color: white; font-size: 48px; font-weight: bold;")
#         titulo.setAlignment(Qt.AlignCenter)
#         layout.addWidget(titulo, 0, 0, 1, 4)


# # gui/service/cleanScreen.py
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont


class cleanScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.valores = valores_dict if valores_dict is not None else {}

        # Tamaño fijo según tu diseño (ajusta si usas escalado)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("background: #0f172a;")  # azul oscuro industrial

        self.current_phase = "Listo para iniciar"
        self.total_time_seconds = 0
        self.remaining_time = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(30)

        # ── Título ───────────────────────────────────────────────
        titulo = QLabel("Limpieza / Desinfección")
        titulo.setStyleSheet("""
            color: #e2e8f0;
            font-size: 52px;
            font-weight: bold;
            background: transparent;
        """)
        titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(titulo)

        # ── Estado actual / Fase ─────────────────────────────────
        self.lbl_phase = QLabel(self.current_phase)
        self.lbl_phase.setStyleSheet("""
            color: #94a3b8;
            font-size: 32px;
            font-weight: bold;
            background: transparent;
            min-height: 60px;
        """)
        self.lbl_phase.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_phase)

        # ── Barra de progreso ────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m seg")
        self.progress_bar.setFixedHeight(60)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b;
                border: 2px solid #475569;
                border-radius: 10px;
                text-align: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3b82f6, stop:1 #60a5fa);
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # ── Tiempo restante ──────────────────────────────────────
        self.lbl_time = QLabel("Tiempo restante: --:--")
        self.lbl_time.setStyleSheet("""
            color: #cbd5e1;
            font-size: 28px;
            font-weight: bold;
            background: transparent;
        """)
        self.lbl_time.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_time)

        # Espaciador
        main_layout.addStretch()

        # ── Botón de inicio ──────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_start = QPushButton("INICIAR LIMPIEZA")
        self.btn_start.setFixedSize(420, 120)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #047857;
                color: white;
                font-size: 38px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #065f46;
            }
            QPushButton:pressed {
                background: #064e3b;
            }
            QPushButton:disabled {
                background: #334155;
                color: #64748b;
            }
        """)
        self.btn_start.clicked.connect(self.start_cleaning)
        btn_layout.addWidget(self.btn_start)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Estado inicial
        self.reset_ui()

    def reset_ui(self):
        """Vuelve al estado inicial"""
        self.current_phase = "Listo para iniciar"
        self.lbl_phase.setText(self.current_phase)
        self.progress_bar.setValue(0)
        self.lbl_time.setText("Tiempo restante: --:--")
        self.btn_start.setEnabled(True)
        self.btn_start.setText("INICIAR LIMPIEZA")
        self.timer.stop()

    def start_cleaning(self):
        """Inicia el proceso de limpieza"""
        # Aquí puedes definir diferentes fases y duraciones
        # Ejemplo: ciclo completo de 15 minutos (900 segundos)
        self.total_time_seconds = 900
        self.remaining_time = self.total_time_seconds

        self.current_phase = "Desinfección química en curso..."
        self.lbl_phase.setText(self.current_phase)
        self.btn_start.setEnabled(False)
        self.btn_start.setText("EN PROCESO...")

        self.progress_bar.setMaximum(self.total_time_seconds)
        self.progress_bar.setValue(0)

        # Inicia el temporizador (cada segundo)
        self.timer.start(1000)  # 1000 ms = 1 segundo

        self.update_time_display()

    def update_progress(self):
        """Actualiza cada segundo"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.progress_bar.setValue(self.total_time_seconds - self.remaining_time)
            self.update_time_display()
        else:
            self.timer.stop()
            self.finish_cleaning()

    def update_time_display(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.lbl_time.setText(f"Tiempo restante: {minutes:02d}:{seconds:02d}")

    def finish_cleaning(self):
        """Finaliza el proceso"""
        self.current_phase = "Limpieza completada"
        self.lbl_phase.setText(self.current_phase)
        self.lbl_phase.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
        self.lbl_time.setText("Tiempo restante: 00:00")
        self.progress_bar.setValue(self.total_time_seconds)

        # Puedes habilitar el botón de nuevo o mostrar "Reiniciar"
        self.btn_start.setText("REINICIAR")
        self.btn_start.setEnabled(True)
        self.btn_start.clicked.disconnect()
        self.btn_start.clicked.connect(self.reset_ui)

   




