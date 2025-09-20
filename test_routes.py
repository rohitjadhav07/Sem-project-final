"""
Simple test routes to debug issues
"""
from flask import Blueprint, jsonify, render_template_string
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.course import Course
from extensions import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

test_bp = Blueprint('test', __name__)

@test_bp.route('/test/simple')
def test_simple():
    """Simple test route"""
    return "✅ Test route working!"

@test_bp.route('/test/db')
def test_db():
    """Test database connection"""
    try:
        from models.user import User
        user_count = User.query.count()
        return f"✅ Database working! Users: {user_count}"
    except Exception as e:
        return f"❌ Database error: {str(e)}"

@test_bp.route('/test/supabase')
def test_supabase():
    """Test Supabase connection and configuration"""
    try:
        # Check environment variables directly
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY')
        supabase_service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        supabase_db_url = os.environ.get('SUPABASE_DATABASE_URL')
        
        # Check if Supabase is available
        try:
            import supabase
            supabase_available = True
        except ImportError:
            supabase_available = False
        
        # Test database connection
        database_status = "Unknown"
        try:
            from models.user import User
            user_count = User.query.count()
            database_status = f"Connected - {user_count} users found"
        except Exception as db_error:
            database_status = f"Error: {str(db_error)}"
        
        result = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Supabase Test - Geo Attendance Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h2>🔍 Supabase Configuration Test</h2>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h5>Environment Variables</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>SUPABASE_URL:</strong> {'✅ Set' if supabase_url else '❌ Missing'}</p>
                                <p><strong>SUPABASE_ANON_KEY:</strong> {'✅ Set' if supabase_anon_key else '❌ Missing'}</p>
                                <p><strong>SUPABASE_SERVICE_ROLE_KEY:</strong> {'✅ Set' if supabase_service_key else '❌ Missing'}</p>
                                <p><strong>SUPABASE_DATABASE_URL:</strong> {'✅ Set' if supabase_db_url else '❌ Missing'}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h5>System Status</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Supabase Library:</strong> {'✅ Available' if supabase_available else '❌ Not installed'}</p>
                                <p><strong>Database Status:</strong> {database_status}</p>
                                <p><strong>Current DB URL:</strong> {os.environ.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="alert alert-info">
                        <h5>🚀 Setup Instructions</h5>
                        <p>To connect to Supabase:</p>
                        <ol>
                            <li>Create a Supabase project at <a href="https://supabase.com" target="_blank">supabase.com</a></li>
                            <li>Get your credentials from Settings → API and Settings → Database</li>
                            <li>Set environment variables in Vercel</li>
                            <li>Redeploy your app</li>
                        </ol>
                        <p><strong>Need help?</strong> Check the complete setup guide in your project files.</p>
                    </div>
                </div>
                
                <div class="mt-4">
                    <a href="/test/db" class="btn btn-primary">Test Database</a>
                    <a href="/" class="btn btn-secondary">Back to Home</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return result
        
        <h3>📋 How to Get Supabase Credentials</h3>
        <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4>🔑 SUPABASE_SERVICE_ROLE_KEY:</h4>
            <p><strong>Location:</strong> Dashboard → Settings → API → Project API keys → <code>service_role</code> <code>secret</code></p>
            
            <h4>🗄️ SUPABASE_DATABASE_URL:</h4>
            <p><strong>Location:</strong> Dashboard → Settings → Database → Connection info → Connection string → URI</p>
            <p><strong>Format:</strong> <code>postgresql://postgres.yourref:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres</code></p>
            <p><strong>⚠️ Important:</strong> Replace <code>PASSWORD</code> with your actual database password!</p>
        </div>
        
        <h3>🚀 Quick Setup Steps</h3>
        <ol>
            <li><strong>Create Supabase project:</strong> <a href="https://supabase.com" target="_blank">supabase.com</a></li>
            <li><strong>Get credentials from:</strong>
                <ul>
                    <li><strong>Settings → API:</strong> Project URL, anon key, service_role key</li>
                    <li><strong>Settings → Database:</strong> Connection string (URI format)</li>
                </ul>
            </li>
            <li><strong>Set in Vercel:</strong> Environment Variables section</li>
            <li><strong>Redeploy:</strong> App will automatically use Supabase</li>
        </ol>
        
        <p><a href="/test/db">Test Database Connection</a> | <a href="/">Back to Home</a></p>
        """
        
        return result
        
    except Exception as e:
        return f"❌ Supabase test error: {str(e)}"

@test_bp.route('/test/student-lectures')
@login_required
def test_student_lectures():
    """Test student lectures without complex template"""
    if current_user.role != 'student':
        return "❌ This test is for students only"
    
    try:
        # Get lectures for enrolled courses
        lectures = Lecture.query.join(Course).join(Enrollment)\
            .filter(
                Enrollment.student_id == current_user.id,
                Enrollment.is_active == True,
                Lecture.is_active == True
            )\
            .all()
        
        result = {
            'student': current_user.username,
            'total_lectures': len(lectures),
            'lectures': []
        }
        
        for lecture in lectures:
            result['lectures'].append({
                'id': lecture.id,
                'title': lecture.title,
                'course': lecture.course.code,
                'status': lecture.status,
                'is_active': lecture.is_active,
                'window_open': lecture.is_attendance_window_open(),
                'scheduled_start': lecture.scheduled_start.isoformat(),
                'location': f"{lecture.latitude}, {lecture.longitude}" if lecture.latitude else "No location"
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@test_bp.route('/test/active-lectures-simple')
@login_required
def test_active_lectures_simple():
    """Simple active lectures page without complex template"""
    if current_user.role != 'student':
        return "❌ This test is for students only"
    
    try:
        # Get active lectures
        current_time = datetime.now(IST)
        today = current_time.date()
        
        lectures = Lecture.query.join(Course).join(Enrollment)\
            .filter(
                Enrollment.student_id == current_user.id,
                Enrollment.is_active == True,
                Lecture.is_active == True,
                db.or_(
                    Lecture.status == 'active',
                    db.and_(
                        Lecture.status == 'scheduled',
                        db.func.date(Lecture.scheduled_start) == today
                    )
                )
            )\
            .order_by(Lecture.scheduled_start)\
            .all()
        
        available_lectures = []
        for lecture in lectures:
            if lecture.is_attendance_window_open():
                available_lectures.append(lecture)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simple Active Lectures Test</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h2>🧪 Simple Active Lectures Test</h2>
                <p><strong>Student:</strong> {current_user.full_name}</p>
                <p><strong>Current Time:</strong> {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
                
                <div class="alert alert-info">
                    <strong>Total Lectures Found:</strong> {len(lectures)}<br>
                    <strong>Available for Check-in:</strong> {len(available_lectures)}
                </div>
                
                <div class="row">
        '''
        
        for lecture in available_lectures:
            html += f'''
                    <div class="col-md-6 mb-3">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6>{lecture.course.code} - {lecture.title}</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Status:</strong> {lecture.status}</p>
                                <p><strong>Start:</strong> {lecture.scheduled_start.strftime('%H:%M')}</p>
                                <p><strong>Location:</strong> {lecture.location_name}</p>
                                <p><strong>Coordinates:</strong> {lecture.latitude}, {lecture.longitude}</p>
                                <p><strong>Radius:</strong> {lecture.geofence_radius}m</p>
                                <button class="btn btn-success" onclick="testCheckin({lecture.id})">
                                    Test Check-in
                                </button>
                            </div>
                        </div>
                    </div>
            '''
        
        if not available_lectures:
            html += '''
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <h5>No Active Lectures</h5>
                            <p>No lectures are currently available for check-in.</p>
                        </div>
                    </div>
            '''
        
        html += '''
                </div>
                
                <div class="mt-4">
                    <a href="/debug/student-lectures" class="btn btn-primary">Debug Info</a>
                    <a href="/student/dashboard" class="btn btn-secondary">Back to Dashboard</a>
                </div>
            </div>
            
            <script>
            function testCheckin(lectureId) {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        fetch('/student/api/checkin', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                lecture_id: lectureId,
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                metadata: JSON.stringify({
                                    accuracy: position.coords.accuracy,
                                    timestamp: new Date().toISOString()
                                })
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('✅ Check-in successful: ' + data.message);
                                location.reload();
                            } else {
                                alert('❌ Check-in failed: ' + data.message);
                            }
                        })
                        .catch(error => {
                            alert('❌ Error: ' + error);
                        });
                    }, function(error) {
                        alert('❌ Location error: ' + error.message);
                    });
                } else {
                    alert('❌ Geolocation not supported');
                }
            }
            </script>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f"❌ Error: {str(e)}"