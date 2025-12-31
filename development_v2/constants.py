# constants.py
# Fresh module – created December 21, 2025
# Constants and limits directly from ASCE 7-22 Chapter 7 (pages 55–57)

# Ground snow load source
GROUND_SNOW_SOURCE_URL = "https://asce7hazardtool.online/"

# Physical and code limits
MAX_UPWIND_FETCH = 500.0  # ft – Sec. 7.1.2 lu definition
MAX_SNOW_DENSITY = 30.0  # pcf – Equation 7.7-1 cap
MIN_GROUND_SNOW_FOR_CASE_STUDY = 140.0  # psf – gray areas on maps trigger geodatabase

# Typical practical limits for valley geometry
MIN_VALLEY_ANGLE_DEG = 60  # degrees – practical for intersecting ridges
MAX_VALLEY_ANGLE_DEG = 120  # degrees

# Roof dead load assumption (adjustable per project)
TYPICAL_ROOF_DEAD_LOAD_PSF = 15.0

# Risk categories (from Table 1.5-1, referenced in ground snow determination)
RISK_CATEGORIES = {
    "I": "Low hazard to human life",
    "II": "Standard buildings (most common)",
    "III": "Substantial hazard (schools, large assembly)",
    "IV": "Essential facilities (hospitals, emergency centers)",
}

# Map contour ratio (from notes on Figures 7.2-1A to 7.2-1D)
MAP_CONTOUR_RATIO = 1.18
