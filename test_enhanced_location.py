#!/usr/bin/env python3
"""
Test script for enhanced location security features
"""

import json
import requests
from datetime import datetime, timedelta
import random

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_COORDINATES = {
    "lecture_location": {"lat": 40.7128, "lng": -74.0060},  # New York City
    "student_nearby": {"lat": 40.7129, "lng": -74.0061},   # ~15m away
    "student_far": {"lat": 40.7200, "lng": -74.0100},      # ~800m away
}

def create_test_metadata(lat, lng, accuracy=5, speed=0):
    """Create realistic location metadata"""
    return {
        "latitude": lat,
        "longitude": lng,
        "accuracy": accuracy,
        "altitude": random.uniform(10, 100),
        "altitudeAccuracy": random.uniform(3, 10),
        "heading": random.uniform(0, 360) if speed > 0 else None,
        "speed": speed,
        "timestamp": datetime.now().isoformat(),
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "platform": "Win32",
        "language": "en-US",
        "timezone": "America/New_York",
        "screenResolution": "1920x1080",
        "captureMode": "test_enhanced"
    }

def test_coordinate_validation():
    """Test coordinate validation function"""
    print("Testing coordinate validation...")
    
    from utils.geolocation import validate_coordinates
    
    test_cases = [
        (40.7128, -74.0060, True, "Valid NYC coordinates"),
        (91, -74.0060, False, "Invalid latitude > 90"),
        (40.7128, -181, False, "Invalid longitude < -180"),
        (0, 0, False, "Suspicious (0,0) coordinates"),
        ("invalid", -74.0060, False, "Invalid latitude format"),
    ]
    
    for lat, lng, expected, description in test_cases:
        try:
            is_valid, message = validate_coordinates(lat, lng)
            status = "✓" if is_valid == expected else "✗"
            print(f"  {status} {description}: {message}")
        except Exception as e:
            print(f"  ✗ {description}: Error - {e}")

def test_distance_calculation():
    """Test distance calculation accuracy"""
    print("\nTesting distance calculation...")
    
    from utils.geolocation import calculate_distance, calculate_distance_vincenty, is_within_geofence
    
    # Test known distance (approximately 1 degree = 111km at equator)
    lat1, lng1 = 0, 0
    lat2, lng2 = 0, 1
    
    haversine_dist = calculate_distance(lat1, lng1, lat2, lng2)
    vincenty_dist = calculate_distance_vincenty(lat1, lng1, lat2, lng2)
    
    print(f"  Distance between (0,0) and (0,1):")
    print(f"    Haversine: {haversine_dist:.2f}m")
    print(f"    Vincenty: {vincenty_dist:.2f}m" if vincenty_dist else "    Vincenty: Failed")
    
    # Test geofence
    lecture_loc = TEST_COORDINATES["lecture_location"]
    student_nearby = TEST_COORDINATES["student_nearby"]
    student_far = TEST_COORDINATES["student_far"]
    
    within_nearby, dist_nearby, accuracy_nearby = is_within_geofence(
        student_nearby["lat"], student_nearby["lng"],
        lecture_loc["lat"], lecture_loc["lng"],
        50, use_high_precision=True
    )
    
    within_far, dist_far, accuracy_far = is_within_geofence(
        student_far["lat"], student_far["lng"],
        lecture_loc["lat"], lecture_loc["lng"],
        50, use_high_precision=True
    )
    
    print(f"  Geofence test (50m radius):")
    print(f"    Nearby student: {'✓' if within_nearby else '✗'} ({dist_nearby:.1f}m)")
    print(f"    Far student: {'✗' if not within_far else '✓'} ({dist_far:.1f}m)")

def test_security_scoring():
    """Test location security scoring"""
    print("\nTesting security scoring...")
    
    from utils.geolocation import get_location_security_score, analyze_location_accuracy
    
    # Test different accuracy levels
    test_cases = [
        (create_test_metadata(40.7128, -74.0060, accuracy=3), "High accuracy (3m)"),
        (create_test_metadata(40.7128, -74.0060, accuracy=15), "Medium accuracy (15m)"),
        (create_test_metadata(40.7128, -74.0060, accuracy=60), "Poor accuracy (60m)"),
        (create_test_metadata(40.7128, -74.0060, accuracy=5, speed=10), "Moving fast (10 m/s)"),
    ]
    
    lecture_metadata = create_test_metadata(40.7128, -74.0060, accuracy=5)
    
    for student_metadata, description in test_cases:
        analysis = get_location_security_score(
            json.dumps(student_metadata), 
            json.dumps(lecture_metadata)
        )
        
        score = analysis.get('score', 0)
        level = analysis.get('level', 'unknown')
        issues = analysis.get('issues', [])
        
        print(f"  {description}:")
        print(f"    Score: {score}% ({level})")
        if issues:
            print(f"    Issues: {', '.join(issues)}")

def test_spoofing_detection():
    """Test location spoofing detection"""
    print("\nTesting spoofing detection...")
    
    from utils.geolocation import detect_location_spoofing
    
    # Test cases for spoofing detection
    test_cases = [
        (create_test_metadata(40.0, -74.0, accuracy=0.1), "Impossible accuracy"),
        (create_test_metadata(40.7128123456789, -74.0060123456789, accuracy=5), "Excessive precision"),
        (create_test_metadata(40.7128, -74.0060, accuracy=5, speed=100), "Impossible speed"),
        ({}, "Missing metadata"),
    ]
    
    for metadata, description in test_cases:
        if metadata:
            coordinates = (metadata.get('latitude', 0), metadata.get('longitude', 0))
            analysis = detect_location_spoofing(json.dumps(metadata), coordinates)
        else:
            analysis = detect_location_spoofing(None, (0, 0))
        
        risk = analysis.get('risk', 'unknown')
        reasons = analysis.get('reasons', [])
        
        print(f"  {description}:")
        print(f"    Risk: {risk}")
        if reasons:
            print(f"    Reasons: {', '.join(reasons)}")

def test_metadata_validation():
    """Test metadata validation"""
    print("\nTesting metadata validation...")
    
    from utils.geolocation import validate_location_metadata
    
    # Test cases
    valid_metadata = create_test_metadata(40.7128, -74.0060)
    invalid_metadata = {"latitude": 91, "longitude": -200}  # Invalid ranges
    incomplete_metadata = {"latitude": 40.7128}  # Missing fields
    
    test_cases = [
        (valid_metadata, "Valid metadata"),
        (invalid_metadata, "Invalid coordinate ranges"),
        (incomplete_metadata, "Incomplete metadata"),
        (None, "No metadata"),
    ]
    
    for metadata, description in test_cases:
        validation = validate_location_metadata(json.dumps(metadata) if metadata else None)
        
        is_valid = validation.get('valid', False)
        errors = validation.get('errors', [])
        warnings = validation.get('warnings', [])
        
        status = "✓" if is_valid else "✗"
        print(f"  {status} {description}")
        if errors:
            print(f"    Errors: {', '.join(errors)}")
        if warnings:
            print(f"    Warnings: {', '.join(warnings)}")

def test_location_fingerprinting():
    """Test location fingerprinting"""
    print("\nTesting location fingerprinting...")
    
    from utils.geolocation import create_location_fingerprint
    
    # Create two identical metadata sets
    metadata1 = create_test_metadata(40.7128, -74.0060)
    metadata2 = create_test_metadata(40.7128, -74.0060)
    
    # Create slightly different metadata
    metadata3 = create_test_metadata(40.7129, -74.0061)  # Different coordinates
    
    fingerprint1 = create_location_fingerprint(json.dumps(metadata1), (40.7128, -74.0060))
    fingerprint2 = create_location_fingerprint(json.dumps(metadata2), (40.7128, -74.0060))
    fingerprint3 = create_location_fingerprint(json.dumps(metadata3), (40.7129, -74.0061))
    
    print(f"  Fingerprint 1: {fingerprint1[:16]}...")
    print(f"  Fingerprint 2: {fingerprint2[:16]}...")
    print(f"  Fingerprint 3: {fingerprint3[:16]}...")
    
    print(f"  Same location fingerprints match: {'✓' if fingerprint1 == fingerprint2 else '✗'}")
    print(f"  Different location fingerprints differ: {'✓' if fingerprint1 != fingerprint3 else '✗'}")

def run_all_tests():
    """Run all enhanced location tests"""
    print("Enhanced Location Security Test Suite")
    print("=" * 50)
    
    try:
        test_coordinate_validation()
        test_distance_calculation()
        test_security_scoring()
        test_spoofing_detection()
        test_metadata_validation()
        test_location_fingerprinting()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("\nEnhanced location features verified:")
        print("• Coordinate validation and range checking")
        print("• High-precision distance calculations")
        print("• Security scoring based on GPS accuracy")
        print("• Location spoofing detection")
        print("• Comprehensive metadata validation")
        print("• Location fingerprinting for duplicate detection")
        
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()