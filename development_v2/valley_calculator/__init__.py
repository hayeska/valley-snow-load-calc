# Valley Snow Load Calculator V2.0
# Professional ASCE 7-22 Compliant Engineering Software with Resilience Features

__version__ = "2.0.0"
__author__ = "Valley Snow Load Calculator Development Team"
__description__ = "Complete ASCE 7-22 snow load analysis for valley roof intersections with crash recovery and data integrity"

# Import key classes for easy access
from .core.calculator import ValleyCalculator
from .core.project import ProjectManager
from .gui.main_window import MainWindow

# Import resilience utilities for advanced users
from .utils.logging.logger import get_logger
from .data.persistence.database import get_database
from .core.recovery.error_handlers import (
    resilient_operation, error_boundary, validate_input,
    get_recovery_manager, register_error_recovery
)
from .core.recovery.checkpoint_system import get_checkpoint_manager

def create_application():
    """Factory function to create the resilient main application."""
    try:
        calculator = ValleyCalculator()
        project_manager = ProjectManager()
        app = MainWindow(calculator, project_manager)

        # Log successful application creation
        logger = get_logger()
        logger.log_recovery_action("Application created successfully", True)

        return app

    except Exception as e:
        # If application creation fails, log the error
        logger = get_logger()
        logger.log_error(e, operation="create_application", recoverable=False)
        raise
