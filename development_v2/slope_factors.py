# slope_factors.py
# Fresh module – created December 21, 2025
# Exact implementation of ASCE 7-22 Figure 7.4-1 slope reduction factor Cs
# Three separate graphs based on Ct value and slippery surface

import math


def calculate_cs(
    theta_deg: float,
    ct: float,
    slippery: bool = False,
    warm_roof: bool = False,
) -> float:
    """
    Calculate slope factor Cs per ASCE 7-22 Figure 7.4-1.
    Parameters:
        theta_deg: Roof slope angle in degrees (arctan(pitch/12))
        ct: Thermal factor from Table 7.3-2 or 7.3-3
        slippery: True for smooth glass/metal/rubber (no aggregate)
        warm_roof: True if unventilated warm roof with Ct ≤ 1.1 (Graph a/b behavior)
    Returns:
        Cs value (0.0 to 1.0)
    """
    theta = max(0.0, min(90.0, theta_deg))  # Clamp to valid range

    # Graph selection based on Ct and roof type (per Figure 7.4-1 notes)
    if ct <= 1.1 or warm_roof:
        # Graphs a and b: warm roofs (unventilated, higher R-value)
        if slippery:
            # Graph b – slippery warm roof
            if theta <= 3.58:  # approx 3/12 to flat transition
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 3.58) / 66.42)
        else:
            # Graph a – non-slippery warm roof
            if theta <= 26.57:  # approx 5/12
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 26.57) / 43.43)
    else:
        # Graph c – cold roofs (Ct > 1.1)
        if slippery:
            if theta <= 8.53:  # approx 1.75/12
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 8.53) / 61.47)
        else:
            if theta <= 37.76:  # approx 8/12
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 37.76) / 32.24)

    return 1.0  # fallback


def cs_from_pitch(
    pitch_numerator: float,
    ct: float,
    slippery: bool = False,
    warm_roof: bool = False,
) -> float:
    """
    Convenience function: input pitch as X in X/12
    """
    if pitch_numerator <= 0:
        theta = 0.0
    else:
        theta = math.degrees(math.atan(pitch_numerator / 12.0))
    return calculate_cs(theta, ct, slippery, warm_roof)
