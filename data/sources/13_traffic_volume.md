# 13 — Traffic Volume Counts (MassDOT)

## What it is
Annual average daily traffic (AADT) counts for roads across Massachusetts, collected by MassDOT and municipalities. Shows how many vehicles use each road segment per day.

## Why we need it
More vehicles = faster pavement wear. A road with 20,000 vehicles/day degrades much faster than a residential street with 500/day. AADT is a standard input in pavement life models.

## Source
- Portal: https://geodot.mass.gov/pages/open-data-portal/
- Dataset: "Road Inventory 2024" (includes AADT field)
- Provider: MassDOT
- License: Public (Massachusetts open data)
- GIS Hub: https://gis.data.mass.gov/maps/MassDOT::road-inventory-2024

## How to fetch

### Option A — ArcGIS REST API (GeoJSON, filtered to Suffolk County / Boston)
```python
import urllib.request, json

# MassDOT Road Inventory ArcGIS REST — filter to Suffolk County (Boston)
url = (
    "https://gis.data.mass.gov/maps/MassDOT::road-inventory-2024/about"
)
# Direct ArcGIS FeatureServer query:
arcgis_url = (
    "https://services.arcgis.com/..."  # get exact URL from ArcGIS Hub page
    "/FeatureServer/0/query"
    "?where=COUNTY_NAME='SUFFOLK'&outFields=ROADWAY_NAME,AADT,FUNC_CLASS,SURF_TYPE&f=geojson"
)
```

### Option B — Download full shapefile from MassDOT Open Data Portal
1. Go to: https://geodot.mass.gov/pages/open-data-portal/
2. Search "Road Inventory"
3. Download GeoJSON or Shapefile
4. Filter to Suffolk County in Python/geopandas

## Key columns
| Column | Description | Used for |
|--------|-------------|----------|
| `ROADWAY_NAME` | Street name | join key |
| `AADT` | Annual average daily traffic count | **traffic load feature** |
| `FUNC_CLASS` | Functional classification (1=Interstate, 7=local) | road type |
| `SURF_TYPE` | Surface material | road quality |
| `SURF_WD` | Surface width (lane count proxy) | feature |
| `COUNTY_NAME` | County | filter: keep SUFFOLK only |
| geometry | Road centerline | spatial join |

## Wrangling needed
1. Filter to Suffolk County (Boston's county)
2. Spatial join to our neighborhood grid cells
3. Compute `avg_aadt_per_neighborhood` — mean traffic volume
4. Compute `high_traffic_road_density` — km of roads with AADT > 10,000 per neighborhood

## Feature to engineer
- `road_aadt` — traffic count per road segment (join to 311 reports by nearest road)
- `is_high_traffic` — boolean: AADT > 10,000 vehicles/day

## Pavement Condition Index (bonus — same source)
The Road Inventory also includes `PSI` (Pavement Serviceability Index, 0–5 scale):
- 5.0 = perfect, 0.0 = impassable
- Use `PSI < 2.5` as a "poor condition" flag
- This directly measures road quality, not just age

## Save to
`data/raw/massdot_road_inventory_suffolk.geojson`
