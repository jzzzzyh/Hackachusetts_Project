# Workflow — Person 2: MBTA Routes + Train the Model

Your job, start to end: pull MBTA route data, add it to the model's
feature file, then train the model and check it learned from the new data.

---

## First, every time

```bash
git pull origin dev
pip install -r requirements.txt
```

---

## Step 1 — Prepare your environment

Sync your local branch with the dev branch and ensure all dependencies are installed.

```bash
git pull origin dev
pip install -r requirements.txt
```

**What this does:** Pulls the latest code and installs required packages so you're working with the current state of the project.

---

## Step 2 — Download and process MBTA data

Create `src/get_mbta.py`. This script downloads the MBTA GTFS zip file and counts how many bus stops sit near each neighborhood centroid.

**Source:** https://cdn.mbta.com/MBTA_GTFS.zip (no login or key required)

```python
# src/get_mbta.py
# Download MBTA GTFS, count bus stops near each neighborhood centroid.
import urllib.request, zipfile, io, os
import pandas as pd
from math import radians, cos, sin, asin, sqrt

# Same neighborhood centroids the model uses (from src/train_xgboost.py)
NEIGHBORHOOD_COORDS = {
    "Dorchester": (42.3021, -71.0707),
    "South Boston": (42.3388, -71.0468),
    "South End": (42.3398, -71.0786),
    "Roxbury": (42.3142, -71.0920),
    "East Boston": (42.3784, -71.0282),
    "Back Bay": (42.3503, -71.0810),
    "Jamaica Plain": (42.3100, -71.1148),
    "Charlestown": (42.3782, -71.0602),
    # add the rest from train_xgboost.py as needed
}

def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * asin(sqrt(d)) * 6371

def main():
    url = "https://cdn.mbta.com/MBTA_GTFS.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=60)
    z = zipfile.ZipFile(io.BytesIO(r.read()))

    stops  = pd.read_csv(z.open("stops.txt"))
    routes = pd.read_csv(z.open("routes.txt"))

    # keep bus routes only (route_type == 3) -> their stop ids, if trips linked
    # simple version: use all stops with lat/lon
    stops = stops.dropna(subset=["stop_lat", "stop_lon"])

    rows = []
    for nbhd, (lat, lon) in NEIGHBORHOOD_COORDS.items():
        near = stops.apply(
            lambda s: haversine_km(lat, lon, s.stop_lat, s.stop_lon) <= 0.5,
            axis=1,
        ).sum()
        rows.append({"neighborhood": nbhd, "bus_stops_near": int(near)})

    os.makedirs("data/processed", exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv("data/processed/mbta.csv", index=False)
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
```

Run the script:

```bash
python src/get_mbta.py
```

**Output:** Creates `data/processed/mbta.csv` with columns: `neighborhood, bus_stops_near`. Verify it looks correct by reviewing the printed output.

---

## Step 3 — Integrate MBTA data into the feature pipeline

Add the MBTA data to the model's feature file by modifying `src/merge_weather.py`.

Find this line near the end of the file:

```python
    merged = counts.merge(weather, on=["year", "month"], how="left")
```

Add these lines immediately after it:

```python
    # --- add MBTA bus-stop feature ---
    mbta = pd.read_csv("data/processed/mbta.csv")
    merged = merged.merge(mbta, on="neighborhood", how="left")
    merged["bus_stops_near"] = merged["bus_stops_near"].fillna(0)
```

Rebuild the feature file:

```bash
python src/merge_weather.py
```

**Output:** `data/processed/features.csv` now includes a `bus_stops_near` column. Verify the file was updated and contains this new column.

---

## Step 4 — Update the model to use the new feature

Modify `src/train_xgboost.py` to include the MBTA bus-stop count in training.

**Part A:** Find the feature column definitions:

```python
WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
```

Add MBTA to the list:

```python
WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
EXTRA_COLS   = ["bus_stops_near"]
```

**Part B:** Find the line that builds the feature column list:

```python
    feature_cols = ["nbhd_enc", "month"] + WEATHER_COLS
```

Update it to include the new column:

```python
    feature_cols = ["nbhd_enc", "month"] + WEATHER_COLS + EXTRA_COLS
```

**Part C:** In the "predict next month" loop, add the MBTA value per neighborhood when building the `feat` dictionary. Look up `bus_stops_near` for each neighborhood.

**Verification:** The code should compile without errors. Check that all feature columns are correctly referenced.

---

## Step 5 — Train the model and verify improvements

Train the model with the new MBTA feature:

```bash
python src/train_xgboost.py
```

**Review the output:** Check both metrics below to confirm the model learned from MBTA data:

| Metric | Meaning | Success Condition |
|--------|---------|------------------|
| `Test MAE` | How far off the predictions are, on average | Lower than before (smaller error) |
| `Feature importance` | Which inputs contributed most to predictions | `bus_stops_near` appears with a value > 0 |

If `bus_stops_near` shows up in the feature importance list with a non-zero value, the model successfully learned from the MBTA data.

**Output:** Creates/updates `data/processed/predictions.csv` with new predictions.

---

## Commit and push your changes

Once training completes and you've verified the metrics:

```bash
git add src/get_mbta.py src/merge_weather.py src/train_xgboost.py data/processed/mbta.csv data/processed/features.csv data/processed/predictions.csv
git commit -m "Add MBTA bus-stop feature and retrain model"
git push origin dev
```

**Risk:** Only one person should train the model at a time. Two concurrent trainers may exhaust available memory.
