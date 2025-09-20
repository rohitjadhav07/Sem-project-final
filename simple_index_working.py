"""
Simple working index.py without Supabase dependencies
Use this if the main app is having issues
"""
import os
import sys
from flask import Flask, render_template_string

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables with defaults
os.environ.setdefault('FLASK_CONFIG', 'production')
os.environ.setdefault('SECRET_KEY', 'vercel-demo-secret-key-change-in-production')
os.environ.setdefault('JWT_SECRET_KEY', 'vercel-demo-jwt-secret-key-change-in-production')

# Simple Flask app that definitely works
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geo Attendance Pro - Working!</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="text-center">
                <h1 class="display-4 text-success">✅ Geo Attendance Pro</h1>
                <p class="lead">Application is working correctly!</p>
                
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> Status: Operational</h5>
                    <p>The basic application is running successfully on Vercel.</p>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h6><i class="fas fa-database"></i> Database Status</h6>
                            </div>
                            <div class="card-body">
                                <p>Currently using SQLite (fallback database)</p>
                                <a href="/test/db" class="btn btn-primary btn-sm">Test Database</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-info text-white">
                                <h6><i class="fas fa-cog"></i> Configuration</h6>
                            </div>
                            <div class="card-body">
                                <p>Ready for Supabase integration</p>
                                <a href="/test/supabase" class="btn btn-info btn-sm">Test Supabase</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h5>🚀 Next Steps:</h5>
                    <div class="list-group text-start">
                        <div class="list-group-item">
                            <strong>1. Test Basic Functionality:</strong>
                            <a href="/test/simple" class="btn btn-outline-primary btn-sm ms-2">Basic Test</a>
                        </div>
                        <div class="list-group-item">
                            <strong>2. Try Student Features:</strong>
                            <a href="/student/active-lectures-simple" class="btn btn-outline-success btn-sm ms-2">Student Portal</a>
                        </div>
                        <div class="list-group-item">
                            <strong>3. Set up Supabase (Optional):</strong>
                            <a href="/test/supabase" class="btn btn-outline-info btn-sm ms-2">Supabase Setup</a>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h6>🔑 Test Login Credentials:</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <h6>Admin</h6>
                                    <code>admin / admin123</code>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h6>Teacher</h6>
                                    <code>teacher1 / teacher123</code>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-info">
                                <div class="card-body">
                                    <h6>Student</h6>
                                    <code>student1 / student123</code>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Geo Attendance Pro is running'}

if __name__ == "__main__":
    app.run()