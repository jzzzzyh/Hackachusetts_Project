# 09 — Public Works Violations

## What it is
Citations issued by Boston's Public Works Department Code Enforcement Division. Covers illegal dumping, blocked sidewalks, unpermitted street cuts, snow removal failures, and other public space violations.

## Why we need it
Public Works violations — especially unpermitted street cuts and blocked sidewalks — directly relate to infrastructure damage. A neighborhood with many street-cut violations likely has deteriorating pavement from repeated digging.

## Source
- Portal: https://data.boston.gov/dataset/public-works-violations
- Organization: Public Works Department
- License: Open Data Commons Public Domain
- Updated: daily

## Resource ID (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `90ed3816-5e70-443c-803d-9a71f44470be` |

## How to fetch

```python
import urllib.request, json

resource_id = "90ed3816-5e70-443c-803d-9a71f44470be"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `status_dttm` | Date violation issued | time join |
| `code` / `description` | Violation type | filter for street-cut, sidewalk violations |
| `address` | Location | spatial join |
| `neighborhood` | Neighborhood | grouping |
| `latitude` / `longitude` | Coordinates | grid mapping |

## Filter for relevant violations
Look for: "Street Cut", "Sidewalk", "Excavation", "Unpermitted" in description.

## Feature to engineer
`pw_violations_per_neighborhood_30d` — rolling 30-day count of public works violations per neighborhood.

## Save to
`data/raw/boston_pw_violations.csv`
