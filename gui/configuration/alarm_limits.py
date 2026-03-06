# core/alarm_limits.py
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

from core.variables_map import VARIABLES


class AlarmLimitsManager:
    def __init__(self, config_path: str = "config/alarm_limits.json"):
        self.config_path = Path(config_path)
        self.limits: Dict[str, Tuple[float, float]] = {}  # tag → (min, max)
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
            print(f"Error cargando límites: {e}. Usando defaults.")

    def save(self):
        """Guarda solo los límites que se han personalizado"""
        data = {tag: list(lim) for tag, lim in self.limits.items()}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

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
        self.save()
    
    
    