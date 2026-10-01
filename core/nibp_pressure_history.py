# core/nibp_pressure_history.py
"""
Historial en memoria de mediciones de presión arterial (NIBP) para UNA terapia.
Se almacena en la sesión sin persistencia a disco.

Cada toma válida contiene:
  - n: número secuencial
  - elapsed_s: segundos desde inicio de RUNNING (None si todavía no está RUNNING)
  - sys, dia, map, hr, spo2: valores o None
  - origen: "manual" o "auto"
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class NibpPressureMeasurement:
    """Representa una toma de presión válida."""
    
    def __init__(self, n: int, elapsed_s: Optional[int], sys: int, dia: int, 
                 map_mmhg: int, hr: int, spo2: Optional[int], origen: str):
        self.n = n
        self.elapsed_s = elapsed_s  # None si todavía no está RUNNING
        self.sys = sys
        self.dia = dia
        self.map_mmhg = map_mmhg
        self.hr = hr
        self.spo2 = spo2
        self.origen = origen  # "manual" o "auto"
    
    def __repr__(self):
        return (f"NibpMeasurement(n={self.n}, elapsed_s={self.elapsed_s}, "
                f"sys={self.sys}, dia={self.dia}, map={self.map_mmhg}, hr={self.hr}, "
                f"spo2={self.spo2}, origen={self.origen})")


class NibpPressureHistory:
    """Historial en memoria de mediciones de una sesión de terapia."""
    
    def __init__(self):
        self.measurements: List[NibpPressureMeasurement] = []
        self._counter = 0  # número secuencial
        self._therapy_start_timestamp = None  # datetime de inicio de RUNNING
    
    def add_measurement(self, sys: int, dia: int, map_mmhg: int, hr: int,
                       elapsed_s: Optional[int], spo2: Optional[int] = None,
                       origen: str = "auto") -> bool:
        """
        Agrega una toma válida si sys, dia, hr >= 0.
        
        Args:
            sys: presión sistólica (mmHg)
            dia: presión diastólica (mmHg)
            map_mmhg: presión media (MAP, mmHg)
            hr: frecuencia cardíaca (lpm)
            elapsed_s: segundos desde inicio de RUNNING (None si no está RUNNING)
            spo2: saturación de oxígeno (%) o None
            origen: "manual" o "auto"
        
        Returns:
            True si se agregó, False si no cumple criterios
        """
        # Validar que la toma sea válida: measurement_ready, SYS/DIA/HR >= 0
        if sys < 0 or dia < 0 or hr < 0:
            logger.debug(f"[NIBP History] Toma rechazada: sys={sys}, dia={dia}, hr={hr}")
            return False
        
        self._counter += 1
        measurement = NibpPressureMeasurement(
            n=self._counter,
            elapsed_s=elapsed_s,
            sys=sys,
            dia=dia,
            map_mmhg=map_mmhg,
            hr=hr,
            spo2=spo2,
            origen=origen
        )
        
        self.measurements.append(measurement)
        logger.info(f"[NIBP History] Toma #{self._counter}: {measurement}")
        return True
    
    def clear(self):
        """Limpia el historial (cuando se entra a RUNNING desde no-PAUSED)."""
        self.measurements.clear()
        self._counter = 0
        self._therapy_start_timestamp = None
        logger.info("[NIBP History] Historial limpiado")
    
    def get_all_measurements(self) -> List[NibpPressureMeasurement]:
        """Retorna todas las mediciones."""
        return list(self.measurements)
    
    def get_measurements_with_elapsed(self) -> List[NibpPressureMeasurement]:
        """Retorna solo mediciones con elapsed_s (para la gráfica)."""
        return [m for m in self.measurements if m.elapsed_s is not None]
    
    def count(self) -> int:
        """Retorna el número total de mediciones."""
        return len(self.measurements)
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convierte a lista de diccionarios para serialización/logging."""
        return [
            {
                "n": m.n,
                "elapsed_s": m.elapsed_s,
                "sys": m.sys,
                "dia": m.dia,
                "map": m.map_mmhg,
                "hr": m.hr,
                "spo2": m.spo2,
                "origen": m.origen,
            }
            for m in self.measurements
        ]
