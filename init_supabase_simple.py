"""
Simple Supabase initialization for Geo Attendance Pro
"""
from extensions import db
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.enrollment import Enrollment
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def init_supabase_data():
    """Initialize Supabase with sample data"""
    try:
        # Create all tables
        db.create_all()
        print("✅ Supabase tables created")
        
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
        students_data = [
            ('student1', 'alice@student.com', 'Alice', 'Johnson', 'STU001'),
            ('student2', 'bob@student.com', 'Bob', 'Wilson', 'STU002'),
            ('student3', 'carol@student.com', 'Carol', 'Davis', 'STU003')
        ]
        
        students = []
        for username, email, first_name, last_name, student_id in students_data:
            student = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='student',
                student_id=student_id
            )
            student.set_password('student123')
            db.session.add(student)
            students.append(student)
        
        # Commit users first
        db.session.commit()
        print("✅ Users created in Supabase")
        
        # Create sample courses
        courses_data = [
            ('Computer Science 101', 'CS101', 'Introduction to Computer Science', 'Computer Lab - Room 101', 19.0760, 72.8777, 50),
            ('Data Structures', 'CS201', 'Advanced programming concepts', 'Theory Class - Room 201', 19.0765, 72.8780, 40),
            ('Web Development', 'CS301', 'Modern web development', 'Web Lab - Room 301', 19.0755, 72.8785, 60)
        ]
        
        courses = []
        for name, code, desc, location, lat, lon, radius in courses_data:
            course = Course(
                name=name,
                code=code,
                description=desc,
                teacher_id=teacher.id,
                location_name=location,
                latitude=lat,
                longitude=lon,
                geofence_radius=radius,
                is_active=True
            )
            db.session.add(course)
            courses.append(course)
        
        db.session.commit()
        print("✅ Courses created in Supabase")
        
        # Enroll all students in all courses
        for student in students:
            for course in courses:
                enrollment = Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    enrollment_date=datetime.now(IST),
                    is_active=True
                )
                db.session.add(enrollment)
        
        db.session.commit()
        print("✅ Enrollments created in Supabase")
        
        # Create active lectures
        current_time = datetime.now(IST)
        
        lectures_data = [
            ('Introduction to Programming', courses[0].id, current_time - timedelta(minutes=5), 'active'),
            ('Variables and Data Types', courses[0].id, current_time + timedelta(hours=2), 'scheduled'),
            ('Arrays and Linked Lists', courses[1].id, current_time - timedelta(minutes=10), 'active'),
            ('HTML and CSS Basics', courses[2].id, current_time + timedelta(hours=1), 'scheduled')
        ]
        
        for title, course_id, start_time, status in lectures_data:
            course = next(c for c in courses if c.id == course_id)
            lecture = Lecture(
                title=title,
                course_id=course_id,
                teacher_id=teacher.id,
                scheduled_start=start_time,
                scheduled_end=start_time + timedelta(hours=2),
                location_name=course.location_name,
                latitude=course.latitude,
                longitude=course.longitude,
                geofence_radius=course.geofence_radius,
                is_active=True,
                status=status,
                attendance_window_start=-15,
                attendance_window_end=30,
                location_locked=True,
                location_accuracy=5.0,
                location_set_at=current_time - timedelta(hours=1)
            )
            db.session.add(lecture)
        
        db.session.commit()
        print("✅ Lectures created in Supabase")
        
        print("🎉 Supabase initialization completed successfully!")
        print("📊 Created:")
        print(f"   - 1 Admin: admin/admin123")
        print(f"   - 1 Teacher: teacher1/teacher123") 
        print(f"   - 3 Students: student1-3/student123")
        print(f"   - 3 Courses with GPS locations")
        print(f"   - 4 Lectures (2 active, 2 scheduled)")
        print(f"   - All students enrolled in all courses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        db.session.rollback()
        return False