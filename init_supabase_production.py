#!/usr/bin/env python3
"""
Production database initialization script for Supabase
This script initializes the database tables without sample data for production
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set production environment
os.environ['FLASK_CONFIG'] = 'production'

from app import create_app, db
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.attendance import Attendance

def init_production_database():
    """Initialize production database with tables only (no sample data)"""
    app = create_app('production')
    
    with app.app_context():
        try:
            print("🔧 Initializing production database...")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if admin user exists, if not create one
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@geoattendance.com',
                    role='admin',
                    first_name='System',
                    last_name='Administrator'
                )
                admin.set_password('admin123')  # Change this in production!
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
            else:
                print("ℹ️ Admin user already exists")
                
            print("🎉 Production database initialization complete!")
            
        except Exception as e:
            print(f"❌ Error initializing production database: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    init_production_database()