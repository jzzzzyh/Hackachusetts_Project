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
