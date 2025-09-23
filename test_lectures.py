#!/usr/bin/env python3
"""
Test script to check lecture availability and attendance window logic
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set environment
os.environ['FLASK_CONFIG'] = 'development'

from app import create_app, db
from models.user import User
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.attendance import Attendance

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def test_lectures():
    """Test lecture availability for students"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing lecture availability...")
        
        # Get a student user
        student = User.query.filter_by(role='student').first()
        if not student:
            print("❌ No student found in database")
            return
        
        print(f"✅ Testing with student: {student.username}")
        
        # Get student enrollments
        enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            is_active=True
        ).all()
        
        print(f"📚 Student enrolled in {len(enrollments)} courses")
        for enrollment in enrollments:
            print(f"   - {enrollment.course.code}: {enrollment.course.name}")
        
        # Get all lectures
        all_lectures = Lecture.query.filter_by(is_active=True).all()
        print(f"📅 Total lectures in database: {len(all_lectures)}")
        
        # Get lectures for enrolled courses
        enrolled_course_ids = [e.course_id for e in enrollments]
        enrolled_lectures = [l for l in all_lectures if l.course_id in enrolled_course_ids]
        print(f"🎯 Lectures for enrolled courses: {len(enrolled_lectures)}")
        
        current_time = datetime.now(IST)
        print(f"🕐 Current time (IST): {current_time}")
        
        for lecture in enrolled_lectures:
            print(f"\n📖 Lecture: {lecture.title}")
            print(f"   Course: {lecture.course.code}")
            print(f"   Status: {lecture.status}")
            print(f"   Scheduled: {lecture.scheduled_start} to {lecture.scheduled_end}")
            
            # Check attendance window
            window_start_minutes = getattr(lecture, 'attendance_window_start', -30)
            window_end_minutes = getattr(lecture, 'attendance_window_end', 60)
            
            start_window = lecture.scheduled_start + timedelta(minutes=window_start_minutes)
            end_window = lecture.scheduled_start + timedelta(minutes=window_end_minutes)
            
            print(f"   Window: {start_window} to {end_window}")
            print(f"   Window open: {start_window <= current_time <= end_window}")
            
            # Check if attendance marked
            existing_attendance = Attendance.query.filter_by(
                student_id=student.id,
                lecture_id=lecture.id
            ).first()
            
            print(f"   Attendance marked: {existing_attendance is not None}")
            
            # Check if should appear in active lectures
            should_appear = (
                not existing_attendance and 
                lecture.is_attendance_window_open() and
                lecture.latitude and 
                lecture.longitude
            )
            
            print(f"   Should appear in active lectures: {should_appear}")
            print(f"   Has location: {bool(lecture.latitude and lecture.longitude)}")

if __name__ == '__main__':
    test_lectures()