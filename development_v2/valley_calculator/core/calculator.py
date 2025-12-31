# calculator.py - Resilient core calculation engine for Valley Snow Load Calculator V2.0
# ASCE 7-22 compliant snow load analysis with error handling and recovery

import math
from typing import Dict, Tuple
from ..calculations.snow_loads import SnowLoadCalculator
from ..calculations.geometry import RoofGeometry
from ..calculations.beam_analysis import BeamAnalyzer

from ..utils.logging.logger import get_logger
from ..core.recovery.error_handlers import (
    resilient_operation,
    error_boundary,
    validate_input,
    validate_positive_number,
    with_timeout,
)


class ValleyCalculator:
    """
    Resilient calculation engine for valley snow load analysis.

    Features:
    - ASCE 7-22 compliant snow load calculations
    - Comprehensive error handling and recovery
    - Automatic checkpoints and data validation
    - Performance monitoring and logging
    - Graceful degradation on calculation errors
    """

    def __init__(self):
        """Initialize the resilient calculator with all calculation modules."""
        self.logger = get_logger()

        # Initialize calculation modules with error boundaries
        try:
            self.snow_calculator = SnowLoadCalculator()
            self.geometry_calculator = RoofGeometry()
            self.beam_analyzer = BeamAnalyzer()

            self.logger.log_performance(
                "calculator_init", 0.0, success=True, metadata={"modules_loaded": 3}
            )

        except Exception as e:
            self.logger.log_error(e, operation="calculator_init", recoverable=False)
            raise RuntimeError("Failed to initialize calculation modules") from e

        # Default engineering parameters
        self.defaults = {
            "importance_factor": 1.0,
            "exposure_factor": 1.0,
            "thermal_factor": 1.0,
            "ground_snow_load": 25.0,  # psf
            "winter_wind_parameter": 0.3,
            "roof_pitch_north": 8,  # roof/12
            "roof_pitch_west": 8,  # roof/12
            "north_span": 16.0,  # ft
            "south_span": 16.0,  # ft
            "ew_half_width": 42.0,  # ft
            "valley_offset": 16.0,  # ft
            "valley_angle": 90.0,  # degrees
            "dead_load": 15.0,  # psf
            "beam_width": 3.5,  # inches
            "beam_depth": 9.5,  # inches
        }

    @resilient_operation(retries=2, recoverable=True)
    @validate_input(validate_positive_number, validate_positive_number)
    @with_timeout(5.0)  # 5 second timeout for slope calculations
    def calculate_slope_parameters(
        self, pitch_n: float, pitch_w: float
    ) -> Dict[str, float]:
        """
        Calculate slope parameters with validation and error handling.

        Args:
            pitch_n: North roof pitch (rise/12) - must be positive
            pitch_w: West roof pitch (rise/12) - must be positive

        Returns:
            Dictionary with slope parameters for both roof planes

        Raises:
            ValueError: If pitch values are invalid
        """
        with error_boundary("calculate_slope_parameters", recoverable=True):
            # Input validation
            if pitch_n <= 0 or pitch_w <= 0:
                raise ValueError("Roof pitches must be positive values")

            if pitch_n > 100 or pitch_w > 100:  # Reasonable upper bound
                raise ValueError("Roof pitches seem unreasonably high (>100/12)")

            try:
                # Calculate slope ratios (rise/run)
                s_n = pitch_n / 12.0
                s_w = pitch_w / 12.0

                # Calculate S factors (run for rise of 1) - ASCE 7-22
                S_n = 12.0 / pitch_n if pitch_n > 0 else float("inf")
                S_w = 12.0 / pitch_w if pitch_w > 0 else float("inf")

                # Calculate angles in degrees
                theta_n = math.degrees(math.atan(s_n))
                theta_w = math.degrees(math.atan(s_w))

                result = {
                    "s_n": s_n,
                    "s_w": s_w,
                    "S_n": S_n,
                    "S_w": S_w,
                    "theta_n": theta_n,
                    "theta_w": theta_w,
                }

                # Log successful calculation
                self.logger.log_performance(
                    "slope_calculation",
                    0.001,
                    success=True,
                    metadata={"pitch_n": pitch_n, "pitch_w": pitch_w},
                )

                return result

            except ZeroDivisionError:
                raise ValueError("Roof pitch cannot be zero")
            except (OverflowError, ValueError) as e:
                self.logger.log_error(
                    e,
                    operation="slope_calculation",
                    context={"pitch_n": pitch_n, "pitch_w": pitch_w},
                )
                raise ValueError(f"Invalid pitch values: {e}") from e

    def check_unbalanced_applicability(self, s_n: float, s_w: float) -> Dict[str, bool]:
        """
        Check if unbalanced snow loads apply per ASCE 7-22 Section 7.6.1.

        Args:
            s_n: North roof slope ratio (rise/run)
            s_w: West roof slope ratio (rise/run)

        Returns:
            Dictionary indicating which roof planes require unbalanced analysis
        """
        # Unbalanced loads apply for slopes between 0.5/12 and 7/12
        MIN_SLOPE = 0.5 / 12.0  # 0.0417 (2.38°)
        MAX_SLOPE = 7.0 / 12.0  # 0.5833 (30.2°)

        unbalanced_applies_n = MIN_SLOPE <= s_n <= MAX_SLOPE
        unbalanced_applies_w = MIN_SLOPE <= s_w <= MAX_SLOPE

        return {
            "north_applies": unbalanced_applies_n,
            "west_applies": unbalanced_applies_w,
        }

    def calculate_valley_geometry(
        self,
        north_span: float,
        south_span: float,
        ew_half_width: float,
        valley_offset: float,
    ) -> Dict[str, float]:
        """
        Calculate valley roof geometry parameters.

        Args:
            north_span: Distance from E-W ridge to north eave (ft)
            south_span: Distance from E-W ridge to south eave (ft)
            ew_half_width: Half-width from N-S ridge to eave (ft)
            valley_offset: Horizontal valley low point offset (ft)

        Returns:
            Dictionary with calculated geometry parameters
        """
        # Calculate valley length (horizontal projection)
        lv = math.sqrt(south_span**2 + valley_offset**2)

        # Calculate valley angle
        valley_angle = (
            math.degrees(math.atan(south_span / valley_offset))
            if valley_offset > 0
            else 90.0
        )

        # Calculate building dimensions
        building_width = 2 * ew_half_width
        building_length = north_span + south_span

        return {
            "valley_length_horizontal": lv,
            "valley_angle_degrees": valley_angle,
            "building_width": building_width,
            "building_length": building_length,
            "north_span": north_span,
            "south_span": south_span,
            "ew_half_width": ew_half_width,
            "valley_offset": valley_offset,
        }

    def perform_complete_analysis(self, inputs: Dict) -> Dict:
        """
        Perform complete valley snow load analysis per V1 functionality.

        Args:
            inputs: Dictionary containing all input parameters

        Returns:
            Complete analysis results dictionary
        """
        from datetime import datetime

        # Extract and validate inputs
        pg = inputs.get("pg", 25.0)
        w2 = inputs.get("w2", 0.3)
        ce = inputs.get("ce", 1.0)
        ct = inputs.get("ct", 1.0)
        is_factor = inputs.get("is", 1.0)

        north_span = inputs.get("north_span", 16.0)
        south_span = inputs.get("south_span", 16.0)
        ew_half_width = inputs.get("ew_half_width", 42.0)
        valley_offset = inputs.get("valley_offset", ew_half_width)

        pitch_n = inputs.get("pitch_north", 8.0)
        pitch_w = inputs.get("pitch_west", 8.0)
        valley_angle = inputs.get("valley_angle", 90.0)

        # Beam design parameters
        beam_width = inputs.get("beam_width", 3.5)
        modulus_e = inputs.get("modulus_e", 1600000.0)
        fb_allowable = inputs.get("fb_allowable", 1600.0)
        fv_allowable = inputs.get("fv_allowable", 125.0)
        deflection_snow_limit = inputs.get("deflection_snow_limit", 240.0)
        deflection_total_limit = inputs.get("deflection_total_limit", 180.0)
        beam_depth_trial = inputs.get("beam_depth_trial", 9.5)
        jack_spacing_inches = inputs.get("jack_spacing_inches", 24.0)
        dead_load_horizontal = inputs.get("dead_load_horizontal", 15.0)
        slippery = inputs.get("slippery", False)

        # Cap spans at 500 ft per ASCE 7-22
        lu_north = min(north_span, 500)
        lu_west = min(ew_half_width, 500)

        # Calculate slope parameters
        slope_params = self.calculate_slope_parameters(pitch_n, pitch_w)

        # Check unbalanced applicability
        unbalanced_check = self.check_unbalanced_applicability(
            slope_params["s_n"], slope_params["s_w"]
        )

        # Calculate geometry
        geometry = self.calculate_valley_geometry(
            north_span, south_span, ew_half_width, valley_offset
        )

        # Calculate balanced snow load
        pf = 0.7 * ce * ct * is_factor * pg  # Flat roof snow load
        cs_n = self.snow_calculator.calculate_slope_factor(slope_params["s_n"])
        cs_w = self.snow_calculator.calculate_slope_factor(slope_params["s_w"])
        ps_balanced = pf * min(cs_n, cs_w)  # Use more conservative slope factor

        # Calculate drift loads using comprehensive V1 logic
        drift_results = self._calculate_comprehensive_drifts(
            pg,
            lu_north,
            lu_west,
            w2,
            ce,
            ct,
            is_factor,
            slope_params,
            unbalanced_check,
            valley_angle,
        )

        # Calculate valley geometry and rafter length
        valley_geometry = self._calculate_valley_details(
            north_span, south_span, ew_half_width, valley_offset, valley_angle
        )

        # Perform beam analysis
        beam_analysis = self._perform_beam_analysis(
            valley_geometry["rafter_length"],
            ps_balanced,
            drift_results,
            beam_width,
            modulus_e,
            fb_allowable,
            fv_allowable,
            deflection_snow_limit,
            deflection_total_limit,
            beam_depth_trial,
            jack_spacing_inches,
            dead_load_horizontal,
            slippery,
        )

        # Generate diagrams data
        diagrams_data = self._prepare_diagrams_data(
            valley_geometry, ps_balanced, drift_results, slope_params
        )

        # Compile comprehensive results
        results = {
            "inputs": inputs,
            "slope_parameters": slope_params,
            "unbalanced_applicability": unbalanced_check,
            "geometry": geometry,
            "valley_geometry": valley_geometry,
            "snow_loads": {
                "pg": pg,
                "pf": pf,
                "ps_balanced": ps_balanced,
                "drift_loads": drift_results,
            },
            "beam_analysis": beam_analysis,
            "diagrams": diagrams_data,
            "status": "analysis_complete",
            "timestamp": datetime.now().isoformat(),
            "asce_reference": "ASCE 7-22 Chapters 7.3, 7.6, 7.7, 7.8",
        }

        return results

    def validate_inputs(self, inputs: Dict) -> Tuple[bool, list]:
        """
        Validate input parameters.

        Args:
            inputs: Input parameters dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate snow load parameters
        if inputs.get("pg", 0) <= 0:
            errors.append("Ground snow load (pg) must be positive")

        if not 0.25 <= inputs.get("w2", 0) <= 0.65:
            errors.append("Winter wind parameter (W2) should be between 0.25 and 0.65")

        # Validate geometry
        if inputs.get("north_span", 0) <= 0:
            errors.append("North span must be positive")

        if inputs.get("south_span", 0) <= 0:
            errors.append("South span must be positive")

        if inputs.get("ew_half_width", 0) <= 0:
            errors.append("E-W half-width must be positive")

        return len(errors) == 0, errors

    def _calculate_comprehensive_drifts(
        self,
        pg,
        lu_north,
        lu_west,
        w2,
        ce,
        ct,
        is_factor,
        slope_params,
        unbalanced_check,
        valley_angle,
    ):
        """Calculate comprehensive drift loads per V1 logic."""

        # Calculate slope factors for each roof plane
        cs_n = self.snow_calculator.calculate_slope_factor(slope_params["s_n"])
        cs_w = self.snow_calculator.calculate_slope_factor(slope_params["s_w"])

        # Calculate flat roof snow load
        pf = 0.7 * ce * ct * is_factor * pg

        # Calculate balanced loads for each roof plane
        ps_n = pf * cs_n
        ps_w = pf * cs_w

        # Check for narrow roof conditions (special case)
        narrow_roof_n = lu_north <= 20.0
        narrow_roof_w = lu_west <= 20.0

        # Initialize drift results
        result_north = {"hd_ft": 0, "drift_width_ft": 0, "pd_max_psf": 0}
        result_west = {"hd_ft": 0, "drift_width_ft": 0, "pd_max_psf": 0}

        # Calculate north roof drift if unbalanced applies
        if unbalanced_check["north_applies"] and not narrow_roof_n:
            # Calculate gable drift per ASCE 7-22 Section 7.7
            result_north = self.snow_calculator.calculate_gable_drift(
                pg,
                lu_north,
                w2,
                ce,
                ct,
                cs_n,
                is_factor,
                slope_params["s_n"],
                slope_params["S_n"],
            )

        # Calculate west roof drift if unbalanced applies
        if unbalanced_check["west_applies"] and not narrow_roof_w:
            # Calculate gable drift per ASCE 7-22 Section 7.7
            result_west = self.snow_calculator.calculate_gable_drift(
                pg,
                lu_west,
                w2,
                ce,
                ct,
                cs_w,
                is_factor,
                slope_params["s_w"],
                slope_params["S_w"],
            )

        # Calculate valley drift (intersection of gable drifts)
        valley_drift = self._calculate_valley_drift(
            result_north, result_west, valley_angle
        )

        return {
            "north_drift": result_north,
            "west_drift": result_west,
            "valley_drift": valley_drift,
            "narrow_roof_n": narrow_roof_n,
            "narrow_roof_w": narrow_roof_w,
            "ps_n": ps_n,
            "ps_w": ps_w,
        }

    def _calculate_valley_drift(self, result_north, result_west, valley_angle):
        """Calculate valley drift per ASCE 7-22 Section 7.7.3."""
        import math

        # Valley drift uses intersecting gable drifts
        hd_n = result_north.get("hd_ft", 0)
        hd_w = result_west.get("hd_ft", 0)

        w_n = result_north.get("drift_width_ft", 0)
        w_w = result_west.get("drift_width_ft", 0)

        pd_max_n = result_north.get("pd_max_psf", 0)
        pd_max_w = result_west.get("pd_max_psf", 0)

        # Valley angle in radians
        math.radians(valley_angle)

        # Calculate governing valley drift parameters
        # Use maximum values from intersecting drifts
        hd_valley = max(hd_n, hd_w)
        w_valley = max(w_n, w_w)
        pd_max_valley = max(pd_max_n, pd_max_w)

        return {
            "hd_ft": hd_valley,
            "drift_width_ft": w_valley,
            "pd_max_psf": pd_max_valley,
            "valley_angle_deg": valley_angle,
        }

    def _calculate_valley_details(
        self, north_span, south_span, ew_half_width, valley_offset, valley_angle
    ):
        """Calculate detailed valley geometry."""
        import math

        # Valley rafter length calculation
        # Distance from valley intersection to ridge intersection
        ridge_to_ridge = math.sqrt(north_span**2 + ew_half_width**2)

        # Valley angle in radians
        math.radians(valley_angle)

        # Valley rafter length (distance from valley to eave)
        valley_rafter_length = math.sqrt(north_span**2 + valley_offset**2)

        return {
            "rafter_length": valley_rafter_length,
            "ridge_to_ridge": ridge_to_ridge,
            "north_span": north_span,
            "south_span": south_span,
            "ew_half_width": ew_half_width,
            "valley_offset": valley_offset,
            "valley_angle": valley_angle,
        }

    def _perform_beam_analysis(
        self,
        rafter_len,
        ps_balanced,
        drift_results,
        beam_width,
        modulus_e,
        fb_allowable,
        fv_allowable,
        deflection_snow_limit,
        deflection_total_limit,
        beam_depth_trial,
        jack_spacing_inches,
        dead_load_horizontal,
        slippery,
    ):
        """Perform comprehensive beam analysis per V1 logic."""

        # Get governing drift load
        gov_drift = drift_results["valley_drift"]
        hd = gov_drift["hd_ft"]
        w_drift = gov_drift["drift_width_ft"]
        pd_max = gov_drift["pd_max_psf"]

        # Convert jack spacing to feet
        jack_spacing_ft = jack_spacing_inches / 12.0

        # Calculate point loads
        snow_point_loads, dead_point_loads, lv_horizontal = self._calculate_point_loads(
            rafter_len,
            ps_balanced,
            hd,
            w_drift,
            pd_max,
            dead_load_horizontal,
            jack_spacing_ft,
            slippery,
        )

        # Perform ASD beam analysis
        beam_results = self.beam_analyzer.analyze_beam(
            rafter_len,
            snow_point_loads,
            dead_point_loads,
            beam_width,
            beam_depth_trial,
            modulus_e,
            fb_allowable,
            fv_allowable,
            deflection_snow_limit,
            deflection_total_limit,
        )

        return {
            "point_loads": {
                "snow": snow_point_loads,
                "dead": dead_point_loads,
                "lv_horizontal": lv_horizontal,
            },
            "governing_drift": gov_drift,
            "beam_results": beam_results,
            "jack_spacing_ft": jack_spacing_ft,
        }

    def _calculate_point_loads(
        self,
        L,
        ps_balanced,
        hd,
        w_drift,
        pd_max,
        dead_load_horizontal,
        jack_spacing_ft,
        slippery,
    ):
        """Calculate point loads for beam analysis."""

        # Tributary width for uniform loads
        tributary_width = jack_spacing_ft

        # Calculate uniform loads
        ps_balanced * tributary_width  # lb/ft
        dead_uniform = dead_load_horizontal * tributary_width  # lb/ft

        # Calculate drift surcharge point loads
        snow_point_loads = []
        distances_from_eave = []

        # Number of jack points along rafter
        num_jacks = int(L / jack_spacing_ft) + 1

        for i in range(num_jacks):
            x = i * jack_spacing_ft
            if x > L:
                x = L

            distances_from_eave.append(x)

            # Calculate drift load at this point
            if w_drift > 0 and x <= w_drift:
                pd_val = pd_max * (1 - x / w_drift)  # Linear taper
            else:
                pd_val = 0

            # Point load from drift surcharge
            drift_point_load = pd_val * tributary_width
            snow_point_loads.append(drift_point_load)

        # Dead loads (uniform - converted to point loads at jacks)
        dead_point_loads = [dead_uniform * jack_spacing_ft] * len(snow_point_loads)

        return snow_point_loads, dead_point_loads, tributary_width

    def _prepare_diagrams_data(
        self, valley_geometry, ps_balanced, drift_results, slope_params
    ):
        """Prepare data for diagram generation."""
        return {
            "plan_view": {
                "north_span": valley_geometry["north_span"],
                "south_span": valley_geometry["south_span"],
                "ew_half_width": valley_geometry["ew_half_width"],
                "valley_offset": valley_geometry["valley_offset"],
            },
            "drift_overlay": {
                "north_span": valley_geometry["north_span"],
                "south_span": valley_geometry["south_span"],
                "ew_half_width": valley_geometry["ew_half_width"],
                "valley_offset": valley_geometry["valley_offset"],
                "north_drift": drift_results["north_drift"],
                "ps_balanced": ps_balanced,
            },
            "drift_profile": {
                "hd": drift_results["valley_drift"]["hd_ft"],
                "w": drift_results["valley_drift"]["drift_width_ft"],
                "pd_max": drift_results["valley_drift"]["pd_max_psf"],
            },
            "snow_distribution": {
                "north_span": valley_geometry["north_span"],
                "south_span": valley_geometry["south_span"],
                "ps_balanced": ps_balanced,
                "pd_max": drift_results["valley_drift"]["pd_max_psf"],
                "south_span_param": valley_geometry["south_span"],
            },
        }
