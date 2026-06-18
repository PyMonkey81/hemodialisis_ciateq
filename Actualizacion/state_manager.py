"""Gestor de estado central inspirado en GRAFCET."""

import logging
from enum import Enum, auto
from datetime import datetime
from typing import Dict, Any

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class TreatmentPhase(Enum):
    IDLE = auto()
    PREPARING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHING = auto()
    CLEANING = auto()
    ERROR = auto()


class AppStateManager(QObject):
    """Motor de estados que controla transiciones válidas y emite señales."""

    state_changed = Signal(TreatmentPhase, str)
    treatment_started = Signal(datetime)
    treatment_paused = Signal()
    treatment_resumed = Signal()
    treatment_finished = Signal()
    cleaning_started = Signal()
    cleaning_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_phase: TreatmentPhase = TreatmentPhase.IDLE
        self.last_state_change: datetime = datetime.now()
        self.state_history: list[dict[str, Any]] = []

    def set_phase(self, new_phase: TreatmentPhase, reason: str = "") -> bool:
        if self.current_phase == new_phase:
            logger.debug("Intento de cambio a fase igual, no se modifica")
            return True

        if not self._is_valid_transition(self.current_phase, new_phase):
            message = f"Transición inválida: {self.current_phase.name} → {new_phase.name}"
            logger.error(f"{message} | {reason}")
            self.error_occurred.emit(message)
            return False

        old_phase = self.current_phase
        self.current_phase = new_phase
        self.last_state_change = datetime.now()
        self._handle_phase_transitions(old_phase, new_phase, reason)

        self.state_history.append({
            "timestamp": self.last_state_change.isoformat(),
            "from": old_phase.name,
            "to": new_phase.name,
            "reason": reason,
        })

        self.state_changed.emit(new_phase, reason)
        logger.info(f"Estado: {old_phase.name} → {new_phase.name} | {reason}")
        return True

    def _handle_phase_transitions(self, old_phase: TreatmentPhase, new_phase: TreatmentPhase, reason: str) -> None:
        if new_phase == TreatmentPhase.RUNNING and old_phase != TreatmentPhase.RUNNING:
            self.treatment_started.emit(self.last_state_change)
        elif new_phase == TreatmentPhase.PAUSED:
            self.treatment_paused.emit()
        elif new_phase == TreatmentPhase.RUNNING and old_phase == TreatmentPhase.PAUSED:
            self.treatment_resumed.emit()
        elif new_phase == TreatmentPhase.FINISHING:
            self.treatment_finished.emit()
        elif new_phase == TreatmentPhase.CLEANING:
            self.cleaning_started.emit()
        elif new_phase == TreatmentPhase.IDLE:
            if old_phase == TreatmentPhase.CLEANING:
                self.cleaning_finished.emit()
            if old_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.READY):
                self.treatment_finished.emit()

    def _is_valid_transition(self, current: TreatmentPhase, new: TreatmentPhase) -> bool:
        allowed: dict[TreatmentPhase, list[TreatmentPhase]] = {
            TreatmentPhase.IDLE: [TreatmentPhase.PREPARING, TreatmentPhase.READY, TreatmentPhase.CLEANING, TreatmentPhase.ERROR],
            TreatmentPhase.PREPARING: [TreatmentPhase.READY, TreatmentPhase.IDLE, TreatmentPhase.CLEANING, TreatmentPhase.ERROR],
            TreatmentPhase.READY: [TreatmentPhase.RUNNING, TreatmentPhase.IDLE, TreatmentPhase.CLEANING, TreatmentPhase.ERROR],
            TreatmentPhase.RUNNING: [TreatmentPhase.PAUSED, TreatmentPhase.FINISHING, TreatmentPhase.IDLE, TreatmentPhase.ERROR],
            TreatmentPhase.PAUSED: [TreatmentPhase.RUNNING, TreatmentPhase.FINISHING, TreatmentPhase.IDLE, TreatmentPhase.ERROR],
            TreatmentPhase.FINISHING: [TreatmentPhase.IDLE, TreatmentPhase.ERROR],
            TreatmentPhase.CLEANING: [TreatmentPhase.IDLE, TreatmentPhase.ERROR],
            TreatmentPhase.ERROR: [TreatmentPhase.IDLE],
        }
        return new in allowed.get(current, [])

    def reset_to_idle(self, reason: str = "Reset manual") -> bool:
        return self.set_phase(TreatmentPhase.IDLE, reason)

    def get_state_info(self) -> Dict[str, Any]:
        return {
            "phase": self.current_phase.name,
            "is_treatment_running": self.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.READY),
            "is_cleaning_in_progress": self.current_phase == TreatmentPhase.CLEANING,
            "is_paused": self.current_phase == TreatmentPhase.PAUSED,
            "is_ready": self.current_phase == TreatmentPhase.READY,
            "last_change": self.last_state_change.isoformat(),
        }
