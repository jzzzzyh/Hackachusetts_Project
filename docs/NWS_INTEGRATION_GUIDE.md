# National Weather Service (NWS) API Integration Guide

Complete guide to using the National Weather Service API for real-time Boston weather data.

---

## 📍 Quick Summary

**What:** Integrate NWS API for live weather forecasts  
**Where:** Boston, MA (42.3601°N, 71.0589°W)  
**Source:** https://api.weather.gov (free, no API key needed)  
**Files:** `src/fetch_nws_weather.py`, `src/nws_weather_cache.py`  
**Status:** ✅ Tested and working

---

## 🔑 Key Concepts

### The NWS API Architecture

The NWS API uses a 3-step process to get weather:

```
Your Location (lat, lon)
    ↓
/points endpoint → Get grid location
    ↓
/forecast endpoint → Get weather data
```

### Boston Location Mapping

Boston is identified by:
- **Coordinates:** 42.3601°N, 71.0589°W (center of city)
- **NWS Forecast Office:** BOX (Boston/Norton, MA)
- **Grid Point:** 96, 70

When you query `/points/42.3601,-71.0589`, the NWS API responds with:
```json
{
  "properties": {
    "forecast": "https://api.weather.gov/gridpoints/BOX/96,70/forecast",
    "forecastHourly": "https://api.weather.gov/gridpoints/BOX/96,70/forecast/hourly"
  }
}
```

### No Authentication Required

- **User-Agent header only** (identify your app)
- No API key needed
- Free and open to public use
- Rate limits are generous (not published, but ~450+ requests per 15 minutes)

---

## 🚀 Getting Started

### Step 1: Check if NWS Works

```bash
# Quick test - fetch Boston weather
python src/fetch_nws_weather.py
```

**Expected output:**
- ✓ Daily forecast: 14 periods
- ✓ Hourly forecast: 156 periods (7 days)
- ✓ CSV files created

### Step 2: Use the Cache Manager

```bash
# Fetch and cache weather
python src/nws_weather_cache.py
```

**Features:**
- Caches data for 1 hour (configurable)
- Returns cached data if fresh
- Automatic refresh if stale
- Formatted for model use

### Step 3: Get Weather for Your Model

```python
from src.nws_weather_cache import get_forecast_for_model

# Get weather formatted for model predictions
weather = get_forecast_for_model()
print(weather)
# Output: {
#   'avg_temp_c': 11.23,
#   'total_precip_mm': 0.18,
#   'total_snow_cm': 0,
#   'max_wind_kmh': 16.09,
#   'source': 'NWS API',
#   'forecast_coverage': '14 periods'
# }
```

---

## 📊 Data Returned

### Daily Forecast

**File:** `data/processed/nws_forecast.csv`

```
period,name,start_time,temperature_f,wind_speed_mph,precipitation_chance_pct,forecast
1,Today,2026-10-24T07:00:00-04:00,61,5.0,0,Sunny
2,Tonight,2026-10-24T19:00:00-04:00,43,5.0,0,Clear
3,Sunday,2026-10-25T06:00:00-04:00,67,5.0,0,Sunny
```

**Columns:**
- `period` — Forecast period number
- `name` — Human readable (Today, Tonight, Sunday, etc.)
- `start_time` — ISO 8601 timestamp with timezone
- `temperature_f` — Temperature in Fahrenheit
- `wind_speed_mph` — Wind speed in miles per hour
- `precipitation_chance_pct` — 0-100 % chance of precipitation
- `forecast` — Short description (Sunny, Clear, Rainy, etc.)

### Hourly Forecast

**File:** `data/processed/nws_forecast_hourly.csv`

Similar structure but with 156 periods (7 days × 24 hours) instead of 14 daily periods.

### Model-Ready Format

**From:** `nws_weather_cache.get_forecast_for_model()`

```python
{
    'avg_temp_c': 11.23,           # Average temperature in Celsius
    'total_precip_mm': 0.18,       # Precipitation in millimeters
    'total_snow_cm': 0.0,          # Snow in centimeters
    'max_wind_kmh': 16.09,         # Max wind in kilometers/hour
    'source': 'NWS API',
    'forecast_coverage': '14 periods',
    'last_updated': '2026-10-24T14:40:17'
}
```

---

## 🔌 API Endpoints

### Get Location Metadata
```bash
curl -H "User-Agent: MyApp" https://api.weather.gov/points/42.3601,-71.0589
```

Response includes grid point and forecast URLs.

### Get Daily Forecast
```bash
curl https://api.weather.gov/gridpoints/BOX/96,70/forecast
```

Returns 14 periods (7 days of daily + nightly forecasts).

### Get Hourly Forecast
```bash
curl https://api.weather.gov/gridpoints/BOX/96,70/forecast/hourly
```

Returns 156 periods (7 days × 24 hours).

### Get Grid Data
```bash
curl https://api.weather.gov/gridpoints/BOX/96,70
```

Raw grid data with individual elements (temperature, wind, etc. by hour).

---

## 💾 How the Cache Works

### Cache File Structure

**Location:** `data/processed/nws_weather_cache.json`

```json
{
  "last_fetch_time": 1729787417.195787,
  "last_fetch_date": "2026-10-24T14:40:17.195787",
  "status": "success",
  "ttl_seconds": 3600,
  "location": "Boston (42.3601, -71.0589)",
  "data_source": "NWS API (api.weather.gov)"
}
```

### Cache Logic

```python
if cache exists and age < 1 hour:
    return cached data
else:
    fetch from NWS API
    save cache
    return data
```

### Cache Benefits

1. **Reduce API calls** — Only fetch every 1 hour
2. **Faster responses** — Local file is instant
3. **Avoid rate limits** — NWS is generous, but cache prevents abuse
4. **Offline capability** — Can use cached data if API is down

---

## 🛠️ Customization

### Change Boston Location

To track a different city, update coordinates in `src/fetch_nws_weather.py`:

```python
# From:
BOSTON_LAT = 42.3601
BOSTON_LON = -71.0589

# To your location:
BOSTON_LAT = 40.7128  # New York
BOSTON_LON = -74.0060
```

### Change Cache TTL

```python
# In src/nws_weather_cache.py:
CACHE_TTL = 3600  # seconds (1 hour)

# Change to:
CACHE_TTL = 1800  # 30 minutes
CACHE_TTL = 7200  # 2 hours
```

### Change Units

The API returns Fahrenheit. To prefer Celsius:

```python
# In nws_weather_cache.py, modify conversion:
avg_temp_c = (avg_temp_f - 32) * 5/9  # Already Celsius

# Or keep Fahrenheit:
# avg_temp_f = df["temperature_f"].mean()
```

---

## 🧪 Testing

### Test 1: Fetch Raw Data

```bash
python src/fetch_nws_weather.py
```

✓ Creates `nws_forecast.csv` and `nws_forecast_hourly.csv`

### Test 2: Cache Manager

```bash
python src/nws_weather_cache.py
```

✓ Shows current conditions, next 24 hours, cache status

### Test 3: Get Model Weather

```python
from src.nws_weather_cache import get_forecast_for_model
weather = get_forecast_for_model()
print(weather)
```

✓ Returns dict with model-compatible weather

### Test 4: Repeated Calls (Cache)

```bash
# First call: fetches from API
python src/nws_weather_cache.py

# Second call (within 1 hour): uses cache
python src/nws_weather_cache.py
```

✓ Second call shows "Using cached forecast" message

---

## 📈 Integration with Model

### Current Setup (Historical)

```python
# Old way - uses historical monthly weather
weather_df = pd.read_csv("data/processed/weather_monthly.csv")
merged = counts.merge(weather_df, on=["year", "month"])
```

### New Setup (Live)

```python
# New way - uses live NWS forecast
from src.nws_weather_cache import get_forecast_for_model

live_weather = get_forecast_for_model()
# Use live_weather["avg_temp_c"], etc. in predictions
```

### Hybrid Approach (Recommended)

```python
# Use live weather for current predictions
# Use historical for model training

# Train: Historical data
training_features = pd.read_csv("data/processed/features.csv")
# ... train model ...

# Predict: Live data
live_weather = get_forecast_for_model()
current_month_pred = model.predict(live_weather)
```

---

## ⚠️ Limitations & Considerations

### NWS Forecast Limitations

1. **Grid Resolution** — 2.5km grid (affects precision)
2. **Update Frequency** — New forecasts issued 4-6 times daily
3. **Forecast Horizon** — Usually 7-14 days ahead
4. **Seasonal** — Less accurate during rapid weather changes

### Conversion Issues

1. **Snow** — Only available in text descriptions, not numeric
2. **Precipitation** — Given as % chance, not actual accumulation
3. **Humidity** — Not available in forecast endpoint

### API Quirks

1. **Precision Limit** — Only 4 decimal places for coordinates
2. **Timezone** — All times are ISO 8601 with timezone offsets
3. **Rate Limits** — Generous but not published; don't hammer

---

## 🔗 Useful Resources

### Official Documentation
- **NWS API Home:** https://www.weather.gov/documentation/services-web-api
- **API GitHub:** https://github.com/weather-gov/api
- **OpenAPI Spec:** https://api.weather.gov/openapi.json

### Example Requests
- **Boston Points:** https://api.weather.gov/points/42.3601,-71.0589
- **Boston Forecast:** https://api.weather.gov/gridpoints/BOX/96,70/forecast
- **Boston Hourly:** https://api.weather.gov/gridpoints/BOX/96,70/forecast/hourly

### Related Locations
- **New York:** 40.7128, -74.0060
- **Washington DC:** 38.9072, -77.0369
- **Philadelphia:** 39.9526, -75.1652

---

## 🚀 Next Steps

1. **Run the tests** → Verify NWS data works
2. **Integrate cache** → Add to production pipeline
3. **Update dashboard** → Show live weather widget
4. **Monitor API** → Track response times
5. **Consider alternatives** → NWS, OpenWeather, WeatherAPI, etc.

---

## 📞 Troubleshooting

### "Could not find forecast URLs"
- Check coordinates are in Boston area (40-43°N, 70-72°W)
- NWS API might be down (rare, but happens)
- Try with a nearby location

### "API rate limit exceeded"
- Cache TTL is too short
- Increase to 3600+ seconds (1+ hour)
- Check for automated requests without caching

### "No precipitation_chance in response"
- It's in daily forecast but not grid data
- Use `/forecast` endpoint, not `/gridpoints`

### "Temperature units wrong"
- NWS returns Fahrenheit by default
- Conversion in script: `(F - 32) * 5/9 = C`

---

**Last Updated:** 2026-10-24  
**Status:** ✅ Tested and working  
**Boston Weather:** Currently 61°F, Sunny
