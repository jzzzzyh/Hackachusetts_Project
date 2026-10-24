# 02 — Boston Historical Weather

## What it is
Daily weather measurements for Boston going back to 1940. Includes temperature min/max, precipitation, snowfall, and wind.

## Why we need it
Freeze/thaw cycles are the #1 driver of pothole formation. A day where min temp < 0°C and max > 2°C cracks pavement. We need this to engineer our most important features.

## Source
- API: https://open-meteo.com/en/docs/historical-weather-api
- Provider: Open-Meteo (open source, no API key, no rate limit for reasonable use)
- License: CC BY 4.0

## How to fetch

```python
import urllib.request, json

url = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=42.3601"
    "&longitude=-71.0589"
    "&start_date=2018-01-01"
    "&end_date=2024-12-31"
    "&daily=temperature_2m_min,temperature_2m_max,precipitation_sum,"
           "snowfall_sum,windspeed_10m_max,rain_sum"
    "&timezone=America%2FNew_York"
)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
data = json.loads(r.read())
# data["daily"] contains lists keyed by variable name + "time"
```

## Schema (daily, one row per day)

| Column | Unit | Description | Used for |
|--------|------|-------------|----------|
| `time` | date | YYYY-MM-DD | join key |
| `temperature_2m_min` | °C | Daily minimum temp | freeze detection |
| `temperature_2m_max` | °C | Daily maximum temp | thaw detection |
| `precipitation_sum` | mm | Total rain + snow | wet roads |
| `snowfall_sum` | cm | Snow accumulation | plow stress |
| `rain_sum` | mm | Rain only | drainage stress |
| `windspeed_10m_max` | km/h | Peak wind speed | storm events |

## Engineered features (derived from this)

| Feature | Formula |
|---------|---------|
| `is_freeze_thaw` | `min < 0°C AND max > 2°C` |
| `freeze_thaw_days_7d` | Rolling 7-day count of freeze/thaw days |
| `freeze_thaw_days_30d` | Rolling 30-day count |
| `snowfall_30d` | Rolling 30-day snowfall sum |
| `days_since_last_freeze` | Days since last freeze/thaw event |
| `is_winter` | Month in [12, 1, 2, 3] |

## Boston coordinates
- Latitude: `42.3601`
- Longitude: `-71.0589`
- Timezone: `America/New_York`

## Scale
- 2018–2024: **2,557 daily rows** — tiny file (~200KB)

## Save to
`data/raw/weather_boston_2018_2024.csv`
