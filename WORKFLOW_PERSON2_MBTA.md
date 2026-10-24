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

## Step 1 — Get MBTA data

Make `src/get_mbta.py`. It downloads the MBTA GTFS zip and turns it into
one small file: how many bus stops sit near each neighborhood.

Source (no login, no key): https://cdn.mbta.com/MBTA_GTFS.zip

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

Run it:

```bash
python src/get_mbta.py
```

Makes `data/processed/mbta.csv` with columns: `neighborhood, bus_stops_near`.

---

## Step 2 — Add MBTA to the model's feature file

The model trains on `data/processed/features.csv`. Add one line to
`src/merge_weather.py` so it joins your MBTA file on `neighborhood`.

Find this line near the end of `src/merge_weather.py`:

```python
    merged = counts.merge(weather, on=["year", "month"], how="left")
```

Add right after it:

```python
    # --- add MBTA bus-stop feature ---
    mbta = pd.read_csv("data/processed/mbta.csv")
    merged = merged.merge(mbta, on="neighborhood", how="left")
    merged["bus_stops_near"] = merged["bus_stops_near"].fillna(0)
```

Then rebuild the feature file:

```bash
python src/merge_weather.py
```

`features.csv` now has a `bus_stops_near` column.

---

## Step 3 — Make the model use the new column

Open `src/train_xgboost.py`. Find:

```python
WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
```

Add MBTA to the feature list used for training:

```python
WEATHER_COLS = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
EXTRA_COLS   = ["bus_stops_near"]
```

Then find:

```python
    feature_cols = ["nbhd_enc", "month"] + WEATHER_COLS
```

Change to:

```python
    feature_cols = ["nbhd_enc", "month"] + WEATHER_COLS + EXTRA_COLS
```

And in the "predict next month" loop, add the MBTA value per neighborhood
when building `feat` (look up `bus_stops_near` for that neighborhood).

---

## Step 4 — Train and check

```bash
python src/train_xgboost.py
```

It prints two things. Check both:

| Print | What it means | What you want |
|---|---|---|
| `Test MAE` | how far off the guess is | lower than before |
| `Feature importance` | which inputs mattered | `bus_stops_near` > 0 |

If `bus_stops_near` shows up in importance with a value above 0, the model
learned from MBTA. Done.

Makes `data/processed/predictions.csv`.

---

## When you finish

```bash
git add src/get_mbta.py src/merge_weather.py src/train_xgboost.py data/processed/mbta.csv data/processed/features.csv data/processed/predictions.csv
git commit -m "Add MBTA bus-stop feature and retrain model"
git push origin dev
```

**Risk:** only one person trains the model at a time. Two trainers at once
may run the machine out of memory.
