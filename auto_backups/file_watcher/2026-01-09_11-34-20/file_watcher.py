#!/usr/bin/env python3
"""
File Watcher System for Valley Snow Load Calculator
- Monitors all .py files for changes
- Creates timestamped backups on file save
- Auto-commits changes to Git
- Cleans up backups older than 30 minutes
"""

import sys
import shutil
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog library not installed. Install with: pip install watchdog")


class PythonFileHandler(FileSystemEventHandler):
    """Handler for Python file changes"""

    def __init__(self, backup_dir: Path, project_dir: Path, auto_commit: bool = True):
        super().__init__()
        self.backup_dir = backup_dir
        self.project_dir = project_dir
        self.auto_commit = auto_commit
        self.last_backup_time = (
            {}
        )  # Track last backup time per file to avoid duplicates
        self.backup_cooldown = 2  # Minimum seconds between backups for same file

        # Setup logging
        self.setup_logging()

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Setup logging for file watcher"""
        log_file = self.project_dir / "file_watcher.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process .py files
        if file_path.suffix != ".py":
            return

        # Ignore files in backup directories and other excluded paths
        if self.should_ignore(file_path):
            return

        # Check cooldown to avoid multiple backups for rapid saves
        now = time.time()
        file_key = str(file_path)
        if file_key in self.last_backup_time:
            if now - self.last_backup_time[file_key] < self.backup_cooldown:
                return

        self.last_backup_time[file_key] = now

        # Backup the file
        self.backup_file(file_path)

        # Auto-commit if enabled
        if self.auto_commit:
            self.auto_commit_file(file_path)

    def should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            "__pycache__",
            ".git",
            "auto_backups",
            "backup_",
            "node_modules",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
        ]

        path_str = str(file_path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def backup_file(self, file_path: Path):
        """Create timestamped backup of file"""
        try:
            # Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_subdir = self.backup_dir / timestamp
            backup_subdir.mkdir(parents=True, exist_ok=True)

            # Get relative path from project root
            try:
                rel_path = file_path.relative_to(self.project_dir)
            except ValueError:
                # File is outside project directory, use filename only
                rel_path = file_path.name

            # Create backup file path (preserve directory structure)
            backup_file_path = backup_subdir / rel_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(file_path, backup_file_path)

            self.logger.info(f"Backed up: {rel_path} -> {timestamp}/{rel_path}")

            # Cleanup old backups
            self.cleanup_old_backups()

        except Exception as e:
            self.logger.error(f"Error backing up {file_path}: {e}")

    def cleanup_old_backups(self):
        """Remove backup directories older than 30 minutes"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=30)

            for backup_subdir in self.backup_dir.iterdir():
                if not backup_subdir.is_dir():
                    continue

                # Parse timestamp from directory name
                try:
                    timestamp_str = backup_subdir.name
                    backup_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

                    if backup_time < cutoff_time:
                        # Remove old backup directory
                        shutil.rmtree(backup_subdir)
                        self.logger.info(f"Cleaned up old backup: {backup_subdir.name}")
                except ValueError:
                    # Directory name doesn't match timestamp format, skip
                    continue

        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")

    def auto_commit_file(self, file_path: Path):
        """Automatically commit file changes to Git"""
        try:
            # Get relative path from project root
            try:
                rel_path = file_path.relative_to(self.project_dir)
            except ValueError:
                rel_path = Path(file_path.name)

            # Check if file is tracked by Git
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(rel_path)],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            # If file is not tracked, add it first
            if result.returncode != 0:
                subprocess.run(
                    ["git", "add", str(rel_path)],
                    cwd=self.project_dir,
                    capture_output=True,
                    check=False,
                )

            # Stage the file
            subprocess.run(
                ["git", "add", str(rel_path)],
                cwd=self.project_dir,
                capture_output=True,
                check=False,
            )

            # Create commit message
            commit_message = f"Auto-save: {rel_path.name}"

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info(f"Auto-committed: {rel_path}")
            else:
                # No changes to commit (file unchanged) or other Git issue
                if "nothing to commit" not in result.stdout.lower():
                    self.logger.warning(
                        f"Auto-commit failed for {rel_path}: {result.stderr}"
                    )

        except Exception as e:
            self.logger.error(f"Error auto-committing {file_path}: {e}")


class FileWatcher:
    """Main file watcher class"""

    def __init__(self, project_dir: Optional[str] = None, auto_commit: bool = True):
        self.project_dir = Path(project_dir or Path.cwd())
        self.backup_dir = self.project_dir / "auto_backups" / "file_watcher"
        self.auto_commit = auto_commit
        self.observer = None
        self.handler = None
        self.running = False

        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog library is required. Install with: pip install watchdog"
            )

    def start(self):
        """Start watching for file changes"""
        if self.running:
            self.logger.warning("File watcher is already running")
            return

        # Create handler
        self.handler = PythonFileHandler(
            backup_dir=self.backup_dir,
            project_dir=self.project_dir,
            auto_commit=self.auto_commit,
        )

        # Create observer
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.project_dir), recursive=True)

        # Start observer
        self.observer.start()
        self.running = True

        self.handler.logger.info("File watcher started")
        self.handler.logger.info(f"Watching: {self.project_dir}")
        self.handler.logger.info(f"Backup directory: {self.backup_dir}")
        self.handler.logger.info(
            f"Auto-commit: {'Enabled' if self.auto_commit else 'Disabled'}"
        )

    def stop(self):
        """Stop watching for file changes"""
        if not self.running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)

        self.running = False

        if self.handler:
            self.handler.logger.info("File watcher stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def start_file_watcher_in_background(
    project_dir: Optional[str] = None, auto_commit: bool = True
):
    """Start file watcher in a background daemon thread"""

    def watcher_thread():
        try:
            watcher = FileWatcher(project_dir=project_dir, auto_commit=auto_commit)
            watcher.start()

            # Keep thread alive
            while True:
                time.sleep(1)
        except Exception as e:
            print(f"Error in file watcher thread: {e}")
            import traceback

            traceback.print_exc()

    thread = threading.Thread(target=watcher_thread, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="File Watcher for Valley Snow Load Calculator"
    )
    parser.add_argument(
        "--project-dir",
        help="Project directory to watch (default: current directory)",
        default=None,
    )
    parser.add_argument(
        "--no-auto-commit", action="store_true", help="Disable auto-commit on file save"
    )
    parser.add_argument(
        "--background", action="store_true", help="Run in background thread"
    )

    args = parser.parse_args()

    if not WATCHDOG_AVAILABLE:
        print("ERROR: watchdog library is required.")
        print("Install with: pip install watchdog")
        sys.exit(1)

    auto_commit = not args.no_auto_commit

    if args.background:
        print("Starting file watcher in background...")
        thread = start_file_watcher_in_background(
            project_dir=args.project_dir, auto_commit=auto_commit
        )
        print("File watcher running in background. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping file watcher...")
    else:
        print("Starting file watcher...")
        with FileWatcher(
            project_dir=args.project_dir, auto_commit=auto_commit
        ) as watcher:
            print("File watcher running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping file watcher...")
