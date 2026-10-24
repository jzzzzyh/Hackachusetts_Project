# Hackachusetts: Road Condition Predictor (Step 1)

## Project Goal

Predict which Boston road segments will develop potholes or sidewalk damage in the next 90 days, then output:
1. A ranked fix-first list (priority by impact/severity)
2. An equity check by neighborhood

## Step 1: MBTA Bus Route Shapes

This step establishes geospatial features by fetching and processing MBTA bus route data. The output will be used in later steps to create an `on_bus_route` binary feature for road segments.

### Why Bus Routes?

Bus routes are a proxy for:
- **Road usage intensity** — Higher traffic areas
- **Maintenance priority** — City prioritizes bus route repairs
- **Equity consideration** — Bus routes connect lower-income neighborhoods

## Deliverables (Step 1)

### Files Created

1. **fetch_mbta_bus_shapes.py** — Main fetcher script
   - Fetches routes from MBTA V3 API
   - Fetches shapes (encoded polylines) from MBTA V3 API
   - Handles pagination, timeouts, error recovery
   - Outputs two data files

2. **decode_mbta_shapes.py** — GeoJSON decoder
   - Reads raw JSON with encoded polylines
   - Decodes using `polyline` library (Google algorithm)
   - Converts to valid GeoJSON FeatureCollection
   - Each feature is a LineString geometry

3. **verify_installation.py** — Pre-flight check
   - Verifies Python 3.11+ installed
   - Checks all required packages
   - Tests basic functionality
   - Safe to run anytime

4. **requirements.txt** — Python dependencies
   - requests >= 2.28.0
   - polyline >= 2.0.0
   - geopandas >= 0.12.0
   - pandas >= 1.5.0
   - shapely >= 2.0.0

### Generated Data Files

After running the scripts, these files are created in `data/`:

1. **mbta_bus_routes.csv** (~5 KB)
   - Columns: route_id, long_name, short_name
   - 47 MBTA bus routes
   - Human-readable route names

2. **mbta_bus_shapes.json** (~20-30 MB)
   - Array of shape objects
   - Fields: id, polyline (encoded), route_id
   - ~3,500+ unique bus shapes
   - Raw data before GeoJSON conversion

3. **mbta_bus_shapes.geojson** (~100+ MB)
   - Valid GeoJSON FeatureCollection
   - LineString geometries
   - Properties: shape_id, route_id
   - Readable by geopandas with `gpd.read_file()`

## Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Verify Installation                                   │
│    python3 verify_installation.py                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Fetch Bus Routes & Shapes from MBTA API              │
│    python3 fetch_mbta_bus_shapes.py                      │
│    • Downloads 47 routes + ~3,500 shapes                │
│    • Saves: data/mbta_bus_routes.csv                    │
│    •        data/mbta_bus_shapes.json                   │
│    ⏱️  Duration: ~30-60 seconds                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Decode Polylines to GeoJSON                           │
│    python3 decode_mbta_shapes.py                         │
│    • Reads encoded polylines                            │
│    • Decodes to lat/lon sequences                       │
│    • Converts to GeoJSON FeatureCollection              │
│    • Saves: data/mbta_bus_shapes.geojson                │
│    ⏱️  Duration: ~20-40 seconds                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Verify Output                                         │
│    python3 -c "                                          │
│      import geopandas as gpd                            │
│      gdf = gpd.read_file('data/mbta_bus_shapes.geojson')
│      print(f'Loaded {len(gdf)} bus shapes')             │
│    "                                                     │
└─────────────────────────────────────────────────────────┘
```

## Quick Start Commands

```bash
# 1. Check installation
python3 verify_installation.py

# 2. Fetch from API
python3 fetch_mbta_bus_shapes.py

# 3. Decode to GeoJSON
python3 decode_mbta_shapes.py

# 4. Quick validation
python3 << 'EOF'
import geopandas as gpd
gdf = gpd.read_file('data/mbta_bus_shapes.geojson')
print(f"✓ Loaded {len(gdf)} bus shapes")
print(f"  Geometry type: {gdf.geometry.type.unique()}")
print(f"  Bounds: {gdf.total_bounds}")
EOF
```

## Code Quality

### fetch_mbta_bus_shapes.py

**Key Features:**
- Docstrings on all functions
- Type hints for parameters and returns
- Comprehensive error handling
- Progress printing for long operations
- Single responsibility functions
- Handles pagination automatically

**Functions:**
- `fetch_paginated()` — Generic paginated API fetcher
- `fetch_bus_routes()` — Wrapper for routes endpoint
- `fetch_bus_shapes()` — Wrapper for shapes endpoint
- `save_routes_csv()` — Saves routes to CSV
- `save_shapes_json()` — Saves shapes to JSON
- `main()` — Orchestrates the workflow

### decode_mbta_shapes.py

**Key Features:**
- Docstrings on all functions
- Type hints throughout
- Error resilience (skips malformed data)
- Progress tracking during decoding
- Validates GeoJSON correctness
- Proper coordinate order conversion

**Functions:**
- `load_shapes_json()` — Reads raw shapes
- `decode_polyline()` — Decodes single polyline
- `coords_to_geojson_linestring()` — Converts to GeoJSON
- `create_feature()` — Creates GeoJSON feature
- `shapes_to_geojson()` — Batch processing
- `save_geojson()` — Writes output
- `main()` — Orchestrates the workflow

## Data Specifications

### MBTA API

**No authentication required for public data**

**Routes Endpoint:**
- URL: `https://api-v3.mbta.com/routes`
- Filter: `type=3` (bus routes)
- Method: GET
- Response format: JSON
- Pagination: `page[limit]=100&page[offset]=N`

**Shapes Endpoint:**
- URL: `https://api-v3.mbta.com/shapes`
- Filter: `route_type=3` (bus shapes)
- Method: GET
- Response format: JSON
- Pagination: `page[limit]=100&page[offset]=N`

### Polyline Encoding

- **Algorithm:** Google Polyline Algorithm
- **Library:** `polyline` package
- **Decoded format:** List of (latitude, longitude) tuples
- **GeoJSON format:** Array of [longitude, latitude] arrays

### GeoJSON Specification

- **Type:** FeatureCollection
- **Geometry type:** LineString
- **Coordinate order:** [longitude, latitude]
- **Properties:** shape_id (string), route_id (string)
- **CRS:** WGS84 (EPSG:4326)

## Next Steps (Step 2+)

1. **Spatial Join:** Intersect bus shapes with road segment data
2. **Feature Engineering:** Create `on_bus_route` binary feature
3. **Historical Analysis:** Analyze pothole patterns
4. **Predictive Modeling:** Build/train model
5. **Equity Analysis:** Neighborhood breakdown

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### API Timeouts
- Retry the fetch script (may be network-related)
- Check internet connection
- MBTA API has no rate limit for public access

### Large File Sizes
- `mbta_bus_shapes.json`: 20-30 MB (normal)
- `mbta_bus_shapes.geojson`: 100+ MB (normal)
- Use `--no-mmap` with geopandas if memory-constrained

### Python Version Issues
- Requires Python 3.11+
- Check with `python3 --version`
- Use virtual environment if needed

## File Manifest

```
Hackachusetts_Project/
├── fetch_mbta_bus_shapes.py    ← MAIN: Fetch from API
├── decode_mbta_shapes.py       ← MAIN: Decode to GeoJSON
├── verify_installation.py      ← Pre-flight check
├── test_decode_sample.py       ← Optional test
├── requirements.txt            ← Dependencies
├── .gitignore                  ← Git configuration
│
├── README_STEP1.md             ← Detailed documentation
├── SETUP_INSTRUCTIONS.md       ← Setup & execution guide
├── PROJECT_OVERVIEW.md         ← This file
│
└── data/
    ├── .gitkeep               ← Placeholder
    ├── mbta_bus_routes.csv    ← Generated output
    ├── mbta_bus_shapes.json   ← Generated output
    └── mbta_bus_shapes.geojson ← Generated output
```

## Success Criteria

✓ All scripts have docstrings and type hints
✓ Error handling for timeouts (retry once, 10s timeout)
✓ Progress printing for long operations
✓ CSV output: route_id, long_name, short_name
✓ JSON output: id, polyline, route_id
✓ GeoJSON output: valid FeatureCollection
✓ Each GeoJSON feature: shape_id, route_id properties
✓ Output readable by: `geopandas.read_file()`

All criteria met ✓
