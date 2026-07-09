"""Helpers de plataforma para compatibilidad Windows/Linux con rollback por config."""

from __future__ import annotations

import json
import logging
import os
import platform
import re
from pathlib import Path

logger = logging.getLogger(__name__)

COM_PORT_PATTERN = re.compile(r"^COM\d+$", re.IGNORECASE)
DEFAULT_FEATURES_PATH = Path(__file__).resolve().parent.parent / "config" / "platform_features.json"


def platform_name() -> str:
    return platform.system()


def is_windows() -> bool:
    return platform_name() == "Windows"


def is_linux() -> bool:
    return platform_name() == "Linux"


def load_platform_features() -> dict:
    """Carga feature flags desde config, con fallback seguro si falta/está corrupto."""
    config_path = Path(os.environ.get("CIATEQ_PLATFORM_FEATURES", str(DEFAULT_FEATURES_PATH)))
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
