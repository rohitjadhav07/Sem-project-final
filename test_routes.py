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