#!/usr/bin/env python3
"""
WSGI entry point for Geo Attendance Pro
"""

import os
from app import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'production')

# Create application instance
app = create_app(config_name)

if __name__ == "__main__":
    app.run()