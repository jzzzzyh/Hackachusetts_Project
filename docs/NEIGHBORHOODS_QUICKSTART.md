# Boston Neighborhoods Quick Start

## TL;DR

Clean Boston neighborhood boundary data in 3 steps:

```bash
# 1. Install dependencies (if needed)
pip install geopandas pandas

# 2. Run the cleaner (searches for your GeoJSON file)
python3 clean_neighborhoods.py

# 3. Outputs created
ls -lh data/boston_neighborhoods.*
```

## What This Does

Takes your `boston_neighborhood_boundaries.geojson` and:
- ✓ Extracts name, neighborhood_id, sqmiles, geometry
- ✓ Saves as GeoJSON (with geometries for spatial joins)
- ✓ Saves as CSV (metadata only for quick lookups)
- ✓ Prints summary of both outputs

## Files Created

| File | Size | Use Case |
|------|------|----------|
| `data/boston_neighborhoods.geojson` | ~100+ MB | Spatial joins with road segments |
| `data/boston_neighborhoods.csv` | ~10 KB | Quick lookups without geometry |

## How to Use the Output

### GeoJSON (for spatial analysis)

```python
import geopandas as gpd

# Load neighborhoods with geometry
gdf_neighborhoods = gpd.read_file('data/boston_neighborhoods.geojson')

# Spatial join with road segments
gdf_roads_with_neighborhoods = gpd.sjoin(
    gdf_roads, 
    gdf_neighborhoods[['neighborhood_id', 'geometry']], 
    how='left', 
    predicate='intersects'
)
```

### CSV (for metadata)

```python
import pandas as pd

# Load neighborhood info quickly
df_neighborhoods = pd.read_csv('data/boston_neighborhoods.csv')

# Get neighborhood name by ID
neighborhood_name = df_neighborhoods[df_neighborhoods['neighborhood_id'] == 5]['name'].values[0]
```

## Testing Without Real Data

If you don't have the real GeoJSON file yet:

```bash
# Create sample data
python3 create_sample_neighborhoods.py

# Clean the sample
python3 clean_neighborhoods.py

# Now you have data/boston_neighborhoods.* ready to use
```

## File Search Locations

The script searches for your GeoJSON in this order:
1. Current directory (`.`)
2. `~/.kiro/crew/uploads/`
3. `~/Downloads/`
4. `~/Desktop/`
5. **Falls back to URL** if local file not found

## Expected Output

```
============================================================
Boston Neighborhood Boundaries Cleaner
============================================================

✓ Output directory: data

Loading neighborhoods...
✓ Loaded 26 features from local file

Cleaning data...
✓ Cleaned to 26 features with 4 columns

Saving outputs...
✓ Saved 26 features to GeoJSON
✓ Saved 26 rows to CSV

Output Summary
Shape: (26, 4)
CRS: EPSG:4326

First 3 rows:
         name  neighborhood_id  sqmiles
0   Downtown               1     1.95
1  Back Bay               2     3.28

============================================================
✓ Complete!
============================================================

Generated files:
  data/boston_neighborhoods.geojson
  data/boston_neighborhoods.csv
```

## Next Steps

Once neighborhoods are cleaned:

```bash
# 1. Verify the files
python3 -c "
import geopandas as gpd
import pandas as pd

gdf = gpd.read_file('data/boston_neighborhoods.geojson')
df = pd.read_csv('data/boston_neighborhoods.csv')

print(f'GeoJSON: {len(gdf)} neighborhoods')
print(f'CSV: {len(df)} neighborhoods')
"

# 2. Use for spatial joins with road segments (Step 2)
python3 << 'EOF'
import geopandas as gpd

# Load both datasets
roads = gpd.read_file('data/road_segments.geojson')  # Your road data
neighborhoods = gpd.read_file('data/boston_neighborhoods.geojson')

# Spatial join
result = gpd.sjoin(roads, neighborhoods, how='left', predicate='intersects')
print(f"Assigned neighborhoods to {len(result)} road segments")
EOF
```

## Troubleshooting

**Q: File not found error**
```bash
# Check if your GeoJSON is in one of the searched locations
ls -la boston_neighborhood_boundaries.geojson
ls -la ~/.kiro/crew/uploads/*neighborhood*
ls -la ~/Downloads/*neighborhood*

# Or copy it to project directory
cp /path/to/boston_neighborhood_boundaries.geojson .
```

**Q: Column not found error**
- Script handles missing columns gracefully
- Will print which columns are available
- Only keeps columns that exist in both the data and your requirements

**Q: Very large file (slow)**
- GeoJSON files are large (~100+ MB) but normal
- Use CSV version for non-spatial operations
- Script caches loaded data, so reloading is fast

## Script Details

### clean_neighborhoods.py
- **Purpose:** Clean and split neighborhood data
- **Input:** GeoJSON with 26 neighborhoods
- **Output:** GeoJSON + CSV in data/ folder
- **Time:** ~10 seconds
- **Lines:** 290 (with docstrings)

### create_sample_neighborhoods.py (Optional)
- **Purpose:** Create test data
- **Output:** `boston_neighborhood_boundaries.geojson` (3 neighborhoods)
- **Time:** <1 second
- **Lines:** 120

## One-Line Summary

Clean your Boston neighborhood GeoJSON into two formats (spatial GeoJSON + metadata CSV) ready for spatial analysis and equity checks.

---

**Ready?** Run: `python3 clean_neighborhoods.py`
