# 06 — Boston Neighborhood Boundaries

## What it is
Official polygon boundaries for Boston's 26 neighborhoods. Used for spatial joins — assigning any lat/lon point to its neighborhood.

## Why we need it
Our model predicts at the neighborhood level. We need these polygons to:
- Assign 311 reports to neighborhoods
- Draw the risk heat map
- Aggregate features by neighborhood

## Source
- Portal: https://data.boston.gov/dataset/bpda-neighborhood-boundaries
- Organization: Boston Planning Department (BPDA)
- License: Open Data Commons Public Domain

## Resource IDs (CKAN)

| Format | Resource ID |
|--------|-------------|
| GeoJSON | `e5849875-a6f6-4c9c-9d8a-5048b0fbd03e` |
| CSV | `d45a6d03-2616-4449-9687-0c864ec9f9e4` |
| Shapefile | `f6be6d34-7813-4b55-955d-4b2c236243d6` |

## How to fetch (GeoJSON recommended for mapping)

```python
import urllib.request, json

# GeoJSON — use for folium/geopandas mapping
resource_id = "e5849875-a6f6-4c9c-9d8a-5048b0fbd03e"
# Direct download URL pattern:
url = f"https://data.boston.gov/dataset/bpda-neighborhood-boundaries/resource/{resource_id}/download"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
geojson = json.loads(r.read())
```

## Boston's 26 neighborhoods
Allston, Back Bay, Bay Village, Beacon Hill, Brighton, Charlestown, Chinatown,
Dorchester, Downtown, East Boston, Fenway, Hyde Park, Jamaica Plain,
Leather District, Longwood, Mattapan, Mission Hill, North End, Roslindale,
Roxbury, South Boston, South End, West End, West Roxbury, Wharf District, Chinatown

## Key columns
| Column | Description |
|--------|-------------|
| `Name` | Neighborhood name (matches 311 `neighborhood` field) |
| `geometry` | Polygon boundary |
| `Shape_Area` | Area in sq meters |

## Save to
`data/raw/boston_neighborhoods.geojson`
