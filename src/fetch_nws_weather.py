#!/usr/bin/env python3
"""
Fetch real-time weather from National Weather Service (NWS) API.
Updates weather forecast for Boston in real-time instead of historical data.

Source: https://api.weather.gov (no API key required)
Boston Location: 42.3601, -71.0589 (NWS Grid: BOX 96,70)

Run: python src/fetch_nws_weather.py

Output: 
  - data/processed/nws_forecast.csv (daily forecast)
  - data/processed/nws_forecast_hourly.csv (hourly forecast)
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime

# Boston coordinates (center of Boston)
BOSTON_LAT = 42.3601
BOSTON_LON = -71.0589

# NWS API endpoint for point lookup
POINTS_URL = f"https://api.weather.gov/points/{BOSTON_LAT},{BOSTON_LON}"

# User-Agent is required by NWS API
USER_AGENT = "Hackachusetts (github.com/jzzzzyh/Hackachusetts_Project, boston311@example.com)"

OUT_DAILY = "data/processed/nws_forecast.csv"
OUT_HOURLY = "data/processed/nws_forecast_hourly.csv"


def get_forecast_urls():
    """Get forecast URLs for Boston from NWS API."""
    print(f"Fetching Boston forecast URLs from NWS...")
    print(f"Location: {BOSTON_LAT}°N, {BOSTON_LON}°W")
    
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(POINTS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        properties = data.get("properties", {})
        
        forecast_url = properties.get("forecast")
        hourly_url = properties.get("forecastHourly")
        grid_data = properties.get("forecastGridData")
        
        if not forecast_url:
            print("ERROR: Could not find forecast URLs in response")
            print(f"Response keys: {list(properties.keys())}")
            return None, None, None
        
        print(f"✓ Got forecast URLs from NWS")
        return forecast_url, hourly_url, grid_data
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network request failed: {e}")
        return None, None, None
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None, None


def fetch_forecast(url, forecast_type="daily"):
    """Fetch weather forecast from NWS."""
    try:
        headers = {"User-Agent": USER_AGENT}
        
        print(f"Fetching {forecast_type} forecast from NWS...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        print(f"ERROR: Failed to fetch {forecast_type} forecast: {e}")
        return None


def parse_forecast(forecast_data, forecast_type="daily"):
    """Parse NWS forecast JSON into structured data."""
    rows = []
    
    try:
        periods = forecast_data.get("properties", {}).get("periods", [])
        print(f"  Found {len(periods)} periods in {forecast_type} forecast")
        
        for period in periods:
            try:
                # Extract weather data
                period_num = period.get("number", 0)
                name = period.get("name", "Unknown")
                start_time = period.get("startTime", "")
                end_time = period.get("endTime", "")
                
                # Core weather metrics
                temperature = period.get("temperature")
                temperature_unit = period.get("temperatureUnit", "F")
                
                # Wind data
                wind_speed_str = period.get("windSpeed", "0 mph")
                wind_direction = period.get("windDirection", "")
                
                # Precipitation and weather type
                weather_forecast = period.get("shortForecast", "")
                detailed_forecast = period.get("detailedForecast", "")
                
                # Precipitation probability (if available)
                precip_dict = period.get("probabilityOfPrecipitation", {})
                precip_chance = precip_dict.get("value", 0) if isinstance(precip_dict, dict) else 0
                
                # Parse wind speed (format: "10 mph" or "10 to 20 mph")
                wind_val = 0
                if wind_speed_str:
                    try:
                        # Take first number from string like "10 to 20 mph"
                        wind_val = float(wind_speed_str.split()[0])
                    except (ValueError, IndexError):
                        pass
                
                rows.append({
                    "period": period_num,
                    "name": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "temperature_f": temperature if temperature_unit == "F" else temperature,
                    "wind_speed_mph": wind_val,
                    "wind_direction": wind_direction,
                    "precipitation_chance_pct": precip_chance,
                    "forecast": weather_forecast,
                    "details": detailed_forecast,
                })
            
            except Exception as e:
                print(f"    ⚠ Warning parsing period {period.get('number')}: {e}")
                continue
        
        return rows
    
    except Exception as e:
        print(f"  ERROR: Failed to parse forecast: {e}")
        return []


def convert_to_model_format(daily_df):
    """Convert NWS forecast to model input format."""
    """
    Model expects:
    - avg_temp_c
    - total_precip_mm
    - total_snow_cm
    - max_wind_kmh
    """
    
    try:
        if daily_df.empty:
            return None
        
        # Average temperature (convert F to C)
        temps_f = daily_df["temperature_f"].dropna()
        avg_temp_f = temps_f.mean()
        avg_temp_c = (avg_temp_f - 32) * 5/9
        
        # Maximum wind speed (convert mph to kmh)
        winds_mph = daily_df["wind_speed_mph"].dropna()
        max_wind_mph = winds_mph.max()
        max_wind_kmh = max_wind_mph * 1.60934
        
        # Average precipitation chance (convert to rough mm estimate)
        # This is simplified: NWS gives % chance, not actual accumulation
        precip_pct = daily_df["precipitation_chance_pct"].mean()
        # Rough estimate: assume 10-20mm per day if high chance
        total_precip_mm = (precip_pct / 100) * 15
        
        # Snow (NWS usually only in detailed forecast text)
        total_snow_cm = 0  # Would need to parse forecast text
        
        return {
            "avg_temp_c": round(avg_temp_c, 2),
            "total_precip_mm": round(total_precip_mm, 2),
            "total_snow_cm": round(total_snow_cm, 2),
            "max_wind_kmh": round(max_wind_kmh, 2),
            "num_periods": len(daily_df),
            "forecast_span": f"{daily_df['start_time'].iloc[0]} to {daily_df['end_time'].iloc[-1]}",
        }
    
    except Exception as e:
        print(f"ERROR converting to model format: {e}")
        return None


def main():
    """Fetch current weather forecast from NWS API."""
    
    print("="*70)
    print("NWS LIVE WEATHER FETCHER FOR BOSTON")
    print("="*70)
    print()
    
    # Step 1: Get forecast URLs
    print("STEP 1: Locating Boston on NWS grid...")
    forecast_url, hourly_url, grid_url = get_forecast_urls()
    if not forecast_url:
        print("Failed to get forecast URLs. Cannot continue.")
        return False
    
    # Step 2: Fetch daily forecast
    print()
    print("STEP 2: Fetching daily forecast...")
    daily_data = fetch_forecast(forecast_url, "daily")
    if not daily_data:
        print("Failed to fetch daily forecast.")
        return False
    
    daily_rows = parse_forecast(daily_data, "daily")
    if not daily_rows:
        print("Failed to parse daily forecast.")
        return False
    
    # Step 3: Fetch hourly forecast
    print()
    print("STEP 3: Fetching hourly forecast...")
    hourly_data = fetch_forecast(hourly_url, "hourly") if hourly_url else None
    if hourly_data:
        hourly_rows = parse_forecast(hourly_data, "hourly")
    else:
        hourly_rows = []
    
    # Step 4: Save data
    print()
    print("STEP 4: Saving forecast data...")
    os.makedirs("data/processed", exist_ok=True)
    
    if daily_rows:
        df_daily = pd.DataFrame(daily_rows)
        df_daily.to_csv(OUT_DAILY, index=False)
        print(f"✓ Daily forecast saved to {OUT_DAILY}")
    
    if hourly_rows:
        df_hourly = pd.DataFrame(hourly_rows)
        df_hourly.to_csv(OUT_HOURLY, index=False)
        print(f"✓ Hourly forecast saved to {OUT_HOURLY}")
    
    # Step 5: Convert to model format
    print()
    print("STEP 5: Converting to model format...")
    model_format = convert_to_model_format(df_daily)
    if model_format:
        print("Model-compatible weather:")
        for key, val in model_format.items():
            print(f"  {key}: {val}")
    
    # Verification summary
    print()
    print("="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"✓ Location: Boston ({BOSTON_LAT}°N, {BOSTON_LON}°W)")
    print(f"✓ Data source: National Weather Service API")
    print(f"✓ API URL: https://api.weather.gov")
    print(f"✓ Daily periods: {len(daily_rows)}")
    print(f"✓ Hourly periods: {len(hourly_rows)}")
    print(f"✓ Files created:")
    print(f"  - {OUT_DAILY}")
    if hourly_rows:
        print(f"  - {OUT_HOURLY}")
    print()
    
    # Show sample forecast
    if not df_daily.empty:
        print("Sample forecast (first 3 days):")
        print(df_daily[["name", "temperature_f", "wind_speed_mph", "forecast"]].head(3).to_string(index=False))
    
    print()
    print("✓ NWS weather fetch completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
