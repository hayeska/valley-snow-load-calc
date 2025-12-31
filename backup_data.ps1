# Valley Snow Load Calculator - Data Backup Script
# Run this script before making significant changes to backup important data files

param(
    [string]$BackupDir = "auto_backups"
)

$ErrorActionPreference = "Stop"

# Get the project root directory
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKUP_DIR = Join-Path $PROJECT_ROOT $BackupDir

# Create backup directory if it doesn't exist
if (!(Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
}

# Generate timestamp for backup folder
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$CURRENT_BACKUP_DIR = Join-Path $BACKUP_DIR $TIMESTAMP

# Create timestamped backup directory
New-Item -ItemType Directory -Path $CURRENT_BACKUP_DIR -Force | Out-Null

Write-Host "Creating data backup: $TIMESTAMP" -ForegroundColor Green

# Files to backup
$BACKUP_FILES = @(
    "user_preferences.json",
    "*.db",
    "*.sqlite",
    "*.sqlite3"
)

# Backup files from project root
foreach ($pattern in $BACKUP_FILES) {
    $files = Get-ChildItem -Path $PROJECT_ROOT -Filter $pattern -File -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        if (Test-Path $file.FullName) {
            $relativePath = $file.Name
            $destinationPath = Join-Path $CURRENT_BACKUP_DIR $relativePath

            # Ensure destination directory exists
            $destDir = Split-Path $destinationPath -Parent
            if (!(Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }

            Copy-Item -Path $file.FullName -Destination $destinationPath -Force
            Write-Host "  Backed up: $relativePath" -ForegroundColor Yellow
        }
    }
}

# Backup TypeScript database files from AppData (if they exist)
$APPDATA_DB_PATH = "$env:USERPROFILE\AppData\Local\ValleySnowLoadCalc\valley_calc.db"
if (Test-Path $APPDATA_DB_PATH) {
    $destPath = Join-Path $CURRENT_BACKUP_DIR "AppData_valley_calc.db"
    Copy-Item -Path $APPDATA_DB_PATH -Destination $destPath -Force
    Write-Host "  Backed up: AppData\ValleySnowLoadCalc\valley_calc.db" -ForegroundColor Yellow
}

# Clean up old backups (keep last 10)
$existingBackups = Get-ChildItem -Path $BACKUP_DIR -Directory | Sort-Object CreationTime -Descending
if ($existingBackups.Count -gt 10) {
    $toDelete = $existingBackups | Select-Object -Skip 10
    foreach ($dir in $toDelete) {
        Remove-Item -Path $dir.FullName -Recurse -Force
        Write-Host "  Cleaned up old backup: $($dir.Name)" -ForegroundColor Gray
    }
}

Write-Host "Data backup completed successfully!" -ForegroundColor Green
Write-Host "Backup location: $CURRENT_BACKUP_DIR" -ForegroundColor Cyan
Write-Host ""
