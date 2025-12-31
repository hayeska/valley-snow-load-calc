#!/usr/bin/env python3
"""
Debug script to test V2 calculation and diagram generation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from valley_calculator.core.calculator import ValleyCalculator


def test_calculation():
    """Test the V2 calculation with debug output."""
    print("=== V2 Calculation Debug Test ===")

    # Create calculator
    calc = ValleyCalculator()

    # Test input data
    test_inputs = {
        "pg": 25.0,  # Ground snow load
        "w2": 0.3,  # Winter wind parameter
        "ce": 1.0,  # Exposure factor
        "ct": 1.0,  # Thermal factor
        "is": 1.0,  # Importance factor
        "north_span": 16.0,  # North span
        "south_span": 16.0,  # South span
        "ew_half_width": 42.0,  # E-W half width
        "valley_offset": 16.0,  # Valley offset
        "pitch_north": 8,  # North pitch
        "pitch_west": 8,  # West pitch
        "dead_load": 15.0,  # Dead load
        "beam_width": 3.5,  # Beam width
        "beam_depth": 9.5,  # Beam depth
    }

    print(f"Test inputs: {test_inputs}")

    # Validate inputs
    is_valid, errors = calc.validate_inputs(test_inputs)
    print(f"Input validation: valid={is_valid}, errors={errors}")

    if is_valid:
        # Perform calculation
        print("Performing calculation...")
        results = calc.perform_complete_analysis(test_inputs)

        print(f"Results keys: {list(results.keys())}")

        # Check snow loads
        snow_loads = results.get("snow_loads", {})
        print(f"Snow loads: {snow_loads}")

        # Check drift loads
        drift_loads = snow_loads.get("drift_loads", {})
        print(f"Drift loads: {drift_loads}")

        north_drift = drift_loads.get("north_drift", {})
        print(f"North drift: {north_drift}")

        return results
    else:
        print("Input validation failed!")
        return None


if __name__ == "__main__":
    results = test_calculation()
    if results:
        print("✅ Calculation successful!")
    else:
        print("❌ Calculation failed!")
