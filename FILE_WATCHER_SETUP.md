# File Watcher System Setup Guide

## Overview

The File Watcher system automatically:
- **Backs up all .py files** every time you save (with 2-second cooldown to avoid duplicates)
- **Auto-commits changes to Git** when files are saved
- **Keeps 30 minutes of backups** (automatically cleans up older backups)
- **Runs automatically** when you start the application

## Installation

1. **Install the watchdog library:**
   ```bash
   pip install watchdog
   ```
   
   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

## How It Works

### Automatic Startup
When you run `python main.py`, the file watcher automatically starts in the background.

### File Backups
- Every time you save a `.py` file, it's automatically backed up to:
  ```
  auto_backups/file_watcher/YYYY-MM-DD_HH-MM-SS/filename.py
  ```
- Backups preserve directory structure
- Old backups (older than 30 minutes) are automatically deleted

### Auto-Commit
- When you save a `.py` file, it's automatically:
  1. Staged with `git add`
  2. Committed with message: `Auto-save: filename.py`
- Commits are local only (you still need to `git push` manually)
- If there are no changes, it won't create an empty commit

### Logging
- All file watcher activity is logged to: `file_watcher.log`
- You can monitor what's being backed up and committed

## Manual Control

### Start File Watcher Manually
```bash
python file_watcher.py
```

### Start in Background
```bash
python file_watcher.py --background
```

### Disable Auto-Commit
```bash
python file_watcher.py --no-auto-commit
```

## Recovery

### Restore from Backup
1. Navigate to `auto_backups/file_watcher/`
2. Find the timestamped folder closest to when you made your changes
3. Copy the file back to its original location

### View Recent Commits
```bash
git log --oneline -20
```

### Revert to Previous Commit
```bash
git log --oneline
git checkout <commit-hash>
```

## Troubleshooting

### File Watcher Not Starting
- Check if `watchdog` is installed: `pip list | grep watchdog`
- Check `file_watcher.log` for errors
- Make sure you're in the project root directory

### Auto-Commit Not Working
- Check if you're in a Git repository: `git status`
- Check `file_watcher.log` for Git errors
- Make sure files are tracked by Git (or they'll be auto-added)

### Too Many Commits
- You can squash commits before pushing:
  ```bash
  git rebase -i HEAD~10  # Squash last 10 commits
  ```

### Backups Taking Too Much Space
- Backups older than 30 minutes are automatically deleted
- You can manually clean up: `rm -rf auto_backups/file_watcher/`

## Configuration

The file watcher is configured in `file_watcher.py`:
- **Backup cooldown**: 2 seconds (prevents duplicate backups)
- **Backup retention**: 30 minutes
- **Auto-commit**: Enabled by default

To modify these settings, edit `file_watcher.py`:
- `backup_cooldown` in `PythonFileHandler.__init__`
- `timedelta(minutes=30)` in `cleanup_old_backups()`
- `auto_commit=True` in `FileWatcher.__init__`
