# gui/screen_state_manager.py
import logging
from PySide6.QtCore import QObject
from core.state_manager import TreatmentPhase

logger = logging.getLogger(__name__)

class ScreenStateManager(QObject):
    """
    Gestor centralizado para actualizar el estado visual de todas las pantallas
    según el TreatmentPhase actual.
    """

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

    def update_all_screens(self, phase: TreatmentPhase):
        """Actualiza todas las pantallas según el estado actual"""
        logger.debug(f"Actualizando pantallas para estado: {phase.name}")

        # Pantalla de Diálisis
        if hasattr(self.main, 'dialysis_screen'):
            self.main.dialysis_screen.update_state(phase)

        # Pantalla de Limpieza
        if hasattr(self.main, 'cleaning_screen'):
            self.main.cleaning_screen.update_state(phase)

        # Pantalla de Mantenimiento
        if hasattr(self.main, 'maintenance_screen'):
            self.main.maintenance_screen.update_state(phase)

        # Pantalla de KTV
        if hasattr(self.main, 'KTVScreen'):
            self.main.KTVScreen.update_state(phase)

        if hasattr(self.main, "therapy_config_screen"):
            self.main.therapy_config_screen.update_state(phase)
        
        

        # Se puede agregar pantallas de la siguiente manera 
        # if hasattr(self.main, 'another_screen'):
        #     self.main.another_screen.update_state(phase)

        logger.debug(f"Actualización de pantallas completada para {phase.name}")