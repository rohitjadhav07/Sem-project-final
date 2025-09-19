#!/usr/bin/env python3
"""
Production startup script for Geo Attendance Pro
"""

import os
import sys
from app import create_app

def main():
    """Start the application in production mode"""
    
    # Set production environment
    os.environ.setdefault('FLASK_CONFIG', 'production')
    
    # Create application
    app = create_app('production')
    
    # Get port from environment (for platforms like Heroku)
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Geo Attendance Pro in production mode...")
    print(f"📡 Server will be available at: http://0.0.0.0:{port}")
    print("🔒 Security features enabled")
    print("📊 Logging enabled")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()