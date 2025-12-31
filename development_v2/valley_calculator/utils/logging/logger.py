# logger.py - Comprehensive logging system for Valley Snow Load Calculator
# Provides error tracking, performance monitoring, and crash recovery logging

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import threading
import traceback


class ResilienceLogger:
    """
    Comprehensive logging system with error recovery and performance monitoring.

    Features:
    - Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Rotating file handlers to prevent log file bloat
    - Performance monitoring and timing
    - Crash recovery logging
    - Error context and stack traces
    - Log archiving and cleanup
    """

    def __init__(
        self,
        log_dir: str = None,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        """
        Initialize the resilient logging system.

        Args:
            log_dir: Directory for log files (defaults to user data directory)
            max_file_size: Maximum size of each log file in bytes
            backup_count: Number of backup log files to keep
        """
        if log_dir is None:
            # Default to user data directory
            home = Path.home()
            self.log_dir = home / "AppData" / "Local" / "ValleySnowLoadCalc" / "logs"
        else:
            self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Create loggers
        self._setup_loggers()

        # Performance monitoring
        self.performance_data = {}
        self._performance_lock = threading.Lock()

        # Recovery tracking
        self.recovery_log_file = self.log_dir / "recovery_log.json"
        self._recovery_lock = threading.Lock()

        # Initialize recovery log if it doesn't exist
        if not self.recovery_log_file.exists():
            self._initialize_recovery_log()

    def _setup_loggers(self):
        """Setup multiple loggers for different purposes."""
        # Main application logger
        self.main_logger = self._create_logger(
            "valley_calc", self.log_dir / "valley_calculator.log", logging.DEBUG
        )

        # Error logger (for critical errors only)
        self.error_logger = self._create_logger(
            "valley_error", self.log_dir / "errors.log", logging.WARNING
        )

        # Performance logger
        self.performance_logger = self._create_logger(
            "valley_perf", self.log_dir / "performance.log", logging.INFO
        )

        # Recovery logger
        self.recovery_logger = self._create_logger(
            "valley_recovery", self.log_dir / "recovery.log", logging.INFO
        )

    def _create_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """Create a configured logger with rotating file handler."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Also log to console for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        operation: str = None,
        recoverable: bool = True,
    ):
        """
        Log an error with full context and stack trace.

        Args:
            error: The exception that occurred
            context: Additional context information
            operation: The operation being performed when error occurred
            recoverable: Whether this error is recoverable
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "operation": operation,
            "recoverable": recoverable,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "thread_id": threading.get_ident(),
        }

        # Log to error logger
        error_msg = f"Error in {operation or 'unknown operation'}: {error}"
        if recoverable:
            self.error_logger.warning(error_msg)
        else:
            self.error_logger.error(error_msg)

        # Log full details to main logger
        self.main_logger.error(f"Error details: {json.dumps(error_info, indent=2)}")

        # Add to recovery log for crash analysis
        self._log_to_recovery(error_info)

    def log_performance(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Dict[str, Any] = None,
    ):
        """
        Log performance metrics.

        Args:
            operation: Name of the operation
            duration: Time taken in seconds
            success: Whether the operation completed successfully
            metadata: Additional performance metadata
        """
        perf_data = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        # Store in memory for analysis
        with self._performance_lock:
            if operation not in self.performance_data:
                self.performance_data[operation] = []
            self.performance_data[operation].append(perf_data)

            # Keep only last 100 entries per operation
            if len(self.performance_data[operation]) > 100:
                self.performance_data[operation] = self.performance_data[operation][
                    -100:
                ]

        # Log to performance logger
        status = "SUCCESS" if success else "FAILED"
        self.performance_logger.info(f"{operation}: {duration:.3f}s ({status})")

    def log_recovery_action(
        self, action: str, success: bool, details: Dict[str, Any] = None
    ):
        """
        Log recovery actions taken by the system.

        Args:
            action: Description of recovery action
            success: Whether recovery was successful
            details: Additional recovery details
        """
        recovery_info = {
            "action": action,
            "success": success,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }

        status = "SUCCESS" if success else "FAILED"
        self.recovery_logger.info(f"Recovery {status}: {action}")

        # Add to recovery log
        self._log_to_recovery(recovery_info)

    def log_checkpoint(self, checkpoint_id: str, data_size: int, operation: str = None):
        """
        Log data checkpoint creation.

        Args:
            checkpoint_id: Unique identifier for the checkpoint
            data_size: Size of checkpointed data in bytes
            operation: Operation that triggered the checkpoint
        """
        checkpoint_info = {
            "checkpoint_id": checkpoint_id,
            "data_size": data_size,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        }

        self.main_logger.info(
            f"Checkpoint created: {checkpoint_id} ({data_size} bytes)"
        )

        # Add to recovery log
        self._log_to_recovery(checkpoint_info)

    def _initialize_recovery_log(self):
        """Initialize the recovery log file."""
        initial_data = {
            "version": "2.0.0",
            "created_at": datetime.now().isoformat(),
            "last_crash": None,
            "recovery_history": [],
            "error_patterns": {},
            "performance_stats": {},
        }

        with self._recovery_lock:
            with open(self.recovery_log_file, "w") as f:
                json.dump(initial_data, f, indent=2)

    def _log_to_recovery(self, data: Dict[str, Any]):
        """Add entry to recovery log for crash analysis."""
        try:
            with self._recovery_lock:
                # Read existing recovery log
                with open(self.recovery_log_file, "r") as f:
                    recovery_data = json.load(f)

                # Add new entry
                if "entries" not in recovery_data:
                    recovery_data["entries"] = []

                recovery_data["entries"].append(data)

                # Keep only last 1000 entries
                if len(recovery_data["entries"]) > 1000:
                    recovery_data["entries"] = recovery_data["entries"][-1000:]

                # Update last activity
                recovery_data["last_activity"] = datetime.now().isoformat()

                # Write back
                with open(self.recovery_log_file, "w") as f:
                    json.dump(recovery_data, f, indent=2)

        except Exception as e:
            # If recovery logging fails, log to main logger
            self.main_logger.error(f"Failed to write to recovery log: {e}")

    def get_performance_stats(self, operation: str = None) -> Dict[str, Any]:
        """
        Get performance statistics.

        Args:
            operation: Specific operation to get stats for, or None for all

        Returns:
            Dictionary with performance statistics
        """
        with self._performance_lock:
            if operation:
                if operation in self.performance_data:
                    data = self.performance_data[operation]
                    if data:
                        durations = [d["duration"] for d in data]
                        return {
                            "operation": operation,
                            "count": len(data),
                            "avg_duration": sum(durations) / len(durations),
                            "min_duration": min(durations),
                            "max_duration": max(durations),
                            "success_rate": sum(1 for d in data if d["success"])
                            / len(data),
                        }
                return {}
            else:
                # Return stats for all operations
                stats = {}
                for op, data in self.performance_data.items():
                    if data:
                        durations = [d["duration"] for d in data]
                        stats[op] = {
                            "count": len(data),
                            "avg_duration": sum(durations) / len(durations),
                            "success_rate": sum(1 for d in data if d["success"])
                            / len(data),
                        }
                return stats

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files.

        Args:
            days_to_keep: Number of days of logs to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    log_file.unlink()
                    self.main_logger.info(f"Cleaned up old log file: {log_file}")
                except Exception as e:
                    self.error_logger.error(
                        f"Failed to clean up log file {log_file}: {e}"
                    )

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent errors for crash analysis.

        Returns:
            Dictionary with error summary
        """
        try:
            with self._recovery_lock:
                with open(self.recovery_log_file, "r") as f:
                    recovery_data = json.load(f)

            entries = recovery_data.get("entries", [])
            recent_errors = [e for e in entries if e.get("error_type")]

            error_counts = {}
            for error in recent_errors[-100:]:  # Last 100 errors
                error_type = error.get("error_type", "Unknown")
                if error_type not in error_counts:
                    error_counts[error_type] = 0
                error_counts[error_type] += 1

            return {
                "total_errors": len(recent_errors),
                "error_types": error_counts,
                "most_common_error": max(error_counts.items(), key=lambda x: x[1])
                if error_counts
                else None,
                "last_error": recent_errors[-1] if recent_errors else None,
            }

        except Exception as e:
            self.error_logger.error(f"Failed to get error summary: {e}")
            return {}


# Global logger instance
_logger_instance = None
_logger_lock = threading.Lock()


def get_logger() -> ResilienceLogger:
    """Get the global logger instance."""
    global _logger_instance
    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = ResilienceLogger()
        return _logger_instance


# Convenience functions for easy logging
def log_error(error: Exception, **kwargs):
    """Log an error."""
    get_logger().log_error(error, **kwargs)


def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics."""
    get_logger().log_performance(operation, duration, **kwargs)


def log_recovery_action(action: str, success: bool, **kwargs):
    """Log recovery actions."""
    get_logger().log_recovery_action(action, success, **kwargs)
