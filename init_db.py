#!/usr/bin/env python3
"""
Database initialization script for Geo Attendance Pro
Creates tables and adds sample data for testing
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, environment variables not loaded from .env file")

from app import create_app, db
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.attendance import Attendance
from datetime import datetime, timedelta
import os

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating tables...")
        db.create_all()
        
        # Create admin user
        print("Creating admin user...")
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
        
        # Create teacher
        print("Creating teacher...")
        teacher = User(
            username='teacher1',
            email='teacher1@example.com',
            first_name='John',
            last_name='Smith',
            role='teacher',
            employee_id='EMP002'
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        
        # Create students
        print("Creating students...")
        students = []
        for i in range(1, 6):
            student = User(
                username=f'student{i}',
                email=f'student{i}@example.com',
                first_name=f'Student',
                last_name=f'User{i}',
                role='student',
                student_id=f'STU00{i}'
            )
            student.set_password('student123')
            students.append(student)
            db.session.add(student)
        
        db.session.commit()
        
        # Create courses
        print("Creating courses...")
        courses = [
            Course(
                code='CS101',
                name='Introduction to Computer Science',
                description='Basic concepts of computer science and programming',
                teacher_id=teacher.id,
                credits=3,
                semester='Fall 2024',
                academic_year='2024-25'
            ),
            Course(
                code='CS201',
                name='Data Structures and Algorithms',
                description='Advanced programming concepts and algorithms',
                teacher_id=teacher.id,
                credits=4,
                semester='Fall 2024',
                academic_year='2024-25'
            )
        ]
        
        for course in courses:
            db.session.add(course)
        
        db.session.commit()
        
        # Enroll students in courses
        print("Creating enrollments...")
        for student in students:
            for course in courses:
                enrollment = Enrollment(
                    student_id=student.id,
                    course_id=course.id
                )
                db.session.add(enrollment)
        
        # Also enroll any existing students (like newly registered ones)
        existing_students = User.query.filter_by(role='student').all()
        for student in existing_students:
            if student not in students:  # Don't duplicate enrollments
                for course in courses:
                    existing_enrollment = Enrollment.query.filter_by(
                        student_id=student.id,
                        course_id=course.id
                    ).first()
                    if not existing_enrollment:
                        enrollment = Enrollment(
                            student_id=student.id,
                            course_id=course.id
                        )
                        db.session.add(enrollment)
        
        db.session.commit()
        
        # Create sample lectures
        print("Creating sample lectures...")
        from datetime import timezone
        # IST timezone (UTC+5:30)
        IST = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(IST)
        
        lectures = [
            # Past lecture
            Lecture(
                title='Introduction to Programming',
                course_id=courses[0].id,
                teacher_id=teacher.id,
                description='Basic programming concepts',
                latitude=40.7128,  # New York coordinates
                longitude=-74.0060,
                location_name='Room 101, Computer Science Building',
                geofence_radius=50,
                scheduled_start=now - timedelta(days=1),
                scheduled_end=now - timedelta(days=1) + timedelta(hours=1, minutes=30),
                status='completed'
            ),
            # Current/Active lecture
            Lecture(
                title='Variables and Data Types',
                course_id=courses[0].id,
                teacher_id=teacher.id,
                description='Understanding variables and data types',
                latitude=40.7128,
                longitude=-74.0060,
                location_name='Room 102, Computer Science Building',
                geofence_radius=50,
                scheduled_start=now - timedelta(minutes=30),
                scheduled_end=now + timedelta(hours=1),
                status='active'
            ),
            # Future lecture
            Lecture(
                title='Control Structures',
                course_id=courses[0].id,
                teacher_id=teacher.id,
                description='If statements, loops, and control flow',
                latitude=40.7128,
                longitude=-74.0060,
                location_name='Room 103, Computer Science Building',
                geofence_radius=50,
                scheduled_start=now + timedelta(days=1),
                scheduled_end=now + timedelta(days=1, hours=1, minutes=30),
                status='scheduled'
            )
        ]
        
        for lecture in lectures:
            db.session.add(lecture)
        
        db.session.commit()
        
        # Create sample attendance records
        print("Creating sample attendance...")
        # For the past lecture, mark some students as present
        past_lecture = lectures[0]
        for i, student in enumerate(students[:3]):  # First 3 students attended
            attendance = Attendance(
                student_id=student.id,
                lecture_id=past_lecture.id,
                status='present',
                student_latitude=40.7128 + (i * 0.0001),  # Slightly different locations
                student_longitude=-74.0060 + (i * 0.0001),
                distance_from_lecture=10 + (i * 5),
                marked_at=past_lecture.scheduled_start + timedelta(minutes=5)
            )
            db.session.add(attendance)
        
        # Mark remaining students as absent
        for student in students[3:]:
            attendance = Attendance(
                student_id=student.id,
                lecture_id=past_lecture.id,
                status='absent'
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nSample login credentials:")
        print("Admin: admin / admin123")
        print("Teacher: teacher1 / teacher123")
        print("Students: student1-student5 / student123")
        print("\nYou can now run the application with: python app.py")

if __name__ == '__main__':
    init_database()