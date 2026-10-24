"""
Clean and consolidate Boston neighborhood boundaries from GeoJSON.

This script:
1. Loads the Boston neighborhood boundaries GeoJSON
2. Keeps only essential columns: name, neighborhood_id, sqmiles, geometry
3. Saves two output files:
   - data/boston_neighborhoods.geojson (for spatial joins)
   - data/boston_neighborhoods.csv (metadata only, no geometry)
4. Validates output and prints summary

Input:
  boston_neighborhood_boundaries.geojson (26 features with MultiPolygon/Polygon geometries)

Output:
  data/boston_neighborhoods.geojson  - GeoJSON with geometry
  data/boston_neighborhoods.csv      - CSV with metadata only
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path


# URL fallback if local file not found
GEOJSON_URL = (
    "https://s3.amazonaws.com/og-production-open-data-bostonma-892364687672/"
    "resources/e5849875-a6f6-4c9c-9d8a-5048b0fbd03e/"
    "boston_neighborhood_boundaries.geojson"
)

# Columns to keep
REQUIRED_COLUMNS = ['name', 'neighborhood_id', 'sqmiles', 'geometry']
OUTPUT_CSV_COLUMNS = ['name', 'neighborhood_id', 'sqmiles']


def find_geojson_file(search_dirs=None) -> str:
    """
    Search for boston_neighborhood_boundaries.geojson in multiple directories.
    
    Args:
        search_dirs: List of directories to search (default: current dir, home, uploads)
        
    Returns:
        Path to GeoJSON file if found, else None
    """
    if search_dirs is None:
        search_dirs = [
            '.',
            Path.home() / '.kiro' / 'crew' / 'uploads',
            Path.home() / 'Downloads',
            Path.home() / 'Desktop'
        ]
    
    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.exists():
            continue
            
        for pattern in ['*boston*neighborhood*', '*neighborhoods*']:
            matches = list(search_path.glob(pattern))
            geojson_files = [f for f in matches if f.suffix == '.geojson']
            if geojson_files:
                return str(geojson_files[0])
    
    return None


def load_neighborhoods() -> gpd.GeoDataFrame:
    """
    Load Boston neighborhood boundaries from GeoJSON.
    
    Tries local file first, falls back to URL if not found.
    
    Returns:
        GeoDataFrame with neighborhood boundaries
        
    Raises:
        Exception: If file cannot be loaded from either source
    """
    # Try local file first
    local_file = find_geojson_file()
    
    if local_file and Path(local_file).exists():
        print(f"Loading from local file: {local_file}")
        try:
            gdf = gpd.read_file(local_file)
            print(f"✓ Loaded {len(gdf)} features from local file")
            return gdf
        except Exception as e:
            print(f"⚠ Failed to load local file: {e}")
    
    # Fall back to URL
    print(f"Loading from URL: {GEOJSON_URL[:80]}...")
    try:
        gdf = gpd.read_file(GEOJSON_URL)
        print(f"✓ Loaded {len(gdf)} features from URL")
        return gdf
    except Exception as e:
        raise Exception(f"Failed to load GeoJSON from both local and URL: {e}")


def clean_neighborhoods(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Clean and prepare neighborhood GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame with neighborhood data
        
    Returns:
        Cleaned GeoDataFrame with only required columns
    """
    print("\nCleaning neighborhoods data...")
    
    # Check which columns exist
    available_columns = gdf.columns.tolist()
    print(f"  Available columns: {available_columns}")
    
    # Select columns that exist and are in our requirements
    columns_to_keep = [col for col in REQUIRED_COLUMNS if col in available_columns]
    
    if 'geometry' not in columns_to_keep and 'geometry' in gdf.columns:
        columns_to_keep.append('geometry')
    
    print(f"  Keeping columns: {columns_to_keep}")
    
    # Select columns
    gdf_clean = gdf[columns_to_keep].copy()
    
    # Validate required columns exist
    missing = [col for col in ['name', 'neighborhood_id', 'sqmiles'] 
               if col not in gdf_clean.columns]
    if missing:
        print(f"⚠ Warning: Missing columns {missing}")
    
    print(f"✓ Cleaned to {len(gdf_clean)} features with {len(gdf_clean.columns)} columns")
    
    return gdf_clean


def save_geojson(gdf: gpd.GeoDataFrame, output_path: str) -> None:
    """
    Save GeoDataFrame to GeoJSON file.
    
    Args:
        gdf: GeoDataFrame to save
        output_path: Path to output GeoJSON file
    """
    print(f"\nSaving GeoJSON to {output_path}...")
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"✓ Saved {len(gdf)} features to GeoJSON")


def save_csv(gdf: gpd.GeoDataFrame, output_path: str) -> None:
    """
    Save neighborhood metadata to CSV (without geometry).
    
    Args:
        gdf: GeoDataFrame to save
        output_path: Path to output CSV file
    """
    print(f"\nSaving CSV to {output_path}...")
    
    # Select only non-geometry columns
    csv_columns = [col for col in OUTPUT_CSV_COLUMNS if col in gdf.columns]
    df_csv = gdf[csv_columns].copy()
    
    # Save as CSV
    df_csv.to_csv(output_path, index=False)
    print(f"✓ Saved {len(df_csv)} rows to CSV with columns: {csv_columns}")


def print_sample(gdf: gpd.GeoDataFrame, name: str) -> None:
    """
    Print shape and first 3 rows of GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame to print
        name: Name for printing (e.g., "GeoJSON", "CSV")
    """
    print(f"\n{name} Summary")
    print("-" * 60)
    print(f"Shape: {gdf.shape}")
    print(f"Columns: {gdf.columns.tolist()}")
    print(f"CRS: {gdf.crs}")
    
    if len(gdf) > 0:
        print(f"\nFirst 3 rows:")
        # For display, drop geometry column if present
        display_cols = [col for col in gdf.columns if col != 'geometry']
        if display_cols:
            print(gdf[display_cols].head(3).to_string())


def main():
    """Main entry point."""
    print("=" * 60)
    print("Boston Neighborhood Boundaries Cleaner")
    print("=" * 60)
    
    # Create output directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    print(f"\n✓ Output directory: {data_dir}")
    
    # Load neighborhoods
    print("\n" + "=" * 60)
    print("Loading neighborhoods...")
    print("=" * 60)
    gdf = load_neighborhoods()
    
    # Clean data
    print("\n" + "=" * 60)
    print("Cleaning data...")
    print("=" * 60)
    gdf_clean = clean_neighborhoods(gdf)
    
    # Save outputs
    print("\n" + "=" * 60)
    print("Saving outputs...")
    print("=" * 60)
    
    geojson_path = str(data_dir / 'boston_neighborhoods.geojson')
    csv_path = str(data_dir / 'boston_neighborhoods.csv')
    
    save_geojson(gdf_clean, geojson_path)
    save_csv(gdf_clean, csv_path)
    
    # Print summaries
    print("\n" + "=" * 60)
    print("Output Summary")
    print("=" * 60)
    
    # Reload to show what was saved
    gdf_geojson = gpd.read_file(geojson_path)
    df_csv = pd.read_csv(csv_path)
    
    print_sample(gdf_geojson, "GeoJSON")
    print_sample(df_csv, "CSV")
    
    # Final summary
    print("\n" + "=" * 60)
    print("✓ Complete!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  {geojson_path}")
    print(f"  {csv_path}")
    print(f"\nNext steps:")
    print(f"  • Use {geojson_path} for spatial joins with road segments")
    print(f"  • Use {csv_path} for neighborhood metadata lookups")


if __name__ == '__main__':
    main()
