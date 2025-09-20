"""
Working version of the full app without problematic dependencies
"""
import os
import sys
from flask import Flask, render_template_string, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Simple in-memory user storage (for demo)
users_db = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'password_hash': generate_password_hash('admin123'),
        'first_name': 'System',
        'last_name': 'Administrator',
        'role': 'admin',
        'email': 'admin@geoattendance.com'
    },
    'teacher1': {
        'id': 2,
        'username': 'teacher1',
        'password_hash': generate_password_hash('teacher123'),
        'first_name': 'Dr. John',
        'last_name': 'Smith',
        'role': 'teacher',
        'email': 'teacher@geoattendance.com'
    },
    'student1': {
        'id': 3,
        'username': 'student1',
        'password_hash': generate_password_hash('student123'),
        'first_name': 'Alice',
        'last_name': 'Johnson',
        'role': 'student',
        'email': 'student@geoattendance.com'
    }
}

# Sample lectures data
lectures_db = [
    {
        'id': 1,
        'title': 'Introduction to Programming',
        'course_code': 'CS101',
        'course_name': 'Computer Science 101',
        'teacher_id': 2,
        'scheduled_start': datetime.now(IST) - timedelta(minutes=5),
        'scheduled_end': datetime.now(IST) + timedelta(hours=1, minutes=55),
        'location_name': 'Computer Lab - Room 101',
        'latitude': 19.0760,
        'longitude': 72.8777,
        'geofence_radius': 50,
        'status': 'active',
        'is_active': True
    },
    {
        'id': 2,
        'title': 'Data Structures',
        'course_code': 'CS201',
        'course_name': 'Advanced Programming',
        'teacher_id': 2,
        'scheduled_start': datetime.now(IST) + timedelta(hours=2),
        'scheduled_end': datetime.now(IST) + timedelta(hours=4),
        'location_name': 'Theory Class - Room 201',
        'latitude': 19.0765,
        'longitude': 72.8780,
        'geofence_radius': 40,
        'status': 'scheduled',
        'is_active': True
    }
]

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.role = user_data['role']
        self.email = user_data['email']
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def create_working_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'demo-secret-key')
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        for username, user_data in users_db.items():
            if user_data['id'] == int(user_id):
                return User(user_data)
        return None
    
    @app.route('/')
    def home():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif current_user.role == 'student':
                return redirect(url_for('student_dashboard'))
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Geo Attendance Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-map-marker-alt"></i> Geo Attendance Pro
                    </a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="{{ url_for('login') }}">Login</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-5">
                <div class="row">
                    <div class="col-md-8 mx-auto text-center">
                        <h1 class="display-4 mb-4">
                            <i class="fas fa-map-marker-alt text-primary"></i>
                            Geo Attendance Pro
                        </h1>
                        <p class="lead">Location-based attendance tracking system for educational institutions</p>
                        
                        <div class="mt-4">
                            <a href="{{ url_for('login') }}" class="btn btn-primary btn-lg me-3">
                                <i class="fas fa-sign-in-alt"></i> Login
                            </a>
                        </div>
                        
                        <div class="mt-5">
                            <h5>Demo Credentials:</h5>
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h6>Admin</h6>
                                            <code>admin / admin123</code>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h6>Teacher</h6>
                                            <code>teacher1 / teacher123</code>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card">
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
            </div>
        </body>
        </html>
        ''')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if username in users_db:
                user = User(users_db[username])
                if user.check_password(password):
                    login_user(user)
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    
                    if user.role == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    elif user.role == 'teacher':
                        return redirect(url_for('teacher_dashboard'))
                    elif user.role == 'student':
                        return redirect(url_for('student_dashboard'))
                else:
                    flash('Invalid password', 'error')
            else:
                flash('Invalid username', 'error')
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Geo Attendance Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h4>Login to Geo Attendance Pro</h4>
                            </div>
                            <div class="card-body">
                                {% with messages = get_flashed_messages(with_categories=true) %}
                                    {% if messages %}
                                        {% for category, message in messages %}
                                            <div class="alert alert-danger">{{ message }}</div>
                                        {% endfor %}
                                    {% endif %}
                                {% endwith %}
                                
                                <form method="POST">
                                    <div class="mb-3">
                                        <label for="username" class="form-label">Username</label>
                                        <input type="text" class="form-control" id="username" name="username" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="password" class="form-label">Password</label>
                                        <input type="password" class="form-control" id="password" name="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Login</button>
                                    <a href="/" class="btn btn-secondary">Back</a>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            flash('Access denied', 'error')
            return redirect(url_for('home'))
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="/">Geo Attendance Pro</a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">{{ current_user.full_name }}</span>
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2><i class="fas fa-cogs"></i> Admin Dashboard</h2>
                <p class="text-muted">Welcome, {{ current_user.full_name }}!</p>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5>Total Users</h5>
                                <h3>{{ users_count }}</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5>Active Lectures</h5>
                                <h3>{{ active_lectures }}</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <h5>System Status</h5>
                                <h3>✅ Online</h3>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="alert alert-success">
                        <h5><i class="fas fa-check-circle"></i> System Status</h5>
                        <p>All systems are operational. The Geo Attendance Pro application is running successfully!</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', users_count=len(users_db), active_lectures=len([l for l in lectures_db if l['status'] == 'active']))
    
    @app.route('/teacher/dashboard')
    @login_required
    def teacher_dashboard():
        if current_user.role != 'teacher':
            flash('Access denied', 'error')
            return redirect(url_for('home'))
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Teacher Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-success">
                <div class="container">
                    <a class="navbar-brand" href="/">Geo Attendance Pro</a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">{{ current_user.full_name }}</span>
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2><i class="fas fa-chalkboard-teacher"></i> Teacher Dashboard</h2>
                <p class="text-muted">Welcome, {{ current_user.full_name }}!</p>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-calendar"></i> Today's Lectures</h5>
                            </div>
                            <div class="card-body">
                                {% for lecture in lectures %}
                                <div class="mb-3 p-3 border rounded">
                                    <h6>{{ lecture.title }}</h6>
                                    <p><strong>Course:</strong> {{ lecture.course_code }} - {{ lecture.course_name }}</p>
                                    <p><strong>Time:</strong> {{ lecture.scheduled_start.strftime('%H:%M') }} - {{ lecture.scheduled_end.strftime('%H:%M') }}</p>
                                    <p><strong>Location:</strong> {{ lecture.location_name }}</p>
                                    <span class="badge bg-{{ 'success' if lecture.status == 'active' else 'warning' }}">
                                        {{ lecture.status.title() }}
                                    </span>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-bar"></i> Quick Stats</h5>
                            </div>
                            <div class="card-body">
                                <div class="row text-center">
                                    <div class="col-6">
                                        <h4 class="text-primary">{{ lectures|length }}</h4>
                                        <small>Total Lectures</small>
                                    </div>
                                    <div class="col-6">
                                        <h4 class="text-success">{{ active_count }}</h4>
                                        <small>Active Now</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', lectures=lectures_db, active_count=len([l for l in lectures_db if l['status'] == 'active']))
    
    @app.route('/student/dashboard')
    @login_required
    def student_dashboard():
        if current_user.role != 'student':
            flash('Access denied', 'error')
            return redirect(url_for('home'))
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-info">
                <div class="container">
                    <a class="navbar-brand" href="/">Geo Attendance Pro</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="{{ url_for('student_active_lectures') }}">Active Lectures</a>
                        <span class="navbar-text me-3">{{ current_user.full_name }}</span>
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2><i class="fas fa-user-graduate"></i> Student Dashboard</h2>
                <p class="text-muted">Welcome, {{ current_user.full_name }}!</p>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5>Enrolled Courses</h5>
                                <h3>3</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5>Active Lectures</h5>
                                <h3>{{ active_count }}</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <h5>Attendance Rate</h5>
                                <h3>95%</h3>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-broadcast-tower"></i> Available Lectures</h5>
                        </div>
                        <div class="card-body">
                            {% if active_lectures %}
                                {% for lecture in active_lectures %}
                                <div class="alert alert-success">
                                    <h6>{{ lecture.title }}</h6>
                                    <p><strong>Course:</strong> {{ lecture.course_code }}</p>
                                    <p><strong>Location:</strong> {{ lecture.location_name }}</p>
                                    <a href="{{ url_for('student_active_lectures') }}" class="btn btn-success btn-sm">
                                        <i class="fas fa-map-marker-alt"></i> Check In
                                    </a>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i> No active lectures at the moment.
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''', active_count=len([l for l in lectures_db if l['status'] == 'active']), 
             active_lectures=[l for l in lectures_db if l['status'] == 'active'])
    
    @app.route('/student/active-lectures')
    @login_required
    def student_active_lectures():
        if current_user.role != 'student':
            flash('Access denied', 'error')
            return redirect(url_for('home'))
        
        active_lectures = [l for l in lectures_db if l['status'] == 'active']
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Active Lectures</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-info">
                <div class="container">
                    <a class="navbar-brand" href="/">Geo Attendance Pro</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="{{ url_for('student_dashboard') }}">Dashboard</a>
                        <span class="navbar-text me-3">{{ current_user.full_name }}</span>
                        <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2><i class="fas fa-broadcast-tower"></i> Active Lectures</h2>
                <p class="text-muted">Mark your attendance for ongoing lectures</p>
                
                {% if lectures %}
                    <div class="row">
                        {% for lecture in lectures %}
                        <div class="col-md-6 mb-4">
                            <div class="card border-success">
                                <div class="card-header bg-success text-white">
                                    <h6>{{ lecture.course_code }} - {{ lecture.title }}</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Course:</strong> {{ lecture.course_name }}</p>
                                    <p><strong>Time:</strong> {{ lecture.scheduled_start.strftime('%H:%M') }} - {{ lecture.scheduled_end.strftime('%H:%M') }}</p>
                                    <p><strong>Location:</strong> {{ lecture.location_name }}</p>
                                    <p><strong>Required Distance:</strong> Within {{ lecture.geofence_radius }}m</p>
                                    
                                    <button class="btn btn-success" onclick="startCheckin({{ lecture.id }}, '{{ lecture.title }}', {{ lecture.latitude }}, {{ lecture.longitude }}, {{ lecture.geofence_radius }})">
                                        <i class="fas fa-map-marker-alt"></i> Check In Now
                                    </button>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle fa-3x mb-3"></i>
                        <h5>No Active Lectures</h5>
                        <p>There are no lectures available for check-in at the moment.</p>
                    </div>
                {% endif %}
            </div>
            
            <script>
            function startCheckin(lectureId, title, lat, lon, radius) {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const userLat = position.coords.latitude;
                        const userLon = position.coords.longitude;
                        const accuracy = position.coords.accuracy;
                        
                        // Calculate distance
                        const distance = calculateDistance(userLat, userLon, lat, lon);
                        
                        if (distance <= radius) {
                            alert(`✅ Check-in successful for "${title}"!\\n\\nYour distance: ${Math.round(distance)}m\\nRequired: Within ${radius}m\\nGPS accuracy: ${Math.round(accuracy)}m`);
                        } else {
                            alert(`❌ You are too far from the lecture location.\\n\\nYour distance: ${Math.round(distance)}m\\nRequired: Within ${radius}m\\n\\nPlease move closer to the lecture location.`);
                        }
                    }, function(error) {
                        alert('❌ Unable to get your location. Please enable GPS and try again.');
                    }, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    });
                } else {
                    alert('❌ Geolocation is not supported by this browser.');
                }
            }
            
            function calculateDistance(lat1, lon1, lat2, lon2) {
                const R = 6371000; // Earth's radius in meters
                const dLat = (lat2 - lat1) * Math.PI / 180;
                const dLon = (lon2 - lon1) * Math.PI / 180;
                const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                          Math.sin(dLon/2) * Math.sin(dLon/2);
                const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                return R * c;
            }
            </script>
        </body>
        </html>
        ''', lectures=active_lectures)
    
    return app

# Create the working app instance
working_app = create_working_app()