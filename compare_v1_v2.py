#!/usr/bin/env python3
"""
V1 vs V2 Comparison Script
Comprehensive comparison of Valley Snow Load Calculator versions
"""

import sys
import os
from pathlib import Path
import json

# Add paths for both versions
v1_path = Path(__file__).parent
v2_path = Path(__file__).parent / "development_v2"

sys.path.insert(0, str(v1_path))
sys.path.insert(0, str(v2_path))

def test_v1_calculation():
    """Test V1 calculation functionality."""
    print("=" * 60)
    print("TESTING V1 CALCULATION")
    print("=" * 60)

    try:
        # Import V1 modules
        sys.path.insert(0, str(v1_path))
        import gui_interface

        # Create a mock Tk root for testing
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window

        # Create V1 calculator instance
        v1_app = gui_interface.ValleySnowCalculator(root)

        # Set test inputs (using V1's internal methods)
        test_inputs = {
            'pg': 25.0,
            'north_span': 16.0,
            'south_span': 16.0,
            'ew_half_width': 42.0,
            'valley_offset': 42.0,
            'pitch_north': 8.0,
            'pitch_west': 8.0,
            'beam_width': 3.5,
            'beam_depth_trial': 9.5,
            'ce': 1.0,
            'ct': 1.0,
            'is': 1.0,
            'w2': 0.3
        }

        # Set inputs in V1 app (simulate user input)
        for key, value in test_inputs.items():
            if hasattr(v1_app, f"{key}_var"):
                getattr(v1_app, f"{key}_var").set(str(value))

        print("V1 inputs set successfully")

        # Run calculation
        v1_app.calculate()

        # Extract results from output text
        output_text = v1_app.output_text.get(1.0, tk.END)
        print("V1 calculation completed")

        # Check for key results in output
        results_found = {
            'balanced_load': 'ps =' in output_text,
            'drift_load': 'Governing drift' in output_text or 'pd_max' in output_text,
            'beam_analysis': 'Maximum Moment' in output_text,
            'shear_force': 'Maximum shear' in output_text,
            'deflection': 'Maximum deflection' in output_text,
            'diagrams': 'generating diagrams' in output_text.lower(),
            'validation': 'Validation passed' in output_text
        }

        print(f"V1 Results found: {sum(results_found.values())}/{len(results_found)}")
        for key, found in results_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {key.replace('_', ' ').title()}")

        root.destroy()
        return output_text, results_found

    except Exception as e:
        print(f"V1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, {}

def test_v2_calculation():
    """Test V2 calculation functionality."""
    print("\n" + "=" * 60)
    print("TESTING V2 CALCULATION")
    print("=" * 60)

    try:
        # Import V2 modules
        from valley_calculator import create_application

        # Create V2 app
        v2_app = create_application()

        # Test inputs
        test_inputs = {
            'pg': 25.0,
            'north_span': 16.0,
            'south_span': 16.0,
            'ew_half_width': 42.0,
            'valley_offset': 42.0,
            'pitch_north': 8.0,
            'pitch_west': 8.0,
            'beam_width': 3.5,
            'beam_depth_trial': 9.5,
            'ce': 1.0,
            'ct': 1.0,
            'is': 1.0,
            'w2': 0.3
        }

        print("Running V2 calculation...")
        results = v2_app.calculator.perform_complete_analysis(test_inputs)

        print("V2 calculation completed")

        # Check results structure
        results_found = {
            'inputs': 'inputs' in results,
            'slope_parameters': 'slope_parameters' in results,
            'snow_loads': 'snow_loads' in results and 'ps_balanced' in results['snow_loads'],
            'drift_loads': 'drift_loads' in results.get('snow_loads', {}),
            'beam_analysis': 'beam_analysis' in results,
            'beam_results': 'beam_results' in results.get('beam_analysis', {}),
            'stress_checks': 'stress_checks' in results.get('beam_analysis', {}).get('beam_results', {}),
            'diagrams': 'diagrams' in results,
            'validation': results.get('status') == 'analysis_complete'
        }

        print(f"V2 Results found: {sum(results_found.values())}/{len(results_found)}")
        for key, found in results_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {key.replace('_', ' ').title()}")

        return results, results_found

    except Exception as e:
        print(f"V2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, {}

def compare_features():
    """Compare feature sets between V1 and V2."""
    print("\n" + "=" * 80)
    print("FEATURE COMPARISON: V1 vs V2")
    print("=" * 80)

    features = {
        'Core Calculations': {
            'ASCE 7-22 Snow Loads': 'Both have this',
            'Balanced Load Calculation': 'Both have this',
            'Drift Load Analysis': 'Both have this',
            'Slope Factor Calculation': 'Both have this',
            'Load Factor Application': 'Both have this'
        },
        'Structural Analysis': {
            'ASD Beam Design': 'Both have this',
            'Load Combinations': 'Both have this',
            'Stress Checks (Bending/Shear)': 'Both have this',
            'Deflection Analysis': 'Both have this',
            'Point Load Distribution': 'Both have this'
        },
        'Geometry & Diagrams': {
            'Valley Rafter Calculations': 'Both have this',
            'Roof Plan Diagrams': 'Both have this',
            'Drift Profile Diagrams': 'Both have this',
            'Load Distribution Diagrams': 'Both have this',
            'Real-time Diagram Updates': 'V1 only'
        },
        'User Interface': {
            'Input Validation': 'Both have this',
            'Error Messages': 'Both have this',
            'Progress Indicators': 'V2 only (modern)',
            'Themes (Light/Dark)': 'V2 only',
            'Tooltips': 'V2 only (comprehensive)',
            'Responsive Layout': 'V2 only'
        },
        'Reporting': {
            'PDF Report Generation': 'Both have this',
            'HTML Report Generation': 'V1 only',
            'Project Save/Load': 'Both have this',
            'Results Export': 'Both have this'
        },
        'Architecture': {
            'Modular Design': 'V2 only',
            'Maintainable Code': 'V2 only',
            'Unit Testing Ready': 'V2 only',
            'Single Monolithic File': 'V1 only',
            'Hard to Maintain': 'V1 only'
        }
    }

    for category, category_features in features.items():
        print(f"\n{category}:")
        print("-" * len(category))
        for feature, status in category_features.items():
            print(f"  {feature}: {status}")

def main():
    """Main comparison function."""
    print("VALLEY SNOW LOAD CALCULATOR - V1 vs V2 COMPARISON")
    print("Testing both versions with identical inputs...")

    # Test V1
    v1_output, v1_results = test_v1_calculation()

    # Test V2
    v2_output, v2_results = test_v2_calculation()

    # Feature comparison
    compare_features()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)

    v1_score = sum(v1_results.values())
    v2_score = sum(v2_results.values())

    print(f"V1 Functionality Score: {v1_score}/{len(v1_results)}")
    print(f"V2 Functionality Score: {v2_score}/{len(v2_results)}")

    if v1_score > v2_score:
        print("\n🔴 V2 is MISSING functionality compared to V1")
        missing = [k for k, v in v2_results.items() if not v and k in v1_results and v1_results[k]]
        if missing:
            print("Missing in V2:", ", ".join(missing))
    elif v2_score > v1_score:
        print("\n🟢 V2 has ADDITIONAL functionality compared to V1")
    else:
        print("\n🟡 V1 and V2 have equivalent functionality")

    print("\nRECOMMENDATIONS:")
    print("- Use V1 for complete, proven engineering calculations")
    print("- Use V2 for modern UI and maintainable codebase (once complete)")
    print("- V2 needs additional migration work to match V1 functionality")

if __name__ == "__main__":
    main()
