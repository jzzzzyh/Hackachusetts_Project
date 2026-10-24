# Dev Branch Auto Sync Setup

Your dev branch is now configured for **automatic push and pull**.

## How It Works

### 🤖 Automatic (Default)
Every time you **save a file** in the editor, the hook runs:
1. Fetches latest from `origin/dev`
2. Pulls changes (rebases if possible, merges otherwise)
3. Stages your local changes
4. Commits with timestamp
5. Pushes to `origin/dev`

**You don't need to do anything** — just save files, and they sync automatically.

### 🖱️ Manual
Run this anytime you want to force a sync:

```bash
cd /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project
python3 scripts/auto_sync_dev.py
```

Output example:
```
🔄 Dev Branch Auto Sync
==================================================
✅ On branch: dev
📥 Fetching from remote...
✅ Fetched latest from origin/dev
⬇️  Pulling changes...
✅ Pulled latest changes
🔍 Checking for changes...
📝 Found changes:
M  data/bprd_trees.csv
D  src/old_script.py
?? notebooks/new_analysis.ipynb

📦 Staging changes...
✅ Staged all changes
💬 Committing: Auto-sync dev branch [2026-10-24 14:32:15]
✅ Committed changes
📤 Pushing to origin/dev...
✅ Pushed to origin/dev
==================================================
✅ Sync complete!
```

---

## Configuration

### Kiro Hook
- **Location:** `.kiro/hooks/auto-sync-dev-on-save.json`
- **Trigger:** `PostFileSave` (runs after any file save)
- **Timeout:** 60 seconds
- **Status:** ✅ Active on next session start

### Manual Script
- **Location:** `scripts/auto_sync_dev.py`
- **Executable:** `python3 scripts/auto_sync_dev.py`
- **Safe:** Only commits/pushes if there are changes

---

## What Gets Synced

✅ **Synced automatically:**
- Python scripts (`.py`)
- Notebooks (`.ipynb`)
- Markdown (`.md`)
- Data files (`.csv`, `.geojson`, `.json`)
- Config files

❌ **NOT synced** (in `.gitignore`):
- `data/raw/` — too large (100+ MB)
- `data/processed/` — too large
- `venv/` — Python virtual environment
- `*.log`, `*.tmp`, `*.cache`

To add new files to sync, make sure they're not in `.gitignore`.

---

## Workflow

### Day-to-Day
1. Edit code/notebooks/data
2. Save (Ctrl+S or Cmd+S)
3. ✨ Automatically synced to GitHub dev branch

### If You Want to Check Status
```bash
# See what's staged/changed
git status

# See commit history
git log --oneline -10

# See what's different from origin/dev
git diff origin/dev
```

### If You Want to Push Specific Files
```bash
# Stage specific file
git add path/to/file.py

# Commit
git commit -m "Your message"

# Push
git push origin dev
```

---

## Troubleshooting

### "Push failed" message in hook
This usually means:
1. You're offline (no internet)
2. GitHub credentials not configured
3. Remote branch has conflicts

**Fix:** Run `python3 scripts/auto_sync_dev.py` manually to see the full error.

### Merge conflicts during pull
If pull fails:
1. The script automatically tries `git merge` as fallback
2. If that fails, you may have conflicting changes
3. **Action:** Resolve conflicts manually:
   ```bash
   # See conflicts
   git status
   
   # Edit files to resolve
   # Then:
   git add .
   git commit -m "Resolved conflicts"
   git push origin dev
   ```

### Disable auto-sync temporarily
**To stop the hook from running:**
- Open `.kiro/hooks/auto-sync-dev-on-save.json`
- Change `"disabled": false` to `"disabled": true`
- Save

**Or delete the hook entirely:**
```bash
rm .kiro/hooks/auto-sync-dev-on-save.json
```

---

## Switching Branches

If you need to switch to `main` or another branch:

```bash
git checkout main
# Auto-sync hook will now operate on main branch
```

The script detects which branch you're on and syncs that branch only.

---

## What Branch Are You On?

```bash
git branch
# Output:
# * dev        ← you're here
#   main
```

---

## Integration with Phases 2–6

During Phase 2 (data fetch), Phase 3 (EDA), etc.:
- You'll edit notebooks and scripts
- Each save → auto-synced to GitHub
- Team members pulling `dev` branch get your updates instantly
- No manual `git push` needed

---

## Questions?

Run a manual sync anytime:
```bash
python3 scripts/auto_sync_dev.py
```

Or check hook logs in Kiro to see what happened.
