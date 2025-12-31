#!/bin/bash
# Valley Snow Load Calculator - Cron Job Setup Script
# Sets up automatic hourly backups using cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Valley Snow Load Calculator - Backup Cron Setup"
echo "=================================================="

# Check if Python backup script exists
if [ -f "$PROJECT_DIR/backup_scheduler.py" ]; then
    echo "✅ Python backup script found"
else
    echo "❌ Python backup script not found: $PROJECT_DIR/backup_scheduler.py"
    exit 1
fi

# Check if crontab is available
if ! command -v crontab &> /dev/null; then
    echo "❌ crontab command not found. Please install cron."
    exit 1
fi

echo ""
echo "📋 Current cron jobs:"
crontab -l | grep -v "^#" | grep -v "^$" || echo "   No cron jobs found"

echo ""
echo "🔧 Setting up hourly backup cron job..."
echo "   This will run the backup script every hour at minute 0"

# Create cron job entry
PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null || echo "python")
if [ "$PYTHON_PATH" = "python" ]; then
    echo "⚠️  Warning: Could not find python3, using 'python'"
fi

CRON_JOB="0 * * * * cd \"$PROJECT_DIR\" && \"$PYTHON_PATH\" backup_scheduler.py --once >> \"$PROJECT_DIR/backup_cron.log\" 2>&1"

echo ""
echo "📝 Cron job to be added:"
echo "   $CRON_JOB"
echo ""

read -p "❓ Do you want to add this cron job? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

    if [ $? -eq 0 ]; then
        echo "✅ Cron job added successfully!"
        echo ""
        echo "📋 Updated cron jobs:"
        crontab -l | grep -v "^#" | grep -v "^$" || echo "   No cron jobs found"
        echo ""
        echo "📁 Backup logs will be written to: $PROJECT_DIR/backup_cron.log"
        echo "💾 Backups will be stored in: ~/backups/valley_snow_calc/"
        echo ""
        echo "🛑 To stop automatic backups:"
        echo "   ./setup_backup_cron.sh --remove"
        echo ""
        echo "✅ Setup complete! Backups will run every hour."
    else
        echo "❌ Failed to add cron job"
        exit 1
    fi
else
    echo "⏭️  Cron job setup cancelled"
fi

echo ""
echo "💡 Alternative setup methods:"
echo "   1. Systemd timer (Linux): Create /etc/systemd/system/valley-backup.timer"
echo "   2. Windows Task Scheduler: Use schtasks.exe"
echo "   3. Manual: Run 'python backup_scheduler.py' in background"

# Check for --remove flag
if [ "$1" = "--remove" ]; then
    echo ""
    echo "🗑️  Removing backup cron job..."
    crontab -l | grep -v "backup_scheduler.py" | crontab -
    echo "✅ Backup cron job removed"
    exit 0
fi


