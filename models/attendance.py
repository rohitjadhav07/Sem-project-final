from datetime import datetime, timedelta, timezone
from app import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    
    # Attendance status
    status = db.Column(db.Enum('present', 'absent', 'late', 'excused', 
                              name='attendance_status'), default='absent')
    
    # Enhanced location data when marked
    student_latitude = db.Column(db.Float(precision=10))
    student_longitude = db.Column(db.Float(precision=10))
    distance_from_lecture = db.Column(db.Float)  # meters
    location_accuracy = db.Column(db.String(50))  # Accuracy method used
    security_score = db.Column(db.Integer)  # Location security score (0-100)
    location_metadata = db.Column(db.Text)  # JSON string with location metadata
    
    # Security and audit fields
    client_ip = db.Column(db.String(45))  # IP address when marked
    verification_status = db.Column(db.String(20), default='verified')  # verified, suspicious, flagged
    
    # Timing
    marked_at = db.Column(db.DateTime)
    auto_marked = db.Column(db.Boolean, default=False)
    
    # Additional info
    notes = db.Column(db.Text)
    user_agent = db.Column(db.Text)  # Browser/device info
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('student_id', 'lecture_id', name='unique_student_lecture'),)
    
    def mark_present(self, latitude=None, longitude=None, distance=None, auto_marked=False):
        """Mark attendance as present"""
        self.status = 'present'
        self.marked_at = datetime.utcnow()
        self.student_latitude = latitude
        self.student_longitude = longitude
        self.distance_from_lecture = distance
        self.auto_marked = auto_marked
        
        # Check if marked late
        if self.lecture and self.marked_at > self.lecture.scheduled_start:
            late_threshold = self.lecture.scheduled_start + timedelta(
                minutes=self.lecture.attendance_window_end
            )
            if self.marked_at <= late_threshold:
                self.status = 'late'
    
    def mark_absent(self, notes=None):
        """Mark attendance as absent"""
        self.status = 'absent'
        self.notes = notes
        self.marked_at = datetime.utcnow()
    
    def mark_excused(self, notes=None):
        """Mark attendance as excused"""
        self.status = 'excused'
        self.notes = notes
        self.marked_at = datetime.utcnow()
    
    def is_valid_location(self):
        """Check if marked location is within geofence"""
        if not (self.student_latitude and self.student_longitude and self.lecture):
            return False
        
        return self.distance_from_lecture <= self.lecture.geofence_radius
    
    def get_status_color(self):
        """Get color code for status"""
        colors = {
            'present': 'green',
            'late': 'yellow',
            'absent': 'red',
            'excused': 'blue'
        }
        return colors.get(self.status, 'gray')
    
    def to_dict(self):
        """Convert attendance to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'student_username': self.student.username if self.student else None,
            'lecture_id': self.lecture_id,
            'lecture_title': self.lecture.title if self.lecture else None,
            'course_name': self.lecture.course.name if self.lecture and self.lecture.course else None,
            'course_code': self.lecture.course.code if self.lecture and self.lecture.course else None,
            'status': self.status,
            'status_color': self.get_status_color(),
            'marked_latitude': self.student_latitude,
            'marked_longitude': self.student_longitude,
            'distance_from_lecture': self.distance_from_lecture,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None,
            'auto_marked': self.auto_marked,
            'notes': self.notes,
            'is_valid_location': self.is_valid_location(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Attendance {self.student_id} -> {self.lecture_id}: {self.status}>'