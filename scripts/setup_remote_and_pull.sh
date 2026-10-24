#!/bin/bash

# Setup GitHub remote and pull latest changes
# Usage: ./scripts/setup_remote_and_pull.sh

REPO_URL="https://github.com/jzzzzyh/Hackachusetts_Project.git"
PROJECT_DIR="/Users/zhouyuhai/Documents/Kiro/Hackachusetts_Project"

echo "=================================================="
echo "Git Remote Setup & Pull"
echo "=================================================="
echo ""
echo "Project: $PROJECT_DIR"
echo "Remote URL: $REPO_URL"
echo ""

cd "$PROJECT_DIR"

# Check current remote
echo "Current remote configuration:"
git remote -v
echo ""

# Add or update origin
echo "Setting up remote origin..."
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"
echo "✓ Remote configured"
echo ""

# Fetch latest
echo "Fetching latest changes..."
git fetch origin
echo "✓ Fetch complete"
echo ""

# Pull from main or master
echo "Pulling latest changes..."
if git show-ref --verify --quiet refs/heads/main; then
    echo "Pulling from 'main' branch..."
    git pull origin main --no-edit
else
    echo "Pulling from 'master' branch..."
    git pull origin master --no-edit
fi

echo ""
echo "✓ Pull complete!"
echo ""
echo "Current status:"
git status
echo ""
echo "Recent commits:"
git log --oneline -5
