#!/usr/bin/env python3
"""
Run script for Geo Attendance Pro
"""

from app import create_app, db
import os

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created/verified.")
    
    # Get configuration from environment
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"Starting Geo Attendance Pro...")
    print(f"Debug mode: {debug}")
    print(f"Server: http://{host}:{port}")
    print(f"Admin login: admin / admin123")
    print(f"Teacher login: teacher1 / teacher123")
    print(f"Student login: student1 / student123")
    
    app.run(host=host, port=port, debug=debug)