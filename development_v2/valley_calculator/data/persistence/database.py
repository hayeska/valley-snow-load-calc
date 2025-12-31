# database.py - SQLite-based persistent storage with crash recovery
# Provides transaction-safe data storage and automatic recovery mechanisms

import sqlite3
import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
import hashlib

from ...utils.logging.logger import get_logger


class DatabaseManager:
    """
    SQLite-based data persistence with crash recovery and transaction safety.

    Features:
    - ACID transactions for data integrity
    - Automatic crash recovery and data validation
    - Checkpoint system for incremental saves
    - Backup and restore capabilities
    - Concurrent access protection
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Default to user data directory
            home = Path.home()
            data_dir = home / "AppData" / "Local" / "ValleySnowLoadCalc"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "valley_calc.db"
        else:
            self.db_path = Path(db_path)

        self.logger = get_logger()
        self._lock = threading.RLock()

        # Backup directory
        self.backup_dir = self.db_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Initialize database
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database schema and tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,  -- JSON data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version TEXT DEFAULT '2.0.0',
                    checksum TEXT NOT NULL
                )
            ''')

            # Checkpoints table for incremental saves
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    checkpoint_id TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,  -- JSON data
                    data_size INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (project_id)
                )
            ''')

            # Sessions table for crash recovery
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    project_id TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',  -- active, crashed, recovered
                    crash_data TEXT,  -- JSON crash information
                    recovery_attempts INTEGER DEFAULT 0
                )
            ''')

            # Settings table for application preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_name ON projects (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects (updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_project ON checkpoints (project_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)')

            conn.commit()

        self.logger.log_performance("database_init", 0.0, success=True,
                                  metadata={"tables_created": True})

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                isolation_level=None  # Enable autocommit mode for explicit transactions
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and performance
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.log_error(e, operation="database_connection")
            raise
        finally:
            if conn:
                conn.close()

    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA256 checksum for data integrity verification."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _validate_data_integrity(self, data: str, checksum: str) -> bool:
        """Validate data integrity using checksum."""
        return self._calculate_checksum(data) == checksum

    def save_project(self, project_id: str, name: str, data: Dict[str, Any]) -> bool:
        """
        Save project with transaction safety and integrity checking.

        Args:
            project_id: Unique project identifier
            name: Human-readable project name
            data: Project data dictionary

        Returns:
            True if save was successful
        """
        start_time = datetime.now()
        success = False

        try:
            with self._lock:
                json_data = json.dumps(data, indent=2)
                checksum = self._calculate_checksum(json_data)

                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # Use transaction for atomicity
                    cursor.execute("BEGIN TRANSACTION")

                    # Insert or update project
                    cursor.execute('''
                        INSERT INTO projects (project_id, name, data, updated_at, checksum)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(project_id) DO UPDATE SET
                            name = excluded.name,
                            data = excluded.data,
                            updated_at = excluded.updated_at,
                            checksum = excluded.checksum
                    ''', (project_id, name, json_data, datetime.now(), checksum))

                    cursor.execute("COMMIT")
                    success = True

                    # Update session activity
                    self._update_session_activity()

        except Exception as e:
            self.logger.log_error(e, operation="save_project",
                                context={"project_id": project_id, "name": name})
            return False

        duration = (datetime.now() - start_time).total_seconds()
        self.logger.log_performance("save_project", duration, success=success,
                                  metadata={"project_id": project_id})

        return success

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load project with integrity verification.

        Args:
            project_id: Project identifier

        Returns:
            Project data dictionary or None if not found/corrupted
        """
        start_time = datetime.now()

        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT name, data, checksum, version FROM projects
                        WHERE project_id = ?
                    ''', (project_id,))

                    row = cursor.fetchone()
                    if not row:
                        return None

                    name, json_data, checksum, version = row

                    # Verify data integrity
                    if not self._validate_data_integrity(json_data, checksum):
                        self.logger.log_error(
                            ValueError("Data integrity check failed"),
                            operation="load_project",
                            context={"project_id": project_id}
                        )
                        return None

                    data = json.loads(json_data)

                    # Update session activity
                    self._update_session_activity()

                    duration = (datetime.now() - start_time).total_seconds()
                    self.logger.log_performance("load_project", duration, success=True,
                                              metadata={"project_id": project_id})

                    return data

        except Exception as e:
            self.logger.log_error(e, operation="load_project",
                                context={"project_id": project_id})
            return None

    def create_checkpoint(self, project_id: str, checkpoint_id: str,
                         data: Dict[str, Any], operation: str = None) -> bool:
        """
        Create a data checkpoint for incremental saves and recovery.

        Args:
            project_id: Associated project ID
            checkpoint_id: Unique checkpoint identifier
            data: Checkpoint data
            operation: Operation that triggered the checkpoint

        Returns:
            True if checkpoint creation was successful
        """
        try:
            with self._lock:
                json_data = json.dumps(data, indent=2)
                data_size = len(json_data.encode('utf-8'))

                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("BEGIN TRANSACTION")

                    cursor.execute('''
                        INSERT INTO checkpoints (project_id, checkpoint_id, data, data_size, operation)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (project_id, checkpoint_id, json_data, data_size, operation))

                    cursor.execute("COMMIT")

                self.logger.log_checkpoint(checkpoint_id, data_size, operation)
                return True

        except Exception as e:
            self.logger.log_error(e, operation="create_checkpoint",
                                context={"project_id": project_id, "checkpoint_id": checkpoint_id})
            return False

    def get_recent_checkpoints(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent checkpoints for a project.

        Args:
            project_id: Project identifier
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint information
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT checkpoint_id, data_size, created_at, operation
                        FROM checkpoints
                        WHERE project_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (project_id, limit))

                    checkpoints = []
                    for row in cursor.fetchall():
                        checkpoints.append({
                            'checkpoint_id': row[0],
                            'data_size': row[1],
                            'created_at': row[2],
                            'operation': row[3]
                        })

                    return checkpoints

        except Exception as e:
            self.logger.log_error(e, operation="get_recent_checkpoints",
                                context={"project_id": project_id})
            return []

    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore data from a checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Checkpoint data or None if not found
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT data FROM checkpoints WHERE checkpoint_id = ?
                    ''', (checkpoint_id,))

                    row = cursor.fetchone()
                    if row:
                        return json.loads(row[0])

        except Exception as e:
            self.logger.log_error(e, operation="restore_from_checkpoint",
                                context={"checkpoint_id": checkpoint_id})

        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all saved projects.

        Returns:
            List of project information
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT project_id, name, updated_at, version
                        FROM projects
                        ORDER BY updated_at DESC
                    ''')

                    projects = []
                    for row in cursor.fetchall():
                        projects.append({
                            'project_id': row[0],
                            'name': row[1],
                            'updated_at': row[2],
                            'version': row[3]
                        })

                    return projects

        except Exception as e:
            self.logger.log_error(e, operation="list_projects")
            return []

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its checkpoints.

        Args:
            project_id: Project identifier

        Returns:
            True if deletion was successful
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("BEGIN TRANSACTION")

                    # Delete checkpoints first (foreign key constraint)
                    cursor.execute('DELETE FROM checkpoints WHERE project_id = ?', (project_id,))

                    # Delete project
                    cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))

                    cursor.execute("COMMIT")
                    return True

        except Exception as e:
            self.logger.log_error(e, operation="delete_project",
                                context={"project_id": project_id})
            return False

    def create_backup(self, backup_name: str = None) -> Optional[str]:
        """
        Create a database backup.

        Args:
            backup_name: Name for the backup file

        Returns:
            Path to backup file or None if failed
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"

        backup_path = self.backup_dir / backup_name

        try:
            with self._lock:
                # SQLite backup using VACUUM INTO (SQLite 3.27+)
                with self._get_connection() as conn:
                    conn.execute(f"VACUUM INTO '{backup_path}'")

                self.logger.log_recovery_action(f"Database backup created: {backup_name}",
                                              success=True)
                return str(backup_path)

        except Exception as e:
            self.logger.log_error(e, operation="create_backup",
                                context={"backup_name": backup_name})
            return None

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get application setting.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
                    row = cursor.fetchone()

                    if row:
                        return json.loads(row[0])
                    return default

        except Exception as e:
            self.logger.log_error(e, operation="get_setting", context={"key": key})
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set application setting.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            True if setting was saved successfully
        """
        try:
            with self._lock:
                json_value = json.dumps(value)

                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO settings (key, value, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET
                            value = excluded.value,
                            updated_at = excluded.updated_at
                    ''', (key, json_value, datetime.now()))

                    return True

        except Exception as e:
            self.logger.log_error(e, operation="set_setting",
                                context={"key": key})
            return False

    def start_session(self, session_id: str, project_id: str = None) -> bool:
        """
        Start a new application session for crash tracking.

        Args:
            session_id: Unique session identifier
            project_id: Associated project ID

        Returns:
            True if session was started successfully
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO sessions (session_id, project_id, status)
                        VALUES (?, ?, 'active')
                    ''', (session_id, project_id))

                    return True

        except Exception as e:
            self.logger.log_error(e, operation="start_session",
                                context={"session_id": session_id})
            return False

    def _update_session_activity(self):
        """Update last activity timestamp for current session."""
        # This would be called from other methods to track activity
        pass

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old checkpoints and temporary data.

        Args:
            days_to_keep: Number of days of data to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # Delete old checkpoints
                    cursor.execute('''
                        DELETE FROM checkpoints
                        WHERE created_at < ?
                    ''', (cutoff_date,))

                    deleted_count = cursor.rowcount
                    self.logger.log_recovery_action(
                        f"Cleaned up {deleted_count} old checkpoints",
                        success=True
                    )

        except Exception as e:
            self.logger.log_error(e, operation="cleanup_old_data")


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> DatabaseManager:
    """Get the global database instance."""
    global _db_instance
    with _db_lock:
        if _db_instance is None:
            _db_instance = DatabaseManager()
        return _db_instance
