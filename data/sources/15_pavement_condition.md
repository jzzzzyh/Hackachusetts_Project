# 15 — Pavement Condition Index (MassDOT Road Inventory 2024)

## What it is
MassDOT's Road Inventory includes a Pavement Serviceability Index (PSI) for road segments across Massachusetts. PSI runs from 0 (impassable) to 5 (perfect). It's a composite score based on cracking, ride quality, and surface distress — measured by vehicle-mounted sensors.

## Why we need it
This is the most direct measure of road quality we can get. A low PSI road is already damaged and almost certain to generate 311 reports soon. Including PSI as a feature makes our model dramatically more accurate.

## Source
- Dataset: MassDOT Road Inventory 2024
- GIS Hub: https://gis.data.mass.gov/maps/MassDOT::road-inventory-2024
- MassDOT Open Data Portal: https://geodot.mass.gov/pages/open-data-portal/
- Provider: MassDOT
- License: Public (Massachusetts open data)
- Updated: annually

**Note:** PSI data is in the same Road Inventory file as traffic counts (source 13). You only need to download it once.

## How to fetch

### Via ArcGIS REST (Suffolk County / Boston only)
```python
import urllib.request, json

# Get the ArcGIS REST endpoint URL from:
# https://gis.data.mass.gov/maps/MassDOT::road-inventory-2024
# Click "I want to use this" → ArcGIS REST API

# Example query structure (replace ... with actual service URL):
arcgis_query = (
    "https://maps.massdot.state.ma.us/arcgis/rest/services/"
    "Road_Inventory/MapServer/0/query"
    "?where=COUNTY_NAME='SUFFOLK'"
    "&outFields=ROADWAY_NAME,PSI,AADT,FUNC_CLASS,SURF_TYPE"
    "&f=geojson"
)
req = urllib.request.Request(arcgis_query, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
data = json.loads(r.read())
```

### Via direct download (whole state, then filter)
1. Go to: https://geodot.mass.gov/pages/open-data-portal/
2. Search "Road Inventory 2024"
3. Download GeoJSON or SHP
4. Filter: `gdf[gdf['COUNTY_NAME'] == 'SUFFOLK']`

## Key columns
| Column | Description | Used for |
|--------|-------------|----------|
| `PSI` | Pavement Serviceability Index (0–5) | **condition score** |
| `ROADWAY_NAME` | Street name | join key |
| `COUNTY_NAME` | County | filter to SUFFOLK |
| `AADT` | Traffic count | traffic feature (see source 13) |
| `FUNC_CLASS` | Road type (local, arterial, highway) | stratification |
| `SURF_TYPE` | Surface material | feature |
| geometry | Road centerline | spatial join to 311 reports |

## PSI scale
| PSI | Condition |
|-----|-----------|
| 4.0–5.0 | Good |
| 3.0–3.9 | Fair |
| 2.0–2.9 | Poor |
| 0–1.9 | Very Poor / Impassable |

## Features to engineer
- `road_psi` — direct condition score per road segment
- `is_poor_condition` — boolean: PSI < 2.5
- `avg_psi_per_neighborhood` — neighborhood-level condition index
- `pct_poor_roads` — fraction of road-km in poor condition per neighborhood

## Save to
`data/raw/massdot_road_inventory_suffolk.geojson` (same file as source 13 — one download covers both)
