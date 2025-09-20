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
        
        # Try to restore from backup first
        from database_manager import db_manager
        if db_manager.restore_database_from_json(db.session):
            print("✅ Data restored from backup")
            return
        
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
        
        # Create multiple sample lectures for testing
        
        # Lecture 1: Currently active (attendance window open)
        current_time = datetime.now(IST)
        lecture1 = Lecture(
            title='Introduction to Programming',
            course_id=course.id,
            teacher_id=teacher.id,
            scheduled_start=current_time - timedelta(minutes=5),  # Started 5 minutes ago
            scheduled_end=current_time + timedelta(hours=1, minutes=55),  # Ends in ~2 hours
            location_name='Room 101, Computer Lab',
            latitude=19.0760,
            longitude=72.8777,
            geofence_radius=50,
            is_active=True,
            status='active',
            attendance_window_start=-15,  # 15 minutes before start
            attendance_window_end=30,     # 30 minutes after start
            location_locked=True,
            location_accuracy=5.0,
            location_set_at=current_time - timedelta(hours=1)
        )
        db.session.add(lecture1)
        
        # Lecture 2: Upcoming lecture (window opens soon)
        lecture2 = Lecture(
            title='Data Structures and Algorithms',
            course_id=course.id,
            teacher_id=teacher.id,
            scheduled_start=current_time + timedelta(hours=2),
            scheduled_end=current_time + timedelta(hours=4),
            location_name='Room 102, Theory Class',
            latitude=19.0765,  # Slightly different location
            longitude=72.8780,
            geofence_radius=40,
            is_active=True,
            status='scheduled',
            attendance_window_start=-10,
            attendance_window_end=20,
            location_locked=True,
            location_accuracy=3.0,
            location_set_at=current_time - timedelta(minutes=30)
        )
        db.session.add(lecture2)
        
        # Lecture 3: Another active lecture for testing
        lecture3 = Lecture(
            title='Web Development Basics',
            course_id=course.id,
            teacher_id=teacher.id,
            scheduled_start=current_time - timedelta(minutes=10),
            scheduled_end=current_time + timedelta(hours=1, minutes=50),
            location_name='Room 103, Lab Session',
            latitude=19.0755,
            longitude=72.8785,
            geofence_radius=60,
            is_active=True,
            status='active',
            attendance_window_start=-20,
            attendance_window_end=25,
            location_locked=True,
            location_accuracy=4.0,
            location_set_at=current_time - timedelta(hours=2)
        )
        db.session.add(lecture3)
        
        db.session.commit()
        
        # Backup the data for persistence
        db_manager.backup_database_to_json(db.session)
        
        print("✅ Sample data initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        db.session.rollback()