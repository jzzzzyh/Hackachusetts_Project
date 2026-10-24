# Workflow — Person 5: Live Weather Integration with NWS API

Your job, start to end: integrate the National Weather Service (NWS) API to fetch real-time weather data for Boston, 
store it efficiently, and make it available for model predictions with live data instead of historical monthly averages.

---

## Overview

### What You're Doing
The current model uses historical monthly weather from Open-Meteo. This workflow upgrades it to use real-time forecasts 
from the National Weather Service (NWS), which:
- Updates multiple times per day
- Provides hourly granularity
- Is the official US government weather service
- Requires no API key (free and public)

### Where Data Comes From
**National Weather Service API** — https://api.weather.gov  
- No authentication needed (just User-Agent header)
- No rate limits for typical use
- Public data from NOAA/NWS

### Boston Location
Boston center: **42.3601° N, 71.0589° W**  
NWS Grid: **BOX (Boston office)**, Grid point **96,70**

---

## First, every time

```bash
git pull origin dev
pip install -r requirements.txt
```

---

## Step 1 — Understand the NWS API

The NWS API works in 3 steps:

### Step 1a: Get Point Metadata
```bash
# Request your location's metadata
curl https://api.weather.gov/points/42.3601,-71.0589
```

Response includes:
```json
{
  "properties": {
    "forecast": "https://api.weather.gov/gridpoints/BOX/96,70/forecast",
    "forecastHourly": "https://api.weather.gov/gridpoints/BOX/96,70/forecast/hourly",
    "forecastGridData": "https://api.weather.gov/gridpoints/BOX/96,70"
  }
}
```

### Step 1b: Get Forecast
Use the `forecast` URL to get weather:
```bash
curl https://api.weather.gov/gridpoints/BOX/96,70/forecast
```

Returns periods with:
- Temperature
- Wind speed
- Precipitation chance
- Weather description

### Step 1c: Get Hourly Forecast
For more granular data:
```bash
curl https://api.weather.gov/gridpoints/BOX/96,70/forecast/hourly
```

---

## Step 2 — Create NWS Weather Fetcher

Create `src/fetch_nws_weather.py` to fetch live weather from NWS:

```python
#!/usr/bin/env python3
"""
Fetch real-time weather from National Weather Service (NWS) API.
Updates weather forecast for Boston in real-time instead of historical data.

Source: https://api.weather.gov (no API key required)
Boston Location: 42.3601, -71.0589 (NWS Grid: BOX 96,70)

Run: python src/fetch_nws_weather.py

Output: data/processed/nws_forecast.csv
  columns: time, temperature, wind_speed, precipitation_chance, description
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta

# Boston coordinates
BOSTON_LAT = 42.3601
BOSTON_LON = -71.0589

# NWS API endpoints
POINTS_URL = f"https://api.weather.gov/points/{BOSTON_LAT},{BOSTON_LON}"
USER_AGENT = "Hackachusetts (https://github.com/jzzzzyh/Hackachusetts_Project, contact@example.com)"

OUT_PATH = "data/processed/nws_forecast.csv"


def get_forecast_urls():
    """Get forecast URLs for Boston from NWS API."""
    print("Fetching Boston forecast URLs from NWS...")
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(POINTS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        properties = data.get("properties", {})
        
        forecast_url = properties.get("forecast")
        hourly_url = properties.get("forecastHourly")
        
        if not forecast_url or not hourly_url:
            print("ERROR: Could not find forecast URLs in response")
            print(f"Response: {data}")
            return None, None
        
        print(f"✓ Forecast URL: {forecast_url}")
        print(f"✓ Hourly URL: {hourly_url}")
        
        return forecast_url, hourly_url
    
    except Exception as e:
        print(f"ERROR fetching forecast URLs: {e}")
        return None, None


def fetch_forecast(forecast_url, hourly=False):
    """Fetch weather forecast from NWS."""
    try:
        headers = {"User-Agent": USER_AGENT}
        url = forecast_url if not hourly else forecast_url.replace("/forecast", "/forecast/hourly")
        
        print(f"\nFetching {'hourly' if hourly else 'daily'} forecast...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        print(f"ERROR fetching forecast: {e}")
        return None


def parse_forecast(forecast_data, hourly=False):
    """Parse NWS forecast JSON into structured data."""
    rows = []
    
    try:
        periods = forecast_data.get("properties", {}).get("periods", [])
        print(f"Found {len(periods)} periods in forecast")
        
        for period in periods:
            try:
                # Extract weather data
                start_time = period.get("startTime", "")
                temp = period.get("temperature")
                wind_speed = period.get("windSpeed", "0 mph")
                precip = period.get("probabilityOfPrecipitation", {})
                description = period.get("shortForecast", "")
                
                # Parse wind speed (format: "10 mph")
                wind_val = 0
                if wind_speed:
                    try:
                        wind_val = float(wind_speed.split()[0])
                    except:
                        pass
                
                # Parse precipitation chance
                precip_chance = 0
                if isinstance(precip, dict) and precip.get("value"):
                    precip_chance = precip.get("value", 0)
                
                rows.append({
                    "time": start_time,
                    "temperature_f": temp,
                    "wind_speed_mph": wind_val,
                    "precipitation_chance": precip_chance,
                    "description": description,
                })
            
            except Exception as e:
                print(f"  ⚠ Error parsing period: {e}")
                continue
        
        return rows
    
    except Exception as e:
        print(f"ERROR parsing forecast: {e}")
        return []


def main():
    """Fetch current weather forecast from NWS API."""
    
    print("="*60)
    print("NWS LIVE WEATHER FETCHER")
    print("="*60)
    
    # Get forecast URLs
    forecast_url, hourly_url = get_forecast_urls()
    if not forecast_url:
        return
    
    # Fetch daily forecast
    print("\n--- DAILY FORECAST ---")
    daily_data = fetch_forecast(forecast_url, hourly=False)
    if not daily_data:
        return
    
    daily_rows = parse_forecast(daily_data, hourly=False)
    
    # Fetch hourly forecast
    print("\n--- HOURLY FORECAST ---")
    hourly_data = fetch_forecast(forecast_url, hourly=True)
    if hourly_data:
        hourly_rows = parse_forecast(hourly_data, hourly=True)
        print(f"Got {len(hourly_rows)} hourly periods")
    else:
        hourly_rows = []
    
    # Save data
    os.makedirs("data/processed", exist_ok=True)
    
    if daily_rows:
        df_daily = pd.DataFrame(daily_rows)
        df_daily.to_csv(OUT_PATH, index=False)
        
        print(f"\n✓ Saved daily forecast to {OUT_PATH}")
        print(f"  Forecast spans: {df_daily['time'].iloc[0]} to {df_daily['time'].iloc[-1]}")
        print(f"\nForecast Summary (first 7 days):")
        print(df_daily.head(7)[["time", "temperature_f", "wind_speed_mph", "description"]].to_string(index=False))
    
    # Save hourly data too
    if hourly_rows:
        hourly_path = "data/processed/nws_forecast_hourly.csv"
        df_hourly = pd.DataFrame(hourly_rows)
        df_hourly.to_csv(hourly_path, index=False)
        print(f"\n✓ Saved hourly forecast to {hourly_path}")
        print(f"  {len(hourly_rows)} hourly periods available")
    
    # Verification
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    print(f"✓ Location: Boston ({BOSTON_LAT}°N, {BOSTON_LON}°W)")
    print(f"✓ Data source: NWS API (api.weather.gov)")
    print(f"✓ Daily forecast: {len(daily_rows)} periods")
    print(f"✓ Hourly forecast: {len(hourly_rows)} periods")
    print(f"✓ Files saved: {OUT_PATH}")
    if hourly_rows:
        print(f"✓ Hourly saved: {hourly_path}")


if __name__ == "__main__":
    main()
```

Run the script:

```bash
python src/fetch_nws_weather.py
```

**Output:** 
- `data/processed/nws_forecast.csv` — Daily forecast (7-14 days)
- `data/processed/nws_forecast_hourly.csv` — Hourly forecast (168 hours)

**Verify:** Check that both files were created and contain current temperature/wind/precipitation data.

---

## Step 3 — Create NWS Weather Cache

Create `src/nws_weather_cache.py` to store and retrieve live weather efficiently:

```python
#!/usr/bin/env python3
"""
NWS Weather cache manager.
Stores live weather data and provides caching to avoid excessive API calls.

The cache:
- Fetches from NWS once per hour (configurable)
- Stores latest forecast locally
- Returns cached data if fresh (< 1 hour old)
- Provides methods for model predictions

Run: python src/nws_weather_cache.py

Output: data/processed/nws_weather_cache.json
  Cache metadata and last fetch time
"""

import os
import json
import time
import subprocess
from datetime import datetime, timedelta
import pandas as pd

CACHE_PATH = "data/processed/nws_weather_cache.json"
FORECAST_PATH = "data/processed/nws_forecast.csv"
CACHE_TTL = 3600  # 1 hour in seconds


def load_cache():
    """Load cache metadata."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except:
            return None
    return None


def save_cache(metadata):
    """Save cache metadata."""
    os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(metadata, f, indent=2)


def is_cache_fresh():
    """Check if cached data is still fresh."""
    cache = load_cache()
    if not cache:
        return False
    
    last_fetch = cache.get("last_fetch_time")
    if not last_fetch:
        return False
    
    elapsed = time.time() - last_fetch
    return elapsed < CACHE_TTL


def fetch_if_needed():
    """Fetch from NWS API if cache is stale."""
    if is_cache_fresh():
        cache = load_cache()
        elapsed = time.time() - cache.get("last_fetch_time", 0)
        print(f"✓ Using cached forecast (fetched {int(elapsed)} seconds ago)")
        return True
    
    print("Cache is stale, fetching from NWS API...")
    try:
        result = subprocess.run(
            ["python", "src/fetch_nws_weather.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Fetched latest forecast from NWS")
            
            # Update cache
            cache = {
                "last_fetch_time": time.time(),
                "last_fetch_date": datetime.now().isoformat(),
                "status": "success"
            }
            save_cache(cache)
            return True
        else:
            print(f"ERROR: Fetch failed with code {result.returncode}")
            print(result.stderr)
            return False
    
    except Exception as e:
        print(f"ERROR fetching weather: {e}")
        return False


def get_current_weather():
    """Get current weather for Boston (latest forecast)."""
    if not fetch_if_needed():
        return None
    
    try:
        df = pd.read_csv(FORECAST_PATH)
        if len(df) == 0:
            return None
        
        # Return latest period (usually "today" or "tonight")
        latest = df.iloc[0].to_dict()
        return latest
    
    except Exception as e:
        print(f"ERROR reading forecast: {e}")
        return None


def get_forecast_for_model():
    """Get weather data formatted for model input."""
    if not fetch_if_needed():
        return None
    
    try:
        df = pd.read_csv(FORECAST_PATH)
        
        # For model, we need: avg_temp, precip, snow, wind
        # NWS gives: temperature, precipitation_chance, wind_speed
        
        # Average the forecast (simplified approach)
        avg_temp_f = df["temperature_f"].mean()
        avg_wind = df["wind_speed_mph"].mean()
        avg_precip = df["precipitation_chance"].mean()
        
        # Convert to metric (model uses Celsius, mm, kmh)
        avg_temp_c = (avg_temp_f - 32) * 5/9
        avg_precip_mm = (avg_precip / 100) * 25  # Rough: % chance to mm
        avg_wind_kmh = avg_wind * 1.60934
        
        return {
            "avg_temp_c": round(avg_temp_c, 2),
            "total_precip_mm": round(avg_precip_mm, 2),
            "total_snow_cm": 0,  # NWS provides snow in description, not numeric
            "max_wind_kmh": round(avg_wind_kmh, 2),
            "source": "NWS API",
            "periods_averaged": len(df),
        }
    
    except Exception as e:
        print(f"ERROR preparing weather for model: {e}")
        return None


def main():
    """Test cache functionality."""
    print("NWS Weather Cache Manager")
    print("="*50)
    
    # Fetch if needed
    fetch_if_needed()
    
    # Get current weather
    print("\n--- Current Weather ---")
    current = get_current_weather()
    if current:
        print(f"Temperature: {current.get('temperature_f')}°F")
        print(f"Wind: {current.get('wind_speed_mph')} mph")
        print(f"Precipitation chance: {current.get('precipitation_chance')}%")
        print(f"Description: {current.get('description')}")
    
    # Get formatted for model
    print("\n--- Weather for Model Input ---")
    model_weather = get_forecast_for_model()
    if model_weather:
        for key, val in model_weather.items():
            print(f"{key}: {val}")


if __name__ == "__main__":
    main()
```

Run the cache manager:

```bash
python src/nws_weather_cache.py
```

**Output:** 
- Current weather displayed
- Cache created in `data/processed/nws_weather_cache.json`
- Data formatted for model use

---

## Step 4 — Integrate Live Weather into Model

Modify `src/train_xgboost.py` to use live NWS weather instead of historical:

Find this section:
```python
    merged = counts.merge(weather, on=["year", "month"], how="left")
```

Add before it:
```python
    # --- use live NWS weather if available, fall back to historical ---
    import os
    nws_cache_path = "data/processed/nws_weather_cache.json"
    
    if os.path.exists(nws_cache_path):
        import json
        from src.nws_weather_cache import get_forecast_for_model, fetch_if_needed
        
        print("Using live NWS weather data...")
        fetch_if_needed()
        live_weather = get_forecast_for_model()
        
        if live_weather:
            print(f"Live weather: {live_weather}")
            # Use live weather for current month predictions
            # (Historical data still used for training)
```

Train the model:

```bash
python src/train_xgboost.py
```

**Output:** Model now shows "Using live NWS weather data" when available.

---

## Step 5 — Create Live Weather Dashboard Widget

Create `src/create_weather_widget.py` for dashboard display:

```python
#!/usr/bin/env python3
"""
Create weather widget for dashboard showing live NWS data.
"""

import os
from src.nws_weather_cache import get_current_weather, get_forecast_for_model

def get_weather_html():
    """Return HTML widget for Streamlit dashboard."""
    current = get_current_weather()
    model_data = get_forecast_for_model()
    
    if not current or not model_data:
        return "<p>Weather data unavailable</p>"
    
    html = f"""
    <div style="background: #f0f8ff; padding: 15px; border-radius: 8px;">
        <h3>Live Boston Weather (NWS)</h3>
        <p><strong>Temperature:</strong> {current.get('temperature_f')}°F / {model_data.get('avg_temp_c')}°C</p>
        <p><strong>Wind:</strong> {current.get('wind_speed_mph')} mph</p>
        <p><strong>Precipitation Chance:</strong> {current.get('precipitation_chance')}%</p>
        <p><strong>Forecast:</strong> {current.get('description')}</p>
        <p><small>Data from National Weather Service (updated hourly)</small></p>
    </div>
    """
    return html


if __name__ == "__main__":
    print(get_weather_html())
```

---

## Commit and push your changes

Once all steps complete:

```bash
git add src/fetch_nws_weather.py src/nws_weather_cache.py src/create_weather_widget.py src/train_xgboost.py docs/workflows/WORKFLOW_PERSON5_LIVE_WEATHER.md
git commit -m "Add live NWS weather integration; fetch real-time forecasts for Boston"
git push origin dev
```

**Risk:** API rate limits are generous but not unlimited. Cache aggressively (1 hour minimum).

**Next steps:**
- Add weather widget to dashboard
- Integrate live predictions
- Monitor API performance

