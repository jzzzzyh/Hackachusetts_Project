#!/usr/bin/env python3
"""
Automatic git sync script for Hackachusetts project.

This script:
1. Pulls latest changes from remote
2. Stages all changes
3. Commits with timestamp
4. Pushes to remote

Can be run manually or via cron/scheduler.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """
    Run a shell command and report results.
    
    Args:
        cmd: Command to run
        description: Description for logging
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"📤 {description}")
    print('=' * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout)
            print(f"✓ {description} - SUCCESS")
            return True
        else:
            print(f"⚠ {description} - WARNING")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return True  # Don't fail on warnings
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False


def get_git_config(key: str) -> str:
    """Get git configuration value."""
    try:
        result = subprocess.run(
            f"git config {key}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None


def auto_sync(project_dir: Path = None) -> bool:
    """
    Automatically sync git repository (pull, stage, commit, push).
    
    Args:
        project_dir: Project directory (default: current directory)
        
    Returns:
        True if all operations succeeded, False otherwise
    """
    if project_dir is None:
        project_dir = Path(__file__).parent.parent
    
    # Change to project directory
    import os
    os.chdir(project_dir)
    
    print("\n" + "=" * 60)
    print("🔄 HACKACHUSETTS AUTO SYNC")
    print("=" * 60)
    print(f"📁 Project: {project_dir}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check git configuration
    remote_url = get_git_config("remote.origin.url")
    if remote_url:
        print(f"📡 Remote: {remote_url}")
    
    # 1. Pull latest changes
    if not run_command("git pull origin main --no-edit || git pull origin master --no-edit", 
                       "Pulling latest changes"):
        print("⚠ Pull failed, but continuing...")
    
    # 2. Stage all changes
    if not run_command("git add -A", "Staging all changes"):
        print("⚠ Staging failed, but continuing...")
    
    # 3. Check if there are changes to commit
    result = subprocess.run("git diff --cached --quiet", shell=True)
    has_changes = result.returncode != 0
    
    if has_changes:
        # 4. Commit with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Auto sync: {timestamp}"
        
        if not run_command(f'git commit -m "{commit_msg}"', "Committing changes"):
            print("✗ Commit failed")
            return False
        
        # 5. Push to remote
        if not run_command("git push origin main || git push origin master", "Pushing to remote"):
            print("✗ Push failed")
            return False
    else:
        print("\n✓ No changes to commit - repository up to date")
    
    print("\n" + "=" * 60)
    print("✓ SYNC COMPLETE")
    print("=" * 60 + "\n")
    
    return True


def setup_cron(interval_minutes: int = 30) -> None:
    """
    Setup automatic sync via cron job.
    
    Args:
        interval_minutes: How often to run sync (default: 30 minutes)
    """
    project_path = Path(__file__).parent.parent
    script_path = Path(__file__).resolve()
    
    cron_entry = f"*/{interval_minutes} * * * * /usr/bin/python3 {script_path} >> {project_path}/auto_sync.log 2>&1"
    
    print(f"\nTo setup automatic sync every {interval_minutes} minutes, add this to crontab:")
    print(f"  crontab -e")
    print(f"  # Then add this line:")
    print(f"  {cron_entry}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automatic git sync for Hackachusetts project"
    )
    parser.add_argument(
        "--cron",
        type=int,
        metavar="MINUTES",
        help="Setup cron job to run every N minutes"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Project directory (default: script parent)"
    )
    
    args = parser.parse_args()
    
    if args.cron:
        setup_cron(args.cron)
    else:
        project_dir = Path(args.dir) if args.dir else None
        success = auto_sync(project_dir)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
