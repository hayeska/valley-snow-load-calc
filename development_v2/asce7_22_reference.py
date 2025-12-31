# asce7_22_reference.py
# Fresh module – created December 21, 2025
# Based solely on ASCE 7-22 Chapter 7 pages you uploaded (pages 55–57 shown)

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class GroundSnowLoadSource:
    name: str = "ASCE Design Ground Snow Load Geodatabase"
    version: str = "2022-1.0"
    url: str = "https://asce7hazardtool.online/"
    description: str = (
        "Geocoded, risk-targeted ground snow loads (pg) for the United States. "
        "Provides values for Risk Categories I–IV and winter wind parameter W2."
    )
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = [
                "Figures 7.2-1A to 7.2-1D are illustrative only – always use the online geodatabase",
                "Contours spaced by constant ratio 1.18 (values: 10, 12, 14, ..., 140 psf)",
                "Gray shaded areas indicate pg > 140 psf – must use online tool",
                "W2 = percent time wind >10 mph Oct–Apr (new in ASCE 7-22)",
                "Site-specific case studies required only in limited high-variance zones"
            ]

GROUND_SNOW_SOURCE = GroundSnowLoadSource()

# Symbols from Section 7.1.2 (page 55)
SYMBOLS: Dict[str, str] = {
    "Ce": "Exposure factor, as determined from Table 7.3-1",
    "Cs": "Slope factor, as determined from Figure 7.4-1",
    "Ct": "Thermal factor, as determined from Table 7.3-2",
    "h": "Vertical separation distance, feet (m), between the edge of a higher roof and the edge of a lower adjacent roof",
    "hb": "Height of balanced snow load, determined by dividing ps by γ, ft (m)",
    "hc": "Clear height from top of balanced snow load to closest point on adjacent upper roof, parapet, or projection, ft (m)",
    "hd": "Height of snow drift, ft (m)",
    "hd1 or hd2": "Heights of snow drifts where two intersecting snow drifts can form, ft (m)",
    "ho": "Height of obstruction above the surface of the roof, ft (m)",
    "lu": "Length of the roof upwind of the drift, ft (m)",
    "pd": "Maximum intensity of drift surcharge load, lb/ft² (kN/m²)",
    "pf": "Snow load on flat roofs, lb/ft² (kN/m²)",
    "pg": "Ground snow load from geodatabase, lb/ft² (kN/m²)",
    "pm": "Minimum snow load for low-slope roofs, lb/ft² (kN/m²)",
    "ps": "Sloped roof (balanced) snow load, lb/ft² (kN/m²)",
    "s": "Horizontal separation distance between the edges of two adjacent buildings, ft (m)",
    "S": "Roof slope run for a rise of one",
    "w": "Width of snow drift, ft (m)",
    "w1 or w2": "Widths of snow drifts where two intersecting snow drifts can form, ft (m)",
    "W": "Horizontal distance from eave to ridge, ft (m)",
    "W2": "Percent time wind speed is above 10 mph during winter (October through April); winter wind parameter",
    "γ": "Snow density, as determined from Equation (7.7-1), lb/ft³ (kN/m³)",
    "θ": "Roof slope on the leeward side, degrees"
}

# Key definitions from Section 7.1.1 (page 55)
DEFINITIONS = {
    "DRIFT": "The accumulation of wind-driven snow that results in a local surcharge load on the roof structure at locations such as a parapet or roof step",
    "FLAT ROOF SNOW LOAD": "Uniform load for flat roofs",
    "FREEZER BUILDINGS": "Buildings in which the inside temperature is kept at or below freezing. Buildings with an air space between the roof insulation layer above and a ceiling of the freezer area below are not considered freezer buildings",
    "GROUND SNOW LOAD": "The site-specific weight of the accumulated snow at the ground level used to develop roof snow loads on the structure",
    "SLIPPERY SURFACE": "Membranes with a smooth surface, for example, glass, metal, or rubber. Membranes with an embedded aggregate or mineral granule surface are not considered a slippery surface",
    "VENTILATED ROOF": "Roof that allows exterior air to naturally circulate between the roof surface above and the insulation layer below"
}