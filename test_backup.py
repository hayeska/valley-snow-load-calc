#!/usr/bin/env python3
"""
Test script for backup system functionality
Run this to verify backup scripts work correctly
"""

import os
import sys
import json
import tempfile
from pathlib import Path


def test_python_backup():
    """Test the Python backup scheduler"""
    print("🧪 Testing Python Backup Scheduler")
    print("=" * 40)

    try:
        # Import the backup scheduler
        sys.path.insert(0, os.getcwd())
        from backup_scheduler import BackupScheduler

        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project = Path(temp_dir) / "test_project"
            test_backup = Path(temp_dir) / "test_backups"

            # Create a minimal test project
            test_project.mkdir()
            (test_project / "test_file.txt").write_text("Test content")
            (test_project / "test_config.json").write_text('{"test": true}')

            # Create test config
            test_config = test_project / "backup_config.json"
            test_config.write_text(
                json.dumps({"excludePatterns": ["*.log"], "maxLocalBackups": 5})
            )

            print(f"📁 Test project: {test_project}")
            print(f"💾 Test backup dir: {test_backup}")

            # Initialize scheduler
            scheduler = BackupScheduler(
                project_dir=str(test_project),
                backup_dir=str(test_backup),
                max_backups=3,
            )

            # Test backup creation
            print("\n📦 Creating test backup...")
            result = scheduler.run_once()

            if result and result.exists():
                size = result.stat().st_size
                print(f"✅ Backup created: {result.name}")
                print(f"📊 Size: {size} bytes")

                # Verify backup contents
                import zipfile

                with zipfile.ZipFile(result, "r") as zipf:
                    files = zipf.namelist()
                    print(f"📁 Contains {len(files)} files:")
                    for file in files[:5]:  # Show first 5 files
                        print(f"   - {file}")
                    if len(files) > 5:
                        print(f"   ... and {len(files) - 5} more files")

                return True
            else:
                print("❌ Backup creation failed")
                return False

    except ImportError as e:
        print(f"❌ Cannot import BackupScheduler: {e}")
        print("💡 Make sure backup_scheduler.py is in the current directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_config_file():
    """Test backup configuration file"""
    print("\n🧪 Testing Backup Configuration")
    print("=" * 40)

    config_path = Path("backup_config.json")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            print("✅ Configuration file found and valid")
            print(f"📋 Exclude patterns: {len(config.get('excludePatterns', []))}")
            print(f"☁️  Cloud upload: {config.get('cloudUpload', False)}")
            print(f"🗜️  Compression level: {config.get('compressionLevel', 6)}")

            # Validate required fields
            required_fields = ["excludePatterns", "cloudUpload", "compressionLevel"]
            missing = [field for field in required_fields if field not in config]
            if missing:
                print(f"⚠️  Missing config fields: {missing}")
            else:
                print("✅ All required config fields present")

            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            return False
    else:
        print("❌ backup_config.json not found")
        print("💡 Creating default configuration...")

        default_config = {
            "excludePatterns": [
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                "*.log",
                "auto_backups",
                "*.tmp",
                ".DS_Store",
            ],
            "includeDataFiles": True,
            "cloudUpload": False,
            "cloudProvider": "google_drive",
            "compressionLevel": 6,
            "googleDriveFolder": "Valley Snow Load Backups",
        }

        try:
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            print("✅ Default configuration created")
            return True
        except Exception as e:
            print(f"❌ Failed to create config: {e}")
            return False


def test_dependencies():
    """Test if required dependencies are available"""
    print("\n🧪 Testing Dependencies")
    print("=" * 40)

    required_modules = ["zipfile", "json", "pathlib", "os"]
    missing = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing.append(module)

    if missing:
        print(f"❌ Missing required modules: {missing}")
        return False
    else:
        print("✅ All required modules available")
        return True


def test_backup_location():
    """Test backup directory creation and permissions"""
    print("\n🧪 Testing Backup Location")
    print("=" * 40)

    try:
        # Test default backup location
        home = Path.home()
        backup_dir = home / "backups" / "valley_snow_calc"

        print(f"🏠 Home directory: {home}")
        print(f"💾 Default backup location: {backup_dir}")

        # Try to create directory
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        test_file = backup_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()

        print("✅ Backup directory is writable")
        return True

    except Exception as e:
        print(f"❌ Backup location test failed: {e}")
        return False


def main():
    """Run all backup system tests"""
    print("🚀 Valley Snow Load Calculator - Backup System Test")
    print("=" * 60)

    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_config_file),
        ("Backup Location", test_backup_location),
        ("Python Backup", test_python_backup),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Backup system is ready.")
        print("\n🚀 To start backups:")
        print("   python backup_scheduler.py --test    # Test mode")
        print("   python backup_scheduler.py --once    # Single backup")
        print("   python backup_scheduler.py           # Continuous mode")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure Python 3.x is installed")
        print("   - Check file permissions")
        print("   - Verify backup_config.json is valid JSON")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
