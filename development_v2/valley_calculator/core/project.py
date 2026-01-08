# project.py - Resilient project management for Valley Calculator V2.0

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from ..data.persistence.database import get_database
from ..utils.logging.logger import get_logger
from ..core.recovery.error_handlers import (
    resilient_operation,
    error_boundary,
)
from ..core.recovery.checkpoint_system import (
    get_checkpoint_manager,
)


class ProjectManager:
    """
    Resilient project management with crash recovery and data integrity.

    Features:
    - SQLite-based persistent storage with transaction safety
    - Automatic checkpoints and recovery points
    - Comprehensive error handling and logging
    - Data integrity verification
    - Backup and restore capabilities
    - Auto-save functionality
    """

    def __init__(self, projects_dir: str = None):
        """Initialize resilient project manager."""
        # Legacy JSON support for migration
        if projects_dir is None:
            home = Path.home()
            self.projects_dir = home / "Documents" / "Valley Snow Load Projects"
        else:
            self.projects_dir = Path(projects_dir)

        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.recent_projects_file = self.projects_dir / "recent_projects.json"
        self.templates_dir = self.projects_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # New resilient components
        self.db = get_database()
        self.logger = get_logger()
        self.checkpoint_mgr = get_checkpoint_manager()

        # Load legacy data and migrate if needed
        self._load_recent_projects()
        self._migrate_legacy_projects()

    def _load_recent_projects(self):
        """Load list of recent projects."""
        if self.recent_projects_file.exists():
            try:
                with open(self.recent_projects_file, "r") as f:
                    self.recent_projects = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.recent_projects = []
        else:
            self.recent_projects = []

    def _save_recent_projects(self):
        """Save list of recent projects."""
        with open(self.recent_projects_file, "w") as f:
            json.dump(self.recent_projects, f, indent=2)

    @resilient_operation(retries=3, recoverable=True)
    def save_project(self, project_data: Dict, project_id: str = None) -> str:
        """
        Save project with resilience and data integrity.

        Args:
            project_data: Project data dictionary
            project_id: Optional project ID (auto-generated if not provided)

        Returns:
            Project ID of saved project
        """
        with error_boundary("save_project", recoverable=True):
            # Generate project ID if not provided
            if project_id is None:
                project_id = f"project_{uuid.uuid4().hex}"

            # Validate project data
            if not isinstance(project_data, dict):
                raise ValueError("Project data must be a dictionary")

            # Add metadata
            project_data["_metadata"] = {
                "version": "2.0.0",
                "saved_at": datetime.now().isoformat(),
                "software": "Valley Snow Load Calculator V2.0",
                "project_id": project_id,
            }

            # Extract project name for database storage
            project_name = project_data.get("project_name", "Unnamed Project")

            # Save to resilient database
            success = self.db.save_project(project_id, project_name, project_data)

            if not success:
                raise RuntimeError("Failed to save project to database")

            # Create checkpoint for recovery (only after successful save)
            try:
                self.checkpoint_mgr.create_checkpoint(
                    project_id, project_data, operation="save_project"
                )

                # Mark project as active for auto-checkpointing
                self.checkpoint_mgr.mark_project_active(project_id)
            except Exception as checkpoint_error:
                # Log checkpoint failure but don't fail the save
                self.logger.log_error(
                    checkpoint_error,
                    operation="checkpoint_creation",
                    context={"project_id": project_id},
                )

            # Add to recent projects (legacy support)
            self._add_to_recent_projects_legacy(project_id, project_name)

            # Log successful save
            self.logger.log_recovery_action(
                f"Project {project_name} saved successfully",
                True,
                {"project_id": project_id},
            )

            return project_id

    @resilient_operation(retries=3, recoverable=True)
    def load_project(self, project_id: str) -> Optional[Dict]:
        """
        Load project with resilience and recovery options.

        Args:
            project_id: Project identifier

        Returns:
            Project data dictionary or None if not found/corrupted
        """
        with error_boundary("load_project", recoverable=True):
            # Try to load from resilient database first
            project_data = self.db.load_project(project_id)

            if project_data:
                # Mark project as active for auto-checkpointing
                self.checkpoint_mgr.mark_project_active(project_id)

                # Add to recent projects (legacy support)
                project_name = project_data.get("project_name", "Unknown Project")
                self._add_to_recent_projects_legacy(project_id, project_name)

                self.logger.log_recovery_action(
                    f"Project {project_name} loaded successfully from database",
                    True,
                    {"project_id": project_id},
                )

                return project_data

            # Fallback to legacy JSON file loading
            return self._load_legacy_project(project_id)

    def _upgrade_project_format(self, project_data: Dict) -> Dict:
        """
        Upgrade project from V1.x to V2.0 format.

        Args:
            project_data: V1.x project data

        Returns:
            V2.0 compatible project data
        """
        # Add default V2.0 structure
        upgraded = {
            "project_name": project_data.get("project_name", "Upgraded Project"),
            "inputs": project_data.get("inputs", {}),
            "results": project_data.get("results", {}),
            "diagrams": project_data.get("diagrams", []),
            "metadata": project_data.get("metadata", {}),
        }

        return upgraded

    def _load_legacy_project(self, project_id: str) -> Optional[Dict]:
        """
        Load project from legacy JSON files.

        Args:
            project_id: Project identifier (may be a file path)

        Returns:
            Project data or None if not found
        """
        try:
            # Check if project_id is actually a file path
            if os.path.isfile(project_id):
                filepath = project_id
            else:
                # Try to find legacy file by project name
                filepath = None
                for file_path in self.projects_dir.glob("*.json"):
                    if project_id in file_path.name:
                        filepath = str(file_path)
                        break

                if not filepath:
                    return None

            with open(filepath, "r") as f:
                project_data = json.load(f)

            # Validate and upgrade if needed
            metadata = project_data.get("_metadata", {})
            version = metadata.get("version", "1.0.0")

            if version.startswith("1."):
                project_data = self._upgrade_project_format(project_data)

            # Migrate to database
            migrated_id = self._migrate_project_to_database(project_data, filepath)

            # Add to recent projects
            self._add_to_recent_projects(filepath)

            self.logger.log_recovery_action(
                f"Legacy project loaded and migrated: {filepath}",
                True,
                {"migrated_id": migrated_id},
            )

            return project_data

        except Exception as e:
            self.logger.log_error(
                e, operation="load_legacy_project", context={"project_id": project_id}
            )
            return None

    def _migrate_project_to_database(self, project_data: Dict, filepath: str) -> str:
        """
        Migrate a legacy project to the database.

        Args:
            project_data: Project data from legacy file
            filepath: Original file path

        Returns:
            New project ID in database
        """
        try:
            project_name = project_data.get("project_name", Path(filepath).stem)
            project_id = f"migrated_{uuid.uuid4().hex}"

            success = self.db.save_project(project_id, project_name, project_data)

            if success:
                # Create backup of original file
                backup_path = (
                    self.projects_dir / "backups" / f"{Path(filepath).name}.backup"
                )
                backup_path.parent.mkdir(exist_ok=True)

                import shutil

                shutil.copy2(filepath, backup_path)

                self.logger.log_recovery_action(
                    f"Project migrated to database: {project_name}",
                    True,
                    {"project_id": project_id, "backup_path": str(backup_path)},
                )

            return project_id

        except Exception as e:
            self.logger.log_error(
                e, operation="migrate_project", context={"filepath": filepath}
            )
            return ""

    def _migrate_legacy_projects(self):
        """Migrate any existing legacy projects to the database."""
        try:
            # Only migrate if we haven't done it before
            migration_flag = self.db.get_setting("legacy_migration_completed")
            if migration_flag:
                return

            migrated_count = 0
            for json_file in self.projects_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        project_data = json.load(f)

                    # Skip if already migrated (has project_id in metadata)
                    metadata = project_data.get("_metadata", {})
                    if metadata.get("project_id"):
                        continue

                    self._migrate_project_to_database(project_data, str(json_file))
                    migrated_count += 1

                except Exception as e:
                    self.logger.log_error(
                        e, operation="bulk_migration", context={"file": str(json_file)}
                    )

            if migrated_count > 0:
                self.db.set_setting("legacy_migration_completed", True)
                self.logger.log_recovery_action(
                    f"Migrated {migrated_count} legacy projects to database", True
                )

        except Exception as e:
            self.logger.log_error(e, operation="legacy_migration")

    def _add_to_recent_projects(self, filepath: str):
        """Add project to recent projects list (legacy method)."""
        filepath = os.path.abspath(filepath)

        # Remove if already exists
        self.recent_projects = [
            p for p in self.recent_projects if p["path"] != filepath
        ]

        # Add to beginning
        project_info = {
            "path": filepath,
            "name": Path(filepath).stem,
            "last_opened": datetime.now().isoformat(),
        }

        self.recent_projects.insert(0, project_info)

        # Keep only last 10
        self.recent_projects = self.recent_projects[:10]

        self._save_recent_projects()

    def _add_to_recent_projects_legacy(self, project_id: str, project_name: str):
        """Add project to recent projects list (new method)."""
        # For now, we'll maintain both systems during transition
        # Remove if already exists
        self.recent_projects = [
            p for p in self.recent_projects if p.get("project_id") != project_id
        ]

        # Add to beginning
        project_info = {
            "project_id": project_id,
            "name": project_name,
            "last_opened": datetime.now().isoformat(),
            "type": "database",  # Mark as database project
        }

        self.recent_projects.insert(0, project_info)

        # Keep only last 10
        self.recent_projects = self.recent_projects[:10]

        self._save_recent_projects()

    @resilient_operation(retries=2, recoverable=True)
    def get_recent_projects(self) -> List[Dict]:
        """Get list of recent projects from both database and legacy sources."""
        # Combine database projects with legacy recent projects
        db_projects = self.db.list_projects()

        # Convert to recent projects format
        recent_db_projects = []
        for project in db_projects[:5]:  # Last 5 database projects
            recent_db_projects.append(
                {
                    "project_id": project["project_id"],
                    "name": project["name"],
                    "last_opened": project["updated_at"],
                    "type": "database",
                }
            )

        # Combine with legacy recent projects
        combined = recent_db_projects + self.recent_projects

        # Remove duplicates and sort by last_opened
        seen_ids = set()
        unique_projects = []
        for project in combined:
            proj_id = project.get("project_id") or project.get("path")
            if proj_id not in seen_ids:
                seen_ids.add(proj_id)
                unique_projects.append(project)

        # Sort by last_opened descending
        unique_projects.sort(key=lambda x: x.get("last_opened", ""), reverse=True)

        return unique_projects[:10]

    @resilient_operation(retries=2, recoverable=True)
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects with metadata.

        Returns:
            List of project information including recovery options
        """
        try:
            projects = self.db.list_projects()

            # Add recovery information for each project
            for project in projects:
                project_id = project["project_id"]
                recovery_options = self.checkpoint_mgr.get_recovery_options(project_id)
                project["recovery_options"] = len(recovery_options)
                project["has_checkpoints"] = len(recovery_options) > 0

            return projects

        except Exception as e:
            self.logger.log_error(e, operation="list_projects")
            return []

    @resilient_operation(retries=2, recoverable=True)
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its data.

        Args:
            project_id: Project identifier

        Returns:
            True if deletion was successful
        """
        try:
            success = self.db.delete_project(project_id)

            if success:
                # Remove from recent projects
                self.recent_projects = [
                    p for p in self.recent_projects if p.get("project_id") != project_id
                ]
                self._save_recent_projects()

                # Mark as inactive for checkpointing
                self.checkpoint_mgr.mark_project_inactive(project_id)

                self.logger.log_recovery_action(
                    f"Project {project_id} deleted successfully",
                    True,
                    {"project_id": project_id},
                )

            return success

        except Exception as e:
            self.logger.log_error(
                e, operation="delete_project", context={"project_id": project_id}
            )
            return False

    @resilient_operation(retries=2, recoverable=True)
    def get_project_recovery_options(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get recovery options for a specific project.

        Args:
            project_id: Project identifier

        Returns:
            List of available recovery options
        """
        try:
            return self.checkpoint_mgr.get_recovery_options(project_id)
        except Exception as e:
            self.logger.log_error(
                e, operation="get_recovery_options", context={"project_id": project_id}
            )
            return []

    @resilient_operation(retries=3, recoverable=True)
    def recover_project_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        """
        Recover project data from a checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Recovered project data or None if recovery failed
        """
        try:
            data = self.checkpoint_mgr.restore_from_checkpoint(checkpoint_id)

            if data:
                self.logger.log_recovery_action(
                    f"Project recovered from checkpoint {checkpoint_id}",
                    True,
                    {"checkpoint_id": checkpoint_id},
                )

            return data

        except Exception as e:
            self.logger.log_error(
                e,
                operation="recover_from_checkpoint",
                context={"checkpoint_id": checkpoint_id},
            )
            return None

    @resilient_operation(retries=2, recoverable=True)
    def create_backup(self, project_id: str = None) -> Optional[str]:
        """
        Create a backup of project data or entire database.

        Args:
            project_id: Specific project to backup, or None for full database backup

        Returns:
            Path to backup file or None if failed
        """
        try:
            if project_id:
                # Backup specific project
                project_data = self.load_project(project_id)
                if project_data:
                    backup_path = self.db.create_backup(f"project_{project_id}_backup")
                    # Additional project-specific backup logic could go here
                    return backup_path
            else:
                # Full database backup
                return self.db.create_backup()

        except Exception as e:
            self.logger.log_error(
                e, operation="create_backup", context={"project_id": project_id}
            )
            return None

    def get_system_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health and recovery status.

        Returns:
            Dictionary with health metrics and recovery information
        """
        try:
            error_summary = self.logger.get_error_summary()
            db_projects = len(self.db.list_projects())

            health_status = {
                "database_status": "healthy",
                "total_projects": db_projects,
                "error_summary": error_summary,
                "last_backup": None,  # Could be implemented to track backup times
                "recovery_ready": True,
            }

            # Check for recent errors
            if error_summary.get("total_errors", 0) > 10:
                health_status["database_status"] = "warning"

            return health_status

        except Exception as e:
            self.logger.log_error(e, operation="health_check")
            return {
                "database_status": "error",
                "error": str(e),
                "recovery_ready": False,
            }

    def create_project_template(self, name: str, template_data: Dict):
        """
        Create a project template.

        Args:
            name: Template name
            template_data: Template data
        """
        template_file = self.templates_dir / f"{name}.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f, indent=2)

    def get_project_templates(self) -> List[str]:
        """Get list of available project templates."""
        return [f.stem for f in self.templates_dir.glob("*.json")]

    def load_project_template(self, name: str) -> Dict:
        """
        Load a project template.

        Args:
            name: Template name

        Returns:
            Template data
        """
        template_file = self.templates_dir / f"{name}.json"
        with open(template_file, "r") as f:
            return json.load(f)

    def export_results(
        self, results: Dict, format: str = "json", filepath: str = None
    ) -> str:
        """
        Export analysis results.

        Args:
            results: Analysis results dictionary
            format: Export format ('json', 'csv')
            filepath: Optional output filepath

        Returns:
            Path to exported file
        """
        if format == "json":
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = str(self.projects_dir / f"results_export_{timestamp}.json")

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2)

        elif format == "csv":
            # Basic CSV export for key results
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = str(self.projects_dir / f"results_export_{timestamp}.csv")

            import csv

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Parameter", "Value", "Unit"])

                # Write key results
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        writer.writerow([key, value, ""])

        return filepath

    def validate_project_data(self, project_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate project data integrity.

        Args:
            project_data: Project data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required sections
        required_sections = ["inputs", "results"]
        for section in required_sections:
            if section not in project_data:
                errors.append(f"Missing required section: {section}")

        # Check metadata
        metadata = project_data.get("_metadata", {})
        if "version" not in metadata:
            errors.append("Missing version information")

        return len(errors) == 0, errors
