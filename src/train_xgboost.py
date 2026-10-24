"""
STEPS 7 + 8 — Feature Matrix + XGBoost
======================================
Builds the feature matrix from features.csv (311 counts + weather) and
trains an XGBoost model to predict next month's report count per
neighborhood. Replaces the Random Forest baseline.

Run: python src/train_xgboost.py

Input:  data/processed/features.csv
Output: data/processed/predictions.csv
  columns: neighborhood, predicted_reports, risk_level, lat, lon

Features used:
  - neighborhood (label-encoded)
  - month
  - avg_temp_c, total_precip_mm, total_snow_cm, max_wind_kmh
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
import os

IN_PATH  = "data/processed/features.csv"
OUT_PATH = "data/processed/predictions.csv"

# Approximate neighborhood centroids for the map (same as the RF baseline)
NEIGHBORHOOD_COORDS = {
    "Dorchester":                                    (42.3021, -71.0707),
    "South Boston / South Boston Waterfront":        (42.3388, -71.0468),
    "South Boston":                                  (42.3388, -71.0468),
    "South End":                                     (42.3398, -71.0786),
    "Allston / Brighton":                            (42.3500, -71.1430),
    "Allston":                                       (42.3534, -71.1312),
    "Brighton":                                      (42.3467, -71.1564),
    "Roxbury":                                       (42.3142, -71.0920),
    "East Boston":                                   (42.3784, -71.0282),
    "Back Bay":                                      (42.3503, -71.0810),
    "Jamaica Plain":                                 (42.3100, -71.1148),
    "Downtown / Financial District":                 (42.3560, -71.0550),
    "Boston":                                        (42.3601, -71.0589),
    "Beacon Hill":                                   (42.3588, -71.0707),
    "Roslindale":                                    (42.2840, -71.1284),
    "Charlestown":                                   (42.3782, -71.0602),
    "Hyde Park":                                     (42.2551, -71.1243),
    "Greater Mattapan":                              (42.2736, -71.0921),
    "Mattapan":                                      (42.2736, -71.0921),
    "West Roxbury":                                  (42.2793, -71.1607),
    "Fenway / Kenmore / Audubon Circle / Longwood":  (42.3467, -71.1003),
    "Fenway":                                        (42.3467, -71.1003),
    "Mission Hill":                                  (42.3278, -71.1003),
    "Chestnut Hill":                                 (42.3258, -71.1662),
    "North End":                                     (42.3647, -71.0542),
}

WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
EXTRA_COLS   = ["bus_stops_near"]
EXTRA_COLS = ["bus_stops_near", "tree_count"]


def main():
    print("Loading features.csv ...")
    df = pd.read_csv(IN_PATH)
    df["report_count"] = pd.to_numeric(df["report_count"], errors="coerce").fillna(0)

    # --- Encode neighborhood ---
    le = LabelEncoder()
    df["nbhd_enc"] = le.fit_transform(df["neighborhood"].astype(str))

    feature_cols = ["nbhd_enc", "month"] + WEATHER_COLS + EXTRA_COLS
    X = df[feature_cols].values
    y = df["report_count"].values

    # --- Train/test split to report honest accuracy ---
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training XGBoost ...")
    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        random_state=42,
    )
    model.fit(X_tr, y_tr)

    mae = mean_absolute_error(y_te, model.predict(X_te))
    print(f"Test MAE: {mae:.1f} reports  (lower is better)")

    # --- Feature importance (shows weather matters) ---
    imp = dict(zip(feature_cols, model.feature_importances_.round(3)))
    print("Feature importance:", imp)

    # --- save proof that weather trained the model ---
    imp_df = pd.DataFrame(
        {"feature": list(imp.keys()), "importance": list(imp.values())}
    ).sort_values("importance", ascending=False)
    imp_df.to_csv("data/processed/feature_importance.csv", index=False)
    print("Saved proof to data/processed/feature_importance.csv")

    # --- Predict next month (November) using Nov weather from the data ---
    next_month = 11
    nov_weather = df[df["month"] == next_month][WEATHER_COLS].iloc[0].to_dict()

    neighborhoods = df["neighborhood"].unique()
    tree_lookup = df.groupby("neighborhood")["tree_count"].first().to_dict()
    rows = []
    for nbhd in neighborhoods:
        enc = le.transform([nbhd])[0]
        # Get bus stops for this neighborhood
        bus_stops = df[df["neighborhood"] == nbhd]["bus_stops_near"].iloc[0]
        feat = [enc, next_month] + [nov_weather[c] for c in WEATHER_COLS] + [bus_stops]
        # Extra per-neighborhood features, in EXTRA_COLS order
        bus_stops = df[df["neighborhood"] == nbhd]["bus_stops_near"].iloc[0]
        feat = (
            [enc, next_month]
            + [nov_weather[c] for c in WEATHER_COLS]
            + [bus_stops, tree_lookup.get(nbhd, 0)]
        )
        pred = model.predict(np.array([feat]))[0]
        lat, lon = NEIGHBORHOOD_COORDS.get(nbhd, (42.36, -71.06))
        rows.append({
            "neighborhood": nbhd,
            "predicted_reports": max(0, round(pred)),
            "lat": lat,
            "lon": lon,
        })

    out = pd.DataFrame(rows).sort_values("predicted_reports", ascending=False)
    out["rank_pct"] = out["predicted_reports"].rank(pct=True)
    out["risk_level"] = out["rank_pct"].apply(
        lambda p: "high" if p >= 0.70 else ("medium" if p >= 0.30 else "low")
    )
    out = out.drop(columns="rank_pct")

    os.makedirs("data/processed", exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(out)} rows to {OUT_PATH}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
