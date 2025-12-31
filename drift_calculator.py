# drift_calculator.py
# Fresh module – created December 21, 2025
# Gable roof drift calculations per ASCE 7-22 Section 7.6 and 7.7
# Includes new W2 winter wind parameter (from your uploaded PDF page 55)

import math
from constants import MAX_SNOW_DENSITY
from slope_factors import calculate_cs

def snow_density(pg: float) -> float:
    """Equation 7.7-1 – γ = 0.13 pg + 14, capped at 30 pcf"""
    return min(0.13 * pg + 14, MAX_SNOW_DENSITY)

def gable_roof_drift_height(
    pg: float,
    lu: float,
    W2: float,
    gamma: float,
) -> float:
    """
    New drift height formula in ASCE 7-22 incorporating W2
    hd = 1.5 * (pg^0.74 * lu^0.7 * W2^1.7 / gamma)^0.5
    """
    if lu <= 0 or pg <= 0:
        return 0.0
    exponent = pg**0.74 * lu**0.7 * W2**1.7 / gamma
    hd = 1.5 * math.sqrt(exponent)
    return round(hd, 2)

def drift_surcharge_and_width(
    hd: float,
    gamma: float,
    s_slope: float,
) -> dict:
    """
    pd_max = 2 * (hd * gamma / sqrt(s))
    w = (8 * hd * sqrt(s)) / 3
    s = pitch/12
    """
    if hd <= 0:
        return {"pd_max_psf": 0.0, "drift_width_ft": 0.0}

    pd_avg = hd * gamma / math.sqrt(s_slope)
    pd_max = 2 * pd_avg
    w = (8 * hd * math.sqrt(s_slope)) / 3

    return {
        "pd_max_psf": round(pd_max, 1),
        "drift_width_ft": round(w, 1),
    }

def single_gable_drift(
    pg: float,
    lu: float,
    W2: float,
    pitch_numerator: float,
) -> dict:
    """
    Complete drift calculation for one wind direction (one gable)
    """
    gamma = snow_density(pg)
    hd = gable_roof_drift_height(pg, lu, W2, gamma)
    s = pitch_numerator / 12.0 if pitch_numerator > 0 else 0.001  # avoid divide by zero

    drift = drift_surcharge_and_width(hd, gamma, s)

    return {
        "hd_ft": hd,
        "gamma_pcf": gamma,
        "pd_max_psf": drift["pd_max_psf"],
        "drift_width_ft": drift["drift_width_ft"],
    }

def valley_governing_drift(
    north_drift: dict,
    west_drift: dict,
) -> dict:
    """
    For intersecting ridges (valley): governing drift is the maximum pd_max
    """
    gov_pd_max = max(north_drift["pd_max_psf"], west_drift["pd_max_psf"])
    gov_hd = max(north_drift["hd_ft"], west_drift["hd_ft"])

    return {
        "governing_pd_max_psf": gov_pd_max,
        "governing_hd_ft": gov_hd,
        "north": north_drift,
        "west": west_drift,
    }