#!/usr/bin/env python3
"""
Download Boston neighborhoods shapefile from data.boston.gov and convert to CSV.
Needed for equity check — join segments to neighborhoods.
Source: https://data.boston.gov/dataset/boston-neighborhoods (Shapefile)
"""

import os
import pandas as pd
import geopandas as gpd
import requests
import zipfile
import io
import ssl

# Handle SSL certificate verification issues
ssl._create_default_https_context = ssl._create_unverified_context

# Boston neighborhoods via ArcGIS REST API (GeoJSON output)
# Source: https://data.boston.gov/dataset/boston-neighborhoods
GEOJSON_URL = "https://bostonopendata-boston.opendata.arcgis.com/rest/services/OpenData/boston_neighborhoods/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson"
OUT_PATH = "data/processed/neighborhoods.csv"
GEOJSON_PATH = "data/processed/neighborhoods.geojson"


def download_and_extract_shapefile(url, extract_dir="data/raw"):
    """Download and extract shapefile from URL."""
    
    print(f"Downloading neighborhoods shapefile from data.boston.gov...")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Extract to temporary directory
        os.makedirs(extract_dir, exist_ok=True)
        print(f"Extracting shapefile to {extract_dir}...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_dir)
        
        # Find the .shp file
        shp_file = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(".shp"):
                    shp_file = os.path.join(root, file)
                    break
        
        if not shp_file:
            raise FileNotFoundError("No .shp file found in downloaded archive")
        
        print(f"✓ Found shapefile: {shp_file}")
        return shp_file
    
    except Exception as e:
        print(f"Error downloading shapefile: {e}")
        return None


def main():
    """Download neighborhoods shapefile and convert to usable formats."""
    
    # Try downloading GeoJSON directly first
    print(f"Downloading neighborhoods data from data.boston.gov...")
    try:
        response = requests.get(GEOJSON_URL, timeout=120)
        response.raise_for_status()
        
        print("✓ Downloaded GeoJSON successfully")
        
        # Save and read as GeoDataFrame
        geojson_data = response.json()
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
        
    except Exception as e:
        print(f"Error with GeoJSON endpoint: {e}")
        print("Trying alternative shapefile download...")
        
        # Try shapefile download as fallback
        shp_file = download_and_extract_shapefile(SHAPEFILE_URL)
        if not shp_file:
            return
        
        try:
            gdf = gpd.read_file(shp_file)
        except Exception as e:
            print(f"Error reading shapefile: {e}")
            return
    
    # Display basic info
    print(f"✓ Loaded {len(gdf)} neighborhoods")
    print(f"Columns available: {list(gdf.columns)}")
    
    # Try to find the neighborhood name column
    name_col = None
    for col in ["Name", "name", "NEIGHBORHOOD", "neighborhood", "NAME"]:
        if col in gdf.columns:
            name_col = col
            break
    
    if not name_col:
        print(f"Available columns: {list(gdf.columns)}")
        # Try first non-geometry column
        for col in gdf.columns:
            if col != "geometry":
                name_col = col
                break
    
    if not name_col:
        print("ERROR: Could not find neighborhood name column")
        return
    
    print(f"Using '{name_col}' as neighborhood name column")
    print(f"\nFirst few neighborhoods:")
    print(gdf[[name_col, "geometry"]].head().to_string())
    
    # Extract key neighborhood info
    neighborhoods = []
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        # Get centroid for lat/lon
        centroid = geom.centroid
        
        neighborhoods.append({
            "neighborhood": str(row[name_col]).strip(),
            "lat": centroid.y,
            "lon": centroid.x,
            "area_sqm": geom.area if hasattr(geom, "area") else None,
        })
    
    # Save as CSV
    os.makedirs("data/processed", exist_ok=True)
    df = pd.DataFrame(neighborhoods)
    df.to_csv(OUT_PATH, index=False)
    
    print(f"\n✓ Neighborhoods saved to {OUT_PATH}")
    print("\nSummary (first 10):")
    print(df.head(10).to_string(index=False))
    print(f"\nTotal neighborhoods: {len(df)}")
    print(f"Area range: {df['area_sqm'].min():.0f} - {df['area_sqm'].max():.0f} sq meters")
    
    # Also save as GeoJSON for mapping
    gdf_clean = gdf[[name_col, "geometry"]].copy()
    gdf_clean.columns = ["neighborhood", "geometry"]
    gdf_clean.to_file(GEOJSON_PATH, driver="GeoJSON")
    print(f"\n✓ GeoJSON saved to {GEOJSON_PATH} for mapping")
    
    # Verify all neighborhoods are covered
    print("\n=== Neighborhood Coverage Verification ===")
    
    # Expected neighborhoods from train_xgboost.py
    expected = [
        "Dorchester", "South Boston", "South End", "Roxbury", "East Boston",
        "Back Bay", "Jamaica Plain", "Charlestown", "Brighton", "Allston",
        "Fenway", "Beacon Hill", "Downtown", "North End", "West End", "Waterfront"
    ]
    
    loaded_neighborhoods = set(df["neighborhood"].str.lower().unique())
    expected_lower = set([n.lower() for n in expected])
    
    # Check for exact matches (case-insensitive)
    matched = expected_lower & loaded_neighborhoods
    missing = expected_lower - loaded_neighborhoods
    
    print(f"Expected neighborhoods: {len(expected)}")
    print(f"Loaded neighborhoods: {len(loaded_neighborhoods)}")
    print(f"Matched: {len(matched)}")
    
    if missing:
        print(f"\n⚠ WARNING: {len(missing)} expected neighborhoods not found:")
        for nbhd in sorted(missing):
            print(f"  - {nbhd}")
        print("\nAvailable neighborhoods in shapefile:")
        for nbhd in sorted(loaded_neighborhoods)[:20]:
            print(f"  - {nbhd}")
    else:
        print("✓ All expected neighborhoods found!")
    
    print(f"\nAll {len(df)} neighborhoods:")
    for nbhd in sorted(df["neighborhood"].unique()):
        print(f"  - {nbhd}")


if __name__ == "__main__":
    main()
