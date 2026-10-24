"""
STEP 5 — Weather Data Fetch
===========================
Pulls 2024 daily weather for Boston from the Open-Meteo Archive API
(free, no API key) and aggregates it to monthly values.

Run: python src/fetch_weather.py

Output: data/processed/weather_monthly.csv
  columns: year, month, avg_temp_c, total_precip_mm, total_snow_cm, max_wind_kmh

Why weather? Rain/snow/freeze cause potholes and sidewalk damage, which
drive 311 reports. Weather is the live, adaptive feed the model needs.

Step 6 merges this with report_counts.csv by year + month.
"""

import requests
import pandas as pd
import os
from datetime import date, timedelta

# Boston city-center coordinates (one weather point for the whole city —
# neighborhoods are too close together for weather to differ meaningfully).
LAT, LON = 42.3601, -71.0589

OUT_PATH = "data/processed/weather_monthly.csv"

# Open-Meteo historical archive endpoint (free, no key, no rate limit for this size)
URL = "https://archive-api.open-meteo.com/v1/archive"

PARAMS = {
    "latitude": LAT,
    "longitude": LON,
    "start_date": "2015-01-01",
    # archive lags real time by a few days -> stop a week back
    "end_date": (date.today() - timedelta(days=7)).isoformat(),
    "daily": ",".join([
        "temperature_2m_mean",
        "temperature_2m_min",
        "temperature_2m_max",
        "precipitation_sum",
        "snowfall_sum",
        "wind_speed_10m_max",
    ]),
    "timezone": "America/New_York",
}


def main():
    print(f"Fetching Boston weather {PARAMS['start_date']} -> {PARAMS['end_date']} from Open-Meteo ...")
    resp = requests.get(URL, params=PARAMS, timeout=60)
    resp.raise_for_status()
    data = resp.json()["daily"]

    df = pd.DataFrame({
        "date":        pd.to_datetime(data["time"]),
        "temp_c":      data["temperature_2m_mean"],
        "temp_min_c":  data["temperature_2m_min"],
        "temp_max_c":  data["temperature_2m_max"],
        "precip_mm":   data["precipitation_sum"],
        "snow_cm":     data["snowfall_sum"],
        "wind_kmh":    data["wind_speed_10m_max"],
    })

    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Freeze-thaw day = daily low at/below 0C AND daily high above 0C.
    # Water in pavement cracks freezes overnight, expands, thaws by day, and
    # widens the crack — the real mechanical cause of potholes.
    df["freeze_thaw"] = ((df["temp_min_c"] <= 0) & (df["temp_max_c"] > 0)).astype(int)

    # Aggregate daily -> monthly
    monthly = df.groupby(["year", "month"]).agg(
        avg_temp_c      =("temp_c",   "mean"),
        total_precip_mm =("precip_mm", "sum"),
        total_snow_cm   =("snow_cm",   "sum"),
        max_wind_kmh    =("wind_kmh",  "max"),
        freeze_thaw_days=("freeze_thaw", "sum"),
    ).reset_index()

    monthly = monthly.round(2)

    os.makedirs("data/processed", exist_ok=True)
    monthly.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(monthly)} months to {OUT_PATH}")
    print(monthly.to_string(index=False))


if __name__ == "__main__":
    main()
