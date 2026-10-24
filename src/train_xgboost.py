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
EXTRA_COLS = ["bus_stops_near", "rail_stops_near", "route_count", "tree_count", "equity_score", "past_pothole_rate"]


def season_from_month(m):
    """Month (1-12) -> season code: 0 winter, 1 spring, 2 summer, 3 fall."""
    if m in (12, 1, 2):
        return 0
    if m in (3, 4, 5):
        return 1
    if m in (6, 7, 8):
        return 2
    return 3


def train_one(df, feature_cols, target_col):
    """Train one XGBoost model on target_col. Returns (model, mae, accuracy_pct)."""
    X = df[feature_cols].values
    y = pd.to_numeric(df[target_col], errors="coerce").fillna(0).values

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        random_state=42,
    )
    model.fit(X_tr, y_tr)

    mae = mean_absolute_error(y_te, model.predict(X_te))
    # success % = how close on average, as a share of the average true value.
    # accuracy = 1 - (MAE / mean of true values), floored at 0, as a percent.
    mean_true = float(np.mean(y_te)) if len(y_te) else 0.0
    accuracy = max(0.0, 1.0 - (mae / mean_true)) * 100 if mean_true > 0 else 0.0
    return model, mae, accuracy


def predict_current_month(df, le, model, feature_cols, next_month, season, out_col):
    """Predict target for the current month for every neighborhood."""
    month_rows = df[df["month"] == next_month]
    cur_weather = month_rows[WEATHER_COLS].mean().to_dict()
    extra_lookup = {
        col: df.groupby("neighborhood")[col].first().to_dict()
        for col in EXTRA_COLS
    }
    rows = []
    for nbhd in df["neighborhood"].unique():
        enc = le.transform([nbhd])[0]
        feat = (
            [enc, next_month, season]
            + [cur_weather[c] for c in WEATHER_COLS]
            + [extra_lookup[col].get(nbhd, 0) for col in EXTRA_COLS]
        )
        pred = model.predict(np.array([feat]))[0]
        lat, lon = NEIGHBORHOOD_COORDS.get(nbhd, (42.36, -71.06))
        rows.append({
            "neighborhood": nbhd,
            out_col: max(0, round(pred)),
            "lat": lat,
            "lon": lon,
        })
    return pd.DataFrame(rows)


def risk_from(series):
    """Turn a numeric prediction column into high/medium/low by rank."""
    pct = series.rank(pct=True)
    return pct.apply(
        lambda p: "high" if p >= 0.70 else ("medium" if p >= 0.30 else "low")
    )


def main():
    print("Loading features.csv ...")
    df = pd.read_csv(IN_PATH)
    df["report_count"] = pd.to_numeric(df["report_count"], errors="coerce").fillna(0)
    if "pothole_count" not in df.columns:
        df["pothole_count"] = 0
    df["pothole_count"] = pd.to_numeric(df["pothole_count"], errors="coerce").fillna(0)

    # --- Encode neighborhood ---
    le = LabelEncoder()
    df["nbhd_enc"] = le.fit_transform(df["neighborhood"].astype(str))

    # --- Season, derived from month (the model learns season effects) ---
    df["season"] = df["month"].apply(season_from_month)

    feature_cols = ["nbhd_enc", "month", "season"] + WEATHER_COLS + EXTRA_COLS

    # --- Train BOTH models: everything vs potholes only ---
    print("Training XGBoost — EVERYTHING (all 311 reports) ...")
    model_all, mae_all, acc_all = train_one(df, feature_cols, "report_count")
    print(f"  Everything : Test MAE {mae_all:.1f}  |  success {acc_all:.0f}%")

    print("Training XGBoost — POTHOLES ONLY ...")
    model_pot, mae_pot, acc_pot = train_one(df, feature_cols, "pothole_count")
    print(f"  Potholes   : Test MAE {mae_pot:.1f}  |  success {acc_pot:.0f}%")

    # --- save success-rate comparison for the dashboard ---
    acc_df = pd.DataFrame([
        {"mode": "everything", "label": "Everything (all 311)",
         "mae": round(mae_all, 1), "success_pct": round(acc_all, 1)},
        {"mode": "pothole",    "label": "Potholes only",
         "mae": round(mae_pot, 1), "success_pct": round(acc_pot, 1)},
    ])
    acc_df.to_csv("data/processed/model_accuracy.csv", index=False)
    print("Saved success rates to data/processed/model_accuracy.csv")

    # --- Feature importance (from the EVERYTHING model, same as before) ---
    imp = dict(zip(feature_cols, model_all.feature_importances_.round(3)))
    imp_df = pd.DataFrame(
        {"feature": list(imp.keys()), "importance": list(imp.values())}
    ).sort_values("importance", ascending=False)
    imp_df.to_csv("data/processed/feature_importance.csv", index=False)
    print("Saved proof to data/processed/feature_importance.csv")

    # --- Predict for the CURRENT month, read live from today's date ---
    from datetime import date
    today = date.today()
    next_month = today.month
    season = season_from_month(next_month)
    season_name = {0: "winter", 1: "spring", 2: "summer", 3: "fall"}[season]
    print(f"Predicting for {today:%B %Y} (month {next_month}, {season_name}).")

    pred_all = predict_current_month(
        df, le, model_all, feature_cols, next_month, season, "predicted_reports")
    pred_pot = predict_current_month(
        df, le, model_pot, feature_cols, next_month, season, "predicted_potholes")

    # one row per neighborhood with BOTH predictions + a risk level for each
    out = pred_all.merge(
        pred_pot[["neighborhood", "predicted_potholes"]], on="neighborhood")
    out["risk_level"] = risk_from(out["predicted_reports"])
    out["risk_level_pothole"] = risk_from(out["predicted_potholes"])
    out = out.sort_values("predicted_reports", ascending=False)
    out = out[["neighborhood", "predicted_reports", "predicted_potholes",
               "lat", "lon", "risk_level", "risk_level_pothole"]]

    os.makedirs("data/processed", exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(out)} rows to {OUT_PATH}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
