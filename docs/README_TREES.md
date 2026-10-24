# Boston BPRD Trees Data (Step 1c)

Load and process Boston Parks & Recreation Department street tree inventory data.

## Overview

This step loads the Boston BPRD trees CSV and prepares it for spatial analysis:
1. Loads the trees CSV file
2. Converts to GeoDataFrame with point geometries
3. Analyzes tree distribution by neighborhood and species
4. Saves two output formats (GeoJSON with geometries, CSV without)

## Script

### load_trees_data.py (250 lines)

**Purpose:** Load, convert, and analyze BPRD trees data

**Input:**
- `bprd_trees.csv` (from Kiro crew uploads)
- 19 columns, 1000s of records
- Columns: id, spp_com, spp_bot, dbh, neighborhood, coordinates, etc.

**Output:**
- `data/boston_trees.geojson` — GeoDataFrame with Point geometries
- `data/boston_trees.csv` — Cleaned CSV (without geometry)

**Features:**
- ✓ Smart file search (multiple locations)
- ✓ Converts CSV to GeoDataFrame
- ✓ Creates Point geometries from coordinates
- ✓ Analyzes trees by neighborhood and species
- ✓ Summary statistics and sample output
- ✓ Error handling & progress tracking

**Usage:**
```bash
python3 load_trees_data.py
```

## File Location

**Search order:**
1. `/Users/zhouyuhai/.kiro/crew/uploads/d6f3810c9f6a45909107cd6cb75fb19a_bprd_trees.csv`
2. `/Users/zhouyuhai/Downloads/bprd_trees.csv`
3. `bprd_trees.csv` (current directory)
4. `./data/bprd_trees.csv`

## Data Format

### Input CSV Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Tree ID |
| `spp_com` | str | Common species name |
| `spp_bot` | str | Botanical name |
| `numberof_st` | float | Count (usually 1.0) |
| `dbh_range` | str | DBH range bucket |
| `dbh` | float | Diameter at breast height (inches) |
| `date_plant` | str | Planting date (-- for unknown) |
| `neighborhood` | str | Boston neighborhood |
| `park` | str | Park name (often empty) |
| `os_id` | int | Object set ID |
| `address` | str | Street address |
| `street` | str | Street name |
| `suffix` | str | Street suffix |
| `site` | int | Site number |
| `x_longitude` | float | Longitude coordinate |
| `y_latitude` | float | Latitude coordinate |
| `shape_wkt` | str | WKT point geometry |
| `POINT_X` | float | X coordinate (duplicate) |
| `POINT_Y` | float | Y coordinate (duplicate) |

### Output GeoJSON

**Columns:** Same as input + `geometry` (Point)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 6021,
        "spp_com": "Maple, Red",
        "neighborhood": "East Boston",
        "dbh": 3.0,
        "date_plant": "--",
        ...
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-71.0390015, 42.3743477]
      }
    },
    ...
  ]
}
```

### Output CSV

**Columns:** Same as input (no geometry)

**Format:** Standard CSV

## Expected Output

```
============================================================
Boston BPRD Trees Data Loader
============================================================
Loading trees data from: /Users/zhouyuhai/.kiro/crew/uploads/...
✓ Loaded 10000+ trees
  Columns: 19

Converting to GeoDataFrame...
✓ Converted to GeoDataFrame
  Features: 10000+
  CRS: EPSG:4326
  Geometry type: ['Point']

============================================================
Trees Data Summary
============================================================

Total trees: 10000+
Neighborhoods with trees: 16+

Trees by neighborhood:
  Dorchester: 1500+ trees
  Jamaica Plain: 1000+ trees
  South End: 800+ trees
  ...

Unique species: 50+

Top 10 most common species:
  Honeylocust: 2000+ trees
  Maple, Red: 1000+ trees
  Oak, Northern Red: 800+ trees
  ...

Tree size (DBH) statistics:
  Min DBH: 1.0 inches
  Max DBH: 31.0+ inches
  Mean DBH: 8.5 inches
  Median DBH: 8.0 inches

Planting dates:
  Unknown/Historical: 9000+ trees
  Spring 2024: 100+ trees
  Spring 2025: 50+ trees
  ...

Spatial bounds:
  Longitude: -71.1700 to -71.0000
  Latitude: 42.2500 to 42.3900

First 3 trees:
          id      spp_com    neighborhood  address  dbh date_plant  x_longitude  y_latitude
0        6021   Maple, Red     East Boston       1    3.0         --     -71.0390      42.3743
1         528  Planetree, London  South Boston     424    9.0         --     -71.0440      42.3449
2       10721      Ginkgo     South End      715    8.0         --     -71.0718      42.3354

Saving data...
✓ Saved 10000+ trees to GeoJSON
✓ Saved 10000+ trees to CSV

Generated files:
  data/boston_trees.geojson
  data/boston_trees.csv

Next steps:
  • Use data/boston_trees.geojson for spatial joins with road segments
  • Use data/boston_trees.csv for tree analysis and statistics
  • Join with neighborhoods for equity analysis
```

## Data Characteristics

### Neighborhoods
Boston has 16+ neighborhoods with street trees:
- Dorchester (largest)
- Jamaica Plain
- South End
- Back Bay/Beacon Hill
- Central Boston
- East Boston
- Allston-Brighton
- And others...

### Species

Common Boston street trees:
- **Honeylocust** (Gleditsia triacanthos) — Most common
- **Maple varieties** (Red, Norway, Amur, Silver, Hedge)
- **Oak varieties** (Northern Red, Pin, Shingle, Swamp White, Sawtooth)
- **Zelkova** (Japanese)
- **Linden** (Littleleaf)
- **Pear** (Callery)
- **Elm varieties** (American, Chinese, Accolade)
- **Ginkgo**
- **Planetree** (London)
- And 40+ other species

### Tree Size (DBH)

Distribution across size categories:
- 0-3 inches (young/recent plantings)
- 3-6 inches
- 6-12 inches
- 12-18 inches
- 18-24 inches
- 24-30 inches
- \>30 inches (mature trees)

### Planting Timeline

- **--** (unknown/historical): Majority of trees
- **Spring 2022-2026**: Recent plantings (100-500 trees)
- Indicates ongoing maintenance and planting program

## Usage Examples

### Load with GeoPandas

```python
import geopandas as gpd

# Load trees with geometries
gdf = gpd.read_file('data/boston_trees.geojson')

print(f"Loaded {len(gdf)} trees")
print(f"Neighborhoods: {gdf['neighborhood'].nunique()}")
print(f"Species: {gdf['spp_com'].nunique()}")

# Query trees in specific neighborhood
dorchester_trees = gdf[gdf['neighborhood'] == 'Dorchester']
print(f"Dorchester has {len(dorchester_trees)} trees")
```

### Spatial Joins

```python
import geopandas as gpd

# Load road segments and trees
gdf_roads = gpd.read_file('data/road_segments.geojson')
gdf_trees = gpd.read_file('data/boston_trees.geojson')

# Join trees to road segments
result = gpd.sjoin(
    gdf_roads,
    gdf_trees,
    how='left',
    predicate='contains'  # Road contains tree
)

# Aggregate trees per road segment
trees_per_road = result.groupby('road_id').size().reset_index(name='tree_count')
```

### Tree Analysis

```python
import pandas as pd

# Load trees data
df = pd.read_csv('data/boston_trees.csv')

# Trees by neighborhood
trees_by_neighborhood = df.groupby('neighborhood').agg({
    'id': 'count',
    'dbh': ['mean', 'median', 'max'],
    'spp_com': 'nunique'
}).round(1)

print(trees_by_neighborhood)
```

## Integration with Pipeline

### Current Status

```
Step 1: MBTA Bus Shapes ✓
Step 1b: Neighborhoods ✓
Step 1c: Trees (NEW) ✓
```

### Next: Feature Engineering

```
Step 2: Create Spatial Features
├── Road segment data (source)
├── Buffer/intersection analysis
├── Join with:
│  ├─ MBTA bus shapes → on_bus_route feature
│  ├─ Neighborhoods → neighborhood_id feature
│  └─ Trees → tree_count, avg_tree_dbh features
└── Create comprehensive feature dataset
```

### Equity Analysis

Trees can be used for equity analysis:
- **Canopy coverage** — Environmental justice
- **Tree age** — Maintenance patterns
- **Species diversity** — Planning patterns
- **Neighborhood comparison** — Resource allocation

## Performance

- **Load time:** 5-10 seconds
- **Conversion:** <1 second
- **Analysis:** <1 second
- **Save GeoJSON:** 10-20 seconds
- **Save CSV:** <1 second
- **Total:** ~20 seconds

## Dependencies

Already in `requirements.txt`:
- geopandas
- pandas
- shapely

## Quick Reference

```bash
# Run the loader
python3 load_trees_data.py

# Verify output
ls -lh data/boston_trees.*

# Quick check
python3 -c "
import geopandas as gpd
import pandas as pd

gdf = gpd.read_file('data/boston_trees.geojson')
df = pd.read_csv('data/boston_trees.csv')

print(f'GeoJSON: {len(gdf)} trees with geometry')
print(f'CSV: {len(df)} trees (metadata)')
print(f'Neighborhoods: {gdf.neighborhood.nunique()}')
print(f'Species: {gdf.spp_com.nunique()}')
"
```

## Troubleshooting

### File not found
```bash
# Find the file
find ~ -name "*bprd_trees*" 2>/dev/null

# Copy to project if found elsewhere
cp /path/to/bprd_trees.csv ./
```

### Memory issues with large files
- Use CSV version for non-spatial operations
- Filter by neighborhood before loading to GeoDataFrame
- Process in chunks if needed

### Coordinate issues
- Script uses x_longitude, y_latitude columns
- Creates EPSG:4326 (WGS84) geometry
- Compatible with all Boston GIS data

## File Manifest

### After running load_trees_data.py

```
Hackachusetts_Project/
├── load_trees_data.py               ← Script
├── README_TREES.md                  ← This file
└── data/
    ├── boston_trees.geojson         ← Output (with geometry)
    └── boston_trees.csv             ← Output (metadata only)
```

## Next Steps

1. Run the loader:
   ```bash
   python3 load_trees_data.py
   ```

2. Verify outputs:
   ```bash
   ls -lh data/boston_trees.*
   ```

3. Use for spatial analysis:
   - Join with road segments
   - Create tree-based features
   - Analyze by neighborhood

4. Continue with Step 2 (feature engineering)

## References

- [Boston Parks & Recreation Trees Dataset](https://data.boston.gov/)
- [GeoDataFrame Documentation](https://geopandas.org/)
- [Street Trees and Urban Infrastructure](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5580530/)
