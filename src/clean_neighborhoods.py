"""
clean_neighborhoods.py
Loads Boston neighborhood boundaries GeoJSON, keeps essential columns,
and saves two outputs: a GeoJSON (for spatial joins) and a CSV (for lookups).
"""

import os
import geopandas as gpd
import pandas as pd

# Possible local paths to search
SEARCH_PATHS = [
    "data/boston_neighborhood_boundaries.geojson",
    os.path.expanduser("~/.kiro/crew/uploads/boston_neighborhood_boundaries.geojson"),
    os.path.expanduser("~/Downloads/boston_neighborhood_boundaries.geojson"),
    os.path.expanduser("~/Desktop/boston_neighborhood_boundaries.geojson"),
]

FALLBACK_URL = (
    "https://data.boston.gov/dataset/3525b0ee-1e7c-43d5-ab83-7c0fbdf2b929"
    "/resource/e5849875-a6f6-4c9c-9d8a-5048b0fbd03e"
    "/download/boston_neighborhood_boundaries.geojson"
)

KEEP_COLS = ["name", "neighborhood_id", "sqmiles", "geometry"]
OUT_DIR = "data"


def find_source() -> str:
    for path in SEARCH_PATHS:
        if os.path.exists(path):
            print(f"Found local file: {path}")
            return path
    print("Local file not found -- downloading from Boston Open Data...")
    return FALLBACK_URL


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    source = find_source()
    gdf = gpd.read_file(source)
    print(f"Loaded {len(gdf)} neighborhoods. Columns: {list(gdf.columns)}")

    # Keep only the columns we need (gracefully handle missing ones)
    available = [c for c in KEEP_COLS if c in gdf.columns or c == "geometry"]
    gdf = gdf[available]

    # GeoJSON output (for spatial joins)
    geojson_path = os.path.join(OUT_DIR, "boston_neighborhoods.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"\nSaved GeoJSON: {geojson_path}  ({len(gdf)} rows)")
    print(gdf[["name", "neighborhood_id", "sqmiles"]].head(3).to_string())

    # CSV output (lightweight lookup, no geometry)
    csv_cols = [c for c in ["name", "neighborhood_id", "sqmiles"] if c in gdf.columns]
    csv_path = os.path.join(OUT_DIR, "boston_neighborhoods.csv")
    gdf[csv_cols].to_csv(csv_path, index=False)
    print(f"\nSaved CSV:     {csv_path}  ({len(gdf)} rows, {len(csv_cols)} cols)")


if __name__ == "__main__":
    main()
