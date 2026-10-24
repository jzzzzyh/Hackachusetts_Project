# Boston 311 Data Profile
*Generated from live API: data.boston.gov — October 2026*

---

## Source

- **Portal:** [Analyze Boston (CKAN)](https://data.boston.gov/dataset/311-service-requests)
- **API base:** `https://data.boston.gov/api/3/action/`
- **Format:** CSV per year (2011–2026) + live JSON API (no auth needed)
- **License:** Open Data Commons Public Domain

---

## Scale

| Year | Rows (approx) |
|------|--------------|
| 2024 | **306,756** |
| 2023 | ~300,000 |
| 2022 | ~290,000 |
| 2018–2021 | ~250,000–280,000/yr |
| Total (2018–2024) | **~2 million rows** |

---

## Schema (2018–2024 legacy format)

| Column | Type | Description | Our use |
|--------|------|-------------|---------|
| `case_enquiry_id` | text | Unique case ID | dedup |
| `open_dt` | datetime | When report was filed | **TARGET DATE** |
| `closed_dt` | datetime | When case was closed | response time feature |
| `on_time` | text | ONTIME / OVERDUE | SLA feature |
| `case_status` | text | Open / Closed | filter to closed for ground truth |
| `case_title` | text | Short type label | **PRIMARY LABEL** |
| `subject` | text | Department category | grouping |
| `reason` | text | Sub-reason | feature |
| `type` | text | Detailed type | feature |
| `department` | text | City dept assigned | feature |
| `location` | text | Human-readable address | fallback |
| `neighborhood` | text | Boston neighborhood name | **SPATIAL GROUPING** |
| `pwd_district` | text | Public Works district | spatial feature |
| `ward` | text | City ward number | spatial feature |
| `latitude` | float | Lat (WGS84) | **GRID MAPPING** |
| `longitude` | float | Lon (WGS84) | **GRID MAPPING** |
| `source` | text | Citizens Connect / Phone / Web | feature |
| `fire_district` | text | Fire district | spatial feature |
| `police_district` | text | Police district | spatial feature |

---

## Issue Types Relevant to Our Model

### Potholes
- `case_title`: `Pothole`, `BWSC Pothole`, `Highway Pothole`
- `reason`: `Pothole`
- **2024 count: 10,859 reports**
- Seasonal: peaks March–May (post-freeze thaw)

### Sidewalk Damage
- `case_title`: `Request for Pothole Repair`, `Sidewalk Repair`
- `reason`: `Sidewalk`, `Administrative & General Requests`
- **2024 count: 14,610 reports** (includes general PWD requests)
- Seasonal: peaks spring and fall

### Street Light Outages
- `case_title`: `Street Light Outages`
- `reason`: `Street Lights`
- `subject`: `Public Works Department`
- **2024 count: 5,964 reports**
- Less seasonal, more random failures

---

## Data Quality Notes

1. **Lat/lon present on most rows** — good for grid cell mapping
2. **Neighborhood field is clean** — 26 distinct Boston neighborhoods
3. **`open_dt` is always filled** — reliable date for time series
4. **`closed_dt` sometimes null** — only use for resolved cases
5. **2025–2026 is transitioning** to a new backend system — schema may differ; use 2018–2024 as training data, treat 2025+ as validation
6. **No weather data included** — must join externally (NOAA/Open-Meteo)

---

## Resource IDs (for API queries)

```python
RESOURCE_IDS = {
    "2024": "dff4d804-5031-443a-8409-8344efd0e5c8",
    "2023": "e6013a93-1321-4f2a-bf91-8d8a02f1e62f",
    "2022": "81a7b022-f8fc-4da5-80e4-b160058ca207",
    "2021": "f53ebccd-bc61-49f9-83db-625f209c95f5",
    "2020": "6ff6a6fd-3141-4440-a880-6f60a37fe789",
    "2019": "ea2e4696-4a2d-429c-9807-d02eb92e0222",
    "2018": "2be28d90-3a90-4af1-a3f6-f28c1e25880a",
}

# CSV download URLs (blocked by 403 for some years — use API instead)
CKAN_API = "https://data.boston.gov/api/3/action/datastore_search"
```

---

## Recommended Fetch Strategy

Use the CKAN `datastore_search` API (JSON, no auth, no redirect issues):

```python
import urllib.request, json

def fetch_311(resource_id, limit=1000, offset=0):
    url = (
        "https://data.boston.gov/api/3/action/datastore_search"
        f"?resource_id={resource_id}&limit={limit}&offset={offset}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=60)
    return json.loads(r.read())["result"]
```

Paginate with `offset` in steps of 1000 until `offset >= total`.

---

## Weather Data (external join)

- **Source:** [Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api) — free, no key
- **Location:** Boston lat/lon = `42.3601, -71.0589`
- **Variables needed:**
  - `temperature_2m_min` / `temperature_2m_max` — freeze/thaw detection
  - `precipitation_sum` — rain/snow
  - `snowfall_sum` — snow accumulation
  - `windspeed_10m_max` — storm events
- **Date range:** 2018-01-01 to 2024-12-31

```
https://archive-api.open-meteo.com/v1/archive
  ?latitude=42.3601&longitude=-71.0589
  &start_date=2018-01-01&end_date=2024-12-31
  &daily=temperature_2m_min,temperature_2m_max,precipitation_sum,snowfall_sum
  &timezone=America/New_York
```

---

## Feature Engineering Plan

From the joined 311 + weather data:

| Feature | Derived from |
|---------|-------------|
| `freeze_thaw_days_last7` | Count days where min < 0°C and max > 2°C in past 7 days |
| `snowfall_last30` | Sum of daily snowfall over past 30 days |
| `days_since_last_report` | Days since last pothole report in same neighborhood |
| `report_count_last30` | Count of same-type reports in neighborhood last 30 days |
| `month` | Extracted from `open_dt` |
| `is_winter` | Boolean: Dec–Mar |
| `neighborhood` | Direct from 311 (one-hot encode) |
| `pwd_district` | Direct from 311 |

---

## Next Step: fetch_data.py

A script to:
1. Pull all 311 data (2018–2024) via CKAN API and save to `data/raw/311_YYYY.csv`
2. Pull weather data from Open-Meteo and save to `data/raw/weather_boston_2018_2024.csv`
