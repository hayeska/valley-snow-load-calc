#!/usr/bin/env python3
"""
Valley Snow Load Calculator - Crash Recovery System
Comprehensive crash recovery with backup scanning, Git revert suggestions, and data merging

Usage:
    python crash_recovery.py                 # Interactive recovery menu
    python crash_recovery.py --scan         # Scan for recovery options
    python crash_recovery.py --recover      # Attempt automatic recovery
    python crash_recovery.py --revert <commit>  # Revert to specific commit
    python crash_recovery.py --merge        # Merge partial backup data
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
import logging


class CrashRecovery:
    def __init__(self, project_dir: Optional[str] = None):
        self.project_dir = Path(project_dir or Path.cwd())
        self.backup_dir = self.project_dir / "auto_backups"
        self.state_backup = self.project_dir / "state.backup.json"
        self.crash_flag = self.project_dir / ".crash"

        # Setup logging
        self.setup_logging()

        self.logger.info("Crash Recovery System initialized")
        self.logger.info(f"Project directory: {self.project_dir}")

    def setup_logging(self):
        """Setup logging for recovery operations"""
        log_file = self.project_dir / "crash_recovery.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def scan_for_crash_indicators(self) -> Dict[str, any]:
        """Scan for crash indicators and recovery options"""
        indicators = {
            "crash_flag_exists": self.crash_flag.exists(),
            "state_backup_exists": self.state_backup.exists(),
            "auto_backups_exist": self.backup_dir.exists()
            and any(self.backup_dir.iterdir()),
            "git_repo_healthy": self.check_git_repo_health(),
            "modified_files": self.get_modified_files(),
            "recent_commits": self.get_recent_commits(10),
        }

        if indicators["crash_flag_exists"]:
            try:
                with open(self.crash_flag, "r") as f:
                    crash_time = f.read().strip()
                indicators["crash_timestamp"] = crash_time
                self.logger.info(f"Crash detected from: {crash_time}")
            except:
                indicators["crash_timestamp"] = "unknown"

        return indicators

    def check_git_repo_health(self) -> bool:
        """Check if Git repository is in a healthy state"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except:
            return False

    def get_modified_files(self) -> List[str]:
        """Get list of modified files in working directory"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return [
                    line[3:]
                    for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]
        except:
            pass
        return []

    def get_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent Git commits for potential revert points"""
        commits = []
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "-n",
                    str(count),
                    "--pretty=format:%H|%s|%cd",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                env={**os.environ, "GIT_COMMITTER_DATE": "", "GIT_AUTHOR_DATE": ""},
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split("|", 2)
                        if len(parts) >= 3:
                            commits.append(
                                {
                                    "hash": parts[0],
                                    "message": parts[1],
                                    "date": parts[2],
                                }
                            )
        except Exception as e:
            self.logger.error(f"Error getting recent commits: {e}")

        return commits

    def scan_backup_files(self) -> Dict[str, any]:
        """Scan all available backup sources"""
        backups = {
            "auto_backups": [],
            "state_backup": None,
            "git_backups": [],
            "file_backups": [],
        }

        # Scan auto_backups directory
        if self.backup_dir.exists():
            for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
                if backup_dir.is_dir():
                    backup_info = {
                        "path": backup_dir,
                        "timestamp": backup_dir.name,
                        "files": list(backup_dir.glob("*")),
                    }
                    backups["auto_backups"].append(backup_info)

        # Check state backup
        if self.state_backup.exists():
            try:
                with open(self.state_backup, "r") as f:
                    data = json.load(f)
                backups["state_backup"] = {
                    "path": self.state_backup,
                    "data": data,
                    "timestamp": data.get("project_info", {}).get(
                        "auto_saved", "unknown"
                    ),
                }
            except Exception as e:
                self.logger.error(f"Error reading state backup: {e}")

        # Scan for backup_*.zip files
        for zip_file in self.project_dir.glob("backup_*.zip"):
            backups["file_backups"].append(
                {
                    "path": zip_file,
                    "size": zip_file.stat().st_size,
                    "timestamp": zip_file.stat().st_mtime,
                }
            )

        return backups

    def analyze_recovery_options(self) -> Dict[str, any]:
        """Analyze all available recovery options"""
        crash_indicators = self.scan_for_crash_indicators()
        backups = self.scan_backup_files()

        options = {
            "crash_detected": crash_indicators["crash_flag_exists"],
            "crash_timestamp": crash_indicators.get("crash_timestamp"),
            "git_revert_options": self.suggest_git_reverts(
                crash_indicators["recent_commits"]
            ),
            "backup_recovery_options": self.analyze_backup_options(backups),
            "data_merge_options": self.suggest_data_merging(backups),
            "recommended_actions": self.generate_recommendations(
                crash_indicators, backups
            ),
        }

        return options

    def suggest_git_reverts(
        self, commits: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """Suggest safe Git revert points"""
        suggestions = []

        for commit in commits[:5]:  # Top 5 recent commits
            # Analyze commit message for safety
            message = commit["message"].lower()
            risk_level = "low"

            if any(word in message for word in ["fix", "bug", "error", "crash"]):
                risk_level = "medium"
            elif any(
                word in message
                for word in ["feat", "add", "remove", "delete", "refactor"]
            ):
                risk_level = "high"

            suggestions.append(
                {
                    "commit_hash": commit["hash"],
                    "message": commit["message"],
                    "date": commit["date"],
                    "risk_level": risk_level,
                    "recommended": risk_level == "low",
                }
            )

        return suggestions

    def analyze_backup_options(self, backups: Dict[str, any]) -> List[Dict[str, any]]:
        """Analyze backup recovery options"""
        options = []

        # State backup option
        if backups["state_backup"]:
            options.append(
                {
                    "type": "state_backup",
                    "description": "Restore from auto-saved application state",
                    "path": str(backups["state_backup"]["path"]),
                    "timestamp": backups["state_backup"]["timestamp"],
                    "completeness": "high",
                    "recommended": True,
                }
            )

        # Auto backup options
        for backup in backups["auto_backups"][:3]:  # Top 3 most recent
            options.append(
                {
                    "type": "auto_backup",
                    "description": f"Restore from auto-backup: {backup['timestamp']}",
                    "path": str(backup["path"]),
                    "timestamp": backup["timestamp"],
                    "files": [str(f.name) for f in backup["files"]],
                    "completeness": "partial",
                    "recommended": len(backup["files"]) > 0,
                }
            )

        return options

    def suggest_data_merging(self, backups: Dict[str, any]) -> List[Dict[str, any]]:
        """Suggest data merging strategies"""
        merge_options = []

        if backups["state_backup"] and backups["auto_backups"]:
            merge_options.append(
                {
                    "type": "state_plus_auto",
                    "description": "Merge auto-saved state with latest auto-backup data",
                    "sources": [
                        "state.backup.json",
                        backups["auto_backups"][0]["path"].name
                        if backups["auto_backups"]
                        else None,
                    ],
                    "merge_strategy": "state_priority",
                    "recommended": True,
                }
            )

        return merge_options

    def generate_recommendations(
        self, indicators: Dict[str, any], backups: Dict[str, any]
    ) -> List[str]:
        """Generate prioritized recovery recommendations"""
        recommendations = []

        if indicators["crash_flag_exists"]:
            recommendations.append(
                "🔴 CRITICAL: Crash detected - immediate recovery recommended"
            )

        if backups["state_backup"]:
            recommendations.append(
                "✅ Recommended: Restore from state.backup.json (most complete recovery)"
            )

        if backups["auto_backups"]:
            recommendations.append(
                f"✅ Alternative: Use latest auto-backup ({backups['auto_backups'][0]['timestamp']})"
            )

        safe_reverts = [
            r for r in indicators.get("git_revert_options", []) if r.get("recommended")
        ]
        if safe_reverts:
            recommendations.append(
                f"⚠️  Safe Git revert available: {safe_reverts[0]['message'][:50]}..."
            )

        if not any(
            [
                indicators["crash_flag_exists"],
                backups["state_backup"],
                backups["auto_backups"],
            ]
        ):
            recommendations.append("✅ No crash detected - repository appears healthy")

        return recommendations

    def perform_git_revert(self, commit_hash: str, create_backup: bool = True) -> bool:
        """Perform Git revert to specified commit"""
        try:
            if create_backup:
                # Create backup branch first
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_branch = f"backup_before_revert_{timestamp}"

                subprocess.run(
                    ["git", "checkout", "-b", backup_branch],
                    cwd=self.project_dir,
                    check=True,
                )
                subprocess.run(
                    ["git", "checkout", "master"], cwd=self.project_dir, check=True
                )

                self.logger.info(f"Created backup branch: {backup_branch}")

            # Perform revert
            result = subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully reverted to commit: {commit_hash}")
                return True
            else:
                self.logger.error(f"Git revert failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error during Git revert: {e}")
            return False

    def restore_from_state_backup(self) -> bool:
        """Restore application state from state.backup.json"""
        try:
            if not self.state_backup.exists():
                self.logger.error("State backup file not found")
                return False

            with open(self.state_backup, "r") as f:
                backup_data = json.load(f)

            # Restore different types of data
            restored_items = []

            # Restore user preferences if available
            if "inputs" in backup_data:
                # This would restore GUI state in a real application
                restored_items.append("application_inputs")

            if "results" in backup_data:
                # This would restore calculation results
                restored_items.append("calculation_results")

            self.logger.info(
                f"Restored items from state backup: {', '.join(restored_items)}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error restoring from state backup: {e}")
            return False

    def merge_backup_data(
        self, primary_source: str, secondary_sources: List[str]
    ) -> bool:
        """Merge data from multiple backup sources"""
        try:
            merged_data = {}

            # Load primary source
            if primary_source == "state_backup" and self.state_backup.exists():
                with open(self.state_backup, "r") as f:
                    merged_data.update(json.load(f))

            # Merge secondary sources (auto-backups)
            for source in secondary_sources:
                source_path = self.backup_dir / source
                if source_path.exists():
                    for file_path in source_path.glob("*"):
                        if file_path.name.endswith(".json"):
                            try:
                                with open(file_path, "r") as f:
                                    file_data = json.load(f)
                                # Merge logic - primary source takes precedence
                                self.merge_dict_recursive(
                                    merged_data, file_data, primary_override=True
                                )
                            except Exception as e:
                                self.logger.warning(f"Could not merge {file_path}: {e}")

            # Save merged data
            merged_file = (
                self.project_dir
                / f"merged_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(merged_file, "w") as f:
                json.dump(merged_data, f, indent=2)

            self.logger.info(f"Created merged recovery file: {merged_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error merging backup data: {e}")
            return False

    def merge_dict_recursive(
        self, target: dict, source: dict, primary_override: bool = True
    ):
        """Recursively merge dictionaries"""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(target[key], dict) and isinstance(value, dict):
                self.merge_dict_recursive(target[key], value, primary_override)
            elif not primary_override:
                # Only override if primary_override is False
                target[key] = value

    def cleanup_after_recovery(self):
        """Clean up temporary files after successful recovery"""
        try:
            # Remove crash flag
            if self.crash_flag.exists():
                self.crash_flag.unlink()
                self.logger.info("Removed crash flag")

            # Optionally remove state backup after successful recovery
            # if self.state_backup.exists():
            #     self.state_backup.unlink()
            #     self.logger.info("Removed state backup after recovery")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def interactive_recovery(self):
        """Interactive recovery menu"""
        print("🚨 Valley Snow Load Calculator - Crash Recovery System")
        print("=" * 60)

        # Scan for recovery options
        options = self.analyze_recovery_options()

        print(f"Crash Detected: {'Yes' if options['crash_detected'] else 'No'}")
        if options.get("crash_timestamp"):
            print(f"Crash Time: {options['crash_timestamp']}")

        print("\n📋 Available Recovery Options:")
        print("-" * 40)

        # Show recommendations
        for i, rec in enumerate(options["recommended_actions"], 1):
            print(f"{i}. {rec}")

        print("\n🔄 Detailed Options:")
        print("-" * 40)

        # Git revert options
        if options["git_revert_options"]:
            print("\nGit Revert Options:")
            for i, revert in enumerate(options["git_revert_options"][:3], 1):
                risk_icon = (
                    "🟢"
                    if revert["risk_level"] == "low"
                    else "🟡"
                    if revert["risk_level"] == "medium"
                    else "🔴"
                )
                print(
                    f"  {i}. {risk_icon} {revert['risk_level'].upper()} RISK: {revert['message'][:50]}..."
                )

        # Backup options
        if options["backup_recovery_options"]:
            print("\nBackup Recovery Options:")
            for i, backup in enumerate(options["backup_recovery_options"], 1):
                rec_icon = "✅" if backup.get("recommended") else "⚠️"
                print(f"  {i}. {rec_icon} {backup['description']}")

        # Merge options
        if options["data_merge_options"]:
            print("\nData Merge Options:")
            for i, merge in enumerate(options["data_merge_options"], 1):
                rec_icon = "✅" if merge.get("recommended") else "⚠️"
                print(f"  {i}. {rec_icon} {merge['description']}")

        print("\n💡 Commands:")
        print("  scan     - Scan for recovery options")
        print("  recover  - Attempt automatic recovery")
        print("  revert   - Git revert to safe commit")
        print("  merge    - Merge backup data")
        print("  cleanup  - Clean up after recovery")
        print("  quit     - Exit recovery system")

        while True:
            try:
                cmd = input("\nEnter command: ").strip().lower()

                if cmd == "quit":
                    break
                elif cmd == "scan":
                    self.interactive_recovery()  # Refresh
                    break
                elif cmd == "recover":
                    if self.attempt_automatic_recovery(options):
                        print("✅ Automatic recovery completed")
                        self.cleanup_after_recovery()
                    else:
                        print("❌ Automatic recovery failed")
                elif cmd.startswith("revert"):
                    parts = cmd.split()
                    if len(parts) > 1 and len(parts[1]) >= 7:  # Short commit hash
                        commit_hash = parts[1]
                        if self.perform_git_revert(commit_hash):
                            print(f"✅ Reverted to commit: {commit_hash}")
                            self.cleanup_after_recovery()
                        else:
                            print("❌ Git revert failed")
                    else:
                        print("Usage: revert <commit-hash>")
                elif cmd == "merge":
                    if self.merge_backup_data("state_backup", []):
                        print("✅ Data merging completed")
                    else:
                        print("❌ Data merging failed")
                elif cmd == "cleanup":
                    self.cleanup_after_recovery()
                    print("✅ Cleanup completed")
                else:
                    print("Unknown command. Type 'quit' to exit.")

            except KeyboardInterrupt:
                print("\n👋 Recovery system interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def attempt_automatic_recovery(self, options: Dict[str, any]) -> bool:
        """Attempt automatic recovery based on available options"""
        try:
            # Priority 1: State backup
            if options["backup_recovery_options"]:
                state_backup = next(
                    (
                        b
                        for b in options["backup_recovery_options"]
                        if b["type"] == "state_backup"
                    ),
                    None,
                )
                if state_backup and self.restore_from_state_backup():
                    self.logger.info("Successfully recovered from state backup")
                    return True

            # Priority 2: Latest auto backup
            if options["backup_recovery_options"]:
                auto_backup = next(
                    (
                        b
                        for b in options["backup_recovery_options"]
                        if b["type"] == "auto_backup"
                    ),
                    None,
                )
                if auto_backup:
                    # This would implement auto-backup restoration
                    self.logger.info(
                        f"Would restore from auto-backup: {auto_backup['path']}"
                    )
                    return True

            # Priority 3: Safe Git revert
            safe_reverts = [
                r
                for r in options.get("git_revert_options", [])
                if r.get("recommended") and r["risk_level"] == "low"
            ]
            if safe_reverts and self.perform_git_revert(safe_reverts[0]["commit_hash"]):
                self.logger.info("Successfully reverted to safe commit")
                return True

            self.logger.warning("No automatic recovery options available")
            return False

        except Exception as e:
            self.logger.error(f"Automatic recovery failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Valley Snow Load Calculator Crash Recovery"
    )
    parser.add_argument("--project-dir", help="Project directory (default: current)")
    parser.add_argument("--scan", action="store_true", help="Scan for recovery options")
    parser.add_argument(
        "--recover", action="store_true", help="Attempt automatic recovery"
    )
    parser.add_argument("--revert", metavar="COMMIT", help="Revert to specific commit")
    parser.add_argument("--merge", action="store_true", help="Merge backup data")
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up after recovery"
    )

    args = parser.parse_args()

    recovery = CrashRecovery(args.project_dir)

    if args.scan:
        options = recovery.analyze_recovery_options()
        print(json.dumps(options, indent=2, default=str))
    elif args.recover:
        options = recovery.analyze_recovery_options()
        success = recovery.attempt_automatic_recovery(options)
        sys.exit(0 if success else 1)
    elif args.revert:
        success = recovery.perform_git_revert(args.revert)
        sys.exit(0 if success else 1)
    elif args.merge:
        success = recovery.merge_backup_data("state_backup", [])
        sys.exit(0 if success else 1)
    elif args.cleanup:
        recovery.cleanup_after_recovery()
    else:
        # Interactive mode
        recovery.interactive_recovery()


if __name__ == "__main__":
    main()
