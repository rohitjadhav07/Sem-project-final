from datetime import datetime, timezone, timedelta
from app import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credits = db.Column(db.Integer, default=3)
    semester = db.Column(db.String(20))
    academic_year = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic',
                                cascade='all, delete-orphan')
    lectures = db.relationship('Lecture', backref='course', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def get_enrolled_students(self):
        """Get all enrolled students"""
        from models.user import User
        return User.query.join(Enrollment).filter(
            Enrollment.course_id == self.id,
            Enrollment.is_active == True
        ).all()
    
    def get_total_lectures(self):
        """Get total number of lectures"""
        return self.lectures.filter_by(is_active=True).count()
    
    def get_enrollment_count(self):
        """Get number of enrolled students"""
        return self.enrollments.filter_by(is_active=True).count()
    
    def to_dict(self):
        """Convert course to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else None,
            'credits': self.credits,
            'semester': self.semester,
            'academic_year': self.academic_year,
            'is_active': self.is_active,
            'enrollment_count': self.get_enrollment_count(),
            'total_lectures': self.get_total_lectures(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'