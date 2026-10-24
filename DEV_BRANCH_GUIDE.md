# Dev Branch Workflow

Set up and use the dev branch for development work.

## Quick Start

### Pull to dev branch

```bash
python3 scripts/pull_dev_branch.py
```

This will:
1. ✓ Setup GitHub remote (if needed)
2. ✓ Fetch all branches
3. ✓ Create/checkout dev branch
4. ✓ Pull latest changes
5. ✓ Show status and recent commits

## Dev Branch Commands

### One-Time Setup

```bash
python3 scripts/pull_dev_branch.py
```

### Daily Development

```bash
# Pull latest dev branch
python3 scripts/auto_sync_dev.py

# Or manual git
git pull origin dev
```

### After Making Changes

```bash
# Auto-sync (pull → add → commit → push)
python3 scripts/auto_sync_dev.py

# Or manual
git add -A
git commit -m "Your message"
git push origin dev
```

### Setup Automatic Sync (Every 30 min)

```bash
python3 scripts/auto_sync_dev.py --cron 30
```

## Workflow: Dev → Main

### 1. Develop on dev branch
```bash
# Already on dev after setup
git checkout dev
# Make your changes
git add -A
git commit -m "Your feature"
git push origin dev
```

### 2. When ready to merge to main
```bash
# Switch to main
git checkout main

# Merge dev into main
git merge dev

# Push main
git push origin main
```

### 3. Back to dev for next feature
```bash
git checkout dev
git pull origin dev
# Start new feature
```

## Scripts Available

### pull_dev_branch.py
**Purpose:** Initial setup for dev branch
**Usage:** `python3 scripts/pull_dev_branch.py`
**What it does:**
- Sets up GitHub remote
- Fetches all branches
- Creates/checks out dev
- Pulls latest changes
- Shows status

### auto_sync_dev.py
**Purpose:** Auto-sync on dev branch
**Usage:** `python3 scripts/auto_sync_dev.py`
**What it does:**
- Ensures on dev branch
- Pulls latest
- Stages changes
- Commits with timestamp
- Pushes to dev

**Setup auto-sync:** `python3 scripts/auto_sync_dev.py --cron 30`

## Branch Structure

```
GitHub Repository
├── main (production)
│   └── stable, tested code
└── dev (development)
    └── active development
    
Your Local
├── main (synced with main)
└── dev (synced with dev) ← YOU'RE HERE
```

## Typical Day

### Morning
```bash
python3 scripts/auto_sync_dev.py  # Get latest dev changes
```

### During Day
```
Edit files
Save (Kiro auto-syncs if configured)
git push origin dev  # or auto-sync
```

### Evening
```bash
python3 scripts/auto_sync_dev.py  # Final push
```

## Git Commands Reference

| Command | Purpose |
|---------|---------|
| `git checkout dev` | Switch to dev branch |
| `git branch -a` | List all branches |
| `git pull origin dev` | Pull dev from GitHub |
| `git push origin dev` | Push dev to GitHub |
| `git status` | See current state |
| `git log --oneline -5` | See recent commits |
| `git merge main` | Merge main into current (dev) |

## Integration with Auto-Sync

Your setup has:

1. **File Save Hook** (Kiro IDE)
   - Auto-syncs on every save
   - Works on current branch (dev)

2. **Manual Sync Script** (any time)
   - `python3 scripts/auto_sync_dev.py`
   - Specific to dev branch

3. **Scheduled Sync** (optional)
   - `python3 scripts/auto_sync_dev.py --cron 30`
   - Syncs every 30 minutes

## Verify You're on dev

```bash
# Check current branch
git branch
# Should show: * dev

# Or check status
git status
# Should show: On branch dev
```

## If You Accidentally Switch Branches

```bash
# Go back to dev
git checkout dev

# Check you're on dev
git branch
```

## Files Created

✓ **scripts/pull_dev_branch.py**
- Setup script for dev branch

✓ **scripts/auto_sync_dev.py**
- Auto-sync for dev branch
- Can setup cron job

✓ **DEV_BRANCH_GUIDE.md**
- This guide

## Next Steps

1. **Run setup:** `python3 scripts/pull_dev_branch.py`
2. **Verify branch:** `git branch` (should show * dev)
3. **Start coding:** Changes auto-sync to dev
4. **When ready:** Merge to main

## FAQ

### Q: Am I on the dev branch?
**A:** Check with `git branch` - should show `* dev`

### Q: How do I pull dev changes?
**A:** `python3 scripts/auto_sync_dev.py` or `git pull origin dev`

### Q: How do I push dev changes?
**A:** `python3 scripts/auto_sync_dev.py` or `git push origin dev`

### Q: Can I switch to main?
**A:** Yes: `git checkout main` - but always come back to dev

### Q: How do I merge to main?
**A:** 
```bash
git checkout main
git merge dev
git push origin main
```

### Q: Do my auto-sync hooks work on dev?
**A:** Yes! Kiro hook works on whichever branch you're on

## Summary

✓ **Initial Setup:** `python3 scripts/pull_dev_branch.py`
✓ **Daily Sync:** `python3 scripts/auto_sync_dev.py`
✓ **Auto Sync:** `python3 scripts/auto_sync_dev.py --cron 30`

You're now on the dev branch, ready to develop! 🚀

---

See `AUTO_SYNC_README.md` for general auto-sync info.
