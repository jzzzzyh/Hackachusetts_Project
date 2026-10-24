# 12 — Water & Sewer Main Age (BWSC)

## What it is
The Boston Water and Sewer Commission (BWSC) maintains GIS data on the city's water mains, sewer mains, and combined sewer infrastructure — including pipe age, material, and diameter. Old pipes crack and burst, causing the road above to collapse.

## Why we need it
"BWSC Pothole" is one of the top 311 issue types (explicitly tagged in the 311 dataset). These potholes are caused by water/sewer main failures, not weather. Pipe age is the key predictor for this category.

## Source
- Portal: https://www.bwsc.org/about/maps-gis-data
- Provider: Boston Water and Sewer Commission
- License: Public (open data via MassGIS)
- MassGIS mirror: https://gis.data.mass.gov (search "Boston Water Sewer")

## How to fetch

BWSC GIS data is available through MassGIS ArcGIS REST APIs:

```python
import urllib.request, json

# ArcGIS FeatureServer for BWSC Water Mains (public)
# Query all features in Boston with age info
base_url = "https://gis.data.mass.gov/datasets/boston-water-and-sewer-commission-water-mains"
# Or use direct ArcGIS REST:
arcgis_url = (
    "https://services1.arcgis.com/rMSgGcHVW9Ppy3BI/arcgis/rest/services/"
    "BWSC_Water_Mains/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&f=geojson"
)
```

Alternatively, download the shapefile from:
https://www.bwsc.org/about/maps-gis-data → "Water Distribution System" or "Sewer System"

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `INSTALLYR` | Year pipe was installed | **age feature** |
| `MATERIAL` | Pipe material (cast iron, PVC, etc.) | failure risk |
| `DIAMETER` | Pipe diameter (inches) | feature |
| `STATUS` | Active / Abandoned | filter |
| geometry | Pipe segment geometry | spatial join |

## Wrangling needed
1. Download shapefile or GeoJSON of water + sewer mains
2. Compute `pipe_age` = current year - `INSTALLYR`
3. Spatial join to neighborhood boundaries
4. Compute `avg_pipe_age_per_neighborhood`
5. Flag neighborhoods with high proportion of pre-1960 cast iron pipes (highest failure risk)

## Feature to engineer
- `avg_water_main_age` — mean pipe age per neighborhood
- `pct_cast_iron_pipes` — most brittle, most failure-prone material
- `pipe_breaks_30d` — if BWSC provides break history (not always public)

## Note on access
BWSC data accessibility varies. Start with the MassGIS ArcGIS Hub search:
https://gis.data.mass.gov — search "BWSC" or "Boston water sewer"
Fallback: use the 311 "BWSC Pothole" report density as a proxy.

## Save to
`data/raw/bwsc_water_mains.geojson` / `data/raw/bwsc_sewer_mains.geojson`
