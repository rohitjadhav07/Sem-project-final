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
            <title>Geo Attendance Pro - Loading...</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-warning">
                    <h1>⚠️ Application Loading Issue</h1>
                    <p><strong>Error:</strong> {{ error }}</p>
                    <p>The application is trying to load but encountered an issue. This is likely due to missing dependencies.</p>
                </div>
                
                <div class="alert alert-info">
                    <h5>🔧 Quick Fix Options:</h5>
                    <ol>
                        <li><strong>Try the working version:</strong> <a href="/student/active-lectures-simple" class="btn btn-success btn-sm">Student Portal</a></li>
                        <li><strong>Test basic features:</strong> <a href="/test/simple" class="btn btn-primary btn-sm">Basic Test</a></li>
                        <li><strong>Check database:</strong> <a href="/test/db" class="btn btn-info btn-sm">DB Test</a></li>
                    </ol>
                </div>
                
                <div class="card mt-4">
                    <div class="card-header">Technical Details</div>
                    <div class="card-body">
                        <pre style="font-size: 12px;">{{ details }}</pre>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', error=str(e), details=error_details)
    
    @app.route('/health')
    def health():
        return "Server is running but main app failed to initialize"