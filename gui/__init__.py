# gui/__init__.py
from .therapy.main_screen import MainScreen
from .therapy.dialysis_screen import DialysisScreen
from .therapy.patient_config_screen import PatientConfigScreen
from .therapy.therapy_config_screen import TherapyConfigScreen
from .therapy.treatment_mode_screen import TreatmentModeScreen

from .service.options_screen import OptionsScreen
from .service.cleaning_screen import CleaningScreen
from .service.manual_mode_screen import ManualModeScreen
from .service.test_panel_screen import TestPanelScreen
from .service.network_config_screen import NetworkConfigScreen
from .service.calibration_screen import CalibrationScreen



#=== PANTALLAS Y WIDGETS 
from .components.tank_gauge import TankGauge
from .components.conductivity_bar import ConductivityBar
from .components.real_time_variables import RealTimeVariablesMonitor
from .components.ToggleSwitch import ToggleSwitch
from .components.numpad_modal import NumpadDialog
from .components.time_numpad_modal import TimeNumpadDialog
from .components.ui_components import ToggleBox
from .components.ui_components import DoubleToggleBox
from .components.ui_components import ClickableLineEdit