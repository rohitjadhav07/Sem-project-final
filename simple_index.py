"""
Minimal Vercel entry point to test basic functionality
"""
import os
from flask import Flask, render_template_string

# Set environment variables
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key')

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
    </head>
    <body>
        <div class="container mt-5">
            <div class="text-center">
                <h1 class="display-4 text-primary">🎉 Geo Attendance Pro</h1>
                <p class="lead">Location-based attendance tracking system</p>
                <div class="alert alert-success">
                    <strong>✅ Deployment Successful!</strong><br>
                    The app is now running on Vercel.
                </div>
                <div class="mt-4">
                    <a href="/test" class="btn btn-primary">Test Database Connection</a>
                    <a href="/full-app" class="btn btn-success">Launch Full App</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test')
def test():
    try:
        # Test imports
        from extensions import db
        from config import config
        
        return render_template_string('''
        <div class="container mt-5">
            <h2>✅ Test Results</h2>
            <ul class="list-group">
                <li class="list-group-item list-group-item-success">Extensions imported successfully</li>
                <li class="list-group-item list-group-item-success">Config imported successfully</li>
                <li class="list-group-item list-group-item-info">Environment: {{ env }}</li>
                <li class="list-group-item list-group-item-info">Secret Key: {{ secret_set }}</li>
            </ul>
            <a href="/" class="btn btn-primary mt-3">Back to Home</a>
        </div>
        ''', 
        env=os.environ.get('FLASK_CONFIG', 'not set'),
        secret_set='Set' if os.environ.get('SECRET_KEY') else 'Not set'
        )
    except Exception as e:
        return f"<h2>❌ Test Failed</h2><p>Error: {str(e)}</p><a href='/'>Back</a>"

@app.route('/full-app')
def full_app():
    try:
        from app import create_app
        full_app = create_app('production')
        return "<h2>✅ Full app created successfully!</h2><p>Ready to redirect to main app.</p>"
    except Exception as e:
        import traceback
        return f"<h2>❌ Full App Failed</h2><pre>{traceback.format_exc()}</pre><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run()