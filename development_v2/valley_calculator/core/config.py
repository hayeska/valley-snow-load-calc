# config.py - Centralized configuration management for Valley Calculator V2.0

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from ..utils.logging.logger import get_logger


@dataclass
class CalculationConfig:
    """Configuration for calculation engine."""

    # Timeouts and limits
    calculation_timeout: float = 30.0  # seconds
    max_iterations: int = 1000
    convergence_tolerance: float = 1e-6

    # ASCE 7-22 constants
    max_upwind_fetch: float = 500.0  # ft
    snow_density_range: tuple = (14.0, 30.0)  # pcf
    min_ground_snow_load: float = 0.0  # psf
    max_ground_snow_load: float = 500.0  # psf

    # Validation limits
    min_roof_pitch: float = 0.0  # rise/12
    max_roof_pitch: float = 24.0  # rise/12
    min_valley_angle: float = 60.0  # degrees
    max_valley_angle: float = 120.0  # degrees

    # Default material properties
    default_modulus_e: float = 1600000.0  # psi (Douglas Fir)
    default_fb_allowable: float = 1600.0  # psi
    default_fv_allowable: float = 125.0  # psi


@dataclass
class UIConfig:
    """Configuration for user interface."""

    # Window settings
    default_width: int = 1200
    default_height: int = 800
    min_width: int = 1000
    min_height: int = 700

    # Themes
    default_theme: str = "default"
    available_themes: list = field(default_factory=lambda: ["default", "dark", "light"])

    # Auto-save settings
    auto_save_enabled: bool = True
    auto_save_interval: int = 120  # seconds
    max_recent_projects: int = 10

    # Performance settings
    enable_animations: bool = True
    max_chart_points: int = 1000
    chart_update_interval: float = 0.1  # seconds


@dataclass
class PersistenceConfig:
    """Configuration for data persistence."""

    # Database settings
    database_path: Optional[str] = None
    backup_on_save: bool = True
    max_backup_files: int = 50

    # Project directories
    projects_dir_name: str = "Valley Snow Load Projects"
    templates_dir_name: str = "templates"
    backups_dir_name: str = "backups"

    # File formats
    project_file_extension: str = ".vcalc"
    export_formats: list = field(default_factory=lambda: ["json", "csv", "pdf"])

    # Migration settings
    legacy_migration_enabled: bool = True
    migration_backup_originals: bool = True


@dataclass
class RecoveryConfig:
    """Configuration for error recovery and resilience."""

    # Checkpoint settings
    checkpoint_enabled: bool = True
    max_checkpoints_per_project: int = 10
    checkpoint_interval: int = 300  # seconds

    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    graceful_degradation: bool = True

    # Crash recovery
    crash_detection_enabled: bool = True
    auto_recovery_enabled: bool = True
    recovery_timeout: float = 10.0  # seconds


@dataclass
class LoggingConfig:
    """Configuration for logging system."""

    # Log levels
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_files: int = 5

    # Performance monitoring
    performance_logging: bool = True
    slow_operation_threshold: float = 1.0  # seconds

    # Error tracking
    error_summary_enabled: bool = True
    error_summary_window: int = 100  # operations


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""

    # API settings
    api_enabled: bool = False
    api_host: str = "localhost"
    api_port: int = 8000

    # External services
    asce_api_enabled: bool = False
    weather_api_enabled: bool = False

    # Plugin system
    plugins_enabled: bool = True
    plugin_directory: str = "plugins"


class ConfigurationManager:
    """
    Centralized configuration management system.

    Features:
    - Hierarchical configuration loading
    - Environment-specific overrides
    - Runtime configuration updates
    - Configuration validation
    - Auto-save and persistence
    """

    def __init__(self, config_dir: Optional[str] = None):
        self.logger = get_logger()

        # Configuration file paths
        if config_dir is None:
            self.config_dir = Path.home() / ".valley_calculator"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.user_config_file = self.config_dir / "user_config.json"

        # Configuration components
        self.calculation = CalculationConfig()
        self.ui = UIConfig()
        self.persistence = PersistenceConfig()
        self.recovery = RecoveryConfig()
        self.logging = LoggingConfig()
        self.integration = IntegrationConfig()

        # Load configuration
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from files and environment."""
        try:
            # Load default configuration
            self._load_default_config()

            # Load user configuration (overrides defaults)
            self._load_user_config()

            # Apply environment overrides
            self._apply_environment_overrides()

            # Validate configuration
            self._validate_configuration()

            self.logger.log_recovery_action("Configuration loaded successfully", True)

        except Exception as e:
            self.logger.log_error(e, operation="load_configuration")
            # Continue with defaults if loading fails

    def _load_default_config(self):
        """Load default configuration values."""
        # Configuration is already initialized with defaults via dataclass
        pass

    def _load_user_config(self):
        """Load user-specific configuration overrides."""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, "r") as f:
                    user_config = json.load(f)

                # Apply user configuration
                self._apply_config_dict(user_config)

            except Exception as e:
                self.logger.log_error(e, operation="load_user_config")

    def _apply_environment_overrides(self):
        """Apply configuration overrides from environment variables."""
        # Example: VALLEY_CALCULATION_TIMEOUT=60.0
        env_mappings = {
            "VALLEY_CALCULATION_TIMEOUT": ("calculation", "calculation_timeout"),
            "VALLEY_UI_THEME": ("ui", "default_theme"),
            "VALLEY_AUTO_SAVE_INTERVAL": ("ui", "auto_save_interval"),
            "VALLEY_DATABASE_PATH": ("persistence", "database_path"),
            "VALLEY_LOG_LEVEL": ("logging", "console_level"),
        }

        for env_var, (component, attribute) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert string to appropriate type
                    if attribute in [
                        "calculation_timeout",
                        "retry_delay",
                        "recovery_timeout",
                    ]:
                        value = float(value)
                    elif attribute in [
                        "max_iterations",
                        "max_checkpoints_per_project",
                        "max_backup_files",
                        "max_recent_projects",
                    ]:
                        value = int(value)
                    elif attribute in [
                        "checkpoint_enabled",
                        "auto_save_enabled",
                        "api_enabled",
                    ]:
                        value = value.lower() in ("true", "1", "yes")

                    # Apply the value
                    config_component = getattr(self, component)
                    setattr(config_component, attribute, value)

                except (ValueError, TypeError) as e:
                    self.logger.log_error(
                        e,
                        operation="apply_env_override",
                        context={"env_var": env_var, "value": value},
                    )

    def _apply_config_dict(self, config_dict: Dict[str, Any]):
        """Apply configuration from dictionary."""
        for component_name, component_config in config_dict.items():
            if hasattr(self, component_name):
                component = getattr(self, component_name)
                if isinstance(component_config, dict):
                    for attr_name, value in component_config.items():
                        if hasattr(component, attr_name):
                            setattr(component, attr_name, value)

    def _validate_configuration(self):
        """Validate configuration values."""
        errors = []

        # Validate calculation config
        if self.calculation.calculation_timeout <= 0:
            errors.append("calculation_timeout must be positive")
        if self.calculation.max_iterations <= 0:
            errors.append("max_iterations must be positive")

        # Validate UI config
        if self.ui.default_width < self.ui.min_width:
            errors.append("default_width cannot be less than min_width")
        if self.ui.default_height < self.ui.min_height:
            errors.append("default_height cannot be less than min_height")

        # Validate persistence config
        if self.persistence.max_backup_files < 1:
            errors.append("max_backup_files must be at least 1")

        if errors:
            for error in errors:
                self.logger.log_error(
                    ValueError(error), operation="validate_configuration"
                )

    def save_configuration(self):
        """Save current configuration to user config file."""
        try:
            config_dict = {
                "calculation": self._dataclass_to_dict(self.calculation),
                "ui": self._dataclass_to_dict(self.ui),
                "persistence": self._dataclass_to_dict(self.persistence),
                "recovery": self._dataclass_to_dict(self.recovery),
                "logging": self._dataclass_to_dict(self.logging),
                "integration": self._dataclass_to_dict(self.integration),
            }

            with open(self.user_config_file, "w") as f:
                json.dump(config_dict, f, indent=2)

            self.logger.log_recovery_action("Configuration saved", True)

        except Exception as e:
            self.logger.log_error(e, operation="save_configuration")

    def get(self, component: str, attribute: str, default=None):
        """
        Get a configuration value.

        Args:
            component: Configuration component name
            attribute: Attribute name
            default: Default value if not found

        Returns:
            Configuration value
        """
        try:
            config_component = getattr(self, component)
            return getattr(config_component, attribute, default)
        except AttributeError:
            return default

    def set(self, component: str, attribute: str, value):
        """
        Set a configuration value.

        Args:
            component: Configuration component name
            attribute: Attribute name
            value: New value
        """
        try:
            config_component = getattr(self, component)
            if hasattr(config_component, attribute):
                setattr(config_component, attribute, value)
                self.save_configuration()
                self.logger.log_recovery_action(
                    f"Configuration updated: {component}.{attribute}", True
                )
        except Exception as e:
            self.logger.log_error(e, operation="set_configuration")

    def reset_to_defaults(self, component: Optional[str] = None):
        """
        Reset configuration to defaults.

        Args:
            component: Specific component to reset, or None for all
        """
        try:
            if component:
                # Reset specific component
                default_configs = {
                    "calculation": CalculationConfig(),
                    "ui": UIConfig(),
                    "persistence": PersistenceConfig(),
                    "recovery": RecoveryConfig(),
                    "logging": LoggingConfig(),
                    "integration": IntegrationConfig(),
                }
                if component in default_configs:
                    setattr(self, component, default_configs[component])
            else:
                # Reset all components
                self.calculation = CalculationConfig()
                self.ui = UIConfig()
                self.persistence = PersistenceConfig()
                self.recovery = RecoveryConfig()
                self.logging = LoggingConfig()
                self.integration = IntegrationConfig()

            self.save_configuration()
            self.logger.log_recovery_action(
                f"Configuration reset to defaults ({component or 'all'})", True
            )

        except Exception as e:
            self.logger.log_error(e, operation="reset_to_defaults")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for debugging.

        Returns:
            Dictionary with configuration summary
        """
        return {
            "calculation_timeout": self.calculation.calculation_timeout,
            "default_theme": self.ui.default_theme,
            "auto_save_enabled": self.ui.auto_save_enabled,
            "database_path": self.persistence.database_path,
            "checkpoint_enabled": self.recovery.checkpoint_enabled,
            "api_enabled": self.integration.api_enabled,
        }

    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return {
            field.name: getattr(obj, field.name)
            for field in obj.__dataclass_fields__.values()
        }


# Global configuration instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_config(component: str, attribute: str, default=None):
    """
    Convenience function to get configuration value.

    Args:
        component: Configuration component name
        attribute: Attribute name
        default: Default value if not found

    Returns:
        Configuration value
    """
    return get_config_manager().get(component, attribute, default)


def set_config(component: str, attribute: str, value):
    """
    Convenience function to set configuration value.

    Args:
        component: Configuration component name
        attribute: Attribute name
        value: New value
    """
    get_config_manager().set(component, attribute, value)
