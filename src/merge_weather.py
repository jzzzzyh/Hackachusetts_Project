"""
STEP 6 — Build features.csv
===========================
Joins monthly weather and per-area context (MBTA transit, street trees,
tree-equity score, map coordinates) onto report_counts.csv.

Run: python src/merge_weather.py

Inputs:
  data/processed/report_counts.csv   (from prep_data.py, canonical area names)
  data/processed/weather_monthly.csv (from fetch_weather.py)
  data/processed/mbta.csv            (from get_mbta.py)          optional
  data/processed/trees.csv           (from get_trees_live.py)    optional
  data/equity_scores.csv                                         optional
  data/processed/neighborhoods.csv   (lat / lon / area)          optional

Output:
  data/processed/features.csv  — one row per area x month.

Past-count features (last month, same month last year, ...) are NOT built
here: train_xgboost.py builds them with one shared function so training and
prediction always use exactly the same definition.

Every context file uses its own neighborhood labels; they are all mapped to the
canonical 311 areas with prep_data.canon_neighborhood and SUMMED (e.g. Allston +
Brighton trees -> "Allston / Brighton"), so no area is double counted or dropped.
"""

import os

import numpy as np
import pandas as pd

from prep_data import canon_neighborhood

COUNTS_PATH  = "data/processed/report_counts.csv"
WEATHER_PATH = "data/processed/weather_monthly.csv"
MBTA_PATH    = "data/processed/mbta.csv"
TREES_PATH   = "data/processed/trees.csv"
EQUITY_PATH  = "data/equity_scores.csv"
HOODS_PATH   = "data/processed/neighborhoods.csv"
OUT_PATH     = "data/processed/features.csv"


def per_area(path, value_cols, how="sum"):
    """Load a per-neighborhood file, map labels to canonical areas, combine duplicates."""
    if not os.path.exists(path):
        print(f"NOTE: {path} not found, skipping {value_cols}")
        return None
    df = pd.read_csv(path)
    df["neighborhood"] = df["neighborhood"].map(canon_neighborhood)
    df["neighborhood"] = df["neighborhood"].astype(object)
    labels = pd.read_csv(path)["neighborhood"]
    dropped = labels[df["neighborhood"].isna()].tolist()
    if dropped:
        print(f"  {path}: dropped labels outside the 311 areas: {dropped}")
    df = df.dropna(subset=["neighborhood"])
    return df.groupby("neighborhood", as_index=False)[value_cols].agg(how)


def main():
    print("Loading 311 counts and weather ...")
    counts = pd.read_csv(COUNTS_PATH)
    merged = counts.merge(pd.read_csv(WEATHER_PATH), on=["year", "month"], how="left")
    areas = merged["neighborhood"].unique()

    # --- MBTA transit (bus stops, rail stops, routes): summed per area ---
    mbta = per_area(MBTA_PATH, ["bus_stops_near", "rail_stops_near", "route_count"])
    if mbta is not None:
        merged = merged.merge(mbta, on="neighborhood", how="left")
        merged[mbta.columns[1:]] = merged[mbta.columns[1:]].fillna(0)

    # --- Tree-equity score: averaged per area, city median for gaps ---
    eq = per_area(EQUITY_PATH, ["equity_score"], how="mean")
    if eq is not None:
        merged = merged.merge(eq, on="neighborhood", how="left")
        merged["equity_score"] = merged["equity_score"].fillna(eq["equity_score"].median())

    # --- Street trees (live ArcGIS count): summed per area ---
    trees = per_area(TREES_PATH, ["tree_count"])
    if trees is not None:
        merged = merged.merge(trees, on="neighborhood", how="left")
        merged["tree_count"] = merged["tree_count"].fillna(0)
        # Estimate missing tree counts from equity (only if some area has none)
        zero = merged["tree_count"] == 0
        if zero.any() and "equity_score" in merged:
            have = merged.loc[~zero, ["equity_score", "tree_count"]].drop_duplicates()
            if len(have) >= 2:
                a, b = np.polyfit(have["equity_score"], have["tree_count"], 1)
                merged.loc[zero, "tree_count"] = (a * merged.loc[zero, "equity_score"] + b).clip(lower=0).round()
                print(f"Filled {merged.loc[zero, 'neighborhood'].nunique()} area(s) with no tree data from equity.")
    else:
        print("      -> run `python src/get_trees_live.py` to add the tree feature")

    # --- Map coordinates + area size ---
    if os.path.exists(HOODS_PATH):
        hoods = pd.read_csv(HOODS_PATH)[["neighborhood", "lat", "lon", "area_sqm"]]
        hoods = hoods[hoods["neighborhood"].isin(areas)]       # canonical rows only
        merged = merged.merge(hoods, on="neighborhood", how="left")

    # --- Sanity checks ---
    done = merged[merged["complete"] == 1]
    missing = done["avg_temp_c"].isna().sum()
    print(f"WARNING: {missing} completed months have no weather — re-run fetch_weather.py"
          if missing else "All completed months matched a weather month.")

    merged = merged.sort_values(["neighborhood", "year", "month"])
    os.makedirs("data/processed", exist_ok=True)
    merged.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(merged)} rows ({len(areas)} areas) to {OUT_PATH}")
    print(f"Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
