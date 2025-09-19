from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from app import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student', name='user_roles'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    student_id = db.Column(db.String(20), unique=True, nullable=True)  # For students
    employee_id = db.Column(db.String(20), unique=True, nullable=True)  # For teachers/admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    last_login = db.Column(db.DateTime)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', 
                                foreign_keys='Enrollment.student_id')
    taught_courses = db.relationship('Course', backref='teacher', lazy='dynamic',
                                   foreign_keys='Course.teacher_id')
    lectures = db.relationship('Lecture', backref='teacher', lazy='dynamic',
                             foreign_keys='Lecture.teacher_id')
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic',
                                foreign_keys='Attendance.student_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_teacher(self):
        """Check if user is teacher"""
        return self.role == 'teacher'
    
    def is_student(self):
        """Check if user is student"""
        return self.role == 'student'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'phone': self.phone,
            'student_id': self.student_id,
            'employee_id': self.employee_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'