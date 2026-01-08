# gui/__init__.py
from .therapy.mainScreen import mainScr
from .therapy.dialysisScreen import dialysisScr

from .service.optionScreen import optionScr
from .service.cleanScreen import cleanScr
from .service.mManualScreen import mManualScr
from .service.pPruebasScreen import pPruebasScr
from .service.cfgRedScreen import cfgRedScr
from .service.ctrlCfgScreen import ctrlCfgScr



#=== PANTALLAS Y WIDGETS 
from .components.keypad import NumpadWidget
from .components.keypad import TimeLineEdit
from .components.TankGaugeW import TankGauge
from .components.PowerBar import ConductivityBar
from .components.rVariables import monitorVariables
from .components.ToggleSwitch import ToggleSwitch