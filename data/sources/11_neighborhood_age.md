# 11 — Neighborhood Age (Building Year Built via Property Assessment)

## What it is
Boston's Property Assessment dataset includes a `YR_BUILT` field for every parcel — the year the building was constructed. Aggregated by neighborhood, this gives us the median construction era per area, a proxy for infrastructure age.

## Why we need it
Older neighborhoods have older underground pipes, older road subbase, and older sidewalk slabs — all more prone to failure. A neighborhood built in the 1920s behaves very differently from one built in the 1990s.

## Source
- Portal: https://data.boston.gov/dataset/property-assessment
- Organization: City of Boston Assessing Department
- License: Open Data Commons Public Domain
- Updated: annually (fiscal year)

## Resource IDs (CKAN) — most recent CSV

| Year | Resource ID |
|------|-------------|
| FY2024 (most recent unnamed) | `ee73430d-96c0-423e-ad21-c4cfb54c8961` |
| FY2015 (named) | `bdb17c2b-e9ab-44e4-a070-bf804a0e1a7f` |
| FY2014 (named) | `7190b0a4-30c4-44c5-911d-c34f60b22181` |

Use the most recent unnamed CSV — it's the current year's assessment.

## How to fetch

```python
import urllib.request, json

# FY2024 property assessment
resource_id = "ee73430d-96c0-423e-ad21-c4cfb54c8961"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
data = json.loads(r.read())
```

## Key columns
| Column | Description | Used for |
|--------|-------------|----------|
| `PID` | Parcel ID | join key |
| `ST_NAME` | Street name | spatial join |
| `ZIPCODE` | ZIP code | spatial grouping |
| `YR_BUILT` | Year building was constructed | **neighborhood age feature** |
| `YR_REMOD` | Year last remodeled | renovation timeline |
| `BLDG_SEQ` | Building sequence (ignore multi-unit) | filter |
| `GROSS_AREA` | Building size | context |

## Wrangling needed
1. Filter to residential + commercial (ignore vacant land)
2. Group by neighborhood (join to neighborhood boundaries via ZIP or coordinates)
3. Compute `median_yr_built` per neighborhood
4. Compute `pct_pre_1950` — fraction of buildings built before 1950 (proxy for very old infrastructure)

## Feature to engineer
`neighborhood_median_yr_built` — older = higher failure risk baseline.

## Save to
`data/raw/boston_property_assessment.csv`
