"""
Debug routes for testing attendance functionality
"""
from flask import Blueprint, render_template_string, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from models.lecture import Lecture
from models.enrollment import Enrollment
from models.attendance import Attendance
from models.course import Course
from extensions import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/student-lectures')
@login_required
def debug_student_lectures():
    """Debug page to show all lecture information for current student"""
    
    if current_user.role != 'student':
        return "This debug page is only for students"
    
    # Get all lectures for enrolled courses
    lectures = Lecture.query.join(Course).join(Enrollment)\
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.is_active == True
        )\
        .order_by(Lecture.scheduled_start)\
        .all()
    
    current_time = datetime.now(IST)
    
    debug_info = []
    for lecture in lectures:
        # Calculate attendance window
        start_window = lecture.scheduled_start + timedelta(minutes=lecture.attendance_window_start)
        end_window = lecture.scheduled_start + timedelta(minutes=lecture.attendance_window_end)
        window_open = start_window <= current_time <= end_window
        
        # Check existing attendance
        existing_attendance = Attendance.query.filter_by(
            student_id=current_user.id,
            lecture_id=lecture.id
        ).first()
        
        debug_info.append({
            'id': lecture.id,
            'title': lecture.title,
            'course': f"{lecture.course.code} - {lecture.course.name}",
            'status': lecture.status,
            'is_active': lecture.is_active,
            'location_locked': lecture.location_locked,
            'scheduled_start': lecture.scheduled_start.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'window_start': start_window.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'window_end': end_window.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'window_open': window_open,
            'attendance_marked': existing_attendance is not None,
            'attendance_status': existing_attendance.status if existing_attendance else None,
            'latitude': lecture.latitude,
            'longitude': lecture.longitude,
            'geofence_radius': lecture.geofence_radius,
            'location_name': lecture.location_name
        })
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Lecture Debug</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .window-open { background-color: #d4edda; }
            .window-closed { background-color: #f8d7da; }
            .attendance-marked { background-color: #cce5ff; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h2>🔍 Student Lecture Debug - {{ student_name }}</h2>
            <p><strong>Current Time:</strong> {{ current_time }}</p>
            
            <div class="table-responsive">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Course</th>
                            <th>Status</th>
                            <th>Active</th>
                            <th>Location Locked</th>
                            <th>Scheduled Start</th>
                            <th>Window Start</th>
                            <th>Window End</th>
                            <th>Window Open</th>
                            <th>Attendance</th>
                            <th>Location</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lecture in lectures %}
                        <tr class="{% if lecture.window_open %}window-open{% elif lecture.attendance_marked %}attendance-marked{% else %}window-closed{% endif %}">
                            <td>{{ lecture.id }}</td>
                            <td>{{ lecture.title }}</td>
                            <td>{{ lecture.course }}</td>
                            <td>{{ lecture.status }}</td>
                            <td>{{ '✅' if lecture.is_active else '❌' }}</td>
                            <td>{{ '🔒' if lecture.location_locked else '🔓' }}</td>
                            <td>{{ lecture.scheduled_start }}</td>
                            <td>{{ lecture.window_start }}</td>
                            <td>{{ lecture.window_end }}</td>
                            <td>{{ '✅ OPEN' if lecture.window_open else '❌ CLOSED' }}</td>
                            <td>{{ lecture.attendance_status or 'Not marked' }}</td>
                            <td>
                                {{ lecture.location_name }}<br>
                                <small>{{ lecture.latitude }}, {{ lecture.longitude }} ({{ lecture.geofence_radius }}m)</small>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="mt-4">
                <h4>Legend:</h4>
                <div class="row">
                    <div class="col-md-4">
                        <div class="p-2 window-open">✅ Attendance Window Open</div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-2 attendance-marked">📝 Attendance Already Marked</div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-2 window-closed">❌ Window Closed</div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/student/active-lectures" class="btn btn-primary">Go to Active Lectures</a>
                <a href="/student/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html, 
                                lectures=debug_info, 
                                student_name=current_user.full_name,
                                current_time=current_time.strftime('%Y-%m-%d %H:%M:%S %Z'))

@debug_bp.route('/debug/test-location')
def debug_test_location():
    """Test location page for debugging GPS"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Location Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h2>📍 Location Test</h2>
            <div id="location-info" class="alert alert-info">
                Click "Get Location" to test GPS functionality
            </div>
            <button onclick="getLocation()" class="btn btn-primary">Get My Location</button>
            
            <div class="mt-4">
                <h4>Sample Lecture Locations:</h4>
                <ul class="list-group">
                    <li class="list-group-item">Room 101: 19.0760, 72.8777 (50m radius)</li>
                    <li class="list-group-item">Room 102: 19.0765, 72.8780 (40m radius)</li>
                    <li class="list-group-item">Room 103: 19.0755, 72.8785 (60m radius)</li>
                </ul>
            </div>
        </div>
        
        <script>
        function getLocation() {
            const info = document.getElementById('location-info');
            
            if (!navigator.geolocation) {
                info.innerHTML = '❌ Geolocation is not supported by this browser.';
                info.className = 'alert alert-danger';
                return;
            }
            
            info.innerHTML = '🔄 Getting location...';
            info.className = 'alert alert-warning';
            
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const accuracy = position.coords.accuracy;
                    
                    info.innerHTML = `
                        ✅ <strong>Location Found!</strong><br>
                        📍 Latitude: ${lat}<br>
                        📍 Longitude: ${lon}<br>
                        🎯 Accuracy: ${accuracy} meters<br>
                        🕒 Timestamp: ${new Date(position.timestamp).toLocaleString()}
                    `;
                    info.className = 'alert alert-success';
                },
                function(error) {
                    let message = '❌ Error getting location: ';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message += 'Permission denied by user.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message += 'Location information unavailable.';
                            break;
                        case error.TIMEOUT:
                            message += 'Location request timed out.';
                            break;
                        default:
                            message += 'Unknown error occurred.';
                            break;
                    }
                    info.innerHTML = message;
                    info.className = 'alert alert-danger';
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        }
        </script>
    </body>
    </html>
    '''
    return html