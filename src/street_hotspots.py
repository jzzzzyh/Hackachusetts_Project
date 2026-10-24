"""
Street-level pothole hotspots
=============================
Turns each neighborhood's predicted pothole total (predictions.csv) into a
per-STREET forecast, so the map can point at actual streets.

Run (after train_xgboost.py): python src/street_hotspots.py

How it works
  1. Every pothole report since 2022 (lat/lon) is snapped to the nearest
     street segment of Boston's managed-streets map (within 60 m).
     A "street" = one street name inside one neighborhood
     (Washington St in Roxbury and in Dorchester are separate rows).
  2. Each street's share of its neighborhood = its recent reports,
     weighted so that newer months count more (half-life 12 months, 36 months back).
  3. This month: street forecast = reports already filed on that street
     + the neighborhood's REMAINING predicted potholes x the street's share.
  4. Back-test: the same split is replayed on the last 12 complete months
     (using the real neighborhood totals, so only the street split is scored)
     and compared with splitting by road length.

Inputs:  data/raw/311_*.csv, data/raw/311_new_system.csv  (prep_data.py)
         data/raw/managed_streets.geojson                  (get_exposure.py)
         data/processed/predictions.csv                    (train_xgboost.py)
Outputs: data/processed/street_predictions.csv      one row per street
         data/processed/street_predictions.geojson  same + street lines, for the map
         data/processed/street_accuracy.csv         back-test results
"""

import os
from datetime import date

import geopandas as gpd
import numpy as np
import pandas as pd

from prep_data import canon_neighborhood

STREETS_PATH = "data/raw/managed_streets.geojson"
PRED_PATH = "data/processed/predictions.csv"
OUT_CSV = "data/processed/street_predictions.csv"
OUT_GEO = "data/processed/street_predictions.geojson"
ACC_PATH = "data/processed/street_accuracy.csv"

FIRST_YEAR = 2022        # history needed: 36 months before the oldest back-test month
HISTORY_MONTHS = 36
HALF_LIFE = 12           # months; a report 12 months old counts half as much
SNAP_METERS = 60
METRIC_CRS = "EPSG:26986"  # Massachusetts state plane, meters
HIGH_N, MEDIUM_N = 50, 200   # citywide street ranks for high / medium risk
TEST_MONTHS = 12


# ---------------------------------------------------------------- loading
def load_pothole_points() -> pd.DataFrame:
    """All pothole reports since FIRST_YEAR with location, canonical area and date."""
    parts = []
    today = date.today()
    for year in range(FIRST_YEAR, today.year + 1):
        path = f"data/raw/311_{year}.csv"
        if not os.path.exists(path):
            raise SystemExit(f"{path} missing — run `python src/prep_data.py` first.")
        d = pd.read_csv(path, usecols=["open_dt", "type", "neighborhood", "latitude", "longitude"],
                        low_memory=False)
        d = d[d["type"].astype(str).str.lower().str.contains("pothole")]
        parts.append(pd.DataFrame({"dt": pd.to_datetime(d["open_dt"], errors="coerce", format="mixed"),
                                   "nbhd": d["neighborhood"], "lat": d["latitude"], "lon": d["longitude"]}))
    new = "data/raw/311_new_system.csv"
    if os.path.exists(new):
        n = pd.read_csv(new, usecols=["open_date", "service_name", "neighborhood", "latitude", "longitude"],
                        low_memory=False)
        n = n[n["service_name"].astype(str).str.lower().str.contains("pothole")]
        dt = pd.to_datetime(n["open_date"], errors="coerce", utc=True, format="mixed")
        parts.append(pd.DataFrame({"dt": dt.dt.tz_convert("America/New_York").dt.tz_localize(None),
                                   "nbhd": n["neighborhood"], "lat": n["latitude"], "lon": n["longitude"]}))
    p = pd.concat(parts, ignore_index=True)
    p["neighborhood"] = p["nbhd"].map(canon_neighborhood)
    p = p.dropna(subset=["dt", "neighborhood", "lat", "lon"])
    p = p[p["lat"].between(42.2, 42.45) & p["lon"].between(-71.2, -70.95)]   # inside Boston
    p["year"], p["month"], p["day"] = p["dt"].dt.year, p["dt"].dt.month, p["dt"].dt.day
    p["ym"] = p["year"] * 12 + p["month"] - 1
    return p.drop(columns=["nbhd", "dt"])


def snap_to_streets(points: pd.DataFrame, streets: gpd.GeoDataFrame) -> pd.DataFrame:
    """Attach the nearest street segment (within SNAP_METERS) to every report."""
    pts = gpd.GeoDataFrame(points, geometry=gpd.points_from_xy(points["lon"], points["lat"]),
                           crs="EPSG:4326").to_crs(METRIC_CRS)
    joined = gpd.sjoin_nearest(pts, streets[["seg", "street", "geometry"]], how="left",
                               max_distance=SNAP_METERS, distance_col="dist_m")
    joined = joined[~joined.index.duplicated()]          # ties: keep one segment
    print(f"Reports snapped to a street within {SNAP_METERS} m: "
          f"{joined['seg'].notna().mean():.1%} of {len(joined):,}")
    return pd.DataFrame(joined.dropna(subset=["seg"]).drop(columns=["geometry", "index_right"]))


def load_streets() -> gpd.GeoDataFrame:
    if not os.path.exists(STREETS_PATH):
        raise SystemExit(f"{STREETS_PATH} missing — run `python src/get_exposure.py` first.")
    s = gpd.read_file(STREETS_PATH).to_crs(METRIC_CRS)
    s["street"] = s["STREETNAME"].fillna(s["STREET_NAM"]).astype(str).str.strip().str.title()
    s = s[~s["street"].isin(["", "None", "Nan"])].copy()
    s["seg"] = np.arange(len(s))
    s["block"] = ("between " + s["FM_ST_NAME"].astype(str).str.title() + " and "
                  + s["TO_ST_NAME"].astype(str).str.title())
    return s[["seg", "street", "block", "LENGTH_MI", "geometry"]]


# ---------------------------------------------------------------- the split
def street_shares(points: pd.DataFrame, before_ym: int) -> pd.DataFrame:
    """Recency-weighted share of each street within its neighborhood, using months < before_ym."""
    h = points[(points["ym"] < before_ym) & (points["ym"] >= before_ym - HISTORY_MONTHS)]
    w = 0.5 ** ((before_ym - 1 - h["ym"]) / HALF_LIFE)
    s = h.assign(w=w).groupby(["neighborhood", "street"])["w"].sum().rename("weight").reset_index()
    s["share"] = s["weight"] / s.groupby("neighborhood")["weight"].transform("sum")
    return s


def split_month(points, ym, area_totals, cutoff_day):
    """Street forecast for month ym, given each area's total and reports up to cutoff_day."""
    shares = street_shares(points, ym)
    cur = points[(points["ym"] == ym) & (points["day"] <= cutoff_day)]
    so_far = cur.groupby(["neighborhood", "street"]).size().rename("so_far").reset_index()
    s = shares.merge(so_far, on=["neighborhood", "street"], how="outer").fillna({"share": 0, "so_far": 0, "weight": 0})
    area_so_far = s.groupby("neighborhood")["so_far"].transform("sum")
    remaining = (s["neighborhood"].map(area_totals).fillna(0) - area_so_far).clip(lower=0)
    s["predicted"] = s["so_far"] + remaining * s["share"]
    return s


# ---------------------------------------------------------------- back-test
def backtest(points, streets, last_complete_ym, cutoff_frac):
    """Replay the split on the last TEST_MONTHS complete months with real area totals."""
    length = (streets.assign(n=None).merge(
        points.groupby(["neighborhood", "seg"]).size().rename("n").reset_index()[["neighborhood", "seg"]],
        on="seg")[["neighborhood", "street", "LENGTH_MI"]]
        .drop_duplicates().groupby(["neighborhood", "street"])["LENGTH_MI"].sum())
    rows = []
    for ym in range(last_complete_ym - TEST_MONTHS + 1, last_complete_ym + 1):
        y, m = divmod(ym, 12)
        days = pd.Period(f"{y}-{m + 1:02d}").days_in_month
        actual = points[points["ym"] == ym].groupby(["neighborhood", "street"]).size().rename("actual")
        totals = actual.groupby(level=0).sum()
        for label, cutoff in [("start of month", 0), (f"{cutoff_frac:.0%} of month known", int(cutoff_frac * days))]:
            s = split_month(points, ym, totals, cutoff).set_index(["neighborhood", "street"])
            s = s.join(actual, how="outer").fillna(0)
            # naive: split each area's REMAINING potholes by road length instead of history
            ln = length.reindex(s.index).fillna(0)
            ln_share = ln / ln.groupby(level=0).transform("sum").replace(0, np.nan)
            rem = (s.index.get_level_values(0).map(totals).fillna(0).values
                   - s["so_far"].groupby(level=0).transform("sum").values).clip(min=0)
            s["by_length"] = s["so_far"] + rem * ln_share.fillna(0).values
            top_actual = set(s["actual"].nlargest(HIGH_N).index)
            for method, col in [("history split", "predicted"), ("road-length split", "by_length")]:
                rows.append({"month": f"{y}-{m + 1:02d}", "known": label, "method": method,
                             "mae_per_street": (s[col] - s["actual"]).abs().mean(),
                             "top50_hit": len(top_actual & set(s[col].nlargest(HIGH_N).index)) / HIGH_N,
                             "share_in_top200": s.loc[s[col].nlargest(MEDIUM_N).index, "actual"].sum()
                                                / max(s["actual"].sum(), 1)})
    r = pd.DataFrame(rows)
    summary = r.groupby(["known", "method"])[["mae_per_street", "top50_hit", "share_in_top200"]].mean().round(3)
    return summary.reset_index()


# ---------------------------------------------------------------- main
def main():
    preds = pd.read_csv(PRED_PATH)
    if "predicted_potholes" not in preds.columns:
        raise SystemExit("predictions.csv has no pothole predictions — run train_xgboost.py first.")
    year, month = int(preds["predict_year"].iloc[0]), int(preds["predict_month"].iloc[0])
    cutoff = int(preds.get("data_through_day", pd.Series([0])).iloc[0])
    ym = year * 12 + month - 1
    days = pd.Period(f"{year}-{month:02d}").days_in_month

    print("Loading pothole reports and streets ...")
    streets = load_streets()
    points = snap_to_streets(load_pothole_points(), streets)

    # --- back-test the street split ---
    acc = backtest(points, streets, ym - 1, cutoff / days if cutoff else 0.5)
    acc.to_csv(ACC_PATH, index=False)
    print("\nBack-test, last 12 complete months (real area totals; only the street split is scored):")
    print(acc.to_string(index=False))

    # --- this month's street forecast ---
    totals = preds.set_index("neighborhood")["predicted_potholes"]
    s = split_month(points, ym, totals, cutoff)
    past12 = points[(points["ym"] < ym) & (points["ym"] >= ym - 12)].groupby(
        ["neighborhood", "street"]).size().rename("past_12_months")
    s = s.merge(past12.reset_index(), on=["neighborhood", "street"], how="left").fillna({"past_12_months": 0})
    s = s[s["predicted"] >= 0.5].sort_values("predicted", ascending=False).reset_index(drop=True)
    s["rank"] = np.arange(1, len(s) + 1)
    s["risk"] = np.where(s["rank"] <= HIGH_N, "high", np.where(s["rank"] <= MEDIUM_N, "medium", "low"))

    # worst block = segment with the most reports in the last 12 months
    recent = points[(points["ym"] < ym) & (points["ym"] >= ym - 12)]
    blk = (recent.groupby(["neighborhood", "street", "seg"]).size().rename("n").reset_index()
           .sort_values("n", ascending=False).drop_duplicates(["neighborhood", "street"])
           .merge(streets[["seg", "block"]], on="seg"))
    s = s.merge(blk[["neighborhood", "street", "block", "n"]], on=["neighborhood", "street"], how="left")

    area_pred = s["neighborhood"].map(totals)
    s["why"] = [
        f"{int(r.past_12_months)} potholes reported here in the last 12 months "
        f"({r.share:.0%} of {r.neighborhood}'s recent reports, newer ones weighted more)"
        + (f"; {int(r.so_far)} already this month (days 1-{cutoff})" if cutoff else "")
        + f"; {r.neighborhood} is predicted {int(ap)} this month"
        + (f"; worst block {r.block} ({int(r.n)} in 12 months)" if isinstance(r.block, str) else "")
        for r, ap in zip(s.itertuples(), area_pred)
    ]
    s["predicted"] = s["predicted"].round(1)
    s["so_far"] = s["so_far"].astype(int)
    s["past_12_months"] = s["past_12_months"].astype(int)
    out = s[["rank", "neighborhood", "street", "predicted", "so_far", "past_12_months",
             "share", "risk", "block", "why"]].rename(columns={"predicted": "predicted_potholes",
                                                              "so_far": "potholes_so_far",
                                                              "block": "worst_block"})
    out["share"] = out["share"].round(4)
    out.to_csv(OUT_CSV, index=False)

    # --- line geometry: the segments where this street's reports land (inside its area) ---
    used = points[["neighborhood", "street", "seg"]].drop_duplicates()
    geo = streets[["seg", "geometry"]].merge(used, on="seg")
    geo = geo.dissolve(by=["neighborhood", "street"]).reset_index()[["neighborhood", "street", "geometry"]]
    geo["geometry"] = geo.geometry.simplify(5)
    geo = gpd.GeoDataFrame(out.merge(geo, on=["neighborhood", "street"]), crs=METRIC_CRS).to_crs("EPSG:4326")
    geo.to_file(OUT_GEO, driver="GeoJSON")

    print(f"\nDone! {len(out)} streets -> {OUT_CSV} and {OUT_GEO}")
    print(out.head(15).drop(columns=["why", "share"]).to_string(index=False))
    print("\nWhy (top 3):")
    for r in out.head(3).itertuples():
        print(f"  {r.street}, {r.neighborhood}: {r.predicted_potholes} — {r.why}")


if __name__ == "__main__":
    main()
