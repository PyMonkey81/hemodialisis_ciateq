"""Lógica y persistencia de perfiles de ultrafiltración (UF, L/h)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import logging
import math
from pathlib import Path
from typing import Optional

from logic.conductivity_profile import ProfileType, step_index_by_seconds
from utilities.platform_runtime import get_runtime_config_path

logger = logging.getLogger(__name__)

# Rango de edición de UF: 0.00 - 2.00 L/h (distinto del clamp de seguridad
# de logic/calculos.py, que es un tope de hardware, no de este perfil).
UF_MIN = 0.0
UF_MAX = 2.0
UF_DEFAULT = 0.0
EPSILON = 0.001


@dataclass
class UFProfile:
    enabled: bool = False
    profile_type: ProfileType = ProfileType.NONE
    therapy_duration_min: int = 240

    start_uf: float = UF_DEFAULT
    end_uf: float = UF_DEFAULT

    step_high: float = 2.0
    step_low: float = 0.0
    step_change_at_percent: float = 50.0

    points: list = field(default_factory=lambda: [UF_DEFAULT] * 6)

    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["profile_type"] = self.profile_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "UFProfile":
        profile_type_raw = str(data.get("profile_type", ProfileType.NONE.value)).lower().strip()
        try:
            profile_type = ProfileType(profile_type_raw)
        except ValueError:
            profile_type = ProfileType.NONE

        start_uf = float(data.get("start_uf", UF_DEFAULT))
        end_uf = float(data.get("end_uf", UF_DEFAULT))
        step_high = float(data.get("step_high", 2.0))
        step_low = float(data.get("step_low", 0.0))

        raw_points = data.get("points")
        points = _points_from_raw(raw_points, profile_type, start_uf, end_uf, step_high, step_low)

        return cls(
            enabled=bool(data.get("enabled", False)),
            profile_type=profile_type,
            therapy_duration_min=int(data.get("therapy_duration_min", 240)),
            start_uf=start_uf,
            end_uf=end_uf,
            step_high=step_high,
            step_low=step_low,
            step_change_at_percent=float(data.get("step_change_at_percent", 50.0)),
            points=points,
            created_at=str(data.get("created_at", "")),
            notes=str(data.get("notes", "")),
        )


def clamp_uf(value: float) -> float:
    return max(UF_MIN, min(UF_MAX, value))


def _decay_progress(progress: float, k: float = 3.0) -> float:
    return (1.0 - math.exp(-k * progress)) / (1.0 - math.exp(-k))


def _linear_points(start: float, end: float) -> list:
    return [clamp_uf(start + (end - start) * (i / 5.0)) for i in range(6)]


def _exp_points(start: float, end: float) -> list:
    values = []
    for i in range(6):
        normalized = _decay_progress(i / 5.0)
        values.append(start + (end - start) * normalized)
    return [clamp_uf(v) for v in values]


def _step_points(high: float, low: float) -> list:
    return [clamp_uf(v) for v in (high, low, high, low, high, low)]


def _points_from_raw(
    raw_points,
    profile_type: "ProfileType",
    start: float,
    end: float,
    step_high: float,
    step_low: float,
) -> list:
    if isinstance(raw_points, list) and len(raw_points) == 6:
        try:
            return [clamp_uf(float(v)) for v in raw_points]
        except (TypeError, ValueError):
            pass

    if profile_type == ProfileType.LINEAR:
        return _linear_points(start, end)
    if profile_type == ProfileType.CUSTOM:
        return _exp_points(start, end)
    if profile_type == ProfileType.STEP:
        high = step_high if step_high else start
        low = step_low if step_low else end
        return _step_points(high, low)

    return [UF_DEFAULT] * 6


def validate_uf(value: float, name: str = "flujo UF") -> tuple[bool, str]:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return False, f"{name} no es un número válido"

    if val < UF_MIN:
        return False, f"{name} demasiado bajo (mínimo {UF_MIN:.2f} L/h)"
    if val > UF_MAX:
        return False, f"{name} demasiado alto (máximo {UF_MAX:.2f} L/h)"

    return True, ""


def validate_profile(profile: UFProfile) -> tuple[bool, str]:
    if profile.therapy_duration_min <= 0:
        return False, "La duración de terapia debe ser mayor a 0 minutos"

    if profile.profile_type == ProfileType.LINEAR:
        ok, msg = validate_uf(profile.start_uf, "UF inicial")
        if not ok:
            return False, msg

        ok, msg = validate_uf(profile.end_uf, "UF final")
        if not ok:
            return False, msg

    elif profile.profile_type == ProfileType.STEP:
        ok, msg = validate_uf(profile.step_high, "Valor alto del escalón")
        if not ok:
            return False, msg

        ok, msg = validate_uf(profile.step_low, "Valor bajo del escalón")
        if not ok:
            return False, msg

        if not (0.0 <= profile.step_change_at_percent <= 100.0):
            return False, "El porcentaje de cambio del escalón debe estar entre 0 y 100"

    if profile.points:
        if len(profile.points) != 6:
            return False, "El perfil debe tener 6 puntos"
        for idx, point in enumerate(profile.points, start=1):
            ok, msg = validate_uf(point, f"Punto {idx}")
            if not ok:
                return False, msg

    return True, ""


def linear_interpolate(start: float, end: float, elapsed_min: float, total_min: float) -> float:
    if total_min <= 0:
        return clamp_uf(end)

    progress = max(0.0, min(1.0, elapsed_min / total_min))
    value = start + (end - start) * progress
    return clamp_uf(value)


def exp_interpolate(start: float, end: float, elapsed_min: float, total_min: float) -> float:
    if total_min <= 0:
        return clamp_uf(end)

    progress = max(0.0, min(1.0, elapsed_min / total_min))
    normalized = _decay_progress(progress)
    value = start + (end - start) * normalized
    return clamp_uf(value)


def calculate_target_uf(profile: UFProfile, elapsed_min: float) -> Optional[float]:
    """Devuelve el valor objetivo de UF en L/h, o None si el perfil no aplica."""
    if not profile.enabled or profile.profile_type == ProfileType.NONE:
        return None

    total = float(profile.therapy_duration_min)

    if profile.profile_type == ProfileType.LINEAR:
        return linear_interpolate(
            start=profile.start_uf,
            end=profile.end_uf,
            elapsed_min=elapsed_min,
            total_min=total,
        )

    if profile.profile_type == ProfileType.CUSTOM:
        return exp_interpolate(
            start=profile.start_uf,
            end=profile.end_uf,
            elapsed_min=elapsed_min,
            total_min=total,
        )

    if profile.profile_type == ProfileType.STEP:
        points = profile.points if len(profile.points) == 6 else _step_points(
            profile.step_high or profile.start_uf,
            profile.step_low or profile.end_uf,
        )
        # Periodo fijo de 30 min de segundos de terapia (ver step_index_by_seconds).
        idx = step_index_by_seconds(elapsed_min * 60.0)
        return clamp_uf(float(points[idx]))

    return None


DEFAULT_PROFILE_PATH = get_runtime_config_path("profiles/uf_profile.json")


def load_profile(path: Path = DEFAULT_PROFILE_PATH) -> UFProfile:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)

            profile = UFProfile.from_dict(data)
            logger.info("Perfil de UF cargado: %s", profile.profile_type.value)
            return profile
    except Exception as exc:
        logger.error("Error cargando perfil de UF: %s", exc)

    return UFProfile()


def save_profile(profile: UFProfile, path: Path = DEFAULT_PROFILE_PATH) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        ok, msg = validate_profile(profile)
        if not ok:
            logger.error("No se puede guardar perfil de UF inválido: %s", msg)
            return False

        profile.created_at = datetime.now().isoformat(timespec="seconds")

        with path.open("w", encoding="utf-8") as file_obj:
            json.dump(profile.to_dict(), file_obj, ensure_ascii=False, indent=2)

        logger.info("Perfil de UF guardado: %s", profile.profile_type.value)
        return True
    except Exception as exc:
        logger.error("Error guardando perfil de UF: %s", exc)
        return False
