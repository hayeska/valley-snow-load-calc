# checkpoint_system.py - Auto-save and checkpoint management
# Provides incremental saves and recovery points to prevent data loss

import time
import threading
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta

from ...utils.logging.logger import get_logger
from ...data.persistence.database import get_database
from .error_handlers import resilient_operation, auto_save


class CheckpointManager:
    """
    Manages automatic checkpoints and data recovery points.

    Features:
    - Automatic periodic checkpoints
    - Change-based checkpoints (when significant changes occur)
    - Recovery point management and restoration
    - Performance-aware checkpointing
    """

    def __init__(self, auto_save_interval: int = 300, max_checkpoints: int = 50):
        """
        Initialize the checkpoint manager.

        Args:
            auto_save_interval: Seconds between automatic checkpoints
            max_checkpoints: Maximum number of checkpoints to keep per project
        """
        self.auto_save_interval = auto_save_interval
        self.max_checkpoints = max_checkpoints
        self.logger = get_logger()
        self.db = get_database()

        # Checkpoint state
        self.last_checkpoint_time = time.time()
        self.checkpoint_lock = threading.Lock()
        self.active_projects = {}  # project_id -> last_change_time

        # Auto-save thread
        self.auto_save_thread = None
        self.stop_auto_save = threading.Event()

        # Start auto-save daemon
        self._start_auto_save_daemon()

    def _start_auto_save_daemon(self):
        """Start the background auto-save daemon."""
        self.auto_save_thread = threading.Thread(
            target=self._auto_save_worker,
            daemon=True,
            name="CheckpointAutoSave"
        )
        self.auto_save_thread.start()

    def _auto_save_worker(self):
        """Background worker for automatic checkpoints."""
        while not self.stop_auto_save.wait(self.auto_save_interval):
            try:
                self._perform_auto_checkpoints()
            except Exception as e:
                self.logger.log_error(e, operation="auto_checkpoint_worker")

    def _perform_auto_checkpoints(self):
        """Perform automatic checkpoints for active projects."""
        current_time = time.time()

        with self.checkpoint_lock:
            # Check each active project
            for project_id, last_change in self.active_projects.items():
                if current_time - last_change > self.auto_save_interval:
                    try:
                        # Get current project data (this would be implemented by subclasses)
                        project_data = self._get_project_data(project_id)
                        if project_data:
                            self.create_checkpoint(
                                project_id,
                                project_data,
                                f"auto_save_{int(current_time)}",
                                "auto_save"
                            )
                    except Exception as e:
                        self.logger.log_error(e, operation="auto_checkpoint",
                                            context={"project_id": project_id})

    def create_checkpoint(self, project_id: str, data: Dict[str, Any],
                         checkpoint_id: str = None, operation: str = None) -> bool:
        """
        Create a checkpoint for the given data.

        Args:
            project_id: Project identifier
            data: Data to checkpoint
            checkpoint_id: Optional checkpoint identifier
            operation: Operation that triggered the checkpoint

        Returns:
            True if checkpoint was created successfully
        """
        if checkpoint_id is None:
            checkpoint_id = f"checkpoint_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        try:
            success = self.db.create_checkpoint(project_id, checkpoint_id, data, operation)

            if success:
                # Update last checkpoint time
                with self.checkpoint_lock:
                    self.last_checkpoint_time = time.time()
                    self.active_projects[project_id] = time.time()

                # Cleanup old checkpoints
                self._cleanup_old_checkpoints(project_id)

                self.logger.log_checkpoint(checkpoint_id, len(str(data)), operation)

            return success

        except Exception as e:
            self.logger.log_error(e, operation="create_checkpoint",
                                context={"project_id": project_id, "checkpoint_id": checkpoint_id})
            return False

    def _cleanup_old_checkpoints(self, project_id: str):
        """Clean up old checkpoints to prevent storage bloat."""
        try:
            checkpoints = self.db.get_recent_checkpoints(project_id, self.max_checkpoints + 10)

            if len(checkpoints) > self.max_checkpoints:
                # This would need database schema changes to support deletion
                # For now, just log the need for cleanup
                excess_count = len(checkpoints) - self.max_checkpoints
                self.logger.log_recovery_action(
                    f"Checkpoint cleanup needed: {excess_count} excess checkpoints for {project_id}",
                    True
                )

        except Exception as e:
            self.logger.log_error(e, operation="cleanup_checkpoints",
                                context={"project_id": project_id})

    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore data from a checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Restored data or None if checkpoint not found
        """
        try:
            data = self.db.restore_from_checkpoint(checkpoint_id)

            if data:
                self.logger.log_recovery_action(
                    f"Successfully restored from checkpoint {checkpoint_id}",
                    True
                )
            else:
                self.logger.log_recovery_action(
                    f"Failed to restore from checkpoint {checkpoint_id}",
                    False
                )

            return data

        except Exception as e:
            self.logger.log_error(e, operation="restore_checkpoint",
                                context={"checkpoint_id": checkpoint_id})
            return None

    def get_recovery_options(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get available recovery options for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of recovery options with metadata
        """
        try:
            checkpoints = self.db.get_recent_checkpoints(project_id, 10)

            recovery_options = []
            for checkpoint in checkpoints:
                recovery_options.append({
                    'type': 'checkpoint',
                    'id': checkpoint['checkpoint_id'],
                    'timestamp': checkpoint['created_at'],
                    'operation': checkpoint['operation'],
                    'data_size': checkpoint['data_size']
                })

            # Add option to restore from last known good state
            recovery_options.append({
                'type': 'last_good_state',
                'description': 'Restore from last successfully saved state'
            })

            return recovery_options

        except Exception as e:
            self.logger.log_error(e, operation="get_recovery_options",
                                context={"project_id": project_id})
            return []

    def mark_project_active(self, project_id: str):
        """
        Mark a project as active for auto-checkpointing.

        Args:
            project_id: Project identifier
        """
        with self.checkpoint_lock:
            self.active_projects[project_id] = time.time()

    def mark_project_inactive(self, project_id: str):
        """
        Mark a project as inactive (removes from auto-checkpointing).

        Args:
            project_id: Project identifier
        """
        with self.checkpoint_lock:
            self.active_projects.pop(project_id, None)

    def force_checkpoint_all_active(self):
        """Force immediate checkpoint for all active projects."""
        with self.checkpoint_lock:
            active_projects = list(self.active_projects.keys())

        for project_id in active_projects:
            try:
                project_data = self._get_project_data(project_id)
                if project_data:
                    self.create_checkpoint(
                        project_id,
                        project_data,
                        f"forced_{int(time.time())}",
                        "forced_save"
                    )
            except Exception as e:
                self.logger.log_error(e, operation="force_checkpoint",
                                    context={"project_id": project_id})

    def _get_project_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current project data. This should be overridden by subclasses.

        Args:
            project_id: Project identifier

        Returns:
            Current project data
        """
        # This is a placeholder - in a real implementation, this would
        # get the current state from the application
        return None

    def shutdown(self):
        """Shutdown the checkpoint system gracefully."""
        self.logger.log_recovery_action("Checkpoint system shutting down", True)

        # Stop auto-save thread
        self.stop_auto_save.set()
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            self.auto_save_thread.join(timeout=5.0)

        # Force final checkpoints for all active projects
        self.force_checkpoint_all_active()


class DataChangeTracker:
    """
    Tracks data changes to determine when checkpoints are needed.

    This class monitors data modifications and triggers checkpoints
    when significant changes occur.
    """

    def __init__(self, checkpoint_manager: CheckpointManager,
                 change_threshold: float = 0.1):
        """
        Initialize the data change tracker.

        Args:
            checkpoint_manager: Checkpoint manager instance
            change_threshold: Threshold for triggering checkpoints (0.1 = 10% change)
        """
        self.checkpoint_manager = checkpoint_manager
        self.change_threshold = change_threshold
        self.last_data_hash = None
        self.change_lock = threading.Lock()

    def track_change(self, project_id: str, new_data: Dict[str, Any],
                    force_checkpoint: bool = False):
        """
        Track a data change and potentially trigger a checkpoint.

        Args:
            project_id: Project identifier
            new_data: New data state
            force_checkpoint: Force checkpoint regardless of change threshold
        """
        with self.change_lock:
            current_hash = self._calculate_data_hash(new_data)

            if force_checkpoint or self._has_significant_change(current_hash):
                self.checkpoint_manager.create_checkpoint(
                    project_id,
                    new_data,
                    operation="data_change"
                )
                self.last_data_hash = current_hash

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate a simple hash of the data for change detection."""
        import hashlib
        import json

        # Create a normalized JSON string for consistent hashing
        normalized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _has_significant_change(self, new_hash: str) -> bool:
        """Determine if the change is significant enough for a checkpoint."""
        if self.last_data_hash is None:
            return True

        # Simple hash comparison - in a more sophisticated implementation,
        # you could calculate actual change percentage
        return new_hash != self.last_data_hash


# Decorators for checkpoint integration
def checkpoint_on_change(project_id_param: str = "project_id"):
    """
    Decorator that creates checkpoints when data changes significantly.

    Args:
        project_id_param: Parameter name containing the project ID
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get project ID from parameters
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            else:
                # Try to find it in positional args by inspecting function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if project_id_param in param_names:
                    idx = param_names.index(project_id_param)
                    if idx < len(args):
                        project_id = args[idx]

            result = func(*args, **kwargs)

            # Create checkpoint if we have project_id and result indicates data change
            if project_id and result is not None:
                try:
                    checkpoint_mgr = get_checkpoint_manager()
                    if hasattr(checkpoint_mgr, 'data_tracker'):
                        checkpoint_mgr.data_tracker.track_change(project_id, result)
                except Exception as e:
                    logger.log_error(e, operation="checkpoint_on_change")

            return result

        return wrapper
    return decorator


# Global checkpoint manager instance
_checkpoint_manager_instance = None
_checkpoint_manager_lock = threading.Lock()


def get_checkpoint_manager() -> CheckpointManager:
    """Get the global checkpoint manager instance."""
    global _checkpoint_manager_instance
    with _checkpoint_manager_lock:
        if _checkpoint_manager_instance is None:
            _checkpoint_manager_instance = CheckpointManager()
        return _checkpoint_manager_instance


# Convenience functions
def create_checkpoint(project_id: str, data: Dict[str, Any], **kwargs) -> bool:
    """Create a checkpoint for the given data."""
    return get_checkpoint_manager().create_checkpoint(project_id, data, **kwargs)


def get_recovery_options(project_id: str) -> List[Dict[str, Any]]:
    """Get recovery options for a project."""
    return get_checkpoint_manager().get_recovery_options(project_id)
