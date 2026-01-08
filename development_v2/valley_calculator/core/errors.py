# errors.py - Comprehensive error handling and recovery for Valley Calculator V2.0

import functools
import time
import threading
from typing import Callable, Any, Dict
from ..utils.logging.logger import get_logger


class CalculationError(Exception):
    """Base class for all calculation-related errors."""

    def __init__(
        self, message: str, error_code: str = None, context: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.error_code = error_code or "CALCULATION_ERROR"
        self.context = context or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": str(self),
            "context": self.context,
            "timestamp": self.timestamp,
        }


class ValidationError(CalculationError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None, value: Any = None, **context):
        super().__init__(
            message, "VALIDATION_ERROR", {"field": field, "value": value, **context}
        )
        self.field = field
        self.value = value


class ConvergenceError(CalculationError):
    """Raised when numerical calculations fail to converge."""

    def __init__(
        self, message: str, iterations: int = None, tolerance: float = None, **context
    ):
        super().__init__(
            message,
            "CONVERGENCE_ERROR",
            {"iterations": iterations, "tolerance": tolerance, **context},
        )
        self.iterations = iterations
        self.tolerance = tolerance


class GeometryError(CalculationError):
    """Raised when geometric calculations are invalid."""

    def __init__(self, message: str, geometry_params: Dict[str, Any] = None, **context):
        super().__init__(
            message, "GEOMETRY_ERROR", {"geometry_params": geometry_params, **context}
        )
        self.geometry_params = geometry_params or {}


class MaterialError(CalculationError):
    """Raised when material properties are invalid."""

    def __init__(
        self,
        message: str,
        material_name: str = None,
        property_name: str = None,
        **context,
    ):
        super().__init__(
            message,
            "MATERIAL_ERROR",
            {"material_name": material_name, "property_name": property_name, **context},
        )
        self.material_name = material_name
        self.property_name = property_name


class DatabaseError(CalculationError):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, operation: str = None, table: str = None, **context
    ):
        super().__init__(
            message,
            "DATABASE_ERROR",
            {"operation": operation, "table": table, **context},
        )
        self.operation = operation
        self.table = table


class ConfigurationError(CalculationError):
    """Raised when configuration is invalid."""

    def __init__(
        self, message: str, config_key: str = None, config_value: Any = None, **context
    ):
        super().__init__(
            message,
            "CONFIGURATION_ERROR",
            {"config_key": config_key, "config_value": config_value, **context},
        )
        self.config_key = config_key
        self.config_value = config_value


class RecoveryStrategy:
    """Base class for error recovery strategies."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description or f"Recovery strategy: {name}"

    def can_recover(self, error: Exception) -> bool:
        """Check if this strategy can recover from the given error."""
        raise NotImplementedError

    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from the error."""
        raise NotImplementedError


class RetryStrategy(RecoveryStrategy):
    """Retry operation with exponential backoff."""

    def __init__(
        self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
    ):
        super().__init__(
            "retry", f"Retry up to {max_attempts} times with exponential backoff"
        )
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def can_recover(self, error: Exception) -> bool:
        # Retry for transient errors
        return isinstance(error, (OSError, ConnectionError, TimeoutError))

    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Retry the operation with exponential backoff."""
        operation = context.get("operation")
        attempt = context.get("attempt", 0)

        if attempt >= self.max_attempts:
            raise error

        delay = min(self.base_delay * (2**attempt), self.max_delay)
        time.sleep(delay)

        # Return indication to retry
        return {"action": "retry", "delay": delay}


class FallbackStrategy(RecoveryStrategy):
    """Use fallback values or simplified calculations."""

    def __init__(self, fallback_values: Dict[str, Any] = None):
        super().__init__("fallback", "Use fallback values for failed calculations")
        self.fallback_values = fallback_values or {}

    def can_recover(self, error: Exception) -> bool:
        # Can recover from most calculation errors with fallbacks
        return isinstance(error, CalculationError)

    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Return fallback values."""
        return {"action": "fallback", "values": self.fallback_values}


class DegradationStrategy(RecoveryStrategy):
    """Degrade functionality gracefully."""

    def __init__(self):
        super().__init__("degrade", "Continue with reduced functionality")

    def can_recover(self, error: Exception) -> bool:
        # Can degrade for non-critical errors
        return isinstance(error, (ValidationError, GeometryError))

    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Continue with reduced functionality."""
        return {"action": "degrade", "warnings": [str(error)]}


class ErrorHandler:
    """
    Comprehensive error handling and recovery system.

    Features:
    - Multiple recovery strategies
    - Error classification and prioritization
    - Performance monitoring
    - Graceful degradation
    """

    def __init__(self):
        self.logger = get_logger()
        self.recovery_strategies = [
            RetryStrategy(),
            FallbackStrategy(),
            DegradationStrategy(),
        ]
        self.error_counts: Dict[str, int] = {}
        self._lock = threading.RLock()

    def handle_error(
        self,
        error: Exception,
        operation: str,
        context: Dict[str, Any] = None,
        recoverable: bool = True,
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate recovery strategy.

        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
            context: Additional context information
            recoverable: Whether the operation can be recovered

        Returns:
            Recovery result dictionary
        """
        context = context or {}
        context["operation"] = operation

        with self._lock:
            # Classify error
            error_type = self._classify_error(error)
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

            # Log error
            self.logger.log_error(error, operation=operation, context=context)

            if not recoverable:
                return {"action": "fail", "error": str(error)}

            # Try recovery strategies
            for strategy in self.recovery_strategies:
                if strategy.can_recover(error):
                    try:
                        recovery_result = strategy.recover(error, context)
                        self.logger.log_recovery_action(
                            f"Recovery attempted: {strategy.name}",
                            recovery_result.get("action") != "fail",
                            {"strategy": strategy.name, "operation": operation},
                        )
                        return recovery_result
                    except Exception as recovery_error:
                        self.logger.log_error(
                            recovery_error,
                            operation=f"{operation}_recovery",
                            context={"recovery_strategy": strategy.name},
                        )
                        continue

            # No recovery possible
            return {"action": "fail", "error": str(error)}

    def _classify_error(self, error: Exception) -> str:
        """Classify error by type."""
        if isinstance(error, ValidationError):
            return "validation"
        elif isinstance(error, ConvergenceError):
            return "convergence"
        elif isinstance(error, GeometryError):
            return "geometry"
        elif isinstance(error, MaterialError):
            return "material"
        elif isinstance(error, DatabaseError):
            return "database"
        elif isinstance(error, ConfigurationError):
            return "configuration"
        else:
            return "general"

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors for monitoring."""
        with self._lock:
            return {
                "total_errors": sum(self.error_counts.values()),
                "error_types": self.error_counts.copy(),
                "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])
                if self.error_counts
                else None,
            }


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Decorators for error handling


def resilient_operation(
    retries: int = 2, recoverable: bool = True, save_checkpoint: bool = False
):
    """
    Decorator for resilient operations with error recovery.

    Args:
        retries: Number of retry attempts
        recoverable: Whether operation can be recovered
        save_checkpoint: Whether to save checkpoint on success
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            operation_name = func.__name__

            for attempt in range(retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Log successful operation
                    if attempt > 0:
                        handler.logger.log_recovery_action(
                            f"Operation recovered on attempt {attempt + 1}",
                            True,
                            {"operation": operation_name, "attempts": attempt + 1},
                        )

                    if save_checkpoint:
                        # Would integrate with checkpoint system
                        pass

                    return result

                except Exception as e:
                    context = {
                        "attempt": attempt,
                        "max_attempts": retries + 1,
                        "function_args": len(args),
                        "function_kwargs": list(kwargs.keys()),
                    }

                    recovery_result = handler.handle_error(
                        e, operation_name, context, recoverable
                    )

                    if recovery_result["action"] == "retry" and attempt < retries:
                        delay = recovery_result.get("delay", 1.0)
                        time.sleep(delay)
                        continue
                    elif recovery_result["action"] == "fallback":
                        return recovery_result.get("values")
                    elif recovery_result["action"] == "degrade":
                        # Continue with warnings
                        handler.logger.log_recovery_action(
                            f"Operation degraded: {operation_name}",
                            True,
                            {"warnings": recovery_result.get("warnings", [])},
                        )
                        break
                    else:
                        # Final failure
                        raise e

            # If we get here, operation was allowed to degrade
            return None

        return wrapper

    return decorator


def error_boundary(operation_name: str, recoverable: bool = True):
    """
    Context manager for error boundaries.

    Args:
        operation_name: Name of the operation
        recoverable: Whether errors in this boundary can be recovered
    """
    return ErrorBoundary(operation_name, recoverable)


class ErrorBoundary:
    """Context manager for error boundaries."""

    def __init__(self, operation_name: str, recoverable: bool = True):
        self.operation_name = operation_name
        self.recoverable = recoverable
        self.handler = get_error_handler()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            recovery_result = self.handler.handle_error(
                exc_val, self.operation_name, recoverable=self.recoverable
            )

            # Don't suppress the exception unless recovery was successful
            if recovery_result["action"] in ["fallback", "degrade"]:
                return True  # Suppress exception

        return False  # Don't suppress exception


def validate_input(*validators):
    """
    Decorator for input validation.

    Args:
        *validators: Validation functions to apply to positional arguments (skips self for methods)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip 'self' parameter for instance methods
            start_idx = 1 if len(args) > 0 and hasattr(args[0], func.__name__) else 0

            # Apply validators to arguments (skipping self)
            for i, validator in enumerate(validators):
                arg_idx = start_idx + i
                if arg_idx < len(args):
                    try:
                        validator(args[arg_idx])
                    except Exception as e:
                        raise ValidationError(
                            f"Input validation failed for argument {arg_idx}: {str(e)}",
                            field=f"arg_{arg_idx}",
                            value=args[arg_idx],
                        ) from e

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_positive_number(value):
    """Validate that value is a positive number."""
    if not isinstance(value, (int, float)):
        raise ValidationError("Value must be a number", value=value)
    if value <= 0:
        raise ValidationError("Value must be positive", value=value)


def validate_range(min_val: float, max_val: float):
    """Create a range validator."""

    def validator(value):
        if not isinstance(value, (int, float)):
            raise ValidationError("Value must be a number", value=value)
        if not (min_val <= value <= max_val):
            raise ValidationError(
                f"Value must be between {min_val} and {max_val}",
                value=value,
                min_val=min_val,
                max_val=max_val,
            )

    return validator


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to function execution.

    Args:
        timeout_seconds: Maximum execution time in seconds
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)

            if thread.is_alive():
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds} seconds"
                )

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator
