"""
Simple active lectures functionality without complex templates
"""
from flask import Blueprint, render_template_string, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from models.enrollment import Enrollment
from models.lecture import Lecture
from models.attendance import Attendance
from models.course import Course
from utils.auth import student_required
from extensions import db

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

simple_bp = Blueprint('simple', __name__)

@simple_bp.route('/student/active-lectures-simple')
@login_required
@student_required
def active_lectures_simple():
    """Simple active lectures page that works"""
    try:
        # Get current time in IST
        current_time = datetime.now(IST)
        today = current_time.date()
        
        # Get lectures for enrolled courses
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
        
        # Filter lectures where attendance window is open
        available_lectures = []
        upcoming_lectures = []
        completed_lectures = []
        
        for lecture in lectures:
            # Check if attendance already marked
            existing_attendance = Attendance.query.filter_by(
                student_id=current_user.id,
                lecture_id=lecture.id
            ).first()
            
            if existing_attendance:
                completed_lectures.append({
                    'lecture': lecture,
                    'attendance': existing_attendance,
                    'status': 'attended'
                })
            elif lecture.is_attendance_window_open():
                available_lectures.append(lecture)
            else:
                # Check if window will open later today
                start_window = lecture.scheduled_start + timedelta(minutes=lecture.attendance_window_start)
                if current_time < start_window:
                    upcoming_lectures.append({
                        'lecture': lecture,
                        'opens_at': start_window
                    })
                else:
                    completed_lectures.append({
                        'lecture': lecture,
                        'attendance': None,
                        'status': 'missed'
                    })
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Active Lectures - {{ student_name }}</title>
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
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text">{{ student_name }}</span>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row">
                    <div class="col-12">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <div>
                                <h2><i class="fas fa-broadcast-tower"></i> Active Lectures</h2>
                                <p class="text-muted">Current time: {{ current_time }}</p>
                            </div>
                            <div>
                                <button class="btn btn-outline-primary" onclick="location.reload()">
                                    <i class="fas fa-sync-alt"></i> Refresh
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Available for Check-in -->
                {% if available_lectures %}
                <div class="row mb-4">
                    <div class="col-12">
                        <h4 class="text-success"><i class="fas fa-check-circle"></i> Available for Check-in ({{ available_lectures|length }})</h4>
                    </div>
                    {% for lecture in available_lectures %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0">{{ lecture.course.code }} - {{ lecture.title }}</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Course:</strong> {{ lecture.course.name }}</p>
                                <p><strong>Time:</strong> {{ lecture.scheduled_start.strftime('%H:%M') }} - {{ lecture.scheduled_end.strftime('%H:%M') }}</p>
                                <p><strong>Location:</strong> {{ lecture.location_name }}</p>
                                <p><strong>Status:</strong> <span class="badge bg-success">{{ lecture.status.title() }}</span></p>
                                
                                <div class="d-grid gap-2">
                                    <button class="btn btn-success" onclick="startCheckin({{ lecture.id }}, '{{ lecture.title }}', {{ lecture.latitude }}, {{ lecture.longitude }}, {{ lecture.geofence_radius }})">
                                        <i class="fas fa-map-marker-alt"></i> Check In Now
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <!-- Upcoming Lectures -->
                {% if upcoming_lectures %}
                <div class="row mb-4">
                    <div class="col-12">
                        <h4 class="text-warning"><i class="fas fa-clock"></i> Upcoming Today ({{ upcoming_lectures|length }})</h4>
                    </div>
                    {% for item in upcoming_lectures %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0">{{ item.lecture.course.code }} - {{ item.lecture.title }}</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Course:</strong> {{ item.lecture.course.name }}</p>
                                <p><strong>Starts:</strong> {{ item.lecture.scheduled_start.strftime('%H:%M') }}</p>
                                <p><strong>Check-in opens:</strong> {{ item.opens_at.strftime('%H:%M') }}</p>
                                <div class="alert alert-info">
                                    <small><i class="fas fa-info-circle"></i> Check-in will be available starting {{ item.opens_at.strftime('%H:%M') }}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <!-- Completed/Attended -->
                {% if completed_lectures %}
                <div class="row mb-4">
                    <div class="col-12">
                        <h4 class="text-secondary"><i class="fas fa-history"></i> Today's Completed ({{ completed_lectures|length }})</h4>
                    </div>
                    {% for item in completed_lectures %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-secondary">
                            <div class="card-header bg-light">
                                <h6 class="mb-0">{{ item.lecture.course.code }} - {{ item.lecture.title }}</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Course:</strong> {{ item.lecture.course.name }}</p>
                                <p><strong>Time:</strong> {{ item.lecture.scheduled_start.strftime('%H:%M') }} - {{ item.lecture.scheduled_end.strftime('%H:%M') }}</p>
                                {% if item.attendance %}
                                    <div class="alert alert-success">
                                        <i class="fas fa-check"></i> <strong>Attended</strong><br>
                                        <small>Marked at: {{ item.attendance.marked_at.strftime('%H:%M') if item.attendance.marked_at else 'N/A' }}</small>
                                    </div>
                                {% else %}
                                    <div class="alert alert-danger">
                                        <i class="fas fa-times"></i> <strong>Missed</strong><br>
                                        <small>Attendance window closed</small>
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <!-- No lectures message -->
                {% if not available_lectures and not upcoming_lectures and not completed_lectures %}
                <div class="row">
                    <div class="col-12">
                        <div class="alert alert-info text-center">
                            <i class="fas fa-info-circle fa-3x mb-3"></i>
                            <h5>No Lectures Today</h5>
                            <p>There are no lectures scheduled for today in your enrolled courses.</p>
                            <button class="btn btn-outline-primary" onclick="location.reload()">
                                <i class="fas fa-sync-alt"></i> Refresh
                            </button>
                        </div>
                    </div>
                </div>
                {% endif %}
                
                <div class="row mt-4">
                    <div class="col-12">
                        <a href="/student/dashboard" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back to Dashboard
                        </a>
                        <a href="/test/student-lectures" class="btn btn-info">
                            <i class="fas fa-bug"></i> Debug Info
                        </a>
                    </div>
                </div>
            </div>
            
            <!-- Check-in Modal -->
            <div class="modal fade" id="checkinModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Check-in to Lecture</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="checkinStatus" class="alert alert-info">
                                <div class="d-flex align-items-center">
                                    <div class="spinner-border spinner-border-sm me-2"></div>
                                    <span>Getting your location...</span>
                                </div>
                            </div>
                            <div id="lectureDetails"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" id="confirmCheckin" disabled>
                                <i class="fas fa-check"></i> Confirm Check-in
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
            let currentLecture = null;
            let userLocation = null;
            
            function startCheckin(lectureId, title, lat, lon, radius) {
                currentLecture = {
                    id: lectureId,
                    title: title,
                    latitude: lat,
                    longitude: lon,
                    geofence_radius: radius
                };
                
                const modal = new bootstrap.Modal(document.getElementById('checkinModal'));
                modal.show();
                
                document.getElementById('lectureDetails').innerHTML = `
                    <h6>${title}</h6>
                    <p><strong>Required Distance:</strong> Within ${radius} meters</p>
                `;
                
                // Get location
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            userLocation = {
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                accuracy: position.coords.accuracy
                            };
                            
                            const distance = calculateDistance(
                                userLocation.latitude, userLocation.longitude,
                                currentLecture.latitude, currentLecture.longitude
                            );
                            
                            document.getElementById('lectureDetails').innerHTML += `
                                <p><strong>Your Distance:</strong> ${Math.round(distance)} meters</p>
                                <p><strong>GPS Accuracy:</strong> ${Math.round(userLocation.accuracy)} meters</p>
                            `;
                            
                            if (distance <= currentLecture.geofence_radius) {
                                document.getElementById('checkinStatus').className = 'alert alert-success';
                                document.getElementById('checkinStatus').innerHTML = 
                                    '<i class="fas fa-check-circle"></i> <strong>Perfect!</strong> You are within the lecture area.';
                                document.getElementById('confirmCheckin').disabled = false;
                            } else {
                                document.getElementById('checkinStatus').className = 'alert alert-warning';
                                document.getElementById('checkinStatus').innerHTML = 
                                    `<i class="fas fa-exclamation-triangle"></i> <strong>Too far!</strong> You need to be within ${currentLecture.geofence_radius}m.`;
                            }
                        },
                        function(error) {
                            document.getElementById('checkinStatus').className = 'alert alert-danger';
                            document.getElementById('checkinStatus').innerHTML = 
                                '<i class="fas fa-times-circle"></i> <strong>Error:</strong> Unable to get your location.';
                        },
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        }
                    );
                }
            }
            
            document.getElementById('confirmCheckin').addEventListener('click', function() {
                if (!userLocation || !currentLecture) return;
                
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Checking in...';
                
                fetch('/student/api/checkin', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        lecture_id: currentLecture.id,
                        latitude: userLocation.latitude,
                        longitude: userLocation.longitude,
                        metadata: JSON.stringify({
                            accuracy: userLocation.accuracy,
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
                        this.disabled = false;
                        this.innerHTML = '<i class="fas fa-check"></i> Confirm Check-in';
                    }
                })
                .catch(error => {
                    alert('❌ Error: ' + error);
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-check"></i> Confirm Check-in';
                });
            });
            
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
        '''
        
        return render_template_string(html,
                                    student_name=current_user.full_name,
                                    current_time=current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                                    available_lectures=available_lectures,
                                    upcoming_lectures=upcoming_lectures,
                                    completed_lectures=completed_lectures)
        
    except Exception as e:
        return f"❌ Error loading active lectures: {str(e)}"