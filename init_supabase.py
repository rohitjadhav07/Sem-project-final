"""
Initialize Supabase database with tables and sample data
"""
from extensions import db
from supabase_config import supabase_config
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.attendance import Attendance
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def create_supabase_tables():
    """Create all tables in Supabase"""
    try:
        print("🔄 Creating Supabase tables...")
        db.create_all()
        print("✅ Supabase tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating Supabase tables: {e}")
        return False

def init_supabase_data():
    """Initialize Supabase with sample data"""
    try:
        # Check if Supabase is configured
        if not supabase_config.is_configured():
            print("⚠️ Supabase not configured, using fallback database")
            return init_fallback_data()
        
        print("🔄 Initializing Supabase data...")
        
        # Check if data already exists
        if User.query.first():
            print("✅ Supabase data already exists")
            return True
        
        # Create sample admin user
        admin = User(
            username='admin',
            email='admin@geoattendance.com',
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
            email='teacher@geoattendance.com',
            first_name='Dr. John',
            last_name='Smith',
            role='teacher',
            employee_id='EMP002'
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        
        # Create sample students
        students = [
            {
                'username': 'student1',
                'email': 'alice@student.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'student_id': 'STU001'
            },
            {
                'username': 'student2',
                'email': 'bob@student.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'student_id': 'STU002'
            },
            {
                'username': 'student3',
                'email': 'carol@student.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'student_id': 'STU003'
            }
        ]
        
        student_objects = []
        for student_data in students:
            student = User(
                username=student_data['username'],
                email=student_data['email'],
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                role='student',
                student_id=student_data['student_id']
            )
            student.set_password('student123')
            db.session.add(student)
            student_objects.append(student)
        
        # Commit users first
        db.session.commit()
        
        # Create sample courses
        courses = [
            {
                'name': 'Computer Science 101',
                'code': 'CS101',
                'description': 'Introduction to Computer Science and Programming',
                'location_name': 'Computer Lab - Room 101',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'geofence_radius': 50
            },
            {
                'name': 'Data Structures & Algorithms',
                'code': 'CS201',
                'description': 'Advanced programming concepts and algorithms',
                'location_name': 'Theory Class - Room 201',
                'latitude': 19.0765,
                'longitude': 72.8780,
                'geofence_radius': 40
            },
            {
                'name': 'Web Development',
                'code': 'CS301',
                'description': 'Modern web development with HTML, CSS, JavaScript',
                'location_name': 'Web Lab - Room 301',
                'latitude': 19.0755,
                'longitude': 72.8785,
                'geofence_radius': 60
            }
        ]
        
        course_objects = []
        for course_data in courses:
            course = Course(
                name=course_data['name'],
                code=course_data['code'],
                description=course_data['description'],
                teacher_id=teacher.id,
                location_name=course_data['location_name'],
                latitude=course_data['latitude'],
                longitude=course_data['longitude'],
                geofence_radius=course_data['geofence_radius']
            )
            db.session.add(course)
            course_objects.append(course)
        
        db.session.commit()
        
        # Enroll students in courses
        for student in student_objects:
            for course in course_objects:
                enrollment = Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    enrollment_date=datetime.now(IST),
                    is_active=True
                )
                db.session.add(enrollment)
        
        # Create sample lectures
        current_time = datetime.now(IST)
        
        lectures = [
            {
                'title': 'Introduction to Programming',
                'course_id': course_objects[0].id,
                'scheduled_start': current_time - timedelta(minutes=5),
                'scheduled_end': current_time + timedelta(hours=1, minutes=55),
                'status': 'active',
                'attendance_window_start': -15,
                'attendance_window_end': 30
            },
            {
                'title': 'Variables and Data Types',
                'course_id': course_objects[0].id,
                'scheduled_start': current_time + timedelta(hours=2),
                'scheduled_end': current_time + timedelta(hours=4),
                'status': 'scheduled',
                'attendance_window_start': -10,
                'attendance_window_end': 20
            },
            {
                'title': 'Arrays and Linked Lists',
                'course_id': course_objects[1].id,
                'scheduled_start': current_time - timedelta(minutes=10),
                'scheduled_end': current_time + timedelta(hours=1, minutes=50),
                'status': 'active',
                'attendance_window_start': -20,
                'attendance_window_end': 25
            },
            {
                'title': 'HTML and CSS Basics',
                'course_id': course_objects[2].id,
                'scheduled_start': current_time + timedelta(hours=1),
                'scheduled_end': current_time + timedelta(hours=3),
                'status': 'scheduled',
                'attendance_window_start': -15,
                'attendance_window_end': 30
            }
        ]
        
        for i, lecture_data in enumerate(lectures):
            course = course_objects[i % len(course_objects)]
            lecture = Lecture(
                title=lecture_data['title'],
                course_id=lecture_data['course_id'],
                teacher_id=teacher.id,
                scheduled_start=lecture_data['scheduled_start'],
                scheduled_end=lecture_data['scheduled_end'],
                location_name=course.location_name,
                latitude=course.latitude,
                longitude=course.longitude,
                geofence_radius=course.geofence_radius,
                is_active=True,
                status=lecture_data['status'],
                attendance_window_start=lecture_data['attendance_window_start'],
                attendance_window_end=lecture_data['attendance_window_end'],
                location_locked=True,
                location_accuracy=5.0,
                location_set_at=current_time - timedelta(hours=1)
            )
            db.session.add(lecture)
        
        db.session.commit()
        
        print("✅ Supabase data initialized successfully!")
        print("📊 Created:")
        print(f"   - 1 Admin user (admin/admin123)")
        print(f"   - 1 Teacher user (teacher1/teacher123)")
        print(f"   - 3 Student users (student1-3/student123)")
        print(f"   - 3 Courses (CS101, CS201, CS301)")
        print(f"   - 4 Lectures (2 active, 2 scheduled)")
        print(f"   - Student enrollments in all courses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Supabase data: {e}")
        db.session.rollback()
        return False

def init_fallback_data():
    """Initialize fallback SQLite data if Supabase not available"""
    try:
        from init_sample_data import init_sample_data
        init_sample_data()
        return True
    except Exception as e:
        print(f"❌ Error initializing fallback data: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        if not supabase_config.is_configured():
            return False, "Supabase not configured"
        
        client = supabase_config.get_supabase_client()
        if not client:
            return False, "Could not create Supabase client"
        
        # Test connection by trying to query a simple table
        response = client.table('users').select('id').limit(1).execute()
        return True, "Supabase connection successful"
        
    except Exception as e:
        return False, f"Supabase connection failed: {str(e)}"

if __name__ == "__main__":
    # Test script
    success, message = test_supabase_connection()
    print(f"Connection test: {message}")
    
    if success:
        create_supabase_tables()
        init_supabase_data()
    else:
        print("Using fallback database...")
        init_fallback_data()