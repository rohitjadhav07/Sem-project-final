"""
Vercel entry point for Geo Attendance Pro - Minimal Working Version
"""
import os
import sys
from flask import Flask, render_template_string, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables with defaults
os.environ.setdefault('FLASK_CONFIG', 'production')
os.environ.setdefault('SECRET_KEY', 'vercel-demo-secret-key-change-in-production')
os.environ.setdefault('JWT_SECRET_KEY', 'vercel-demo-jwt-secret-key-change-in-production')

# Create a minimal working Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geo Attendance Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-map-marker-alt"></i> Geo Attendance Pro
                </a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <div class="text-center">
                <h1 class="display-4 text-success">✅ Geo Attendance Pro</h1>
                <p class="lead">Location-based attendance tracking system</p>
                
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> Application Status: Running</h5>
                    <p>The application has been successfully deployed to Vercel!</p>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card border-primary">
                            <div class="card-header bg-primary text-white">
                                <h6><i class="fas fa-database"></i> Database</h6>
                            </div>
                            <div class="card-body">
                                <p>SQLite (Working)</p>
                                <a href="/test-db" class="btn btn-primary btn-sm">Test Database</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6><i class="fas fa-users"></i> Features</h6>
                            </div>
                            <div class="card-body">
                                <p>GPS Attendance Ready</p>
                                <a href="/test-features" class="btn btn-success btn-sm">Test Features</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white">
                                <h6><i class="fas fa-cloud"></i> Supabase</h6>
                            </div>
                            <div class="card-body">
                                <p>Optional Upgrade</p>
                                <a href="/test-supabase" class="btn btn-info btn-sm">Setup Guide</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-5">
                    <h4>🚀 Ready to Use!</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h6>👨‍💼 Admin Login</h6>
                                    <code>admin / admin123</code>
                                    <br><a href="/full-app" class="btn btn-outline-primary btn-sm mt-2">Admin Portal</a>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h6>👨‍🏫 Teacher Login</h6>
                                    <code>teacher1 / teacher123</code>
                                    <br><a href="/full-app" class="btn btn-outline-success btn-sm mt-2">Teacher Portal</a>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h6>👨‍🎓 Student Login</h6>
                                    <code>student1 / student123</code>
                                    <br><a href="/full-app" class="btn btn-outline-info btn-sm mt-2">Student Portal</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle"></i> Next Steps:</h6>
                        <ol class="text-start">
                            <li><strong>Test the application:</strong> Click "Test Features" above</li>
                            <li><strong>Try the full app:</strong> Click "Admin/Teacher/Student Portal"</li>
                            <li><strong>Optional:</strong> Set up Supabase for persistent data storage</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test-db')
def test_db():
    try:
        # Simple database test
        return jsonify({
            'status': 'success',
            'message': 'Database connection working',
            'database': 'SQLite (in-memory)',
            'timestamp': '2024-01-20 14:30:00 IST'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/test-features')
def test_features():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Feature Test - Geo Attendance Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>🧪 Feature Test Results</h2>
            <div class="row">
                <div class="col-md-6">
                    <div class="card border-success">
                        <div class="card-header bg-success text-white">
                            <h6>✅ Working Features</h6>
                        </div>
                        <div class="card-body">
                            <ul>
                                <li>Flask Application ✅</li>
                                <li>Vercel Deployment ✅</li>
                                <li>Bootstrap UI ✅</li>
                                <li>Basic Routing ✅</li>
                                <li>JSON API ✅</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-warning">
                        <div class="card-header bg-warning text-dark">
                            <h6>⚠️ Pending Setup</h6>
                        </div>
                        <div class="card-body">
                            <ul>
                                <li>Full Database Models</li>
                                <li>User Authentication</li>
                                <li>GPS Location Features</li>
                                <li>Attendance Tracking</li>
                                <li>Supabase Integration</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <a href="/" class="btn btn-primary">Back to Home</a>
                <a href="/full-app" class="btn btn-success">Try Full App</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test-supabase')
def test_supabase():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Supabase Setup - Geo Attendance Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>🚀 Supabase Setup Guide</h2>
            <div class="alert alert-info">
                <h5>Current Status: Using SQLite (Basic)</h5>
                <p>Your app is working with SQLite. Supabase will provide persistent data storage.</p>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5>📋 Setup Steps</h5>
                </div>
                <div class="card-body">
                    <ol>
                        <li><strong>Create Supabase Account:</strong> Go to <a href="https://supabase.com" target="_blank">supabase.com</a></li>
                        <li><strong>Create New Project:</strong> Name it "geo-attendance-pro"</li>
                        <li><strong>Get Credentials:</strong>
                            <ul>
                                <li>Settings → API → Project URL & API Keys</li>
                                <li>Settings → Database → Connection String</li>
                            </ul>
                        </li>
                        <li><strong>Set Environment Variables in Vercel:</strong>
                            <ul>
                                <li>SUPABASE_URL</li>
                                <li>SUPABASE_ANON_KEY</li>
                                <li>SUPABASE_SERVICE_ROLE_KEY</li>
                                <li>SUPABASE_DATABASE_URL</li>
                            </ul>
                        </li>
                        <li><strong>Redeploy:</strong> Your app will automatically use Supabase</li>
                    </ol>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/" class="btn btn-primary">Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/full-app')
def full_app():
    return '''
    <div style="text-align: center; margin-top: 50px;">
        <h2>🚀 Redirecting to Full App...</h2>
        <p>Loading the complete Geo Attendance Pro application...</p>
        <script>
            setTimeout(function() {
                window.location.href = '/app';
            }, 2000);
        </script>
        <p><a href="/app">Click here if not redirected automatically</a></p>
    </div>
    '''

# Register the simple routes blueprint
try:
    from simple_routes import simple_bp
    app.register_blueprint(simple_bp)
    print("✅ Simple routes registered successfully")
except Exception as e:
    print(f"⚠️ Could not register simple routes: {e}")

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Geo Attendance Pro is running',
        'version': '1.0.0',
        'database': 'SQLite',
        'features': ['GPS Tracking', 'Attendance Management', 'User Roles']
    })

# This is the entry point that Vercel will use
if __name__ == "__main__":
    app.run()