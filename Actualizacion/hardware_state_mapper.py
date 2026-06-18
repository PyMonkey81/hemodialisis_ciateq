"""Traductor de estados de hardware a pasos del GRAFCET."""

import logging
from enum import Enum, auto

from Actualizacion.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)


class TreatmentMode(Enum):
    DIALYSIS = 0
    HEMODIAFILTRATION = 1
    ULTRAFILTRATION = 2
    CLEANING = 3


class HardwareStateMapper:
    STATUS_TO_PHASE = {
        1: TreatmentPhase.IDLE,
        13: TreatmentPhase.READY,
        14: TreatmentPhase.RUNNING,
        15: TreatmentPhase.PAUSED,
        16: TreatmentPhase.IDLE,
    }

    PREPARING_STATUSES = set(range(2, 13))
    CLEANING_ACTIVE_STATUS = 6
    CLEANING_PREPARATION_STATUSES = {2, 3, 4, 5}

    @staticmethod
    def get_phase(status_code: int, treatment_mode: int = TreatmentMode.DIALYSIS.value) -> TreatmentPhase:
        code = int(status_code)
        mode = int(treatment_mode)

        if mode == TreatmentMode.CLEANING.value:
            if code == HardwareStateMapper.CLEANING_ACTIVE_STATUS:
                return TreatmentPhase.CLEANING
            if code in HardwareStateMapper.CLEANING_PREPARATION_STATUSES:
                return TreatmentPhase.PREPARING

        if code in HardwareStateMapper.STATUS_TO_PHASE:
            return HardwareStateMapper.STATUS_TO_PHASE[code]

        if code in HardwareStateMapper.PREPARING_STATUSES:
            return TreatmentPhase.PREPARING

        return TreatmentPhase.IDLE

    @staticmethod
    def is_operation_step(status_code: int, treatment_mode: int = TreatmentMode.DIALYSIS.value) -> bool:
        return int(status_code) == 14 and int(treatment_mode) != TreatmentMode.CLEANING.value

    @staticmethod
    def is_cleaning_step(status_code: int, treatment_mode: int = TreatmentMode.CLEANING.value) -> bool:
        return int(treatment_mode) == TreatmentMode.CLEANING.value and int(status_code) == HardwareStateMapper.CLEANING_ACTIVE_STATUS

    @staticmethod
    def get_display_text(status_code: int, treatment_mode: int = TreatmentMode.DIALYSIS.value) -> str:
        code = int(status_code)
        mode = int(treatment_mode)

        if mode == TreatmentMode.CLEANING.value and code == HardwareStateMapper.CLEANING_ACTIVE_STATUS:
            return "LIMPIEZA EN\nPROGRESO..."

        descriptions = {
            1: "ESPERA",
            2: "LLENADO DE TANQUE",
            3: "LLENADO DE LINEA",
            4: "LLENADO DE CÁMARA",
            5: "CALENTAMIENTO",
            6: "INFUSIÓN",
            7: "COLOCAR FILTRO",
            8: "DIÁLISIS",
            9: "BYPASS",
            10: "CERRADO",
            12: "ULTRAFILT. OFF",
            13: "LISTO PARA\nINICIAR",
            14: "TERAPIA EN CURSO",
            15: "PAUSA",
            16: "TRATAMIENTO\nDETENIDO",
        }

        return descriptions.get(code, f"Preparando ({code})")
