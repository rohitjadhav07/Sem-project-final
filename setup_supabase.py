"""
Supabase Setup Script for Geo Attendance Pro
Run this after setting up your Supabase project and environment variables
"""
import os
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def setup_supabase():
    """Set up Supabase database with tables and sample data"""
    
    # Get Supabase credentials from environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in environment variables")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Create tables using SQL
        create_tables_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            role VARCHAR(20) CHECK (role IN ('admin', 'teacher', 'student')) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            phone VARCHAR(20),
            student_id VARCHAR(20) UNIQUE,
            employee_id VARCHAR(20) UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE
        );
        
        -- Courses table
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            code VARCHAR(20) UNIQUE NOT NULL,
            description TEXT,
            teacher_id INTEGER REFERENCES users(id),
            location_name VARCHAR(200),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            geofence_radius INTEGER DEFAULT 50,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Lectures table
        CREATE TABLE IF NOT EXISTS lectures (
            id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES courses(id) NOT NULL,
            teacher_id INTEGER REFERENCES users(id) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            location_name VARCHAR(200),
            geofence_radius INTEGER DEFAULT 50,
            location_accuracy DECIMAL,
            location_metadata TEXT,
            location_set_at TIMESTAMP WITH TIME ZONE,
            location_locked BOOLEAN DEFAULT FALSE,
            location_hash VARCHAR(64),
            scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
            scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,
            actual_start TIMESTAMP WITH TIME ZONE,
            actual_end TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')) DEFAULT 'scheduled',
            is_active BOOLEAN DEFAULT TRUE,
            attendance_window_start INTEGER DEFAULT -15,
            attendance_window_end INTEGER DEFAULT 15,
            auto_mark_attendance BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Enrollments table
        CREATE TABLE IF NOT EXISTS enrollments (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES users(id) NOT NULL,
            course_id INTEGER REFERENCES courses(id) NOT NULL,
            enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(student_id, course_id)
        );
        
        -- Attendances table
        CREATE TABLE IF NOT EXISTS attendances (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES users(id) NOT NULL,
            lecture_id INTEGER REFERENCES lectures(id) NOT NULL,
            status VARCHAR(20) CHECK (status IN ('present', 'absent', 'late', 'excused')) DEFAULT 'absent',
            student_latitude DECIMAL(10,8),
            student_longitude DECIMAL(11,8),
            distance_from_lecture DECIMAL,
            location_accuracy VARCHAR(50),
            security_score INTEGER,
            metadata TEXT,
            client_ip VARCHAR(45),
            verification_status VARCHAR(20) DEFAULT 'verified',
            marked_at TIMESTAMP WITH TIME ZONE,
            auto_marked BOOLEAN DEFAULT FALSE,
            notes TEXT,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(student_id, lecture_id)
        );
        
        -- Audit logs table
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            table_name VARCHAR(50),
            record_id INTEGER,
            old_values JSONB,
            new_values JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_courses_teacher ON courses(teacher_id);
        CREATE INDEX IF NOT EXISTS idx_lectures_course ON lectures(course_id);
        CREATE INDEX IF NOT EXISTS idx_lectures_teacher ON lectures(teacher_id);
        CREATE INDEX IF NOT EXISTS idx_lectures_status ON lectures(status);
        CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
        CREATE INDEX IF NOT EXISTS idx_attendances_student ON attendances(student_id);
        CREATE INDEX IF NOT EXISTS idx_attendances_lecture ON attendances(lecture_id);
        """
        
        # Execute table creation
        result = supabase.rpc('exec_sql', {'sql': create_tables_sql}).execute()
        print("✅ Database tables created successfully")
        
        # Insert sample data
        insert_sample_data(supabase)
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Supabase: {e}")
        return False

def insert_sample_data(supabase: Client):
    """Insert sample data into Supabase"""
    try:
        from werkzeug.security import generate_password_hash
        
        # Insert sample users
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@geoattendance.com',
                'password_hash': generate_password_hash('admin123'),
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'employee_id': 'EMP001'
            },
            {
                'username': 'teacher1',
                'email': 'teacher@geoattendance.com',
                'password_hash': generate_password_hash('teacher123'),
                'first_name': 'Dr. John',
                'last_name': 'Smith',
                'role': 'teacher',
                'employee_id': 'EMP002'
            },
            {
                'username': 'student1',
                'email': 'student@geoattendance.com',
                'password_hash': generate_password_hash('student123'),
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'student',
                'student_id': 'STU001'
            }
        ]
        
        # Insert users
        users_result = supabase.table('users').insert(users_data).execute()
        print("✅ Sample users created")
        
        # Get user IDs
        teacher_id = None
        student_id = None
        for user in users_result.data:
            if user['role'] == 'teacher':
                teacher_id = user['id']
            elif user['role'] == 'student':
                student_id = user['id']
        
        if not teacher_id or not student_id:
            print("⚠️ Could not get user IDs, skipping course creation")
            return
        
        # Insert sample courses
        courses_data = [
            {
                'name': 'Computer Science 101',
                'code': 'CS101',
                'description': 'Introduction to Computer Science and Programming',
                'teacher_id': teacher_id,
                'location_name': 'Computer Lab - Room 101',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'geofence_radius': 50
            },
            {
                'name': 'Data Structures & Algorithms',
                'code': 'CS201',
                'description': 'Advanced programming concepts and algorithms',
                'teacher_id': teacher_id,
                'location_name': 'Theory Class - Room 201',
                'latitude': 19.0765,
                'longitude': 72.8780,
                'geofence_radius': 40
            }
        ]
        
        courses_result = supabase.table('courses').insert(courses_data).execute()
        print("✅ Sample courses created")
        
        # Enroll student in courses
        for course in courses_result.data:
            enrollment_data = {
                'student_id': student_id,
                'course_id': course['id'],
                'enrollment_date': datetime.now(IST).isoformat()
            }
            supabase.table('enrollments').insert(enrollment_data).execute()
        
        print("✅ Student enrollments created")
        
        # Create sample lectures
        current_time = datetime.now(IST)
        for course in courses_result.data:
            lecture_data = {
                'title': f'Introduction to {course["name"]}',
                'course_id': course['id'],
                'teacher_id': teacher_id,
                'scheduled_start': (current_time - timedelta(minutes=5)).isoformat(),
                'scheduled_end': (current_time + timedelta(hours=1, minutes=55)).isoformat(),
                'location_name': course['location_name'],
                'latitude': course['latitude'],
                'longitude': course['longitude'],
                'geofence_radius': course['geofence_radius'],
                'status': 'active',
                'is_active': True,
                'location_locked': True,
                'location_accuracy': 5.0,
                'location_set_at': (current_time - timedelta(hours=1)).isoformat()
            }
            supabase.table('lectures').insert(lecture_data).execute()
        
        print("✅ Sample lectures created")
        print("🎉 Supabase setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")

if __name__ == "__main__":
    print("🚀 Setting up Supabase for Geo Attendance Pro...")
    success = setup_supabase()
    if success:
        print("\n✅ Setup completed! Your Supabase database is ready.")
        print("\n🔑 Login credentials:")
        print("Admin: admin / admin123")
        print("Teacher: teacher1 / teacher123")
        print("Student: student1 / student123")
    else:
        print("\n❌ Setup failed. Please check your environment variables and try again.")