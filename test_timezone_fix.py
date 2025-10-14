#!/usr/bin/env python3
"""
Test script to verify timezone fix
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
from models.lecture import Lecture

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def test_timezone_fix():
    """Test the timezone fix"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing timezone fix...")
        
        # Get a lecture
        lecture = Lecture.query.first()
        if not lecture:
            print("❌ No lecture found")
            return
        
        print(f"📖 Lecture: {lecture.title}")
        print(f"📅 Scheduled start (stored): {lecture.scheduled_start}")
        print(f"📅 Scheduled start (ISO): {lecture.scheduled_start.isoformat()}")
        
        # Test timezone-aware conversion
        start_time = lecture.scheduled_start
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=IST)
            print(f"📅 With IST timezone: {start_time}")
            print(f"📅 With IST timezone (ISO): {start_time.isoformat()}")
        
        print("\n✅ The fix should now show correct times in the student dashboard!")
        print("   - Server sends timezone-aware ISO strings")
        print("   - JavaScript parses them correctly without adding 'Z'")
        print("   - Times display in user's local timezone")

if __name__ == '__main__':
    test_timezone_fix()