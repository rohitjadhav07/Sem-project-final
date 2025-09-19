from datetime import datetime, timezone, timedelta
from extensions import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    is_active = db.Column(db.Boolean, default=True)
    grade = db.Column(db.String(5))  # A+, A, B+, etc.
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_student_course'),)
    
    def get_attendance_percentage(self):
        """Calculate attendance percentage for this enrollment"""
        from models.lecture import Lecture
        from models.attendance import Attendance
        
        total_lectures = Lecture.query.filter_by(
            course_id=self.course_id,
            is_active=True
        ).count()
        
        if total_lectures == 0:
            return 0
        
        attended_lectures = Attendance.query.join(Lecture).filter(
            Attendance.student_id == self.student_id,
            Lecture.course_id == self.course_id,
            Attendance.status == 'present'
        ).count()
        
        return round((attended_lectures / total_lectures) * 100, 2)
    
    def to_dict(self):
        """Convert enrollment to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'student_name': self.student.full_name if self.student else None,
            'course_name': self.course.name if self.course else None,
            'course_code': self.course.code if self.course else None,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'is_active': self.is_active,
            'grade': self.grade,
            'attendance_percentage': self.get_attendance_percentage()
        }
    
    def __repr__(self):
        return f'<Enrollment {self.student_id} -> {self.course_id}>'