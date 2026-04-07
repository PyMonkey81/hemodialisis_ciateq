# # gui/service/maintenance_screen.py
# import logging
# from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QMessageBox, QHBoxLayout
# from PySide6.QtCore import Qt, QDateTime
# from PySide6.QtGui import QFont

# logger = logging.getLogger(__name__)

# class MaintenanceScreen(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.parent_window = parent
#         self.setup_ui()

#     def setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setSpacing(25)
#         main_layout.setContentsMargins(40, 40, 40, 40)

#         # Título
#         title = QLabel("Mantenimiento Preventivo")
#         title.setStyleSheet("color: #ffffff; font-size: 40px;")
#         title.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title)

#         # === Power On Hours ===
#         pon_frame = QFrame()
#         pon_frame.setStyleSheet("background: #1e40af; border-radius: 12px; padding: 20px;")
#         pon_layout = QVBoxLayout(pon_frame)

#         lbl_pon = QLabel("Horas de Máquina Encendida (Power On Hours)")
#         lbl_pon.setStyleSheet("color: #ffffff; font-size: 30px;")
#         lbl_pon.setAlignment(Qt.AlignCenter)

#         self.pon_value = QLabel("0.00 h")
#         self.pon_value.setStyleSheet("color: #67e8f9; font-size: 42px; font-weight: bold;")
#         self.pon_value.setAlignment(Qt.AlignCenter)

#         pon_layout.addWidget(lbl_pon)
#         pon_layout.addWidget(self.pon_value)
#         main_layout.addWidget(pon_frame)

#         # === Operation Hours ===
#         op_frame = QFrame()
#         op_frame.setStyleSheet("background: #166534; border-radius: 12px; padding: 20px;")
#         op_layout = QVBoxLayout(op_frame)

#         lbl_op = QLabel("Horas de Operación en Tratamiento")
#         lbl_op.setStyleSheet("color: #ffffff; font-size: 30px;")
#         lbl_op.setAlignment(Qt.AlignCenter)

#         self.op_value = QLabel("0.00 h")
#         self.op_value.setStyleSheet("color: #86efac; font-size: 42px; font-weight: bold;")
#         self.op_value.setAlignment(Qt.AlignCenter)

#         op_layout.addWidget(lbl_op)
#         op_layout.addWidget(self.op_value)
#         main_layout.addWidget(op_frame)

#         # Información IMSS
#         imss_info = QLabel("Requisito IMSS: Mínimo 350 horas de operación en tratamiento")
#         imss_info.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: bold;")
#         imss_info.setWordWrap(True)
#         imss_info.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(imss_info)

#         main_layout.addStretch()

#         # Botones de reset separados y protegidos
#         reset_layout = QHBoxLayout()

#         btn_reset_pon = QPushButton("Resetear Power On Hours")
#         btn_reset_pon.setStyleSheet("background: #b91c1c; color: white; font-size: 18px; padding: 12px;")
#         btn_reset_pon.clicked.connect(lambda: self.reset_power_on_hours())

#         btn_reset_op = QPushButton("Resetear Horas de Operación")
#         btn_reset_op.setStyleSheet("background: #b91c1c; color: white; font-size: 18px; padding: 12px;")
#         btn_reset_op.clicked.connect(lambda: self.reset_operation_hours())

#         reset_layout.addWidget(btn_reset_pon)
#         reset_layout.addWidget(btn_reset_op)
#         main_layout.addLayout(reset_layout)


#     def update_power_on_hours(self, hours: float):
#         self.pon_value.setText(f"{hours:.2f} horas")

#     def update_operation_hours(self, hours: float):
#         self.op_value.setText(f"{hours:.2f} horas")

#     def reset_all_hours(self):
#         reply = QMessageBox.question(self, "Confirmación de Reset",
#                                     "¿Estás seguro de resetear TODAS las horas?\n\n"
#                                     "Esta acción es irreversible y debe ser realizada solo por técnico autorizado.",
#                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
#         if reply == QMessageBox.Yes and self.parent_window:
#             self.parent_window.power_on_hours = 0.0
#             self.parent_window.total_operation_hours = 0.0
#             self.parent_window._save_power_on_hours()
#             self.parent_window._save_operation_hours()
#             self.pon_value.setText("0.00 horas")
#             self.op_value.setText("0.00 horas")
#             logger.warning("¡Ambos contadores de horas fueron reseteados!")

#     def reset_power_on_hours(self):
#         if not self._confirm_reset("Power On Hours"):
#             return
#         if self.parent_window:
#             self.parent_window.power_on_hours = 0.0
#             self.parent_window._save_power_on_hours()
#             self.pon_value.setText("0.00 horas")
#             logger.warning("Power On Hours reseteado por técnico")

#     def reset_operation_hours(self):
#         if not self._confirm_reset("Horas de Operación en Tratamiento"):
#             return
#         if self.parent_window:
#             self.parent_window.total_operation_hours = 0.0
#             self.parent_window._save_operation_hours()
#             self.op_value.setText("0.00 horas")
#             logger.warning("Horas de Operación en Tratamiento reseteadas por técnico")

#     def _confirm_reset(self, counter_name: str) -> bool:
#         """Confirmación fuerte + registro"""
#         msg = QMessageBox(self)
#         msg.setIcon(QMessageBox.Warning)
#         msg.setWindowTitle("Reset de Contador - Acción Crítica")
#         msg.setText(f"¿Estás seguro de resetear **{counter_name}**?\n\n"
#                     "Esta acción es irreversible y debe ser realizada solo por técnico autorizado.\n"
#                     "Se registrará esta acción en el log del sistema.")
#         msg.setInformativeText("Escribe 'RESET' para confirmar:")
#         msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
#         msg.setDefaultButton(QMessageBox.No)

#         # Para mayor seguridad podrías pedir una contraseña aquí en el futuro
#         reply = msg.exec()
#         return reply == QMessageBox.Yes
# gui/service/maintenance_screen.py
"""
Pantalla de Mantenimiento Preventivo
Incluye: Power On Hours y Horas de Operación en Tratamiento
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, 
    QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)

class MaintenanceScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Título
        title = QLabel("Mantenimiento Preventivo")
        title.setStyleSheet("color: #000000; font-size: 40px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Power On Hours
        pon_frame = QFrame()
        pon_frame.setStyleSheet("background: #1e40af; border-radius: 12px; padding: 25px;")
        pon_layout = QVBoxLayout(pon_frame)

        lbl_pon = QLabel("Horas de Máquina Encendida")
        lbl_pon.setStyleSheet("color: #ffffff; font-size: 26px;")
        lbl_pon.setAlignment(Qt.AlignCenter)

        self.pon_value = QLabel("00:00 h:m")
        self.pon_value.setStyleSheet("color: #67e8f9; font-size: 46px; font-weight: bold;")
        self.pon_value.setAlignment(Qt.AlignCenter)

        pon_layout.addWidget(lbl_pon)
        pon_layout.addWidget(self.pon_value)
        main_layout.addWidget(pon_frame)

        # Horas de Operación en Tratamiento
        op_frame = QFrame()
        op_frame.setStyleSheet("background: #166534; border-radius: 12px; padding: 25px;")
        op_layout = QVBoxLayout(op_frame)

        lbl_op = QLabel("Horas de Operación en Tratamiento")
        lbl_op.setStyleSheet("color: #ffffff; font-size: 26px;")
        lbl_op.setAlignment(Qt.AlignCenter)

        self.op_value = QLabel("0.00 h")
        self.op_value.setStyleSheet("color: #86efac; font-size: 46px; font-weight: bold;")
        self.op_value.setAlignment(Qt.AlignCenter)

        op_layout.addWidget(lbl_op)
        op_layout.addWidget(self.op_value)
        main_layout.addWidget(op_frame)

        # Información IMSS
        imss_info = QLabel("Requisito IMSS: Mínimo 350 horas de operación en tratamiento")
        imss_info.setStyleSheet("color: #000000; font-size: 26px; font-weight: bold;")
        imss_info.setWordWrap(True)
        imss_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(imss_info)

        main_layout.addStretch()

        # Botones de reset separados y protegidos
        reset_layout = QHBoxLayout()
        reset_layout.setSpacing(15)

        btn_reset_pon = QPushButton("Resetear Power On Hours")
        btn_reset_pon.setStyleSheet("""
            QPushButton { background: #b91c1c; color: #ffffff; font-size: 18px; padding: 15px; border-radius: 8px; }
            QPushButton:hover { background: #991b1b; }
        """)
        btn_reset_pon.clicked.connect(self.reset_power_on_hours)

        btn_reset_op = QPushButton("Resetear Horas de Operación")
        btn_reset_op.setStyleSheet("""
            QPushButton { background: #b91c1c; color: #ffffff; font-size: 18px; padding: 15px; border-radius: 8px; }
            QPushButton:hover { background: #991b1b; }
        """)
        btn_reset_op.clicked.connect(self.reset_operation_hours)

        reset_layout.addWidget(btn_reset_pon)
        reset_layout.addWidget(btn_reset_op)
        main_layout.addLayout(reset_layout)

    # def update_power_on_hours(self, hours: float, minutes: float):
    #     self.pon_value.setText(f"{hours:.0f}:{minutes:02.0f} hh:mm")
    def update_power_on_hours(self, hours: int, minutes: int): # CAMBIO: hours y minutes como int
        # Mejor que un flotante, ya que son enteros para la visualización HH:MM
        self.pon_value.setText(f"{hours:02d}:{minutes:02d} hh:mm") # CAMBIO: :02d para formato HH:MM
        # Esto asegurará que 5 se muestre como 05.
    def update_operation_hours(self, hours: int, minutes: int): # ASUMIMOS un método similar para OP Hours
        # Si no lo tienes, deberías crearlo.
        self.op_value.setText(f"{hours:02d}:{minutes:02d} hh:mm") # CAMBIO: :02d para formato HH:MM

    # def update_operation_hours(self, hours: float):
    #     self.op_value.setText(f"{hours:.2f} h")

    def reset_power_on_hours(self):
        if self._confirm_reset("Power On Hours"):
            if self.parent_window:
                self.parent_window.power_on_hours = 0.0
                self.parent_window._save_power_on_hours()
                self.pon_value.setText("0.00 h")
                logger.warning("Power On Hours fue reseteado por técnico")

    def reset_operation_hours(self):
        if self._confirm_reset("Horas de Operación en Tratamiento"):
            if self.parent_window:
                self.parent_window.total_operation_hours = 0.0
                self.parent_window._save_operation_hours()
                self.op_value.setText("0.00 h")
                logger.warning("Horas de Operación en Tratamiento fueron reseteadas por técnico")

    def _confirm_reset(self, counter_name: str) -> bool:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirmación Crítica")
        msg.setText(f"¿Resetear {counter_name}?")
        msg.setInformativeText("Esta acción es irreversible.\n\nEscribe 'RESET' si estás seguro.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        reply = msg.exec()
        return reply == QMessageBox.Yes