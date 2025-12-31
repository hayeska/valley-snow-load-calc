# Valley Snow Load Calculator - Backup System

Automated backup system that creates hourly compressed archives of the project and optionally uploads to cloud storage.

## 🚀 Quick Start

### Python Version (Recommended)
```bash
# Run once
python backup_scheduler.py --once

# Test backup creation
python backup_scheduler.py --test

# Run continuously (hourly backups)
python backup_scheduler.py
```

### JavaScript/Node.js Version
```bash
cd development_v2/typescript_version

# Install dependencies
npm install

# Test backup
npm run backup:test

# Run once
npm run backup:once

# Run continuously
npm run backup
```

## 📋 Features

- **Hourly Automated Backups**: Scheduled zipping of entire project
- **Smart Exclusions**: Automatically excludes build artifacts, logs, and temporary files
- **Compression**: High-compression ZIP archives
- **Cloud Upload**: Optional Google Drive integration
- **Cleanup**: Automatic removal of old backups (configurable)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Logging**: Comprehensive backup operation logs

## 📁 Backup Locations

### Local Backups
- **Python**: `~/backups/valley_snow_calc/`
- **JavaScript**: `~/backups/valley_snow_calc/` (configurable)

### Cloud Storage
- **Google Drive**: Creates folder "Valley Snow Load Backups"
- **Automatic Upload**: Enabled via configuration

## ⚙️ Configuration

Edit `backup_config.json` to customize behavior:

```json
{
  "excludePatterns": [
    "__pycache__", "*.pyc", ".git", "node_modules",
    "*.log", "auto_backups", "*.tmp", ".DS_Store"
  ],
  "includeDataFiles": true,
  "cloudUpload": false,
  "cloudProvider": "google_drive",
  "compressionLevel": 6,
  "googleDriveFolder": "Valley Snow Load Backups",
  "maxLocalBackups": 24,
  "backupSchedule": "0 * * * *"
}
```

## 🔧 Google Drive Setup (Optional)

### 1. Enable Google Drive API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Drive API"
4. Create OAuth 2.0 credentials
5. Download `credentials.json` to project root

### 2. Install Dependencies
```bash
cd development_v2/typescript_version
npm install
```

### 3. First Run Authentication
```bash
npm run backup
# Follow browser authentication prompts
```

### 4. Enable Cloud Upload
Edit `backup_config.json`:
```json
{
  "cloudUpload": true,
  "cloudProvider": "google_drive"
}
```

## 🕒 Scheduling Backups

### Windows (Task Scheduler)
```cmd
# Run setup script as Administrator
setup_backup_task.bat

# Or manually create task:
schtasks /create /tn "Valley Snow Load Backup" /tr "python C:\path\to\backup_scheduler.py --once" /sc hourly /mo 1
```

### Linux/macOS (Cron)
```bash
# Make script executable and run setup
chmod +x setup_backup_cron.sh
./setup_backup_cron.sh

# Or manually add to crontab:
crontab -e
# Add: 0 * * * * cd /path/to/project && python backup_scheduler.py --once
```

### Systemd Timer (Linux)
Create `/etc/systemd/system/valley-backup.service`:
```ini
[Unit]
Description=Valley Snow Load Calculator Backup

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/backup_scheduler.py --once
User=your-user
```

Create `/etc/systemd/system/valley-backup.timer`:
```ini
[Unit]
Description=Hourly Valley Snow Load Backup

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## 📊 Monitoring Backups

### Log Files
- **Python**: `~/backups/valley_snow_calc/backup_scheduler.log`
- **JavaScript**: Console output (redirect to file if needed)
- **Cron/Windows Task**: `backup_cron.log` / `backup_task.log`

### Backup Contents
Each backup ZIP contains:
- All source code
- Configuration files
- Documentation
- User preferences (if enabled)
- Database files (if enabled)

Excluded by default:
- `node_modules/`, `__pycache__/`
- `*.log`, `*.tmp` files
- Build artifacts (`dist/`, `.next/`)
- Git repository (`.git/`)

## 🧪 Testing

### Python Tests
```bash
# Test basic functionality
python backup_scheduler.py --test

# Test with custom directory
python backup_scheduler.py --test --backup-dir ./test_backups

# Test continuous mode (Ctrl+C to stop)
python backup_scheduler.py --max-backups 5
```

### JavaScript Tests
```bash
cd development_v2/typescript_version

# Test backup creation
npm run backup:test

# Test with custom options
node backup-scheduler.js --test --backup-dir ../test_backups
```

## 🚨 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.x from python.org
- Or use `python3` instead of `python`

**"Google Drive authentication failed"**
- Ensure `credentials.json` is in project root
- Check Google Cloud Console API settings
- Try deleting `token.json` and re-authenticating

**"Permission denied" (Linux/macOS)**
- Make scripts executable: `chmod +x setup_backup_cron.sh`
- Run setup as user with cron access

**"Access denied" (Windows)**
- Run setup script as Administrator
- Check Task Scheduler permissions

### Backup Verification
```bash
# Check backup directory
ls -la ~/backups/valley_snow_calc/

# Verify latest backup
unzip -l ~/backups/valley_snow_calc/valley_snow_calc_backup_*.zip | head -20

# Check log files
tail -f ~/backups/valley_snow_calc/backup_scheduler.log
```

## 🔄 Backup Rotation

- **Default**: Keep last 24 backups (1 day of hourly backups)
- **Configurable**: Change `maxLocalBackups` in config
- **Automatic**: Old backups deleted automatically
- **Cloud**: Backups remain in Google Drive until manually deleted

## 🛡️ Security Notes

- **Local backups**: Stored in user home directory
- **Cloud backups**: Protected by Google account security
- **Credentials**: `credentials.json` should not be committed to version control
- **Logs**: May contain file paths - review before sharing

## 📈 Performance

- **Compression**: ~60-80% size reduction
- **Speed**: Typically 10-30 seconds for full project backup
- **Storage**: ~50-200MB per backup (depending on project size)
- **Network**: Cloud upload adds 30-60 seconds depending on file size

## 🎯 Best Practices

1. **Test regularly**: Run `--test` to verify backup integrity
2. **Monitor logs**: Check for errors in backup logs
3. **Verify restores**: Periodically test backup restoration
4. **Keep credentials secure**: Don't commit Google API credentials
5. **Monitor storage**: Watch backup directory size
6. **Offsite backup**: Use cloud upload for disaster recovery

## 📞 Support

For issues with the backup system:
1. Check log files for error messages
2. Run test mode to isolate problems
3. Verify configuration file syntax
4. Ensure proper permissions on backup directories


