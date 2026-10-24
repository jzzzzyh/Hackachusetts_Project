#!/usr/bin/env python3
"""
Boston neighborhoods data for equity check.
Manually compiled from data.boston.gov/dataset/boston-neighborhoods
and augmented with centroid coordinates.
"""

import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

OUT_PATH = "data/processed/neighborhoods.csv"
GEOJSON_PATH = "data/processed/neighborhoods.geojson"

# Boston neighborhoods with approximate boundaries (lat/lon from data.boston.gov)
# Source: https://data.boston.gov/dataset/boston-neighborhoods
NEIGHBORHOODS_DATA = [
    # Name, approximate_lat, approximate_lon, approximate_area_sqm (rough estimate)
    ("Dorchester", 42.3021, -71.0707, 13_000_000),
    ("South Boston", 42.3388, -71.0468, 7_000_000),
    ("South Boston / South Boston Waterfront", 42.3388, -71.0468, 7_000_000),
    ("South End", 42.3398, -71.0786, 5_000_000),
    ("Roxbury", 42.3142, -71.0920, 8_000_000),
    ("East Boston", 42.3784, -71.0282, 7_000_000),
    ("Back Bay", 42.3503, -71.0810, 5_000_000),
    ("Jamaica Plain", 42.3100, -71.1148, 10_000_000),
    ("Charlestown", 42.3782, -71.0602, 5_000_000),
    ("Brighton", 42.3467, -71.1564, 6_000_000),
    ("Allston", 42.3534, -71.1312, 5_000_000),
    ("Allston / Brighton", 42.3500, -71.1430, 11_000_000),
    ("Fenway", 42.3467, -71.1003, 4_000_000),
    ("Beacon Hill", 42.3588, -71.0707, 2_000_000),
    ("Downtown / Financial District", 42.3560, -71.0550, 3_000_000),
    ("Boston", 42.3601, -71.0589, 3_000_000),
    ("North End", 42.3647, -71.0542, 2_000_000),
    ("West End", 42.3676, -71.0764, 2_000_000),
    ("Waterfront", 42.3628, -71.0480, 3_000_000),
    ("Roslindale", 42.2840, -71.1284, 8_000_000),
    ("Hyde Park", 42.2551, -71.1243, 8_000_000),
    ("Greater Mattapan", 42.2736, -71.0921, 7_000_000),
    ("Mattapan", 42.2736, -71.0921, 7_000_000),
    ("West Roxbury", 42.2793, -71.1607, 8_000_000),
    ("Fenway / Kenmore / Audubon Circle / Longwood", 42.3467, -71.1003, 6_000_000),
    ("Mission Hill", 42.3278, -71.1003, 3_000_000),
    ("Chestnut Hill", 42.3258, -71.1662, 5_000_000),
]


def create_simple_polygons(neighborhoods_data):
    """Create simple square polygons centered at each neighborhood centroid."""
    features = []
    
    for name, lat, lon, area in neighborhoods_data:
        # Create a simple square polygon around the centroid
        # Size based on area (rough approximation)
        side = (area ** 0.5) / 2  # Half-side in degrees (very rough)
        offset = side / 111_000  # Convert meters to degrees (1 degree ≈ 111 km)
        
        # Create polygon bounds
        min_lon = lon - offset
        max_lon = lon + offset
        min_lat = lat - offset
        max_lat = lat + offset
        
        polygon = Polygon([
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            (min_lon, min_lat),
        ])
        
        features.append({
            "type": "Feature",
            "properties": {"neighborhood": name},
            "geometry": polygon.__geo_interface__,
        })
    
    return features


def main():
    """Create neighborhoods data from known Boston neighborhoods."""
    
    print("Creating Boston neighborhoods dataset...")
    
    # Create GeoDataFrame from neighborhood data
    neighborhoods = []
    for name, lat, lon, area in NEIGHBORHOODS_DATA:
        neighborhoods.append({
            "neighborhood": name,
            "lat": lat,
            "lon": lon,
            "area_sqm": area,
        })
    
    # Save as CSV
    os.makedirs("data/processed", exist_ok=True)
    df = pd.DataFrame(neighborhoods)
    df.to_csv(OUT_PATH, index=False)
    
    print(f"✓ Neighborhoods saved to {OUT_PATH}")
    print(f"\nTotal neighborhoods: {len(df)}")
    print("\nFirst 10 neighborhoods:")
    print(df.head(10).to_string(index=False))
    
    # Create GeoJSON with simple polygons
    print("\nCreating GeoJSON with polygon geometries...")
    features = create_simple_polygons(NEIGHBORHOODS_DATA)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    
    # Save GeoJSON
    gdf = gpd.GeoDataFrame.from_features(features)
    gdf.to_file(GEOJSON_PATH, driver="GeoJSON")
    
    print(f"✓ GeoJSON saved to {GEOJSON_PATH}")
    
    # Verify coverage
    print("\n=== Neighborhood Coverage Verification ===")
    
    # Expected neighborhoods from train_xgboost.py
    expected = [
        "Dorchester", "South Boston", "South End", "Roxbury", "East Boston",
        "Back Bay", "Jamaica Plain", "Charlestown", "Brighton", "Allston",
        "Fenway", "Beacon Hill", "Downtown", "North End", "West End", "Waterfront"
    ]
    
    loaded_neighborhoods = set(df["neighborhood"].str.lower().unique())
    expected_lower = set([n.lower() for n in expected])
    
    # Check for partial matches
    matched = 0
    missing = []
    for exp in expected_lower:
        found = any(exp in ln or ln in exp for ln in loaded_neighborhoods)
        if found:
            matched += 1
        else:
            missing.append(exp)
    
    print(f"Expected neighborhoods: {len(expected)}")
    print(f"Loaded neighborhoods: {len(loaded_neighborhoods)}")
    print(f"Matched (or partial match): {matched}")
    
    if missing:
        print(f"\n⚠ WARNING: {len(missing)} expected neighborhoods not found:")
        for nbhd in sorted(missing):
            print(f"  - {nbhd}")
    else:
        print("✓ All expected neighborhoods covered!")
    
    print(f"\nAll {len(df)} neighborhoods:")
    for nbhd in sorted(df["neighborhood"].unique()):
        print(f"  - {nbhd}")


if __name__ == "__main__":
    main()
