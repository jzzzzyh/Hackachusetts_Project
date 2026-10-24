#!/usr/bin/env python3
"""
Auto Sync Dev Branch
====================
Automatically pull from dev, then push local changes to dev.

Run manually: python3 scripts/auto_sync_dev.py
Or configure to run automatically via Kiro hook.

This script:
1. Fetches latest from remote
2. Rebases dev branch (or merges if rebase fails)
3. Stages all changes
4. Commits with timestamp
5. Pushes to dev branch

Safe: only syncs if there are actual changes to commit.
"""

import subprocess
import sys
from datetime import datetime

def run_cmd(cmd, check=True):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=check
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        print(f"Error running command: {cmd}")
        print(f"Exception: {e}")
        return 1, "", str(e)

def sync_dev_branch():
    """Pull + push dev branch."""
    
    print("🔄 Dev Branch Auto Sync")
    print("=" * 50)
    
    # Step 1: Check we're on dev
    code, branch, _ = run_cmd("git rev-parse --abbrev-ref HEAD")
    if branch != "dev":
        print(f"❌ Not on dev branch (current: {branch})")
        return False
    print(f"✅ On branch: {branch}")
    
    # Step 2: Fetch latest
    print("\n📥 Fetching from remote...")
    code, out, err = run_cmd("git fetch origin dev")
    if code != 0:
        print(f"⚠️  Fetch warning: {err}")
    else:
        print("✅ Fetched latest from origin/dev")
    
    # Step 3: Pull (rebase preferred)
    print("\n⬇️  Pulling changes...")
    code, out, err = run_cmd("git pull --rebase origin dev", check=False)
    if code != 0:
        print(f"⚠️  Rebase conflict, falling back to merge...")
        run_cmd("git rebase --abort", check=False)
        code, out, err = run_cmd("git pull origin dev", check=False)
        if code != 0:
            print(f"❌ Pull failed: {err}")
            return False
    print("✅ Pulled latest changes")
    
    # Step 4: Check for unstaged changes
    print("\n🔍 Checking for changes...")
    code, status, _ = run_cmd("git status --porcelain")
    
    if not status:
        print("✅ No changes to commit")
        return True
    
    print(f"📝 Found changes:\n{status}")
    
    # Step 5: Stage all changes
    print("\n📦 Staging changes...")
    code, out, err = run_cmd("git add -A")
    if code != 0:
        print(f"❌ Stage failed: {err}")
        return False
    print("✅ Staged all changes")
    
    # Step 6: Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Auto-sync dev branch [{timestamp}]"
    print(f"\n💬 Committing: {commit_msg}")
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"⚠️  Commit failed (may be nothing to commit): {err}")
    else:
        print("✅ Committed changes")
    
    # Step 7: Push
    print("\n📤 Pushing to origin/dev...")
    code, out, err = run_cmd("git push origin dev")
    if code != 0:
        print(f"❌ Push failed: {err}")
        return False
    print("✅ Pushed to origin/dev")
    
    print("\n" + "=" * 50)
    print("✅ Sync complete!")
    return True

if __name__ == "__main__":
    success = sync_dev_branch()
    sys.exit(0 if success else 1)
