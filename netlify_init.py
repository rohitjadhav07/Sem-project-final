"""
Netlify initialization script
"""
import os
from app import create_app, db

def init_netlify():
    """Initialize for Netlify deployment"""
    # Set up environment
    os.environ.setdefault('DATABASE_URL', 'sqlite:///geo_attendance_netlify.db')
    
    app = create_app('production')
    
    with app.app_context():
        # Import models
        from models.user import User
        from models.course import Course
        from models.lecture import Lecture
        from models.attendance import Attendance
        from models.enrollment import Enrollment
        
        print("Setting up database for Netlify...")
        db.create_all()
        
        # Create sample data
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            from datetime import datetime, timezone, timedelta
            
            IST = timezone(timedelta(hours=5, minutes=30))
            
            admin = User(
                username='admin',
                email='admin@geoattendance.com',
                password_hash=generate_password_hash('admin123'),
                first_name='System',
                last_name='Administrator',
                role='admin',
                is_active=True,
                created_at=datetime.now(IST)
            )
            db.session.add(admin)
            db.session.commit()
            print("Netlify setup completed!")

if __name__ == '__main__':
    init_netlify()