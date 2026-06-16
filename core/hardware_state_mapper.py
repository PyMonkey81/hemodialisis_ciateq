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

        # Caso especial: Limpieza
        if mode == 3 and code == 6:
            return TreatmentPhase.CLEANING

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
            return "Limpieza en progreso"

        descriptions = {
            1: "Espera",
            2: "Preparando",
            3: "Preparando",
            4: "Preparando",
            5: "Preparando",
            6: "Infusión",           # Solo se ve si NO eslimpieza 
            7: "Colocar filtro",
            8: "Diálisis",
            9: "Bypass",
            10: "Cerrado",
            12: "Ultrafilt. Off",
            13: "Listo para iniciar",
            14: "Terapia en curso",
            15: "Pausa",
            16: "Tratamiento detenido",
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
    
