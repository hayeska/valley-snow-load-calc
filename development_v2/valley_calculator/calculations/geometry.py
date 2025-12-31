# geometry.py - Roof geometry calculations for Valley Calculator V2.0

import math
from typing import Dict, Tuple, List


class RoofGeometry:
    """
    Valley roof geometry calculations and validation.

    Handles complex valley roof configurations including:
    - Valley rafter layouts
    - Jack rafter spacing
    - Tributary area calculations
    - Geometry validation
    """

    def __init__(self):
        """Initialize with default geometry parameters."""
        self.min_valley_angle = 30.0  # degrees
        self.max_valley_angle = 150.0  # degrees

    def calculate_valley_parameters(
        self, south_span: float, valley_offset: float
    ) -> Dict[str, float]:
        """
        Calculate valley geometry parameters.

        Args:
            south_span: Distance from E-W ridge to south eave (ft)
            valley_offset: Horizontal offset to valley low point (ft)

        Returns:
            Dictionary with valley geometry parameters
        """
        # Valley length (horizontal projection)
        lv = math.sqrt(south_span**2 + valley_offset**2)

        # Valley angle from horizontal
        valley_angle = (
            math.degrees(math.atan(south_span / valley_offset))
            if valley_offset > 0
            else 90.0
        )

        # Valley slope
        valley_slope = south_span / valley_offset if valley_offset > 0 else float("inf")

        return {
            "valley_length_horizontal": lv,
            "valley_angle_degrees": valley_angle,
            "valley_slope_ratio": valley_slope,
            "south_span": south_span,
            "valley_offset": valley_offset,
        }

    def calculate_jack_rafter_positions(
        self, south_span: float, valley_offset: float, spacing_inches: float = 16.0
    ) -> List[Tuple[float, float]]:
        """
        Calculate jack rafter positions along the valley.

        Args:
            south_span: Distance from E-W ridge to south eave (ft)
            valley_offset: Horizontal offset to valley low point (ft)
            spacing_inches: Jack rafter spacing (inches)

        Returns:
            List of (sloped_distance, horizontal_distance) tuples for each jack rafter
        """
        spacing_ft = spacing_inches / 12.0
        valley_length = math.sqrt(south_span**2 + valley_offset**2)

        # Calculate number of jack rafters
        num_jacks = int(valley_length / spacing_ft)

        positions = []
        for i in range(num_jacks + 1):
            # Distance from valley low point
            distance_from_low = i * spacing_ft

            if distance_from_low <= valley_length:
                # Calculate position relative to valley low point
                if valley_offset > 0:
                    # Position along the valley line
                    ratio = distance_from_low / valley_length
                    x_pos = ratio * valley_offset  # horizontal component
                    y_pos = ratio * south_span  # vertical component

                    positions.append((distance_from_low, x_pos))
                else:
                    # Vertical valley
                    positions.append((distance_from_low, 0.0))

        return positions

    def calculate_tributary_areas(
        self,
        jack_positions: List[Tuple[float, float]],
        ew_half_width: float,
        north_span: float,
        south_span: float,
    ) -> List[Dict[str, float]]:
        """
        Calculate tributary areas for each jack rafter.

        Args:
            jack_positions: List of (sloped_distance, horizontal_offset) tuples
            ew_half_width: Half-width from N-S ridge to eave (ft)
            north_span: North roof span (ft)
            south_span: South roof span (ft)

        Returns:
            List of dictionaries with tributary area data for each jack rafter
        """
        tributary_data = []

        for i, (sloped_dist, horiz_offset) in enumerate(jack_positions):
            # Calculate tributary width (half spacing on each side)
            if i == 0:
                # First rafter at valley low point
                tributary_width = (
                    sloped_dist if len(jack_positions) > 1 else sloped_dist * 2
                )
            elif i == len(jack_positions) - 1:
                # Last rafter
                prev_dist = jack_positions[i - 1][0]
                tributary_width = (sloped_dist - prev_dist) / 2
            else:
                # Middle rafters
                prev_dist = jack_positions[i - 1][0]
                next_dist = jack_positions[i + 1][0]
                tributary_width = (next_dist - prev_dist) / 2

            # Tributary areas for north and west roof planes
            # Simplified calculation - would be more complex in reality
            north_area = tributary_width * ew_half_width * 2  # Both sides
            west_area = tributary_width * north_span

            tributary_data.append(
                {
                    "jack_number": i + 1,
                    "sloped_distance_ft": sloped_dist,
                    "horizontal_offset_ft": horiz_offset,
                    "tributary_width_ft": tributary_width,
                    "north_tributary_area_sqft": north_area,
                    "west_tributary_area_sqft": west_area,
                    "total_tributary_area_sqft": north_area + west_area,
                }
            )

        return tributary_data

    def validate_geometry(
        self,
        north_span: float,
        south_span: float,
        ew_half_width: float,
        valley_offset: float,
    ) -> Tuple[bool, List[str]]:
        """
        Validate roof geometry parameters.

        Args:
            north_span: North roof span (ft)
            south_span: South roof span (ft)
            ew_half_width: E-W half-width (ft)
            valley_offset: Valley horizontal offset (ft)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Basic positive checks
        if north_span <= 0:
            errors.append("North span must be positive")

        if south_span <= 0:
            errors.append("South span must be positive")

        if ew_half_width <= 0:
            errors.append("E-W half-width must be positive")

        if valley_offset < 0:
            errors.append("Valley offset cannot be negative")

        # Geometry consistency checks
        if north_span < 5.0:
            errors.append("North span seems unusually small (< 5 ft)")

        if south_span < 5.0:
            errors.append("South span seems unusually small (< 5 ft)")

        if ew_half_width < 10.0:
            errors.append("E-W half-width seems unusually small (< 10 ft)")

        # Valley angle check
        if valley_offset > 0:
            valley_angle = math.degrees(math.atan(south_span / valley_offset))
            if valley_angle < self.min_valley_angle:
                errors.append(
                    f"Valley angle ({valley_angle:.1f}°) is unusually shallow"
                )
            if valley_angle > self.max_valley_angle:
                errors.append(f"Valley angle ({valley_angle:.1f}°) is unusually steep")

        return len(errors) == 0, errors

    def calculate_roof_plan_dimensions(
        self, north_span: float, south_span: float, ew_half_width: float
    ) -> Dict[str, float]:
        """
        Calculate overall roof plan dimensions.

        Args:
            north_span: North roof span (ft)
            south_span: South roof span (ft)
            ew_half_width: E-W half-width (ft)

        Returns:
            Dictionary with plan dimensions
        """
        building_length = north_span + south_span
        building_width = 2 * ew_half_width

        # Calculate roof areas (simplified - flat projections)
        north_roof_area = north_span * building_width
        south_roof_area = south_span * building_width
        total_roof_area = north_roof_area + south_roof_area

        return {
            "building_length_ft": building_length,
            "building_width_ft": building_width,
            "north_roof_area_sqft": north_roof_area,
            "south_roof_area_sqft": south_roof_area,
            "total_roof_area_sqft": total_roof_area,
        }
