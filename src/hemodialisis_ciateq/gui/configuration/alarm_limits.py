# core/alarm_limits.py

"""
Módulo para la gestión persistente de los límites de alarma.

Este módulo define la clase `AlarmLimitsManager`, que se encarga de almacenar,
cargar y gestionar los umbrales (límites inferior y superior) para las variables
monitoreadas por el sistema de alarmas. Permite establecer límites por defecto
basados en la configuración inicial del sistema y guardar/cargar límites
personalizados por el usuario en un archivo JSON.

Características:
----------------
- **Persistencia:** Guarda los límites de alarma modificados por el usuario
  en un archivo JSON (`config/alarm_limits.json` por defecto) para que persistan
  entre reinicios de la aplicación.
- **Valores por Defecto:** Carga los límites predefinidos de las variables
  críticas desde el módulo `core.variables_map` como valores de respaldo.
- **Gestión de Límites:** Proporciona métodos para obtener los límites actuales
  (personalizados o por defecto), establecer nuevos límites y restaurar a los
  valores predefinidos.
- **Validación Básica:** Asegura que el límite inferior no sea mayor o igual
  que el límite superior al intentar establecer nuevos valores.

Clase principal:
----------------
- `AlarmLimitsManager`: Maneja la lógica de carga, guardado, obtención y
  establecimiento de los límites de alarma.

Dependencias:
-------------
- `json`: Para serializar y deserializar los límites a/desde JSON.
- `pathlib`: Para una gestión de rutas de archivo más robusta.
- `typing`: Para anotaciones de tipo (Dict, Tuple, Optional).
- `core.variables_map`: Fuente de los límites de alarma por defecto.

Uso:
----
Una instancia de `AlarmLimitsManager` debe ser creada una sola vez en el
componente principal de la aplicación (ej. `HemodialysisHMI`) y luego
pasada a cualquier componente que necesite acceder o modificar los límites
de alarma, como `AlarmSystem` o `AlarmsScreen`.
"""


import json
from pathlib import Path
from typing import Dict, Tuple, Optional

from hemodialisis_ciateq.core.variables_map import VARIABLES
import logging
logger = logging.getLogger(__name__)


class AlarmLimitsManager:
    def __init__(self, config_path: str = "config/alarm_limits.json"):
        self.config_path = Path(config_path)
        self.limits: Dict[str, Tuple[float, float]] = {}  
        self.defaults: Dict[str, Tuple[float, float]] = {}
        
        self._load_defaults()
        self._load_from_file()
        self.defaults = {}
        
        for group in VARIABLES.values():
            for idx, info in group.items():
                if "limites" in info and info["limites"] is not None:
                    tag = info.get("tag")
                    if tag:
                        self.defaults[tag] = info["limites"]

    def _load_defaults(self):
        """Extrae los límites por defecto del mapa estático"""
        for group in VARIABLES.values():
            for idx, info in group.items():
                if "limites" in info and info["limites"] is not None:
                    tag = info.get("tag")
                    if tag:
                        self.defaults[tag] = info["limites"]
                        

    def _load_from_file(self):
        if not self.config_path.exists():
            self.save()  
            return
        
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                for tag, (minv, maxv) in data.items():
                    if tag in self.defaults:  
                        self.limits[tag] = (float(minv), float(maxv))
        except Exception as e:
            logger.error(f"Error cargando límites: {e}. Usando defaults.")

    def save(self):
        """Guarda solo los límites que se han personalizado"""
        data = {tag: list(lim) for tag, lim in self.limits.items()}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Límites de alarma guardados en {self.config_path}")

    def get_limits(self, tag: str) -> Tuple[float, float]:
        """Devuelve límites personalizados o por defecto"""
        return self.limits.get(tag) or self.defaults.get(tag, (-9999.0, 9999.0))

    def set_limits(self, tag: str, min_val: float, max_val: float):
        if min_val >= max_val:
            raise ValueError("Límite inferior debe ser menor que el superior")
        self.limits[tag] = (min_val, max_val)
        self.save()

    def reset_to_default(self, tag: str = None):
        if tag:
            self.limits.pop(tag, None)
        else:
            self.limits.clear()
            logger.info("Todos los límites de alarma han sido restablecidos a los valores por defecto.")
        self.save()
        logger.info(f"Límite(s) de alarma restablecido(s) a valores por defecto: {tag if tag else 'todos'}")    
    
    
    