# 08 — After-Hours Construction

## What it is
Permits issued for construction activity outside normal working hours (nights/weekends). Indicates intensive construction projects that run around the clock.

## Why we need it
After-hours construction signals large-scale projects (major renovations, utility infrastructure) that cause the most road damage. It's a more targeted signal than general building permits.

## Source
- Portal: https://data.boston.gov/dataset/after-hours-construction
- Organization: Inspectional Services Department
- License: Open Data Commons Public Domain
- Updated: daily

## Resource ID (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `c66524ea-36f5-43b1-aa9c-da36d7cb8744` |

## How to fetch

```python
import urllib.request, json

resource_id = "c66524ea-36f5-43b1-aa9c-da36d7cb8744"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `startdate` / `stopdate` | Construction window | time join |
| `address` | Location | spatial join |
| `neighborhood` | Neighborhood | grouping |
| `applicant` | Contractor name | (ignore) |

## Feature to engineer
`afterhours_construction_active` — binary flag: is there active after-hours construction within 200m this week?

## Save to
`data/raw/boston_afterhours_construction.csv`
