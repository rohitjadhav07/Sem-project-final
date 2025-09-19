import math
import json
from datetime import datetime, timedelta

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using Haversine formula
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters (more precise value)
    r = 6371008.8
    
    return c * r

def calculate_distance_vincenty(lat1, lon1, lat2, lon2):
    """
    More accurate distance calculation using Vincenty's formula
    Better for short distances and high precision requirements
    """
    from math import radians, sin, cos, sqrt, atan2, fabs, atan, tan
    
    # WGS84 ellipsoid parameters
    a = 6378137.0  # semi-major axis
    f = 1/298.257223563  # flattening
    b = (1 - f) * a  # semi-minor axis
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    L = lon2 - lon1
    U1 = atan((1 - f) * tan(lat1))
    U2 = atan((1 - f) * tan(lat2))
    
    sinU1, cosU1 = sin(U1), cos(U1)
    sinU2, cosU2 = sin(U2), cos(U2)
    
    lambda_val = L
    lambda_prev = 2 * math.pi
    iter_limit = 100
    
    while fabs(lambda_val - lambda_prev) > 1e-12 and iter_limit > 0:
        sin_lambda = sin(lambda_val)
        cos_lambda = cos(lambda_val)
        
        sin_sigma = sqrt((cosU2 * sin_lambda) ** 2 + 
                        (cosU1 * sinU2 - sinU1 * cosU2 * cos_lambda) ** 2)
        
        if sin_sigma == 0:
            return 0  # coincident points
            
        cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cos_lambda
        sigma = atan2(sin_sigma, cos_sigma)
        
        sin_alpha = cosU1 * cosU2 * sin_lambda / sin_sigma
        cos2_alpha = 1 - sin_alpha ** 2
        
        cos_2sigma_m = cos_sigma - 2 * sinU1 * sinU2 / cos2_alpha if cos2_alpha != 0 else 0
        
        C = f / 16 * cos2_alpha * (4 + f * (4 - 3 * cos2_alpha))
        
        lambda_prev = lambda_val
        lambda_val = L + (1 - C) * f * sin_alpha * (
            sigma + C * sin_sigma * (
                cos_2sigma_m + C * cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
            )
        )
        
        iter_limit -= 1
    
    if iter_limit == 0:
        return None  # formula failed to converge
    
    u2 = cos2_alpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    
    delta_sigma = B * sin_sigma * (
        cos_2sigma_m + B / 4 * (
            cos_sigma * (-1 + 2 * cos_2sigma_m ** 2) -
            B / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos_2sigma_m ** 2)
        )
    )
    
    s = b * A * (sigma - delta_sigma)
    return s

def is_within_geofence(student_lat, student_lon, lecture_lat, lecture_lon, radius, use_high_precision=True):
    """
    Check if student is within the geofence of the lecture location
    
    Args:
        student_lat: Student's latitude
        student_lon: Student's longitude  
        lecture_lat: Lecture location latitude
        lecture_lon: Lecture location longitude
        radius: Geofence radius in meters
        use_high_precision: Use Vincenty formula for higher accuracy
    
    Returns:
        tuple: (is_within, distance, accuracy_info)
    """
    try:
        if use_high_precision:
            distance = calculate_distance_vincenty(student_lat, student_lon, lecture_lat, lecture_lon)
            if distance is None:
                # Fallback to Haversine if Vincenty fails
                distance = calculate_distance(student_lat, student_lon, lecture_lat, lecture_lon)
                accuracy_info = "haversine_fallback"
            else:
                accuracy_info = "vincenty_high_precision"
        else:
            distance = calculate_distance(student_lat, student_lon, lecture_lat, lecture_lon)
            accuracy_info = "haversine_standard"
        
        is_within = distance <= radius
        
        return is_within, distance, accuracy_info
        
    except Exception as e:
        # Fallback to basic calculation
        distance = calculate_distance(student_lat, student_lon, lecture_lat, lecture_lon)
        is_within = distance <= radius
        return is_within, distance, f"error_fallback: {str(e)}"

def validate_coordinates(lat, lon):
    """
    Validate GPS coordinates
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        lat = float(lat)
        lon = float(lon)
        
        if lat < -90 or lat > 90:
            return False, "Latitude must be between -90 and 90 degrees"
            
        if lon < -180 or lon > 180:
            return False, "Longitude must be between -180 and 180 degrees"
            
        # Check for suspicious coordinates
        if lat == 0 and lon == 0:
            return False, "Invalid coordinates (0,0) detected"
            
        # Check for coordinates that are too precise (potential spoofing)
        lat_str = str(lat)
        lon_str = str(lon)
        
        if '.' in lat_str and len(lat_str.split('.')[1]) > 8:
            return False, "Latitude precision too high (potential spoofing)"
            
        if '.' in lon_str and len(lon_str.split('.')[1]) > 8:
            return False, "Longitude precision too high (potential spoofing)"
            
        return True, "Valid coordinates"
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

def analyze_location_accuracy(metadata_json):
    """
    Analyze location metadata for accuracy and reliability
    
    Returns:
        dict: Analysis results
    """
    try:
        if not metadata_json:
            return {"status": "no_metadata", "reliability": "unknown"}
            
        metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
        
        accuracy = metadata.get('accuracy', 999)
        altitude = metadata.get('altitude')
        speed = metadata.get('speed', 0)
        timestamp = metadata.get('timestamp')
        
        analysis = {
            "accuracy_meters": accuracy,
            "has_altitude": altitude is not None,
            "speed_kmh": speed * 3.6 if speed else 0,
            "timestamp": timestamp
        }
        
        # Determine reliability
        if accuracy <= 5:
            analysis["reliability"] = "excellent"
            analysis["status"] = "high_precision"
        elif accuracy <= 10:
            analysis["reliability"] = "very_good"
            analysis["status"] = "good_precision"
        elif accuracy <= 20:
            analysis["reliability"] = "good"
            analysis["status"] = "acceptable_precision"
        elif accuracy <= 50:
            analysis["reliability"] = "fair"
            analysis["status"] = "low_precision"
        else:
            analysis["reliability"] = "poor"
            analysis["status"] = "very_low_precision"
            
        # Check for potential issues
        if speed and speed > 5:  # Moving faster than 5 m/s (18 km/h)
            analysis["warning"] = "high_speed_detected"
            
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_seconds = (datetime.now().timestamp() - ts.timestamp())
                if age_seconds > 300:  # Older than 5 minutes
                    analysis["warning"] = "stale_location_data"
            except:
                pass
                
        return analysis
        
    except Exception as e:
        return {"status": "error", "error": str(e), "reliability": "unknown"}

def get_location_security_score(student_metadata, lecture_metadata):
    """
    Calculate a security score based on location data comparison
    Higher score = more trustworthy
    
    Returns:
        dict: Security analysis
    """
    try:
        student_analysis = analyze_location_accuracy(student_metadata)
        lecture_analysis = analyze_location_accuracy(lecture_metadata)
        
        score = 100  # Start with perfect score
        issues = []
        
        # Accuracy comparison
        student_acc = student_analysis.get('accuracy_meters', 999)
        lecture_acc = lecture_analysis.get('accuracy_meters', 999)
        
        if student_acc > 50:
            score -= 30
            issues.append("poor_student_accuracy")
            
        if lecture_acc > 20:
            score -= 20
            issues.append("poor_lecture_accuracy")
            
        # Speed check
        if student_analysis.get('speed_kmh', 0) > 10:
            score -= 25
            issues.append("student_moving_fast")
            
        # Timestamp freshness
        if 'warning' in student_analysis:
            if student_analysis['warning'] == 'stale_location_data':
                score -= 15
                issues.append("stale_location")
            elif student_analysis['warning'] == 'high_speed_detected':
                score -= 20
                issues.append("high_speed")
                
        return {
            "score": max(0, score),
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "issues": issues,
            "student_analysis": student_analysis,
            "lecture_analysis": lecture_analysis
        }
        
    except Exception as e:
        return {
            "score": 0,
            "level": "error",
            "error": str(e),
            "issues": ["analysis_failed"]
        }

def detect_location_spoofing(metadata_json, coordinates):
    """
    Detect potential location spoofing attempts
    
    Returns:
        dict: Spoofing analysis
    """
    try:
        if not metadata_json:
            return {"risk": "unknown", "reasons": ["no_metadata"]}
        
        metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
        lat, lon = coordinates
        
        risk_factors = []
        risk_score = 0
        
        # Check for perfect coordinates (suspicious)
        if lat == int(lat) and lon == int(lon):
            risk_factors.append("perfect_integer_coordinates")
            risk_score += 30
        
        # Check for excessive precision
        lat_str = str(lat)
        lon_str = str(lon)
        if '.' in lat_str and len(lat_str.split('.')[1]) > 6:
            risk_factors.append("excessive_precision")
            risk_score += 20
        
        # Check for impossible accuracy
        accuracy = metadata.get('accuracy', 999)
        if accuracy < 1:
            risk_factors.append("impossible_accuracy")
            risk_score += 40
        
        # Check for missing expected fields
        expected_fields = ['accuracy', 'timestamp', 'userAgent']
        missing_fields = [f for f in expected_fields if f not in metadata]
        if missing_fields:
            risk_factors.append(f"missing_fields: {', '.join(missing_fields)}")
            risk_score += len(missing_fields) * 10
        
        # Check for suspicious speed
        speed = metadata.get('speed', 0)
        if speed and speed > 50:  # > 180 km/h
            risk_factors.append("impossible_speed")
            risk_score += 35
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        elif risk_score > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk": risk_level,
            "score": risk_score,
            "reasons": risk_factors,
            "metadata_analysis": metadata
        }
        
    except Exception as e:
        return {
            "risk": "error",
            "error": str(e),
            "reasons": ["analysis_failed"]
        }

def create_location_fingerprint(metadata_json, coordinates):
    """
    Create a unique fingerprint for location data
    Used for detecting duplicate or suspicious submissions
    
    Returns:
        str: Location fingerprint hash
    """
    try:
        import hashlib
        
        if not metadata_json:
            return None
        
        metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
        lat, lon = coordinates
        
        # Create fingerprint from key data points
        fingerprint_data = {
            "coordinates": f"{lat:.6f},{lon:.6f}",
            "accuracy": metadata.get('accuracy'),
            "userAgent": metadata.get('userAgent', ''),
            "platform": metadata.get('platform', ''),
            "timezone": metadata.get('timezone', ''),
            "timestamp_rounded": metadata.get('timestamp', '')[:16] if metadata.get('timestamp') else ''  # Round to minute
        }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
    except Exception as e:
        return None

def validate_location_metadata(metadata_json):
    """
    Validate location metadata for completeness and consistency
    
    Returns:
        dict: Validation results
    """
    try:
        if not metadata_json:
            return {"valid": False, "errors": ["no_metadata"]}
        
        metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ['latitude', 'longitude', 'accuracy', 'timestamp']
        for field in required_fields:
            if field not in metadata:
                errors.append(f"missing_required_field: {field}")
        
        # Validate accuracy
        accuracy = metadata.get('accuracy')
        if accuracy is not None:
            if accuracy < 0:
                errors.append("negative_accuracy")
            elif accuracy > 1000:
                warnings.append("very_poor_accuracy")
        
        # Validate timestamp
        timestamp = metadata.get('timestamp')
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_seconds = abs((datetime.now() - ts.replace(tzinfo=None)).total_seconds())
                if age_seconds > 3600:  # Older than 1 hour
                    warnings.append("old_timestamp")
            except:
                errors.append("invalid_timestamp_format")
        
        # Validate coordinates
        lat = metadata.get('latitude')
        lon = metadata.get('longitude')
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90):
                errors.append("invalid_latitude_range")
            if not (-180 <= lon <= 180):
                errors.append("invalid_longitude_range")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"validation_error: {str(e)}"]
        }