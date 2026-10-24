# 07 — Building & Property Violations

## What it is
Violations issued by Boston's Inspectional Services Department for unsafe or non-compliant buildings and properties. Includes structural, sanitary, and safety violations.

## Why we need it
Property violations cluster in areas with deferred maintenance — the same neighborhoods often see more infrastructure neglect (broken sidewalks, poor drainage). It's a proxy for neighborhood disinvestment.

## Source
- Portal: https://data.boston.gov/dataset/building-and-property-violations1
- Organization: Inspectional Services Department
- License: Open Data Commons Public Domain
- Updated: daily

## Resource ID (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `800a2663-1d6a-46e7-9356-bedb70f5332c` |

## How to fetch

```python
import urllib.request, json

resource_id = "800a2663-1d6a-46e7-9356-bedb70f5332c"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `status_dttm` | Date violation was filed | time join |
| `code` | Violation code | filter |
| `description` | Violation description | filter |
| `address` | Property address | spatial join |
| `neighborhood` | Neighborhood | grouping |
| `latitude` / `longitude` | Coordinates | grid mapping |

## Feature to engineer
`violations_per_neighborhood_year` — annual count of violations per neighborhood as a neighborhood health index.

## Save to
`data/raw/boston_property_violations.csv`
