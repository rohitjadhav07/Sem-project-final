#!/usr/bin/env python3
"""
Test script for rectangular boundary functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.rectangular_geofence import (
    RectangularBoundary,
    point_in_rectangular_boundary,
    calculate_distance_to_boundary_edge,
    apply_tolerance_buffer,
    validate_gps_accuracy
)


def test_rectangular_boundary_creation():
    """Test creating a rectangular boundary"""
    print("\n" + "="*60)
    print("TEST 1: Rectangular Boundary Creation")
    print("="*60)
    
    # Define a classroom boundary (approximately 20m x 15m)
    ne = (40.7130, -74.0058)
    nw = (40.7130, -74.0062)
    se = (40.7128, -74.0058)
    sw = (40.7128, -74.0062)
    
    try:
        boundary = RectangularBoundary(ne, nw, se, sw)
        print("✅ Boundary created successfully")
        print(f"   Area: {boundary.calculate_area():.1f} m²")
        print(f"   Perimeter: {boundary.calculate_perimeter():.1f} m")
        print(f"   Center: {boundary.get_center()}")
        return boundary
    except Exception as e:
        print(f"❌ Failed to create boundary: {e}")
        return None


def test_point_in_polygon(boundary):
    """Test point-in-polygon validation"""
    print("\n" + "="*60)
    print("TEST 2: Point-in-Polygon Validation")
    print("="*60)
    
    test_points = [
        (40.7129, -74.0060, "Center (should be inside)"),
        (40.7131, -74.0060, "North of boundary (should be outside)"),
        (40.7127, -74.0060, "South of boundary (should be outside)"),
        (40.7129, -74.0057, "East of boundary (should be outside)"),
        (40.7129, -74.0063, "West of boundary (should be outside)"),
    ]
    
    for lat, lon, description in test_points:
        result = point_in_rectangular_boundary(lat, lon, boundary)
        status = "✅ INSIDE" if result['inside'] else "❌ OUTSIDE"
        print(f"{status} - {description}")
        print(f"   Distance to edge: {result['distance_to_edge']:.1f}m")
        print(f"   Nearest edge: {result['nearest_edge']}")
        print(f"   Method: {result['method']}")
        print()


def test_tolerance_buffer(boundary):
    """Test tolerance buffer application"""
    print("\n" + "="*60)
    print("TEST 3: Tolerance Buffer")
    print("="*60)
    
    # Point just outside boundary
    lat, lon = 40.7131, -74.0060
    
    # Test with good GPS (should accept with tolerance)
    result1 = apply_tolerance_buffer(lat, lon, boundary, tolerance_m=2.0, gps_accuracy=8.0)
    print(f"Point 1m outside with 8m GPS accuracy:")
    print(f"   Accepted: {result1['accepted']}")
    print(f"   Reason: {result1['reason']}")
    print()
    
    # Test with poor GPS (should reject)
    result2 = apply_tolerance_buffer(lat, lon, boundary, tolerance_m=2.0, gps_accuracy=25.0)
    print(f"Point 1m outside with 25m GPS accuracy:")
    print(f"   Accepted: {result2['accepted']}")
    print(f"   Reason: {result2['reason']}")
    print()


def test_gps_accuracy_validation(boundary):
    """Test GPS accuracy validation"""
    print("\n" + "="*60)
    print("TEST 4: GPS Accuracy Validation")
    print("="*60)
    
    # Point inside boundary
    lat, lon = 40.7129, -74.0060
    
    test_cases = [
        (8.0, 20, "Good GPS (8m) vs 20m threshold"),
        (25.0, 20, "Poor GPS (25m) vs 20m threshold"),
        (15.0, 10, "Medium GPS (15m) vs 10m threshold"),
    ]
    
    for gps_acc, threshold, description in test_cases:
        result = validate_gps_accuracy(gps_acc, threshold, lat, lon, boundary)
        status = "✅ ACCEPTABLE" if result['acceptable'] else "❌ REJECTED"
        print(f"{status} - {description}")
        print(f"   Reason: {result['reason']}")
        print()


def test_circular_to_rectangular_conversion():
    """Test converting circular geofence to rectangular"""
    print("\n" + "="*60)
    print("TEST 5: Circular to Rectangular Conversion")
    print("="*60)
    
    center_lat = 40.7129
    center_lon = -74.0060
    radius = 50  # 50 meters
    
    try:
        boundary = RectangularBoundary.from_circular(center_lat, center_lon, radius)
        print("✅ Conversion successful")
        print(f"   Original circular area: {3.14159 * radius**2:.1f} m²")
        print(f"   Rectangular area: {boundary.calculate_area():.1f} m²")
        print(f"   Corners:")
        print(f"     NE: {boundary.ne}")
        print(f"     NW: {boundary.nw}")
        print(f"     SE: {boundary.se}")
        print(f"     SW: {boundary.sw}")
        return boundary
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None


def test_json_serialization(boundary):
    """Test JSON serialization"""
    print("\n" + "="*60)
    print("TEST 6: JSON Serialization")
    print("="*60)
    
    try:
        # Convert to dict
        boundary_dict = boundary.to_dict()
        print("✅ Serialization successful")
        print(f"   Type: {boundary_dict['type']}")
        print(f"   Version: {boundary_dict['version']}")
        
        # Convert back from dict
        boundary2 = RectangularBoundary.from_dict(boundary_dict)
        print("✅ Deserialization successful")
        print(f"   Area matches: {abs(boundary.calculate_area() - boundary2.calculate_area()) < 1}")
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("RECTANGULAR BOUNDARY FUNCTIONALITY TESTS")
    print("="*70)
    
    # Test 1: Create boundary
    boundary = test_rectangular_boundary_creation()
    if not boundary:
        print("\n❌ Cannot continue tests without valid boundary")
        return
    
    # Test 2: Point-in-polygon
    test_point_in_polygon(boundary)
    
    # Test 3: Tolerance buffer
    test_tolerance_buffer(boundary)
    
    # Test 4: GPS accuracy
    test_gps_accuracy_validation(boundary)
    
    # Test 5: Circular conversion
    converted_boundary = test_circular_to_rectangular_conversion()
    
    # Test 6: JSON serialization
    if converted_boundary:
        test_json_serialization(converted_boundary)
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()
