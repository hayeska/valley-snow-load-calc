#!/usr/bin/env python3
"""
Valley Snow Load Calculator - Automated Backup Scheduler
Zips the project folder every hour and saves to ~/backups/
Optional: Upload to Google Drive via API

Usage:
    python backup_scheduler.py              # Run continuously
    python backup_scheduler.py --once       # Run once and exit
    python backup_scheduler.py --test       # Test backup creation
"""

import os
import zipfile
import schedule
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
import json
import sys


class BackupScheduler:
    def __init__(self, project_dir=None, backup_dir=None, max_backups=24):
        self.project_dir = Path(project_dir or Path.cwd())
        self.backup_dir = Path(
            backup_dir or Path.home() / "backups" / "valley_snow_calc"
        )
        self.max_backups = max_backups
        self.backup_count = 0

        # Setup logging
        self.setup_logging()

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self.load_config()

        self.logger.info("Backup scheduler initialized")
        self.logger.info(f"Project directory: {self.project_dir}")
        self.logger.info(f"Backup directory: {self.backup_dir}")

    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.backup_dir / "backup_scheduler.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load backup configuration"""
        config_file = self.project_dir / "backup_config.json"
        default_config = {
            "exclude_patterns": [
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                "*.log",
                "auto_backups",
                "*.tmp",
                ".DS_Store",
                "Thumbs.db",
            ],
            "include_data_files": True,
            "cloud_upload": False,
            "cloud_provider": "google_drive",
            "compression_level": 6,
        }

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                self.logger.info("Loaded backup configuration from file")
            except Exception as e:
                self.logger.error(f"Error loading config file: {e}")

        return default_config

    def create_backup_zip(self):
        """Create a compressed backup of the project directory"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"valley_snow_calc_backup_{timestamp}.zip"
            zip_path = self.backup_dir / zip_filename

            self.logger.info(f"Creating backup: {zip_filename}")

            with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED,
                compresslevel=self.config["compression_level"],
            ) as zipf:
                # Walk through project directory
                for root, dirs, files in os.walk(self.project_dir):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not self.should_exclude(d)]

                    for file in files:
                        if not self.should_exclude(file):
                            file_path = Path(root) / file
                            try:
                                # Get relative path for zip file
                                rel_path = file_path.relative_to(self.project_dir)
                                zipf.write(file_path, rel_path)
                            except Exception as e:
                                self.logger.warning(f"Failed to add {file_path}: {e}")

            # Get zip file size
            zip_size = zip_path.stat().st_size
            self.logger.info(f"Backup created successfully: {zip_size} bytes")

            # Update backup count
            self.backup_count += 1

            # Cleanup old backups
            self.cleanup_old_backups()

            # Optional cloud upload
            if self.config.get("cloud_upload"):
                self.upload_to_cloud(zip_path)

            return zip_path

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    def should_exclude(self, name):
        """Check if a file or directory should be excluded from backup"""
        exclude_patterns = self.config["exclude_patterns"]

        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in name:
                return True

        return False

    def cleanup_old_backups(self):
        """Remove old backup files to prevent disk space issues"""
        try:
            backup_files = list(self.backup_dir.glob("valley_snow_calc_backup_*.zip"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            if len(backup_files) > self.max_backups:
                files_to_delete = backup_files[self.max_backups :]
                for old_file in files_to_delete:
                    old_file.unlink()
                    self.logger.info(f"Cleaned up old backup: {old_file.name}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")

    def upload_to_cloud(self, zip_path):
        """Upload backup to cloud storage"""
        try:
            if self.config["cloud_provider"] == "google_drive":
                self.upload_to_google_drive(zip_path)
            else:
                self.logger.warning(
                    f"Unsupported cloud provider: {self.config['cloud_provider']}"
                )

        except Exception as e:
            self.logger.error(f"Failed to upload to cloud: {e}")

    def upload_to_google_drive(self, zip_path):
        """Upload file to Google Drive"""
        try:
            # This would require google-api-python-client and oauth2client
            # For now, just log the intention
            self.logger.info(f"Would upload {zip_path.name} to Google Drive")
            self.logger.warning(
                "Google Drive upload not implemented yet - requires API setup"
            )

            # TODO: Implement actual Google Drive upload
            # 1. Install google-api-python-client, google-auth-httplib2, google-auth-oauthlib
            # 2. Setup OAuth 2.0 credentials
            # 3. Implement upload logic

        except Exception as e:
            self.logger.error(f"Google Drive upload failed: {e}")

    def run_once(self):
        """Run a single backup"""
        self.logger.info("Running single backup...")
        result = self.create_backup_zip()
        if result:
            self.logger.info(f"Backup completed: {result}")
        else:
            self.logger.error("Backup failed")
        return result

    def run_scheduler(self):
        """Run the backup scheduler continuously"""
        self.logger.info("Starting backup scheduler...")

        # Schedule hourly backups
        schedule.every().hour.do(self.create_backup_zip)

        # Also run immediately
        self.create_backup_zip()

        self.logger.info("Backup scheduler running. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Backup scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Backup scheduler error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Valley Snow Load Calculator Backup Scheduler"
    )
    parser.add_argument(
        "--project-dir", help="Project directory to backup (default: current directory)"
    )
    parser.add_argument(
        "--backup-dir", help="Backup directory (default: ~/backups/valley_snow_calc)"
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--test", action="store_true", help="Test backup creation")
    parser.add_argument(
        "--max-backups",
        type=int,
        default=24,
        help="Maximum number of backups to keep (default: 24)",
    )

    args = parser.parse_args()

    # Create scheduler
    scheduler = BackupScheduler(
        project_dir=args.project_dir,
        backup_dir=args.backup_dir,
        max_backups=args.max_backups,
    )

    if args.test:
        # Test mode - create a small test backup
        print("🧪 Testing backup creation...")
        result = scheduler.run_once()
        if result:
            print(f"✅ Test backup created: {result}")
            print(f"📁 Backup location: {result.parent}")
            print(f"📊 Backup size: {result.stat().st_size} bytes")
        else:
            print("❌ Test backup failed")
        return

    if args.once:
        # Run once
        scheduler.run_once()
    else:
        # Run continuously
        scheduler.run_scheduler()


if __name__ == "__main__":
    main()
