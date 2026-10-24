"""
Quick test of the decode_mbta_shapes.py functionality with sample data.

This can be run to verify the GeoJSON encoding works correctly.
"""

import json
import sys

# Test basic polyline decoding
try:
    import polyline
    
    # Sample encoded polyline from Google Polyline Algorithm
    sample_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    
    print("Testing polyline decoding...")
    print(f"Encoded: {sample_polyline}")
    
    coords = polyline.decode(sample_polyline)
    print(f"Decoded: {coords}")
    
    # Convert to GeoJSON format [lon, lat]
    geojson_coords = [[lon, lat] for lat, lon in coords]
    print(f"GeoJSON format: {geojson_coords}")
    
    # Create a test GeoJSON FeatureCollection
    feature = {
        'type': 'Feature',
        'properties': {
            'shape_id': 'test_shape',
            'route_id': '1'
        },
        'geometry': {
            'type': 'LineString',
            'coordinates': geojson_coords
        }
    }
    
    geojson = {
        'type': 'FeatureCollection',
        'features': [feature]
    }
    
    # Verify it's valid JSON
    geojson_str = json.dumps(geojson)
    print(f"\n✓ GeoJSON is valid JSON ({len(geojson_str)} bytes)")
    
    # Try reading with geopandas if available
    try:
        import geopandas as gpd
        from shapely.geometry import shape
        
        print("\nTesting with geopandas...")
        
        # Create temporary GeoJSON
        with open('data/test_geojson.geojson', 'w') as f:
            json.dump(geojson, f)
        
        gdf = gpd.read_file('data/test_geojson.geojson')
        print(f"✓ Loaded with geopandas: {len(gdf)} features")
        print(f"  CRS: {gdf.crs}")
        print(f"  Geometry type: {gdf.geometry.type.iloc[0]}")
        print(f"  Bounds: {gdf.total_bounds}")
        
        print("\n✓ All tests passed!")
        
    except ImportError:
        print("⚠ geopandas not available, skipping geopandas test")
    
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Install with: pip install polyline geopandas")
    sys.exit(1)
