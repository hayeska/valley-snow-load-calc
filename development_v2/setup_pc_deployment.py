#!/usr/bin/env python3
"""
Valley Snow Load Calculator - PC Deployment Setup
Creates a standalone executable for Windows PC deployment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "matplotlib",
        "reportlab",
        "pytest",  # For testing
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Missing required packages. Installing...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    print("✅ All dependencies verified")


def create_executable():
    """Create standalone executable using PyInstaller."""
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("Creating standalone executable...")

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--name",
        "ValleySnowLoadCalculator",
        "--icon",
        "icon.ico",  # Add icon if available
        "main_v2.py",
    ]

    subprocess.check_call(cmd)
    print("✅ Executable created in dist/ directory")


def create_installer():
    """Create Windows installer (optional, requires NSIS or similar)."""
    print("Windows installer creation would go here...")
    print("For now, the executable in dist/ can be distributed directly")
    print("Or use tools like:")
    print("- NSIS (Nullsoft Scriptable Install System)")
    print("- Inno Setup")
    print("- Advanced Installer")


def create_portable_version():
    """Create portable version with all dependencies."""
    print("Creating portable version...")

    # Create portable directory
    portable_dir = Path("portable_valley_calculator")
    portable_dir.mkdir(exist_ok=True)

    # Copy executable
    if Path("dist/ValleySnowLoadCalculator.exe").exists():
        shutil.copy("dist/ValleySnowLoadCalculator.exe", portable_dir)

    # Copy required data files
    data_files = [
        "README.md",
        "LICENSE",  # If you have one
    ]

    for file in data_files:
        if Path(file).exists():
            shutil.copy(file, portable_dir)

    # Create run script
    run_script = portable_dir / "Run_Calculator.bat"
    with open(run_script, "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting Valley Snow Load Calculator...\n")
        f.write("ValleySnowLoadCalculator.exe\n")
        f.write("pause\n")

    print(f"✅ Portable version created in {portable_dir}/")


def main():
    """Main deployment setup."""
    print("=== Valley Snow Load Calculator - PC Deployment Setup ===")
    print()

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    try:
        print("1. Checking dependencies...")
        check_dependencies()

        print("\n2. Creating executable...")
        create_executable()

        print("\n3. Creating portable version...")
        create_portable_version()

        print("\n4. Optional: Windows installer...")
        create_installer()

        print("\n" + "=" * 50)
        print("🎉 PC DEPLOYMENT COMPLETE!")
        print("=" * 50)
        print()
        print("Distribution options:")
        print("• Portable: Copy the 'portable_valley_calculator' folder")
        print("• Installer: Use the executable from 'dist/' for installation")
        print("• Direct: Run 'dist/ValleySnowLoadCalculator.exe' directly")
        print()
        print("The application will:")
        print("• Run completely offline (no internet required)")
        print("• Store projects locally in user's Documents folder")
        print("• Include auto-save and crash recovery")
        print("• Provide professional engineering interface")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
