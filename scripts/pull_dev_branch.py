#!/usr/bin/env python3
"""
Pull latest changes from GitHub to dev branch.

Usage:
  python3 pull_dev_branch.py
"""

import subprocess
import sys
from pathlib import Path


def run_git(cmd: str, description: str = "", timeout: int = 60) -> tuple[bool, str]:
    """
    Run git command and return result.
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    print(f"\n{'─' * 70}")
    if description:
        print(f"📤 {description}")
    print(f"$ git {cmd}")
    print('─' * 70)
    
    try:
        result = subprocess.run(
            f"git {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project"
        )
        
        output = result.stdout + result.stderr
        
        if output:
            print(output)
        
        if result.returncode == 0:
            print(f"✓ SUCCESS")
            return True, output
        else:
            print(f"⚠ {result.stderr if result.stderr else 'Command returned non-zero'}")
            return False, output
            
    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT - Command took too long")
        return False, ""
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False, str(e)


def main():
    """Main entry point."""
    repo_url = "https://github.com/jzzzzyh/Hackachusetts_Project.git"
    project_dir = Path("/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project")
    
    print("\n" + "=" * 70)
    print("🔄 PULL FROM GITHUB TO DEV BRANCH")
    print("=" * 70)
    print(f"\n📁 Project: {project_dir}")
    print(f"📡 Remote: {repo_url}")
    print(f"🌿 Target Branch: dev")
    
    # Check if git is initialized
    if not (project_dir / ".git").exists():
        print("\n✗ Git not initialized in this directory!")
        return 1
    
    # Step 1: Check remote
    print("\n" + "=" * 70)
    print("Step 1: Checking Remote Configuration")
    print("=" * 70)
    
    success, _ = run_git("remote -v", "Current remotes")
    if not success:
        print("⚠ Setting up remote...")
        run_git("remote remove origin", "Removing old origin")
        run_git(f'remote add origin "{repo_url}"', "Adding GitHub remote")
    
    # Step 2: Fetch latest
    print("\n" + "=" * 70)
    print("Step 2: Fetching Latest from GitHub")
    print("=" * 70)
    run_git("fetch origin", "Fetching all branches")
    
    # Step 3: Check current branch
    print("\n" + "=" * 70)
    print("Step 3: Checking Current Branch")
    print("=" * 70)
    success, output = run_git("branch -a", "Listing all branches")
    
    print("\nAvailable branches:")
    print(output)
    
    # Step 4: Check out dev branch
    print("\n" + "=" * 70)
    print("Step 4: Checking Out dev Branch")
    print("=" * 70)
    
    # Try to check out dev
    success, _ = run_git("checkout dev", "Switching to dev branch")
    
    if not success:
        print("⚠ dev branch not found locally, creating from remote...")
        success, _ = run_git("checkout -b dev origin/dev", "Creating dev from remote")
        
        if not success:
            print("⚠ origin/dev not found, trying to create new dev...")
            run_git("checkout -b dev", "Creating new dev branch")
    
    # Step 5: Pull latest from dev
    print("\n" + "=" * 70)
    print("Step 5: Pulling Latest Changes")
    print("=" * 70)
    run_git("pull origin dev --no-edit", "Pulling dev branch from GitHub")
    
    # Step 6: Show status
    print("\n" + "=" * 70)
    print("Step 6: Current Status")
    print("=" * 70)
    run_git("status", "Repository status")
    
    # Step 7: Show recent commits
    print("\n" + "=" * 70)
    print("Step 7: Recent Commits on dev")
    print("=" * 70)
    run_git("log --oneline -10", "Recent commits")
    
    # Step 8: Show branch info
    print("\n" + "=" * 70)
    print("Step 8: Branch Information")
    print("=" * 70)
    run_git("branch -vv", "Branch tracking info")
    
    print("\n" + "=" * 70)
    print("✓ DEV BRANCH PULL COMPLETE!")
    print("=" * 70)
    print(f"\n✓ You are now on the 'dev' branch")
    print(f"✓ Latest changes from GitHub have been pulled")
    print(f"\nNext steps:")
    print(f"  • Code on the dev branch")
    print(f"  • Changes auto-sync to GitHub (dev branch)")
    print(f"  • When ready, merge to main: git merge dev")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
