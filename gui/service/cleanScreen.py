# gui/service/cleanScreen.py

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton,
    QProgressBar, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont

try:
    from core.variables_map import VARIABLES
except ImportError:
    VARIABLES = {0x01: {}, 0x02: {}}

class cleanScr(QWidget):
    def __init__(self, parent=None, valores_dict=None):
        super().__init__(parent)
        self.parent_window = parent
        self.valores = valores_dict if valores_dict is not None else {}

        # Estado interno para saber si ya iniciamos la limpieza manualmente
        self.limpieza_en_curso = False 

        # Tamaño fijo según tu diseño (ajusta si usas escalado)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("background: #0f172a;")  # azul oscuro industrial

        self.current_phase = "Esperando condiciones..."
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
            color: #3d3d3d;
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
                color: #ffffff;
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

        self.btn_start = QPushButton("Iniciar limpieza")
        self.btn_start.setFixedSize(300, 100)
        # Inicialmente deshabilitado
        self.btn_start.setEnabled(False) 
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

        # Estado inicial (OJO: No llamamos a reset_ui completo aquí para no sobrescribir el estado disabled)
        self.lbl_phase.setText("Esperando estado listo...")
        self.progress_bar.setValue(0)
        self.timer.stop()

    def reset_ui(self):
        """Vuelve al estado inicial"""
        self.limpieza_en_curso = False
        self.current_phase = "Esperando condiciones..."
        self.lbl_phase.setText(self.current_phase)
        self.progress_bar.setValue(0)
        self.lbl_time.setText("Tiempo restante: --:--")
        
        # El botón vuelve a estar deshabilitado hasta que se lea el estado 12 de nuevo
        self.btn_start.setEnabled(False) 
        self.btn_start.setText("Iniciar limpieza")
        
        # Reconectamos la señal original por si se cambió a reset_ui en finish_cleaning
        try:
            self.btn_start.clicked.disconnect()
        except:
            pass
        self.btn_start.clicked.connect(self.start_cleaning)
        
        self.timer.stop()

    def start_cleaning(self):
        """Inicia el proceso de limpieza"""
        # Marcar que estamos en proceso para ignorar actualizaciones automáticas del botón
        self.limpieza_en_curso = True
        
        # Enviar comando
        self.write_setpoint("treatmentModeSelection", 3.0)
        
        # Configurar UI
        self.total_time_seconds = 900
        self.remaining_time = self.total_time_seconds

        self.current_phase = "Desinfección química en curso..."
        self.lbl_phase.setText(self.current_phase)
        self.btn_start.setEnabled(False)
        self.btn_start.setText("En proceso...")
        
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
        self.limpieza_en_curso = False # Liberamos para permitir reiniciar si es necesario
        self.current_phase = "Limpieza completada"
        self.lbl_phase.setText(self.current_phase)
        self.lbl_phase.setStyleSheet("color: #6ee7b7; font-size: 36px; font-weight: bold;")
        self.lbl_time.setText("Tiempo restante: 00:00")
        self.progress_bar.setValue(self.total_time_seconds)

        self.btn_start.setText("Reiniciar")
        self.btn_start.setEnabled(True)
        
        # Cambiamos la función del botón para reiniciar la UI
        try:
            self.btn_start.clicked.disconnect()
        except:
            pass
        self.btn_start.clicked.connect(self.reset_ui)

    def actualizar_valores(self, nuevos_valores):
        self.valores = nuevos_valores

        # Si la limpieza ya está en curso, no tocamos el estado del botón
        if self.limpieza_en_curso:
            return

        # Obtenemos el estado (default 0.0)
        current_state = self.valores.get("primingProcessStatus", 0.0)
        
        # Estado 6, infusión
        ES_ESTADO_LISTO = (int(current_state) == 6)

        if ES_ESTADO_LISTO:
            if not self.btn_start.isEnabled():
                self.btn_start.setEnabled(True)
                self.current_phase = "Sistema listo para limpieza"
                self.lbl_phase.setText(self.current_phase)
                self.lbl_phase.setStyleSheet("color: #4ade80; font-size: 32px; font-weight: bold;") # Verde claro
        else:
            # Si no es 12 y no estamos limpiando, deshabilitamos
            if self.btn_start.isEnabled():
                self.btn_start.setEnabled(False)
                # Diccionario opcional para mostrar qué estado es (debug visual)
                nombres_estados = {
                    1: "INICIALIZANDO (1)", 2: "LLENADO TANQUE (2)", 3: "LLENADO LINEA (3)",
                    4: "LLENADO DE CÁMARA (4)", 5: "CALENTAMIENTO DIALIZANTE(5)", 6: "INFUSIÓN (6)",
                    7: "DIÁLISIS (7)",
                    12: "LISTO (HDUF_RDY)"
                }
                nombre = nombres_estados.get(int(current_state), f"ESPERANDO (Estado {int(current_state)})")
                
                self.current_phase = nombre
                self.lbl_phase.setText(self.current_phase)
                self.lbl_phase.setStyleSheet("color: #94a3b8; font-size: 32px; font-weight: bold;") # Gris

    def write_setpoint(self, tag, value):
        try:
            # Lógica para enviar el setpoint (treatmentModeSelection)
            texto = value 
            valor = float(texto)
            print(f"[SETPOINT] Intentando escribir {tag} = {valor}")
            
            target_group = -1
            target_id = -1
            found = False
            
            for group_key, variables_in_group in VARIABLES.items():                
                if isinstance(variables_in_group, dict): 
                    for var_id, info in variables_in_group.items():
                        if info.get("tag") == tag:
                            target_group = group_key
                            target_id = var_id
                            found = True
                            break
                if found: break 
            
            if found and target_group != -1 and target_id != -1:
                if VARIABLES[target_group][target_id].get("rw", False):
                    print(f" -> Variable '{tag}' encontrada: Grupo {hex(target_group)}, ID {target_id}")
                    if self.parent_window and hasattr(self.parent_window, 'serial'):                      
                        self.parent_window.serial.escribir_double(target_group, target_id, valor)
                    else:
                        print(f"[INFO] Serial no conectado.  {tag}: Grupo {hex(target_group)}, ID {target_id}, Valor {valor}")
                else:
                    print(f"[ADVERTENCIA] La variable '{tag}' no es escribible (rw=False en variables_map).")
            else:
                print(f"[ERROR] No se encontró la definición de la variable para el tag '{tag}'.")
            
            self.setFocus()

        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
