"""
Create sample Boston neighborhoods GeoJSON for testing clean_neighborhoods.py

This script creates a minimal valid GeoJSON file with 3 sample neighborhoods
for testing the cleaning workflow when the real file is not available.

Output:
  boston_neighborhood_boundaries.geojson - Sample GeoJSON with 3 neighborhoods
"""

import json
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from pathlib import Path


def create_sample_geojson():
    """Create sample GeoJSON with 3 Boston neighborhoods."""
    
    # Sample neighborhood geometries (simplified coordinates for Boston)
    neighborhoods = [
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
                "coordinates": [[
                    [-71.060, 42.358], [-71.056, 42.358], 
                    [-71.056, 42.362], [-71.060, 42.362], 
                    [-71.060, 42.358]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "OBJECTID": 2,
                "name": "Back Bay",
                "acres": 2100,
                "neighborhood_id": 2,
                "sqmiles": 3.28
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-71.080, 42.345], [-71.070, 42.345],
                    [-71.070, 42.360], [-71.080, 42.360],
                    [-71.080, 42.345]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "OBJECTID": 3,
                "name": "Cambridge",
                "acres": 3800,
                "neighborhood_id": 3,
                "sqmiles": 5.94
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[
                        [-71.100, 42.370], [-71.090, 42.370],
                        [-71.090, 42.380], [-71.100, 42.380],
                        [-71.100, 42.370]
                    ]]],
                    [[[
                        [-71.085, 42.360], [-71.075, 42.360],
                        [-71.075, 42.368], [-71.085, 42.368],
                        [-71.085, 42.360]
                    ]]]
                ]
            }
        }
    ]
    
    geojson = {
        "type": "FeatureCollection",
        "features": neighborhoods
    }
    
    return geojson


def save_sample_geojson(output_path: str = 'boston_neighborhood_boundaries.geojson'):
    """Create and save sample GeoJSON file."""
    
    print("Creating sample Boston neighborhoods GeoJSON...")
    print(f"Output: {output_path}")
    
    geojson = create_sample_geojson()
    
    # Save as GeoJSON
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"✓ Created {output_path}")
    
    # Load with geopandas and display info
    gdf = gpd.read_file(output_path)
    print(f"\n✓ Sample GeoJSON loaded with geopandas")
    print(f"  Features: {len(gdf)}")
    print(f"  Columns: {gdf.columns.tolist()}")
    print(f"  CRS: {gdf.crs}")
    print(f"\nFirst row:")
    print(gdf[['name', 'neighborhood_id', 'sqmiles']].head(1).to_string())
    
    return output_path


if __name__ == '__main__':
    save_sample_geojson()
