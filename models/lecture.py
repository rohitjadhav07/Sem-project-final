from datetime import datetime, timedelta, timezone
from extensions import db
from utils.geolocation import is_within_geofence

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class Lecture(db.Model):
    __tablename__ = 'lectures'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Enhanced Location data with security
    latitude = db.Column(db.Float(precision=10))
    longitude = db.Column(db.Float(precision=10))
    location_name = db.Column(db.String(200))
    geofence_radius = db.Column(db.Integer, default=50)  # meters
    
    # Rectangular boundary support
    geofence_type = db.Column(db.String(20), default='circular')  # 'circular' or 'rectangular'
    boundary_coordinates = db.Column(db.Text)  # JSON: {"ne": [lat, lon], "nw": [...], "se": [...], "sw": [...]}
    boundary_area_sqm = db.Column(db.Float)  # Area in square meters
    boundary_perimeter_m = db.Column(db.Float)  # Perimeter in meters
    boundary_center_lat = db.Column(db.Float(precision=10))  # Calculated center point
    boundary_center_lon = db.Column(db.Float(precision=10))
    gps_accuracy_threshold = db.Column(db.Integer, default=20)  # meters (10, 15, or 20)
    boundary_tolerance_m = db.Column(db.Float, default=2.0)  # Edge tolerance in meters
    boundary_validation_method = db.Column(db.String(50))  # 'point_in_polygon', 'circular', etc.
    boundary_created_at = db.Column(db.DateTime)
    boundary_last_modified = db.Column(db.DateTime)
    
    # Location security and precision
    location_accuracy = db.Column(db.Float)  # GPS accuracy in meters when location was set
    location_metadata = db.Column(db.Text)  # JSON string with device/GPS metadata
    location_set_at = db.Column(db.DateTime)  # When location was captured
    location_locked = db.Column(db.Boolean, default=False)  # Prevent location changes once set
    location_hash = db.Column(db.String(64))  # Hash of location data for integrity
    location_device_info = db.Column(db.Text)  # Device info when location was set
    location_ip_address = db.Column(db.String(45))  # IP address when location was set
    location_verification_status = db.Column(db.String(20), default='pending')  # pending, verified, suspicious
    location_confirmation_count = db.Column(db.Integer, default=0)  # Number of times location was confirmed
    location_last_verified = db.Column(db.DateTime)  # Last time location was verified
    
    # Location validation settings
    min_accuracy_required = db.Column(db.Integer, default=10)  # Max acceptable GPS accuracy in meters
    allow_location_updates = db.Column(db.Boolean, default=False)  # Allow teacher to update location after lock
    location_verification_required = db.Column(db.Boolean, default=True)  # Require location verification
    require_location_confirmation = db.Column(db.Boolean, default=True)  # Require teacher to confirm location multiple times
    
    # Timing
    scheduled_start = db.Column(db.DateTime, nullable=False)
    scheduled_end = db.Column(db.DateTime, nullable=False)
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.Enum('scheduled', 'active', 'completed', 'cancelled', 
                              name='lecture_status'), default='scheduled')
    is_active = db.Column(db.Boolean, default=True)
    
    # Attendance settings
    attendance_window_start = db.Column(db.Integer, default=-15)  # minutes before start
    attendance_window_end = db.Column(db.Integer, default=15)    # minutes after start
    auto_mark_attendance = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    
    # Relationships
    attendances = db.relationship('Attendance', backref='lecture', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    def is_attendance_window_open(self):
        """Check if attendance window is currently open"""
        now = datetime.now(IST)
        
        # Use default values if not set - more lenient for testing
        window_start_minutes = getattr(self, 'attendance_window_start', -30)  # 30 minutes before
        window_end_minutes = getattr(self, 'attendance_window_end', 60)       # 60 minutes after start
        
        # Handle timezone-aware vs timezone-naive datetime comparison
        scheduled_start = self.scheduled_start
        if scheduled_start.tzinfo is None:
            # If stored datetime is naive, assume it's in IST
            scheduled_start = scheduled_start.replace(tzinfo=IST)
        elif now.tzinfo is None:
            # If current time is naive, make it timezone-aware
            now = now.replace(tzinfo=IST)
        
        start_window = scheduled_start + timedelta(minutes=window_start_minutes)
        end_window = scheduled_start + timedelta(minutes=window_end_minutes)
        
        return start_window <= now <= end_window
    
    def get_attendance_stats(self):
        """Get attendance statistics for this lecture"""
        total_enrolled = self.course.get_enrollment_count()
        present_count = self.attendances.filter_by(status='present').count()
        absent_count = self.attendances.filter_by(status='absent').count()
        late_count = self.attendances.filter_by(status='late').count()
        
        return {
            'total_enrolled': total_enrolled,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'attendance_rate': round((present_count / total_enrolled * 100), 2) if total_enrolled > 0 else 0
        }
    
    def start_lecture(self):
        """Start the lecture"""
        self.status = 'active'
        self.actual_start = datetime.now(IST)
        db.session.commit()
    
    def end_lecture(self):
        """End the lecture"""
        self.status = 'completed'
        self.actual_end = datetime.now(IST)
        db.session.commit()
    
    def is_within_geofence(self, student_lat, student_lon):
        """Check if student location is within lecture geofence"""
        within_fence, distance = is_within_geofence(
            student_lat, student_lon,
            self.latitude, self.longitude,
            self.geofence_radius
        )
        return within_fence
    
    def set_secure_location(self, latitude, longitude, accuracy, metadata=None, device_info=None):
        """Set location with security measures"""
        import hashlib
        import json
        from datetime import datetime
        
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Invalid coordinates")
        
        # Check if location is already locked
        if self.location_locked and not self.allow_location_updates:
            raise ValueError("Location is locked and cannot be updated")
        
        # Check accuracy requirements
        if accuracy and accuracy > self.min_accuracy_required:
            raise ValueError(f"GPS accuracy too low: {accuracy}m (required: <{self.min_accuracy_required}m)")
        
        # Set location data
        self.latitude = round(latitude, 8)  # Precision to ~1mm
        self.longitude = round(longitude, 8)
        self.location_accuracy = accuracy
        self.location_set_at = datetime.now(IST)
        
        # Store metadata
        if metadata:
            self.location_metadata = json.dumps(metadata) if isinstance(metadata, dict) else metadata
        
        if device_info:
            self.location_device_info = json.dumps(device_info) if isinstance(device_info, dict) else device_info
        
        # Create location hash for integrity verification
        location_string = f"{self.latitude}:{self.longitude}:{self.location_set_at.isoformat()}"
        self.location_hash = hashlib.sha256(location_string.encode()).hexdigest()
        
        # Lock location after setting (security measure)
        self.location_locked = True
        
        db.session.commit()
    
    def verify_location_integrity(self):
        """Verify that location data hasn't been tampered with"""
        import hashlib
        
        if not self.location_hash or not self.location_set_at:
            return False
        
        location_string = f"{self.latitude}:{self.longitude}:{self.location_set_at.isoformat()}"
        expected_hash = hashlib.sha256(location_string.encode()).hexdigest()
        
        return self.location_hash == expected_hash
    
    def get_location_security_info(self):
        """Get location security information"""
        import json
        
        info = {
            'is_locked': self.location_locked,
            'accuracy': self.location_accuracy,
            'set_at': self.location_set_at.isoformat() if self.location_set_at else None,
            'integrity_verified': self.verify_location_integrity(),
            'precision_level': 'high' if self.location_accuracy and self.location_accuracy <= 5 else 
                             'medium' if self.location_accuracy and self.location_accuracy <= 15 else 'low'
        }
        
        # Parse metadata if available
        if self.location_metadata:
            try:
                metadata = json.loads(self.location_metadata)
                info['metadata'] = metadata
            except:
                pass
        
        return info
    
    def set_rectangular_boundary(self, ne_corner, nw_corner, se_corner, sw_corner, 
                                gps_threshold=20, tolerance=2.0):
        """
        Set rectangular boundary for lecture
        
        Args:
            ne_corner: (lat, lon) tuple for northeast corner
            nw_corner: (lat, lon) tuple for northwest corner
            se_corner: (lat, lon) tuple for southeast corner
            sw_corner: (lat, lon) tuple for southwest corner
            gps_threshold: GPS accuracy threshold in meters
            tolerance: Edge tolerance in meters
        """
        import json
        from utils.rectangular_geofence import RectangularBoundary
        
        # Create and validate boundary
        boundary = RectangularBoundary(ne_corner, nw_corner, se_corner, sw_corner)
        
        # Store boundary data
        self.geofence_type = 'rectangular'
        self.boundary_coordinates = json.dumps(boundary.to_dict())
        self.boundary_area_sqm = boundary.calculate_area()
        self.boundary_perimeter_m = boundary.calculate_perimeter()
        
        center = boundary.get_center()
        self.boundary_center_lat = center[0]
        self.boundary_center_lon = center[1]
        
        # Also update center point for backward compatibility
        self.latitude = center[0]
        self.longitude = center[1]
        
        # Set thresholds
        self.gps_accuracy_threshold = gps_threshold
        self.boundary_tolerance_m = tolerance
        
        # Set metadata
        self.boundary_validation_method = 'point_in_polygon'
        self.boundary_created_at = datetime.now(IST)
        self.boundary_last_modified = datetime.now(IST)
        
        db.session.commit()
    
    def get_boundary(self):
        """
        Get boundary object (rectangular or circular)
        
        Returns:
            RectangularBoundary object or None
        """
        if self.geofence_type == 'rectangular' and self.boundary_coordinates:
            import json
            from utils.rectangular_geofence import RectangularBoundary
            
            try:
                data = json.loads(self.boundary_coordinates)
                return RectangularBoundary.from_dict(data)
            except Exception as e:
                print(f"Error loading boundary: {e}")
                return None
        
        return None
    
    def convert_circular_to_rectangular(self):
        """
        Convert circular geofence to rectangular approximation
        
        Returns:
            Dictionary with suggested boundary
        """
        from utils.rectangular_geofence import RectangularBoundary
        
        if not self.latitude or not self.longitude or not self.geofence_radius:
            raise ValueError("Circular geofence not properly configured")
        
        # Create rectangular approximation
        boundary = RectangularBoundary.from_circular(
            self.latitude,
            self.longitude,
            self.geofence_radius
        )
        
        return {
            'suggested_boundary': boundary.to_dict(),
            'original_circular': {
                'center': (self.latitude, self.longitude),
                'radius': self.geofence_radius,
                'area_sqm': 3.14159 * (self.geofence_radius ** 2)
            }
        }
    
    def get_geofence_type(self):
        """Get geofence type"""
        return self.geofence_type or 'circular'
    
    def is_within_geofence_enhanced(self, student_lat, student_lon, gps_accuracy=None):
        """
        Enhanced geofence check supporting both circular and rectangular boundaries
        
        Args:
            student_lat: Student latitude
            student_lon: Student longitude
            gps_accuracy: GPS accuracy in meters (optional)
        
        Returns:
            Dictionary with validation results
        """
        try:
            if self.geofence_type == 'rectangular':
                # Use rectangular boundary validation
                from utils.rectangular_geofence import (
                    point_in_rectangular_boundary,
                    apply_tolerance_buffer,
                    validate_gps_accuracy
                )
                
                boundary = self.get_boundary()
                if not boundary:
                    # Fallback to circular
                    return self._validate_circular(student_lat, student_lon)
                
                # Validate GPS accuracy if provided
                if gps_accuracy:
                    gps_result = validate_gps_accuracy(
                        gps_accuracy,
                        self.gps_accuracy_threshold or 20,
                        student_lat,
                        student_lon,
                        boundary
                    )
                    
                    if not gps_result['acceptable'] and gps_result['reason'].startswith('gps_accuracy_exceeds'):
                        return {
                            'within_geofence': False,
                            'method': 'rectangular',
                            'reason': 'gps_accuracy_too_low',
                            'gps_accuracy': gps_accuracy,
                            'threshold': self.gps_accuracy_threshold,
                            'details': gps_result
                        }
                
                # Apply tolerance buffer
                tolerance_result = apply_tolerance_buffer(
                    student_lat,
                    student_lon,
                    boundary,
                    self.boundary_tolerance_m or 2.0,
                    gps_accuracy or 999
                )
                
                return {
                    'within_geofence': tolerance_result['accepted'],
                    'method': 'rectangular',
                    'reason': tolerance_result['reason'],
                    'distance_to_edge': tolerance_result.get('distance_to_edge', 0),
                    'tolerance_applied': tolerance_result.get('applied_tolerance', False),
                    'details': tolerance_result
                }
                
            else:
                # Use circular validation
                return self._validate_circular(student_lat, student_lon)
                
        except Exception as e:
            # Fallback to circular validation
            print(f"Error in enhanced geofence check: {e}")
            return self._validate_circular(student_lat, student_lon)
    
    def _validate_circular(self, student_lat, student_lon):
        """Fallback circular validation"""
        within_fence, distance = is_within_geofence(
            student_lat, student_lon,
            self.latitude, self.longitude,
            self.geofence_radius
        )
        
        return {
            'within_geofence': within_fence,
            'method': 'circular',
            'distance': distance,
            'radius': self.geofence_radius
        }
    
    def to_dict(self):
        """Convert lecture to dictionary"""
        base_dict = {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'course_code': self.course.code if self.course else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else None,
            'title': self.title,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_name': self.location_name,
            'geofence_radius': self.geofence_radius,
            'geofence_type': self.geofence_type,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'status': self.status,
            'is_active': self.is_active,
            'attendance_window_start': self.attendance_window_start,
            'attendance_window_end': self.attendance_window_end,
            'auto_mark_attendance': self.auto_mark_attendance,
            'is_attendance_window_open': self.is_attendance_window_open(),
            'attendance_stats': self.get_attendance_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add rectangular boundary info if applicable
        if self.geofence_type == 'rectangular' and self.boundary_coordinates:
            import json
            try:
                base_dict['boundary'] = json.loads(self.boundary_coordinates)
                base_dict['boundary_area_sqm'] = self.boundary_area_sqm
                base_dict['boundary_perimeter_m'] = self.boundary_perimeter_m
                base_dict['gps_accuracy_threshold'] = self.gps_accuracy_threshold
                base_dict['boundary_tolerance_m'] = self.boundary_tolerance_m
            except:
                pass
        
        return base_dict
    
    def __repr__(self):
        return f'<Lecture {self.title} - {self.course.code if self.course else "Unknown"}>'