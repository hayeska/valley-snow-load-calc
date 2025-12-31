# validation.py
# Fresh module – created December 21, 2025
# Input validation based on ASCE 7-22 Chapter 7 (pages 55–56 shown in your PDF)

from typing import Optional
from constants import MAX_UPWIND_FETCH, MIN_VALLEY_ANGLE_DEG, MAX_VALLEY_ANGLE_DEG

def validate_ground_snow_load(pg: float) -> Optional[str]:
    """Validate pg from ASCE Hazard Tool – Section 7.2"""
    if pg < 0:
        return "Ground snow load (pg) cannot be negative"
    if pg == 0:
        return "pg = 0 psf – confirm site has no snow load requirement"
    if pg > 300:
        return "pg > 300 psf is extremely rare – verify with site-specific study"
    return None

def validate_upwind_fetch(lu: float, direction: str = "") -> Optional[str]:
    """Validate lu per Section 7.1.2 definition (lu ≤ 500 ft)"""
    if lu <= 0:
        return f"{direction} upwind fetch (lu) must be > 0 ft"
    if lu > MAX_UPWIND_FETCH:
        return f"{direction} upwind fetch (lu) cannot exceed {MAX_UPWIND_FETCH} ft per ASCE 7-22"
    return None

def validate_valley_angle(angle_deg: float) -> Optional[str]:
    """Practical limit for intersecting ridges forming a valley"""
    if not (MIN_VALLEY_ANGLE_DEG <= angle_deg <= MAX_VALLEY_ANGLE_DEG):
        return f"Valley angle must be between {MIN_VALLEY_ANGLE_DEG}° and {MAX_VALLEY_ANGLE_DEG}° for reliable drift calculation"
    return None

def validate_pitch(numerator: float, roof_side: str = "") -> Optional[str]:
    """Validate roof pitch numerator (X in X/12)"""
    if numerator <= 0:
        return f"{roof_side} pitch numerator must be > 0"
    if numerator > 24:
        return f"{roof_side} pitch > 24/12 is very steep – verify applicability of Chapter 7 provisions"
    return None

def validate_exposure_factor(ce: float) -> Optional[str]:
    """Ce from Table 7.3-1"""
    if not (0.7 <= ce <= 1.2):
        return "Exposure factor (Ce) must be between 0.7 and 1.2 per Table 7.3-1"
    return None

def validate_thermal_factor(ct: float) -> Optional[str]:
    """Rough check for Ct values from Tables 7.3-2 and 7.3-3"""
    if ct < 0.85 or ct > 1.3:
        return "Thermal factor (Ct) typically 0.85–1.3 – verify Tables 7.3-2 or 7.3-3"
    return None

def validate_importance_factor(is_factor: float) -> Optional[str]:
    """Is from Table 1.5-2"""
    valid_values = [0.8, 0.9, 1.0, 1.1, 1.2]
    if is_factor not in valid_values:
        return f"Importance factor (Is) must be one of {valid_values} per Table 1.5-2"
    return None