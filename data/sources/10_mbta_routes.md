# 10 — MBTA Bus & Rail Routes (GTFS)

## What it is
The complete MBTA transit network in GTFS format — all bus routes, subway lines, commuter rail, and ferry routes with their stop locations and route shapes.

## Why we need it
High-frequency transit routes (especially buses) cause severe road wear:
- Bus routes = heaviest vehicle traffic = fastest pavement degradation
- Bus stops = concentrated heavy braking = pothole hotspots
- Streets with multiple bus routes need more frequent repair

## Source
- URL: https://cdn.mbta.com/MBTA_GTFS.zip (direct download, no auth)
- Provider: MBTA
- License: Open Data (MBTA public data)
- Updated: weekly (live schedule)
- Spec: Google GTFS standard

## How to fetch

```python
import urllib.request, zipfile, io

url = "https://cdn.mbta.com/MBTA_GTFS.zip"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
z = zipfile.ZipFile(io.BytesIO(r.read()))
# Files inside: routes.txt, trips.txt, stops.txt, shapes.txt, stop_times.txt, etc.
z.extractall("data/raw/mbta_gtfs/")
```

## Files we need from the ZIP

| File | Contents | Used for |
|------|---------|----------|
| `routes.txt` | All routes with type (bus=3, subway=1) | filter to bus routes |
| `stops.txt` | All stop locations with lat/lon | bus stop proximity feature |
| `shapes.txt` | Route polylines (lat/lon sequences) | road segment overlay |
| `trips.txt` | Trips per route per day | frequency proxy |

## Key columns — stops.txt
| Column | Description |
|--------|-------------|
| `stop_id` | Unique stop ID |
| `stop_lat` | Latitude |
| `stop_lon` | Longitude |
| `stop_name` | Stop name |

## Key columns — routes.txt
| Column | Description |
|--------|-------------|
| `route_id` | Route ID |
| `route_type` | 0=tram, 1=subway, 3=bus, 4=ferry |
| `route_short_name` | Route number (e.g., "1", "39", "66") |

## Features to engineer
- `bus_stops_within_100m` — count of bus stops within 100m of a grid cell center
- `bus_routes_on_street` — number of distinct bus routes using a street
- `is_on_bus_route` — binary flag for high-frequency bus corridor

## Save to
`data/raw/mbta_gtfs/` (extracted ZIP contents)

## Note
GTFS is a static schedule — it doesn't change with seasons. Download once and keep.
