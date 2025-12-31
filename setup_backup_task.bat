@echo off
REM Valley Snow Load Calculator - Windows Task Scheduler Setup
REM Sets up automatic hourly backups using Windows Task Scheduler

echo 🚀 Valley Snow Load Calculator - Backup Task Setup
echo ====================================================

REM Get the project directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Remove trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo 📁 Project directory: %PROJECT_DIR%

REM Check if Python backup script exists
if exist "%PROJECT_DIR%\backup_scheduler.py" (
    echo ✅ Python backup script found
) else (
    echo ❌ Python backup script not found: %PROJECT_DIR%\backup_scheduler.py
    pause
    exit /b 1
)

REM Check if schtasks is available
schtasks /? >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ schtasks command not found. Windows Task Scheduler is required.
    pause
    exit /b 1
)

echo.
echo 📋 Current backup tasks:
schtasks /query /tn "Valley Snow Load Backup" 2>nul
if %errorlevel% neq 0 (
    echo    No Valley Snow Load backup task found
)

echo.
echo 🔧 Setting up hourly backup task...
echo    This will run the backup script every hour

REM Find Python executable
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python3"
    ) else (
        echo ⚠️  Warning: Could not find python or python3 in PATH
        set "PYTHON_CMD=python"
    )
)

set "TASK_COMMAND=cd /d "%PROJECT_DIR%" && "%PYTHON_CMD%" backup_scheduler.py --once >> "%PROJECT_DIR%\backup_task.log" 2>&1"

echo.
echo 📝 Task command to be scheduled:
echo    %TASK_COMMAND%
echo.

set /p "choice=❓ Do you want to create this scheduled task? (y/N): "
if /i "%choice%"=="y" (
    REM Create the scheduled task
    schtasks /create /tn "Valley Snow Load Backup" /tr "%TASK_COMMAND%" /sc hourly /mo 1 /f

    if %errorlevel% equ 0 (
        echo ✅ Scheduled task created successfully!
        echo.
        echo 📋 Task details:
        schtasks /query /tn "Valley Snow Load Backup" /v /fo list | findstr /C:"TaskName" /C:"Schedule" /C:"Next Run Time"
        echo.
        echo 📁 Backup logs will be written to: %PROJECT_DIR%\backup_task.log
        echo 💾 Backups will be stored in: %%USERPROFILE%%\backups\valley_snow_calc\
        echo.
        echo 🛑 To remove the scheduled task:
        echo    setup_backup_task.bat --remove
        echo.
        echo ✅ Setup complete! Backups will run every hour.
    ) else (
        echo ❌ Failed to create scheduled task
        echo 💡 Try running as Administrator
        pause
        exit /b 1
    )
) else (
    echo ⏭️  Task creation cancelled
)

echo.
echo 💡 Alternative setup methods:
echo    1. Cron (Linux/Mac): Use setup_backup_cron.sh
echo    2. Manual: Run 'python backup_scheduler.py' in background

REM Check for --remove flag
if "%1"=="--remove" (
    echo.
    echo 🗑️  Removing backup scheduled task...
    schtasks /delete /tn "Valley Snow Load Backup" /f
    if %errorlevel% equ 0 (
        echo ✅ Backup scheduled task removed
    ) else (
        echo ❌ Failed to remove task
    )
    goto :end
)

:end
echo.
pause


