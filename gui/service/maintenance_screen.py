# gui/service/maintenance_screen.py
"""
Pantalla de Mantenimiento Preventivo
Incluye: Power On Hours, Horas de Operación en Tratamiento y Horas de Limpieza
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, 
    QHBoxLayout
)
from PySide6.QtCore import Qt
import logging
from gui.components.floating_confirm import FloatingConfirmDialog
from core.state_manager import TreatmentPhase
logger = logging.getLogger(__name__)


class MaintenanceScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Fondo claro forzado
        self.setStyleSheet("""
            MaintenanceScreen {
                background-color: #f8fafc;
                color: #1e293b;
            }
        """)
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Título
        title = QLabel("Mantenimiento Preventivo")
        title.setStyleSheet("color: #1e293b; font-size: 36px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Estilo base para los marcos
        frame_style = """
            QFrame {
                background: #ffffff; 
                border: 1px solid #cbd5e1; 
                border-radius: 10px; 
                padding: 5px;
            }
        """
    
        label_style = """
            color: #475569; 
            font-size: 26px;
            border: none;
        """
        
        value_style = """
            color: #0f172a; 
            font-size: 46px; 
            font-weight: bold;
            border: none;
        """

        # ==================== Power On Hours ====================
        pon_frame = QFrame()
        pon_frame.setStyleSheet(frame_style)
        pon_layout = QVBoxLayout(pon_frame)
        pon_layout.setSpacing(15)
        pon_layout.setAlignment(Qt.AlignCenter)   # Centrado horizontal

        lbl_pon = QLabel("Horas de Máquina Encendida")
        lbl_pon.setStyleSheet(label_style)
        lbl_pon.setAlignment(Qt.AlignCenter)

        self.pon_value = QLabel("00:00:00 hh:mm:ss")
        self.pon_value.setStyleSheet(value_style)
        self.pon_value.setAlignment(Qt.AlignCenter)

        pon_layout.addStretch()          
        pon_layout.addWidget(lbl_pon)
        pon_layout.addWidget(self.pon_value)
        pon_layout.addStretch()          

        main_layout.addWidget(pon_frame)

        # ==================== Horas de Operación ====================
        op_frame = QFrame()
        op_frame.setStyleSheet(frame_style)
        op_layout = QVBoxLayout(op_frame)
        op_layout.setSpacing(15)
        op_layout.setAlignment(Qt.AlignCenter)

        lbl_op = QLabel("Horas de Operación en Tratamiento")
        lbl_op.setStyleSheet(label_style)
        lbl_op.setAlignment(Qt.AlignCenter)

        self.op_value = QLabel("00:00:00 hh:mm:ss")
        self.op_value.setStyleSheet(value_style)
        self.op_value.setAlignment(Qt.AlignCenter)

        op_layout.addStretch()
        op_layout.addWidget(lbl_op)
        op_layout.addWidget(self.op_value)
        op_layout.addStretch()

        main_layout.addWidget(op_frame)

        # ==================== Horas de Limpieza ====================
        clean_frame = QFrame()
        clean_frame.setStyleSheet(frame_style)
        clean_layout = QVBoxLayout(clean_frame)
        clean_layout.setSpacing(15)
        clean_layout.setAlignment(Qt.AlignCenter)

        lbl_clean = QLabel("Horas de Limpieza")
        lbl_clean.setStyleSheet(label_style)
        lbl_clean.setAlignment(Qt.AlignCenter)

        self.clean_value = QLabel("00:00:00 hh:mm:ss")
        self.clean_value.setStyleSheet(value_style)
        self.clean_value.setAlignment(Qt.AlignCenter)

        clean_layout.addStretch()
        clean_layout.addWidget(lbl_clean)
        clean_layout.addWidget(self.clean_value)
        clean_layout.addStretch()

        main_layout.addWidget(clean_frame)

        # Información IMSS
        imss_info = QLabel("Requisito IMSS: Mínimo 350 horas de operación en tratamiento")
        imss_info.setStyleSheet("color: #1e293b; font-size: 24px;")
        imss_info.setWordWrap(True)
        imss_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(imss_info)

        main_layout.addStretch()

        # ==================== Botones de Reset ====================
        btn_style = """
            QPushButton { 
                background: #C4302B; 
                color: #ffffff; 
                font-size: 30px; 
                padding: 5px; 
                border-radius: 8px; 
            }
            QPushButton:hover { 
                background: #991b1b; 
            }
        """

        reset_layout = QHBoxLayout()
        reset_layout.setSpacing(20)

        btn_reset_pon = QPushButton("Resetear Encendido")
        btn_reset_pon.setStyleSheet(btn_style)
        btn_reset_pon.clicked.connect(self.reset_power_on_hours)

        btn_reset_op = QPushButton("Resetear Operación")
        btn_reset_op.setStyleSheet(btn_style)
        btn_reset_op.clicked.connect(self.reset_operation_hours)

        btn_reset_clean = QPushButton("Resetear Limpieza")
        btn_reset_clean.setStyleSheet(btn_style)
        btn_reset_clean.clicked.connect(self.reset_cleaning_hours)

        reset_layout.addWidget(btn_reset_pon)
        reset_layout.addWidget(btn_reset_op)
        reset_layout.addWidget(btn_reset_clean)
        main_layout.addLayout(reset_layout)

    # ==================== Métodos de actualización (Soporte legado por si acaso) ====================
    def update_power_on_hours(self, hours: int, minutes: int, seconds: int = 0):
        self.pon_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d} hh:mm:ss")

    def update_operation_hours(self, hours: int, minutes: int, seconds: int = 0):
        self.op_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d} hh:mm:ss")

    def update_cleaning_hours(self, hours: int, minutes: int, seconds: int = 0):
        self.clean_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d} hh:mm:ss")

    # ==================== Métodos de reset ====================
    def reset_power_on_hours(self):
        if self._confirm_reset("Power On Hours"):
            if self.parent_window:
                if hasattr(self.parent_window, 'timer_manager'):
                    self.parent_window.timer_manager.power_on_hours = 0.0
                    self.parent_window.timer_manager._save_power_on_hours()
                self.pon_value.setText("00:00:00 hh:mm:ss")
                logger.warning("Power On Hours fue reseteado por técnico")

    def reset_operation_hours(self):
        if self._confirm_reset("Horas de Operación en Tratamiento"):
            if self.parent_window:
                if hasattr(self.parent_window, 'timer_manager'):
                    self.parent_window.timer_manager.total_operation_hours = 0.0
                    self.parent_window.timer_manager._save_operation_hours()
                self.op_value.setText("00:00:00 hh:mm:ss")
                logger.warning("Horas de Operación en Tratamiento fueron reseteadas por técnico")

    def reset_cleaning_hours(self):
        if self._confirm_reset("Horas de Limpieza"):
            if self.parent_window:
                if hasattr(self.parent_window, 'timer_manager'):
                    self.parent_window.timer_manager.cleaning_hours = 0.0
                    self.parent_window.timer_manager._save_cleaning_hours()
                self.clean_value.setText("00:00:00 hh:mm:ss")
                logger.warning("Horas de Limpieza fueron reseteadas por técnico")
                
    def _confirm_reset(self, counter_name: str) -> bool:
        dialog = FloatingConfirmDialog(self)
        mensaje = f"¿Estás seguro de resetear {counter_name}?\nEsta acción es irreversible.\nPresiona 'Resetear' si estás completamente seguro."
        return dialog.show_confirm(mensaje, accept_text="Sí, Resetear", cancel_text="Cancelar")

    def update_hours_display(self, power_on: float, operation: float, cleaning: float):
        """Actualiza los displays de horas en tiempo real desde TimerManager calculando Segundos"""
        try:
            # Función auxiliar para convertir las horas en formato decimal a H:M:S
            def convert_to_hms(decimal_hours):
                total_seconds = int(decimal_hours * 3600)
                h = total_seconds // 3600
                m = (total_seconds % 3600) // 60
                s = total_seconds % 60
                return h, m, s

            # Power On
            po_h, po_m, po_s = convert_to_hms(power_on)
            self.pon_value.setText(f"{po_h:02d}:{po_m:02d}:{po_s:02d} hh:mm:ss")

            # Operation
            op_h, op_m, op_s = convert_to_hms(operation)
            self.op_value.setText(f"{op_h:02d}:{op_m:02d}:{op_s:02d} hh:mm:ss")

            # Cleaning
            cl_h, cl_m, cl_s = convert_to_hms(cleaning)
            self.clean_value.setText(f"{cl_h:02d}:{cl_m:02d}:{cl_s:02d} hh:mm:ss")

        except Exception as e:
            logger.warning(f"Error actualizando horas en MaintenanceScreen: {e}")
            
    def update_state(self, phase: TreatmentPhase):
        pass
