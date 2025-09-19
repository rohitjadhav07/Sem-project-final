"""
Vercel entry point for Geo Attendance Pro
"""
from app import create_app

# Create the Flask app for Vercel
app = create_app('production')

# This is the entry point that Vercel will use
if __name__ == "__main__":
    app.run()