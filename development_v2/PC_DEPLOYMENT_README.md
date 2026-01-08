# Valley Snow Load Calculator - PC Version 2.0

A professional, PC-based engineering application for ASCE 7-22 snow load analysis with modern architecture and comprehensive features.

## 🎯 Perfect for PC-Based Engineering Work

This version is specifically designed as a **desktop engineering application** - no web dependencies, no cloud requirements, just professional engineering software that runs locally on your PC.

## ✨ Key Features

### 🏗️ Professional Engineering Software

- **ASCE 7-22 Compliant**: Complete snow load calculations for valley structures
- **Beam Design**: Integrated ASD analysis with load combinations
- **PDF Reports**: Professional engineering documentation
- **Project Management**: Save/load with full project history

### 💻 PC-Optimized Design

- **Desktop GUI**: Modern Tkinter interface optimized for desktop use
- **Local Storage**: All data stored locally (Documents folder)
- **Offline Operation**: No internet connection required
- **Fast Performance**: Calculations run instantly on local hardware
- **Auto-Save**: Automatic project saving and crash recovery

### 🛡️ Reliability & Data Integrity

- **Crash Recovery**: Automatic state restoration after crashes
- **Data Backup**: Multiple backup strategies and recovery points
- **Validation**: Comprehensive input validation and error checking
- **Logging**: Detailed operation logs for troubleshooting

## 🚀 Getting Started

### Prerequisites

- **Windows 10/11** (primary target platform)
- **Python 3.8+** (for development)
- **4GB RAM minimum** (recommended 8GB+)
- **1GB free disk space**

### Installation Options

#### Option 1: Direct Python Execution (Development)

```bash
cd development_v2
python main_v2.py
```

#### Option 2: Standalone Executable (Production)

```bash
# Run the deployment script
python setup_pc_deployment.py

# Then run the created executable
./dist/ValleySnowLoadCalculator.exe
```

#### Option 3: Portable Version

```bash
# Run deployment script
python setup_pc_deployment.py

# Copy the 'portable_valley_calculator' folder anywhere
# Run Run_Calculator.bat to start
```

## 🏛️ Architecture Overview

### Clean Modular Design

```
valley_calculator/
├── core/                 # Application core
│   ├── state.py         # State management
│   ├── config.py        # Configuration
│   └── calculator.py    # Main engine
├── calculations/         # Pure math (no UI)
│   ├── engine.py        # Calculation logic
│   └── [modules]        # ASCE 7-22 formulas
├── gui/                 # Desktop interface
│   └── main_window.py   # Tkinter GUI
├── data/                # Local storage
│   └── persistence/     # SQLite database
└── utils/               # Shared utilities
```

### Why This Architecture Works Perfectly for PC Software

1. **No Web Dependencies**: Everything runs locally
2. **Fast Performance**: Direct hardware access
3. **Data Security**: All files stay on local machine
4. **Professional UX**: Desktop-optimized interface
5. **Reliable Operation**: No network connectivity issues

## 📊 Engineering Capabilities

### Snow Load Analysis

- Ground snow load determination
- Roof slope factor calculations
- Balanced and unbalanced load analysis
- Drift load calculations for intersecting roofs

### Structural Design

- Valley beam analysis with ASD
- Load combination generation
- Deflection and stress analysis
- Material property integration

### Professional Output

- Detailed calculation reports
- PDF documentation generation
- Project templates and standards
- Engineering notation and units

## 🔧 Configuration & Customization

### User Preferences

- Interface themes and layouts
- Default engineering parameters
- Project templates
- Auto-save settings

### System Configuration

- Calculation precision settings
- Performance optimization
- Logging levels
- Backup frequency

## 📁 Data Management

### Local Storage

- **Projects**: `~/Documents/Valley Snow Load Projects/`
- **Database**: SQLite for project metadata
- **Backups**: Automatic timestamped backups
- **Logs**: Operation logs in app directory

### Data Integrity

- **Auto-save**: Every 2 minutes during active use
- **Crash Recovery**: Automatic state restoration
- **Backup System**: Multiple recovery points
- **Validation**: Data integrity checking

## 🧪 Quality Assurance

### Testing Coverage

- **22 Unit Tests**: All calculation functions verified
- **Integration Tests**: End-to-end workflows tested
- **Validation Tests**: Input checking and error handling
- **Performance Tests**: Speed and reliability verified

### Code Quality

- **Modular Design**: 11 focused modules vs 1 monolithic file
- **Error Handling**: Comprehensive recovery strategies
- **Documentation**: Full API documentation
- **Standards**: PEP 8 compliance, type hints

## 🚀 Deployment Options

### For Engineers (End Users)

1. **Download executable** from project releases
2. **Extract to any folder** (portable)
3. **Run directly** - no installation required
4. **Projects save automatically** to Documents folder

### For IT Deployment

1. **Standalone executable** - no dependencies
2. **Portable folder** - can be deployed via network
3. **Group policy** - standard Windows deployment
4. **Licensing ready** - can add license keys if needed

## 🎯 Perfect for Engineering Workflows

### Typical Usage Scenarios

- **Office Engineering**: Daily design calculations
- **Site Analysis**: Field data processing
- **Report Generation**: Professional documentation
- **Code Compliance**: ASCE 7-22 verification
- **Project Archiving**: Long-term record keeping

### Integration Ready

- **Excel Import/Export**: CSV data exchange
- **PDF Reports**: Standard engineering format
- **Project Templates**: Reusable configurations
- **Batch Processing**: Multiple load cases

## 📞 Support & Maintenance

### Self-Contained

- **No internet required** for normal operation
- **Local help system** built into interface
- **Automatic updates** can be added later
- **Comprehensive logging** for troubleshooting

### Future Enhancements

- **Plugin system** ready for extensions
- **Additional materials** database expandable
- **Regional codes** can be added
- **Advanced analysis** features possible

---

## 🎉 Summary

**Version 2.0 is a complete, professional PC-based engineering application** that transforms the original calculator into modern, maintainable software while preserving all engineering accuracy and adding significant reliability improvements.

**Perfect for:**

- Structural engineers doing snow load analysis
- Building officials verifying code compliance
- Engineering consultants preparing calculations
- Educational institutions teaching structural design

**Ready to deploy as:**

- Standalone desktop application
- Portable engineering tool
- Professional engineering software

The architecture supports long-term maintenance, feature additions, and professional engineering workflows - all while remaining a reliable PC-based application that engineers can trust. 🏗️⚡
