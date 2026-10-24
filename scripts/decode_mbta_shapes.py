"""
Decode MBTA bus shape polylines into GeoJSON.

This script reads the raw MBTA shapes with encoded polylines,
decodes them using the polyline library, and outputs a proper
GeoJSON FeatureCollection with LineString geometries.

Input: data/mbta_bus_shapes.json
Output: data/mbta_bus_shapes.geojson
"""

import json
import polyline
from pathlib import Path
from typing import List, Dict, Any


def load_shapes_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load shapes from JSON file.
    
    Args:
        input_path: Path to mbta_bus_shapes.json
        
    Returns:
        List of shape records with id, polyline, route_id
    """
    print(f"Loading shapes from {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        shapes = json.load(f)
    
    print(f"  Loaded {len(shapes)} shapes")
    return shapes


def decode_polyline(encoded: str) -> List[tuple]:
    """
    Decode an encoded polyline string to a list of (lat, lon) tuples.
    
    Args:
        encoded: Encoded polyline string from MBTA API
        
    Returns:
        List of (latitude, longitude) tuples
    """
    if not encoded:
        return []
    
    try:
        # polyline.decode returns list of (lat, lon) tuples
        coords = polyline.decode(encoded)
        return coords
    except Exception as e:
        print(f"  Warning: Failed to decode polyline: {e}")
        return []


def coords_to_geojson_linestring(coords: List[tuple]) -> Dict[str, Any]:
    """
    Convert list of (lat, lon) tuples to GeoJSON LineString coordinates.
    
    GeoJSON uses [lon, lat] order (not lat, lon).
    
    Args:
        coords: List of (latitude, longitude) tuples
        
    Returns:
        GeoJSON LineString geometry dict or None if empty
    """
    if not coords:
        return None
    
    # Convert (lat, lon) to [lon, lat] for GeoJSON
    geojson_coords = [[lon, lat] for lat, lon in coords]
    return {
        'type': 'LineString',
        'coordinates': geojson_coords
    }


def create_feature(shape_id: str, route_id: str, geometry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a GeoJSON Feature from shape data.
    
    Args:
        shape_id: Shape identifier
        route_id: Route identifier
        geometry: GeoJSON geometry dict
        
    Returns:
        GeoJSON Feature dict
    """
    return {
        'type': 'Feature',
        'properties': {
            'shape_id': shape_id,
            'route_id': route_id
        },
        'geometry': geometry
    }


def shapes_to_geojson(shapes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert shapes to GeoJSON FeatureCollection.
    
    Args:
        shapes: List of shape records with id, polyline, route_id
        
    Returns:
        GeoJSON FeatureCollection dict
    """
    print("Decoding polylines...")
    
    features = []
    valid_count = 0
    skipped_count = 0
    
    for i, shape in enumerate(shapes):
        if (i + 1) % 100 == 0:
            print(f"  Decoded {i + 1}/{len(shapes)} shapes...")
        
        shape_id = shape.get('id', '')
        route_id = shape.get('route_id', '')
        encoded_polyline = shape.get('polyline', '')
        
        if not encoded_polyline:
            skipped_count += 1
            continue
        
        # Decode polyline
        coords = decode_polyline(encoded_polyline)
        
        if not coords:
            skipped_count += 1
            continue
        
        # Create GeoJSON LineString
        geometry = coords_to_geojson_linestring(coords)
        
        if geometry:
            feature = create_feature(shape_id, route_id, geometry)
            features.append(feature)
            valid_count += 1
    
    print(f"  Valid shapes: {valid_count}, Skipped: {skipped_count}")
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    return geojson


def save_geojson(geojson: Dict[str, Any], output_path: str) -> None:
    """
    Save GeoJSON to file.
    
    Args:
        geojson: GeoJSON FeatureCollection dict
        output_path: Path to write GeoJSON file
    """
    print(f"Saving GeoJSON to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    
    print(f"  Saved {len(geojson['features'])} features")


def main():
    """Main entry point."""
    print("=" * 60)
    print("MBTA Shapes GeoJSON Decoder")
    print("=" * 60)
    
    # Load shapes
    shapes = load_shapes_json('data/mbta_bus_shapes.json')
    
    # Decode to GeoJSON
    geojson = shapes_to_geojson(shapes)
    
    # Save GeoJSON
    print("\n" + "=" * 60)
    print("Saving output...")
    print("=" * 60)
    
    save_geojson(geojson, 'data/mbta_bus_shapes.geojson')
    
    print("\n" + "=" * 60)
    print("✓ Complete!")
    print("=" * 60)
    print(f"\nOutput file: data/mbta_bus_shapes.geojson")
    print(f"Total features: {len(geojson['features'])}")


if __name__ == '__main__':
    main()
