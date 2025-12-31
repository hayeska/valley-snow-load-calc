# Valley Snow Load Calculator - Crash Recovery Guide

Complete guide for recovering from crashes, data loss, and system failures.

## 🚨 Quick Recovery Commands

### Immediate Recovery (Recommended)
```bash
# Interactive recovery with guided options
python crash_recovery.py

# Automatic recovery attempt
python crash_recovery.py --recover

# Scan for recovery options without acting
python crash_recovery.py --scan
```

### Data Merging
```bash
# Merge state backup with auto-backup data
python data_merge_utilities.py --merge state.backup.json auto_backups/2025-12-31_13-45-53/

# Analyze backup compatibility before merging
python data_merge_utilities.py --analyze state.backup.json auto_backups/2025-12-31_13-45-53/
```

### Git Operations
```bash
# Revert to safe commit (use hash from recovery scan)
python crash_recovery.py --revert dc92ee8

# Check Git status
git status
git log --oneline -10
```

## 🔍 Recovery System Overview

### What Gets Monitored
- **Crash Flags**: `.crash` file presence indicates unclean shutdown
- **Auto-Save State**: `state.backup.json` contains complete application state
- **Auto-Backups**: `auto_backups/` directory with timestamped partial data
- **Git History**: Safe revert points with risk assessment
- **File Modifications**: Uncommitted changes that may need preservation

### Recovery Priority Order
1. **State Backup** (highest priority - complete application state)
2. **Auto-Backup Merge** (combine multiple partial backups)
3. **Git Revert** (rollback to last known good commit)
4. **Manual Recovery** (guided reconstruction from available data)

## 📋 Recovery Scenarios

### Scenario 1: Clean Crash Recovery
**Symptoms**: Application crashed, `.crash` file exists, backups available
```bash
$ python crash_recovery.py
🚨 Valley Snow Load Calculator - Crash Recovery System
Crash Detected: Yes
Crash Time: 2025-12-31T14:30:00

Recommendations:
• 🔴 CRITICAL: Crash detected - immediate recovery recommended
• ✅ Recommended: Restore from state.backup.json (most complete recovery)
• ✅ Alternative: Use latest auto-backup (2025-12-31_13-45-53)
```

**Recovery Steps:**
1. Run `python crash_recovery.py`
2. Choose option 1 (state backup) or 2 (auto-backup)
3. System automatically restores data
4. Remove crash flag and restart application

### Scenario 2: Data Loss Recovery
**Symptoms**: Lost work, no crash flag, partial backups available
```bash
$ python data_merge_utilities.py --analyze auto_backups/2025-12-31_13-45-53/ auto_backups/2025-12-31_14-15-30/
Compatibility Score: 0.85
Recommended Strategy: primary_override
```

**Recovery Steps:**
1. Analyze backup compatibility
2. Merge compatible backups
3. Review merged data
4. Restore to application

### Scenario 3: Git Repository Issues
**Symptoms**: Repository corruption, merge conflicts, accidental commits
```bash
$ python crash_recovery.py --scan
Git Revert Options:
  1. 🟢 LOW RISK: docs: update README with backup instructions
  2. 🟢 LOW RISK: feat: implement auto-save protocol
  3. 🟡 MEDIUM RISK: feat: add TypeScript implementation
```

**Recovery Steps:**
1. Identify safe revert point
2. Create backup branch if needed
3. Revert to safe commit
4. Reapply lost work manually

## 🔧 Advanced Recovery Techniques

### Manual Data Reconstruction
When automatic recovery isn't sufficient:

1. **Identify Data Sources**
   ```bash
   find . -name "*.json" -o -name "*.backup" | head -20
   ```

2. **Compare Backup Versions**
   ```bash
   python data_merge_utilities.py --analyze state.backup.json auto_backups/*/
   ```

3. **Interactive Merging**
   ```bash
   python data_merge_utilities.py --merge primary.json secondary.json --output merged.json
   python data_merge_utilities.py --resolve-conflicts merged.json
   ```

### Git Recovery Options
```bash
# Create recovery branch
git checkout -b recovery_attempt_$(date +%Y%m%d_%H%M%S)

# Reset to safe point but keep changes staged
git reset --soft dc92ee8

# Cherry-pick good commits
git cherry-pick abc123 def456

# Reconstruct lost work from backups
# ... manual reconstruction steps ...
```

### Database Recovery (if applicable)
```bash
# For SQLite databases in backups
cp auto_backups/2025-12-31_13-45-53/valley_calc.db recovered.db
sqlite3 recovered.db ".schema"  # Verify integrity
```

## 🛡️ Prevention Strategies

### Regular Backup Verification
```bash
# Test backup system weekly
python test_backup.py

# Verify backup integrity
python backup_scheduler.py --test

# Check recovery system
python test_recovery_system.py
```

### Safe Development Practices
- **Commit Frequently**: Small, atomic commits
- **Use Feature Branches**: Isolate risky changes
- **Backup Before Major Changes**: Run manual backup
- **Test Recovery**: Periodically test restore procedures

### Monitoring Setup
```bash
# Setup automated health checks
crontab -e
# Add: 0 */4 * * * cd /path/to/project && python crash_recovery.py --scan >> recovery_monitor.log
```

## 🔍 Diagnostic Tools

### System Health Check
```bash
# Check all backup systems
python crash_recovery.py --scan

# Verify file integrity
find auto_backups/ -name "*.json" -exec python -m json.tool {} \; > /dev/null

# Git repository health
git fsck --full
git reflog --all
```

### Performance Analysis
```bash
# Check backup sizes over time
du -sh auto_backups/*/

# Monitor recovery time
time python crash_recovery.py --recover
```

### Log Analysis
```bash
# Check recovery logs
tail -f crash_recovery.log

# Analyze backup patterns
grep "Auto-saved" backup_scheduler.log | tail -10

# Monitor for errors
grep "ERROR\|FAIL" *.log
```

## 🚨 Emergency Procedures

### Complete Data Loss
1. **Don't Panic**: Data likely exists in backups
2. **Stop All Changes**: Prevent further data loss
3. **Run Full Scan**:
   ```bash
   python crash_recovery.py --scan > emergency_scan.txt
   ```
4. **Contact Recovery Expert** if automated recovery fails

### Repository Corruption
1. **Backup Current State**:
   ```bash
   cp -r .git .git.backup.$(date +%s)
   ```
2. **Use Recovery Tools**:
   ```bash
   git reflog  # Find last good state
   python crash_recovery.py --revert <safe-commit>
   ```

### Multiple System Failures
1. **Isolate Systems**: Work on one recovery at a time
2. **Document Process**: Keep detailed recovery notes
3. **Test Incrementally**: Verify each recovery step
4. **Have Backup Plan**: Know when to restore from external backups

## 📞 Getting Help

### Built-in Help
```bash
python crash_recovery.py --help
python data_merge_utilities.py --help
```

### Self-Diagnosis
```bash
# Run comprehensive test
python test_recovery_system.py

# Check system compatibility
python -c "import sys; print(f'Python {sys.version}'); import json, os, pathlib; print('Dependencies OK')"
```

### External Resources
- **Git Recovery**: `git help reflog`, `git help reset`
- **Data Recovery**: Professional data recovery services
- **Backup Best Practices**: Review backup_scheduler.py documentation

## 🎯 Success Metrics

### Recovery Completeness
- **Full Recovery**: All data restored automatically
- **Partial Recovery**: Some data restored, manual reconstruction needed
- **Minimal Recovery**: Critical data preserved, major work lost

### Recovery Time Objectives (RTO)
- **Immediate (< 5 min)**: State backup restoration
- **Quick (15-30 min)**: Auto-backup merging
- **Extended (1-4 hours)**: Complex data reconstruction

### Recovery Point Objectives (RPO)
- **Minimal Loss**: Auto-save every 2 minutes
- **Acceptable Loss**: Auto-backup every hour
- **Maximum Loss**: Git commit frequency

## 🔄 Continuous Improvement

### Monitoring Recovery Effectiveness
```bash
# Track recovery success rates
grep "Recovery completed" crash_recovery.log | wc -l

# Monitor backup coverage
find auto_backups/ -type f -name "*.json" | wc -l
```

### Updating Recovery Procedures
- Review recovery logs monthly
- Test recovery procedures quarterly
- Update documentation after incidents
- Train team on recovery procedures

---

**Remember**: Regular testing and preparation are key to successful recovery. The recovery system is designed to be automated and safe, but always have a human in the loop for critical decisions.
