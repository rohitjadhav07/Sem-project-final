#!/usr/bin/env python3
"""
Create a test lecture for current time to test the active lectures functionality
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
from models.course import Course

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def create_test_lecture():
    """Create a test lecture for current time"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Creating test lecture for current time...")
        
        # Get teacher and course
        teacher = User.query.filter_by(role='teacher').first()
        course = Course.query.first()
        
        if not teacher or not course:
            print("❌ No teacher or course found")
            return
        
        # Create a lecture for current time
        now = datetime.now()  # Use naive datetime to match database
        
        # Delete any existing test lectures
        existing_test = Lecture.query.filter_by(title='Test Active Lecture').first()
        if existing_test:
            db.session.delete(existing_test)
            print("🗑️ Deleted existing test lecture")
        
        test_lecture = Lecture(
            title='Test Active Lecture',
            course_id=course.id,
            teacher_id=teacher.id,
            description='Test lecture for checking active lectures functionality',
            latitude=40.7128,  # New York coordinates
            longitude=-74.0060,
            location_name='Test Room, Computer Science Building',
            geofence_radius=50,
            scheduled_start=now - timedelta(minutes=15),  # Started 15 minutes ago
            scheduled_end=now + timedelta(minutes=45),    # Ends in 45 minutes
            status='active',
            attendance_window_start=-30,  # 30 minutes before
            attendance_window_end=60      # 60 minutes after start
        )
        
        db.session.add(test_lecture)
        db.session.commit()
        
        print(f"✅ Created test lecture: {test_lecture.title}")
        print(f"   Course: {course.code}")
        print(f"   Start: {test_lecture.scheduled_start}")
        print(f"   End: {test_lecture.scheduled_end}")
        print(f"   Status: {test_lecture.status}")
        print(f"   Window open: {test_lecture.is_attendance_window_open()}")
        
        print("\n🎯 Now test the student dashboard - you should see this lecture!")

if __name__ == '__main__':
    create_test_lecture()