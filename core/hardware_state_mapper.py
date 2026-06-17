# core/hardware_state_mapper.py
"""
Traductor centralizado entre estados del hardware y fases de la aplicación.
"""

import logging
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)


class HardwareStateMapper:
    """Mapeo oficial y único de estados del hardware"""

    STATUS_TO_PHASE = {
        1: TreatmentPhase.IDLE,
        13: TreatmentPhase.READY,
        14: TreatmentPhase.RUNNING,
        15: TreatmentPhase.PAUSED,
        16: TreatmentPhase.IDLE,
    }

    PREPARING_STATUSES = set(range(2, 13))

    @staticmethod
    def get_phase(status_code: int, treatment_mode: int = 0) -> TreatmentPhase:
        """Devuelve fase considerando también el modo de tratamiento"""
        code = int(status_code)
        mode = int(treatment_mode)

        # Caso especial: Limpieza (solo cuando realmente está en modo limpieza)
        if mode == 3:
            if code == 6:
                return TreatmentPhase.CLEANING
            elif code in [2, 3, 4, 5]:  
                return TreatmentPhase.PREPARING   # Preparación de limpieza     
            

        # Estados normales
        if code in HardwareStateMapper.STATUS_TO_PHASE:
            return HardwareStateMapper.STATUS_TO_PHASE[code]

        if code in HardwareStateMapper.PREPARING_STATUSES:
            return TreatmentPhase.PREPARING

        return TreatmentPhase.IDLE

    @staticmethod
    def get_display_text(status_code: int, treatment_mode: int = 0) -> str:
        """Texto amigable para mostrar en UI (nunca números crudos)"""
        code = int(status_code)
        mode = int(treatment_mode)

        # Limpieza especial
        if mode == 3 and code == 6:
            return "Limpieza en progreso.."
        # if mode == 3 and code in [2,3,4,5]:
        #     return "Preparando limpieza"

        descriptions = {
            1: "ESPERA",
            2: "LLENADO DE TANQUE",
            3: "LLENADO DE LINEA",
            4: "LLENADO DE CÁMARA",
            5: "CALENTAMIENTO",
            6: "INFUSIÓN",           # Solo se ve si NO es limpieza
            7: "COLOCAR FILTRO",
            8: "Diálisis",
            9: "Bypass",
            10: "Cerrado",
            12: "Ultrafilt. Off",
            13: "LISTO PARA\nINICIAR ",
            14: "TERAPIA EN CURSO",
            15: "PAUSA",
            16: "TRATAMIENTO\n DETENIDO",
        }

        return descriptions.get(code, f"Preparando ({code})")

    @staticmethod
    def should_count_operation_time(status_code: int, treatment_mode: int = 0) -> bool:
        """Solo cuenta tiempo de terapia cuando está realmente en tratamiento"""
        if int(treatment_mode) == 3:  # Limpieza no cuenta como operación
            return False
        return int(status_code) == 14

    @staticmethod
    def is_preparing(status_code: int) -> bool:
        return int(status_code) in HardwareStateMapper.PREPARING_STATUSES
    


# # core/hardware_state_mapper.py
# """
# Traductor centralizado entre estados del hardware (primingProcessStatus)
# y las fases internas de la aplicación (TreatmentPhase).
# """

# import logging
# from core.state_manager import TreatmentPhase

# logger = logging.getLogger(__name__)


# class HardwareStateMapper:
#     """Mapeo oficial y único de estados del hardware"""

#     # Mapeo directo
#     STATUS_TO_PHASE = {
#         1: TreatmentPhase.IDLE,      # INICIO CEBADO / Espera
#         13: TreatmentPhase.READY,
#         14: TreatmentPhase.RUNNING,
#         15: TreatmentPhase.PAUSED,
#         16: TreatmentPhase.IDLE,     # TRATAMIENTO DETENIDO
#     }

#     PREPARING_STATUSES = set(range(2, 13))   # 2 al 12 inclusive

#     @staticmethod
#     def get_phase(status_code: int) -> TreatmentPhase:
#         """Devuelve la fase correspondiente según el hardware"""
#         code = int(status_code)

#         if code in HardwareStateMapper.STATUS_TO_PHASE:
#             return HardwareStateMapper.STATUS_TO_PHASE[code]

#         if code in HardwareStateMapper.PREPARING_STATUSES:
#             return TreatmentPhase.PREPARING

#         # Default seguro
#         return TreatmentPhase.IDLE

#     @staticmethod
#     def should_count_operation_time(status_code: int) -> bool:
#         """Solo cuenta tiempo de terapia cuando el hardware está realmente en RUNNING"""
#         return int(status_code) == 14

#     @staticmethod
#     def is_preparing(status_code: int) -> bool:
#         return int(status_code) in HardwareStateMapper.PREPARING_STATUSES

#     @staticmethod
#     def get_description(status_code: int) -> str:
#         """Descripciones amigables para UI"""
#         desc = {
#             1: "Espera...",
#             7: "Colocar filtro",
#             14: "Tratamiento en curso",
#             13: "Inicia\ntratamiento",
#             15: "Pausa",
#             16: "Tratamiento\ndetenido",
#         }
#         return desc.get(int(status_code), f"Estado {status_code}")