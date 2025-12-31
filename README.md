# Valley Snow Load Calculator

A comprehensive engineering tool for calculating snow loads on valley structures according to ASCE 7-22 standards.

## Repository

**GitHub**: [https://github.com/YOUR_USERNAME/valley-snow-load-calc](https://github.com/YOUR_USERNAME/valley-snow-load-calc)  
**Cloud Backup**: Active on GitHub ✅

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

### Auto-Save & Crash Recovery

- **Automatic backup every 2 minutes** or when data changes
- **Crash detection** with `.crash` flag file
- **Auto-save to `state.backup.json`** for immediate recovery
- **Startup recovery** - automatically detects crashes and offers restoration
- **Data preservation** - never lose work due to application crashes
- **Multi-platform support** - works on Python GUI and TypeScript versions

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
   # Backup data before making changes (recommended)
   .\backup_data.ps1

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

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com) for automated code quality checks. Pre-commit hooks run automatically on every commit to ensure code consistency and quality.

#### Installation

```bash
# Install pre-commit (Python package)
pip install pre-commit

# Install the pre-commit hooks in this repository
pre-commit install

# Optional: Install hooks for commit-msg checks (conventional commits)
pre-commit install --hook-type commit-msg
```

#### Windows PATH Fix

On Windows, if `pre-commit` command is not in your PATH, use the provided batch file:

```bash
# Use this instead of 'pre-commit'
precommit install
precommit run --all-files
precommit run

# Optional: Add project root to Windows PATH permanently
# 1. Right-click "This PC" → Properties → Advanced system settings
# 2. Environment Variables → System Variables → Path → Edit
# 3. Add: C:\path\to\your\valley_snow_load_calc
# 4. Restart command prompt/terminal
```

#### Available Scripts

For the TypeScript version, you can also use npm scripts:

```bash
cd development_v2/typescript_version

# Install pre-commit hooks
npm run precommit:install

# Run all pre-commit checks on all files
npm run precommit:run
```

#### What the Hooks Do

- **trailing-whitespace**: Removes trailing whitespace from files
- **end-of-file-fixer**: Ensures files end with a newline
- **black**: Auto-formats Python code
- **ruff**: Lints and fixes Python code
- **prettier**: Auto-formats JavaScript/TypeScript/JSON/YAML/Markdown files
- **eslint**: Lints and fixes JavaScript/TypeScript code
- **check-added-large-files**: Prevents committing files larger than 500KB
- **commitizen** (optional): Validates conventional commit messages

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

## Daily Workflow

### Quick Start Commands

Use these npm scripts from the TypeScript version directory (`cd development_v2/typescript_version`):

```bash
# Start your day
npm run pull

# Work and commit frequently (every 15-30 minutes)
npm run commit "feat: implement new calculation module"

# Check current status
npm run status

# Fix linting/formatting issues
npm run precommit:run

# End your day
npm run push
```

### Step-by-Step Daily Routine

1. **Morning Start**

   ```bash
   cd development_v2/typescript_version
   npm run pull  # Get latest changes
   npm run status  # See what's new
   ```

2. **Development Work**

   ```bash
   # Make your changes...
   npm run commit "feat: add new feature"  # Commit every 15-30 mins
   npm run commit "fix: resolve bug in calculations"
   npm run commit "docs: update API documentation"
   ```

3. **Code Quality**

   ```bash
   # Before pushing, ensure code quality
   npm run precommit:run  # Fix any lint/format issues
   npm run test  # Run tests
   ```

4. **End of Day**
   ```bash
   npm run push  # Push your work
   ```

### Tips

- **Commit Often**: Small, frequent commits make collaboration easier
- **Clear Messages**: Use conventional commit format (feat:, fix:, docs:, etc.)
- **Pre-commit First**: Run `npm run precommit:run` before pushing to catch issues early
- **Test Before Push**: Always run tests before pushing changes

## Auto-Save Protocol

The Valley Snow Load Calculator includes a comprehensive auto-save system to prevent data loss:

### Automatic Features

- **Real-time Auto-Save**: Saves current state every 2 minutes
- **Change Detection**: Saves immediately when any input data changes
- **Crash Detection**: Creates `.crash` flag file on startup, removes on normal exit
- **Recovery System**: Automatically detects crashes and offers state restoration

### Manual Backup

Run the backup script before making significant changes:

```powershell
# Windows PowerShell
.\backup_data.ps1

# Or specify custom backup directory
.\backup_data.ps1 -BackupDir "my_backups"
```

### Files and Locations

#### Auto-Save Files

- `state.backup.json` - Current application state (auto-saved)
- `.crash` - Crash detection flag (removed on normal exit)

#### Manual Backup Files

- `auto_backups/YYYY-MM-DD_HH-MM-SS/` - Timestamped backup directories
- `user_preferences.json` - User interface preferences
- SQLite databases (`*.db`, `*.sqlite`, `*.sqlite3`)
- TypeScript app database (`%APPDATA%\ValleySnowLoadCalc\valley_calc.db`)

### Recovery Process

1. **Crash Detection**: Application checks for `.crash` file on startup
2. **Backup Verification**: Confirms `state.backup.json` exists and is valid
3. **User Prompt**: Asks if user wants to restore auto-saved state
4. **State Restoration**: Reloads all inputs, calculations, and results
5. **Cleanup**: Removes crash flag and backup file on successful recovery

### Technical Implementation

- **Python Version**: Threading-based timer with Tkinter integration
- **TypeScript Version**: Event-driven checkpoint system with file system monitoring
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Data Integrity**: JSON format with timestamp validation

## Data Backup System

The project includes additional data backup protection:

- **Pre-commit Hook**: Automatically backs up data files before each commit
- **Backup Location**: `auto_backups/YYYY-MM-DD_HH-MM-SS/`
- **Backed Up Files**:
  - User preferences (`user_preferences.json`)
  - SQLite databases (`*.db`, `*.sqlite`, `*.sqlite3`)
  - Application data files

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
