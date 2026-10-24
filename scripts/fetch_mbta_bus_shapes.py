"""
Fetch MBTA bus routes and shapes from the V3 API.

This script retrieves:
1. All bus route metadata (routes with type=3)
2. All bus shape geometries (encoded polylines)

Data is paginated through the MBTA API and saved to:
- data/mbta_bus_routes.csv
- data/mbta_bus_shapes.json
"""

import json
import csv
import requests
import time
from typing import List, Dict, Any
from pathlib import Path


BASE_URL = "https://api-v3.mbta.com"
PAGE_LIMIT = 100
MAX_RETRIES = 1
TIMEOUT = 10


def fetch_paginated(endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Fetch paginated data from MBTA API.
    
    Args:
        endpoint: API endpoint path (e.g., '/routes')
        params: Query parameters
        
    Returns:
        List of all records across all pages
    """
    if params is None:
        params = {}
    
    all_data = []
    offset = 0
    page_num = 0
    
    while True:
        page_num += 1
        params['page[limit]'] = PAGE_LIMIT
        params['page[offset]'] = offset
        
        url = f"{BASE_URL}{endpoint}"
        
        retry_count = 0
        while retry_count <= MAX_RETRIES:
            try:
                print(f"  Fetching page {page_num} (offset={offset})...")
                response = requests.get(url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    raise Exception(f"Timeout after {MAX_RETRIES} retries on {url}")
                print(f"    Timeout, retrying... (attempt {retry_count})")
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to fetch {url}: {e}")
        
        data = response.json()
        records = data.get('data', [])
        
        if not records:
            break
        
        all_data.extend(records)
        print(f"    Retrieved {len(records)} records (total: {len(all_data)})")
        
        offset += PAGE_LIMIT
    
    return all_data


def fetch_bus_routes() -> List[Dict[str, Any]]:
    """
    Fetch all bus routes (type=3) from MBTA API.
    
    Returns:
        List of route records with id, long_name, short_name
    """
    print("Fetching bus routes...")
    params = {'filter[type]': '3'}
    return fetch_paginated('/routes', params)


def fetch_bus_shapes() -> List[Dict[str, Any]]:
    """
    Fetch all bus shapes (type=3) from MBTA API.
    
    Returns:
        List of shape records with id, polyline, route_id
    """
    print("Fetching bus shapes...")
    params = {'filter[route_type]': '3'}
    return fetch_paginated('/shapes', params)


def save_routes_csv(routes: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save routes to CSV with columns: route_id, long_name, short_name.
    
    Args:
        routes: List of route records from API
        output_path: Path to write CSV file
    """
    print(f"Saving routes to {output_path}...")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['route_id', 'long_name', 'short_name'])
        
        for route in routes:
            writer.writerow([
                route.get('id', ''),
                route.get('attributes', {}).get('long_name', ''),
                route.get('attributes', {}).get('short_name', '')
            ])
    
    print(f"  Saved {len(routes)} routes")


def save_shapes_json(shapes: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save shapes to JSON with id, polyline, route_id fields.
    
    Args:
        shapes: List of shape records from API
        output_path: Path to write JSON file
    """
    print(f"Saving shapes to {output_path}...")
    
    # Extract relevant fields
    simplified_shapes = []
    for shape in shapes:
        simplified_shapes.append({
            'id': shape.get('id', ''),
            'polyline': shape.get('attributes', {}).get('polyline', ''),
            'route_id': shape.get('relationships', {}).get('route', {}).get('data', {}).get('id', '')
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_shapes, f, indent=2)
    
    print(f"  Saved {len(simplified_shapes)} shapes")


def main():
    """Main entry point."""
    print("=" * 60)
    print("MBTA Bus Shapes Fetcher")
    print("=" * 60)
    
    # Create data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Fetch data
    routes = fetch_bus_routes()
    shapes = fetch_bus_shapes()
    
    print(f"\nTotal fetched: {len(routes)} routes, {len(shapes)} shapes")
    
    # Save data
    print("\n" + "=" * 60)
    print("Saving data files...")
    print("=" * 60)
    
    save_routes_csv(routes, 'data/mbta_bus_routes.csv')
    save_shapes_json(shapes, 'data/mbta_bus_shapes.json')
    
    print("\n" + "=" * 60)
    print("✓ Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
