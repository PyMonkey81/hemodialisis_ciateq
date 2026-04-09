# core/alarm_config_manager.py
from PySide6.QtCore import QSettings
from typing import List, Tuple, Dict, Set

from core.variables_map import VARIABLES

class AlarmConfigManager:
    """
    Gestor central de configuración de alarmas usando QSettings.
    - enabled_tags: Qué variables están activadas para monitoreo (Servicio Técnico)
    - limits: Límite inferior y superior por tag (Operador)
    - severity: Nivel de alarma por tag (Operador)
    """
    def __init__(self, organization: str = "HemodialisisApp", app_name: str = "AlarmSystem"):
        self.settings = QSettings(organization, app_name)

        # Claves
        self.KEY_ENABLED = "alarms/enabled_tags"
        self.KEY_LIMITS = "alarms/limits"      # dict: tag -> [min, max]
        self.KEY_SEVERITY = "alarms/severity"  # dict: tag -> "cian" | "naranja" | "amarillo" | "rojo"

    # ====================== Métodos para obtener valores por defecto del VARIABLES_MAP ======================
    def _get_default_info_from_variables_map(self, tag: str) -> dict:
        """Helper para buscar la info de una variable en VARIABLES_MAP."""
        for group in VARIABLES.values():
            for info in group.values():
                if info.get("tag") == tag:
                    return info
        return {} # Devuelve diccionario vacío si no se encuentra

    def get_default_limits_from_variables_map(self, tag: str) -> Tuple[float, float]:
        """Devuelve los límites por defecto de VARIABLES_MAP o un fallback."""
        info = self._get_default_info_from_variables_map(tag)
        limits_from_map = info.get("limites")
        if limits_from_map and isinstance(limits_from_map, (list, tuple)) and len(limits_from_map) == 2:
            try:
                return float(limits_from_map[0]), float(limits_from_map[1])
            except ValueError:
                pass # Si los valores en el mapa no son válidos, usar fallback
        return 0.0, 100.0 # Fallback general si no hay límites en el mapa o son inválidos

    def get_default_severity_from_variables_map(self, tag: str) -> str:
        """Devuelve la severidad por defecto de VARIABLES_MAP o un fallback."""
        info = self._get_default_info_from_variables_map(tag)
        severity_from_map = info.get("nivel")
        if severity_from_map and isinstance(severity_from_map, str):
            return severity_from_map
        return "cian" # Fallback general si no hay nivel en el mapa
    
    # ====================== ENABLED TAGS (Servicio Técnico) ======================
    def get_enabled_tags(self) -> List[str]:
        """Devuelve lista de tags habilitados"""
        tags = self.settings.value(self.KEY_ENABLED, [])
        if isinstance(tags, str):          # Seguridad por posible bug en listas de 1 elemento en algunos sistemas
            tags = [tags]
        return tags if isinstance(tags, list) else []

    def set_enabled_tags(self, tags: List[str]):
        """Guarda la lista completa de tags habilitados"""
        self.settings.setValue(self.KEY_ENABLED, tags)
        self.settings.sync()   # Fuerza guardar inmediatamente

    def is_enabled(self, tag: str) -> bool:
        return tag in self.get_enabled_tags()

    def set_enabled(self, tag: str, enabled: bool):
        """Activa o desactiva una sola variable"""
        current = set(self.get_enabled_tags())
        if enabled:
            current.add(tag)
        else:
            current.discard(tag)
        self.set_enabled_tags(sorted(list(current)))

    # ====================== LIMITS (Operador) ======================
    def get_limits(self, tag: str) -> Tuple[float, float]:
        """Devuelve (min, max). Si no existe en QSettings → usa defaults de VARIABLES_MAP."""
        limits_dict: Dict = self.settings.value(self.KEY_LIMITS, {})
        if tag in limits_dict:
            try:
                minv, maxv = limits_dict[tag]
                return float(minv), float(maxv)
            except (ValueError, TypeError):
                pass # Si el formato es incorrecto en QSettings, ignorar y usar el default
        
        return self.get_default_limits_from_variables_map(tag) 

    def set_limits(self, tag: str, min_val: float, max_val: float):
        limits_dict_raw = self.settings.value(self.KEY_LIMITS, {})
        limits_dict = dict(limits_dict_raw) if isinstance(limits_dict_raw, dict) else {}
        limits_dict[tag] = [float(min_val), float(max_val)]
        self.settings.setValue(self.KEY_LIMITS, limits_dict)
        self.settings.sync()
    # ====================== SEVERITY ======================
    def get_severity(self, tag: str) -> str:
        severity_dict_raw = self.settings.value(self.KEY_SEVERITY, {})
        # QSettings puede devolver QVariant, convertimos a dict si es necesario
        severity_dict = dict(severity_dict_raw) if isinstance(severity_dict_raw, dict) else {}
        
        return severity_dict.get(tag, self.get_default_severity_from_variables_map(tag)) # Usa el default del mapa



    def set_severity(self, tag: str, level: str):
        severity_dict_raw = self.settings.value(self.KEY_SEVERITY, {})
        # QSettings puede devolver QVariant, convertimos a dict si es necesario
        severity_dict = dict(severity_dict_raw) if isinstance(severity_dict_raw, dict) else {}

        severity_dict[tag] = level
        self.settings.setValue(self.KEY_SEVERITY, severity_dict)
        self.settings.sync

    # ====================== UTILIDADES ======================
    
    def get_all_enabled_with_config(self) -> List[Dict]:
        """Devuelve lista de tags habilitados con sus límites y severidad actuales"""
        enabled = self.get_enabled_tags()
        result = []
        for tag in enabled:
            result.append({
                "tag": tag,
                "limits": self.get_limits(tag),
                "severity": self.get_severity(tag)
            })
        return result

    # Método para guardar explícitamente (si es necesario)
    def save_config(self):
        """Fuerza la escritura de todos los cambios pendientes a disco."""
        self.settings.sync()