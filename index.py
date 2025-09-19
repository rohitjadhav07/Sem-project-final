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
    # Create a minimal Flask app that shows the error
    from flask import Flask, render_template_string
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        import traceback
        error_details = traceback.format_exc()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Geo Attendance Pro - Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h1>❌ Application Error</h1>
                    <p><strong>Error:</strong> {{ error }}</p>
                </div>
                <div class="card">
                    <div class="card-header">Error Details</div>
                    <div class="card-body">
                        <pre>{{ details }}</pre>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', error=str(e), details=error_details)
    
    @app.route('/health')
    def health():
        return "Server is running but app failed to initialize"