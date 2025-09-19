"""
Vercel serverless function entry point
"""
from app import create_app

# Create the Flask app
app = create_app('production')

# This is required for Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)