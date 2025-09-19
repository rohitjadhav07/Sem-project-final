from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app import db
from models.user import User
from models.lecture import Lecture
from models.attendance import Attendance
from models.enrollment import Enrollment
from utils.geolocation import calculate_distance, is_within_geofence, validate_coordinates
from utils.auth import student_required, jwt_student_required, log_user_activity
from utils.notifications import send_attendance_notification, send_geofence_alert

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/mark', methods=['POST'])
@login_required
@student_required
def mark_attendance():
    """Mark attendance for a lecture"""
    data = request.get_json()
    
    lecture_id = data.get('lecture_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([lecture_id, latitude, longitude]):
        return jsonify({'error': 'Lecture ID, latitude, and longitude are required'}), 400
    
    # Validate coordinates
    valid, message = validate_coordinates(latitude, longitude)
    if not valid:
        return jsonify({'error': message}), 400
    
    # Get lecture
    lecture = Lecture.query.get(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404
    
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=lecture.course_id,
        is_active=True
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Check if attendance window is open
    if not lecture.is_attendance_window_open():
        return jsonify({'error': 'Attendance window is not open for this lecture'}), 400
    
    # Check if attendance already marked
    existing_attendance = Attendance.query.filter_by(
        student_id=current_user.id,
        lecture_id=lecture_id
    ).first()
    
    if existing_attendance:
        return jsonify({'error': 'Attendance already marked for this lecture'}), 400
    
    # Calculate distance from lecture location
    within_geofence, distance = is_within_geofence(
        latitude, longitude,
        lecture.latitude, lecture.longitude,
        lecture.geofence_radius
    )
    
    # Create attendance record
    attendance = Attendance(
        student_id=current_user.id,
        lecture_id=lecture_id,
        marked_latitude=latitude,
        marked_longitude=longitude,
        distance_from_lecture=distance,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    if within_geofence:
        attendance.mark_present(latitude, longitude, distance, auto_marked=False)
        status_message = 'Attendance marked successfully'
    else:
        # Send geofence alert but don't mark as present
        send_geofence_alert(
            current_user.id,
            lecture.title,
            distance,
            lecture.geofence_radius
        )
        return jsonify({
            'error': f'You are {distance:.0f}m away from the lecture location. Please move within {lecture.geofence_radius}m to mark attendance.',
            'distance': distance,
            'required_distance': lecture.geofence_radius
        }), 400
    
    try:
        db.session.add(attendance)
        db.session.commit()
        
        # Send notification
        send_attendance_notification(
            current_user.id,
            lecture.title,
            attendance.status,
            lecture.course.name
        )
        
        # Log activity
        log_user_activity('mark_attendance', 'attendance', attendance.id, {
            'lecture_id': lecture_id,
            'status': attendance.status,
            'distance': distance
        })
        
        return jsonify({
            'message': status_message,
            'attendance': attendance.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to mark attendance'}), 500

@attendance_bp.route('/api/mark', methods=['POST'])
@jwt_required()
@jwt_student_required
def api_mark_attendance():
    """API endpoint to mark attendance"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    lecture_id = data.get('lecture_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([lecture_id, latitude, longitude]):
        return jsonify({'error': 'Lecture ID, latitude, and longitude are required'}), 400
    
    # Similar logic as above but for JWT authentication
    # ... (implement similar logic as mark_attendance but using JWT user)
    
    return jsonify({'message': 'API attendance marking not yet implemented'}), 501

@attendance_bp.route('/check-location', methods=['POST'])
@login_required
@student_required
def check_location():
    """Check if student is within geofence for a lecture"""
    data = request.get_json()
    
    lecture_id = data.get('lecture_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([lecture_id, latitude, longitude]):
        return jsonify({'error': 'Lecture ID, latitude, and longitude are required'}), 400
    
    # Validate coordinates
    valid, message = validate_coordinates(latitude, longitude)
    if not valid:
        return jsonify({'error': message}), 400
    
    # Get lecture
    lecture = Lecture.query.get(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404
    
    # Calculate distance
    within_geofence, distance = is_within_geofence(
        latitude, longitude,
        lecture.latitude, lecture.longitude,
        lecture.geofence_radius
    )
    
    return jsonify({
        'within_geofence': within_geofence,
        'distance': round(distance, 2),
        'geofence_radius': lecture.geofence_radius,
        'lecture_location': {
            'latitude': lecture.latitude,
            'longitude': lecture.longitude,
            'name': lecture.location_name
        }
    }), 200

@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_attendance(student_id):
    """Get attendance records for a student"""
    # Check permissions
    if not (current_user.is_admin() or 
            current_user.is_teacher() or 
            current_user.id == student_id):
        return jsonify({'error': 'Access denied'}), 403
    
    student = User.query.get(student_id)
    if not student or not student.is_student():
        return jsonify({'error': 'Student not found'}), 404
    
    # Get attendance records
    attendances = Attendance.query.filter_by(student_id=student_id)\
        .join(Lecture)\
        .order_by(Lecture.scheduled_start.desc())\
        .all()
    
    return jsonify({
        'student': student.to_dict(),
        'attendances': [attendance.to_dict() for attendance in attendances]
    }), 200

@attendance_bp.route('/lecture/<int:lecture_id>')
@login_required
def lecture_attendance(lecture_id):
    """Get attendance records for a lecture"""
    lecture = Lecture.query.get(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404
    
    # Check permissions
    if not (current_user.is_admin() or 
            current_user.id == lecture.teacher_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get attendance records
    attendances = Attendance.query.filter_by(lecture_id=lecture_id)\
        .join(User)\
        .order_by(User.last_name, User.first_name)\
        .all()
    
    # Get enrolled students who haven't marked attendance
    enrolled_students = User.query.join(Enrollment)\
        .filter(Enrollment.course_id == lecture.course_id,
                Enrollment.is_active == True)\
        .all()
    
    marked_student_ids = {a.student_id for a in attendances}
    unmarked_students = [s for s in enrolled_students if s.id not in marked_student_ids]
    
    return jsonify({
        'lecture': lecture.to_dict(),
        'attendances': [attendance.to_dict() for attendance in attendances],
        'unmarked_students': [student.to_dict() for student in unmarked_students],
        'stats': lecture.get_attendance_stats()
    }), 200

@attendance_bp.route('/update/<int:attendance_id>', methods=['PUT'])
@login_required
def update_attendance(attendance_id):
    """Update attendance record (admin/teacher only)"""
    if not (current_user.is_admin() or current_user.is_teacher()):
        return jsonify({'error': 'Access denied'}), 403
    
    attendance = Attendance.query.get(attendance_id)
    if not attendance:
        return jsonify({'error': 'Attendance record not found'}), 404
    
    # Check if teacher owns the course
    if current_user.is_teacher() and attendance.lecture.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes')
    
    if new_status not in ['present', 'absent', 'late', 'excused']:
        return jsonify({'error': 'Invalid status'}), 400
    
    # Update attendance
    old_status = attendance.status
    attendance.status = new_status
    attendance.notes = notes
    attendance.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Log activity
        log_user_activity('update_attendance', 'attendance', attendance_id, {
            'old_status': old_status,
            'new_status': new_status,
            'student_id': attendance.student_id,
            'lecture_id': attendance.lecture_id
        })
        
        return jsonify({
            'message': 'Attendance updated successfully',
            'attendance': attendance.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update attendance'}), 500

@attendance_bp.route('/bulk-update', methods=['POST'])
@login_required
def bulk_update_attendance():
    """Bulk update attendance records"""
    if not (current_user.is_admin() or current_user.is_teacher()):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    updates = data.get('updates', [])
    
    if not updates:
        return jsonify({'error': 'No updates provided'}), 400
    
    updated_count = 0
    errors = []
    
    for update in updates:
        try:
            attendance_id = update.get('attendance_id')
            new_status = update.get('status')
            notes = update.get('notes')
            
            attendance = Attendance.query.get(attendance_id)
            if not attendance:
                errors.append(f'Attendance {attendance_id} not found')
                continue
            
            # Check permissions
            if current_user.is_teacher() and attendance.lecture.teacher_id != current_user.id:
                errors.append(f'Access denied for attendance {attendance_id}')
                continue
            
            if new_status in ['present', 'absent', 'late', 'excused']:
                attendance.status = new_status
                attendance.notes = notes
                attendance.updated_at = datetime.utcnow()
                updated_count += 1
        
        except Exception as e:
            errors.append(f'Error updating attendance {attendance_id}: {str(e)}')
    
    try:
        db.session.commit()
        
        return jsonify({
            'message': f'Updated {updated_count} attendance records',
            'updated_count': updated_count,
            'errors': errors
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update attendance records'}), 500