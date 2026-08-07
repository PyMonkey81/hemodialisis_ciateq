"""Lógica y persistencia de perfiles de conductividad."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Optional

from utilities.platform_runtime import get_runtime_config_path

logger = logging.getLogger(__name__)

CONDUCTIVITY_MIN = 12.0
CONDUCTIVITY_MAX = 16.0
CONDUCTIVITY_DEFAULT = 14.0
EPSILON = 0.01


class ProfileType(str, Enum):
    NONE = "none"
    LINEAR = "linear"
    STEP = "step"
    CUSTOM = "custom"


@dataclass
class ConductivityProfile:
    enabled: bool = False
    profile_type: ProfileType = ProfileType.NONE
    therapy_duration_min: int = 240

    start_conductivity: float = CONDUCTIVITY_DEFAULT
    end_conductivity: float = CONDUCTIVITY_DEFAULT

    step_high: float = 14.2
    step_low: float = 13.6
    step_change_at_percent: float = 50.0

    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["profile_type"] = self.profile_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ConductivityProfile":
        profile_type_raw = str(data.get("profile_type", ProfileType.NONE.value)).lower().strip()
        try:
            profile_type = ProfileType(profile_type_raw)
        except ValueError:
            profile_type = ProfileType.NONE

        return cls(
            enabled=bool(data.get("enabled", False)),
            profile_type=profile_type,
            therapy_duration_min=int(data.get("therapy_duration_min", 240)),
            start_conductivity=float(data.get("start_conductivity", CONDUCTIVITY_DEFAULT)),
            end_conductivity=float(data.get("end_conductivity", CONDUCTIVITY_DEFAULT)),
            step_high=float(data.get("step_high", 14.2)),
            step_low=float(data.get("step_low", 13.6)),
            step_change_at_percent=float(data.get("step_change_at_percent", 50.0)),
            created_at=str(data.get("created_at", "")),
            notes=str(data.get("notes", "")),
        )


def clamp_conductivity(value: float) -> float:
    return max(CONDUCTIVITY_MIN, min(CONDUCTIVITY_MAX, value))


def validate_conductivity(value: float, name: str = "conductividad") -> tuple[bool, str]:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return False, f"{name} no es un número válido"

    if val < CONDUCTIVITY_MIN:
        return False, f"{name} demasiado baja (mínimo {CONDUCTIVITY_MIN} mS/cm)"
    if val > CONDUCTIVITY_MAX:
        return False, f"{name} demasiado alta (máximo {CONDUCTIVITY_MAX} mS/cm)"

    return True, ""


def validate_profile(profile: ConductivityProfile) -> tuple[bool, str]:
    if profile.therapy_duration_min <= 0:
        return False, "La duración de terapia debe ser mayor a 0 minutos"

    if profile.profile_type == ProfileType.LINEAR:
        ok, msg = validate_conductivity(profile.start_conductivity, "Conductividad inicial")
        if not ok:
            return False, msg

        ok, msg = validate_conductivity(profile.end_conductivity, "Conductividad final")
        if not ok:
            return False, msg

    elif profile.profile_type == ProfileType.STEP:
        ok, msg = validate_conductivity(profile.step_high, "Valor alto del escalón")
        if not ok:
            return False, msg

        ok, msg = validate_conductivity(profile.step_low, "Valor bajo del escalón")
        if not ok:
            return False, msg

        if not (0.0 <= profile.step_change_at_percent <= 100.0):
            return False, "El porcentaje de cambio del escalón debe estar entre 0 y 100"

    return True, ""


def linear_interpolate(start: float, end: float, elapsed_min: float, total_min: float) -> float:
    if total_min <= 0:
        return clamp_conductivity(end)

    progress = max(0.0, min(1.0, elapsed_min / total_min))
    value = start + (end - start) * progress
    return clamp_conductivity(value)


def step_value(
    high: float,
    low: float,
    change_at_percent: float,
    elapsed_min: float,
    total_min: float,
) -> float:
    if total_min <= 0:
        return clamp_conductivity(low)

    change_at_min = (change_at_percent / 100.0) * total_min
    if elapsed_min < change_at_min:
        return clamp_conductivity(high)

    return clamp_conductivity(low)


def calculate_target_conductivity(profile: ConductivityProfile, elapsed_min: float) -> Optional[float]:
    if not profile.enabled or profile.profile_type == ProfileType.NONE:
        return None

    total = float(profile.therapy_duration_min)

    if profile.profile_type == ProfileType.LINEAR:
        return linear_interpolate(
            start=profile.start_conductivity,
            end=profile.end_conductivity,
            elapsed_min=elapsed_min,
            total_min=total,
        )

    if profile.profile_type == ProfileType.STEP:
        return step_value(
            high=profile.step_high,
            low=profile.step_low,
            change_at_percent=profile.step_change_at_percent,
            elapsed_min=elapsed_min,
            total_min=total,
        )

    if profile.profile_type == ProfileType.CUSTOM:
        logger.warning("Perfil CUSTOM aún no implementado")
        return None

    return None


DEFAULT_PROFILE_PATH = get_runtime_config_path("profiles/conductivity_profile.json")


def load_profile(path: Path = DEFAULT_PROFILE_PATH) -> ConductivityProfile:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)

            profile = ConductivityProfile.from_dict(data)
            logger.info("Perfil de conductividad cargado: %s", profile.profile_type.value)
            return profile
    except Exception as exc:
        logger.error("Error cargando perfil de conductividad: %s", exc)

    return ConductivityProfile()


def save_profile(profile: ConductivityProfile, path: Path = DEFAULT_PROFILE_PATH) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        ok, msg = validate_profile(profile)
        if not ok:
            logger.error("No se puede guardar perfil inválido: %s", msg)
            return False

        profile.created_at = datetime.now().isoformat(timespec="seconds")

        with path.open("w", encoding="utf-8") as file_obj:
            json.dump(profile.to_dict(), file_obj, indent=2, ensure_ascii=False)

        logger.info("Perfil de conductividad guardado en %s", path)
        return True
    except Exception as exc:
        logger.error("Error guardando perfil de conductividad: %s", exc)
        return False
