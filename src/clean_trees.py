"""
clean_trees.py
Loads BPRD street trees CSV, filters to street trees only (park == null),
and saves a GeoDataFrame (GeoJSON) plus a flat CSV.
"""

import os
import glob
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

SEARCH_PATTERNS = [
    "data/*bprd_trees*",
    "data/*tree*",
    os.path.expanduser("~/Downloads/*bprd_trees*"),
    os.path.expanduser("~/Downloads/*tree*"),
]

KEEP_COLS = ["id", "spp_com", "dbh", "neighborhood", "park", "x_longitude", "y_latitude"]
OUT_DIR = "data"


def find_source() -> str:
    for pattern in SEARCH_PATTERNS:
        matches = glob.glob(pattern)
        if matches:
            print(f"Found: {matches[0]}")
            return matches[0]
    raise FileNotFoundError(
        "Cannot find trees CSV. Place bprd_trees.csv in the data/ folder."
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    path = find_source()
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded {len(df):,} rows. Columns: {list(df.columns[:8])} ...")

    # Keep only the columns we need (gracefully skip missing ones)
    available = [c for c in KEEP_COLS if c in df.columns]
    df = df[available]

    # Filter: street trees only (park column is null/empty)
    before = len(df)
    df = df[df["park"].isna() | (df["park"].str.strip() == "")]
    print(f"Street trees after filtering park==null: {len(df):,} (removed {before - len(df):,} park trees)")

    # Rename for clarity
    df = df.rename(columns={"x_longitude": "lon", "y_latitude": "lat", "spp_com": "species"})

    # Drop rows missing coordinates
    df = df.dropna(subset=["lat", "lon"])
    print(f"Rows with valid coordinates: {len(df):,}")

    # Build GeoDataFrame
    geometry = gpd.points_from_xy(df["lon"], df["lat"])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # GeoJSON output
    geojson_path = os.path.join(OUT_DIR, "boston_street_trees.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"\nSaved GeoJSON: {geojson_path}")

    # CSV output (no geometry column)
    csv_path = os.path.join(OUT_DIR, "boston_street_trees.csv")
    df.drop(columns=["park"], errors="ignore").to_csv(csv_path, index=False)
    print(f"Saved CSV:     {csv_path}")

    print(f"\nFirst 3 rows:\n{df[['id','species','lat','lon']].head(3).to_string()}")


if __name__ == "__main__":
    main()
