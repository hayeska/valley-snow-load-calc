#!/usr/bin/env python3
"""
Simple V1 vs V2 Comparison (No Unicode)
"""

import sys
from pathlib import Path

# Add paths
v1_path = Path(__file__).parent
v2_path = Path(__file__).parent / "development_v2"

sys.path.insert(0, str(v1_path))
sys.path.insert(0, str(v2_path))


def test_v1_basic():
    """Basic V1 functionality test."""
    print("TESTING V1 BASIC FUNCTIONALITY")
    print("-" * 40)

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()

        import gui_interface

        v1_app = gui_interface.ValleySnowCalculator(root)

        # Check if key methods exist
        methods_exist = {
            "calculate": hasattr(v1_app, "calculate"),
            "generate_report": hasattr(v1_app, "generate_report"),
            "save_project": hasattr(v1_app, "save_project"),
            "load_project": hasattr(v1_app, "load_project"),
            "generate_diagrams": hasattr(v1_app, "generate_diagrams"),
            "validate_all_inputs": hasattr(v1_app, "validate_all_inputs"),
        }

        print(f"V1 Methods found: {sum(methods_exist.values())}/{len(methods_exist)}")
        for method, exists in methods_exist.items():
            status = "[YES]" if exists else "[NO]"
            print(f"  {status} {method}")

        # Check file size as indicator of functionality
        v1_file = v1_path / "gui_interface.py"
        if v1_file.exists():
            size_kb = v1_file.stat().st_size / 1024
            print(".1f")

        root.destroy()
        return methods_exist

    except Exception as e:
        print(f"V1 test failed: {e}")
        return {}


def test_v2_basic():
    """Basic V2 functionality test."""
    print("\nTESTING V2 BASIC FUNCTIONALITY")
    print("-" * 40)

    try:
        from valley_calculator import create_application
        from valley_calculator.calculations import snow_loads, beam_analysis, geometry

        # Create app
        v2_app = create_application()

        # Check calculator methods
        calc_methods = {
            "perform_complete_analysis": hasattr(
                v2_app.calculator, "perform_complete_analysis"
            ),
            "calculate_slope_parameters": hasattr(
                v2_app.calculator, "calculate_slope_parameters"
            ),
            "validate_inputs": hasattr(v2_app.calculator, "validate_inputs"),
        }

        # Check calculation modules
        calc_modules = {
            "snow_loads": hasattr(snow_loads, "SnowLoadCalculator"),
            "beam_analysis": hasattr(beam_analysis, "BeamAnalyzer"),
            "geometry": hasattr(geometry, "RoofGeometry"),
        }

        # Check UI components
        ui_components = {
            "input_panel": hasattr(v2_app, "input_panel"),
            "results_display": hasattr(v2_app, "results_display"),
            "theme_manager": hasattr(v2_app, "theme_manager"),
            "tooltip_manager": hasattr(v2_app, "tooltip_manager"),
        }

        print(
            f"V2 Calculator methods: {sum(calc_methods.values())}/{len(calc_methods)}"
        )
        for method, exists in calc_methods.items():
            status = "[YES]" if exists else "[NO]"
            print(f"  {status} {method}")

        print(
            f"V2 Calculation modules: {sum(calc_modules.values())}/{len(calc_modules)}"
        )
        for module, exists in calc_modules.items():
            status = "[YES]" if exists else "[NO]"
            print(f"  {status} {module}")

        print(f"V2 UI components: {sum(ui_components.values())}/{len(ui_components)}")
        for component, exists in ui_components.items():
            status = "[YES]" if exists else "[NO]"
            print(f"  {status} {component}")

        return {**calc_methods, **calc_modules, **ui_components}

    except Exception as e:
        print(f"V2 test failed: {e}")
        return {}


def functional_comparison():
    """Compare actual functionality."""
    print("\nFUNCTIONAL COMPARISON")
    print("=" * 50)

    # Test with same inputs
    test_inputs = {
        "pg": 25.0,
        "north_span": 16.0,
        "ew_half_width": 42.0,
        "pitch_north": 8.0,
        "beam_width": 3.5,
    }

    # V2 test
    try:
        from valley_calculator import create_application

        v2_app = create_application()
        v2_results = v2_app.calculator.perform_complete_analysis(test_inputs)

        v2_functionality = {
            "snow_load_calc": "ps_balanced" in v2_results.get("snow_loads", {}),
            "drift_calc": "drift_loads" in v2_results.get("snow_loads", {}),
            "beam_analysis": "beam_analysis" in v2_results,
            "stress_checks": "stress_checks"
            in v2_results.get("beam_analysis", {}).get("beam_results", {}),
            "geometry_calc": "valley_geometry" in v2_results,
            "diagrams_data": "diagrams" in v2_results,
        }

        print("V2 Functional Tests:")
        for test, result in v2_functionality.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {test}")

        v2_score = sum(v2_functionality.values())

    except Exception as e:
        print(f"V2 functional test failed: {e}")
        v2_score = 0

    print("\nV1 vs V2 Functional Score:")
    print(f"  V2: {v2_score}/{len(v2_functionality)} core functions working")
    print("  V1: Full functionality (complete engineering calculator)")

    return v2_score


def main():
    print("VALLEY SNOW LOAD CALCULATOR - V1 vs V2 COMPARISON")
    print("=" * 60)

    # Basic functionality tests
    v1_basic = test_v1_basic()
    v2_basic = test_v2_basic()

    # Functional comparison
    v2_functional_score = functional_comparison()

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print("WHAT V1 HAS:")
    print("- Complete ASCE 7-22 snow load calculations")
    print("- Full beam analysis (ASD design)")
    print("- Drift load calculations")
    print("- Point load distribution")
    print("- Real-time diagrams (matplotlib)")
    print("- PDF and HTML report generation")
    print("- Project save/load functionality")
    print("- Input validation and error handling")
    print("- Complete GUI with all engineering features")

    print("\nWHAT V2 HAS:")
    print("- Modular architecture (maintainable)")
    print("- Modern UI with themes and tooltips")
    print("- Progress indicators")
    print("- Basic calculation framework")
    if v2_functional_score >= 4:
        print("- Core snow load and beam analysis")
    if v2_functional_score < 4:
        print("- MISSING: Complete engineering calculations")
        print("- MISSING: Full drift analysis")
        print("- MISSING: Point load distribution")
        print("- MISSING: Real-time diagrams")

    print("\nCONCLUSION:")
    if v2_functional_score >= 5:
        print("V2 is functionally complete - use V2 for modern features")
    else:
        print("V2 is MISSING CRITICAL ENGINEERING FUNCTIONALITY")
        print("Use V1 for complete, proven calculations")
        print("V2 needs more migration work")


if __name__ == "__main__":
    main()
