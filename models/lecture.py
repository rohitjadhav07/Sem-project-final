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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='lecture', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    def is_attendance_window_open(self):
        """Check if attendance window is currently open"""
        now = datetime.now(IST)
        start_window = self.scheduled_start + timedelta(minutes=self.attendance_window_start)
        end_window = self.scheduled_start + timedelta(minutes=self.attendance_window_end)
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
        self.location_set_at = datetime.utcnow()
        
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
    
    def to_dict(self):
        """Convert lecture to dictionary"""
        return {
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
    
    def __repr__(self):
        return f'<Lecture {self.title} - {self.course.code if self.course else "Unknown"}>'