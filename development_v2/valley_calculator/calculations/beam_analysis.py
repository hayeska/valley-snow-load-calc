# beam_analysis.py - Structural beam analysis for Valley Calculator V2.0

from typing import Dict, List, Tuple


class BeamAnalyzer:
    """
    Structural analysis for valley beam design.

    Performs ASD (Allowable Stress Design) analysis including:
    - Load combinations per ASCE 7-05/16
    - Bending stress calculations
    - Shear stress calculations
    - Deflection checks
    """

    def __init__(self):
        """Initialize with default material properties."""
        # Default Douglas Fir-Larch Select Structural properties
        self.defaults = {
            "Fb": 2400,  # Bending stress (psi)
            "Fv": 265,  # Shear stress (psi)
            "E": 1800000,  # Modulus of elasticity (psi)
            "density": 35,  # pcf
            "width": 3.5,  # inches
            "depth": 9.5,  # inches
        }

    def calculate_section_properties(
        self, width: float, depth: float
    ) -> Dict[str, float]:
        """
        Calculate beam section properties.

        Args:
            width: Beam width (inches)
            depth: Beam depth (inches)

        Returns:
            Dictionary with section properties
        """
        area = width * depth
        moment_inertia = width * depth**3 / 12.0
        section_modulus = moment_inertia / (depth / 2.0)

        return {
            "area_sqin": area,
            "moment_inertia_in4": moment_inertia,
            "section_modulus_in3": section_modulus,
            "width_in": width,
            "depth_in": depth,
        }

    def calculate_load_combinations(
        self,
        dead_loads: List[float],
        snow_loads: List[float],
        valley_drift_load: float = 0.0,
    ) -> Dict[str, List[float]]:
        """
        Calculate ASD load combinations per ASCE 7-05 Section 2.4.

        Args:
            dead_loads: Dead load values at each position (lb)
            snow_loads: Snow load values at each position (lb)
            valley_drift_load: Additional valley drift load (psf)

        Returns:
            Dictionary with load combinations
        """
        combinations = {}

        # Basic combinations
        combinations["D"] = dead_loads  # Dead load only
        combinations["D+S"] = [d + s for d, s in zip(dead_loads, snow_loads)]  # D + S
        combinations["D+0.7S"] = [
            d + 0.7 * s for d, s in zip(dead_loads, snow_loads)
        ]  # D + 0.7S

        # Include valley drift if present
        if valley_drift_load > 0:
            combinations["D+S+Drift"] = [
                d + s + valley_drift_load for d, s in zip(dead_loads, snow_loads)
            ]

        return combinations

    def calculate_shear_force(
        self, loads: List[float], span_length: float
    ) -> List[float]:
        """
        Calculate shear force diagram.

        Args:
            loads: Point loads along the beam (lb)
            span_length: Total beam span (ft)

        Returns:
            List of shear forces at key points (lb)
        """
        shear_forces = []
        cumulative_load = 0.0

        # Calculate shear at each load point (simplified)
        for i, load in enumerate(loads):
            cumulative_load += load
            shear_forces.append(cumulative_load)

        return shear_forces

    def calculate_bending_moment(
        self, loads: List[float], positions: List[float], span_length: float
    ) -> Tuple[List[float], float]:
        """
        Calculate bending moment diagram.

        Args:
            loads: Point loads along the beam (lb)
            positions: Positions of loads from left end (ft)
            span_length: Total beam span (ft)

        Returns:
            Tuple of (moment_values, max_moment)
        """
        moments = []
        max_moment = 0.0

        # Calculate moment at each point (simplified for point loads)
        for i, (load, pos) in enumerate(zip(loads, positions)):
            # Moment contribution from loads to the right
            moment_right = load * (span_length - pos)

            # Moment contribution from loads to the left (simplified)
            moment_left = sum(l * p for l, p in zip(loads[:i], positions[:i]))

            total_moment = moment_right - moment_left
            moments.append(total_moment)
            max_moment = max(max_moment, abs(total_moment))

        return moments, max_moment

    def calculate_deflection(
        self,
        loads: List[float],
        positions: List[float],
        span_length: float,
        E: float,
        I: float,
    ) -> Tuple[List[float], float]:
        """
        Calculate beam deflection using moment-area method (simplified).

        Args:
            loads: Point loads along the beam (lb)
            positions: Positions of loads from left end (ft)
            span_length: Total beam span (ft)
            E: Modulus of elasticity (psi)
            I: Moment of inertia (in^4)

        Returns:
            Tuple of (deflection_values, max_deflection)
        """
        # Simplified deflection calculation
        # For a simply supported beam with point loads, max deflection occurs at center
        total_load = sum(loads)
        center_deflection = (5 * total_load * span_length**4) / (
            384 * E * I * 1728
        )  # Convert to inches

        # Simplified - return constant deflection for now
        deflections = [center_deflection * 0.8] * len(loads)  # Approximation
        max_deflection = center_deflection

        return deflections, max_deflection

    def check_bending_stress(
        self,
        max_moment: float,
        section_modulus: float,
        Fb: float,
        load_duration_factor: float = 1.0,
    ) -> Dict[str, float]:
        """
        Check bending stress against allowable.

        Args:
            max_moment: Maximum bending moment (lb-ft)
            section_modulus: Section modulus (in^3)
            Fb: Allowable bending stress (psi)
            load_duration_factor: Load duration factor

        Returns:
            Dictionary with stress analysis results
        """
        # Convert moment to lb-in
        moment_in = max_moment * 12.0

        # Calculate actual bending stress
        fb_actual = moment_in / section_modulus

        # Allowable stress with load duration
        fb_allowable = Fb * load_duration_factor

        # Utilization ratio
        utilization = fb_actual / fb_allowable

        return {
            "fb_actual_psi": fb_actual,
            "fb_allowable_psi": fb_allowable,
            "utilization_ratio": utilization,
            "passes_bending": utilization <= 1.0,
        }

    def check_shear_stress(
        self, max_shear: float, area: float, Fv: float
    ) -> Dict[str, float]:
        """
        Check shear stress against allowable.

        Args:
            max_shear: Maximum shear force (lb)
            area: Cross-sectional area (in^2)
            Fv: Allowable shear stress (psi)

        Returns:
            Dictionary with shear analysis results
        """
        # Calculate actual shear stress
        fv_actual = max_shear / area

        # Utilization ratio
        utilization = fv_actual / Fv

        return {
            "fv_actual_psi": fv_actual,
            "fv_allowable_psi": Fv,
            "utilization_ratio": utilization,
            "passes_shear": utilization <= 1.0,
        }

    def check_deflection(
        self, max_deflection: float, span_length: float, deflection_limit: float = 0.003
    ) -> Dict[str, float]:
        """
        Check deflection against allowable limits.

        Args:
            max_deflection: Maximum deflection (inches)
            span_length: Beam span (ft)
            deflection_limit: Allowable deflection ratio (span/300 = 0.0033)

        Returns:
            Dictionary with deflection analysis results
        """
        span_inches = span_length * 12.0
        allowable_deflection = deflection_limit * span_inches

        utilization = max_deflection / allowable_deflection

        return {
            "deflection_actual_in": max_deflection,
            "deflection_allowable_in": allowable_deflection,
            "utilization_ratio": utilization,
            "passes_deflection": utilization <= 1.0,
        }

    def perform_beam_analysis(
        self,
        loads: List[float],
        positions: List[float],
        span_length: float,
        width: float = None,
        depth: float = None,
        Fb: float = None,
        Fv: float = None,
        E: float = None,
    ) -> Dict:
        """
        Perform complete beam analysis.

        Args:
            loads: Point loads along the beam (lb)
            positions: Positions of loads from left end (ft)
            span_length: Total beam span (ft)
            width, depth: Beam dimensions (inches)
            Fb, Fv, E: Material properties (psi)

        Returns:
            Complete beam analysis results
        """
        # Use defaults if not provided
        width = width or self.defaults["width"]
        depth = depth or self.defaults["depth"]
        Fb = Fb or self.defaults["Fb"]
        Fv = Fv or self.defaults["Fv"]
        E = E or self.defaults["E"]

        # Calculate section properties
        section_props = self.calculate_section_properties(width, depth)

        # Calculate shear and moment
        shear_forces = self.calculate_shear_force(loads, span_length)
        moments, max_moment = self.calculate_bending_moment(
            loads, positions, span_length
        )
        deflections, max_deflection = self.calculate_deflection(
            loads, positions, span_length, E, section_props["moment_inertia_in4"]
        )

        # Stress checks
        bending_check = self.check_bending_stress(
            max_moment, section_props["section_modulus_in3"], Fb
        )
        shear_check = self.check_shear_stress(
            max(shear_forces), section_props["area_sqin"], Fv
        )
        deflection_check = self.check_deflection(max_deflection, span_length)

        return {
            "section_properties": section_props,
            "loads": {
                "point_loads_lb": loads,
                "positions_ft": positions,
                "max_load_lb": max(loads),
            },
            "analysis": {
                "max_shear_lb": max(shear_forces),
                "max_moment_lbft": max_moment,
                "max_deflection_in": max_deflection,
            },
            "checks": {
                "bending": bending_check,
                "shear": shear_check,
                "deflection": deflection_check,
            },
            "overall_passes": all(
                [
                    bending_check["passes_bending"],
                    shear_check["passes_shear"],
                    deflection_check["passes_deflection"],
                ]
            ),
        }

    def analyze_beam(
        self,
        span_length,
        snow_point_loads,
        dead_point_loads,
        beam_width,
        beam_depth_trial,
        modulus_e,
        fb_allowable,
        fv_allowable,
        deflection_snow_limit,
        deflection_total_limit,
    ):
        """
        Analyze beam per V1 logic - comprehensive ASD analysis.

        Args:
            span_length: Rafter length (ft)
            snow_point_loads: Snow load point loads (lb)
            dead_point_loads: Dead load point loads (lb)
            beam_width: Beam width (inches)
            beam_depth_trial: Trial beam depth (inches)
            modulus_e: Modulus of elasticity (psi)
            fb_allowable, fv_allowable: Allowable stresses (psi)
            deflection_snow_limit, deflection_total_limit: Deflection limits (inches)

        Returns:
            Complete beam analysis results
        """

        # Convert deflection limits from inches to span ratios
        span_inches = span_length * 12.0
        deflection_snow_limit / span_inches
        deflection_total_ratio = deflection_total_limit / span_inches

        # Create positions for loads (assume evenly spaced)
        num_loads = len(snow_point_loads)
        positions = (
            [i * span_length / (num_loads - 1) for i in range(num_loads)]
            if num_loads > 1
            else [0]
        )

        # Calculate load combinations
        load_combinations = self.calculate_load_combinations(
            dead_point_loads, snow_point_loads
        )

        # Analyze each load combination
        results = {}
        max_moment_overall = 0
        max_shear_overall = 0
        max_deflection_overall = 0

        for combo_name, loads in load_combinations.items():
            # Calculate shear and moment
            shear_forces = self.calculate_shear_force(loads, span_length)
            moments, max_moment = self.calculate_bending_moment(
                loads, positions, span_length
            )
            deflections, max_deflection = self.calculate_deflection(
                loads,
                positions,
                span_length,
                modulus_e,
                self.calculate_section_properties(beam_width, beam_depth_trial)[
                    "moment_inertia_in4"
                ],
            )

            # Update overall maximums
            max_moment_overall = max(max_moment_overall, max_moment)
            max_shear_overall = max(max_shear_overall, max(shear_forces))
            max_deflection_overall = max(max_deflection_overall, max_deflection)

            results[combo_name] = {
                "loads": loads,
                "shear_forces": shear_forces,
                "moments": moments,
                "deflections": deflections,
                "max_moment": max_moment,
                "max_shear": max(shear_forces),
                "max_deflection": max_deflection,
            }

        # Section properties
        section_props = self.calculate_section_properties(beam_width, beam_depth_trial)

        # Stress checks
        bending_check = self.check_bending_stress(
            max_moment_overall, section_props["section_modulus_in3"], fb_allowable
        )
        shear_check = self.check_shear_stress(
            max_shear_overall, section_props["area_sqin"], fv_allowable
        )
        deflection_check = self.check_deflection(
            max_deflection_overall, span_length, deflection_total_ratio
        )

        return {
            "load_combinations": results,
            "section_properties": section_props,
            "max_values": {
                "moment_lbft": max_moment_overall,
                "shear_lb": max_shear_overall,
                "deflection_in": max_deflection_overall,
            },
            "stress_checks": {
                "bending": bending_check,
                "shear": shear_check,
                "deflection": deflection_check,
            },
            "overall_passes": all(
                [
                    bending_check["passes_bending"],
                    shear_check["passes_shear"],
                    deflection_check["passes_deflection"],
                ]
            ),
            "beam_size": {"width_in": beam_width, "depth_in": beam_depth_trial},
        }
