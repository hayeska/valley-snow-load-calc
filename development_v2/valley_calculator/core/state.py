# state.py - Centralized state management for Valley Calculator V2.0

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
from ..utils.logging.logger import get_logger


@dataclass
class InputParameters:
    """Structured input parameters for snow load calculations."""

    # Snow load parameters
    ground_snow_load: float = 25.0  # pg (psf)
    winter_wind_parameter: float = 0.3  # W2
    importance_factor: float = 1.0  # Is
    exposure_factor: float = 1.0  # Ce
    thermal_factor: float = 1.0  # Ct

    # Roof geometry
    north_roof_pitch: float = 8.0  # rise/12
    west_roof_pitch: float = 8.0  # rise/12
    north_span: float = 16.0  # ft
    south_span: float = 16.0  # ft
    ew_half_width: float = 42.0  # ft
    valley_offset: float = 16.0  # ft
    valley_angle: float = 90.0  # degrees

    # Building parameters
    dead_load: float = 15.0  # psf
    beam_width: float = 3.5  # inches
    beam_depth: float = 9.5  # inches

    # Material properties
    modulus_e: float = 1600000.0  # psi
    fb_allowable: float = 1600.0  # psi
    fv_allowable: float = 125.0  # psi

    # Analysis options
    deflection_snow_limit: float = 240.0  # 1/240 for snow
    deflection_total_limit: float = 180.0  # 1/180 for total
    jack_spacing_inches: float = 24.0
    slippery_roof: bool = False
    warm_roof: bool = False


@dataclass
class CalculationResults:
    """Structured calculation results."""

    # Core result sections
    inputs: Dict[str, Any] = field(default_factory=dict)
    slope_parameters: Dict[str, Any] = field(default_factory=dict)
    geometry: Dict[str, Any] = field(default_factory=dict)
    snow_loads: Dict[str, Any] = field(default_factory=dict)
    beam_analysis: Dict[str, Any] = field(default_factory=dict)
    diagrams: Dict[str, Any] = field(default_factory=dict)

    # Analysis type and metadata
    analysis_type: str = ""
    status: str = "not_calculated"
    timestamp: Optional[str] = None
    asce_reference: str = "ASCE 7-22"
    calculation_engine_version: str = "2.0.0"

    # Legacy fields for backward compatibility
    pf_flat: float = 0.0  # psf
    ps_balanced: float = 0.0  # psf
    pm_minimum: float = 0.0  # psf
    valley_geometry: Dict[str, Any] = field(default_factory=dict)
    north_drift: Dict[str, Any] = field(default_factory=dict)
    west_drift: Dict[str, Any] = field(default_factory=dict)
    valley_drift: Dict[str, Any] = field(default_factory=dict)
    calculation_time: float = 0.0


@dataclass
class ProjectMetadata:
    """Project metadata and management information."""

    project_id: Optional[str] = None
    project_name: str = "Unnamed Project"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: str = "2.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    author: str = ""
    company: str = ""


@dataclass
class UIState:
    """UI state management."""

    current_tab: str = "inputs"
    calculation_in_progress: bool = False
    last_calculation_duration: float = 0.0
    status_message: str = "Ready"
    error_messages: List[str] = field(default_factory=list)
    theme: str = "default"
    show_advanced: bool = False
    auto_save_enabled: bool = True


class StateManager:
    """
    Centralized state management system for the Valley Calculator.

    Features:
    - Atomic state updates with validation
    - State change notifications
    - State persistence and restoration
    - Thread-safe operations
    - State change history for undo/redo
    """

    def __init__(self):
        self.logger = get_logger()

        # Core state components
        self.inputs = InputParameters()
        self.results = CalculationResults()
        self.project = ProjectMetadata()
        self.ui_state = UIState()

        # State management
        self._lock = threading.RLock()
        self._listeners: Dict[str, List[Callable]] = {}
        self._state_history: List[Dict[str, Any]] = []
        self._max_history = 50
        self._auto_save_interval = 120  # seconds
        self._last_auto_save = time.time()

        # Initialize state
        self._initialize_state()

    def _initialize_state(self):
        """Initialize default state values."""
        self.project.created_at = datetime.now().isoformat()
        self.project.updated_at = datetime.now().isoformat()
        self.logger.log_recovery_action("State manager initialized", True)

    def update_inputs(self, **kwargs) -> bool:
        """
        Update input parameters with validation.

        Args:
            **kwargs: Input parameter updates

        Returns:
            True if update was successful
        """
        with self._lock:
            try:
                # Save current state for undo
                self._save_to_history()

                # Validate inputs before updating
                if not self._validate_inputs(kwargs):
                    return False

                # Update parameters
                for key, value in kwargs.items():
                    if hasattr(self.inputs, key):
                        setattr(self.inputs, key, value)

                # Mark project as modified
                self.project.updated_at = datetime.now().isoformat()

                # Notify listeners
                self._notify_listeners("inputs_updated", kwargs)

                # Trigger auto-save if needed
                self._check_auto_save()

                self.logger.log_recovery_action(
                    f"Input parameters updated: {list(kwargs.keys())}", True
                )
                return True

            except Exception as e:
                self.logger.log_error(e, operation="update_inputs")
                return False

    def update_results(self, results: CalculationResults) -> bool:
        """
        Update calculation results.

        Args:
            results: New calculation results

        Returns:
            True if update was successful
        """
        with self._lock:
            try:
                # Save current state for undo
                self._save_to_history()

                # Update results
                self.results = results
                self.results.timestamp = datetime.now().isoformat()

                # Update UI state
                self.ui_state.calculation_in_progress = False
                self.ui_state.status_message = "Calculation completed"

                # Mark project as modified
                self.project.updated_at = datetime.now().isoformat()

                # Notify listeners
                self._notify_listeners("results_updated", results)

                # Trigger auto-save
                self._check_auto_save()

                self.logger.log_recovery_action("Calculation results updated", True)
                return True

            except Exception as e:
                self.logger.log_error(e, operation="update_results")
                return False

    def update_project_metadata(self, **kwargs) -> bool:
        """
        Update project metadata.

        Args:
            **kwargs: Project metadata updates

        Returns:
            True if update was successful
        """
        with self._lock:
            try:
                # Update metadata
                for key, value in kwargs.items():
                    if hasattr(self.project, key):
                        setattr(self.project, key, value)

                self.project.updated_at = datetime.now().isoformat()

                # Notify listeners
                self._notify_listeners("project_updated", kwargs)

                self.logger.log_recovery_action(
                    f"Project metadata updated: {list(kwargs.keys())}", True
                )
                return True

            except Exception as e:
                self.logger.log_error(e, operation="update_project_metadata")
                return False

    def update_ui_state(self, **kwargs) -> bool:
        """
        Update UI state.

        Args:
            **kwargs: UI state updates

        Returns:
            True if update was successful
        """
        with self._lock:
            try:
                for key, value in kwargs.items():
                    if hasattr(self.ui_state, key):
                        setattr(self.ui_state, key, value)

                # Notify listeners
                self._notify_listeners("ui_updated", kwargs)

                return True

            except Exception as e:
                self.logger.log_error(e, operation="update_ui_state")
                return False

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get complete current state snapshot.

        Returns:
            Dictionary containing all state components
        """
        with self._lock:
            return {
                "inputs": self._dataclass_to_dict(self.inputs),
                "results": self._dataclass_to_dict(self.results),
                "project": self._dataclass_to_dict(self.project),
                "ui_state": self._dataclass_to_dict(self.ui_state),
                "timestamp": datetime.now().isoformat(),
            }

    def restore_state(self, state_dict: Dict[str, Any]) -> bool:
        """
        Restore state from dictionary.

        Args:
            state_dict: State dictionary to restore from

        Returns:
            True if restoration was successful
        """
        with self._lock:
            try:
                # Save current state for undo
                self._save_to_history()

                # Restore each component
                if "inputs" in state_dict:
                    self._dict_to_dataclass(state_dict["inputs"], self.inputs)
                if "results" in state_dict:
                    self._dict_to_dataclass(state_dict["results"], self.results)
                if "project" in state_dict:
                    self._dict_to_dataclass(state_dict["project"], self.project)
                if "ui_state" in state_dict:
                    self._dict_to_dataclass(state_dict["ui_state"], self.ui_state)

                # Notify listeners
                self._notify_listeners("state_restored", state_dict)

                self.logger.log_recovery_action("State restored from dictionary", True)
                return True

            except Exception as e:
                self.logger.log_error(e, operation="restore_state")
                return False

    def undo_last_change(self) -> bool:
        """
        Undo the last state change.

        Returns:
            True if undo was successful
        """
        with self._lock:
            try:
                if not self._state_history:
                    return False

                # Get last state
                previous_state = self._state_history.pop()

                # Restore it
                return self.restore_state(previous_state)

            except Exception as e:
                self.logger.log_error(e, operation="undo_last_change")
                return False

    def add_state_listener(self, event_type: str, callback: Callable):
        """
        Add a state change listener.

        Args:
            event_type: Type of event to listen for
            callback: Callback function to invoke
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def remove_state_listener(self, event_type: str, callback: Callable):
        """
        Remove a state change listener.

        Args:
            event_type: Type of event to stop listening for
            callback: Callback function to remove
        """
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)

    def _validate_inputs(self, inputs_dict: Dict[str, Any]) -> bool:
        """
        Validate input parameters.

        Args:
            inputs_dict: Input parameters to validate

        Returns:
            True if all inputs are valid
        """
        try:
            # Basic validation rules
            validations = {
                "ground_snow_load": lambda x: x > 0,
                "winter_wind_parameter": lambda x: 0.25 <= x <= 0.65,
                "importance_factor": lambda x: 0.8 <= x <= 1.6,
                "exposure_factor": lambda x: 0.7 <= x <= 1.2,
                "thermal_factor": lambda x: 1.0 <= x <= 1.3,
                "north_roof_pitch": lambda x: 0 <= x <= 24,
                "west_roof_pitch": lambda x: 0 <= x <= 24,
                "north_span": lambda x: x > 0,
                "south_span": lambda x: x > 0,
                "ew_half_width": lambda x: x > 0,
                "dead_load": lambda x: x >= 0,
                "beam_width": lambda x: x > 0,
                "beam_depth": lambda x: x > 0,
                "modulus_e": lambda x: x > 0,
                "fb_allowable": lambda x: x > 0,
                "fv_allowable": lambda x: x > 0,
            }

            errors = []
            for param, validator in validations.items():
                if param in inputs_dict:
                    if not validator(inputs_dict[param]):
                        errors.append(
                            f"Invalid value for {param}: {inputs_dict[param]}"
                        )

            if errors:
                self.ui_state.error_messages.extend(errors)
                return False

            return True

        except Exception as e:
            self.logger.log_error(e, operation="validate_inputs")
            return False

    def _save_to_history(self):
        """Save current state to history for undo functionality."""
        try:
            state_snapshot = self.get_current_state()
            self._state_history.append(state_snapshot)

            # Limit history size
            if len(self._state_history) > self._max_history:
                self._state_history.pop(0)

        except Exception as e:
            self.logger.log_error(e, operation="save_to_history")

    def _check_auto_save(self):
        """Check if auto-save should be triggered."""
        if self.ui_state.auto_save_enabled:
            current_time = time.time()
            if current_time - self._last_auto_save >= self._auto_save_interval:
                self._trigger_auto_save()
                self._last_auto_save = current_time

    def _trigger_auto_save(self):
        """Trigger auto-save of current state."""
        try:
            # This would integrate with the project manager
            # For now, just log the event
            self.logger.log_recovery_action("Auto-save triggered", True)
        except Exception as e:
            self.logger.log_error(e, operation="trigger_auto_save")

    def _notify_listeners(self, event_type: str, data: Any):
        """Notify listeners of state changes."""
        try:
            if event_type in self._listeners:
                for callback in self._listeners[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.log_error(
                            e, operation=f"notify_listener_{event_type}"
                        )
        except Exception as e:
            self.logger.log_error(e, operation="notify_listeners")

    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return {
            field.name: getattr(obj, field.name)
            for field in obj.__dataclass_fields__.values()
        }

    def _dict_to_dataclass(self, data: Dict[str, Any], obj):
        """Update dataclass from dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current state for status display.

        Returns:
            Dictionary with state summary
        """
        with self._lock:
            return {
                "project_name": self.project.project_name,
                "has_results": self.results.status == "completed",
                "last_updated": self.project.updated_at,
                "calculation_status": self.results.status,
                "ui_status": self.ui_state.status_message,
                "error_count": len(self.ui_state.error_messages),
            }
