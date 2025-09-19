#!/usr/bin/env python3
"""
Script to enroll students in courses for testing
"""

from app import create_app
from models.user import User
from models.course import Course
from models.enrollment import Enrollment
from app import db
from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def enroll_students():
    app = create_app()
    with app.app_context():
        # Get all students
        students = User.query.filter_by(role='student').all()
        
        # Get all courses
        courses = Course.query.filter_by(is_active=True).all()
        
        print(f"Found {len(students)} students and {len(courses)} courses")
        
        # Enroll each student in all courses
        for student in students:
            print(f"\nEnrolling {student.username} ({student.full_name}):")
            
            for course in courses:
                # Check if already enrolled
                existing = Enrollment.query.filter_by(
                    student_id=student.id,
                    course_id=course.id
                ).first()
                
                if existing:
                    if not existing.is_active:
                        existing.is_active = True
                        existing.enrollment_date = datetime.now(IST)
                        print(f"  - Reactivated enrollment in {course.code}")
                    else:
                        print(f"  - Already enrolled in {course.code}")
                else:
                    # Create new enrollment
                    enrollment = Enrollment(
                        student_id=student.id,
                        course_id=course.id,
                        enrollment_date=datetime.now(IST),
                        is_active=True
                    )
                    db.session.add(enrollment)
                    print(f"  - Enrolled in {course.code}")
        
        db.session.commit()
        print("\nAll students enrolled successfully!")
        
        # Show enrollment summary
        print("\nEnrollment Summary:")
        for student in students:
            enrollments = Enrollment.query.filter_by(
                student_id=student.id,
                is_active=True
            ).count()
            print(f"  {student.username}: {enrollments} courses")

if __name__ == "__main__":
    enroll_students()