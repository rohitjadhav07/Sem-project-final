from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.attendance import Attendance
from models.enrollment import Enrollment
from utils.auth import teacher_required
from app import db
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.before_request
@login_required
def require_teacher():
    if current_user.role not in ['teacher', 'admin']:
        flash('Access denied. Teacher privileges required.', 'error')
        return redirect(url_for('main.index'))

@teacher_bp.route('/dashboard')
def dashboard():
    """Teacher dashboard"""
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    recent_lectures = Lecture.query.filter_by(teacher_id=current_user.id).order_by(
        Lecture.created_at.desc()
    ).limit(5).all()
    
    return render_template('teacher/dashboard.html', 
                         courses=courses, 
                         recent_lectures=recent_lectures)

@teacher_bp.route('/courses')
def courses():
    """Manage courses"""
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/courses.html', courses=courses)

@teacher_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    """Course detail page"""
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    lectures = Lecture.query.filter_by(course_id=course_id).order_by(Lecture.scheduled_start.desc()).all()
    enrollments = Enrollment.query.filter_by(course_id=course_id, is_active=True).all()
    
    return render_template('teacher/course_detail.html', 
                         course=course, 
                         lectures=lectures, 
                         enrollments=enrollments)

@teacher_bp.route('/lectures')
def lectures():
    """Manage lectures"""
    lectures = Lecture.query.filter_by(teacher_id=current_user.id).order_by(Lecture.scheduled_start.desc()).all()
    return render_template('teacher/lectures.html', lectures=lectures)

@teacher_bp.route('/lectures/create', methods=['GET', 'POST'])
def create_lecture():
    """Create new lecture with enhanced location security"""
    if request.method == 'POST':
        try:
            data = request.form
            
            # Basic validation
            required_fields = ['title', 'course_id', 'scheduled_start', 'duration', 'latitude', 'longitude']
            for field in required_fields:
                if not data.get(field):
                    flash(f'Missing required field: {field}', 'error')
                    return redirect(url_for('teacher.create_lecture'))
            
            # Parse and validate coordinates
            try:
                latitude = float(data['latitude'])
                longitude = float(data['longitude'])
            except ValueError:
                flash('Invalid coordinates provided', 'error')
                return redirect(url_for('teacher.create_lecture'))
            
            # Validate coordinate ranges
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                flash('Coordinates out of valid range', 'error')
                return redirect(url_for('teacher.create_lecture'))
            
            # Calculate scheduled_end from duration
            scheduled_start = datetime.fromisoformat(data['scheduled_start'])
            duration_minutes = int(data['duration'])
            scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
            
            # Parse location metadata and device info
            location_metadata = data.get('location_metadata', '{}')
            device_info = data.get('device_info', '{}')
            
            # Validate location accuracy if provided
            accuracy = None
            if location_metadata:
                try:
                    import json
                    metadata = json.loads(location_metadata)
                    accuracy = metadata.get('accuracy')
                except:
                    pass
            
            # Check accuracy requirements (relaxed for teacher location setup)
            min_accuracy_required = int(data.get('min_accuracy_required', 20))
            if accuracy and accuracy > 100:
                # Only warn if accuracy is very poor (>100m)
                flash(f'Warning: GPS accuracy (±{accuracy:.1f}m) is poor. Location may not be precise.', 'warning')
            elif accuracy and accuracy > min_accuracy_required:
                # Just log it, don't block
                print(f'GPS accuracy (±{accuracy:.1f}m) exceeds target (±{min_accuracy_required}m) but allowing')
            
            # Generate location hash for integrity verification
            import hashlib
            location_string = f"{latitude:.8f},{longitude:.8f},{scheduled_start.isoformat()}"
            location_hash = hashlib.sha256(location_string.encode()).hexdigest()
            
            # Get client IP address
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            
            # Parse boundary dimensions
            boundary_width = float(data.get('boundary_width', 30))  # meters (East-West)
            boundary_height = float(data.get('boundary_height', 30))  # meters (North-South)
            gps_threshold = int(data.get('gps_accuracy_threshold', 20))
            
            # Create lecture with enhanced location data
            lecture = Lecture(
                title=data['title'],
                description=data.get('description', ''),
                course_id=int(data['course_id']),
                teacher_id=current_user.id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                latitude=round(latitude, 8),  # Precision to ~1mm
                longitude=round(longitude, 8),  # Precision to ~1mm
                location_name=data.get('location_name', ''),
                geofence_type='rectangular',
                gps_accuracy_threshold=gps_threshold,
                boundary_tolerance_m=2.0,
                location_accuracy=accuracy,
                location_metadata=location_metadata,
                location_set_at=datetime.now(IST),
                location_locked=True,  # Lock location immediately upon creation
                location_hash=location_hash,
                location_device_info=device_info,
                location_ip_address=client_ip,
                location_verification_status='verified' if accuracy and accuracy <= 10 else 'pending',
                min_accuracy_required=min_accuracy_required,
                allow_location_updates=bool(data.get('allow_location_updates')),
                location_verification_required=bool(data.get('location_verification_required', True)),
                attendance_window_start=int(data.get('attendance_window_start', 15)) * -1,  # Convert to negative
                attendance_window_end=int(data.get('attendance_window_end', 15))
            )
            location_string = f"{lecture.latitude}:{lecture.longitude}:{lecture.location_set_at.isoformat()}"
            lecture.location_hash = hashlib.sha256(location_string.encode()).hexdigest()
            
            db.session.add(lecture)
            db.session.flush()  # Get lecture ID
            
            # Calculate rectangular boundary corners from center point and dimensions
            from utils.rectangular_geofence import RectangularBoundary
            
            # Create boundary from center and dimensions
            boundary = RectangularBoundary.from_center_and_dimensions(
                latitude, longitude, boundary_width, boundary_height
            )
            
            # Set the boundary on the lecture
            lecture.set_rectangular_boundary(
                boundary.ne,
                boundary.nw,
                boundary.se,
                boundary.sw,
                gps_threshold=gps_threshold,
                tolerance=2.0
            )
            
            db.session.commit()
            
            # Success message with location details
            success_msg = f'Lecture created with {boundary_width}m × {boundary_height}m rectangular boundary!'
            if accuracy:
                success_msg += f' Location accuracy: ±{accuracy:.1f}m'
            
            flash(success_msg, 'success')
            return redirect(url_for('teacher.lecture_detail', lecture_id=lecture.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating lecture: {str(e)}', 'error')
            return redirect(url_for('teacher.create_lecture'))
    
    # GET request - show form
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/create_lecture_enhanced.html', courses=courses)
@teacher_bp.route('/lecture/<int:lecture_id>')
def lecture_detail(lecture_id):
    """Lecture detail page"""
    lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first_or_404()
    attendances = Attendance.query.filter_by(lecture_id=lecture_id).all()
    
    return render_template('teacher/lecture_detail.html', 
                         lecture=lecture, 
                         attendances=attendances)

@teacher_bp.route('/lecture/<int:lecture_id>/start', methods=['POST'])
def start_lecture(lecture_id):
    """Start a lecture"""
    lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first_or_404()
    lecture.start_lecture()
    flash('Lecture started successfully!', 'success')
    return redirect(url_for('teacher.lecture_detail', lecture_id=lecture_id))

@teacher_bp.route('/lecture/<int:lecture_id>/end', methods=['POST'])
def end_lecture(lecture_id):
    """End a lecture"""
    lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first_or_404()
    lecture.end_lecture()
    flash('Lecture ended successfully!', 'success')
    return redirect(url_for('teacher.lecture_detail', lecture_id=lecture_id))

@teacher_bp.route('/attendance/reports')
def attendance_reports():
    """Attendance reports"""
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/attendance_reports.html', courses=courses)

@teacher_bp.route('/attendance/report')
def generate_attendance_report():
    """Generate attendance report based on filters"""
    course_id = request.args.get('course_id')
    date_range = request.args.get('date_range', '30')
    report_type = request.args.get('report_type', 'summary')
    format_type = request.args.get('format', 'html')
    
    # Build query based on filters
    query = Lecture.query.filter_by(teacher_id=current_user.id)
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    # Date filtering
    if date_range.isdigit():
        days_ago = int(date_range)
        start_date = datetime.utcnow() - timedelta(days=days_ago)
        query = query.filter(Lecture.scheduled_start >= start_date)
    
    lectures = query.order_by(Lecture.scheduled_start.desc()).all()
    
    # Generate report data
    report_data = {
        'report_type': report_type,
        'lectures': [],
        'courses': [],
        'stats': {
            'total_lectures': len(lectures),
            'avg_attendance': 0,
            'total_students': 0
        }
    }
    
    if report_type == 'summary':
        # Group by course
        course_stats = {}
        for lecture in lectures:
            course_code = lecture.course.code
            if course_code not in course_stats:
                course_stats[course_code] = {
                    'code': course_code,
                    'name': lecture.course.name,
                    'total_lectures': 0,
                    'total_attendance': 0,
                    'total_students': lecture.course.get_enrollment_count()
                }
            
            stats = lecture.get_attendance_stats()
            course_stats[course_code]['total_lectures'] += 1
            course_stats[course_code]['total_attendance'] += stats['attendance_rate']
        
        for course_code, stats in course_stats.items():
            stats['avg_attendance'] = round(stats['total_attendance'] / stats['total_lectures'], 1) if stats['total_lectures'] > 0 else 0
            report_data['courses'].append(stats)
    
    elif report_type == 'detailed':
        for lecture in lectures:
            stats = lecture.get_attendance_stats()
            report_data['lectures'].append({
                'date': lecture.scheduled_start.isoformat(),
                'course_code': lecture.course.code,
                'title': lecture.title,
                'present': stats['present'],
                'absent': stats['absent'],
                'late': stats['late'],
                'attendance_rate': stats['attendance_rate']
            })
    
    return jsonify(report_data)

@teacher_bp.route('/attendance/mark/<int:lecture_id>')
def mark_attendance(lecture_id):
    """Manual attendance marking page"""
    lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first_or_404()
    enrollments = Enrollment.query.filter_by(course_id=lecture.course_id, is_active=True).all()
    attendances = Attendance.query.filter_by(lecture_id=lecture_id).all()
    attendance_dict = {a.student_id: a for a in attendances}
    
    return render_template('teacher/mark_attendance.html', 
                         lecture=lecture, 
                         enrollments=enrollments,
                         attendance_dict=attendance_dict)

@teacher_bp.route('/lecture/<int:lecture_id>/attendance', methods=['POST'])
def save_attendance(lecture_id):
    """Save bulk attendance updates"""
    lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first_or_404()
    
    data = request.get_json()
    updates = data.get('updates', [])
    
    if not updates:
        return jsonify({'error': 'No updates provided'}), 400
    
    try:
        for update in updates:
            student_id = update.get('student_id')
            status = update.get('status')
            notes = update.get('notes', '')
            
            # Find or create attendance record
            attendance = Attendance.query.filter_by(
                student_id=student_id,
                lecture_id=lecture_id
            ).first()
            
            if not attendance:
                attendance = Attendance(
                    student_id=student_id,
                    lecture_id=lecture_id
                )
                db.session.add(attendance)
            
            # Update attendance
            attendance.status = status
            attendance.notes = notes
            attendance.marked_at = datetime.utcnow()
            attendance.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Attendance saved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save attendance'}), 500

# Removed duplicate route - using the enhanced version below

@teacher_bp.route('/api/location/reset-session', methods=['POST'])
def api_reset_location_session():
    """Reset location confirmation session"""
    try:
        data = request.get_json()
        lecture_id = data.get('lecture_id')
        
        if not lecture_id:
            return jsonify({'success': False, 'message': 'Lecture ID required'})
        
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Check if teacher owns this lecture
        if lecture.course.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Clear session
        from utils.location_security import clear_confirmation_session
        clear_confirmation_session(lecture_id, current_user.id)
        
        return jsonify({'success': True, 'message': 'Session reset successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/api/location/confirm', methods=['POST'])
def api_confirm_location():
    """Confirm location for secure location setting"""
    try:
        data = request.get_json()
        lecture_id = data.get('lecture_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        metadata = data.get('metadata', {})
        
        if not all([lecture_id, latitude, longitude, accuracy]):
            return jsonify({'success': False, 'message': 'Missing required location data'})
        
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Check if teacher owns this lecture
        if lecture.course.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Check if location is already locked
        if lecture.location_locked and not lecture.allow_location_updates:
            return jsonify({'success': False, 'message': 'Location is already locked and cannot be updated'})
        
        # Get or create confirmation session
        from utils.location_security import get_or_create_confirmation_session
        session = get_or_create_confirmation_session(lecture_id, current_user.id)
        
        # Add confirmation to session
        success, message, result = session.add_confirmation(
            float(latitude), float(longitude), float(accuracy), metadata
        )
        
        return jsonify({
            'success': success,
            'message': message,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/api/location/finalize', methods=['POST'])
def api_finalize_location():
    """Finalize and lock the lecture location"""
    try:
        data = request.get_json()
        lecture_id = data.get('lecture_id')
        geofence_radius = data.get('geofence_radius', 50)
        location_name = data.get('location_name', '')
        
        if not lecture_id:
            return jsonify({'success': False, 'message': 'Lecture ID required'})
        
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Check if teacher owns this lecture
        if lecture.course.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Get confirmation session
        from utils.location_security import get_or_create_confirmation_session, clear_confirmation_session
        session = get_or_create_confirmation_session(lecture_id, current_user.id)
        
        if not session.is_complete or not session.final_location:
            return jsonify({'success': False, 'message': 'Location confirmation not complete'})
        
        # Set the final location
        final_loc = session.final_location
        
        # Update lecture with secure location data
        lecture.latitude = final_loc['latitude']
        lecture.longitude = final_loc['longitude']
        lecture.location_accuracy = final_loc['average_accuracy']
        lecture.geofence_radius = geofence_radius
        lecture.location_name = location_name
        lecture.location_set_at = datetime.now(IST)
        lecture.location_locked = True
        lecture.allow_location_updates = False
        lecture.location_confirmation_count = final_loc['confirmation_count']
        lecture.location_hash = final_loc['location_hash']
        lecture.location_verification_status = 'verified'
        lecture.location_last_verified = datetime.now(IST)
        
        # Store session summary as metadata
        import json
        session_summary = session._get_session_summary()
        lecture.location_metadata = json.dumps({
            'final_location': final_loc,
            'session_summary': session_summary,
            'teacher_id': current_user.id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        db.session.commit()
        
        # Clear the session
        clear_confirmation_session(lecture_id, current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Location finalized and secured successfully',
            'location_data': {
                'latitude': lecture.latitude,
                'longitude': lecture.longitude,
                'accuracy': lecture.location_accuracy,
                'geofence_radius': lecture.geofence_radius,
                'confirmation_count': lecture.location_confirmation_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@teacher_bp.route('/location-management')
def location_management():
    """Location management dashboard for teachers"""
    # Get all lectures for this teacher
    lectures = Lecture.query.join(Course).filter(
        Course.teacher_id == current_user.id
    ).order_by(Lecture.scheduled_start.desc()).all()
    
    # Calculate statistics
    total_lectures = len(lectures)
    lectures_with_location = len([l for l in lectures if l.latitude and l.longitude])
    high_accuracy_count = len([l for l in lectures if l.location_accuracy and l.location_accuracy <= 10])
    
    # Calculate average accuracy
    accuracies = [l.location_accuracy for l in lectures if l.location_accuracy]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    
    return render_template('teacher/location_management.html',
                         lectures=lectures,
                         total_lectures=total_lectures,
                         lectures_with_location=lectures_with_location,
                         high_accuracy_count=high_accuracy_count,
                         avg_accuracy=round(avg_accuracy, 1))

@teacher_bp.route('/lecture/<int:lecture_id>/secure-location-setup')
@login_required
@teacher_required
def secure_location_setup(lecture_id):
    """Secure location setup page for lectures"""
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Check if teacher owns this lecture
    if lecture.course.teacher_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # Check if location is already locked
    if lecture.location_locked and not lecture.allow_location_updates:
        flash('Location is already locked for this lecture.', 'warning')
        return redirect(url_for('teacher.lecture_detail', lecture_id=lecture_id))
    
    return render_template('teacher/secure_location_setup.html', lecture=lecture)

@teacher_bp.route('/lecture/<int:lecture_id>/secure-location-setup', methods=['POST'])
@login_required
@teacher_required
def process_secure_location_setup(lecture_id):
    """Process secure location setup"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Check if teacher owns this lecture
        if lecture.course.teacher_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        # Get form data
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        location_name = request.form.get('location_name', '').strip()
        geofence_radius = int(request.form.get('geofence_radius', 25))
        location_metadata = request.form.get('location_metadata', '{}')
        security_data = request.form.get('security_data', '{}')
        
        # Parse security data
        import json
        try:
            security_info = json.loads(security_data)
            metadata_info = json.loads(location_metadata)
        except:
            flash('Invalid location data received.', 'error')
            return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))
        
        # Validate security requirements
        if security_info.get('securityInfo', {}).get('score', 0) < 70:
            flash('Location security score too low. Please try again with better GPS conditions.', 'error')
            return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))
        
        # Validate confirmations
        confirmations = security_info.get('confirmations', [])
        if len(confirmations) < 3:
            flash('Insufficient location confirmations. Please complete all verification steps.', 'error')
            return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))
        
        # Check confirmation consistency (all should be within 5m of each other)
        original_lat = security_info.get('captures', [{}])[0].get('latitude')
        original_lng = security_info.get('captures', [{}])[0].get('longitude')
        
        if original_lat and original_lng:
            from utils.geolocation import calculate_distance
            for conf in confirmations:
                distance = calculate_distance(
                    original_lat, original_lng,
                    conf.get('latitude', 0), conf.get('longitude', 0)
                )
                if distance > 5:  # More than 5m difference
                    flash('Location confirmations are inconsistent. Please ensure you stay in the same location during setup.', 'error')
                    return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))
        
        # Set location with enhanced security
        try:
            # Get device and IP info
            device_info = {
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr,
                'timestamp': datetime.now(IST).isoformat(),
                'confirmations_count': len(confirmations),
                'security_score': security_info.get('securityInfo', {}).get('score', 0)
            }
            
            # Use the secure location setting method
            lecture.set_secure_location(
                latitude=latitude,
                longitude=longitude,
                accuracy=metadata_info.get('finalAccuracy'),
                metadata=location_metadata,
                device_info=device_info
            )
            
            # Set additional fields
            if location_name:
                lecture.location_name = location_name
            lecture.geofence_radius = geofence_radius
            lecture.location_ip_address = request.remote_addr
            lecture.location_verification_status = 'verified'
            lecture.location_confirmation_count = len(confirmations)
            lecture.location_last_verified = datetime.now(IST)
            
            db.session.commit()
            
            flash('Location has been securely set and locked for this lecture!', 'success')
            return redirect(url_for('teacher.lecture_detail', lecture_id=lecture_id))
            
        except ValueError as e:
            flash(f'Location setup failed: {str(e)}', 'error')
            return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error setting up location: {str(e)}', 'error')
        return redirect(url_for('teacher.secure_location_setup', lecture_id=lecture_id))

@teacher_bp.route('/api/lecture/<int:lecture_id>/location-details')
@login_required
@teacher_required
def api_lecture_location_details(lecture_id):
    """API endpoint to get detailed location information for a lecture"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Check if teacher owns this lecture
        if lecture.course.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Parse location metadata
        metadata = {}
        if lecture.location_metadata:
            try:
                import json
                metadata = json.loads(lecture.location_metadata)
            except:
                pass
        
        # Get security info
        security_info = lecture.get_location_security_info()
        
        # Generate HTML content
        html_content = f"""
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-map-pin"></i> Coordinates</h6>
                <p><strong>Latitude:</strong> {lecture.latitude:.8f if lecture.latitude else 'Not set'}</p>
                <p><strong>Longitude:</strong> {lecture.longitude:.8f if lecture.longitude else 'Not set'}</p>
                <p><strong>Geofence Radius:</strong> {lecture.geofence_radius}m</p>
                <p><strong>Location Name:</strong> {lecture.location_name or 'Not specified'}</p>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-shield-alt"></i> Security Information</h6>
                <p><strong>Location Locked:</strong> {'Yes' if lecture.location_locked else 'No'}</p>
                <p><strong>Accuracy:</strong> ±{lecture.location_accuracy:.1f}m</p>
                <p><strong>Set At:</strong> {lecture.location_set_at.strftime('%Y-%m-%d %H:%M:%S') if lecture.location_set_at else 'Not set'}</p>
                <p><strong>Verification Status:</strong> 
                    <span class="badge badge-{'success' if lecture.location_verification_status == 'verified' else 'warning'}">
                        {lecture.location_verification_status or 'Pending'}
                    </span>
                </p>
                <p><strong>Confirmations:</strong> {lecture.location_confirmation_count or 0}</p>
                <p><strong>Integrity Check:</strong> 
                    <span class="badge badge-{'success' if security_info.get('integrity_verified') else 'danger'}">
                        {'Verified' if security_info.get('integrity_verified') else 'Failed'}
                    </span>
                </p>
            </div>
        </div>
        
        <hr>
        
        <div class="row">
            <div class="col-md-12">
                <h6><i class="fas fa-info-circle"></i> Technical Details</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <tr>
                            <td><strong>Precision Level:</strong></td>
                            <td><span class="badge badge-{'success' if security_info.get('precision_level') == 'high' else 'warning' if security_info.get('precision_level') == 'medium' else 'danger'}">{security_info.get('precision_level', 'Unknown').title()}</span></td>
                        </tr>
                        <tr>
                            <td><strong>IP Address:</strong></td>
                            <td>{lecture.location_ip_address or 'Not recorded'}</td>
                        </tr>
                        <tr>
                            <td><strong>Last Verified:</strong></td>
                            <td>{lecture.location_last_verified.strftime('%Y-%m-%d %H:%M:%S') if lecture.location_last_verified else 'Never'}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        """
        
        if metadata:
            html_content += f"""
            <hr>
            <div class="row">
                <div class="col-md-12">
                    <h6><i class="fas fa-code"></i> Metadata</h6>
                    <pre class="bg-light p-2 small">{json.dumps(metadata, indent=2)}</pre>
                </div>
            </div>
            """
        
        return jsonify({'success': True, 'html': html_content})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



# ============================================================================
# RECTANGULAR BOUNDARY API ENDPOINTS
# ============================================================================

@teacher_bp.route('/api/lecture/<int:lecture_id>/set-rectangular-boundary', methods=['POST'])
@login_required
@teacher_required
def set_rectangular_boundary(lecture_id):
    """
    Set rectangular boundary for a lecture
    
    POST /teacher/api/lecture/<id>/set-rectangular-boundary
    Body: {
        "geofence_type": "rectangular",
        "corners": {
            "ne": {"lat": 40.7128, "lon": -74.0060},
            "nw": {"lat": 40.7128, "lon": -74.0070},
            "se": {"lat": 40.7120, "lon": -74.0060},
            "sw": {"lat": 40.7120, "lon": -74.0070}
        },
        "gps_accuracy_threshold": 20,
        "tolerance_m": 2.0
    }
    """
    try:
        lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first()
        
        if not lecture:
            return jsonify({
                'success': False,
                'error': 'Lecture not found or access denied'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract corners
        corners = data.get('corners', {})
        ne = corners.get('ne', {})
        nw = corners.get('nw', {})
        se = corners.get('se', {})
        sw = corners.get('sw', {})
        
        # Validate corners
        required_corners = ['ne', 'nw', 'se', 'sw']
        for corner_name in required_corners:
            corner = corners.get(corner_name, {})
            if 'lat' not in corner or 'lon' not in corner:
                return jsonify({
                    'success': False,
                    'error': f'Missing lat/lon for {corner_name} corner'
                }), 400
        
        # Convert to tuples
        ne_corner = (float(ne['lat']), float(ne['lon']))
        nw_corner = (float(nw['lat']), float(nw['lon']))
        se_corner = (float(se['lat']), float(se['lon']))
        sw_corner = (float(sw['lat']), float(sw['lon']))
        
        # Get thresholds
        gps_threshold = int(data.get('gps_accuracy_threshold', 20))
        tolerance = float(data.get('tolerance_m', 2.0))
        
        # Set rectangular boundary
        lecture.set_rectangular_boundary(
            ne_corner, nw_corner, se_corner, sw_corner,
            gps_threshold, tolerance
        )
        
        # Get boundary for response
        boundary = lecture.get_boundary()
        
        return jsonify({
            'success': True,
            'message': 'Rectangular boundary set successfully',
            'boundary': {
                'area_sqm': round(lecture.boundary_area_sqm, 2),
                'perimeter_m': round(lecture.boundary_perimeter_m, 2),
                'center': {
                    'lat': lecture.boundary_center_lat,
                    'lon': lecture.boundary_center_lon
                }
            },
            'validation': {
                'is_valid_rectangle': True,
                'alignment_check': 'passed',
                'warnings': []
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'validation': {
                'is_valid_rectangle': False,
                'alignment_check': 'failed'
            }
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@teacher_bp.route('/api/lecture/<int:lecture_id>/convert-to-rectangular', methods=['POST'])
@login_required
@teacher_required
def convert_to_rectangular(lecture_id):
    """
    Convert circular geofence to rectangular boundary
    
    POST /teacher/api/lecture/<id>/convert-to-rectangular
    Body: {
        "conversion_method": "square_approximation"
    }
    """
    try:
        lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first()
        
        if not lecture:
            return jsonify({
                'success': False,
                'error': 'Lecture not found or access denied'
            }), 404
        
        # Get conversion suggestion
        conversion_data = lecture.convert_circular_to_rectangular()
        
        return jsonify({
            'success': True,
            'suggested_boundary': conversion_data['suggested_boundary'],
            'original_circular': conversion_data['original_circular']
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@teacher_bp.route('/api/lecture/<int:lecture_id>/boundary-preview', methods=['GET'])
@login_required
@teacher_required
def boundary_preview(lecture_id):
    """
    Get boundary preview data for map visualization
    
    GET /teacher/api/lecture/<id>/boundary-preview
    """
    try:
        lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first()
        
        if not lecture:
            return jsonify({
                'success': False,
                'error': 'Lecture not found or access denied'
            }), 404
        
        response_data = {
            'success': True,
            'geofence_type': lecture.geofence_type or 'circular',
            'lecture_id': lecture.id,
            'lecture_title': lecture.title
        }
        
        if lecture.geofence_type == 'rectangular' and lecture.boundary_coordinates:
            import json
            boundary_data = json.loads(lecture.boundary_coordinates)
            
            response_data['boundary'] = boundary_data
            response_data['visualization_data'] = {
                'map_center': {
                    'lat': lecture.boundary_center_lat,
                    'lon': lecture.boundary_center_lon
                },
                'zoom_level': 18,
                'area_sqm': lecture.boundary_area_sqm,
                'perimeter_m': lecture.boundary_perimeter_m
            }
        else:
            # Circular geofence
            response_data['circular'] = {
                'center': {
                    'lat': lecture.latitude,
                    'lon': lecture.longitude
                },
                'radius': lecture.geofence_radius
            }
            response_data['visualization_data'] = {
                'map_center': {
                    'lat': lecture.latitude,
                    'lon': lecture.longitude
                },
                'zoom_level': 17
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@teacher_bp.route('/api/lecture/<int:lecture_id>/location-details', methods=['GET'])
@login_required
@teacher_required
def get_location_details(lecture_id):
    """
    Get detailed location information for a lecture
    """
    try:
        lecture = Lecture.query.filter_by(id=lecture_id, teacher_id=current_user.id).first()
        
        if not lecture:
            return jsonify({
                'success': False,
                'error': 'Lecture not found or access denied'
            }), 404
        
        details = {
            'success': True,
            'lecture_id': lecture.id,
            'geofence_type': lecture.geofence_type or 'circular',
            'gps_accuracy_threshold': lecture.gps_accuracy_threshold or 20,
            'location_locked': lecture.location_locked,
            'location_accuracy': lecture.location_accuracy
        }
        
        if lecture.geofence_type == 'rectangular':
            details['rectangular'] = {
                'area_sqm': lecture.boundary_area_sqm,
                'perimeter_m': lecture.boundary_perimeter_m,
                'center': {
                    'lat': lecture.boundary_center_lat,
                    'lon': lecture.boundary_center_lon
                },
                'tolerance_m': lecture.boundary_tolerance_m,
                'created_at': lecture.boundary_created_at.isoformat() if lecture.boundary_created_at else None
            }
        else:
            details['circular'] = {
                'center': {
                    'lat': lecture.latitude,
                    'lon': lecture.longitude
                },
                'radius': lecture.geofence_radius
            }
        
        return jsonify(details), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
