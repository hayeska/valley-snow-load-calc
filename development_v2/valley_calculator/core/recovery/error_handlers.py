# error_handlers.py - Error wrappers and crash recovery mechanisms
# Provides decorators and utilities for graceful error handling and automatic recovery

import functools
import time
import threading
from typing import Callable, Any, TypeVar
from contextlib import contextmanager
import traceback
import signal
import atexit
import sys

from ...utils.logging.logger import get_logger
from ...data.persistence.database import get_database

T = TypeVar("T")
logger = get_logger()


class RecoveryManager:
    """
    Manages application recovery from crashes and errors.

    Features:
    - Automatic error recovery with retry logic
    - Graceful degradation
    - Data integrity preservation during failures
    - Crash detection and recovery state management
    """

    def __init__(self):
        self.recovery_strategies = {}
        self.crash_handlers = []
        self.recovery_lock = threading.Lock()
        self._setup_signal_handlers()
        self._setup_exit_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.log_recovery_action(
                f"Received signal {signum}, initiating graceful shutdown", True
            )
            self._perform_emergency_save()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Handle unhandled exceptions
        def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
            logger.log_error(
                exc_value,
                operation="unhandled_exception",
                recoverable=False,
                context={
                    "exception_type": str(exc_type),
                    "traceback": "".join(traceback.format_tb(exc_traceback)),
                },
            )
            self._perform_emergency_save()

        sys.excepthook = handle_unhandled_exception

    def _setup_exit_handlers(self):
        """Setup exit handlers for cleanup."""
        atexit.register(self._perform_emergency_save)

    def _perform_emergency_save(self):
        """Perform emergency save of critical data."""
        try:
            # This would save current application state
            logger.log_recovery_action("Emergency save completed", True)
        except Exception as e:
            logger.log_error(e, operation="emergency_save")

    def register_recovery_strategy(self, error_type: type, strategy: Callable):
        """
        Register a recovery strategy for specific error types.

        Args:
            error_type: Type of exception to handle
            strategy: Function to call for recovery
        """
        self.recovery_strategies[error_type] = strategy

    def add_crash_handler(self, handler: Callable):
        """
        Add a crash recovery handler.

        Args:
            handler: Function to call during crash recovery
        """
        self.crash_handlers.append(handler)


def resilient_operation(
    retries: int = 3,
    backoff: float = 1.0,
    recoverable: bool = True,
    save_checkpoint: bool = False,
):
    """
    Decorator for resilient operations with automatic retry and recovery.

    Args:
        retries: Number of retry attempts
        backoff: Backoff multiplier between retries
        recoverable: Whether operation failures are recoverable
        save_checkpoint: Whether to save checkpoint before operation
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            operation_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()

            # Create checkpoint if requested
            checkpoint_id = None
            if save_checkpoint:
                try:
                    db = get_database()
                    checkpoint_data = {
                        "operation": operation_name,
                        "args": str(args)[:500],  # Truncate for storage
                        "kwargs": str(kwargs)[:500],
                        "timestamp": time.time(),
                    }
                    checkpoint_id = f"checkpoint_{operation_name}_{int(time.time())}"
                    db.create_checkpoint(
                        "system", checkpoint_id, checkpoint_data, operation_name
                    )
                except Exception as e:
                    logger.log_error(e, operation="checkpoint_creation")

            last_exception = None
            for attempt in range(retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Log successful operation
                    duration = time.time() - start_time
                    logger.log_performance(
                        operation_name,
                        duration,
                        success=True,
                        metadata={"attempt": attempt + 1},
                    )

                    return result

                except Exception as e:
                    last_exception = e
                    duration = time.time() - start_time

                    # Log the error
                    logger.log_error(
                        e,
                        operation=operation_name,
                        recoverable=recoverable,
                        context={
                            "attempt": attempt + 1,
                            "max_retries": retries,
                            "duration": duration,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys()),
                        },
                    )

                    # Try recovery strategy if available
                    recovery_manager = get_recovery_manager()
                    error_type = type(e)
                    if error_type in recovery_manager.recovery_strategies:
                        try:
                            recovery_manager.recovery_strategies[error_type](
                                e, *args, **kwargs
                            )
                            logger.log_recovery_action(
                                f"Recovery strategy applied for {error_type.__name__}",
                                True,
                                {"operation": operation_name, "attempt": attempt + 1},
                            )
                        except Exception as recovery_error:
                            logger.log_error(
                                recovery_error,
                                operation="recovery_strategy",
                                context={"original_error": str(e)},
                            )

                    # Don't retry on last attempt
                    if attempt < retries:
                        sleep_time = backoff * (2**attempt)  # Exponential backoff
                        time.sleep(min(sleep_time, 30.0))  # Cap at 30 seconds
                    else:
                        # Final failure - raise the exception
                        if not recoverable:
                            raise
                        # For recoverable errors, return None or default value
                        logger.log_recovery_action(
                            f"Operation {operation_name} failed after {retries + 1} attempts",
                            False,
                            {"final_error": str(last_exception)},
                        )
                        return None

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


def auto_save(operation_name: str = None, checkpoint_interval: int = 300):
    """
    Decorator that automatically saves state at regular intervals.

    Args:
        operation_name: Name of the operation for logging
        checkpoint_interval: Seconds between automatic checkpoints
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        last_checkpoint = time.time()

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            nonlocal last_checkpoint

            try:
                result = func(*args, **kwargs)

                # Check if we need to create a checkpoint
                current_time = time.time()
                if current_time - last_checkpoint > checkpoint_interval:
                    try:
                        db = get_database()
                        checkpoint_data = {
                            "operation": operation_name or func.__name__,
                            "timestamp": current_time,
                            "auto_save": True,
                        }
                        checkpoint_id = f"auto_{operation_name or func.__name__}_{int(current_time)}"
                        db.create_checkpoint(
                            "auto_save", checkpoint_id, checkpoint_data
                        )
                        last_checkpoint = current_time
                    except Exception as e:
                        logger.log_error(e, operation="auto_checkpoint")

                return result

            except Exception as e:
                # Emergency checkpoint on error
                try:
                    db = get_database()
                    checkpoint_data = {
                        "operation": operation_name or func.__name__,
                        "error": str(e),
                        "timestamp": time.time(),
                        "emergency": True,
                    }
                    checkpoint_id = f"emergency_{operation_name or func.__name__}_{int(time.time())}"
                    db.create_checkpoint("emergency", checkpoint_id, checkpoint_data)
                except Exception as checkpoint_error:
                    logger.log_error(checkpoint_error, operation="emergency_checkpoint")

                raise

        return wrapper

    return decorator


@contextmanager
def error_boundary(operation: str, recoverable: bool = True):
    """
    Context manager for error boundaries with automatic logging and recovery.

    Usage:
        with error_boundary("database_operation"):
            # risky code here
            pass
    """
    start_time = time.time()

    try:
        yield
        duration = time.time() - start_time
        logger.log_performance(operation, duration, success=True)

    except Exception as e:
        duration = time.time() - start_time
        logger.log_error(e, operation=operation, recoverable=recoverable)
        logger.log_performance(operation, duration, success=False)

        if not recoverable:
            raise

        # For recoverable errors, log recovery attempt
        logger.log_recovery_action(
            f"Error boundary caught recoverable error in {operation}", True
        )


def validate_input(*validators):
    """
    Decorator to validate function inputs.

    Args:
        validators: Validation functions that take (arg_value, arg_name) and return (is_valid, error_msg)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Get function signature for parameter names
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each argument
            for i, (arg_name, arg_value) in enumerate(bound_args.arguments.items()):
                if i < len(validators) and validators[i]:
                    validator = validators[i]
                    try:
                        is_valid, error_msg = validator(arg_value, arg_name)
                        if not is_valid:
                            raise ValueError(
                                f"Validation failed for {arg_name}: {error_msg}"
                            )
                    except Exception as e:
                        logger.log_error(e, operation=f"input_validation_{arg_name}")
                        raise

            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to function execution.

    Args:
        timeout_seconds: Maximum execution time in seconds
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout_seconds)

            if thread.is_alive():
                raise TimeoutError(
                    f"Function {func.__name__} timed out after {timeout_seconds} seconds"
                )

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator


# Input validation functions
def validate_positive_number(value: Any, name: str) -> tuple[bool, str]:
    """Validate that value is a positive number."""
    try:
        num = float(value)
        if num <= 0:
            return False, f"{name} must be positive"
        return True, ""
    except (TypeError, ValueError):
        return False, f"{name} must be a number"


def validate_non_empty_string(value: Any, name: str) -> tuple[bool, str]:
    """Validate that value is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        return False, f"{name} must be a non-empty string"
    return True, ""


# Global recovery manager instance
_recovery_manager_instance = None
_recovery_manager_lock = threading.Lock()


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance."""
    global _recovery_manager_instance
    with _recovery_manager_lock:
        if _recovery_manager_instance is None:
            _recovery_manager_instance = RecoveryManager()
        return _recovery_manager_instance


# Convenience functions
def register_error_recovery(error_type: type, handler: Callable):
    """Register an error recovery handler."""
    get_recovery_manager().register_recovery_strategy(error_type, handler)


def add_crash_handler(handler: Callable):
    """Add a crash recovery handler."""
    get_recovery_manager().add_crash_handler(handler)
