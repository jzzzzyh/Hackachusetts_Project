# Boston Neighborhoods Cleanup (Step 1b)

Clean and prepare Boston neighborhood boundary data from GeoJSON for spatial analysis.

## Overview

This step takes the Boston neighborhood boundaries GeoJSON file and:
1. Cleans up the data (keeps only essential columns)
2. Exports two formats:
   - GeoJSON with geometries (for spatial joins)
   - CSV with metadata only (for lookups)

## Scripts

### clean_neighborhoods.py

**Purpose:** Clean and split neighborhood boundaries data

**Input:**
- `boston_neighborhood_boundaries.geojson` (26 features, MultiPolygon/Polygon geometries)
- Columns: OBJECTID, name, acres, neighborhood_id, sqmiles, plus geometry

**Output:**
- `data/boston_neighborhoods.geojson` — GeoJSON with geometries
  - Columns: name, neighborhood_id, sqmiles, geometry
  - Ready for spatial joins with road segments
  
- `data/boston_neighborhoods.csv` — Metadata only
  - Columns: name, neighborhood_id, sqmiles
  - For quick lookups without loading geometry

**Functionality:**
- Loads GeoJSON from local file or URL fallback
- Validates required columns exist
- Converts coordinate order if needed
- Prints summaries of input/output data
- Creates data/ directory automatically

**Usage:**
```bash
python3 clean_neighborhoods.py
```

**Output:**
```
============================================================
Boston Neighborhood Boundaries Cleaner
============================================================

✓ Output directory: data

============================================================
Loading neighborhoods...
============================================================
Loading from local file: boston_neighborhood_boundaries.geojson
✓ Loaded 26 features from local file

============================================================
Cleaning data...
============================================================
  Available columns: ['OBJECTID', 'name', 'acres', 'neighborhood_id', 'sqmiles', 'geometry']
  Keeping columns: ['name', 'neighborhood_id', 'sqmiles', 'geometry']
✓ Cleaned to 26 features with 4 columns

============================================================
Saving outputs...
============================================================

Saving GeoJSON to data/boston_neighborhoods.geojson...
✓ Saved 26 features to GeoJSON

Saving CSV to data/boston_neighborhoods.csv...
✓ Saved 26 rows to CSV with columns: ['name', 'neighborhood_id', 'sqmiles']

============================================================
Output Summary
============================================================

GeoJSON Summary
------------------------------------------------------------
Shape: (26, 4)
Columns: ['name', 'neighborhood_id', 'sqmiles', 'geometry']
CRS: EPSG:4326

First 3 rows:
                name  neighborhood_id  sqmiles
0              Downtown               1     1.95
1             Back Bay               2     3.28
2            Cambridge               3     5.94

CSV Summary
------------------------------------------------------------
Shape: (26, 3)
Columns: ['name', 'neighborhood_id', 'sqmiles']
CRS: None

First 3 rows:
                name  neighborhood_id  sqmiles
0              Downtown               1     1.95
1             Back Bay               2     3.28
2            Cambridge               3     5.94

============================================================
✓ Complete!
============================================================

Generated files:
  data/boston_neighborhoods.geojson
  data/boston_neighborhoods.csv

Next steps:
  • Use data/boston_neighborhoods.geojson for spatial joins with road segments
  • Use data/boston_neighborhoods.csv for neighborhood metadata lookups
```

### create_sample_neighborhoods.py (Optional Testing)

**Purpose:** Create sample GeoJSON data for testing

**Use case:** Test `clean_neighborhoods.py` without the full real dataset

**Creates:**
- `boston_neighborhood_boundaries.geojson` — 3 sample neighborhoods
  - Downtown (1.95 sq mi)
  - Back Bay (3.28 sq mi)
  - Cambridge (5.94 sq mi)
  - Mixed Polygon and MultiPolygon geometries

**Usage:**
```bash
python3 create_sample_neighborhoods.py
```

**Then run:**
```bash
python3 clean_neighborhoods.py
```

## Input Data Format

### boston_neighborhood_boundaries.geojson

**Type:** GeoJSON FeatureCollection

**Expected structure:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "OBJECTID": 1,
        "name": "Downtown",
        "acres": 1250,
        "neighborhood_id": 1,
        "sqmiles": 1.95
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [...]
      }
    },
    ...
  ]
}
```

**Required properties:**
- `name` — Neighborhood name
- `neighborhood_id` — Unique identifier
- `sqmiles` — Area in square miles

**Geometry types:**
- Polygon — Single boundary
- MultiPolygon — Multiple disjoint areas

## Output Data Formats

### data/boston_neighborhoods.geojson

**Type:** GeoJSON FeatureCollection

**Columns:**
- `name` — Neighborhood name
- `neighborhood_id` — Unique ID
- `sqmiles` — Area in square miles
- `geometry` — Polygon/MultiPolygon (WGS84)

**Use case:**
- Spatial joins with road segments
- Creating neighborhood-level aggregations
- Mapping and visualization

**Load with geopandas:**
```python
import geopandas as gpd

gdf = gpd.read_file('data/boston_neighborhoods.geojson')
print(f"Loaded {len(gdf)} neighborhoods")
print(gdf.head())
```

### data/boston_neighborhoods.csv

**Type:** CSV (comma-separated values)

**Columns:**
- `name` — Neighborhood name
- `neighborhood_id` — Unique ID
- `sqmiles` — Area in square miles

**No geometry column** — Faster for simple lookups

**Use case:**
- Quick metadata lookups
- Joining with tabular data
- Lightweight data operations

**Load with pandas:**
```python
import pandas as pd

df = pd.read_csv('data/boston_neighborhoods.csv')
print(f"Loaded {len(df)} neighborhoods")
print(df.head())
```

## Workflow

### Full Execution

```bash
# 1. Ensure you have the GeoJSON file
#    Either copy it to the project directory or use the URL fallback
cp boston_neighborhood_boundaries.geojson .

# 2. Clean and split the data
python3 clean_neighborhoods.py

# 3. Verify outputs
ls -lh data/boston_neighborhoods.*

# 4. Quick validation
python3 -c "
import geopandas as gpd
import pandas as pd

gdf = gpd.read_file('data/boston_neighborhoods.geojson')
df = pd.read_csv('data/boston_neighborhoods.csv')

print(f'GeoJSON: {len(gdf)} neighborhoods with geometry')
print(f'CSV: {len(df)} neighborhoods (metadata only)')
"
```

### Testing with Sample Data

```bash
# 1. Create sample data
python3 create_sample_neighborhoods.py

# 2. Run cleaner on sample
python3 clean_neighborhoods.py

# 3. Verify small outputs
ls -lh data/
```

## File Locations

### Input
- Local search paths:
  - Current directory (`.`)
  - `~/.kiro/crew/uploads/`
  - `~/Downloads/`
  - `~/Desktop/`
  - URL fallback (if not found locally)

### Output
- `data/boston_neighborhoods.geojson` (~100+ MB with real data)
- `data/boston_neighborhoods.csv` (~10 KB)

## Features

✓ **Flexible loading** — Searches multiple directories + URL fallback
✓ **Data validation** — Checks for required columns
✓ **Progress tracking** — Prints each step
✓ **Automatic directory creation** — Creates `data/` if needed
✓ **Type hints** — Full type annotations
✓ **Error handling** — Graceful failures with informative messages

## Next Steps

Once neighborhoods are cleaned:

1. **Step 2:** Spatial join with road segments
   - Load `data/boston_neighborhoods.geojson`
   - Load road segment data
   - Assign each segment to a neighborhood
   - Create neighborhood feature for model

2. **Step 3-7:** Continue building predictive pipeline
   - Add traffic intensity features (MBTA bus routes)
   - Integrate historical pothole data
   - Engineer predictive features
   - Train model
   - Generate predictions with equity analysis

## Troubleshooting

### File not found

```bash
# Check current directory
ls -la boston_neighborhood_boundaries.geojson

# Check other locations
find ~ -name "*boston*neighborhood*" 2>/dev/null

# Use URL directly in script (already configured as fallback)
```

### GeoJSON validation errors

```bash
# Test with geopandas directly
python3 -c "import geopandas as gpd; gdf = gpd.read_file('boston_neighborhood_boundaries.geojson'); print(gdf.head())"
```

### Memory issues with large files

```bash
# Use CSV instead for non-spatial operations
import pandas as pd
df = pd.read_csv('data/boston_neighborhoods.csv')
```

## Dependencies

- **geopandas** — GeoJSON/geographic data processing
- **pandas** — CSV handling
- **shapely** — Geometry operations (via geopandas)

Install with:
```bash
pip install geopandas pandas
```

## Performance

| Task | Time | Notes |
|------|------|-------|
| Load 26 neighborhoods | <1s | From local file |
| Clean data | <1s | Simple column selection |
| Save GeoJSON | ~5-10s | I/O bound |
| Save CSV | <1s | Simple CSV write |
| **Total** | **~10s** | Very fast |

## Files Generated

After running `clean_neighborhoods.py`:

```
Hackachusetts_Project/
└── data/
    ├── boston_neighborhoods.geojson  (for spatial ops)
    └── boston_neighborhoods.csv      (for lookups)
```

Both ready for Step 2 (spatial joins with road segments).
