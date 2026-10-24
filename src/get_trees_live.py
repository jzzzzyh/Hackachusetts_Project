"""
LIVE Street-Tree Counts per Neighborhood
========================================
Fully live, no API key.

1. Pulls every Boston tree POINT from the city's live ArcGIS layer
   (updates daily) — paged, because the server caps each response.
2. Pulls the neighborhood boundary SHAPES from data.boston.gov (GeoJSON).
3. Counts how many tree points fall inside each neighborhood polygon
   (point-in-polygon via geopandas spatial join).

Run: python src/get_trees_live.py

Output: data/processed/trees.csv   (neighborhood, tree_count)

Why live? The ArcGIS layer reflects today's tree inventory, so re-running
this picks up new plantings and removals with no code change.
"""

import requests
import geopandas as gpd
import pandas as pd
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Live tree points (ArcGIS, keyless, daily).
TREES_URL = ("https://testgisportal.boston.gov/arcgis/rest/services/"
             "EnvironmentEnergy/OpenData/MapServer/1/query")

# Neighborhood boundary shapes (data.boston.gov GeoJSON, keyless).
HOODS_URL = ("https://data.boston.gov/dataset/e11a621a-6561-4da6-a715-6edd2fa217a4/"
             "resource/c9663e7a-84c2-435c-91c0-91cdce1ee5ac/download/"
             "boston_neighborhood_boundaries_approximated_by_2020_census_block_groups.geojson")

HOODS_LOCAL = "data/raw/neighborhoods.geojson"
OUT_PATH    = "data/processed/trees.csv"
PAGE        = 2000   # ArcGIS caps page size; we page with resultOffset


def fetch_tree_points() -> gpd.GeoDataFrame:
    """Page through the live ArcGIS tree layer, return all points as a GeoDataFrame."""
    feats, offset = [], 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "OBJECTID",
            "resultOffset": offset,
            "resultRecordCount": PAGE,
            "f": "geojson",
        }
        r = requests.get(TREES_URL, params=params, headers=HEADERS, timeout=120)
        r.raise_for_status()
        js = r.json()
        batch = js.get("features", [])
        if not batch:
            break
        feats.extend(batch)
        print(f"  fetched {len(feats)} tree points ...")
        if not js.get("exceededTransferLimit") and not js.get("properties", {}).get("exceededTransferLimit"):
            break
        offset += PAGE
    gdf = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    return gdf


def load_neighborhoods() -> gpd.GeoDataFrame:
    """Download (with browser UA) and read the neighborhood shapes."""
    if not os.path.exists(HOODS_LOCAL):
        os.makedirs("data/raw", exist_ok=True)
        print("Downloading neighborhood boundaries ...")
        data = requests.get(HOODS_URL, headers=HEADERS, timeout=120).content
        with open(HOODS_LOCAL, "wb") as f:
            f.write(data)
    hoods = gpd.read_file(HOODS_LOCAL).to_crs("EPSG:4326")
    hoods = hoods.rename(columns={"blockgr2020_ctr_neighb_name": "neighborhood"})
    return hoods[["neighborhood", "geometry"]]


def main():
    print("Fetching LIVE tree points from Boston ArcGIS ...")
    trees = fetch_tree_points()
    print(f"Total live tree points: {len(trees)}")

    print("Loading neighborhood shapes ...")
    hoods = load_neighborhoods()

    print("Counting trees inside each neighborhood (point-in-polygon) ...")
    joined = gpd.sjoin(trees, hoods, how="inner", predicate="within")
    counts = (joined.groupby("neighborhood").size()
              .reset_index(name="tree_count")
              .sort_values("tree_count", ascending=False))

    os.makedirs("data/processed", exist_ok=True)
    counts.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(counts)} neighborhoods to {OUT_PATH}")
    print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
