# Automatic Git Sync Guide

Set up automatic push/pull sync for your Hackachusetts project.

## What We Created

### 1. Auto Sync Script
**File:** `scripts/auto_sync.py`

Standalone Python script that:
- Pulls latest changes from remote
- Stages all changes (`git add -A`)
- Commits with timestamp
- Pushes to remote (main or master)

### 2. Kiro Hook
**File:** `.kiro/hooks/auto_git_sync.json`

Automatically syncs on every file save in Kiro IDE:
- Runs after each file save
- Adds, commits, and pushes
- Non-blocking (won't interrupt your work)

## Setup Options

### Option 1: Manual Sync (Simplest)

Run sync manually whenever you want:

```bash
# From project root
python3 scripts/auto_sync.py

# Or from anywhere
python3 /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project/scripts/auto_sync.py
```

### Option 2: Auto Sync on Save (Already Set Up!)

The Kiro hook is already configured. Every time you save a file in the IDE:
- Changes are automatically staged
- Committed with timestamp
- Pushed to remote

**Happens silently in background - no interruption to your work**

### Option 3: Scheduled Sync (Cron Job)

Set up automatic sync every 30 minutes:

```bash
# Setup cron
python3 scripts/auto_sync.py --cron 30

# Or manually edit crontab
crontab -e

# Add this line (adjusts path as needed):
*/30 * * * * /usr/bin/python3 /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project/scripts/auto_sync.py >> /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project/auto_sync.log 2>&1
```

**This runs every 30 minutes automatically**

### Option 4: Combined Approach (Recommended)

1. **Kiro hook for save events** (already active)
   - Auto-syncs on every file save in IDE
   
2. **Cron job as fallback**
   - Ensures sync even if IDE sync fails
   - Run every 60 minutes

```bash
# Setup cron fallback (run once)
python3 scripts/auto_sync.py --cron 60
```

## How It Works

### Auto Sync Script Flow

```
1. Pull latest from remote
   └─ Gets any changes from other devices/collaborators

2. Stage all changes
   └─ git add -A (includes all modified/new/deleted files)

3. Check for changes
   └─ Only commits if something changed

4. Commit with timestamp
   └─ Message: "Auto sync: 2026-10-24 15:30:45"

5. Push to remote
   └─ Pushes to main or master (auto-detects)

Result: ✓ Everything synced!
```

### What Gets Synced

✓ **Included:**
- All Python scripts
- All documentation
- Configuration files
- Test data

✗ **Excluded (via .gitignore):**
- Large data files (100+ MB)
- Virtual environments
- Cache files
- `.DS_Store` files

## Usage Examples

### Run Manual Sync

```bash
python3 scripts/auto_sync.py
```

Output:
```
============================================================
🔄 HACKACHUSETTS AUTO SYNC
============================================================
📁 Project: /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project
⏰ Time: 2026-10-24 15:45:30

📤 Pulling latest changes
✓ Already up to date

📤 Staging all changes
✓ Staging - SUCCESS

📤 Committing changes
✓ Committing: Auto sync: 2026-10-24 15:45:30
✓ Committing - SUCCESS

📤 Pushing to remote
✓ Pushing to remote - SUCCESS

============================================================
✓ SYNC COMPLETE
============================================================
```

### Check Git Status

```bash
cd /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project
git status
git log --oneline -5  # See recent commits
```

### View Sync Logs (if using cron)

```bash
tail -f /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project/auto_sync.log
```

## Current Setup

### ✓ Already Configured

1. **Kiro Hook:** `.kiro/hooks/auto_git_sync.json`
   - Trigger: PostFileSave
   - Action: Git add → commit → push
   - Status: ACTIVE (starts next session)

2. **Auto Sync Script:** `scripts/auto_sync.py`
   - Ready to use manually
   - Ready for cron scheduling
   - Supports all git branches

### Optional: Add Cron Job

```bash
python3 scripts/auto_sync.py --cron 60
```

## Best Practices

### ✓ DO

- Run `python3 scripts/auto_sync.py` after major changes
- Let Kiro hook auto-sync on saves
- Use cron job as fallback
- Check git log occasionally: `git log --oneline -10`

### ✗ DON'T

- Don't push large data files (use .gitignore)
- Don't manually edit .git directory
- Don't force push without understanding
- Don't ignore merge conflicts

## Troubleshooting

### "Nothing to commit"
Normal - means repo is already up to date. No action needed.

### "Push rejected"
Usually means remote changed. Solution:
```bash
git pull origin main  # Pull first
git push origin main  # Then push
```

### "Permission denied"
Check SSH key or credentials:
```bash
git config --list | grep remote.origin.url
ssh -T git@github.com  # Test GitHub connection
```

### Large file warnings
These are normal. Files in `.gitignore` are excluded:
```bash
# Check what's being ignored
git check-ignore -v data/mbta_bus_shapes.geojson
```

## Complete Workflow

### Daily Development

```bash
# Morning - pull latest
python3 scripts/auto_sync.py

# During the day - Kiro auto-syncs on every save

# Evening - final sync
python3 scripts/auto_sync.py

# Or just keep working - Kiro will sync on each save!
```

### After Major Changes

```bash
# Manual sync to ensure everything is pushed
python3 scripts/auto_sync.py

# Verify
git log --oneline -1  # See your latest commit
git status            # Should say "nothing to commit"
```

### Collaborating

```bash
# Start session
python3 scripts/auto_sync.py  # Pull any teammate changes

# Work normally (Kiro auto-syncs)

# End session
python3 scripts/auto_sync.py  # Final push
```

## Command Reference

| Command | Purpose |
|---------|---------|
| `python3 scripts/auto_sync.py` | Manual one-time sync |
| `python3 scripts/auto_sync.py --cron 30` | Setup 30-min auto-sync |
| `git status` | Check current state |
| `git log --oneline -5` | See recent commits |
| `git pull` | Pull without pushing |
| `git push` | Push without pulling |
| `tail -f auto_sync.log` | Watch cron logs |

## Files Created/Modified

✓ **Created:**
- `scripts/auto_sync.py` — Main sync script
- `.kiro/hooks/auto_git_sync.json` — Kiro auto-sync hook
- `GIT_SYNC_GUIDE.md` — This guide

✓ **Unchanged:**
- `.gitignore` — Already configured
- `requirements.txt` — No changes
- All project files

## Next Steps

### Immediate

1. ✓ Kiro hook is already active (next session)
2. Optional: Setup cron job
   ```bash
   python3 scripts/auto_sync.py --cron 60
   ```

### Integration

- Works with all git workflows
- Compatible with GitHub, GitLab, Bitbucket
- Works offline (syncs when network available)
- Non-blocking (won't interrupt IDE work)

## Summary

You now have **3 ways to keep your repo synced:**

1. **Kiro Hook** ✓ (Already active)
   - Automatic on every file save
   - Runs silently in background

2. **Manual Script** (Use anytime)
   ```bash
   python3 scripts/auto_sync.py
   ```

3. **Cron Job** (Optional)
   - Set and forget
   - Runs every 30-60 minutes

**Your project stays synced automatically! 🎉**

---

Need help? Check troubleshooting section above.
