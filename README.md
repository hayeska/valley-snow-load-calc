# Valley Snow Load Calculator

A comprehensive engineering tool for calculating snow loads on valley structures according to ASCE 7-22 standards.

## Overview

This calculator implements the ASCE 7-22 Chapter 7 snow load provisions for valley and roof structures. It provides both a production-ready version (V1) and a modern, modular architecture version (V2) currently in development.

### Current Status
- **V1 (Production Ready)**: Complete implementation with all ASCE 7-22 features, HTML reports, and material database
- **V2 (Development)**: 70% complete with modern architecture, missing 5 critical engineering features

## Features

### Core Calculations
- ASCE 7-22 snow load calculations for valley structures
- Ground snow load determination
- Roof snow load calculations
- Drift load analysis
- Balanced and unbalanced load conditions

### User Interface
- Modern GUI with theme support (Light/Dark/High Contrast)
- Real-time input validation
- Comprehensive tooltips and help system
- Professional engineering workflow

### Reporting & Output
- PDF reports with diagrams and calculations
- HTML reports (V1 only)
- Detailed engineering output with intermediate values
- Material properties database integration

## Installation

### Prerequisites
- Python 3.8+
- Git (for version control)

### Setup
```bash
git clone <repository-url>
cd valley_snow_load_calc
pip install -r requirements.txt
python main.py
```

### For Development (V2)
```bash
cd development_v2
pip install -r requirements-dev.txt
python main_v2.py
```

## Project Structure

```
valley_snow_load_calc/
├── main.py                          # V1 Entry point
├── gui_interface.py                 # V1 GUI application
├── constants.py                     # ASCE 7-22 constants
├── asce7_22_reference.py           # Standard references
├── geometry.py                     # Geometric calculations
├── snow_loads.py                   # Snow load calculations
├── beam_design.py                  # Structural analysis
├── drift_calculator.py             # Drift load calculations
├── slope_factors.py                # Slope adjustment factors
├── validation.py                   # Input validation
├── development_v2/                 # V2 modular architecture
│   ├── valley_calculator/
│   │   ├── core/                   # Core calculation modules
│   │   ├── gui/                    # Modern GUI components
│   │   ├── calculations/           # Calculation engines
│   │   ├── reporting/              # Report generation
│   │   └── tests/                  # Unit tests
│   └── typescript_version/         # TypeScript implementation
└── auto_backups/                   # Automatic data backups
```

## Development Workflow

### Branching Strategy

This project uses a simplified Git branching model:

#### `main` Branch
- **Purpose**: Production-ready code only
- **Content**: Stable releases, thoroughly tested
- **Protection**: Requires review and CI/CD approval
- **Merging**: Only from `release/*` branches after QA

#### `feature/*` Branches
- **Purpose**: All new development work
- **Naming**: `feature/descriptive-name` (e.g., `feature/html-reports`, `feature/material-database`)
- **Lifetime**: Created from `main`, merged back to `main` via pull request
- **Guidelines**:
  - One feature per branch
  - Regular commits with clear messages
  - Include tests for new functionality
  - Update documentation as needed

#### `release/*` Branches (Future Use)
- **Purpose**: Release preparation and QA
- **Content**: Feature-complete versions ready for production
- **Process**: Created from `main` when preparing releases

### Development Process

1. **Start New Feature**
   ```bash
   git checkout main
   git pull
   git checkout -b feature/your-feature-name
   ```

2. **Development Workflow**
   ```bash
   # Make changes
   git add .
   git commit -m "feat: implement feature description"

   # Push and create PR when ready
   git push -u origin feature/your-feature-name
   ```

3. **Code Quality**
   - Run tests: `python -m pytest`
   - Check linting: `flake8`
   - Pre-commit hooks automatically backup data files

### Commit Message Conventions

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code restructuring
test: add tests
chore: maintenance tasks
```

## Data Backup System

The project includes automatic data backup protection:

- **Pre-commit Hook**: Automatically backs up data files before each commit
- **Backup Location**: `auto_backups/YYYY-MM-DD_HH-MM-SS/`
- **Backed Up Files**:
  - User preferences (`user_preferences.json`)
  - SQLite databases (`*.db`, `*.sqlite`, `*.sqlite3`)
  - Application data files

### Manual Backup
```bash
# Trigger backup manually
python -c "
import os
import shutil
from datetime import datetime

backup_dir = f'auto_backups/{datetime.now().strftime(\"%Y-%m-%d_%H-%M-%S\")}'
os.makedirs(backup_dir, exist_ok=True)
# Copy data files...
"
```

## Testing

### Running Tests
```bash
# V1 Tests
python -m pytest tests/

# V2 Tests
cd development_v2
python -m pytest valley_calculator/tests/
```

### Test Coverage
- Unit tests for calculation modules
- Integration tests for GUI components
- Validation tests for ASCE 7-22 compliance

## Contributing

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with tests
4. Ensure all tests pass
5. Create a pull request with detailed description
6. Wait for review and approval

### Code Standards
- PEP 8 compliance
- Type hints for all functions
- Comprehensive docstrings
- Unit test coverage > 80%

## Documentation

- [ASCE 7-22 Reference Implementation](asce7_22_reference.py)
- [API Documentation](docs/api.md)
- [User Manual](docs/user_manual.md)
- [Development Guide](development_v2/README_V2.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check existing documentation
- Review the troubleshooting guide

## Version History

### V1.0.0 (Production Ready)
- Complete ASCE 7-22 implementation
- Full HTML reporting
- Material properties database
- Real-time validation

### V2.0.0 (Development)
- Modern modular architecture
- Theme support
- PDF reporting
- 70% feature complete
