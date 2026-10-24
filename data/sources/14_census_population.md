# 14 — Census Population Density

## What it is
Population estimates for Boston's neighborhoods and census tracts, from the City of Boston Planning Department (based on US Census ACS data). Includes total population and can be used to derive density (population per sq km).

## Why we need it
Dense neighborhoods generate more 311 reports per issue — more eyes on the street = more reports filed. Controlling for population density prevents the model from over-predicting in dense areas just because of reporting rate, not actual damage rate.

## Source
- Portal: https://data.boston.gov/dataset/2025-boston-population-estimates-neighborhood-level
- Organization: Boston Planning Department
- License: Open Data Commons Public Domain
- Updated: annually

## Resource IDs (CKAN)

| Format | Resource ID | Description |
|--------|-------------|-------------|
| CSV (neighborhood) | `b0543358-d03f-4682-bf0c-658ea4573d6f` | Population by neighborhood, 2025 |
| GeoJSON (neighborhood) | `faf18a44-8ba1-4d2b-b5c1-2ec1ebe0142d` | Same + geometry |
| CSV (census tract) | `8db6494a-5df4-4061-b11e-d75048584722` | Finer granularity, 2025 |
| GeoJSON (census tract) | `a8214385-2ed1-4a26-a05b-47ee2d4a4335` | Same + geometry |
| CSV (historical tracts) | `1ff3653e-57da-41e2-83a9-db045e87326c` | 2020 census tracts |

## How to fetch

```python
import urllib.request, json

# Neighborhood-level population (simplest)
resource_id = "b0543358-d03f-4682-bf0c-658ea4573d6f"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=100"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
# Returns ~26 rows (one per neighborhood)
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `Name` / `neighborhood` | Neighborhood name | join key to 311 data |
| `Total_Population` | Estimated population | density calculation |
| `Shape_Area` | Area in sq meters | density calculation |
| geometry (GeoJSON) | Boundary polygon | mapping |

## Wrangling needed
1. Compute `pop_density` = `Total_Population` / (`Shape_Area` / 1_000_000) — people per sq km
2. Join to 311 reports by neighborhood name
3. Normalize 311 report count by population: `reports_per_1000_residents`

## Features to engineer
- `pop_density_per_sqkm` — controls for reporting rate bias
- `reports_per_1000_residents` — normalized issue rate (used as validation metric)

## Note
This is a small file — only 26 rows (one per neighborhood). No pagination needed.

## Save to
`data/raw/boston_population_by_neighborhood.csv`
