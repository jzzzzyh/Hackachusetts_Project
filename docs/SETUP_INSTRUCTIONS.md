# Step 1: MBTA Bus Shapes - Setup & Execution

## Quick Start

This project fetches MBTA bus route and shape data, then converts encoded polylines to GeoJSON format.

### Step 1: Install Dependencies

```bash
# Option A: Using pip
pip install -r requirements.txt

# Option B: Individual packages
pip install requests polyline geopandas pandas shapely
```

### Step 2: Run the Fetcher

```bash
python3 fetch_mbta_bus_shapes.py
```

**Expected output:**
```
============================================================
MBTA Bus Shapes Fetcher
============================================================
Fetching bus routes...
  Fetching page 1 (offset=0)...
  Retrieved 47 records (total: 47)
Fetching bus shapes...
  Fetching page 1 (offset=0)...
  Retrieved 100 records (total: 100)
  Fetching page 2 (offset=100)...
  Retrieved 100 records (total: 200)
  ... (continues until all shapes fetched)

Total fetched: 47 routes, ~3,500+ shapes

============================================================
Saving data files...
============================================================
Saving routes to data/mbta_bus_routes.csv...
  Saved 47 routes
Saving shapes to data/mbta_bus_shapes.json...
  Saved 3500+ shapes

============================================================
✓ Complete!
============================================================
```

**Output files created:**
- `data/mbta_bus_routes.csv` (~5 KB)
- `data/mbta_bus_shapes.json` (~20+ MB)

### Step 3: Run the Decoder

```bash
python3 decode_mbta_shapes.py
```

**Expected output:**
```
============================================================
MBTA Shapes GeoJSON Decoder
============================================================
Loading shapes from data/mbta_bus_shapes.json...
  Loaded 3500+ shapes
Decoding polylines...
  Decoded 100/3500 shapes...
  Decoded 200/3500 shapes...
  ... (continues)
  Valid shapes: 3500+, Skipped: 0

============================================================
Saving output...
============================================================
Saving GeoJSON to data/mbta_bus_shapes.geojson...
  Saved 3500+ features

============================================================
✓ Complete!
============================================================

Output file: data/mbta_bus_shapes.geojson
Total features: 3500+
```

**Output file created:**
- `data/mbta_bus_shapes.geojson` (~100+ MB)

## Verification

After running both scripts, verify the output:

```python
import geopandas as gpd

# Load the generated GeoJSON
gdf = gpd.read_file('data/mbta_bus_shapes.geojson')

print(f"✓ Loaded {len(gdf)} bus shapes")
print(f"  Geometry type: {gdf.geometry.type.unique()}")
print(f"  Bounds: {gdf.total_bounds}")
print(f"  Columns: {gdf.columns.tolist()}")

# Show first few features
print("\nFirst 3 features:")
print(gdf[['shape_id', 'route_id', 'geometry']].head(3))
```

## What Each Script Does

### fetch_mbta_bus_shapes.py

1. **Fetches routes:** GET https://api-v3.mbta.com/routes?filter[type]=3
   - Gets all 47 MBTA bus routes
   - Saves to `data/mbta_bus_routes.csv`

2. **Fetches shapes:** GET https://api-v3.mbta.com/shapes?filter[route_type]=3
   - Gets all shape geometries (encoded polylines)
   - Paginates with offset/limit (100 per page)
   - Saves to `data/mbta_bus_shapes.json`

3. **Error handling:**
   - Retries once on timeout (10 second timeout)
   - Prints progress for each page
   - Descriptive error messages

### decode_mbta_shapes.py

1. **Loads raw shapes** from `data/mbta_bus_shapes.json`

2. **Decodes polylines:**
   - Each encoded polyline → list of (lat, lon) tuples
   - Uses `polyline.decode()` (Google algorithm)

3. **Converts to GeoJSON:**
   - (lat, lon) tuples → [lon, lat] arrays (GeoJSON standard)
   - Creates LineString geometries
   - Wraps in FeatureCollection

4. **Saves output** to `data/mbta_bus_shapes.geojson`
   - Valid GeoJSON readable by geopandas
   - Each feature has properties: shape_id, route_id

## File Structure

```
Hackachusetts_Project/
├── fetch_mbta_bus_shapes.py      # Step 1: Fetch from API
├── decode_mbta_shapes.py         # Step 2: Decode to GeoJSON
├── test_decode_sample.py         # Optional: Test polyline decoding
├── requirements.txt              # Python dependencies
├── README_STEP1.md              # Documentation
├── SETUP_INSTRUCTIONS.md        # This file
└── data/
    ├── mbta_bus_routes.csv       # Generated: Route metadata
    ├── mbta_bus_shapes.json      # Generated: Raw encoded shapes
    └── mbta_bus_shapes.geojson   # Generated: Final GeoJSON
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'polyline'"

```bash
pip install polyline
```

### "ModuleNotFoundError: No module named 'requests'"

```bash
pip install requests
```

### Script hangs/times out

- Network issue with MBTA API
- Try running again (may be temporary)
- Check internet connection
- The API has no rate limit for public access

### Output files are very large

- `mbta_bus_shapes.json` can be 20-30 MB
- `mbta_bus_shapes.geojson` can be 100+ MB
- This is normal—it contains all ~3,500+ Boston bus shapes
- Use `--no-mmap` with geopandas on older systems if memory is tight

## Next Steps

Once you have `data/mbta_bus_shapes.geojson`:

1. This is the foundation for Step 2 (spatial features)
2. You'll spatially join with road segment data
3. Create `on_bus_route` binary feature per segment
4. Continue building the pothole prediction pipeline

## Performance Notes

- **Fetch script:** ~30-60 seconds (depends on network)
- **Decode script:** ~20-40 seconds (CPU-bound polyline decoding)
- **GeoJSON file:** ~100+ MB (don't commit to git, add to .gitignore)
- **Total data:** ~40-50 MB raw JSON → ~100+ MB GeoJSON

## Data Dictionary

### mbta_bus_routes.csv
- `route_id`: Unique route identifier (e.g., "1", "22", "47")
- `long_name`: Full route name (e.g., "Charles Circle - Downtown - Jackson Square")
- `short_name`: Short route number (e.g., "1", "22")

### mbta_bus_shapes.json (raw)
- `id`: Unique shape identifier
- `polyline`: Encoded polyline string (Google algorithm)
- `route_id`: Associated route ID

### mbta_bus_shapes.geojson (processed)
- `type`: "FeatureCollection"
- `features[]`: Array of LineString features
  - `shape_id`: Unique shape identifier
  - `route_id`: Associated route ID
  - `geometry`: GeoJSON LineString with [lon, lat] coordinates

## API Details

### MBTA V3 API (No authentication required)

**Routes endpoint:**
- URL: https://api-v3.mbta.com/routes
- Filter: `type=3` (bus routes only)
- Pagination: `page[limit]=100&page[offset]=N`

**Shapes endpoint:**
- URL: https://api-v3.mbta.com/shapes
- Filter: `route_type=3` (bus route shapes)
- Pagination: `page[limit]=100&page[offset]=N`

### Polyline Encoding

Google's encoded polyline algorithm compresses lat/lon sequences.

Example: `_p~iF~ps|U_ulLnnqC_mqNvxq`@`
- Represents a sequence of coordinates
- Decoded: [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]

## References

- [MBTA V3 API Docs](https://www.mbta.com/developers/v3-api)
- [Google Polyline Algorithm](https://developers.google.com/maps/documentation/utilities/polylinealgorithm)
- [GeoJSON Specification](https://geojson.org/)
- [GeoPandas Documentation](https://geopandas.org/)
