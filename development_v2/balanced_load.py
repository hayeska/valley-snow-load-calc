# balanced_load.py
# Fresh module – created December 21, 2025
# Balanced (uniform) snow load calculations per ASCE 7-22 Section 7.3 and 7.4
# pf = 0.7 * Ce * Ct * Is * pg
# ps = pf * Cs

from slope_factors import calculate_cs

def flat_roof_snow_load(
    pg: float,
    Ce: float,
    Ct: float,
    Is: float,
) -> float:
    """
    Calculate flat roof snow load pf per Section 7.3
    pf = 0.7 * Ce * Ct * Is * pg
    """
    pf = 0.7 * Ce * Ct * Is * pg
    return round(pf, 1)

def sloped_roof_balanced_load(
    pf: float,
    theta_north_deg: float,
    theta_west_deg: float,
    Ct: float,
    slippery: bool = False,
    warm_roof: bool = False,
) -> float:
    """
    Calculate sloped roof snow load ps = pf * Cs
    Uses the minimum Cs from both roof sides (conservative for valley)
    """
    cs_north = calculate_cs(theta_north_deg, Ct, slippery, warm_roof)
    cs_west = calculate_cs(theta_west_deg, Ct, slippery, warm_roof)
    cs_min = min(cs_north, cs_west)
    ps = pf * cs_min
    return round(ps, 1)

def minimum_snow_load_for_low_slope_roofs(
    pf: float,
    ps: float,
    Is: float,
) -> float:
    """
    Minimum snow load Pm for low-slope roofs (monoslope, etc.)
    Pm = Is * 20 psf if pf < 20 psf (for Risk Category II, adjust Is accordingly)
    Pm = Is * pf if pf ≥ 20 psf
    """
    if pf < 20.0:
        pm = Is * 20.0
    else:
        pm = Is * pf
    # Pm shall not be less than ps for sloped roofs
    return max(pm, ps)

def full_balanced_load_calculation(
    pg: float,
    Ce: float,
    Ct: float,
    Is: float,
    theta_north_deg: float,
    theta_west_deg: float,
    slippery: bool = False,
    warm_roof: bool = False,
) -> dict:
    """
    Complete balanced load calculation for valley roof
    Returns pf, ps, and minimum Pm
    """
    pf = flat_roof_snow_load(pg, Ce, Ct, Is)
    ps = sloped_roof_balanced_load(pf, theta_north_deg, theta_west_deg, Ct, slippery, warm_roof)
    pm = minimum_snow_load_for_low_slope_roofs(pf, ps, Is)

    return {
        "pf_flat_psf": pf,
        "ps_sloped_balanced_psf": ps,
        "pm_minimum_psf": round(pm, 1),
        "Ce": Ce,
        "Ct": Ct,
        "Is": Is,
    }