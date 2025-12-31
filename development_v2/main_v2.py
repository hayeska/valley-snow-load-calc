#!/usr/bin/env python3
"""
Valley Snow Load Calculator V2.0
ASCE 7-22 Compliant Engineering Software

Main application entry point for the modular version 2.0.

Features:
- Complete ASCE 7-22 snow load analysis
- Modular architecture for maintainability
- Professional GUI with modern design
- Project management and reporting
- Comprehensive engineering calculations

Usage:
    python main_v2.py

Or import as module:
    from valley_calculator import create_application
    app = create_application()
    app.run()
"""

import sys
from pathlib import Path

# Add the valley_calculator package to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from valley_calculator import create_application
except ImportError as e:
    print(f"Error importing valley_calculator: {e}")
    print("Make sure you're running from the development_v2 directory")
    sys.exit(1)


def main():
    """Main application entry point."""
    print("Starting Valley Snow Load Calculator V2.0...")
    print("ASCE 7-22 Compliant Engineering Software")
    print("=" * 50)

    try:
        # Create the application
        app = create_application()

        # Start the GUI event loop
        app.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
