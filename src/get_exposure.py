"""
Exposure per neighborhood: how much road (and how many people) each area has
=============================================================================
Bigger areas with more streets and more traffic log more potholes simply
because there is more road to break. These features let the model tell
"Mission Hill is small" from "Mission Hill is quiet".

Run: python src/get_exposure.py

Sources (data.boston.gov, no API key):
  * City of Boston Managed Streets (MassDOT road inventory, Boston only)
      road_miles          - total centerline miles
      lane_miles          - miles x lanes (wider roads = more pavement)
      daily_vehicle_miles - miles x average daily traffic (AADT)
  * 2025 Boston Population Estimates (neighborhood level)
      population

Output: data/processed/exposure.csv
  columns: neighborhood, road_miles, lane_miles, daily_vehicle_miles, population

Neighborhood labels are left as published; merge_weather.py maps them to the
311 areas and sums them.
"""

import os

import geopandas as gpd
import pandas as pd
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

STREETS_URL = ("https://data.boston.gov/dataset/14bbd7dc-07ef-4107-a7a0-42863afd5f55/"
               "resource/91608357-8efa-4bab-afc0-49647108348e/download/city_of_boston_managed_streets.geojson")
POP_URL = "https://data.boston.gov/api/3/action/datastore_search"
POP_RESOURCE = "b0543358-d03f-4682-bf0c-658ea4573d6f"
POP_COL = "population_b03002_001e"       # total population (ACS table B03002)

STREETS_LOCAL = "data/raw/managed_streets.geojson"
HOODS_LOCAL = "data/raw/neighborhoods.geojson"   # downloaded by get_trees_live.py / get_mbta.py
OUT_PATH = "data/processed/exposure.csv"


def load_streets() -> gpd.GeoDataFrame:
    if not os.path.exists(STREETS_LOCAL):
        print("Downloading Boston managed streets (~18 MB) ...")
        os.makedirs(os.path.dirname(STREETS_LOCAL), exist_ok=True)
        r = requests.get(STREETS_URL, headers=HEADERS, timeout=300)
        r.raise_for_status()
        with open(STREETS_LOCAL, "wb") as f:
            f.write(r.content)
    return gpd.read_file(STREETS_LOCAL).to_crs("EPSG:4326")


def road_exposure() -> pd.DataFrame:
    streets = load_streets()
    if not os.path.exists(HOODS_LOCAL):
        raise SystemExit(f"{HOODS_LOCAL} missing — run `python src/get_trees_live.py` first.")
    hoods = gpd.read_file(HOODS_LOCAL).to_crs("EPSG:4326")
    name_col = next(c for c in hoods.columns if "neighb" in c.lower())

    # one point per street segment, so a segment counts toward exactly one area
    pts = gpd.GeoDataFrame(
        streets[["LENGTH_MI", "AADT", "NUM_LANES"]].apply(pd.to_numeric, errors="coerce").fillna(0),
        geometry=streets.geometry.representative_point(), crs="EPSG:4326")
    joined = gpd.sjoin(pts, hoods[[name_col, "geometry"]], predicate="within")
    print(f"Street segments matched to a neighborhood: {len(joined)}/{len(streets)}")

    joined["lane_mi"] = joined["LENGTH_MI"] * joined["NUM_LANES"].clip(lower=1)
    joined["vmt"] = joined["LENGTH_MI"] * joined["AADT"]
    return (joined.groupby(name_col)
            .agg(road_miles=("LENGTH_MI", "sum"), lane_miles=("lane_mi", "sum"),
                 daily_vehicle_miles=("vmt", "sum"))
            .rename_axis("neighborhood").reset_index())


def population() -> pd.DataFrame:
    r = requests.get(POP_URL, params={"resource_id": POP_RESOURCE, "limit": 100},
                     headers=HEADERS, timeout=60)
    r.raise_for_status()
    pop = pd.DataFrame(r.json()["result"]["records"])
    pop["population"] = pd.to_numeric(pop[POP_COL], errors="coerce")
    return pop.rename(columns={"name": "neighborhood"})[["neighborhood", "population"]].dropna()


def main():
    roads = road_exposure()
    pop = population()
    out = roads.merge(pop, on="neighborhood", how="outer").fillna(0)
    out[["road_miles", "lane_miles"]] = out[["road_miles", "lane_miles"]].round(1)
    out[["daily_vehicle_miles", "population"]] = out[["daily_vehicle_miles", "population"]].round().astype(int)
    out = out.sort_values("road_miles", ascending=False)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\nDone! Saved {len(out)} neighborhoods to {OUT_PATH}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
