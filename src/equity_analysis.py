#!/usr/bin/env python3
"""
STEP 3 — Equity Analysis: Join Neighborhoods to Report Data
============================================================
Spatially joins 311 reports to neighborhoods for equity analysis.
Shows which neighborhoods are getting more or fewer service requests.

Run: python src/equity_analysis.py

Inputs:
  data/raw/311_2024.csv (raw 311 data with lat/lon)
  data/processed/neighborhoods.csv (neighborhood centroids)
  data/processed/neighborhoods.geojson (neighborhood polygons)

Outputs:
  data/processed/equity_check.csv (reports per neighborhood)
  data/processed/311_with_neighborhoods.csv (all reports tagged with neighborhood)
"""

import os
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point
import warnings

warnings.filterwarnings("ignore")

RAW_311_PATH = "data/raw/311_2024.csv"
NEIGHBORHOODS_GEO_PATH = "data/processed/neighborhoods.geojson"
NEIGHBORHOODS_CSV_PATH = "data/processed/neighborhoods.csv"
OUT_EQUITY_PATH = "data/processed/equity_check.csv"
OUT_TAGGED_PATH = "data/processed/311_with_neighborhoods.csv"


def download_311_data():
    """Download 311 data if not cached."""
    if os.path.exists(RAW_311_PATH):
        print(f"Using cached 311 data: {RAW_311_PATH}")
        return
    
    print("Downloading 311 data...")
    url = "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/dff4d804-5031-443a-8409-8344efd0e5c8/download/lagan_311_open_data_2024_rvsd3.csv"
    print("Note: File is ~60MB, may take 1-2 minutes...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    os.makedirs("data/raw", exist_ok=True)
    
    try:
        with requests.get(url, headers=headers, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(RAW_311_PATH, "wb") as f:
                total = 0
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    total += len(chunk)
                    print(f"  Downloaded {total / 1_000_000:.1f} MB...", end="\r")
        print(f"\n✓ Saved to {RAW_311_PATH}")
    except Exception as e:
        print(f"Error downloading: {e}")
        return False
    
    return True


def main():
    """Perform equity analysis: join 311 reports to neighborhoods."""
    
    # Download 311 data if needed
    if not download_311_data():
        return
    
    # Load neighborhoods geometry
    print("\nLoading neighborhoods GeoJSON...")
    try:
        neighborhoods_gdf = gpd.read_file(NEIGHBORHOODS_GEO_PATH)
        neighborhoods_gdf = neighborhoods_gdf.rename(columns={"neighborhood": "neighborhood"})
        print(f"✓ Loaded {len(neighborhoods_gdf)} neighborhoods")
    except Exception as e:
        print(f"Error loading neighborhoods: {e}")
        return
    
    # Load 311 reports
    print("Loading 311 reports (this may take a minute)...")
    try:
        df_311 = pd.read_csv(RAW_311_PATH, low_memory=False)
        print(f"✓ Loaded {len(df_311)} reports")
    except Exception as e:
        print(f"Error loading 311 data: {e}")
        return
    
    # Normalize column names
    df_311.columns = [c.strip().lower().replace(" ", "_") for c in df_311.columns]
    
    # Find latitude/longitude columns
    lat_col = next((c for c in df_311.columns if "latitude" in c or "lat" in c), None)
    lon_col = next((c for c in df_311.columns if "longitude" in c or "lon" in c), None)
    
    if not lat_col or not lon_col:
        print(f"ERROR: Could not find latitude/longitude columns")
        print(f"Available columns: {list(df_311.columns)}")
        return
    
    print(f"Using coordinates: {lat_col}, {lon_col}")
    
    # Filter to reports with valid coordinates
    df_311_valid = df_311.dropna(subset=[lat_col, lon_col])
    print(f"Reports with valid coordinates: {len(df_311_valid)} / {len(df_311)}")
    
    # Convert to GeoDataFrame
    print("Converting to GeoDataFrame...")
    geometry = [Point(xy) for xy in zip(df_311_valid[lon_col], df_311_valid[lat_col])]
    reports_gdf = gpd.GeoDataFrame(
        df_311_valid.reset_index(drop=True),
        geometry=geometry,
        crs="EPSG:4326"
    )
    
    # Spatial join: which neighborhood is each report in?
    print("Performing spatial join (this may take a minute)...")
    try:
        reports_with_nbhd = gpd.sjoin(
            reports_gdf,
            neighborhoods_gdf[["geometry", "neighborhood"]],
            how="left",
            predicate="within"
        )
    except Exception as e:
        print(f"Error in spatial join: {e}")
        # Fallback: use nearest neighbor
        print("Falling back to nearest neighbor join...")
        reports_with_nbhd = gpd.sjoin_nearest(
            reports_gdf,
            neighborhoods_gdf[["geometry", "neighborhood"]],
            how="left"
        )
    
    # Handle reports outside all neighborhoods (shouldn't be many)
    missing = reports_with_nbhd[reports_with_nbhd["neighborhood"].isna()]
    if len(missing) > 0:
        print(f"\n⚠ {len(missing)} reports outside all neighborhoods")
        print("Assigning to nearest neighborhood...")
        
        # Find nearest for these
        missing_coords = gpd.GeoDataFrame(
            missing,
            geometry=missing.geometry,
            crs="EPSG:4326"
        )
        nearest = gpd.sjoin_nearest(
            missing_coords,
            neighborhoods_gdf[["geometry", "neighborhood"]],
            how="left"
        )
        
        # Update with nearest
        reports_with_nbhd.loc[missing.index, "neighborhood"] = nearest["neighborhood"].values
    
    print(f"✓ Assigned neighborhoods to {len(reports_with_nbhd)} reports")
    
    # Save tagged reports (for detailed analysis)
    print(f"\nSaving tagged reports...")
    cols_to_keep = [c for c in reports_with_nbhd.columns if c not in ["geometry", "index_right"]]
    reports_with_nbhd[cols_to_keep].to_csv(OUT_TAGGED_PATH, index=False)
    print(f"✓ Saved to {OUT_TAGGED_PATH}")
    
    # Create equity summary
    print(f"\nCreating equity analysis...")
    equity_check = reports_with_nbhd.groupby("neighborhood").size().reset_index(name="report_count")
    equity_check = equity_check.sort_values("report_count", ascending=False)
    
    # Add percentages
    total = equity_check["report_count"].sum()
    equity_check["pct_of_total"] = (equity_check["report_count"] / total * 100).round(1)
    
    # Save equity check
    os.makedirs("data/processed", exist_ok=True)
    equity_check.to_csv(OUT_EQUITY_PATH, index=False)
    print(f"✓ Saved to {OUT_EQUITY_PATH}")
    
    # Show results
    print("\n=== EQUITY ANALYSIS RESULTS ===")
    print(f"\nTotal 311 reports: {total:,}")
    print(f"Neighborhoods covered: {len(equity_check)}")
    print(f"\nReports by neighborhood (top 10):")
    print(equity_check.head(10).to_string(index=False))
    
    print(f"\nBottom 10 neighborhoods (lower report counts):")
    print(equity_check.tail(10).to_string(index=False))
    
    # Equity insights
    print("\n=== EQUITY INSIGHTS ===")
    mean_reports = equity_check["report_count"].mean()
    high_equity = equity_check[equity_check["report_count"] > mean_reports * 1.5]
    low_equity = equity_check[equity_check["report_count"] < mean_reports * 0.5]
    
    print(f"\nMean reports per neighborhood: {mean_reports:.0f}")
    print(f"\nHigh request areas (>150% mean, {len(high_equity)} neighborhoods):")
    for _, row in high_equity.iterrows():
        print(f"  {row['neighborhood']}: {row['report_count']} ({row['pct_of_total']}%)")
    
    print(f"\nLow request areas (<50% mean, {len(low_equity)} neighborhoods):")
    for _, row in low_equity.iterrows():
        print(f"  {row['neighborhood']}: {row['report_count']} ({row['pct_of_total']}%)")
    
    print("\n✓ Equity analysis complete!")


if __name__ == "__main__":
    main()
