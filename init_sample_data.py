"""
Initialize sample data for demo purposes
"""
from extensions import db
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.enrollment import Enrollment
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def init_sample_data():
    """Initialize sample data for demo"""
    try:
        # Create tables
        db.create_all()
        
        # Check if data already exists
        if User.query.first():
            return  # Data already exists
        
        # Create sample admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='System',
            last_name='Administrator',
            role='admin',
            employee_id='EMP001'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample teacher
        teacher = User(
            username='teacher1',
            email='teacher@example.com',
            first_name='John',
            last_name='Smith',
            role='teacher',
            employee_id='EMP002'
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        
        # Create sample student
        student = User(
            username='student1',
            email='student@example.com',
            first_name='Alice',
            last_name='Johnson',
            role='student',
            student_id='STU001'
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Commit users first
        db.session.commit()
        
        # Create sample course
        course = Course(
            name='Computer Science 101',
            code='CS101',
            description='Introduction to Computer Science',
            teacher_id=teacher.id,
            location_name='Room 101',
            latitude=19.0760,  # Mumbai coordinates
            longitude=72.8777,
            geofence_radius=50
        )
        db.session.add(course)
        db.session.commit()
        
        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id
        )
        db.session.add(enrollment)
        
        # Create sample lecture
        lecture_time = datetime.now(IST) + timedelta(hours=1)
        lecture = Lecture(
            title='Introduction to Programming',
            course_id=course.id,
            teacher_id=teacher.id,
            scheduled_start=lecture_time,
            scheduled_end=lecture_time + timedelta(hours=2),
            location_name='Room 101',
            latitude=19.0760,
            longitude=72.8777,
            geofence_radius=50,
            is_active=True
        )
        db.session.add(lecture)
        
        db.session.commit()
        print("✅ Sample data initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        db.session.rollback()