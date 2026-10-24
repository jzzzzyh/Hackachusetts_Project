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

    # --- add MBTA bus-stop feature ---
    mbta = pd.read_csv("data/processed/mbta.csv")
    merged = merged.merge(mbta, on="neighborhood", how="left")
    merged["bus_stops_near"] = merged["bus_stops_near"].fillna(0)

    # --- add street-tree count feature ---
    # Map each 311 neighborhood label to the tree-data label it draws from.
    # Keyed by the 311 name, so no rename can steal a name from another row.
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
        "Allston / Brighton":                           "Allston-Brighton",
        "Allston":                                      "Allston-Brighton",
        "Brighton":                                     "Allston-Brighton",
        "Back Bay":                                     "Back Bay/Beacon Hill",
        "Beacon Hill":                                  "Back Bay/Beacon Hill",
        "Downtown / Financial District":                "Central Boston",
        "Boston":                                       "Central Boston",
        "Fenway / Kenmore / Audubon Circle / Longwood": "Fenway/Longwood",
        # "Chestnut Hill" has no tree data -> stays 0
    }
    trees = pd.read_csv("data/processed/trees.csv")
    tree_by_name = trees.set_index("neighborhood")["tree_count"].to_dict()

    def tree_count_for(nbhd):
        src = TREE_SOURCE.get(nbhd)
        return tree_by_name.get(src, 0) if src else 0

    merged["tree_count"] = merged["neighborhood"].map(tree_count_for).fillna(0)
    no_trees = (merged["tree_count"] == 0).sum()
    if no_trees:
        print(f"NOTE: {no_trees} rows still have 0 trees (no tree-data match).")

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
