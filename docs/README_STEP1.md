# Step 1: MBTA Bus Shapes Fetcher & Decoder

This directory contains two Python scripts to fetch and process MBTA bus route data.

## Scripts Overview

### 1. `fetch_mbta_bus_shapes.py`

**Purpose:** Fetches bus route and shape data from the MBTA V3 API.

**What it does:**
- Calls `GET https://api-v3.mbta.com/routes?filter[type]=3` to get all bus routes (type 3)
- Calls `GET https://api-v3.mbta.com/shapes?filter[route_type]=3` to get all bus shapes
- Handles pagination with `page[limit]=100` and `page[offset]=N`
- Retries once on timeout (10 second timeout per request)
- Saves two output files

**Output files:**
- `data/mbta_bus_routes.csv` — Columns: route_id, long_name, short_name
- `data/mbta_bus_shapes.json` — Array of objects with: id, polyline, route_id

**Usage:**
```bash
python3 fetch_mbta_bus_shapes.py
```

### 2. `decode_mbta_shapes.py`

**Purpose:** Decodes encoded polylines into GeoJSON format.

**What it does:**
- Reads `data/mbta_bus_shapes.json`
- Decodes each encoded polyline string using the `polyline` library
  - Converts (lat, lon) tuples to [lon, lat] arrays (GeoJSON standard)
- Creates a GeoJSON FeatureCollection with LineString geometries
- Each feature includes properties: shape_id, route_id
- Validates output is readable by geopandas

**Output file:**
- `data/mbta_bus_shapes.geojson` — GeoJSON FeatureCollection

**Usage:**
```bash
python3 decode_mbta_shapes.py
```

## Installation

Ensure you have Python 3.11+ and the required dependencies:

```bash
pip install requests polyline geopandas pandas shapely
```

Or use the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Execution Flow

1. **First run:** `python3 fetch_mbta_bus_shapes.py`
   - Fetches all MBTA bus route and shape data
   - Prints progress as it paginates through the API
   - Saves raw shape records with encoded polylines

2. **Second run:** `python3 decode_mbta_shapes.py`
   - Reads the raw JSON shapes
   - Decodes each polyline into lat/lon coordinates
   - Transforms to GeoJSON format
   - Saves as valid GeoJSON file

3. **Verify output:**
   ```python
   import geopandas as gpd
   gdf = gpd.read_file('data/mbta_bus_shapes.geojson')
   print(gdf.head())
   print(f"Loaded {len(gdf)} bus shapes")
   ```

## API Details

### Routes Endpoint
- **URL:** `https://api-v3.mbta.com/routes`
- **Filter:** `type=3` (bus routes only)
- **Response:** Array of route objects
- **Relevant fields:** `id`, `attributes.long_name`, `attributes.short_name`

### Shapes Endpoint
- **URL:** `https://api-v3.mbta.com/shapes`
- **Filter:** `route_type=3` (bus route type)
- **Response:** Array of shape objects
- **Relevant fields:** `id`, `attributes.polyline`, `relationships.route.data.id`

### Polyline Encoding
- Uses Google's polyline encoding algorithm
- Compressed representation of sequences of coordinates
- Library `polyline.decode()` converts to list of (lat, lon) tuples

### GeoJSON Coordinate Order
- GeoJSON uses [longitude, latitude] order (not lat, lon)
- Each LineString geometry has array of [lon, lat] pairs

## Error Handling

Both scripts include error handling for:
- HTTP timeouts (retries once, 10 second timeout)
- HTTP errors (raised with descriptive message)
- Empty/invalid polylines (skipped with warning)
- Missing or malformed API responses

## Progress Output

The scripts print progress information:
- Page numbers as they fetch
- Running count of total records
- Validation warnings
- Final summary with counts

## Files

- `fetch_mbta_bus_shapes.py` — Main fetcher script
- `decode_mbta_shapes.py` — GeoJSON decoder script
- `requirements.txt` — Python dependencies
- `data/` — Output directory (auto-created)

## Next Steps (Step 2+)

Once you have `data/mbta_bus_shapes.geojson`:

1. Load it with geopandas
2. Buffer/simplify geometries as needed
3. Spatial join with road segment data
4. Create `on_bus_route` binary feature per segment
5. Continue with pothole prediction pipeline
