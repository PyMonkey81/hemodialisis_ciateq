"""Helpers de plataforma para compatibilidad Windows/Linux con rollback por config."""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

COM_PORT_PATTERN = re.compile(r"^COM\d+$", re.IGNORECASE)


def _ensure_config_dir(path: Path) -> Path | None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        return None


def get_runtime_config_dir() -> Path:
    """
    Devuelve un directorio de configuración escribible en runtime.
    Prioridad:
    1) CIATEQ_CONFIG_DIR (si existe)
    2) <dir_del_exe>/config cuando corre congelado
    3) <repo>/config en desarrollo
    """
    env_dir = os.environ.get("CIATEQ_CONFIG_DIR", "").strip()
    if env_dir:
        config_dir = _ensure_config_dir(Path(env_dir))
        if config_dir is not None:
            return config_dir
        logger.warning("No se pudo usar CIATEQ_CONFIG_DIR: %s", env_dir)

    if getattr(sys, "frozen", False):
        executable_config_dir = Path(sys.executable).resolve().parent / "config"
        config_dir = _ensure_config_dir(executable_config_dir)
        if config_dir is not None:
            return config_dir

        app_data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        fallback_dir = app_data_dir / "CIATEQ" / "Hemodialisis" / "config"
        config_dir = _ensure_config_dir(fallback_dir)
        if config_dir is not None:
            logger.warning(
                "Configuración junto al ejecutable no disponible (%s); se usa %s",
                executable_config_dir,
                config_dir,
            )
            return config_dir

    return Path(__file__).resolve().parent.parent / "config"


def get_runtime_config_path(file_name: str) -> Path:
    """Construye la ruta absoluta para un archivo dentro de config."""
    return get_runtime_config_dir() / file_name


def platform_name() -> str:
    return platform.system()


def is_windows() -> bool:
    return platform_name() == "Windows"


def is_linux() -> bool:
    return platform_name() == "Linux"


def safe_int(value, default: int = 0) -> int:
    """Convierte valores de entrada a int sin romper la app si vienen vacíos o corruptos."""
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            return int(float(stripped))
        return default
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Convierte valores numéricos sin forzar truncamiento al cargar horas persistentes."""
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            return float(stripped)
        return default
    except (TypeError, ValueError):
        return default


def safe_json_load(path: str | Path, default=None):
    """Carga JSON con fallback seguro para archivos vacíos o corruptos."""
    if path is None:
        return default

    file_path = Path(path)
    if not file_path.exists():
        return default

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if data is not None else default
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        logger.warning("No se pudo cargar JSON seguro desde %s. Se usa fallback.", file_path)
        return default


def load_platform_features() -> dict:
    """Carga feature flags desde config, con fallback seguro si falta/está corrupto."""
    default_features_path = get_runtime_config_path("platform_features.json")
    config_path = Path(os.environ.get("CIATEQ_PLATFORM_FEATURES", str(default_features_path)))
    defaults = {
        "enable_linux_platform_layer": True,
        "enable_windows_legacy_prescale": True,
        "sanitize_linux_com_ports": True,
    }

    if not config_path.exists():
        return defaults

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return defaults
        return {**defaults, **data}
    except Exception as exc:
        logger.warning("No se pudo cargar %s: %s. Se usan defaults.", config_path, exc)
        return defaults


def feature_enabled(flag_name: str, default: bool = False) -> bool:
    features = load_platform_features()
    value = features.get(flag_name, default)
    return bool(value)


def sanitize_port_for_platform(port_value: str | None) -> str:
    """Normaliza puertos inválidos para Linux. Mantiene Windows intacto."""
    port = (port_value or "Auto").strip() or "Auto"
    if not is_linux():
        return port

    if not feature_enabled("sanitize_linux_com_ports", True):
        return port

    if COM_PORT_PATTERN.match(port):
        logger.warning("Puerto '%s' no es válido en Linux. Se usa 'Auto'.", port)
        return "Auto"
    return port
