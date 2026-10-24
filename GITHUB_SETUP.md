# GitHub Setup & Pull Guide

Connect your local project to GitHub and sync with the remote repository.

## Quick Start

### Option 1: Python Script (Recommended)

```bash
cd /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project
python3 scripts/setup_github_and_pull.py
```

This will:
1. ✓ Setup GitHub remote
2. ✓ Fetch latest changes
3. ✓ Pull to local repository
4. ✓ Show status and recent commits

### Option 2: Bash Script

```bash
bash scripts/setup_remote_and_pull.sh
```

### Option 3: Manual Commands

```bash
cd /Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project

# Remove old remote if exists
git remote remove origin

# Add GitHub remote
git remote add origin https://github.com/jzzzzyh/Hackachusetts_Project.git

# Fetch latest
git fetch origin

# Pull from main (or master if main doesn't exist)
git pull origin main --no-edit
# Or: git pull origin master --no-edit
```

## GitHub Repository

**URL:** https://github.com/jzzzzyh/Hackachusetts_Project.git

This is your remote repository on GitHub. Your local changes will sync with this.

## What Happens

### When You Run Setup Script

```
1. Remove old origin (if exists)
2. Add GitHub as new remote
3. Fetch latest changes
4. Pull to merge changes
5. Show current status
```

### After Setup

**You can now:**
- ✓ `git push` — Send changes to GitHub
- ✓ `git pull` — Get latest from GitHub
- ✓ `python3 scripts/auto_sync.py` — Auto-sync (push & pull)

## Verify Setup

After running setup, verify:

```bash
# Check remote is configured
git remote -v
# Should show: origin  https://github.com/jzzzzyh/Hackachusetts_Project.git

# Check status
git status
# Should say "Your branch is up to date with 'origin/main'"

# See recent commits
git log --oneline -5
```

## Common Workflows

### First Time Setup
```bash
python3 scripts/setup_github_and_pull.py
```

### Daily Pull Latest
```bash
git pull origin main
# Or: python3 scripts/auto_sync.py
```

### Push Your Changes
```bash
git push origin main
# Or: python3 scripts/auto_sync.py
```

### Auto-Sync (Recommended)
```bash
# One-time setup
python3 scripts/auto_sync.py --cron 60

# Then syncs automatically every 60 minutes + on every file save
```

## Scripts Provided

### setup_github_and_pull.py
- **Purpose:** Setup GitHub remote and pull
- **Usage:** `python3 scripts/setup_github_and_pull.py`
- **What it does:** Configures remote, fetches, pulls, shows status

### setup_remote_and_pull.sh
- **Purpose:** Bash version of GitHub setup
- **Usage:** `bash scripts/setup_remote_and_pull.sh`
- **What it does:** Same as Python version

### auto_sync.py
- **Purpose:** Automatic sync (push & pull)
- **Usage:** `python3 scripts/auto_sync.py`
- **What it does:** Pull, add, commit, push (all-in-one)

## Status After Setup

✓ **Local Repository:** Connected to GitHub
✓ **Remote URL:** `https://github.com/jzzzzyh/Hackachusetts_Project.git`
✓ **Ready for:** Push, pull, sync operations
✓ **Auto-sync:** Configured on file save + optional cron job

## Troubleshooting

### "Connection refused"
- Check internet connection
- Verify GitHub URL is correct
- Try: `git fetch origin` to test connectivity

### "Authentication failed"
- You may need SSH key or GitHub token
- See: https://docs.github.com/en/authentication

### "Merge conflict"
```bash
# Resolve conflicts manually, then:
git add .
git commit -m "Resolved conflicts"
git push
```

### "Branch doesn't exist"
- If `main` doesn't exist, use `master`:
  ```bash
  git pull origin master
  ```

## Next Steps

1. **Run setup:** `python3 scripts/setup_github_and_pull.py`
2. **Verify connection:** `git remote -v`
3. **Start working:** Code normally, changes auto-sync
4. **Optional:** Setup cron for extra reliability

## Integration with Auto-Sync

Your setup now has:
- ✓ Kiro hook — auto-syncs on file save
- ✓ Manual script — sync anytime
- ✓ Cron job — optional automatic sync
- ✓ GitHub remote — syncs with GitHub

Everything is connected and ready!

---

**Questions?** See:
- `AUTO_SYNC_README.md` — Auto-sync guide
- `GIT_SYNC_GUIDE.md` — Detailed git guide
