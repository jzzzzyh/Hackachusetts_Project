# 04 — BPRD Street Trees

## What it is
All trees managed by the Boston Parks and Recreation Department, including street trees. Has species, diameter, condition, and location.

## Why we need it
Tree roots are a leading cause of sidewalk heaving and cracking. Areas with large/old trees alongside sidewalks have higher sidewalk damage rates.

## Source
- Portal: https://data.boston.gov/dataset/bprd-trees
- Organization: Parks and Recreation
- License: Open Data Commons Public Domain
- Updated: daily

## Resource IDs (CKAN)

| Format | Resource ID |
|--------|-------------|
| CSV | `995cd80f-2489-41bf-b16b-113dba4f2797` |
| GeoJSON | `2f575489-e721-45ec-865a-e98f10d2ee85` |

## How to fetch

```python
import urllib.request, json

resource_id = "995cd80f-2489-41bf-b16b-113dba4f2797"
url = f"https://data.boston.gov/api/3/action/datastore_search?resource_id={resource_id}&limit=1000&offset=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
```

## Key columns (expected)
| Column | Description | Used for |
|--------|-------------|----------|
| `latitude` / `longitude` | Tree location | spatial join |
| `SPECIES` | Tree species | root aggressiveness proxy |
| `DBH` | Diameter at breast height (trunk size) | root damage potential |
| `CONDITION` | Tree health (Good, Fair, Poor) | feature |
| `park` | Park name (null = street tree) | filter: keep nulls for street trees |
| `neighborhood` | Neighborhood | grouping |

## Filter for street trees
Remove rows where `park` is not null — those are park trees, not sidewalk trees.

## Feature to engineer
`tree_density_per_block` — count of street trees within 50m of a given point. High density = higher sidewalk damage risk.

## Save to
`data/raw/boston_street_trees.csv`
