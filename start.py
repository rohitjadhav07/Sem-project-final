#!/usr/bin/env python3
"""
Quick start script for Geo Attendance Pro
This script will set up the database and start the application
"""

import os
import sys
from app import create_app, db

def setup_database():
    """Initialize database with sample data"""
    print("Setting up database...")
    
    # Import init_db function
    from init_db import init_database
    
    try:
        init_database()
        print("✅ Database setup complete!")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_application():
    """Start the Flask application"""
    app = create_app()
    
    print("\n" + "="*50)
    print("🚀 Starting Geo Attendance Pro")
    print("="*50)
    print(f"📍 Server: http://127.0.0.1:5000")
    print(f"👨‍💼 Admin: admin / admin123")
    print(f"👨‍🏫 Teacher: teacher1 / teacher123") 
    print(f"👨‍🎓 Student: student1 / student123")
    print("="*50)
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")

if __name__ == '__main__':
    print("🎓 Geo Attendance Pro - Quick Start")
    print("-" * 40)
    
    # Check if database exists
    db_path = 'geo_attendance.db'
    if not os.path.exists(db_path):
        print("📊 Database not found. Setting up...")
        if not setup_database():
            sys.exit(1)
    else:
        print("📊 Database found. Skipping setup.")
    
    # Start the application
    start_application()