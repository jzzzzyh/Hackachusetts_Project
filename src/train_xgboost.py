"""
STEPS 7 + 8 — Feature Matrix + XGBoost
======================================
Trains two XGBoost models on features.csv and predicts the CURRENT month
(read from today's date) for every area:
  * Potholes only — pothole reports  (target: pothole_count)  <- MAIN model
  * Everything    — all 311 reports  (target: report_count)   secondary toggle

Run: python src/train_xgboost.py

Input:  data/processed/features.csv
Output: data/processed/predictions.csv
          neighborhood, predicted_reports, predicted_potholes, lat, lon,
          risk_level, risk_level_pothole, predict_year, predict_month
        data/processed/model_accuracy.csv        (test error vs simple guesses)
        data/processed/feature_importance.csv    (pothole model)
        data/processed/feature_importance_everything.csv

Features:
  - area (label-encoded), month, season
  - PAST COUNTS of the same target, built by add_lag_features():
      lag1  = last month, lag12 = same month last year, roll3 = 3-month average
  - per-area context: MBTA transit, street trees, tree-equity score (if present)
  - weather is OFF (USE_WEATHER). Back-tested on 6 held-out years
    (2019, 2021-2025): weather made the all-311 model worse every year
    (+10% to +36% error) and helped potholes in only 3 of 6 years. The month
    + past counts already carry the season.

Honest scoring: train on everything before the last 12 complete months,
test on those 12 months (no future data leaks into training), and compare
with two simple guesses. Then retrain on all complete months to predict.
"""

import os
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

IN_PATH  = "data/processed/features.csv"
OUT_PATH = "data/processed/predictions.csv"

TARGETS = {
    # mode       target column     prediction column      risk column            label
    "everything": ("report_count",  "predicted_reports",  "risk_level",         "Everything (all 311)"),
    "pothole":    ("pothole_count", "predicted_potholes", "risk_level_pothole", "Potholes only"),
}
# pothole_resident exists too, but Boston's new 311 system (potholes since
# 2026-06-23) no longer records who filed a report, so it stops in May 2026.

USE_WEATHER  = False
WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
LAG_COLS     = ["lag1", "lag12", "roll3"]
CONTEXT_COLS = ["bus_stops_near", "rail_stops_near", "route_count", "tree_count", "equity_score"]
TEST_MONTHS  = 12

# Map fallback for areas missing from neighborhoods.csv
DEFAULT_COORDS = (42.3601, -71.0589)


def season_from_month(m):
    """Month (1-12) -> season code: 0 winter, 1 spring, 2 summer, 3 fall."""
    if m in (12, 1, 2):
        return 0
    if m in (3, 4, 5):
        return 1
    if m in (6, 7, 8):
        return 2
    return 3


def add_lag_features(df, target):
    """Past counts of `target` per area. Only uses months BEFORE each row.

    Requires one row per area per month with no gaps (prep_data.py fills them),
    so shift(1) really is last month and shift(12) the same month last year.
    """
    df = df.sort_values(["neighborhood", "year", "month"]).copy()
    past = df.groupby("neighborhood")[target].shift(1)
    df["lag1"] = past
    df["lag12"] = df.groupby("neighborhood")[target].shift(12)
    df["roll3"] = past.groupby(df["neighborhood"]).transform(lambda s: s.rolling(3).mean())
    return df


def make_model(seed=42):
    return XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                        subsample=0.9, random_state=seed)


def evaluate(train_df, feature_cols, target):
    """Time-based test: the last TEST_MONTHS complete months are held out."""
    done = train_df.copy()
    done["ym"] = done["year"] * 12 + done["month"]
    months = np.sort(done["ym"].unique())
    cutoff = months[-TEST_MONTHS]
    tr, te = done[done["ym"] < cutoff], done[done["ym"] >= cutoff]

    model = make_model().fit(tr[feature_cols], tr[target])
    pred = np.clip(model.predict(te[feature_cols]), 0, None)
    mae = mean_absolute_error(te[target], pred)
    mean_true = te[target].mean()
    # success % = 1 - MAE / average true value (100% = perfect), floored at 0
    success = max(0.0, 1 - mae / mean_true) * 100 if mean_true > 0 else 0.0
    first, last = int(te["ym"].min() - 1), int(te["ym"].max() - 1)
    return {
        "mae": round(mae, 1),
        "success_pct": round(success, 1),
        "mae_last_month": round(mean_absolute_error(te[target], te["lag1"]), 1),
        "mae_last_year": round(mean_absolute_error(te[target], te["lag12"]), 1),
        "test_period": f"{first // 12}-{first % 12 + 1:02d} to {last // 12}-{last % 12 + 1:02d}",
        "test_rows": len(te),
        "mean_actual": round(mean_true, 1),
    }


def risk_from(series):
    """Turn a numeric prediction column into high/medium/low by rank."""
    pct = series.rank(pct=True)
    return pct.apply(lambda p: "high" if p >= 0.70 else ("medium" if p >= 0.30 else "low"))


def main():
    print("Loading features.csv ...")
    df = pd.read_csv(IN_PATH)
    if "complete" not in df.columns:
        raise SystemExit("features.csv is from the old pipeline — run prep_data.py and merge_weather.py first.")

    le = LabelEncoder()
    df["nbhd_enc"] = le.fit_transform(df["neighborhood"].astype(str))
    df["season"] = df["month"].apply(season_from_month)

    context = [c for c in CONTEXT_COLS if c in df.columns]
    skipped = sorted(set(CONTEXT_COLS) - set(context))
    if skipped:
        print(f"NOTE: context columns not in features.csv, skipped: {skipped}")
    feature_cols = (["nbhd_enc", "month", "season"] + LAG_COLS + context
                    + (WEATHER_COLS if USE_WEATHER else []))

    # Predict the current month (today's date). It's in progress, so it is never trained on.
    today = date.today()
    pred_year, pred_month = today.year, today.month
    if not ((df["year"] == pred_year) & (df["month"] == pred_month)).any():
        raise SystemExit(f"No rows for {today:%B %Y} — re-run prep_data.py to refresh the 311 data.")
    print(f"Predicting for {today:%B %Y} (season {season_from_month(pred_month)}).")

    accuracy, predictions = [], None
    for mode, (target, pred_col, risk_col, label) in TARGETS.items():
        data = add_lag_features(df, target)
        train = data[(data["complete"] == 1)].dropna(subset=LAG_COLS + [target])

        scores = evaluate(train, feature_cols, target)
        print(f"\n{label}: test {scores['test_period']}, avg {scores['mean_actual']} per area-month")
        print(f"  model MAE {scores['mae']}  |  'same as last month' {scores['mae_last_month']}"
              f"  |  'same month last year' {scores['mae_last_year']}  |  success {scores['success_pct']:.0f}%")
        accuracy.append({"mode": mode, "label": label, **scores})

        # Retrain on every complete month, then predict the current month
        model = make_model().fit(train[feature_cols], train[target])
        imp = (pd.DataFrame({"feature": feature_cols, "importance": model.feature_importances_.round(3)})
               .sort_values("importance", ascending=False))
        imp_path = ("data/processed/feature_importance.csv" if mode == "pothole"
                    else f"data/processed/feature_importance_{mode}.csv")
        imp.to_csv(imp_path, index=False)

        cur = data[(data["year"] == pred_year) & (data["month"] == pred_month)].copy()
        cur[pred_col] = np.clip(model.predict(cur[feature_cols]), 0, None).round().astype(int)
        cur[risk_col] = risk_from(cur[pred_col])
        keep = cur[["neighborhood", pred_col, risk_col]]
        predictions = keep if predictions is None else predictions.merge(keep, on="neighborhood")

    pd.DataFrame(accuracy).to_csv("data/processed/model_accuracy.csv", index=False)
    print("\nSaved model_accuracy.csv and feature_importance*.csv")

    coords = df.groupby("neighborhood")[["lat", "lon"]].first() if "lat" in df.columns else None
    out = predictions.copy()
    out["lat"] = out["neighborhood"].map(coords["lat"]) if coords is not None else np.nan
    out["lon"] = out["neighborhood"].map(coords["lon"]) if coords is not None else np.nan
    out["lat"] = out["lat"].fillna(DEFAULT_COORDS[0])
    out["lon"] = out["lon"].fillna(DEFAULT_COORDS[1])
    out["predict_year"], out["predict_month"] = pred_year, pred_month
    out = out.sort_values("predicted_potholes", ascending=False)[
        ["neighborhood", "predicted_reports", "predicted_potholes", "lat", "lon",
         "risk_level", "risk_level_pothole", "predict_year", "predict_month"]]

    os.makedirs("data/processed", exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\nDone! Saved {len(out)} rows to {OUT_PATH}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
