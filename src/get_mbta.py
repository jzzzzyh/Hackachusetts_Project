#!/usr/bin/env python3
"""
Download MBTA GTFS, count bus stops near each neighborhood centroid.
Source: https://cdn.mbta.com/MBTA_GTFS.zip (no login or key required)
"""

import urllib.request
import zipfile
import io
import os
import pandas as pd
from math import radians, cos, sin, asin, sqrt


# Neighborhood centroids (from src/train_xgboost.py)
NEIGHBORHOOD_COORDS = {
    "Dorchester": (42.3021, -71.0707),
    "South Boston": (42.3388, -71.0468),
    "South End": (42.3398, -71.0786),
    "Roxbury": (42.3142, -71.0920),
    "East Boston": (42.3784, -71.0282),
    "Back Bay": (42.3503, -71.0810),
    "Jamaica Plain": (42.3100, -71.1148),
    "Charlestown": (42.3782, -71.0602),
    "Brighton": (42.3519, -71.1437),
    "Allston": (42.3526, -71.1338),
    "Fenway": (42.3442, -71.0978),
    "Beacon Hill": (42.3601, -71.0650),
    "Downtown": (42.3585, -71.0636),
    "North End": (42.3655, -71.0552),
    "West End": (42.3676, -71.0764),
    "Waterfront": (42.3628, -71.0480),
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points on earth (in km)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * asin(sqrt(d)) * 6371


def main():
    """Download MBTA GTFS and count bus stops near each neighborhood."""
    print("Downloading MBTA GTFS data...")
    url = "https://cdn.mbta.com/MBTA_GTFS.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        r = urllib.request.urlopen(req, timeout=60)
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    except Exception as e:
        print(f"Error downloading MBTA data: {e}")
        return

    print("Extracting stops and routes...")
    try:
        stops = pd.read_csv(z.open("stops.txt"))
        routes = pd.read_csv(z.open("routes.txt"))
    except Exception as e:
        print(f"Error reading GTFS files: {e}")
        return

    # Filter to keep only stops with valid coordinates
    stops = stops.dropna(subset=["stop_lat", "stop_lon"])
    print(f"Found {len(stops)} stops with coordinates")

    # Count bus stops near each neighborhood (within 0.5 km)
    rows = []
    for nbhd, (lat, lon) in NEIGHBORHOOD_COORDS.items():
        near = stops.apply(
            lambda s: haversine_km(lat, lon, s.stop_lat, s.stop_lon) <= 0.5,
            axis=1,
        ).sum()
        rows.append({"neighborhood": nbhd, "bus_stops_near": int(near)})
        print(f"  {nbhd}: {int(near)} stops within 0.5 km")

    # Save to CSV
    os.makedirs("data/processed", exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv("data/processed/mbta.csv", index=False)
    
    print("\nMBTA data saved to data/processed/mbta.csv")
    print("\nSummary:")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
