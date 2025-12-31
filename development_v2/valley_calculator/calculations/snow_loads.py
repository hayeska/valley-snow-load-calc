# snow_loads.py - ASCE 7-22 snow load calculations for Valley Calculator V2.0

import math
from typing import Dict, Tuple


class SnowLoadCalculator:
    """
    ASCE 7-22 compliant snow load calculations.

    Implements Chapter 7 snow load provisions including:
    - Balanced snow loads
    - Unbalanced snow loads
    - Drift calculations for intersecting roofs
    """

    def __init__(self):
        """Initialize with ASCE 7-22 constants."""
        self.MIN_SLOPE = 0.5 / 12.0  # 0.0417 (2.38°)
        self.MAX_SLOPE = 7.0 / 12.0  # 0.5833 (30.2°)

    def calculate_balanced_load(
        self, pg: float, ce: float, ct: float, is_factor: float, cs: float
    ) -> float:
        """
        Calculate balanced snow load per ASCE 7-22 Section 7.3.

        Args:
            pg: Ground snow load (psf)
            ce: Exposure factor
            ct: Thermal factor
            is_factor: Importance factor
            cs: Slope factor

        Returns:
            Balanced snow load ps (psf)
        """
        pf = 0.7 * ce * ct * is_factor * pg  # Flat roof snow load
        ps = pf * cs  # Sloped roof snow load

        return ps

    def calculate_gable_drift(self, pg, lu, W2, Ce, ct, Cs, Is, s, S):
        """
        Calculate gable roof drift per ASCE 7-22 Section 7.7.

        Args:
            pg: Ground snow load (psf)
            lu: Length of upper roof (ft)
            W2: Winter wind parameter
            Ce, ct, Cs, Is: Load factors
            s: Roof slope (rise/run)
            S: Slope parameter (run for rise of 1)

        Returns:
            Dictionary with drift parameters
        """
        import math

        gamma = min(0.13 * pg + 14, 30)
        hd = 1.5 * math.sqrt(pg**0.74 * lu**0.7 * W2**1.7 / gamma)
        pd = hd * gamma / math.sqrt(S)  # Uniform rectangular
        pd_max = pd
        w = (8 * hd * math.sqrt(S)) / 3
        ps = 0.7 * Ce * ct * Is * pg * Cs

        return {
            "hd_ft": hd,
            "pd_max_psf": pd_max,
            "drift_width_ft": w,
            "pd_max": pd_max,
            "w": w,
            "ps": ps,
            "gamma": gamma,
        }

    def calculate_drift_loads(
        self, pg, lu_north, lu_west, w2, s_n, s_w, S_n, S_w, unbalanced_n, unbalanced_w
    ):
        """
        Calculate drift loads for intersecting roofs.

        Args:
            pg: Ground snow load (psf)
            lu_north, lu_west: Upper roof lengths (ft)
            w2: Winter wind parameter
            s_n, s_w: Roof slopes
            S_n, S_w: Slope parameters
            unbalanced_n, unbalanced_w: Whether unbalanced loads apply

        Returns:
            Dictionary with drift load results
        """
        # This is a simplified version - full implementation would include
        # comprehensive drift analysis per ASCE 7-22 Section 7.7

        return {
            "north_drift": {"hd_ft": 0, "drift_width_ft": 0, "pd_max_psf": 0},
            "west_drift": {"hd_ft": 0, "drift_width_ft": 0, "pd_max_psf": 0},
            "valley_drift": {"hd_ft": 0, "drift_width_ft": 0, "pd_max_psf": 0},
        }

    def calculate_slope_factor(self, s: float, s_min: float = 0.0417) -> float:
        """
        Calculate slope factor Cs per ASCE 7-22 Figure 7.4-1.

        Args:
            s: Roof slope (rise/run)
            s_min: Minimum slope for snow retention

        Returns:
            Slope factor Cs
        """
        if s < s_min:
            return 1.0  # Fully exposed
        elif s <= 0.125:
            # Linear reduction from 1.0 to 0.0
            return 1.0 - (s - s_min) / (0.125 - s_min) * 1.0
        else:
            return 0.0  # No snow retention

    def calculate_drift_height(
        self, pg: float, lu: float, w2: float, gamma: float
    ) -> float:
        """
        Calculate drift height per ASCE 7-22 Section 7.7.1.

        Args:
            pg: Ground snow load (psf)
            lu: Upwind fetch length (ft)
            w2: Winter wind parameter
            gamma: Snow density (pcf)

        Returns:
            Drift height hd (ft)
        """
        if lu <= 0 or pg <= 0:
            return 0.0

        # hd = 1.5 * (pg^0.74 * lu^0.7 * W2^1.7 / gamma)^0.5
        exponent = pg**0.74 * lu**0.7 * w2**1.7 / gamma
        hd = 1.5 * math.sqrt(exponent)

        return round(hd, 2)

    def calculate_drift_load(
        self, hd: float, gamma: float, s: float, S: float
    ) -> Tuple[float, float]:
        """
        Calculate drift surcharge per ASCE 7-22 Section 7.7.

        Args:
            hd: Drift height (ft)
            gamma: Snow density (pcf)
            s: Roof slope (rise/run)
            S: Run for rise of 1

        Returns:
            Tuple of (pd_max, w) where:
            pd_max: Maximum drift surcharge (psf)
            w: Drift width (ft)
        """
        if hd <= 0:
            return 0.0, 0.0

        # pd_max = 2 * (hd * gamma / √S) - triangular approximation
        pd_max = 2 * (hd * gamma / math.sqrt(S))

        # w = (8 * hd * √S) / 3
        w = (8 * hd * math.sqrt(S)) / 3

        return round(pd_max, 1), round(w, 1)

    def calculate_drift_loads(
        self,
        pg: float,
        lu_north: float,
        lu_west: float,
        w2: float,
        s_n: float,
        s_w: float,
        S_n: float,
        S_w: float,
        unbalanced_n: bool,
        unbalanced_w: bool,
    ) -> Dict:
        """
        Calculate drift loads for intersecting gable roofs.

        Args:
            pg: Ground snow load (psf)
            lu_north: North upwind fetch (ft)
            lu_west: West upwind fetch (ft)
            w2: Winter wind parameter
            s_n, s_w: Roof slopes (rise/run)
            S_n, S_w: Run for rise of 1
            unbalanced_n, unbalanced_w: Whether unbalanced loads apply

        Returns:
            Dictionary with drift analysis results
        """
        # Calculate snow density
        gamma = min(0.13 * pg + 14, 30)  # Eq. 7.7-1

        results = {
            "gamma_pcf": gamma,
            "north_drift": {},
            "west_drift": {},
            "governing_drift": {},
        }

        # Calculate north drift
        if unbalanced_n:
            hd_north = self.calculate_drift_height(pg, lu_north, w2, gamma)
            pd_north, w_north = self.calculate_drift_load(hd_north, gamma, s_n, S_n)
        else:
            hd_north, pd_north, w_north = 0.0, 0.0, 0.0

        results["north_drift"] = {
            "hd_ft": hd_north,
            "pd_max_psf": pd_north,
            "width_ft": w_north,
        }

        # Calculate west drift
        if unbalanced_w:
            hd_west = self.calculate_drift_height(pg, lu_west, w2, gamma)
            pd_west, w_west = self.calculate_drift_load(hd_west, gamma, s_w, S_w)
        else:
            hd_west, pd_west, w_west = 0.0, 0.0, 0.0

        results["west_drift"] = {
            "hd_ft": hd_west,
            "pd_max_psf": pd_west,
            "width_ft": w_west,
        }

        # Calculate governing drift (larger of the two)
        pd_governing = max(pd_north, pd_west)
        hd_governing = max(hd_north, hd_west)
        w_governing = w_north if pd_north >= pd_west else w_west

        results["governing_drift"] = {
            "pd_max_psf": pd_governing,
            "hd_ft": hd_governing,
            "width_ft": w_governing,
        }

        return results

    def validate_snow_load_inputs(
        self, pg: float, w2: float, ce: float, ct: float
    ) -> list:
        """
        Validate snow load input parameters.

        Args:
            pg: Ground snow load (psf)
            w2: Winter wind parameter
            ce: Exposure factor
            ct: Thermal factor

        Returns:
            List of validation error messages
        """
        errors = []

        if pg <= 0:
            errors.append("Ground snow load (pg) must be positive")

        if pg > 500:
            errors.append("Ground snow load (pg) seems unusually high (>500 psf)")

        if not 0.25 <= w2 <= 0.65:
            errors.append(
                "Winter wind parameter (W2) should typically be between 0.25 and 0.65"
            )

        if not 0.7 <= ce <= 1.3:
            errors.append(
                "Exposure factor (Ce) should typically be between 0.7 and 1.3"
            )

        if not 1.0 <= ct <= 1.3:
            errors.append("Thermal factor (Ct) should typically be between 1.0 and 1.3")

        return errors
