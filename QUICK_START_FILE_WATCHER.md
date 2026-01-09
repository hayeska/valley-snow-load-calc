# Quick Start: File Watcher System

## ✅ System Created!

The File Watcher system has been created and will automatically start when you run the application.

## 📦 Installation Required

**You need to install the `watchdog` library first:**

```bash
py -m pip install watchdog
```

Or if you have `pip` directly:
```bash
pip install watchdog
```

## 🚀 How to Use

1. **Install watchdog** (see above)
2. **Run your application normally:**
   ```bash
   py main.py
   ```
3. **The file watcher starts automatically** - you'll see:
   ```
   Starting file watcher for automatic backups and auto-commit...
   File watcher started successfully.
   ```

## ✨ What Happens Now

### When You Save a .py File:
1. ✅ **Automatic Backup** → Saved to `auto_backups/file_watcher/TIMESTAMP/`
2. ✅ **Auto-Commit** → Committed to Git with message "Auto-save: filename.py"
3. ✅ **Cleanup** → Old backups (30+ minutes) are automatically deleted

### Protection Against Crashes:
- **Every save** = New backup + Git commit
- **30 minutes** of backups kept automatically
- **Recovery**: Copy file from backup folder or `git checkout` to previous commit

## 📁 Backup Location

Backups are stored in:
```
auto_backups/file_watcher/YYYY-MM-DD_HH-MM-SS/filename.py
```

## 📝 Logs

Check `file_watcher.log` to see:
- Which files were backed up
- Which files were committed
- Any errors or warnings

## 🔧 Manual Control

If you want to run the file watcher separately:

```bash
# Run in foreground
py file_watcher.py

# Run in background
py file_watcher.py --background

# Disable auto-commit (backup only)
py file_watcher.py --no-auto-commit
```

## ⚠️ Important Notes

1. **Auto-commits are LOCAL** - You still need to `git push` manually
2. **Backups are separate from Git** - Quick recovery without Git history
3. **2-second cooldown** - Rapid saves won't create duplicate backups
4. **Only .py files** are watched and backed up

## 🆘 Troubleshooting

**File watcher not starting?**
- Make sure `watchdog` is installed: `py -m pip list | findstr watchdog`
- Check `file_watcher.log` for errors

**Too many Git commits?**
- You can squash before pushing: `git rebase -i HEAD~10`

**Need to restore a file?**
- Check `auto_backups/file_watcher/` for timestamped backups
- Or use: `git log` then `git checkout <commit-hash>`

---

**You're all set!** Just install `watchdog` and start coding. Your work will be automatically protected! 🛡️
