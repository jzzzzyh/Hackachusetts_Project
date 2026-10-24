# 05 — Approved Building Permits

## What it is
Every approved building permit issued in Boston. Includes new construction, renovations, demolitions, and utility work — with location, permit type, declared value, and dates.

## Why we need it
Construction activity damages roads:
- Heavy equipment tears up pavement
- Utility cuts (digging for plumbing, electrical) weaken road structure
- High-value renovation areas signal neighborhood change and infrastructure stress

## Source
- Portal: https://data.boston.gov/dataset/approved-building-permits
- Organization: Inspectional Services Department
- License: Open Data Commons Public Domain
- Updated: daily

## Resource ID (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `6ddcd912-32a0-43df-9908-63574f8c7e77` |

## How to fetch

```python
import urllib.request, json

resource_id = "6ddcd912-32a0-43df-9908-63574f8c7e77"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `issued_date` | When permit was approved | time join |
| `permittypedescr` | Permit type (new construction, renovation, etc.) | filter |
| `declared_valuation` | Estimated construction cost | scale of disruption |
| `address` | Street address | spatial join |
| `lat` / `long` | Coordinates | grid mapping |
| `neighborhood` | Neighborhood | grouping |
| `worktype` | Type of work (foundation, roofing, utilities, etc.) | filter for road-damage types |

## Filter for road-impacting permits
Focus on: `worktype` containing "Utility", "Foundation", "Demolition", "New Construction"

## Feature to engineer
`permit_activity_30d` — count of active permits within 200m of a point in the past 30 days.

## Save to
`data/raw/boston_building_permits.csv`
