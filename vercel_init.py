"""
Vercel initialization script - runs once during build
"""
import os
from app import create_app, db

def init_vercel_db():
    """Initialize database for Vercel deployment"""
    # Use environment variable for database URL
    os.environ.setdefault('DATABASE_URL', 'sqlite:///geo_attendance_vercel.db')
    
    app = create_app('production')
    
    with app.app_context():
        # Import all models
        from models.user import User
        from models.course import Course
        from models.lecture import Lecture
        from models.attendance import Attendance
        from models.enrollment import Enrollment
        
        print("Creating database tables...")
        db.create_all()
        
        # Create default users if they don't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default users...")
            from werkzeug.security import generate_password_hash
            from datetime import datetime, timezone, timedelta
            
            IST = timezone(timedelta(hours=5, minutes=30))
            
            # Create admin
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
            
            # Create teacher
            teacher = User(
                username='teacher1',
                email='teacher1@geoattendance.com',
                password_hash=generate_password_hash('teacher123'),
                first_name='John',
                last_name='Teacher',
                role='teacher',
                employee_id='T001',
                is_active=True,
                created_at=datetime.now(IST)
            )
            db.session.add(teacher)
            
            # Create students
            for i in range(1, 4):
                student = User(
                    username=f'student{i}',
                    email=f'student{i}@geoattendance.com',
                    password_hash=generate_password_hash('student123'),
                    first_name=f'Student',
                    last_name=f'User{i}',
                    role='student',
                    student_id=f'S00{i}',
                    is_active=True,
                    created_at=datetime.now(IST)
                )
                db.session.add(student)
            
            db.session.commit()
            print("Default users created!")
        
        print("Database initialization completed!")

if __name__ == '__main__':
    init_vercel_db()