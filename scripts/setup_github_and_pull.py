#!/usr/bin/env python3
"""
Setup GitHub remote and pull latest changes.

Usage:
  python3 setup_github_and_pull.py
"""

import subprocess
import sys
from pathlib import Path


def run_git(cmd: str, description: str = "") -> bool:
    """Run git command and report result."""
    print(f"\n{'─' * 60}")
    if description:
        print(f"📤 {description}")
    print(f"Command: git {cmd}")
    print('─' * 60)
    
    try:
        result = subprocess.run(
            f"git {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project"
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✓ SUCCESS")
            return True
        else:
            if result.stderr:
                print(f"⚠ {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT - Command took too long")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Main entry point."""
    repo_url = "https://github.com/jzzzzyh/Hackachusetts_Project.git"
    project_dir = Path("/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project")
    
    print("\n" + "=" * 60)
    print("🔄 GITHUB REMOTE SETUP & PULL")
    print("=" * 60)
    print(f"\n📁 Project: {project_dir}")
    print(f"📡 Remote URL: {repo_url}")
    
    # Check if git is initialized
    if not (project_dir / ".git").exists():
        print("\n✗ Git not initialized in this directory!")
        print("Initialize with: git init")
        return 1
    
    # 1. Check current remote
    print("\n" + "=" * 60)
    print("Checking current remote configuration...")
    print("=" * 60)
    run_git("remote -v", "Current remotes")
    
    # 2. Remove old origin if exists
    print("\n" + "=" * 60)
    print("Setting up GitHub remote...")
    print("=" * 60)
    run_git("remote remove origin", "Removing old origin")
    
    # 3. Add new origin
    run_git(f'remote add origin "{repo_url}"', "Adding GitHub remote")
    
    # 4. Verify remote
    run_git("remote -v", "Verifying remote")
    
    # 5. Fetch
    print("\n" + "=" * 60)
    print("Fetching from GitHub...")
    print("=" * 60)
    run_git("fetch origin", "Fetching latest")
    
    # 6. Pull from main or master
    print("\n" + "=" * 60)
    print("Pulling latest changes...")
    print("=" * 60)
    
    # Try main first
    success = run_git("pull origin main --no-edit", "Pulling from 'main' branch")
    
    if not success:
        print("\nMain branch not found, trying master...")
        run_git("pull origin master --no-edit", "Pulling from 'master' branch")
    
    # 7. Show status
    print("\n" + "=" * 60)
    print("Repository Status")
    print("=" * 60)
    run_git("status", "Current status")
    
    # 8. Show recent commits
    print("\n" + "=" * 60)
    print("Recent Commits")
    print("=" * 60)
    run_git("log --oneline -10", "Recent commits")
    
    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nYour repository is now synced with:")
    print(f"  {repo_url}")
    print(f"\nYou can now:")
    print(f"  • Use git push to send changes to GitHub")
    print(f"  • Use git pull to get latest updates")
    print(f"  • Use python3 scripts/auto_sync.py for auto-sync")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
