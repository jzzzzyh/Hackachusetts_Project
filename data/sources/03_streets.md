# 03 — Boston Managed Streets

## What it is
All public (and many private) roadways in Boston with geometry, road classification, ownership, and surface type. Formerly called "Road Inventory."

## Why we need it
- Join 311 reports to specific road segments
- Road type (arterial vs residential) is a traffic-load proxy
- Surface type correlates with failure rate

## Source
- Portal: https://data.boston.gov/dataset/city-of-boston-managed-streets
- Organization: Boston Maps
- License: Open Data Commons Public Domain
- Updated: December 2024 (static)

## Resource IDs (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `4fc84110-6cf8-476d-a566-a9db5f8b3225` |
| GeoJSON | `91608357-8efa-4bab-afc0-49647108348e` |

## How to fetch

```python
import urllib.request, json

# CSV via CKAN datastore
resource_id = "4fc84110-6cf8-476d-a566-a9db5f8b3225"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=5"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
# data["result"]["total"] shows total row count
# data["result"]["records"] contains rows
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| geometry / lat/lon | Road segment coordinates | spatial join to 311 reports |
| `STREET_NAM` | Street name | join key |
| `OWNER` | City / State / Private | filter to city-owned |
| `SURF_TYPE` | Surface material (asphalt, concrete, etc.) | failure risk feature |
| `FUNC_CLASS` | Functional classification (arterial, collector, local) | traffic proxy |
| `WARD` | Ward number | spatial grouping |
| `NEIGHBORHO` | Neighborhood | spatial grouping |

## Save to
`data/raw/boston_streets.csv` (CSV) or `data/raw/boston_streets.geojson` (GeoJSON for mapping)
