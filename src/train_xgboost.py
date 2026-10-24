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
          + why_potholes / why_reports: top 3 reasons behind each prediction
        data/processed/prediction_reasons.csv    (top 6 inputs per area, with effect size)
        data/processed/model_accuracy.csv        (test error vs simple guesses)
        data/processed/feature_importance.csv    (pothole model)
        data/processed/feature_importance_everything.csv

Features:
  - area (label-encoded), month, season
  - PAST COUNTS of the same target, built by add_lag_features():
      lag1  = last month, lag12 = same month last year, roll3 = 3-month average
  - per-area context: MBTA transit, street trees, tree-equity score (if present)
  - pothole model only: exposure (road miles, lane miles, traffic, population)
    and a Poisson (count) loss — see OBJECTIVE / USE_EXPOSURE below
  - pothole model only: reports filed SO FAR this month (so_far, pace) from
    pothole_daily.csv — see USE_SO_FAR below
  - weather is OFF (USE_WEATHER). Back-tested on 6 held-out years
    (2019, 2021-2025): weather made the all-311 model worse every year
    (+10% to +36% error) and helped potholes in only 3 of 6 years. The month
    + past counts already carry the season.

Honest scoring: train on everything before the last 12 complete months,
test on those 12 months (no future data leaks into training), and compare
with two simple guesses. Then retrain on all complete months to predict.
"""

import calendar
import os
from datetime import date

import numpy as np
import pandas as pd
import xgboost as xgb
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

# Per-model settings, chosen by back-testing 6 held-out years (2019, 2021-2025):
#  * pothole: Poisson loss (made for counts, so a miss of 10 on a small area
#    counts more than on a big one) + exposure features (road miles, lane
#    miles, traffic, population). Best or tied in 5 of 6 years; cut the worst
#    per-area overshoot from 32% to 25%.
#  * everything: no consistent gain from either change -> unchanged.
OBJECTIVE = {"pothole": "count:poisson", "everything": "reg:squarederror"}
EXPOSURE_COLS = ["road_miles", "lane_miles", "daily_vehicle_miles", "population"]
USE_EXPOSURE = {"pothole": True, "everything": False}

# "So far this month" (pothole model only). The month being predicted is in
# progress, so the reports already filed tell the model whether the spring
# spike has started. Back-test (7 held-out years): knowing the first 14 days
# cut spring error from 32.9 to 18.2 per area-month and city-wide spring misses
# from 23% to 11.5%. Weather / momentum features were tried and did not help.
# Training rows get the SAME share of their month (e.g. 23/31 of the month),
# so the model always learns from the situation it will predict in.
DAILY_PATH = "data/processed/pothole_daily.csv"
USE_SO_FAR = {"pothole": True, "everything": False}
SO_FAR_COLS = ["so_far", "pace"]

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


def add_so_far_features(df, daily, frac):
    """Potholes reported in the first `frac` of each month, per area.

    so_far = reports in days 1..cutoff, where cutoff = floor(frac * days in that month)
    pace   = so_far projected to a full month in a straight line
    """
    df = df.copy()
    days = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1)).dt.days_in_month
    df["cutoff_day"] = np.floor(frac * days).astype(int)
    keys = ["neighborhood", "year", "month"]
    upto = daily.merge(df[keys + ["cutoff_day"]], on=keys)
    upto = upto[upto["day"] <= upto["cutoff_day"]].groupby(keys)["potholes"].sum().rename("so_far")
    df = df.merge(upto.reset_index(), on=keys, how="left")
    df["so_far"] = df["so_far"].fillna(0)
    df["pace"] = np.where(df["cutoff_day"] > 0, df["so_far"] * days.values / df["cutoff_day"].clip(lower=1), 0)
    return df.drop(columns="cutoff_day")


def so_far_cutoff(daily, year, month):
    """Last FULL day of reports we have for the month being predicted (0 = none).

    The newest day in the download is usually partial (e.g. up to 5 am), so it is dropped.
    """
    cur = daily[(daily["year"] == year) & (daily["month"] == month)]
    return max(int(cur["day"].max()) - 1, 0) if len(cur) else 0


REASONS_PATH = "data/processed/prediction_reasons.csv"
TOP_REASONS = 3          # reasons written into predictions.csv (the long file keeps 6)


def describe_input(feature, value, pred_month, cutoff):
    """Plain-English description of one input's value for one area."""
    mname = calendar.month_name[pred_month]
    v = float(value)
    return {
        "lag1": f"{v:.0f} last month",
        "lag12": f"{v:.0f} in {mname} last year",
        "roll3": f"avg {v:.0f}/month over the last 3 months",
        "month": f"time of year ({mname})",
        "season": "the season",
        "nbhd_enc": "this neighborhood's own pattern",
        "route_count": f"{v:.0f} MBTA routes",
        "rail_stops_near": f"{v:.0f} MBTA rail stops",
        "bus_stops_near": f"{v:.0f} MBTA bus stops",
        "tree_count": f"{v:,.0f} street trees",
        "equity_score": f"tree-equity score {v:.0f}",
        "road_miles": f"{v:.0f} miles of road",
        "lane_miles": f"{v:.0f} lane-miles of road",
        "daily_vehicle_miles": f"{v:,.0f} vehicle-miles of traffic a day",
        "population": f"{v:,.0f} residents",
        "so_far": f"{v:.0f} already reported (days 1-{cutoff})",
        "pace": f"on pace for {v:.0f} this month",
    }.get(feature, f"{feature} = {v:g}")


def explain(model, rows, feature_cols, objective, pred_month, cutoff, unit):
    """Why each prediction is what it is: per-input contributions (SHAP, built into XGBoost).

    Contributions are measured against the model's typical area-month (the baseline).
    Poisson model: contributions are on a log scale, so each one is shown as a % change
    (they multiply). Squared-error model: each one is shown in report counts (they add).
    Returns (one reasons string per row, long table of the top inputs per row).
    """
    dm = xgb.DMatrix(rows[feature_cols])
    contrib = model.get_booster().predict(dm, pred_contribs=True)
    poisson = objective.startswith("count:")
    texts, long_rows = [], []
    for i, (_, row) in enumerate(rows.iterrows()):
        c, bias = contrib[i, :-1], contrib[i, -1]
        baseline = float(np.exp(bias)) if poisson else float(bias)
        order = np.argsort(-np.abs(c))
        parts = []
        for rank, j in enumerate(order[:6], start=1):
            f = feature_cols[j]
            effect = (np.exp(c[j]) - 1) * 100 if poisson else c[j]
            eff_txt = f"{effect:+.0f}%" if poisson else f"{effect:+,.0f} {unit}"
            desc = describe_input(f, row[f], pred_month, cutoff)
            long_rows.append({"neighborhood": row["neighborhood"], "rank": rank, "feature": f,
                              "reason": desc, "effect": round(float(effect), 1),
                              "effect_unit": "%" if poisson else unit,
                              "baseline": round(baseline, 1)})
            if rank <= TOP_REASONS:
                parts.append(f"{'▲' if c[j] > 0 else '▼'} {desc} ({eff_txt})")
        texts.append("; ".join(parts))
    return texts, pd.DataFrame(long_rows)


def make_model(seed=42, objective="reg:squarederror"):
    return XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                        subsample=0.9, random_state=seed, objective=objective)


def evaluate(train_df, feature_cols, target, objective="reg:squarederror"):
    """Time-based test: the last TEST_MONTHS complete months are held out."""
    done = train_df.copy()
    done["ym"] = done["year"] * 12 + done["month"]
    months = np.sort(done["ym"].unique())
    cutoff = months[-TEST_MONTHS]
    tr, te = done[done["ym"] < cutoff], done[done["ym"] >= cutoff]

    model = make_model(objective=objective).fit(tr[feature_cols], tr[target])
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
        # fair simple guess when part of the month is known: straight-line projection
        "mae_straight_line": (round(mean_absolute_error(te[target], te["pace"]), 1)
                              if "pace" in feature_cols else np.nan),
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
    base_cols = (["nbhd_enc", "month", "season"] + LAG_COLS + context
                 + (WEATHER_COLS if USE_WEATHER else []))
    exposure = [c for c in EXPOSURE_COLS if c in df.columns]
    if not exposure:
        print("NOTE: no exposure columns in features.csv (run get_exposure.py + merge_weather.py)")

    # Predict the current month (today's date). It's in progress, so it is never trained on.
    today = date.today()
    pred_year, pred_month = today.year, today.month
    if not ((df["year"] == pred_year) & (df["month"] == pred_month)).any():
        raise SystemExit(f"No rows for {today:%B %Y} — re-run prep_data.py to refresh the 311 data.")
    print(f"Predicting for {today:%B %Y} (season {season_from_month(pred_month)}).")

    # How much of the current month we already have reports for
    daily, frac, cutoff = None, 0.0, 0
    if os.path.exists(DAILY_PATH):
        daily = pd.read_csv(DAILY_PATH)
        cutoff = so_far_cutoff(daily, pred_year, pred_month)
        frac = cutoff / pd.Period(f"{pred_year}-{pred_month:02d}").days_in_month
        print(f"Reports so far this month: days 1-{cutoff} ({frac:.0%} of the month).")
    else:
        print(f"NOTE: {DAILY_PATH} not found (re-run prep_data.py) — 'so far this month' skipped.")

    accuracy, predictions, all_reasons = [], None, []
    for mode, (target, pred_col, risk_col, label) in TARGETS.items():
        objective = OBJECTIVE[mode]
        feature_cols = base_cols + (exposure if USE_EXPOSURE[mode] else [])
        data = add_lag_features(df, target)
        use_so_far = USE_SO_FAR[mode] and daily is not None and cutoff > 0
        if use_so_far:
            data = add_so_far_features(data, daily, frac)
            feature_cols = feature_cols + SO_FAR_COLS
        train = data[(data["complete"] == 1)].dropna(subset=LAG_COLS + [target])

        scores = evaluate(train, feature_cols, target, objective)
        print(f"\n{label} [{objective}, {len(feature_cols)} features]: "
              f"test {scores['test_period']}, avg {scores['mean_actual']} per area-month")
        print(f"  model MAE {scores['mae']}  |  'same as last month' {scores['mae_last_month']}"
              f"  |  'same month last year' {scores['mae_last_year']}  |  success {scores['success_pct']:.0f}%")
        if use_so_far:
            print(f"  (with days 1-{cutoff} known) straight-line projection MAE {scores['mae_straight_line']}")
        accuracy.append({"mode": mode, "label": label, **scores,
                         "data_through_day": cutoff if use_so_far else 0})

        # Retrain on every complete month, then predict the current month
        model = make_model(objective=objective).fit(train[feature_cols], train[target])
        imp = (pd.DataFrame({"feature": feature_cols, "importance": model.feature_importances_.round(3)})
               .sort_values("importance", ascending=False))
        imp_path = ("data/processed/feature_importance.csv" if mode == "pothole"
                    else f"data/processed/feature_importance_{mode}.csv")
        imp.to_csv(imp_path, index=False)

        cur = data[(data["year"] == pred_year) & (data["month"] == pred_month)].copy()
        raw = np.clip(model.predict(cur[feature_cols]), 0, None)
        pred = raw
        if use_so_far:
            # a month can't end with fewer reports than were already filed
            pred = np.maximum(raw, cur["so_far"].values)
            cur["potholes_so_far"] = cur["so_far"].astype(int)
        cur[pred_col] = pred.round().astype(int)
        cur[risk_col] = risk_from(cur[pred_col])

        # --- why: top inputs behind each area's prediction ---
        why_col = "why_" + pred_col.replace("predicted_", "")
        unit = "potholes" if mode == "pothole" else "reports"
        texts, long = explain(model, cur, feature_cols, objective, pred_month, cutoff, unit)
        floored = pred > raw + 0.5
        cur[why_col] = [t + (" — raised to the count already reported" if fl else "")
                        for t, fl in zip(texts, floored)]
        long.insert(1, "mode", mode)
        all_reasons.append(long)

        keep = cur[["neighborhood", pred_col, risk_col, why_col]
                   + (["potholes_so_far"] if use_so_far else [])]
        predictions = keep if predictions is None else predictions.merge(keep, on="neighborhood")

    pd.DataFrame(accuracy).to_csv("data/processed/model_accuracy.csv", index=False)
    pd.concat(all_reasons).to_csv(REASONS_PATH, index=False)
    print(f"\nSaved model_accuracy.csv, feature_importance*.csv and {REASONS_PATH}")

    coords = df.groupby("neighborhood")[["lat", "lon"]].first() if "lat" in df.columns else None
    out = predictions.copy()
    out["lat"] = out["neighborhood"].map(coords["lat"]) if coords is not None else np.nan
    out["lon"] = out["neighborhood"].map(coords["lon"]) if coords is not None else np.nan
    out["lat"] = out["lat"].fillna(DEFAULT_COORDS[0])
    out["lon"] = out["lon"].fillna(DEFAULT_COORDS[1])
    out["predict_year"], out["predict_month"] = pred_year, pred_month
    out["data_through_day"] = cutoff
    cols = ["neighborhood", "predicted_reports", "predicted_potholes", "lat", "lon",
            "risk_level", "risk_level_pothole", "predict_year", "predict_month", "data_through_day",
            "why_potholes", "why_reports"]
    if "potholes_so_far" in out.columns:
        cols.insert(3, "potholes_so_far")
    out = out.sort_values("predicted_potholes", ascending=False)[cols]

    os.makedirs("data/processed", exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\nDone! Saved {len(out)} rows to {OUT_PATH}")
    print(out.drop(columns=["why_potholes", "why_reports"]).to_string(index=False))
    print("\nWhy (potholes):")
    for _, r in out.iterrows():
        print(f"  {r['neighborhood']}: {r['predicted_potholes']} — {r['why_potholes']}")


if __name__ == "__main__":
    main()
