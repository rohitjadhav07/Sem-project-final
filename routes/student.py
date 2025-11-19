from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
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

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Student dashboard"""
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()
    
    # Get upcoming lectures
    upcoming_lectures = Lecture.query.join(Course).join(Enrollment)\
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.is_active == True,
            Lecture.scheduled_start > datetime.now(IST),
            Lecture.is_active == True
        )\
        .order_by(Lecture.scheduled_start)\
        .limit(5)\
        .all()
    
    # Get active lectures count (for dashboard display)
    today = datetime.now(IST).date()
    active_lectures_count = Lecture.query.join(Course).join(Enrollment)\
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
        .count()
    
    # Get recent attendance
    recent_attendance = Attendance.query.filter_by(student_id=current_user.id)\
        .join(Lecture)\
        .order_by(Attendance.marked_at.desc())\
        .limit(10)\
        .all()
    
    # Calculate overall attendance percentage
    total_lectures = Attendance.query.filter_by(student_id=current_user.id).count()
    present_lectures = Attendance.query.filter_by(
        student_id=current_user.id,
        status='present'
    ).count()
    
    attendance_percentage = (present_lectures / total_lectures * 100) if total_lectures > 0 else 0
    
    return render_template('student/dashboard.html',
                         enrollments=enrollments,
                         upcoming_lectures=upcoming_lectures,
                         recent_attendance=recent_attendance,
                         attendance_percentage=round(attendance_percentage, 2),
                         active_lectures_count=active_lectures_count)

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    """Student courses page"""
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()
    
    # Also get available courses for enrollment
    available_courses = Course.query.filter_by(is_active=True).all()
    enrolled_course_ids = [e.course_id for e in enrollments]
    available_courses = [c for c in available_courses if c.id not in enrolled_course_ids]
    
    return render_template('student/courses.html', 
                         enrollments=enrollments,
                         available_courses=available_courses)

@student_bp.route('/course/<int:course_id>')
@login_required
@student_required
def course_detail(course_id):
    """Course detail page for student"""
    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
        is_active=True
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'error')
        return redirect(url_for('student.dashboard'))
    
    course = enrollment.course
    
    # Get lectures for this course
    lectures = Lecture.query.filter_by(
        course_id=course_id,
        is_active=True
    ).order_by(Lecture.scheduled_start.desc()).all()
    
    # Get attendance for this course
    attendances = Attendance.query.filter_by(student_id=current_user.id)\
        .join(Lecture)\
        .filter(Lecture.course_id == course_id)\
        .all()
    
    # Create attendance dictionary for easy lookup
    attendance_dict = {att.lecture_id: att for att in attendances}
    
    return render_template('student/course_detail.html',
                         course=course,
                         enrollment=enrollment,
                         lectures=lectures,
                         attendances=attendances,
                         attendance_dict=attendance_dict)

@student_bp.route('/active-lectures')
# @student_bp.route('/active-lectures')
# @student_bp.route('/active-lectures')
@login_required
@student_required
def active_lectures():
    """Active lectures for check-in"""
    try:
        from datetime import datetime, date
        
        # Get current time in IST
        current_time = datetime.now(IST)
        today = current_time.date()
        
        # Get all lectures for enrolled courses
        lectures = []
        try:
            # Simple query to get lectures
            all_lectures = Lecture.query.filter(
                Lecture.is_active == True,
                Lecture.status.in_(['active', 'scheduled'])
            ).all()
            
            # Filter for enrolled courses
            enrollments = Enrollment.query.filter_by(
                student_id=current_user.id,
                is_active=True
            ).all()
            enrolled_course_ids = [e.course_id for e in enrollments]
            
            lectures = [l for l in all_lectures if l.course_id in enrolled_course_ids]
            
        except Exception as query_error:
            print(f"Query error: {query_error}")
            lectures = []
        
        # Categorize lectures
        available_lectures = []  # Can check in now
        upcoming_lectures = []   # Scheduled for later today
        completed_lectures = []  # Already attended or window closed
        
        for lecture in lectures:
            try:
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
                elif hasattr(lecture, 'is_attendance_window_open') and lecture.is_attendance_window_open():
                    available_lectures.append(lecture)
                else:
                    # Check if window will open later today
                    if lecture.scheduled_start.date() == today:
                        start_window = lecture.scheduled_start + timedelta(minutes=getattr(lecture, 'attendance_window_start', -15))
                        if current_time < start_window:
                            lecture.checkin_opens_at = start_window
                            upcoming_lectures.append(lecture)
                        else:
                            completed_lectures.append({
                                'lecture': lecture,
                                'attendance': None,
                                'status': 'missed'
                            })
            except Exception as lecture_error:
                print(f"Error processing lecture {lecture.id}: {lecture_error}")
                continue
        
        return render_template('student/active_lectures_enhanced.html', 
                             lectures=available_lectures,
                             upcoming_lectures=upcoming_lectures,
                             completed_lectures=completed_lectures)
                             
    except Exception as e:
        print(f"Active lectures error: {e}")
        # Return a simple error page
        from flask import render_template_string
        return render_template_string('''
        <div class="container mt-5">
            <div class="alert alert-warning">
                <h4>⚠️ Active Lectures Temporarily Unavailable</h4>
                <p>We're having trouble loading the active lectures. Please try again in a moment.</p>
                <p><strong>Error:</strong> {{ error }}</p>
                <a href="{{ url_for('student.dashboard') }}" class="btn btn-primary">Back to Dashboard</a>
            </div>
        </div>
        ''', error=str(e))

@student_bp.route('/api/checkin', methods=['POST'])
@login_required
@student_required
def api_checkin():
    """Enhanced GPS-based student check-in with rectangular boundary support"""
    try:
        data = request.get_json()
        lecture_id = data.get('lecture_id')
        student_lat = data.get('latitude')
        student_lon = data.get('longitude')
        auto_checkin = data.get('auto_checkin', False)
        
        # Extract GPS metadata
        metadata = data.get('metadata', {})
        gps_accuracy = metadata.get('accuracy', 999)
        
        if not all([lecture_id, student_lat, student_lon]):
            return jsonify({
                'success': False,
                'message': 'Missing required location data'
            })
        
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            return jsonify({
                'success': False,
                'message': 'Lecture not found'
            })
        
        # Validate lecture has location set
        if not lecture.latitude or not lecture.longitude:
            return jsonify({
                'success': False,
                'message': 'Lecture location not configured'
            })
        
        # Check if student is enrolled
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=lecture.course_id,
            is_active=True
        ).first()
        
        if not enrollment:
            return jsonify({
                'success': False,
                'message': 'You are not enrolled in this course'
            })
        
        # Check if already marked
        existing = Attendance.query.filter_by(
            student_id=current_user.id,
            lecture_id=lecture_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Attendance already marked for this lecture'
            })
        
        # Calculate distance from lecture center first (for smart validation)
        import math
        def calculate_distance(lat1, lon1, lat2, lon2):
            R = 6371000
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon/2) * math.sin(delta_lon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        distance_from_center = calculate_distance(
            float(student_lat), float(student_lon),
            float(lecture.latitude), float(lecture.longitude)
        )
        
        # Smart GPS accuracy validation based on distance
        gps_threshold = lecture.gps_accuracy_threshold or 20
        
        # If student is very close to lecture center (< 10m), accept any GPS accuracy
        # This handles cases where student is clearly in the classroom
        if distance_from_center < 10:
            # Student is obviously in the classroom, accept even with poor GPS
            print(f"Smart validation: Student very close ({distance_from_center:.1f}m), accepting despite GPS accuracy {gps_accuracy:.1f}m")
        # If student is reasonably close (10-30m), require moderate GPS accuracy (< 50m)
        elif distance_from_center < 30 and gps_accuracy > 50:
            return jsonify({
                'success': False,
                'message': f'GPS accuracy too low: {gps_accuracy:.1f}m (required: ≤50m for your distance)',
                'validation': {
                    'gps_accuracy_acceptable': False,
                    'required_accuracy': 50,
                    'current_accuracy': gps_accuracy,
                    'distance_from_center': round(distance_from_center, 1)
                },
                'guidance': 'Move to an area with better GPS signal (outdoors or near windows)'
            })
        # If student is at edge of boundary (30-50m), require good GPS accuracy
        elif distance_from_center >= 30 and gps_accuracy > gps_threshold:
            return jsonify({
                'success': False,
                'message': f'GPS accuracy too low: {gps_accuracy:.1f}m (required: ≤{gps_threshold}m)',
                'validation': {
                    'gps_accuracy_acceptable': False,
                    'required_accuracy': gps_threshold,
                    'current_accuracy': gps_accuracy,
                    'distance_from_center': round(distance_from_center, 1)
                },
                'guidance': 'Move to an area with better GPS signal (outdoors or near windows)'
            })
        
        # Use enhanced geofence validation (supports both circular and rectangular)
        validation_result = lecture.is_within_geofence_enhanced(
            float(student_lat),
            float(student_lon),
            gps_accuracy
        )
        
        if not validation_result['within_geofence']:
            # Build error response based on validation method
            error_response = {
                'success': False,
                'validation': {
                    'method': validation_result['method'],
                    'inside_boundary': False,
                    'gps_accuracy_acceptable': True
                }
            }
            
            if validation_result['method'] == 'rectangular':
                distance_to_edge = validation_result.get('distance_to_edge', 0)
                nearest_edge = validation_result.get('details', {}).get('nearest_edge', 'boundary')
                
                error_response['message'] = f'You are outside the classroom boundary ({distance_to_edge:.1f}m from {nearest_edge} edge)'
                error_response['validation']['distance_to_edge'] = round(distance_to_edge, 1)
                error_response['validation']['nearest_edge'] = nearest_edge
                error_response['guidance'] = f'Move closer to the classroom (approximately {distance_to_edge:.1f}m toward {nearest_edge})'
            else:
                # Circular validation
                distance = validation_result.get('distance', 0)
                radius = validation_result.get('radius', 50)
                
                error_response['message'] = f'You are {distance:.1f}m away from the lecture location. Required: within {radius}m'
                error_response['validation']['distance'] = round(distance, 1)
                error_response['validation']['required_radius'] = radius
                error_response['guidance'] = f'Move {distance - radius:.1f}m closer to the lecture location'
            
            return jsonify(error_response)
        
        # distance_from_center already calculated above
        
        # Mark attendance with enhanced metadata
        attendance = Attendance(
            student_id=current_user.id,
            lecture_id=lecture_id,
            status='present',
            marked_at=datetime.now(IST),
            student_latitude=float(student_lat),
            student_longitude=float(student_lon),
            distance_from_lecture=distance_from_center,
            # Enhanced rectangular boundary metadata
            validation_method=validation_result['method'],
            distance_to_boundary_edge=validation_result.get('distance_to_edge', 0),
            gps_accuracy_at_checkin=gps_accuracy,
            boundary_intersection_status='inside' if validation_result['within_geofence'] else 'outside',
            location_uncertainty_radius=gps_accuracy,
            notes=f"{'Auto-' if auto_checkin else ''}Check-in via {validation_result['method']} validation"
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        # Determine if smart validation was used
        smart_validation_used = distance_from_center < 10 and gps_accuracy > gps_threshold
        
        # Build success response
        success_message = f"{'Auto-' if auto_checkin else ''}Attendance marked successfully!"
        if smart_validation_used:
            success_message += f" (Smart validation: {distance_from_center:.1f}m from center)"
        
        success_response = {
            'success': True,
            'message': success_message,
            'validation': {
                'method': validation_result['method'],
                'inside_boundary': True,
                'gps_accuracy_acceptable': True,
                'tolerance_applied': validation_result.get('tolerance_applied', False),
                'smart_validation_used': smart_validation_used,
                'distance_from_center': round(distance_from_center, 1)
            },
            'auto_checkin': auto_checkin,
            'timestamp': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        }
        
        if validation_result['method'] == 'rectangular':
            success_response['validation']['distance_to_edge'] = round(validation_result.get('distance_to_edge', 0), 1)
        else:
            success_response['distance'] = round(distance_from_center, 1)
        
        return jsonify(success_response)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@student_bp.route('/enroll')
@login_required
@student_required
def enroll():
    """Course enrollment page (by code)"""
    return render_template('student/enroll.html')

@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
@student_required
def enroll_course(course_id):
    """Enroll in a course"""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Check if already enrolled
        existing_enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id
        ).first()
        
        if existing_enrollment:
            if existing_enrollment.is_active:
                flash('You are already enrolled in this course.', 'warning')
            else:
                # Reactivate enrollment
                existing_enrollment.is_active = True
                existing_enrollment.enrollment_date = datetime.now(IST)
                db.session.commit()
                flash(f'Successfully re-enrolled in {course.name}!', 'success')
        else:
            # Create new enrollment
            enrollment = Enrollment(
                student_id=current_user.id,
                course_id=course_id,
                enrollment_date=datetime.now(IST),
                is_active=True
            )
            db.session.add(enrollment)
            db.session.commit()
            flash(f'Successfully enrolled in {course.name}!', 'success')
        
        return redirect(url_for('student.courses'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error enrolling in course: {str(e)}', 'error')
        return redirect(url_for('student.browse_courses'))

@student_bp.route('/unenroll/<int:course_id>', methods=['POST'])
@login_required
@student_required
def unenroll_course(course_id):
    """Unenroll from a course"""
    try:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
            is_active=True
        ).first_or_404()
        
        enrollment.is_active = False
        db.session.commit()
        
        flash(f'Successfully unenrolled from {enrollment.course.name}.', 'success')
        return redirect(url_for('student.courses'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error unenrolling from course: {str(e)}', 'error')
        return redirect(url_for('student.courses'))

@student_bp.route('/browse-courses')
@login_required
@student_required
def browse_courses():
    """Browse available courses page"""
    # Get all available courses
    available_courses = Course.query.filter_by(is_active=True).all()
    
    # Get already enrolled course IDs
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()]
    
    # Filter out already enrolled courses
    available_courses = [c for c in available_courses if c.id not in enrolled_course_ids]
    
    return render_template('student/browse_courses.html', courses=available_courses)

@student_bp.route('/attendance-history')
@login_required
@student_required
def attendance_history():
    """Student attendance history"""
    # Get all attendance records for the student
    attendances = Attendance.query.filter_by(student_id=current_user.id)\
        .join(Lecture)\
        .join(Course)\
        .order_by(Lecture.scheduled_start.desc())\
        .all()
    
    # Calculate statistics
    total_lectures = len(attendances)
    present_count = len([a for a in attendances if a.status == 'present'])
    absent_count = len([a for a in attendances if a.status == 'absent'])
    late_count = len([a for a in attendances if a.status == 'late'])
    
    attendance_percentage = (present_count / total_lectures * 100) if total_lectures > 0 else 0
    
    # Group by course
    course_stats = {}
    for attendance in attendances:
        course_code = attendance.lecture.course.code
        if course_code not in course_stats:
            course_stats[course_code] = {
                'course': attendance.lecture.course,
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0
            }
        
        course_stats[course_code]['total'] += 1
        course_stats[course_code][attendance.status] += 1
    
    # Calculate percentages for each course
    for course_code, stats in course_stats.items():
        stats['percentage'] = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    return render_template('student/attendance_history.html',
                         attendances=attendances,
                         total_lectures=total_lectures,
                         present_count=present_count,
                         absent_count=absent_count,
                         late_count=late_count,
                         attendance_percentage=round(attendance_percentage, 2),
                         course_stats=course_stats)

@student_bp.route('/lecture/<int:lecture_id>')
@login_required
@student_required
def lecture_detail(lecture_id):
    """Student lecture detail page"""
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=lecture.course_id,
        is_active=True
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Check if attendance already marked
    attendance = Attendance.query.filter_by(
        student_id=current_user.id,
        lecture_id=lecture_id
    ).first()
    
    return render_template('student/lecture_detail.html', 
                         lecture=lecture, 
                         attendance=attendance)

@student_bp.route('/lecture/<int:lecture_id>/enhanced-checkin')
@login_required
@student_required
def enhanced_checkin(lecture_id):
    """Enhanced secure check-in page"""
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=lecture.course_id,
        is_active=True
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Check if attendance already marked
    existing_attendance = Attendance.query.filter_by(
        student_id=current_user.id,
        lecture_id=lecture_id
    ).first()
    
    if existing_attendance:
        flash('Attendance already marked for this lecture.', 'info')
        return redirect(url_for('student.active_lectures'))
    
    # Check if lecture has location set and locked
    if not lecture.latitude or not lecture.longitude or not lecture.location_locked:
        flash('Lecture location is not properly configured. Please contact your teacher.', 'error')
        return redirect(url_for('student.active_lectures'))
    
    # Check if attendance window is open
    if not lecture.is_attendance_window_open():
        flash('Attendance window is not currently open for this lecture.', 'warning')
        return redirect(url_for('student.active_lectures'))
    
    return render_template('student/enhanced_checkin.html', lecture=lecture)

@student_bp.route('/debug-lectures')
@login_required
@student_required
def debug_lectures():
    """Debug route to check lecture availability"""
    try:
        from datetime import datetime
        
        # Get enrollments
        enrollments = Enrollment.query.filter_by(
            student_id=current_user.id,
            is_active=True
        ).all()
        
        # Get all lectures
        all_lectures = Lecture.query.filter_by(is_active=True).all()
        
        # Get lectures for enrolled courses
        enrolled_course_ids = [e.course_id for e in enrollments]
        enrolled_lectures = [l for l in all_lectures if l.course_id in enrolled_course_ids]
        
        debug_info = {
            'student_id': current_user.id,
            'enrollments_count': len(enrollments),
            'enrolled_courses': [{'id': e.course_id, 'name': e.course.name} for e in enrollments],
            'total_lectures': len(all_lectures),
            'enrolled_lectures_count': len(enrolled_lectures),
            'current_time': datetime.now(IST).isoformat(),
            'lectures': []
        }
        
        for lecture in enrolled_lectures:
            # Check attendance window
            window_open = lecture.is_attendance_window_open()
            
            # Check if attendance already marked
            existing_attendance = Attendance.query.filter_by(
                student_id=current_user.id,
                lecture_id=lecture.id
            ).first()
            
            debug_info['lectures'].append({
                'id': lecture.id,
                'title': lecture.title,
                'course': lecture.course.code,
                'status': lecture.status,
                'is_active': lecture.is_active,
                'scheduled_start': lecture.scheduled_start.isoformat(),
                'scheduled_end': lecture.scheduled_end.isoformat(),
                'window_open': window_open,
                'attendance_marked': existing_attendance is not None,
                'has_location': bool(lecture.latitude and lecture.longitude)
            })
        
        return f"<pre>{debug_info}</pre>"
        
    except Exception as e:
        return f"<pre>Error: {str(e)}</pre>"

@student_bp.route('/lectures/active')
@login_required
@student_required
def lectures_active():
    """API endpoint for active lectures (used by AJAX)"""
    return api_active_lectures()

@student_bp.route('/api/active-lectures')
@login_required
@student_required
def api_active_lectures():
    """API endpoint to get active lectures for AJAX calls"""
    try:
        from datetime import datetime, date
        
        # Get current time
        current_time = datetime.now(IST)
        today = current_time.date()
        
        # Get all lectures for enrolled courses (simplified query)
        enrollments = Enrollment.query.filter_by(
            student_id=current_user.id,
            is_active=True
        ).all()
        
        enrolled_course_ids = [e.course_id for e in enrollments]
        
        if not enrolled_course_ids:
            return jsonify({
                'success': True,
                'lectures': [],
                'count': 0,
                'message': 'No enrolled courses found'
            })
        
        # Get lectures for today and active lectures
        lectures = Lecture.query.filter(
            Lecture.course_id.in_(enrolled_course_ids),
            Lecture.is_active == True,
            db.or_(
                Lecture.status == 'active',
                db.and_(
                    Lecture.status == 'scheduled',
                    db.func.date(Lecture.scheduled_start) == today
                )
            )
        ).order_by(Lecture.scheduled_start).all()
        
        # Process lectures
        available_lectures = []
        debug_info = []
        
        for lecture in lectures:
            # Check if attendance already marked
            existing_attendance = Attendance.query.filter_by(
                student_id=current_user.id,
                lecture_id=lecture.id
            ).first()
            
            # Check attendance window
            window_open = lecture.is_attendance_window_open()
            
            # Add to debug info
            debug_info.append({
                'id': lecture.id,
                'title': lecture.title,
                'status': lecture.status,
                'scheduled_start': lecture.scheduled_start.isoformat(),
                'scheduled_end': lecture.scheduled_end.isoformat(),
                'window_start': getattr(lecture, 'attendance_window_start', -30),
                'window_end': getattr(lecture, 'attendance_window_end', 60),
                'is_window_open': window_open,
                'attendance_marked': existing_attendance is not None,
                'current_time': current_time.isoformat()
            })
            
            # Add to available lectures if window is open and no attendance marked
            if not existing_attendance and window_open:
                # Ensure times are timezone-aware for proper conversion
                start_time = lecture.scheduled_start
                end_time = lecture.scheduled_end
                
                # If times are naive, assume they're in IST
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=IST)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=IST)
                
                lecture_data = {
                    'id': lecture.id,
                    'title': lecture.title,
                    'course_code': lecture.course.code,
                    'course_name': lecture.course.name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'geofence_type': lecture.geofence_type or 'circular',
                    'location': {
                        'latitude': lecture.latitude,
                        'longitude': lecture.longitude,
                        'radius': lecture.geofence_radius,
                        'name': lecture.location_name
                    }
                }
                
                # Add rectangular boundary data if applicable
                if lecture.geofence_type == 'rectangular' and lecture.boundary_coordinates:
                    import json
                    try:
                        boundary_data = json.loads(lecture.boundary_coordinates)
                        lecture_data['boundary'] = boundary_data
                        lecture_data['boundary_area_sqm'] = lecture.boundary_area_sqm
                        lecture_data['boundary_perimeter_m'] = lecture.boundary_perimeter_m
                        lecture_data['gps_accuracy_threshold'] = lecture.gps_accuracy_threshold
                    except:
                        pass
                
                available_lectures.append(lecture_data)
        
        return jsonify({
            'success': True,
            'lectures': available_lectures,
            'count': len(available_lectures),
            'total_lectures': len(lectures),
            'debug': debug_info,
            'enrolled_courses': len(enrolled_course_ids)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'lectures': [],
            'count': 0
        })

@student_bp.route('/api/lecture/<int:lecture_id>/boundary-status', methods=['GET'])
@login_required
@student_required
def check_boundary_status(lecture_id):
    """
    Check if student is within boundary without marking attendance
    
    GET /student/api/lecture/<id>/boundary-status?lat=40.7128&lon=-74.0060&accuracy=10
    """
    try:
        lecture = Lecture.query.get(lecture_id)
        
        if not lecture:
            return jsonify({
                'success': False,
                'error': 'Lecture not found'
            }), 404
        
        # Check enrollment
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=lecture.course_id,
            is_active=True
        ).first()
        
        if not enrollment:
            return jsonify({
                'success': False,
                'error': 'Not enrolled in this course'
            }), 403
        
        # Get location from query parameters
        student_lat = request.args.get('lat', type=float)
        student_lon = request.args.get('lon', type=float)
        gps_accuracy = request.args.get('accuracy', type=float, default=999)
        
        if not student_lat or not student_lon:
            return jsonify({
                'success': False,
                'error': 'Missing location parameters'
            }), 400
        
        # Validate GPS accuracy
        gps_threshold = lecture.gps_accuracy_threshold or 20
        gps_acceptable = gps_accuracy <= gps_threshold
        
        # Check boundary status
        validation_result = lecture.is_within_geofence_enhanced(
            student_lat,
            student_lon,
            gps_accuracy
        )
        
        response = {
            'success': True,
            'lecture_id': lecture_id,
            'geofence_type': lecture.geofence_type or 'circular',
            'student_location': {
                'lat': student_lat,
                'lon': student_lon,
                'accuracy': gps_accuracy
            },
            'boundary_status': {
                'inside': validation_result['within_geofence'],
                'can_checkin': validation_result['within_geofence'] and gps_acceptable,
                'method': validation_result['method']
            },
            'requirements': {
                'gps_accuracy_threshold': gps_threshold,
                'current_gps_accuracy': gps_accuracy,
                'meets_requirements': gps_acceptable
            }
        }
        
        if validation_result['method'] == 'rectangular':
            response['boundary_status']['distance_to_edge'] = round(validation_result.get('distance_to_edge', 0), 1)
            response['boundary_status']['tolerance_applied'] = validation_result.get('tolerance_applied', False)
        else:
            response['boundary_status']['distance'] = round(validation_result.get('distance', 0), 1)
            response['boundary_status']['radius'] = validation_result.get('radius', 50)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
