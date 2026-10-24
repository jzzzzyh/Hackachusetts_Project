"""
Load and analyze Boston BPRD trees data.

This script:
1. Loads the BPRD trees CSV file
2. Converts to GeoDataFrame with proper geometry
3. Analyzes tree distribution by neighborhood
4. Saves processed data for spatial analysis
5. Prints summary statistics

Input:
  bprd_trees.csv (from Boston Parks & Recreation Department)

Output:
  data/boston_trees.geojson   - GeoDataFrame with geometries
  data/boston_trees.csv       - Cleaned CSV data
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Tuple


# File locations to search
SEARCH_PATHS = [
    Path('/Users/zhouyuhai/.kiro/crew/uploads/d6f3810c9f6a45909107cd6cb75fb19a_bprd_trees.csv'),
    Path('/Users/zhouyuhai/Downloads/bprd_trees.csv'),
    Path('bprd_trees.csv'),
    Path('./data/bprd_trees.csv'),
]


def find_trees_file() -> Path:
    """
    Find the BPRD trees CSV file in known locations.
    
    Returns:
        Path to the trees CSV file
        
    Raises:
        FileNotFoundError: If file not found in any location
    """
    for path in SEARCH_PATHS:
        if path.exists():
            return path
    
    raise FileNotFoundError(
        f"Could not find bprd_trees.csv in any of these locations:\n"
        f"{chr(10).join(str(p) for p in SEARCH_PATHS)}"
    )


def load_trees_data(csv_path: Path) -> pd.DataFrame:
    """
    Load trees CSV data.
    
    Args:
        csv_path: Path to bprd_trees.csv
        
    Returns:
        DataFrame with trees data
    """
    print(f"Loading trees data from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} trees")
    print(f"  Columns: {len(df.columns)}")
    return df


def convert_to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Convert trees DataFrame to GeoDataFrame with point geometries.
    
    Args:
        df: Trees DataFrame with x_longitude, y_latitude columns
        
    Returns:
        GeoDataFrame with Point geometries
    """
    print("\nConverting to GeoDataFrame...")
    
    # Validate coordinate columns exist
    if 'x_longitude' not in df.columns or 'y_latitude' not in df.columns:
        raise ValueError("Missing coordinate columns: x_longitude, y_latitude")
    
    # Create GeoDataFrame from coordinates
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['x_longitude'], df['y_latitude']),
        crs='EPSG:4326'  # WGS84
    )
    
    print(f"✓ Converted to GeoDataFrame")
    print(f"  Features: {len(gdf)}")
    print(f"  CRS: {gdf.crs}")
    print(f"  Geometry type: {gdf.geometry.type.unique()}")
    
    return gdf


def analyze_trees(gdf: gpd.GeoDataFrame) -> None:
    """
    Print summary statistics about trees data.
    
    Args:
        gdf: Trees GeoDataFrame
    """
    print("\n" + "=" * 60)
    print("Trees Data Summary")
    print("=" * 60)
    
    # Overall stats
    print(f"\nTotal trees: {len(gdf)}")
    print(f"Columns: {gdf.columns.tolist()}")
    
    # Neighborhoods
    if 'neighborhood' in gdf.columns:
        print(f"\nNeighborhoods with trees: {gdf['neighborhood'].nunique()}")
        print("\nTrees by neighborhood:")
        neighborhood_counts = gdf['neighborhood'].value_counts()
        for neighborhood, count in neighborhood_counts.head(10).items():
            print(f"  {neighborhood}: {count} trees")
    
    # Species
    if 'spp_com' in gdf.columns:
        print(f"\nUnique species: {gdf['spp_com'].nunique()}")
        print("\nTop 10 most common species:")
        species_counts = gdf['spp_com'].value_counts()
        for species, count in species_counts.head(10).items():
            print(f"  {species}: {count} trees")
    
    # DBH (Diameter at Breast Height)
    if 'dbh' in gdf.columns:
        print(f"\nTree size (DBH) statistics:")
        print(f"  Min DBH: {gdf['dbh'].min():.1f} inches")
        print(f"  Max DBH: {gdf['dbh'].max():.1f} inches")
        print(f"  Mean DBH: {gdf['dbh'].mean():.1f} inches")
        print(f"  Median DBH: {gdf['dbh'].median():.1f} inches")
    
    # Planting dates
    if 'date_plant' in gdf.columns:
        print(f"\nPlanting dates:")
        date_counts = gdf['date_plant'].value_counts()
        for date, count in date_counts.head(5).items():
            print(f"  {date if date != '--' else 'Unknown/Historical'}: {count} trees")
    
    # Spatial bounds
    print(f"\nSpatial bounds:")
    bounds = gdf.total_bounds
    print(f"  Longitude: {bounds[0]:.4f} to {bounds[2]:.4f}")
    print(f"  Latitude: {bounds[1]:.4f} to {bounds[3]:.4f}")


def save_trees_data(gdf: gpd.GeoDataFrame, output_dir: Path) -> Tuple[str, str]:
    """
    Save trees data to both GeoJSON and CSV formats.
    
    Args:
        gdf: Trees GeoDataFrame
        output_dir: Directory to save files
        
    Returns:
        Tuple of (geojson_path, csv_path)
    """
    output_dir.mkdir(exist_ok=True)
    
    # Save as GeoJSON (with geometries)
    geojson_path = output_dir / 'boston_trees.geojson'
    print(f"\nSaving GeoJSON to {geojson_path}...")
    gdf.to_file(geojson_path, driver='GeoJSON')
    print(f"✓ Saved {len(gdf)} trees to GeoJSON")
    
    # Save as CSV (without geometry)
    csv_path = output_dir / 'boston_trees.csv'
    print(f"\nSaving CSV to {csv_path}...")
    
    # Select non-geometry columns for CSV
    df_csv = gdf.drop(columns=['geometry'])
    df_csv.to_csv(csv_path, index=False)
    print(f"✓ Saved {len(df_csv)} trees to CSV")
    
    return str(geojson_path), str(csv_path)


def print_sample(gdf: gpd.GeoDataFrame) -> None:
    """
    Print sample of data (first 3 rows).
    
    Args:
        gdf: Trees GeoDataFrame
    """
    print("\nFirst 3 trees:")
    print("-" * 80)
    
    # Display columns
    display_cols = [
        'id', 'spp_com', 'neighborhood', 'address', 'dbh', 
        'date_plant', 'x_longitude', 'y_latitude'
    ]
    available_cols = [col for col in display_cols if col in gdf.columns]
    
    print(gdf[available_cols].head(3).to_string())


def main():
    """Main entry point."""
    print("=" * 60)
    print("Boston BPRD Trees Data Loader")
    print("=" * 60)
    
    try:
        # Find and load data
        csv_path = find_trees_file()
        df = load_trees_data(csv_path)
        
        # Convert to GeoDataFrame
        gdf = convert_to_geodataframe(df)
        
        # Analyze data
        analyze_trees(gdf)
        
        # Print sample
        print_sample(gdf)
        
        # Save outputs
        print("\n" + "=" * 60)
        print("Saving data...")
        print("=" * 60)
        
        output_dir = Path('data')
        geojson_path, csv_path = save_trees_data(gdf, output_dir)
        
        # Final summary
        print("\n" + "=" * 60)
        print("✓ Complete!")
        print("=" * 60)
        print(f"\nGenerated files:")
        print(f"  {geojson_path}")
        print(f"  {csv_path}")
        print(f"\nNext steps:")
        print(f"  • Use {geojson_path} for spatial joins with road segments")
        print(f"  • Use {csv_path} for tree analysis and statistics")
        print(f"  • Join with neighborhoods for equity analysis")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
