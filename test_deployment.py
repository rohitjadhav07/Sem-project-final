#!/usr/bin/env python3
"""
Test script to verify deployment configuration
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_deployment():
    """Test deployment configuration"""
    print("🧪 Testing deployment configuration...")
    
    # Test environment variables
    required_vars = [
        'DATABASE_URL',
        'SUPABASE_URL', 
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 20}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    # Test Flask app creation
    try:
        os.environ['FLASK_CONFIG'] = 'production'
        from app import create_app
        app = create_app('production')
        print("✅ Flask app created successfully")
        
        # Test database connection
        with app.app_context():
            from extensions import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_deployment()
    sys.exit(0 if success else 1)