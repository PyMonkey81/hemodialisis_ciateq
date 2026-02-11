# gui/therapy/alarmsScreen.py
# Pantalla dedicada SOLO a alarmas activas + log/historial
# stacked index 5 (Alarmas)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame,
    QPushButton, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont

from PySide6.QtWidgets import *

from core.variables_map import VARIABLES

class alarmsScr(QWidget):
    def __init__(self, parent=None, valores_dict=None, sistema_alarmas=None):
        super().__init__(parent)
        self.setStyleSheet("background: #f8fafc; font-family: 'Segoe UI';")

        self.setStyleSheet("background: #0f172a;")

   
        # Guardamos referencias
        self.valores = valores_dict if valores_dict is not None else {}
        self.sistema_alarmas = sistema_alarmas
        
        self.setFixedSize(1536, 726)
        self.setStyleSheet("background: #0f172a; color: #e2e8f0;")

        # Diccionario: nombre_alarma → (valor, nivel, hora_activacion)
        self.alarmas_activas = {}

        self.setup_ui()

        # Conexiones y sincronización inicial
        if self.sistema_alarmas:
            print("alarmsScr: sistema_alarmas encontrado. Cantidad de alarmas conocidas:", 
                  len(getattr(self.sistema_alarmas, 'nombres', [])))
            
            self.sistema_alarmas.cambio_alarma.connect(self.on_cambio_alarma)
            self.sistema_alarmas.nuevo_evento.connect(self.on_nuevo_evento)
            
            # ¡Importante! Sincronizar el estado actual de las alarmas
            self._sincronizar_estado_inicial()
        else:
            print("Advertencia: sistema_alarmas no disponible en alarmsScr")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)

        # Título
        title = QLabel("ALARMAS Y EVENTOS DEL SISTEMA")
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #f87171;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #475569; max-height: 2px;")
        layout.addWidget(sep1)

        # Alarmas Activas
        lbl_active = QLabel("ALARMAS ACTIVAS")
        lbl_active.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #ef4444; 
            background: transparent;
            padding: 8px 0;
        """)
        layout.addWidget(lbl_active)

        self.active_display = QTextEdit()
        self.active_display.setReadOnly(True)
        self.active_display.setStyleSheet("""
            QTextEdit {
                background: #1e293b;
                color: #fef2f2;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 20px;
                border: 2px solid #7f1d1d;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        self.active_display.setMinimumHeight(220)
        layout.addWidget(self.active_display)

        # Botón Reconocer todas
        btn_ack = QPushButton("RECONOCER TODAS")
        btn_ack.setFixedSize(320, 60)
        btn_ack.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                font-size: 22px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background: #b91c1c; }
            QPushButton:pressed { background: #991b1b; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)
        btn_ack.clicked.connect(self.acknowledge_all)
        layout.addWidget(btn_ack, alignment=Qt.AlignRight)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #475569; max-height: 2px;")
        layout.addWidget(sep2)

        # Historial
        lbl_log = QLabel("HISTORIAL COMPLETO")
        lbl_log.setStyleSheet("""
            font-size: 26px; 
            font-weight: bold; 
            color: #94a3b8;
        """)
        layout.addWidget(lbl_log)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background: #0f172a;
                color: #cbd5e1;
                font-family: Consolas, monospace;
                font-size: 17px;
                border: none;
                padding: 8px;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidget(self.log_display)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setMinimumHeight(280)
        layout.addWidget(scroll)

        # Mensaje inicial
        self._actualizar_alarmas_activas()
        self.log_display.append(
            f'<span style="color:#64748b;">[Sistema iniciado — {QTime.currentTime().toString("hh:mm:ss")}]</span>'
        )

    def _sincronizar_estado_inicial(self):
        """Lee el estado actual de todas las alarmas y actualiza alarmas_activas"""
        if not hasattr(self.sistema_alarmas, 'nombres') or \
           not hasattr(self.sistema_alarmas, 'ultimo_estado') or \
           not hasattr(self.sistema_alarmas, 'niveles'):
            print("alarmsScr: sistema_alarmas no tiene los atributos esperados (nombres, ultimo_estado, niveles)")
            return

        hora = QTime.currentTime().toString("hh:mm:ss")
        alarmas_cargadas = 0

        for i, nombre in enumerate(self.sistema_alarmas.nombres):
            if i < len(self.sistema_alarmas.ultimo_estado) and self.sistema_alarmas.ultimo_estado[i]:
                nivel = self.sistema_alarmas.niveles[i] if i < len(self.sistema_alarmas.niveles) else "info"
                valor = None  # Puedes intentar obtenerlo de self.valores si tienes el tag mapeado
                self.alarmas_activas[nombre] = (valor, nivel, hora)
                alarmas_cargadas += 1
                # Opcional: registrar en historial como "ya activa al abrir pantalla"
                # self._agregar_al_historial(nombre, valor, nivel, True, hora + " (inicial)")

        print(f"alarmsScr: sincronización inicial → {alarmas_cargadas} alarmas activas cargadas")
        self._actualizar_alarmas_activas()

    def on_cambio_alarma(self, idx, activada, valor, nombre, nivel, limites):
        hora = QTime.currentTime().toString("hh:mm:ss")

        if activada:
            self.alarmas_activas[nombre] = (valor, nivel, hora)
        else:
            self.alarmas_activas.pop(nombre, None)

        self._actualizar_alarmas_activas()
        self._agregar_al_historial(nombre, valor, nivel, activada, hora)

    def on_nuevo_evento(self, evento, valor, hora):
        self._agregar_al_historial(evento, valor, "info", True, hora)

    def _actualizar_alarmas_activas(self):
        if not self.alarmas_activas:
            html = '<center><span style="color:#94a3b8; font-size:20px;">Ninguna alarma activa en este momento</span></center>'
        else:
            prio_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1, "info": 0}
            ordenadas = sorted(
                self.alarmas_activas.items(),
                key=lambda x: prio_map.get(x[1][1], 0),
                reverse=True
            )

            lineas = []
            for nombre, (valor, nivel, hora) in ordenadas:
                color = {
                    "rojo": "#f87171",
                    "naranja": "#fb923c",
                    "amarillo": "#fbbf24",
                    "cian": "#22d3ee",
                    "info": "#94a3b8"
                }.get(nivel, "#cbd5e1")

                val_str = f"  {valor:.1f}" if valor is not None else ""
                linea = (
                    f'<span style="color:{color}; font-weight:bold; font-size:21px;">'
                    f'[{hora}]  {nombre.upper()}{val_str}</span>'
                    f'<span style="color:#64748b; font-size:18px;">  — {nivel.upper()}</span>'
                )
                lineas.append(linea)

            html = "<br>".join(lineas)

        self.active_display.setHtml(html)

    def _agregar_al_historial(self, texto, valor, nivel, activada, hora):
        color = {
            "rojo": "#f87171",
            "naranja": "#fb923c",
            "amarillo": "#fbbf24",
            "cian": "#22d3ee",
            "info": "#94a3b8"
        }.get(nivel, "#94a3b8")

        if nivel == "info":
            estado = ""
            val_str = ""
        else:
            estado = "ACTIVADA" if activada else "DESACTIVADA"
            val_str = f" ({valor:.1f})" if valor is not None and valor != 0 else ""

        linea = (
            f'<span style="color:#64748b;">[{hora}]</span> '
            f'<span style="color:{color}; font-weight:bold;">'
            f'{estado} {texto}{val_str}</span>'
        )

        self.log_display.append(linea)
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def acknowledge_all(self):
        if not self.alarmas_activas:
            QMessageBox.information(self, "Info", "No hay alarmas activas.")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Reconocer TODAS las alarmas activas?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.alarmas_activas.clear()
            self._actualizar_alarmas_activas()
            hora = QTime.currentTime().toString("hh:mm:ss")
            self._agregar_al_historial("Todas las alarmas reconocidas por el usuario", None, "info", True, hora)
            QMessageBox.information(self, "Listo", "Alarmas reconocidas.")

    def actualizar_valores(self, valores_dict):
        """Método para compatibilidad con otras pantallas"""
        self.valores = valores_dict
        # No se usa directamente aquí

    def write_setpoint(self, tag, widget_input):
        try:
            texto = widget_input.text().replace(',', '.')
            if not texto:                 
                current_value = self.valores.get(tag, 0.0)
                widget_input.setText(f"{current_value:.1f}") 
                return 
                
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
            
            widget_input.clearFocus()
            self.setFocus()

        except ValueError:
            print(f"[ERROR] Valor numérico inválido en input para {tag}: {widget_input.text()}")
            val = self.valores.get(tag, 0.0)
            widget_input.setText(f"{val:.1f}")
            widget_input.clearFocus()
        except Exception as e:
            print(f"[ERROR] Ocurrió un error inesperado al escribir setpoint para {tag}: {e}")
  