#!/usr/bin/env python3
"""
Test script for the Valley Snow Load Calculator recovery system
Demonstrates crash recovery, backup scanning, and data merging
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

def create_test_scenario():
    """Create a test scenario with various backup files"""
    print("🧪 Creating test recovery scenario...")

    # Create temporary directory structure
    test_dir = Path(tempfile.mkdtemp(prefix="valley_recovery_test_"))
    print(f"📁 Test directory: {test_dir}")

    # Create mock crash flag
    crash_flag = test_dir / ".crash"
    crash_flag.write_text(datetime.now().isoformat())
    print("🚨 Created crash flag")

    # Create mock state backup
    state_backup = test_dir / "state.backup.json"
    state_data = {
        "project_info": {
            "name": "Valley Snow Load Calculator",
            "version": "1.0",
            "auto_saved": datetime.now().isoformat(),
            "description": "Auto-saved state after crash"
        },
        "inputs": {
            "snow_load_parameters": {
                "pg": "45.0",
                "w2": "0.6",
                "ce": "1.1",
                "ct": "1.0",
                "is_factor": "1.0 - Risk Cat II"
            },
            "building_geometry": {
                "pitch_north": "8.5",
                "pitch_west": "7.2",
                "north_span": "18.0",
                "south_span": "16.5"
            }
        },
        "results": {
            "balanced_loads": {
                "north_roof": 25.3,
                "west_roof": 22.1
            },
            "calculation_timestamp": datetime.now().isoformat()
        }
    }

    with open(state_backup, 'w') as f:
        json.dump(state_data, f, indent=2)
    print("💾 Created state backup")

    # Create auto-backup directory
    auto_backup_dir = test_dir / "auto_backups" / "2025-12-31_15-30-00"
    auto_backup_dir.mkdir(parents=True)

    # Create partial backup files
    user_prefs = {
        "window_geometry": "1920x1080+100+100",
        "theme": "dark",
        "last_project": "test_project.json"
    }

    with open(auto_backup_dir / "user_preferences.json", 'w') as f:
        json.dump(user_prefs, f, indent=2)

    material_data = {
        "materials": [
            {"name": "Southern Pine No. 2", "Fb": 875, "E": 1600000},
            {"name": "Douglas Fir", "Fb": 1000, "E": 1800000}
        ]
    }

    with open(auto_backup_dir / "material_database.json", 'w') as f:
        json.dump(material_data, f, indent=2)

    print("📦 Created auto-backup with partial data")

    return test_dir

def test_recovery_system(test_dir):
    """Test the recovery system with the created scenario"""
    print("\n🔍 Testing Recovery System")
    print("=" * 40)

    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(test_dir)

    try:
        # Import recovery system (assuming it's in the parent directory)
        sys.path.insert(0, str(Path(test_dir).parent))
        from crash_recovery import CrashRecovery

        # Initialize recovery system
        recovery = CrashRecovery()

        # Test crash detection
        print("1. Testing crash detection...")
        indicators = recovery.scan_for_crash_indicators()
        print(f"   Crash detected: {indicators['crash_flag_exists']}")
        print(f"   State backup exists: {indicators['state_backup_exists']}")
        print(f"   Auto backups exist: {indicators['auto_backups_exist']}")

        # Test backup scanning
        print("\n2. Testing backup scanning...")
        backups = recovery.scan_backup_files()

        print(f"   State backups found: {1 if backups['state_backup'] else 0}")
        print(f"   Auto backup directories: {len(backups['auto_backups'])}")
        print(f"   File backups: {len(backups['file_backups'])}")

        # Test recovery options analysis
        print("\n3. Testing recovery analysis...")
        options = recovery.analyze_recovery_options()

        print("   Recommendations:")
        for rec in options['recommended_actions']:
            print(f"   • {rec}")

        print(f"   Git revert options: {len(options['git_revert_options'])}")
        print(f"   Backup recovery options: {len(options['backup_recovery_options'])}")

        # Test state restoration
        print("\n4. Testing state restoration...")
        success = recovery.restore_from_state_backup()
        print(f"   State restoration: {'✅ Success' if success else '❌ Failed'}")

        # Test data merging
        print("\n5. Testing data merging...")
        merge_success = recovery.merge_backup_data(
            "state_backup",
            ["2025-12-31_15-30-00"] if recovery.backup_dir.exists() else []
        )
        print(f"   Data merging: {'✅ Success' if merge_success else '❌ Failed'}")

        # Check for merged file
        merged_files = list(Path(".").glob("merged_recovery_*.json"))
        if merged_files:
            print(f"   Merged file created: {merged_files[0].name}")

            # Show merge contents
            with open(merged_files[0], 'r') as f:
                merged_data = json.load(f)

            merge_info = merged_data.get("_merge_info", {})
            print(f"   Sources merged: {len(merge_info.get('sources', []))}")
            print(f"   Data points: {merge_info.get('data_preserved', 0)}")

        return True

    except Exception as e:
        print(f"❌ Recovery system test failed: {e}")
        return False

    finally:
        # Restore original directory
        os.chdir(original_cwd)

def test_data_merge_utilities(test_dir):
    """Test the data merge utilities"""
    print("\n🔀 Testing Data Merge Utilities")
    print("=" * 40)

    try:
        # Import merge utilities
        sys.path.insert(0, str(Path(test_dir).parent))
        from data_merge_utilities import DataMergeUtilities

        util = DataMergeUtilities()

        # Test source analysis
        print("1. Testing source analysis...")
        sources = [
            str(test_dir / "state.backup.json"),
            str(test_dir / "auto_backups" / "2025-12-31_15-30-00")
        ]

        analysis = util.analyze_backup_sources(*sources)
        print(f"   Sources analyzed: {len(analysis['sources'])}")
        print(".2f")
        print(f"   Potential conflicts: {analysis['potential_conflicts']}")
        print(f"   Recommended strategy: {analysis['recommended_merge_strategy']}")

        # Test data merging
        print("\n2. Testing data merging...")
        merged_data = util.merge_backup_sources(
            sources[0],
            [sources[1]],
            str(test_dir / "test_merged.json")
        )

        merge_info = merged_data.get("_merge_info", {})
        print(f"   Merge completed: {len(merge_info.get('sources', []))} sources")
        print(f"   Conflicts resolved: {merge_info.get('conflicts_resolved', 0)}")
        print(f"   Data points: {merge_info.get('data_preserved', 0)}")

        # Check merged file
        merged_file = test_dir / "test_merged.json"
        if merged_file.exists():
            print(f"   ✅ Merged file created: {merged_file.name}")

        return True

    except Exception as e:
        print(f"❌ Data merge test failed: {e}")
        return False

def cleanup_test_scenario(test_dir):
    """Clean up the test scenario"""
    print(f"\n🧹 Cleaning up test scenario: {test_dir}")
    try:
        import shutil
        shutil.rmtree(test_dir)
        print("✅ Test cleanup completed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run all recovery system tests"""
    print("🚀 Valley Snow Load Calculator - Recovery System Test Suite")
    print("=" * 70)

    # Create test scenario
    test_dir = create_test_scenario()

    try:
        # Run tests
        recovery_success = test_recovery_system(test_dir)
        merge_success = test_data_merge_utilities(test_dir)

        # Summary
        print("\n" + "=" * 70)
        print("📊 Test Results Summary")
        print("=" * 70)

        tests = [
            ("Crash Recovery System", recovery_success),
            ("Data Merge Utilities", merge_success)
        ]

        passed = 0
        for test_name, success in tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1

        print(f"\n📈 Overall: {passed}/{len(tests)} test suites passed")

        if passed == len(tests):
            print("\n🎉 All recovery system tests passed!")
            print("\n🚀 Recovery commands ready for production use:")
            print("   python crash_recovery.py              # Interactive recovery")
            print("   python crash_recovery.py --scan       # Scan for issues")
            print("   python crash_recovery.py --recover    # Auto-recover")
            print("   python data_merge_utilities.py --merge file1.json file2.json")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            print("\n🔧 Troubleshooting:")
            print("   - Ensure all Python files are in the correct locations")
            print("   - Check file permissions")
            print("   - Verify JSON syntax in backup files")

        return passed == len(tests)

    finally:
        # Always cleanup
        cleanup_test_scenario(test_dir)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
