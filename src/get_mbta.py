#!/usr/bin/env python3
"""
LIVE MBTA transit features per neighborhood.
Source: https://cdn.mbta.com/MBTA_GTFS.zip  (live GTFS feed, no key)

Instead of one bus-stop count near a centroid, this pulls the full live
feed and, using the real neighborhood polygons, computes THREE signals per
neighborhood so the model has more to learn from:

  bus_stops_near   - number of bus stops inside the neighborhood
  rail_stops_near  - number of subway/light-rail/commuter-rail stops
  route_count      - number of DISTINCT routes serving those stops

Run: python src/get_mbta.py
Output: data/processed/mbta.csv
  columns: neighborhood, bus_stops_near, rail_stops_near, route_count
"""

import urllib.request, ssl, zipfile, io, os
import pandas as pd
import geopandas as gpd

ssl._create_default_https_context = ssl._create_unverified_context

GTFS_URL   = "https://cdn.mbta.com/MBTA_GTFS.zip"
HOODS_LOCAL = "data/raw/neighborhoods.geojson"
OUT_PATH   = "data/processed/mbta.csv"

# GTFS route_type: 0 tram/light-rail, 1 subway, 2 rail, 3 bus, 4 ferry
RAIL_TYPES = {0, 1, 2}
BUS_TYPES  = {3}


def load_gtfs():
    print("Downloading LIVE MBTA GTFS feed ...")
    req = urllib.request.Request(GTFS_URL, headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.read()))
    stops      = pd.read_csv(z.open("stops.txt"))
    routes     = pd.read_csv(z.open("routes.txt"))
    trips      = pd.read_csv(z.open("trips.txt"))
    stop_times = pd.read_csv(z.open("stop_times.txt"), usecols=["trip_id", "stop_id"])
    return stops, routes, trips, stop_times


def main():
    stops, routes, trips, stop_times = load_gtfs()
    stops = stops.dropna(subset=["stop_lat", "stop_lon"]).copy()
    print(f"Live feed: {len(stops)} stops, {len(routes)} routes")

    # Map each stop -> the route_types and route_ids that serve it
    rt_type = routes.set_index("route_id")["route_type"].to_dict()
    trip_route = trips.set_index("trip_id")["route_id"].to_dict()
    st = stop_times.copy()
    st["route_id"] = st["trip_id"].map(trip_route)
    st = st.dropna(subset=["route_id"])
    st["route_type"] = st["route_id"].map(rt_type)

    # per stop: set of routes, and whether it is served by bus / rail
    by_stop = st.groupby("stop_id").agg(
        routes=("route_id", lambda s: set(s)),
        types=("route_type", lambda s: set(s)),
    )
    stops = stops.merge(by_stop, left_on="stop_id", right_index=True, how="left")
    stops["routes"] = stops["routes"].apply(lambda v: v if isinstance(v, set) else set())
    stops["types"]  = stops["types"].apply(lambda v: v if isinstance(v, set) else set())

    # Point-in-polygon against the real neighborhood shapes
    hoods = gpd.read_file(HOODS_LOCAL).to_crs("EPSG:4326")
    hoods = hoods.rename(columns={"blockgr2020_ctr_neighb_name": "neighborhood"})[["neighborhood", "geometry"]]
    gstops = gpd.GeoDataFrame(
        stops, geometry=gpd.points_from_xy(stops["stop_lon"], stops["stop_lat"]), crs="EPSG:4326"
    )
    joined = gpd.sjoin(gstops, hoods, how="inner", predicate="within")

    rows = []
    for nbhd, grp in joined.groupby("neighborhood"):
        is_bus  = grp["types"].apply(lambda s: bool(s & BUS_TYPES))
        is_rail = grp["types"].apply(lambda s: bool(s & RAIL_TYPES))
        all_routes = set().union(*grp["routes"]) if len(grp) else set()
        rows.append({
            "neighborhood":   nbhd,
            "bus_stops_near":  int(is_bus.sum()),
            "rail_stops_near": int(is_rail.sum()),
            "route_count":     len(all_routes),
        })

    out = pd.DataFrame(rows).sort_values("bus_stops_near", ascending=False)
    os.makedirs("data/processed", exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(out)} neighborhoods to {OUT_PATH}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
