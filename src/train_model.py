"""
PERSON 2 — Model Training
=========================
Reads report_counts.csv and trains a Random Forest to predict
next month's report count per neighborhood.

Run: python src/train_model.py

Input:  data/processed/report_counts.csv
Output: data/processed/predictions.csv
  columns: neighborhood, predicted_reports, risk_level, lat, lon

NOTE: A fake report_counts.csv is already in data/processed/ so you
      can run this immediately. Re-run once Person 1 delivers the real one.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import os

IN_PATH  = "data/processed/report_counts.csv"
OUT_PATH = "data/processed/predictions.csv"

# Approximate neighborhood centroids for the map
NEIGHBORHOOD_COORDS = {
    "Dorchester":      (42.3021, -71.0707),
    "Roxbury":         (42.3142, -71.0920),
    "South Boston":    (42.3388, -71.0468),
    "Jamaica Plain":   (42.3100, -71.1148),
    "East Boston":     (42.3784, -71.0282),
    "Allston":         (42.3534, -71.1312),
    "Brighton":        (42.3467, -71.1564),
    "Back Bay":        (42.3503, -71.0810),
    "Beacon Hill":     (42.3588, -71.0707),
    "Charlestown":     (42.3782, -71.0602),
    "Hyde Park":       (42.2551, -71.1243),
    "Mattapan":        (42.2736, -71.0921),
    "Roslindale":      (42.2840, -71.1284),
    "West Roxbury":    (42.2793, -71.1607),
    "South End":       (42.3398, -71.0786),
    "Fenway":          (42.3467, -71.1003),
    "Mission Hill":    (42.3278, -71.1003),
    "North End":       (42.3647, -71.0542),
    "South Dorchester":(42.2883, -71.0638),
}

# --- Load ---
print("Loading report_counts.csv ...")
df = pd.read_csv(IN_PATH)

# Detect fake placeholder and warn
if df["report_count"].astype(str).str.upper().eq("FAKE").any():
    print("WARNING: Using fake placeholder data. Re-run after Person 1 finishes.")
    # Generate synthetic counts so the script still runs
    import random
    random.seed(42)
    df["report_count"] = [random.randint(10, 200) for _ in range(len(df))]

df["report_count"] = pd.to_numeric(df["report_count"], errors="coerce").fillna(0)

# --- Encode neighborhood ---
le = LabelEncoder()
df["nbhd_enc"] = le.fit_transform(df["neighborhood"].astype(str))

# --- Features: neighborhood encoding + month + year ---
X = df[["nbhd_enc", "month", "year"]].values
y = df["report_count"].values

# --- Train ---
print("Training Random Forest ...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)
print("Training complete.")

# --- Predict next month for each neighborhood ---
next_month = 11   # November (change as needed)
next_year  = 2024

neighborhoods = df["neighborhood"].unique()
rows = []
for nbhd in neighborhoods:
    enc = le.transform([nbhd])[0] if nbhd in le.classes_ else 0
    pred = model.predict([[enc, next_month, next_year]])[0]
    lat, lon = NEIGHBORHOOD_COORDS.get(nbhd, (42.36, -71.06))
    rows.append({
        "neighborhood": nbhd,
        "predicted_reports": round(pred),
        "lat": lat,
        "lon": lon,
    })

out = pd.DataFrame(rows).sort_values("predicted_reports", ascending=False)

# Assign risk level: top 30% high, next 40% medium, rest low
out["rank_pct"] = out["predicted_reports"].rank(pct=True)
out["risk_level"] = out["rank_pct"].apply(
    lambda p: "high" if p >= 0.70 else ("medium" if p >= 0.30 else "low")
)
out = out.drop(columns="rank_pct")

os.makedirs("data/processed", exist_ok=True)
out.to_csv(OUT_PATH, index=False)
print(f"\nDone! Saved {len(out)} rows to {OUT_PATH}")
print(out.to_string(index=False))
