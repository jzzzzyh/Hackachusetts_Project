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

Output: 
  - data/processed/nws_weather_cache.json (cache metadata)
  - data/processed/nws_forecast.csv (weather data)
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
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            return None
    return None


def save_cache(metadata):
    """Save cache metadata."""
    os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")


def is_cache_fresh():
    """Check if cached data is still fresh."""
    cache = load_cache()
    if not cache:
        return False
    
    last_fetch = cache.get("last_fetch_time")
    if not last_fetch:
        return False
    
    elapsed = time.time() - last_fetch
    is_fresh = elapsed < CACHE_TTL
    
    return is_fresh


def get_cache_age():
    """Get age of cache in seconds."""
    cache = load_cache()
    if not cache:
        return None
    
    last_fetch = cache.get("last_fetch_time")
    if not last_fetch:
        return None
    
    return time.time() - last_fetch


def fetch_if_needed(force_refresh=False):
    """Fetch from NWS API if cache is stale."""
    
    if not force_refresh and is_cache_fresh():
        age = get_cache_age()
        print(f"✓ Using cached forecast (fetched {int(age)} seconds ago)")
        return True
    
    print("Fetching fresh forecast from NWS API...")
    try:
        result = subprocess.run(
            ["/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13", "src/fetch_nws_weather.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Successfully fetched latest forecast from NWS")
            
            # Update cache
            cache = {
                "last_fetch_time": time.time(),
                "last_fetch_date": datetime.now().isoformat(),
                "status": "success",
                "ttl_seconds": 3600,
                "location": "Boston (42.3601, -71.0589)",
                "data_source": "NWS API (api.weather.gov)",
            }
            save_cache(cache)
            return True
        else:
            print(f"⚠ Fetch failed with code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False
    
    except subprocess.TimeoutExpired:
        print("⚠ Fetch timed out (NWS API may be slow)")
        return False
    except Exception as e:
        print(f"⚠ Error fetching weather: {e}")
        return False


def get_current_weather():
    """Get current weather for Boston (latest forecast)."""
    if not fetch_if_needed():
        print("Warning: Could not fetch current weather")
        return None
    
    try:
        if not os.path.exists(FORECAST_PATH):
            print("Error: Forecast file not found")
            return None
        
        df = pd.read_csv(FORECAST_PATH)
        if len(df) == 0:
            print("Error: Forecast is empty")
            return None
        
        # Return first period (today or tonight)
        latest = df.iloc[0].to_dict()
        return latest
    
    except Exception as e:
        print(f"Error reading forecast: {e}")
        return None


def get_forecast_for_model(use_cache=True):
    """Get weather data formatted for model input."""
    
    if use_cache:
        fetch_if_needed()
    else:
        fetch_if_needed(force_refresh=True)
    
    try:
        if not os.path.exists(FORECAST_PATH):
            print("Error: Forecast file not found")
            return None
        
        df = pd.read_csv(FORECAST_PATH)
        if df.empty:
            print("Error: Forecast is empty")
            return None
        
        # For model, we need: avg_temp, precip, snow, wind
        # NWS gives: temperature_f, precipitation_chance_pct, wind_speed_mph
        
        # Calculate averages and maximums
        temps_f = pd.to_numeric(df["temperature_f"], errors="coerce").dropna()
        winds_mph = pd.to_numeric(df["wind_speed_mph"], errors="coerce").dropna()
        precips = pd.to_numeric(df["precipitation_chance_pct"], errors="coerce").dropna()
        
        # Conversions
        avg_temp_f = temps_f.mean()
        avg_temp_c = (avg_temp_f - 32) * 5/9
        
        max_wind_mph = winds_mph.max()
        max_wind_kmh = max_wind_mph * 1.60934
        
        # Precipitation: NWS gives % chance, convert to rough mm
        avg_precip_pct = precips.mean()
        # Rough heuristic: if 100% chance, assume 15mm
        total_precip_mm = (avg_precip_pct / 100) * 15
        
        # Snow: Would need to parse forecast text, for now assume 0
        total_snow_cm = 0
        
        return {
            "avg_temp_c": round(avg_temp_c, 2),
            "total_precip_mm": round(total_precip_mm, 2),
            "total_snow_cm": round(total_snow_cm, 2),
            "max_wind_kmh": round(max_wind_kmh, 2),
            "source": "NWS API",
            "forecast_coverage": f"{len(df)} periods",
            "last_updated": datetime.fromtimestamp(load_cache().get("last_fetch_time", 0)).isoformat() if load_cache() else "unknown",
        }
    
    except Exception as e:
        print(f"Error preparing weather for model: {e}")
        return None


def get_latest_hourly():
    """Get latest hourly forecast."""
    try:
        hourly_path = "data/processed/nws_forecast_hourly.csv"
        if not os.path.exists(hourly_path):
            return None
        
        df = pd.read_csv(hourly_path)
        return df.head(24)  # Next 24 hours
    
    except Exception as e:
        print(f"Error reading hourly forecast: {e}")
        return None


def main():
    """Test cache functionality."""
    print("="*70)
    print("NWS WEATHER CACHE MANAGER")
    print("="*70)
    
    # Test fetch
    print("\n--- Fetching weather (with cache) ---")
    fetch_if_needed()
    
    # Get current weather
    print("\n--- Current Conditions (Next Period) ---")
    current = get_current_weather()
    if current:
        print(f"Name: {current.get('name')}")
        print(f"Temperature: {current.get('temperature_f')}°F")
        print(f"Wind: {current.get('wind_speed_mph')} mph {current.get('wind_direction')}")
        print(f"Precip chance: {current.get('precipitation_chance_pct')}%")
        print(f"Forecast: {current.get('forecast')}")
    else:
        print("Could not get current weather")
    
    # Get formatted for model
    print("\n--- Weather Data for Model ---")
    model_weather = get_forecast_for_model()
    if model_weather:
        for key, val in sorted(model_weather.items()):
            print(f"  {key}: {val}")
    else:
        print("Could not get weather for model")
    
    # Show next 24 hours
    print("\n--- Next 24 Hours (Hourly) ---")
    hourly = get_latest_hourly()
    if hourly is not None:
        print(f"Available: {len(hourly)} hours")
        print(hourly[["name", "temperature_f", "forecast"]].head(6).to_string(index=False))
    else:
        print("Hourly forecast not available")
    
    # Cache status
    print("\n--- Cache Status ---")
    cache = load_cache()
    if cache:
        age = get_cache_age()
        print(f"Status: {cache.get('status')}")
        print(f"Last fetch: {cache.get('last_fetch_date')}")
        print(f"Age: {int(age)} seconds")
        print(f"TTL: {cache.get('ttl_seconds')} seconds")
        print(f"Fresh: {'Yes' if is_cache_fresh() else 'No'}")
    else:
        print("No cache found")


if __name__ == "__main__":
    main()
