"""
Enhanced Location Security System
Provides secure location setting and validation for lectures
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import math
import secrets

class LocationSecurityManager:
    """Manages secure location setting and validation"""
    
    # Security constants
    MIN_CONFIRMATION_INTERVAL = 30  # seconds between confirmations
    MAX_CONFIRMATION_INTERVAL = 300  # max seconds between confirmations
    REQUIRED_CONFIRMATIONS = 3  # number of confirmations needed
    MAX_LOCATION_DRIFT = 5  # max meters between confirmations
    MIN_ACCURACY_THRESHOLD = 15  # minimum GPS accuracy required
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, str]:
        """Validate GPS coordinates"""
        try:
            lat = float(latitude)
            lon = float(longitude)
            
            if not (-90 <= lat <= 90):
                return False, "Latitude must be between -90 and 90 degrees"
            
            if not (-180 <= lon <= 180):
                return False, "Longitude must be between -180 and 180 degrees"
            
            # Check for suspicious coordinates
            if lat == 0 and lon == 0:
                return False, "Invalid coordinates (0,0) detected"
            
            # Check for overly precise coordinates (potential spoofing)
            lat_str = str(lat)
            lon_str = str(lon)
            
            if '.' in lat_str and len(lat_str.split('.')[1]) > 8:
                return False, "Latitude precision suspiciously high"
            
            if '.' in lon_str and len(lon_str.split('.')[1]) > 8:
                return False, "Longitude precision suspiciously high"
            
            return True, "Valid coordinates"
            
        except (ValueError, TypeError):
            return False, "Invalid coordinate format"
    
    @staticmethod
    def validate_accuracy(accuracy: float, min_required: float = MIN_ACCURACY_THRESHOLD) -> Tuple[bool, str]:
        """Validate GPS accuracy"""
        if accuracy is None:
            return False, "GPS accuracy not provided"
        
        if accuracy > min_required:
            return False, f"GPS accuracy too low: ±{accuracy}m (required: <{min_required}m)"
        
        if accuracy < 1:
            return False, "GPS accuracy suspiciously high (potential spoofing)"
        
        return True, f"GPS accuracy acceptable: ±{accuracy}m"
    
    @staticmethod
    def create_location_hash(latitude: float, longitude: float, timestamp: datetime, salt: str = None) -> str:
        """Create secure hash of location data"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        location_string = f"{latitude:.8f}:{longitude:.8f}:{timestamp.isoformat()}:{salt}"
        return hashlib.sha256(location_string.encode()).hexdigest()
    
    @staticmethod
    def verify_location_integrity(latitude: float, longitude: float, timestamp: datetime, 
                                stored_hash: str, salt: str = None) -> bool:
        """Verify location data integrity"""
        if not stored_hash or not timestamp:
            return False
        
        expected_hash = LocationSecurityManager.create_location_hash(
            latitude, longitude, timestamp, salt
        )
        return stored_hash == expected_hash
    
    @staticmethod
    def analyze_location_metadata(metadata: Dict) -> Dict:
        """Analyze location metadata for security issues"""
        analysis = {
            'security_score': 100,
            'warnings': [],
            'is_suspicious': False,
            'reliability': 'high'
        }
        
        # Check accuracy
        accuracy = metadata.get('accuracy')
        if accuracy:
            if accuracy > 50:
                analysis['security_score'] -= 30
                analysis['warnings'].append('Poor GPS accuracy')
            elif accuracy > 20:
                analysis['security_score'] -= 15
                analysis['warnings'].append('Moderate GPS accuracy')
        
        # Check speed (movement during capture)
        speed = metadata.get('speed', 0)
        if speed and speed > 2:  # Moving faster than 2 m/s
            analysis['security_score'] -= 25
            analysis['warnings'].append('Device was moving during location capture')
        
        # Check altitude availability (indicates GPS quality)
        if not metadata.get('altitude'):
            analysis['security_score'] -= 10
            analysis['warnings'].append('No altitude data (lower GPS quality)')
        
        # Check timestamp freshness
        timestamp = metadata.get('timestamp')
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_seconds = (datetime.now().timestamp() - ts.timestamp())
                if age_seconds > 300:  # Older than 5 minutes
                    analysis['security_score'] -= 20
                    analysis['warnings'].append('Location data is stale')
            except:
                analysis['security_score'] -= 15
                analysis['warnings'].append('Invalid timestamp format')
        
        # Determine overall reliability
        if analysis['security_score'] >= 80:
            analysis['reliability'] = 'high'
        elif analysis['security_score'] >= 60:
            analysis['reliability'] = 'medium'
        else:
            analysis['reliability'] = 'low'
            analysis['is_suspicious'] = True
        
        return analysis

class LocationConfirmationSession:
    """Manages location confirmation sessions for secure location setting"""
    
    def __init__(self, lecture_id: int, teacher_id: int):
        self.lecture_id = lecture_id
        self.teacher_id = teacher_id
        self.confirmations = []
        self.session_id = secrets.token_hex(16)
        self.created_at = datetime.now()
        self.is_complete = False
        self.final_location = None
    
    def add_confirmation(self, latitude: float, longitude: float, accuracy: float, 
                        metadata: Dict = None) -> Tuple[bool, str, Dict]:
        """Add a location confirmation to the session"""
        
        # Validate coordinates
        is_valid, msg = LocationSecurityManager.validate_coordinates(latitude, longitude)
        if not is_valid:
            return False, f"Invalid coordinates: {msg}", {}
        
        # Validate accuracy
        is_accurate, acc_msg = LocationSecurityManager.validate_accuracy(accuracy)
        if not is_accurate:
            return False, f"Accuracy issue: {acc_msg}", {}
        
        # Check timing between confirmations
        now = datetime.now()
        if self.confirmations:
            last_confirmation = self.confirmations[-1]
            time_diff = (now - last_confirmation['timestamp']).total_seconds()
            
            if time_diff < LocationSecurityManager.MIN_CONFIRMATION_INTERVAL:
                return False, f"Please wait {LocationSecurityManager.MIN_CONFIRMATION_INTERVAL - int(time_diff)} more seconds before next confirmation", {}
            
            if time_diff > LocationSecurityManager.MAX_CONFIRMATION_INTERVAL:
                return False, "Confirmation session expired. Please start over.", {}
            
            # Check location consistency
            distance = LocationSecurityManager.calculate_distance(
                latitude, longitude,
                last_confirmation['latitude'], last_confirmation['longitude']
            )
            
            if distance > LocationSecurityManager.MAX_LOCATION_DRIFT:
                return False, f"Location drift too high: {distance:.1f}m (max: {LocationSecurityManager.MAX_LOCATION_DRIFT}m). Please stay in the same location.", {}
        
        # Analyze metadata
        security_analysis = {}
        if metadata:
            security_analysis = LocationSecurityManager.analyze_location_metadata(metadata)
            if security_analysis['is_suspicious']:
                return False, f"Suspicious location data detected: {', '.join(security_analysis['warnings'])}", security_analysis
        
        # Add confirmation
        confirmation = {
            'latitude': latitude,
            'longitude': longitude,
            'accuracy': accuracy,
            'metadata': metadata,
            'timestamp': now,
            'security_analysis': security_analysis
        }
        
        self.confirmations.append(confirmation)
        
        # Check if we have enough confirmations
        confirmations_needed = LocationSecurityManager.REQUIRED_CONFIRMATIONS - len(self.confirmations)
        
        if confirmations_needed <= 0:
            # Calculate final location (average of all confirmations)
            self.final_location = self._calculate_final_location()
            self.is_complete = True
            return True, "Location confirmed successfully!", {
                'confirmations_complete': True,
                'final_location': self.final_location,
                'session_summary': self._get_session_summary()
            }
        else:
            return True, f"Confirmation {len(self.confirmations)}/{LocationSecurityManager.REQUIRED_CONFIRMATIONS} recorded. {confirmations_needed} more needed.", {
                'confirmations_complete': False,
                'confirmations_remaining': confirmations_needed,
                'current_confirmation': len(self.confirmations)
            }
    
    def _calculate_final_location(self) -> Dict:
        """Calculate final location from all confirmations"""
        if not self.confirmations:
            return None
        
        # Calculate weighted average based on accuracy (better accuracy = higher weight)
        total_weight = 0
        weighted_lat = 0
        weighted_lon = 0
        
        for conf in self.confirmations:
            # Weight is inverse of accuracy (lower accuracy value = higher weight)
            weight = 1 / (conf['accuracy'] + 1)  # +1 to avoid division by zero
            weighted_lat += conf['latitude'] * weight
            weighted_lon += conf['longitude'] * weight
            total_weight += weight
        
        final_lat = weighted_lat / total_weight
        final_lon = weighted_lon / total_weight
        
        # Calculate average accuracy
        avg_accuracy = sum(c['accuracy'] for c in self.confirmations) / len(self.confirmations)
        
        # Calculate location consistency (standard deviation)
        lat_values = [c['latitude'] for c in self.confirmations]
        lon_values = [c['longitude'] for c in self.confirmations]
        
        lat_std = math.sqrt(sum((x - final_lat) ** 2 for x in lat_values) / len(lat_values))
        lon_std = math.sqrt(sum((x - final_lon) ** 2 for x in lon_values) / len(lon_values))
        
        # Convert to meters (approximate)
        lat_std_meters = lat_std * 111000  # 1 degree lat ≈ 111km
        lon_std_meters = lon_std * 111000 * math.cos(math.radians(final_lat))
        
        consistency_score = max(0, 100 - (lat_std_meters + lon_std_meters) * 10)
        
        return {
            'latitude': round(final_lat, 8),
            'longitude': round(final_lon, 8),
            'average_accuracy': round(avg_accuracy, 2),
            'consistency_score': round(consistency_score, 1),
            'confirmation_count': len(self.confirmations),
            'location_hash': LocationSecurityManager.create_location_hash(
                final_lat, final_lon, datetime.now()
            )
        }
    
    def _get_session_summary(self) -> Dict:
        """Get summary of the confirmation session"""
        if not self.confirmations:
            return {}
        
        accuracies = [c['accuracy'] for c in self.confirmations]
        security_scores = [c['security_analysis'].get('security_score', 0) 
                          for c in self.confirmations if c.get('security_analysis')]
        
        return {
            'session_id': self.session_id,
            'total_confirmations': len(self.confirmations),
            'session_duration': (datetime.now() - self.created_at).total_seconds(),
            'best_accuracy': min(accuracies),
            'worst_accuracy': max(accuracies),
            'average_accuracy': sum(accuracies) / len(accuracies),
            'average_security_score': sum(security_scores) / len(security_scores) if security_scores else 0,
            'all_confirmations_reliable': all(
                c['security_analysis'].get('reliability') == 'high' 
                for c in self.confirmations if c.get('security_analysis')
            )
        }
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return (datetime.now() - self.created_at).total_seconds() > 600  # 10 minutes

# Global session storage (in production, use Redis or database)
_active_sessions = {}

def get_or_create_confirmation_session(lecture_id: int, teacher_id: int) -> LocationConfirmationSession:
    """Get existing or create new confirmation session"""
    session_key = f"{lecture_id}_{teacher_id}"
    
    # Clean up expired sessions
    expired_keys = [k for k, v in _active_sessions.items() if v.is_expired()]
    for key in expired_keys:
        del _active_sessions[key]
    
    # Get or create session
    if session_key not in _active_sessions or _active_sessions[session_key].is_expired():
        _active_sessions[session_key] = LocationConfirmationSession(lecture_id, teacher_id)
    
    return _active_sessions[session_key]

def clear_confirmation_session(lecture_id: int, teacher_id: int):
    """Clear confirmation session"""
    session_key = f"{lecture_id}_{teacher_id}"
    if session_key in _active_sessions:
        del _active_sessions[session_key]