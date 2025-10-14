#!/usr/bin/env python3
"""
Debug script to check attendance records and issues
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

def debug_attendance():
    """Debug attendance records"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Debugging attendance records...")
        
        # Get a student
        student = User.query.filter_by(role='student').first()
        if not student:
            print("❌ No student found")
            return
        
        print(f"👤 Student: {student.username} ({student.full_name})")
        
        # Get all attendance records for this student
        attendances = Attendance.query.filter_by(student_id=student.id).all()
        print(f"📊 Total attendance records: {len(attendances)}")
        
        if not attendances:
            print("❌ No attendance records found!")
            return
        
        print("\n📋 Attendance Records:")
        for attendance in attendances:
            print(f"  ID: {attendance.id}")
            print(f"  Lecture: {attendance.lecture.title if attendance.lecture else 'Unknown'}")
            print(f"  Course: {attendance.lecture.course.code if attendance.lecture and attendance.lecture.course else 'Unknown'}")
            print(f"  Status: {attendance.status}")
            print(f"  Marked at: {attendance.marked_at}")
            print(f"  Auto marked: {attendance.auto_marked}")
            print(f"  Location: {attendance.student_latitude}, {attendance.student_longitude}")
            print(f"  Distance: {attendance.distance_from_lecture}m")
            print(f"  Notes: {attendance.notes}")
            print("  ---")
        
        # Check recent attendance query
        print("\n🔍 Testing recent attendance query...")
        recent_attendance = Attendance.query.filter_by(student_id=student.id)\
            .join(Lecture)\
            .order_by(Attendance.marked_at.desc())\
            .limit(10)\
            .all()
        
        print(f"📊 Recent attendance count: {len(recent_attendance)}")
        
        # Check teacher view
        print("\n👨‍🏫 Checking teacher view...")
        teacher = User.query.filter_by(role='teacher').first()
        if teacher:
            lectures = Lecture.query.filter_by(teacher_id=teacher.id).all()
            print(f"📚 Teacher has {len(lectures)} lectures")
            
            for lecture in lectures:
                attendances = Attendance.query.filter_by(lecture_id=lecture.id).all()
                print(f"  Lecture: {lecture.title}")
                print(f"  Attendance records: {len(attendances)}")
                for att in attendances:
                    print(f"    - {att.student.username}: {att.status} (marked: {att.marked_at})")
        
        # Check timezone issues
        print("\n🕐 Checking timezone issues...")
        current_time = datetime.now(IST)
        print(f"Current time (IST): {current_time}")
        
        for attendance in attendances[:3]:  # Check first 3
            if attendance.marked_at:
                print(f"Attendance marked at: {attendance.marked_at}")
                print(f"Timezone info: {attendance.marked_at.tzinfo}")
                
                # Convert to IST if needed
                if attendance.marked_at.tzinfo is None:
                    ist_time = attendance.marked_at.replace(tzinfo=IST)
                    print(f"With IST timezone: {ist_time}")

if __name__ == '__main__':
    debug_attendance()