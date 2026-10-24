# 01 — Boston 311 Service Requests

## What it is
Every non-emergency city service request filed by Boston residents (2011–2026). Includes potholes, sidewalk damage, streetlight outages, sanitation, graffiti, and ~100 other issue types.

## Why we need it
This is our **primary training data** — the ground truth of when and where civic issues occurred.

## Source
- Portal: https://data.boston.gov/dataset/311-service-requests
- Organization: Boston 311
- License: Open Data Commons Public Domain
- Updated: daily

## How to fetch (no auth needed)

### Option A — CKAN JSON API (recommended, no redirect issues)
```python
import urllib.request, json

CKAN_API = "https://data.boston.gov/api/3/action/datastore_search"

RESOURCE_IDS = {
    "2024": "dff4d804-5031-443a-8409-8344efd0e5c8",
    "2023": "e6013a93-1321-4f2a-bf91-8d8a02f1e62f",
    "2022": "81a7b022-f8fc-4da5-80e4-b160058ca207",
    "2021": "f53ebccd-bc61-49f9-83db-625f209c95f5",
    "2020": "6ff6a6fd-3141-4440-a880-6f60a37fe789",
    "2019": "ea2e4696-4a2d-429c-9807-d02eb92e0222",
    "2018": "2be28d90-3a90-4af1-a3f6-f28c1e25880a",
}

def fetch_page(resource_id, limit=1000, offset=0):
    url = f"{CKAN_API}?resource_id={resource_id}&limit={limit}&offset={offset}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=60)
    return json.loads(r.read())["result"]
```

Paginate by incrementing `offset` by `limit` until `offset >= total`.

### Option B — Direct CSV download (2018–2024)
```
https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/<RESOURCE_ID>/download/lagan_311_open_data_YYYY_rvsd3.csv
```
Note: some years return 403; use Option A as fallback.

## Schema

| Column | Type | Description | Used for |
|--------|------|-------------|----------|
| `case_enquiry_id` | text | Unique case ID | dedup |
| `open_dt` | datetime | Date/time report filed | **time axis** |
| `closed_dt` | datetime | Date/time case closed | response time |
| `on_time` | text | ONTIME / OVERDUE | SLA feature |
| `case_status` | text | Open / Closed | filter |
| `case_title` | text | Short issue label | **primary label** |
| `subject` | text | Department category | grouping |
| `reason` | text | Sub-reason | feature |
| `type` | text | Detailed type | feature |
| `department` | text | Assigned city dept | feature |
| `neighborhood` | text | Boston neighborhood | **spatial grouping** |
| `pwd_district` | text | Public Works district | spatial feature |
| `ward` | text | City ward | spatial feature |
| `latitude` | float | WGS84 lat | **grid mapping** |
| `longitude` | float | WGS84 lon | **grid mapping** |
| `source` | text | Citizens Connect / Phone / Web | channel feature |

## Issue types relevant to our model

| Issue | `case_title` / `reason` | 2024 count |
|-------|------------------------|------------|
| Pothole | `Pothole`, `BWSC Pothole`, `Highway Pothole` | 10,859 |
| Sidewalk | `Sidewalk Repair`, `Request for Pothole Repair` | 14,610 |
| Street Light | `Street Light Outages` | 5,964 |

## Scale
- 2024: **306,756 rows**
- 2018–2024 total: ~2 million rows

## Data quality notes
- lat/lon present on most rows
- `open_dt` always filled — reliable time axis
- `closed_dt` sometimes null — only use for resolved cases
- 2025–2026 uses new backend system with different schema; treat as validation only

## Save to
`data/raw/311_YYYY.csv` (one file per year)
