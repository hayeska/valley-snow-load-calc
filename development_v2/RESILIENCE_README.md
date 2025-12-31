# Valley Snow Load Calculator - Resilient Architecture

## Overview

This document describes the resilient architecture implemented for the Valley Snow Load Calculator V2.0, designed to prevent data loss from crashes and provide robust error handling.

## Architecture Components

### 1. Core Resilience Modules

#### Data Persistence (`data/persistence/`)
- **SQLite Database**: ACID-compliant storage with transaction safety
- **Automatic Integrity Checking**: SHA256 checksums for data validation
- **Backup and Recovery**: Automated backup creation and restoration

#### Logging System (`utils/logging/`)
- **Comprehensive Error Tracking**: Multi-level logging with context
- **Performance Monitoring**: Operation timing and success rates
- **Crash Recovery Logging**: Detailed crash analysis and recovery tracking

#### Recovery System (`core/recovery/`)
- **Error Wrappers**: Decorators for automatic retry and recovery
- **Checkpoint System**: Incremental saves and data recovery points
- **Graceful Degradation**: Continued operation during partial failures

### 2. Key Features

#### Crash Prevention
- Auto-save every 5 minutes
- Checkpoints on significant data changes
- Emergency save on application exit/crash

#### Data Integrity
- SQLite transactions for atomic operations
- Checksum validation for data corruption detection
- Backup creation and validation

#### Error Recovery
- Automatic retry with exponential backoff
- Recovery strategies for specific error types
- Graceful degradation for non-critical failures

#### Monitoring & Logging
- Performance metrics collection
- Error pattern analysis
- System health monitoring

## Code Snippets

### Error Wrapper Decorators

```python
from valley_calculator.core.recovery.error_handlers import resilient_operation, error_boundary

# Automatic retry with recovery
@resilient_operation(retries=3, backoff=1.0, recoverable=True, save_checkpoint=True)
def critical_calculation(data):
    # Risky calculation code
    return result

# Error boundary for operations
@error_boundary("database_operation", recoverable=True)
def database_operation():
    # Database code that might fail
    pass

# Input validation
@validate_input(validate_positive_number, validate_non_empty_string)
def process_input(value, name):
    return f"Processing {name}: {value}"
```

### Auto-Save and Checkpoints

```python
from valley_calculator.core.recovery.checkpoint_system import checkpoint_on_change

# Automatic checkpoints on data changes
@checkpoint_on_change("project_id")
def update_project_data(project_id, new_data):
    # Update project data
    return updated_data

# Manual checkpoint creation
checkpoint_mgr = get_checkpoint_manager()
success = checkpoint_mgr.create_checkpoint(
    project_id="my_project",
    data=project_data,
    operation="manual_save"
)
```

### Database Operations

```python
from valley_calculator.data.persistence.database import get_database

db = get_database()

# Save project with integrity checking
project_id = db.save_project("my_project", "Project Name", project_data)

# Load with validation
project_data = db.load_project(project_id)

# Create recovery checkpoint
db.create_checkpoint(project_id, "checkpoint_1", data, "user_action")
```

### Logging

```python
from valley_calculator.utils.logging.logger import get_logger

logger = get_logger()

# Log performance
logger.log_performance("calculation", 1.5, success=True)

# Log errors with context
logger.log_error(exception, operation="calculation", recoverable=True,
                context={"input_data": data})

# Log recovery actions
logger.log_recovery_action("Data recovered from checkpoint", True)
```

## Folder Structure

```
valley_calculator/
├── core/
│   ├── recovery/
│   │   ├── error_handlers.py     # Error wrappers and recovery
│   │   └── checkpoint_system.py  # Auto-save and checkpoints
│   ├── calculator.py             # Resilient calculation engine
│   └── project.py               # Resilient project management
├── data/
│   └── persistence/
│       └── database.py           # SQLite persistence layer
├── utils/
│   └── logging/
│       └── logger.py             # Comprehensive logging system
├── gui/
│   └── main_window.py            # GUI with recovery integration
└── tests/
    └── test_resilience.py        # Resilience feature tests
```

## Usage Examples

### Basic Application Usage

```python
from valley_calculator import create_application

# Create resilient application
app = create_application()

# Application automatically handles:
# - Crash recovery on startup
# - Auto-save during operation
# - Error recovery for failed operations
# - Data integrity validation

app.run()
```

### Manual Recovery

```python
from valley_calculator.core.project import ProjectManager

project_mgr = ProjectManager()

# Get recovery options for a project
recovery_options = project_mgr.get_project_recovery_options("project_id")

# Recover from specific checkpoint
recovered_data = project_mgr.recover_project_from_checkpoint("checkpoint_id")

# Check system health
health = project_mgr.get_system_health_status()
```

### Custom Error Handling

```python
from valley_calculator.core.recovery.error_handlers import (
    register_error_recovery, get_recovery_manager
)

# Register custom recovery strategy
def handle_calculation_error(error, *args, **kwargs):
    # Custom recovery logic
    return fallback_result

register_error_recovery(CalculationError, handle_calculation_error)
```

## Configuration

### Auto-Save Settings

```python
from valley_calculator.core.recovery.checkpoint_system import get_checkpoint_manager

checkpoint_mgr = get_checkpoint_manager()
# Auto-save interval (seconds)
# Default: 300 (5 minutes)
```

### Logging Configuration

```python
from valley_calculator.utils.logging.logger import ResilienceLogger

# Custom log directory
logger = ResilienceLogger(log_dir="/path/to/logs", max_file_size=50*1024*1024)
```

### Database Configuration

```python
from valley_calculator.data.persistence.database import DatabaseManager

# Custom database location
db = DatabaseManager(db_path="/path/to/valley_calc.db")
```

## Testing

Run the resilience tests:

```bash
cd development_v2
python -m pytest valley_calculator/tests/test_resilience.py -v
```

Or run specific tests:

```bash
python -m unittest valley_calculator.tests.test_resilience.TestResilienceFeatures.test_database_operations
```

## Recovery Procedures

### After Application Crash

1. **Automatic Recovery**: Application detects crash on next startup
2. **Recovery Options**: User presented with recovery choices
3. **Data Restoration**: Select checkpoint or last good state
4. **Verification**: Data integrity checked before restoration

### Manual Recovery

1. Open application
2. Go to Tools → Data Recovery
3. Select project and recovery point
4. Confirm restoration

### System Health Check

- Tools → System Health Check
- View error statistics and recovery status
- Run automated recovery procedures

## Performance Considerations

- **Logging Overhead**: Minimal performance impact with async logging
- **Checkpoint Frequency**: Configurable based on data change patterns
- **Database Optimization**: WAL mode for concurrent access
- **Memory Usage**: Bounded logging and checkpoint retention

## Security Features

- **Data Integrity**: Checksum validation prevents tampering
- **Transaction Safety**: ACID properties prevent partial updates
- **Backup Encryption**: Optional encryption for sensitive backups
- **Access Logging**: Comprehensive audit trail

## Future Enhancements

- **Cloud Backup**: Optional cloud storage integration
- **Real-time Sync**: Multi-device synchronization
- **Advanced Analytics**: Error pattern recognition and prediction
- **Performance Profiling**: Detailed performance bottleneck analysis

## Support

For issues with the resilient architecture:

1. Check system health: Tools → System Health Check
2. Review logs: Located in user data directory
3. Run diagnostics: Tools → Data Recovery
4. Contact support with health check results
