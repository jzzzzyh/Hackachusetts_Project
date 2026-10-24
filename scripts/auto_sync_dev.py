#!/usr/bin/env python3
"""
Automatic git sync for dev branch.

This script:
1. Pulls latest from dev branch
2. Stages all changes
3. Commits with timestamp
4. Pushes to dev branch

Usage:
  python3 auto_sync_dev.py
  python3 auto_sync_dev.py --cron 30  # Setup 30-min auto-sync
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and report results."""
    print(f"\n{'=' * 60}")
    print(f"📤 {description}")
    print('=' * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✓ {description} - SUCCESS")
            return True
        else:
            print(f"⚠ {description} - WARNING")
            if result.stderr:
                print("STDERR:", result.stderr)
            return True
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False


def auto_sync_dev(project_dir: Path = None) -> bool:
    """Automatically sync dev branch (pull, stage, commit, push)."""
    if project_dir is None:
        project_dir = Path("/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project")
    
    import os
    os.chdir(project_dir)
    
    print("\n" + "=" * 60)
    print("🔄 AUTO SYNC - DEV BRANCH")
    print("=" * 60)
    print(f"📁 Project: {project_dir}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌿 Branch: dev")
    
    # 1. Ensure on dev branch
    run_command("git checkout dev", "Switching to dev branch")
    
    # 2. Pull latest changes
    run_command("git pull origin dev --no-edit", "Pulling latest from dev")
    
    # 3. Stage all changes
    run_command("git add -A", "Staging all changes")
    
    # 4. Check if there are changes to commit
    result = subprocess.run("git diff --cached --quiet", shell=True)
    has_changes = result.returncode != 0
    
    if has_changes:
        # 5. Commit with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Auto sync (dev): {timestamp}"
        
        if not run_command(f'git commit -m "{commit_msg}"', "Committing changes"):
            print("✗ Commit failed")
            return False
        
        # 6. Push to dev
        if not run_command("git push origin dev", "Pushing to dev branch"):
            print("✗ Push failed")
            return False
    else:
        print("\n✓ No changes to commit - dev branch up to date")
    
    print("\n" + "=" * 60)
    print("✓ SYNC COMPLETE (dev branch)")
    print("=" * 60 + "\n")
    
    return True


def setup_cron(interval_minutes: int = 30) -> None:
    """Setup automatic sync via cron job."""
    project_path = Path("/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project")
    script_path = Path(__file__).resolve()
    
    cron_entry = f"*/{interval_minutes} * * * * /usr/bin/python3 {script_path} >> {project_path}/auto_sync_dev.log 2>&1"
    
    print(f"\nTo setup automatic sync every {interval_minutes} minutes, add this to crontab:")
    print(f"  crontab -e")
    print(f"  # Then add this line:")
    print(f"  {cron_entry}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automatic git sync for dev branch"
    )
    parser.add_argument(
        "--cron",
        type=int,
        metavar="MINUTES",
        help="Setup cron job to run every N minutes"
    )
    
    args = parser.parse_args()
    
    if args.cron:
        setup_cron(args.cron)
    else:
        success = auto_sync_dev()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
