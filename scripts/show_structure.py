#!/usr/bin/env python3
"""
Display the project folder structure using os.walk.

Shows the organized project layout for verification.
"""

import os
from pathlib import Path


def show_tree(startpath, prefix="", ignore_dirs={'.git', '__pycache__', '.pytest_cache', '.venv', 'venv'}):
    """
    Recursively display directory tree structure.
    
    Args:
        startpath: Root directory to display
        prefix: Prefix for tree formatting
        ignore_dirs: Directories to skip
    """
    contents = {}
    
    # Walk the directory
    for dirpath, dirnames, filenames in os.walk(startpath):
        # Remove ignored directories from the walk
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        # Calculate relative path
        level = dirpath.replace(startpath, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(dirpath)}/')
        
        # Filter and sort files
        subindent = ' ' * 2 * (level + 1)
        
        # Show directories first
        for dirname in sorted(dirnames):
            if dirname not in ignore_dirs:
                continue_str = '├── '
                print(f'{subindent}{continue_str}{dirname}/')
        
        # Then show files
        for filename in sorted(filenames):
            # Skip common non-essential files
            if filename.startswith('.'):
                continue
            print(f'{subindent}├── {filename}')


def count_files(startpath, ignore_dirs={'.git', '__pycache__', '.pytest_cache'}):
    """
    Count files by type.
    
    Args:
        startpath: Root directory
        ignore_dirs: Directories to skip
        
    Returns:
        Dictionary with counts
    """
    counts = {
        'python': 0,
        'geojson': 0,
        'csv': 0,
        'json': 0,
        'markdown': 0,
        'other': 0
    }
    
    for dirpath, dirnames, filenames in os.walk(startpath):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            
            if filename.endswith('.py'):
                counts['python'] += 1
            elif filename.endswith('.geojson'):
                counts['geojson'] += 1
            elif filename.endswith('.csv'):
                counts['csv'] += 1
            elif filename.endswith('.json'):
                counts['json'] += 1
            elif filename.endswith('.md'):
                counts['markdown'] += 1
            else:
                counts['other'] += 1
    
    return counts


def main():
    """Main entry point."""
    project_path = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print("HACKACHUSETTS PROJECT STRUCTURE")
    print("=" * 70 + "\n")
    
    show_tree(str(project_path))
    
    print("\n" + "=" * 70)
    print("FILE STATISTICS")
    print("=" * 70 + "\n")
    
    counts = count_files(str(project_path))
    
    total = sum(counts.values())
    print(f"Python scripts:     {counts['python']:3d}")
    print(f"GeoJSON files:      {counts['geojson']:3d}")
    print(f"CSV files:          {counts['csv']:3d}")
    print(f"JSON files:         {counts['json']:3d}")
    print(f"Markdown docs:      {counts['markdown']:3d}")
    print(f"Other files:        {counts['other']:3d}")
    print(f"{'-' * 35}")
    print(f"Total:              {total:3d}")
    
    print("\n" + "=" * 70)
    print("FOLDER ORGANIZATION SUMMARY")
    print("=" * 70 + "\n")
    
    print("✓ data/       - Raw data files (geojson, csv, json)")
    print("✓ scripts/    - Python data processing scripts")
    print("✓ output/     - Model predictions and results")
    print("✓ notebooks/  - Jupyter analysis and exploration")
    print("✓ Root        - Documentation, config, and README")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
