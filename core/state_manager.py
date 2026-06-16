#core/state_manager.py

import logging
from enum import Enum, auto 
from datetime import datetime 
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, Signal 

logger = logging.getLogger(__name__)

class TreatmentPhase(Enum):
    IDLE = auto()
    PREPARING = auto()   # priming state - cebado 
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHING = auto()
    CLEANING = auto()
    ERROR = auto()


class AppStateManager(QObject):
    """Gestor centralizado de estados"""

    #==================SEÑALES======================350405855393267


    state_changed = Signal(TreatmentPhase, str)     # fase - motivo de activación 
    treatment_started = Signal(datetime)
    treatment_paused = Signal()
    treatment_ready = Signal()
    treatment_resumed = Signal()
    treatment_finished = Signal()
    cleaning_started = Signal()
    cleaning_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()  # heredar de QObject
        self.current_phase: TreatmentPhase = TreatmentPhase.IDLE
        self.therapy_start_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        self.state_history: list = []

    # ===================== MÉTODOS PRINCIPALES =====================

    def set_phase(self, new_phase: TreatmentPhase, reason: str = "") -> bool:
        """Cambia de fase de forma segura y emite señales"""
        if self.current_phase == new_phase:
            return True

        if not self._is_valid_transition(self.current_phase, new_phase):
            logger.error(f"Transición inválida: {self.current_phase.name} → {new_phase.name} | {reason}")
            self.error_occurred.emit(f"Transición inválida: {self.current_phase.name} → {new_phase.name}")
            return False

        old_phase = self.current_phase
        self.current_phase = new_phase
        self.last_state_change = datetime.now()

        self._update_derived_flags()
        self._handle_phase_transitions(old_phase, new_phase, reason)

        # Registrar historial
        self.state_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": old_phase.name,
            "to": new_phase.name,
            "reason": reason
        })

        logger.info(f"Estado: {old_phase.name} → {new_phase.name} | {reason}")

        # Emitir señal principal
        self.state_changed.emit(new_phase, reason)

        return True

    
    def _update_derived_flags(self):
        """Actualiza flags derivados"""
        pass  # agregar propiedades si son necesarias 

    def _handle_phase_transitions(self, old, new, reason):
        """Maneja lógica específica por transición"""
        if new == TreatmentPhase.RUNNING and old != TreatmentPhase.RUNNING:
            if not self.therapy_start_time:
                self.therapy_start_time = datetime.now()
            self.treatment_started.emit(self.therapy_start_time)

        elif new == TreatmentPhase.PAUSED:
            self.treatment_paused.emit()
        elif new == TreatmentPhase.RUNNING and old == TreatmentPhase.PAUSED:
            self.treatment_resumed.emit()
        elif new == TreatmentPhase.READY:
            self.treatment_ready.emit()
        elif new == TreatmentPhase.FINISHING:
            self.treatment_finished.emit()
        elif new == TreatmentPhase.CLEANING:
            self.cleaning_started.emit()
        elif new == TreatmentPhase.IDLE:
            if old == TreatmentPhase.CLEANING:
                self.cleaning_finished.emit()
            if old in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.READY):
                self.treatment_finished.emit()

    def reset_to_idle(self, reason: str = "Reset manual"):
        """Vuelve a estado idle"""
        self.therapy_start_time = None
        return self.set_phase(TreatmentPhase.IDLE, reason)

    def get_state_info(self) -> Dict[str, Any]:
        """Información actual del estado"""
        return {
            "phase": self.current_phase.name,
            "is_treatment_running": self.current_phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, TreatmentPhase.READY),
            "is_cleaning_in_progress": self.current_phase == TreatmentPhase.CLEANING,
            "is_paused": self.current_phase == TreatmentPhase.PAUSED,
            "is_ready": self.current_phase == TreatmentPhase.READY,
            "therapy_duration_minutes": self.get_therapy_duration(),
            "last_change": self.last_state_change.isoformat()
        }

    def get_therapy_duration(self) -> int:
        if not self.therapy_start_time:
            return 0
        return int((datetime.now() - self.therapy_start_time).total_seconds() / 60)
    
    def _is_valid_transition(self, current: TreatmentPhase, new: TreatmentPhase) -> bool:
        """Define reglas de transición seguras"""
        allowed = {
            TreatmentPhase.IDLE: [TreatmentPhase.PREPARING, TreatmentPhase.CLEANING, TreatmentPhase.READY, TreatmentPhase.ERROR],
            TreatmentPhase.PREPARING: [TreatmentPhase.READY, TreatmentPhase.IDLE, TreatmentPhase.ERROR, TreatmentPhase.CLEANING],
            TreatmentPhase.READY: [TreatmentPhase.RUNNING, TreatmentPhase.IDLE, TreatmentPhase.ERROR, TreatmentPhase.CLEANING],            
            TreatmentPhase.RUNNING: [TreatmentPhase.PAUSED, TreatmentPhase.FINISHING, TreatmentPhase.ERROR, TreatmentPhase.IDLE],
            TreatmentPhase.PAUSED: [TreatmentPhase.RUNNING, TreatmentPhase.FINISHING, TreatmentPhase.IDLE],
            TreatmentPhase.FINISHING: [TreatmentPhase.IDLE],
            TreatmentPhase.CLEANING: [TreatmentPhase.IDLE],
            TreatmentPhase.ERROR: [TreatmentPhase.IDLE]
        }
        return new in allowed.get(current, [])


