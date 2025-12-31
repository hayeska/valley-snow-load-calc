# geometry.py
# ASCE 7-22 Valley Geometry Calculations – Fixed Names December 21, 2025

import math


def valley_horizontal_length(
    de_north: float, de_west: float, angle_deg: float = 90.0
) -> float:
    """Calculate horizontal length of valley (lv) from eave to ridge distances and angle"""
    angle_rad = math.radians(angle_deg)
    lv = math.sqrt(
        de_north**2 + de_west**2 - 2 * de_north * de_west * math.cos(angle_rad)
    )
    return round(lv, 2)


def valley_rafter_length(
    lv: float, s_north: float, s_west: float, de_north: float, de_west: float
) -> float:
    """Calculate sloped rafter length along valley"""
    h_n = de_north * s_north
    h_w = de_west * s_west
    h_avg = (h_n + h_w) / 2
    return round(math.sqrt(lv**2 + h_avg**2), 2)
