#!/usr/bin/env python3
"""
Create current attendance record for testing
"""

import os
from datetime import datetime, timezone, timedelta

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
from models.attendance import Attendance

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def create_current_attendance():
    """Create attendance for current time"""
    app = create_app()
    
    with app.app_context():
        print("🎯 Creating current attendance record...")
        
        # Get student and current lecture
        student = User.query.filter_by(role='student').first()
        current_lecture = Lecture.query.filter_by(title='Test Active Lecture').first()
        
        if not student or not current_lecture:
            print("❌ Student or current lecture not found")
            return
        
        # Check if attendance already exists
        existing = Attendance.query.filter_by(
            student_id=student.id,
            lecture_id=current_lecture.id
        ).first()
        
        if existing:
            print(f"✅ Attendance already exists: {existing.status}")
            print(f"   Marked at: {existing.marked_at}")
            return
        
        # Create new attendance record
        current_time = datetime.now()  # Use naive datetime to match database
        
        attendance = Attendance(
            student_id=student.id,
            lecture_id=current_lecture.id,
            status='present',
            marked_at=current_time,
            student_latitude=21.362200,  # Your coordinates
            student_longitude=74.884900,
            distance_from_lecture=15.0,  # 15 meters
            auto_marked=True,
            notes="Auto check-in: 15.0m from lecture"
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        print(f"✅ Created attendance record:")
        print(f"   Student: {student.username}")
        print(f"   Lecture: {current_lecture.title}")
        print(f"   Status: {attendance.status}")
        print(f"   Marked at: {attendance.marked_at}")
        print(f"   Location: {attendance.student_latitude}, {attendance.student_longitude}")
        print(f"   Distance: {attendance.distance_from_lecture}m")
        print(f"   Auto marked: {attendance.auto_marked}")

if __name__ == '__main__':
    create_current_attendance()