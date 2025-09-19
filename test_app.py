"""
Simple test to check what's causing the crash
"""
import os
import sys

def test_imports():
    try:
        print("Testing basic imports...")
        from flask import Flask
        print("✅ Flask imported successfully")
        
        from extensions import db, login_manager, jwt, migrate
        print("✅ Extensions imported successfully")
        
        from config import config
        print("✅ Config imported successfully")
        
        # Test app creation
        app = Flask(__name__)
        config_name = os.environ.get('FLASK_CONFIG', 'production')
        app.config.from_object(config[config_name])
        print(f"✅ App configured with {config_name}")
        
        # Test extensions initialization
        db.init_app(app)
        login_manager.init_app(app)
        jwt.init_app(app)
        migrate.init_app(app, db)
        print("✅ Extensions initialized successfully")
        
        return app
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    app = test_imports()
    if app:
        print("✅ App creation successful!")
    else:
        print("❌ App creation failed!")