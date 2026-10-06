"""
Pure logic for heparin infusion time validation.

Clinical rule: Heparin is not infused during the last 30 minutes of therapy.
Maximum allowed = max(0, reference_minutes - 30)
"""

from enum import Enum
from core.state_manager import TreatmentPhase


def reference_minutes(
    phase: TreatmentPhase,
    programmed_minutes: int,
    remaining_seconds: int = 0
) -> int:
    """
    Calculate reference minutes for heparin validation.
    
    Args:
        phase: Current treatment phase
        programmed_minutes: Programmed therapy duration in minutes
        remaining_seconds: Remaining therapy time in seconds (used only if RUNNING or PAUSED)
    
    Returns:
        Reference minutes to use for validation
    
    Logic:
        - If phase is RUNNING or PAUSED: use remaining time (remaining_seconds / 60)
        - Otherwise: use programmed therapy duration
    """
    if phase in (TreatmentPhase.RUNNING, TreatmentPhase.PAUSED):
        remaining_min = int(remaining_seconds / 60)
        return remaining_min
    
    return programmed_minutes


def max_heparin_minutes(reference_minutes: int) -> int:
    """
    Calculate maximum allowed heparin infusion time.
    
    Clinical rule: No heparin infusion during last 30 minutes.
    
    Args:
        reference_minutes: Reference time in minutes (from reference_minutes function)
    
    Returns:
        Maximum allowed heparin infusion time in minutes
    
    Formula: max(0, reference_minutes - 30)
    """
    return max(0, reference_minutes - 30)


def clamp_heparin_time(
    requested_hours: int,
    requested_minutes: int,
    reference_minutes: int
) -> tuple[int, int]:
    """
    Clamp heparin time to maximum allowed.
    
    Args:
        requested_hours: User-requested heparin hours
        requested_minutes: User-requested heparin minutes
        reference_minutes: Reference time in minutes (from reference_minutes function)
    
    Returns:
        Tuple of (clamped_hours, clamped_minutes)
    
    If requested time exceeds max: returns max allowed time
    If requested time is within max: returns requested time unchanged
    """
    requested_total = (int(requested_hours) * 60) + int(requested_minutes)
    max_allowed = max_heparin_minutes(reference_minutes)
    
    clamped_total = min(requested_total, max_allowed)
    clamped_h = clamped_total // 60
    clamped_m = clamped_total % 60
    
    return clamped_h, clamped_m


def was_clamped(
    requested_hours: int,
    requested_minutes: int,
    reference_minutes: int
) -> bool:
    """
    Check if heparin time would be clamped.
    
    Args:
        requested_hours: User-requested heparin hours
        requested_minutes: User-requested heparin minutes
        reference_minutes: Reference time in minutes
    
    Returns:
        True if clamping would occur, False otherwise
    """
    requested_total = (int(requested_hours) * 60) + int(requested_minutes)
    max_allowed = max_heparin_minutes(reference_minutes)
    
    return requested_total > max_allowed
