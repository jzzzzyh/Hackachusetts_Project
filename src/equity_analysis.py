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

Outputs:
  data/processed/equity_check.csv (reports per neighborhood)
"""

import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial.distance import cdist
import numpy as np
import warnings

warnings.filterwarnings("ignore")

RAW_311_PATH = "data/raw/311_2024.csv"
NEIGHBORHOODS_CSV_PATH = "data/processed/neighborhoods.csv"
OUT_EQUITY_PATH = "data/processed/equity_check.csv"


def main():
    """Perform equity analysis: join 311 reports to neighborhoods."""
    
    # Load neighborhoods
    print("Loading neighborhoods...")
    try:
        neighborhoods_df = pd.read_csv(NEIGHBORHOODS_CSV_PATH)
        print(f"✓ Loaded {len(neighborhoods_df)} neighborhoods")
        print(f"  Columns: {list(neighborhoods_df.columns)}")
    except Exception as e:
        print(f"ERROR loading neighborhoods: {e}")
        return
    
    # Load 311 reports
    print("\nLoading 311 reports (this may take 30-60 seconds)...")
    try:
        df_311 = pd.read_csv(RAW_311_PATH, low_memory=False)
        print(f"✓ Loaded {len(df_311)} reports")
    except Exception as e:
        print(f"ERROR loading 311 data: {e}")
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
    df_311_valid = df_311.dropna(subset=[lat_col, lon_col]).copy()
    print(f"✓ Reports with valid coordinates: {len(df_311_valid)} / {len(df_311)}")
    
    # Fast nearest-neighbor join using distance calculations
    print("\nPerforming nearest-neighborhood assignment...")
    
    # Extract coordinates
    reports_coords = df_311_valid[[lon_col, lat_col]].values  # lon, lat for spatial work
    nbhd_coords = neighborhoods_df[["lon", "lat"]].values      # lon, lat
    nbhd_names = neighborhoods_df["neighborhood"].values
    
    print(f"  Calculating distances to {len(nbhd_names)} neighborhoods...")
    
    # Use scipy's cdist for fast nearest neighbor
    # Calculate Euclidean distance (not geodesic, but close enough for Boston)
    distances = cdist(reports_coords, nbhd_coords, metric="euclidean")
    
    # Find nearest neighborhood for each report
    nearest_nbhd_indices = np.argmin(distances, axis=1)
    df_311_valid["neighborhood"] = nbhd_names[nearest_nbhd_indices]
    
    print(f"✓ Assigned all {len(df_311_valid)} reports to neighborhoods")
    
    # Create equity summary
    print(f"\nCreating equity analysis...")
    equity_check = df_311_valid.groupby("neighborhood").size().reset_index(name="report_count")
    equity_check = equity_check.sort_values("report_count", ascending=False)
    
    # Add percentages
    total = equity_check["report_count"].sum()
    equity_check["pct_of_total"] = (equity_check["report_count"] / total * 100).round(1)
    
    # Save equity check
    os.makedirs("data/processed", exist_ok=True)
    equity_check.to_csv(OUT_EQUITY_PATH, index=False)
    print(f"✓ Saved to {OUT_EQUITY_PATH}")
    
    # Show results
    print("\n" + "="*60)
    print("EQUITY ANALYSIS RESULTS")
    print("="*60)
    print(f"\nTotal 311 reports: {total:,}")
    print(f"Neighborhoods: {len(equity_check)}")
    print(f"\n--- TOP 10 NEIGHBORHOODS (most reports) ---")
    print(equity_check.head(10)[["neighborhood", "report_count", "pct_of_total"]].to_string(index=False))
    
    print(f"\n--- BOTTOM 10 NEIGHBORHOODS (fewest reports) ---")
    print(equity_check.tail(10)[["neighborhood", "report_count", "pct_of_total"]].to_string(index=False))
    
    # Equity insights
    print("\n" + "="*60)
    print("EQUITY INSIGHTS")
    print("="*60)
    mean_reports = equity_check["report_count"].mean()
    median_reports = equity_check["report_count"].median()
    
    print(f"\nStatistics:")
    print(f"  Mean reports per neighborhood: {mean_reports:.0f}")
    print(f"  Median: {median_reports:.0f}")
    print(f"  Range: {equity_check['report_count'].min()}-{equity_check['report_count'].max()}")
    
    # High disparity areas
    high_equity = equity_check[equity_check["report_count"] > mean_reports * 1.5]
    low_equity = equity_check[equity_check["report_count"] < mean_reports * 0.5]
    
    print(f"\n--- HIGH REQUEST AREAS (>150% of mean) ---")
    print(f"{len(high_equity)} neighborhoods with {high_equity['report_count'].sum():,} reports ({high_equity['report_count'].sum()/total*100:.1f}% of total)")
    for _, row in high_equity.head(5).iterrows():
        print(f"  • {row['neighborhood']}: {row['report_count']:,} ({row['pct_of_total']}%)")
    
    print(f"\n--- LOW REQUEST AREAS (<50% of mean) ---")
    print(f"{len(low_equity)} neighborhoods with {low_equity['report_count'].sum():,} reports ({low_equity['report_count'].sum()/total*100:.1f}% of total)")
    for _, row in low_equity.iterrows():
        print(f"  • {row['neighborhood']}: {row['report_count']:,} ({row['pct_of_total']}%)")
    
    print("\n✓ Equity analysis complete!")


if __name__ == "__main__":
    main()
