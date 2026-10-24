"""
STEP 6 — Merge Weather into 311 Counts
======================================
Joins weather_monthly.csv onto report_counts.csv by year + month,
so every neighborhood-month row carries that month's weather.

Run: python src/merge_weather.py

Inputs:
  data/processed/report_counts.csv   (neighborhood, year, month, report_count)
  data/processed/weather_monthly.csv (year, month, avg_temp_c, ...)

Output:
  data/processed/features.csv
  columns: neighborhood, year, month, report_count,
           avg_temp_c, total_precip_mm, total_snow_cm, max_wind_kmh

Step 7/8 trains the model on this file.
"""

import pandas as pd
import os

COUNTS_PATH  = "data/processed/report_counts.csv"
WEATHER_PATH = "data/processed/weather_monthly.csv"
OUT_PATH     = "data/processed/features.csv"


def main():
    print("Loading 311 counts and weather ...")
    counts  = pd.read_csv(COUNTS_PATH)
    weather = pd.read_csv(WEATHER_PATH)

    # Normalize join keys to int so the merge lines up
    for col in ("year", "month"):
        counts[col]  = pd.to_numeric(counts[col],  errors="coerce").astype("Int64")
        weather[col] = pd.to_numeric(weather[col], errors="coerce").astype("Int64")

    # Left join: keep every 311 row, attach its month's weather
    merged = counts.merge(weather, on=["year", "month"], how="left")

    # --- add LIVE MBTA transit features (bus stops, rail stops, route count) ---
    # MBTA/ polygon names use the census labels; map them to the 311 labels.
    MBTA_TO_311 = {
        "Allston":                 "Allston / Brighton",
        "Brighton":                "Allston / Brighton",
        "Downtown":                "Downtown / Financial District",
        "Fenway":                  "Fenway / Kenmore / Audubon Circle / Longwood",
        "Longwood":                "Fenway / Kenmore / Audubon Circle / Longwood",
        "South Boston":            "South Boston / South Boston Waterfront",
        "South Boston Waterfront": "South Boston / South Boston Waterfront",
        "Mattapan":                "Greater Mattapan",
    }
    mbta = pd.read_csv("data/processed/mbta.csv")
    mbta["neighborhood"] = mbta["neighborhood"].replace(MBTA_TO_311)
    # several polygons can map to one 311 area -> sum their transit counts
    mbta = mbta.groupby("neighborhood", as_index=False).sum(numeric_only=True)
    merged = merged.merge(mbta, on="neighborhood", how="left")
    for col in ("bus_stops_near", "rail_stops_near", "route_count"):
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # --- add neighborhood metadata for equity analysis (optional) ---
    hoods_meta = "data/processed/neighborhoods.csv"
    if os.path.exists(hoods_meta):
        neighborhoods = pd.read_csv(hoods_meta)
        neighborhoods_meta = neighborhoods[["neighborhood", "lat", "lon", "area_sqm"]]
        merged = merged.merge(neighborhoods_meta, on="neighborhood", how="left")

    # --- add street-tree count feature (from LIVE ArcGIS geo-match) ---
    # Map each 311 neighborhood label to the live tree-data label it draws from.
    TREE_SOURCE = {
        "Dorchester":                                   "Dorchester",
        "Roxbury":                                      "Roxbury",
        "South End":                                    "South End",
        "East Boston":                                  "East Boston",
        "Jamaica Plain":                                "Jamaica Plain",
        "Charlestown":                                  "Charlestown",
        "Roslindale":                                   "Roslindale",
        "West Roxbury":                                 "West Roxbury",
        "Hyde Park":                                    "Hyde Park",
        "Mission Hill":                                 "Mission Hill",
        "South Boston":                                 "South Boston",
        "Mattapan":                                     "Mattapan",
        "Greater Mattapan":                             "Mattapan",
        "South Boston / South Boston Waterfront":       "South Boston",
        "Allston / Brighton":                           "Allston",
        "Allston":                                      "Allston",
        "Brighton":                                     "Brighton",
        "Back Bay":                                     "Back Bay",
        "Beacon Hill":                                  "Beacon Hill",
        "Downtown / Financial District":                "Downtown",
        "Boston":                                       "Downtown",
        "Fenway / Kenmore / Audubon Circle / Longwood": "Fenway",
        # "Chestnut Hill" has no live tree polygon -> equity fill below
    }
    
    trees_file = "data/processed/trees.csv"
    if os.path.exists(trees_file):
        trees = pd.read_csv(trees_file)
        tree_by_name = trees.set_index("neighborhood")["tree_count"].to_dict()

        def tree_count_for(nbhd):
            src = TREE_SOURCE.get(nbhd)
            return tree_by_name.get(src, 0) if src else 0

        merged["tree_count"] = merged["neighborhood"].map(tree_count_for).fillna(0)
        no_trees = (merged["tree_count"] == 0).sum()
        if no_trees:
            print(f"NOTE: {no_trees} rows have 0 trees (no tree-data match).")
    else:
        print(f"NOTE: {trees_file} not found, skipping tree_count feature")

    # --- add Tree Equity Score, and use it to ESTIMATE trees where the count is 0 ---
    # Equity (0-100, American Forests) is published per neighborhood, no API key needed.
    # We fit a simple line tree_count ~ equity on the areas that HAVE a real count,
    # then fill zero-tree areas with that line's estimate instead of leaving them 0.
    equity_file = "data/equity_scores.csv"
    if os.path.exists(equity_file):
        equity = pd.read_csv(equity_file)
        eq_by_name = equity.set_index("neighborhood")["equity_score"].to_dict()
        merged["equity_score"] = merged["neighborhood"].map(eq_by_name)
        # city median fills any area with no published score
        merged["equity_score"] = merged["equity_score"].fillna(equity["equity_score"].median())

        # fit tree_count = a*equity + b on rows with a real (non-zero) tree count
        import numpy as np
        have = merged[merged["tree_count"] > 0][["equity_score", "tree_count"]].drop_duplicates()
        if len(have) >= 2:
            a, b = np.polyfit(have["equity_score"], have["tree_count"], 1)
            est = (a * merged["equity_score"] + b).clip(lower=0).round()
            merged["tree_est_from_equity"] = est
            # fill only the zero-tree rows with the equity estimate
            zero = merged["tree_count"] == 0
            merged.loc[zero, "tree_count"] = est[zero]
            print(f"Filled {int(zero.sum())} zero-tree rows from equity "
                  f"(line: trees ≈ {a:.0f}*equity {b:+.0f}).")
    else:
        print(f"NOTE: {equity_file} not found, skipping equity feature")

    # Report any rows that failed to get weather (missing month)
    missing = merged["avg_temp_c"].isna().sum()
    if missing:
        print(f"WARNING: {missing} rows had no matching weather month.")
    else:
        print("All rows matched a weather month.")

    os.makedirs("data/processed", exist_ok=True)
    merged.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(merged)} rows to {OUT_PATH}")
    print(f"Columns: {list(merged.columns)}")
    print("\nSample:")
    print(merged.head(6).to_string(index=False))


if __name__ == "__main__":
    main()
