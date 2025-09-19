#!/usr/bin/env python3
"""
Quick test script to verify the application is working
"""

from app import create_app, db
from models.user import User

def test_app():
    """Test basic app functionality"""
    app = create_app()
    
    with app.app_context():
        # Test database connection
        try:
            user_count = User.query.count()
            print(f"✅ Database connected - {user_count} users found")
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
        
        # Test user authentication
        try:
            admin = User.query.filter_by(username='admin').first()
            if admin and admin.check_password('admin123'):
                print("✅ Admin login test passed")
            else:
                print("❌ Admin login test failed")
                return False
        except Exception as e:
            print(f"❌ Auth test error: {e}")
            return False
        
        # Test student user
        try:
            student = User.query.filter_by(username='student1').first()
            if student and student.check_password('student123'):
                print("✅ Student login test passed")
            else:
                print("❌ Student login test failed")
                return False
        except Exception as e:
            print(f"❌ Student test error: {e}")
            return False
        
        print("✅ All tests passed! Application is ready to use.")
        print("\n🚀 You can now:")
        print("1. Run 'python run.py' to start the server")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Login with: admin/admin123 or student1/student123")
        
        return True

if __name__ == '__main__':
    test_app()