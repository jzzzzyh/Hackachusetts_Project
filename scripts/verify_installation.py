#!/usr/bin/env python3
"""
Verify that the environment is set up correctly for Step 1.

Run this before executing the main scripts to check:
- Python version
- Required packages installed
- File structure
- Basic functionality

Usage:
    python3 verify_installation.py
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.11+."""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"  ✗ Python {version.major}.{version.minor} found, but 3.11+ required")
        return False
    
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_packages():
    """Check required packages are installed."""
    print("\nChecking required packages...")
    required = ['requests', 'polyline', 'geopandas', 'pandas', 'shapely']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} — NOT FOUND")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_files():
    """Check script files exist."""
    print("\nChecking script files...")
    scripts = ['fetch_mbta_bus_shapes.py', 'decode_mbta_shapes.py']
    all_exist = True
    
    for script in scripts:
        if Path(script).exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ✗ {script} — NOT FOUND")
            all_exist = False
    
    return all_exist


def check_data_dir():
    """Check data directory exists."""
    print("\nChecking data directory...")
    data_dir = Path('data')
    
    if data_dir.exists():
        print(f"  ✓ data/ directory exists")
        files = list(data_dir.glob('*'))
        if files:
            for f in files:
                if f.name != '.gitkeep':
                    print(f"    - {f.name}")
        return True
    else:
        print(f"  ✗ data/ directory — NOT FOUND")
        return False


def test_polyline_decode():
    """Test basic polyline decoding."""
    print("\nTesting polyline decoding...")
    try:
        import polyline
        
        # Sample encoded polyline
        sample = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        coords = polyline.decode(sample)
        
        if coords:
            print(f"  ✓ Successfully decoded sample polyline")
            print(f"    Sample: {sample}")
            print(f"    Result: {coords}")
            return True
        else:
            print(f"  ✗ Failed to decode sample polyline")
            return False
            
    except Exception as e:
        print(f"  ✗ Error during polyline decode: {e}")
        return False


def test_geojson_creation():
    """Test GeoJSON creation."""
    print("\nTesting GeoJSON creation...")
    try:
        import json
        from shapely.geometry import LineString
        
        # Create a simple LineString
        coords = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
        line = LineString(coords)
        
        # Create GeoJSON
        geojson = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {'id': 'test'},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[lon, lat] for lat, lon in coords]
                }
            }]
        }
        
        json_str = json.dumps(geojson)
        print(f"  ✓ Successfully created valid GeoJSON")
        print(f"    Size: {len(json_str)} bytes")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error creating GeoJSON: {e}")
        return False


def test_geopandas():
    """Test geopandas functionality."""
    print("\nTesting geopandas...")
    try:
        import geopandas as gpd
        import tempfile
        import json
        
        # Create test GeoJSON
        geojson = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'properties': {'id': '1', 'route': 'test'},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[0, 0], [1, 1], [2, 0]]
                }
            }]
        }
        
        # Write to temp file and read with geopandas
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson, f)
            temp_file = f.name
        
        try:
            gdf = gpd.read_file(temp_file)
            print(f"  ✓ Successfully read GeoJSON with geopandas")
            print(f"    Features: {len(gdf)}")
            print(f"    Columns: {gdf.columns.tolist()}")
            print(f"    Geometry type: {gdf.geometry.type.iloc[0]}")
            return True
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"  ✗ Error with geopandas: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("MBTA Bus Shapes — Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_packages),
        ("Script Files", check_files),
        ("Data Directory", check_data_dir),
        ("Polyline Decoding", test_polyline_decode),
        ("GeoJSON Creation", test_geojson_creation),
        ("GeoPandas Integration", test_geopandas),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error during {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Ready to run the scripts.")
        print("\nNext steps:")
        print("  1. python3 fetch_mbta_bus_shapes.py")
        print("  2. python3 decode_mbta_shapes.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please address the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
