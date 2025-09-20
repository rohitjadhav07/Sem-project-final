"""
Vercel entry point for Geo Attendance Pro
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables with defaults
os.environ.setdefault('FLASK_CONFIG', 'production')
os.environ.setdefault('SECRET_KEY', 'vercel-demo-secret-key-change-in-production')
os.environ.setdefault('JWT_SECRET_KEY', 'vercel-demo-jwt-secret-key-change-in-production')

try:
    from app import create_app
    
    # Create the Flask app for Vercel
    app = create_app('production')
    
    # This is the entry point that Vercel will use
    if __name__ == "__main__":
        app.run()
        
except Exception as e:
    # If main app fails, show error but keep working backup
    print(f"Main app failed to load: {e}")
    
    # Import the working backup
    from working_index import app
    print("Using working backup version")