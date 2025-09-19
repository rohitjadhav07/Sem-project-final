from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.user import User
from models.course import Course
from models.lecture import Lecture
from models.attendance import Attendance
from app import db
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/check-in', methods=['POST'])
@jwt_required()
def check_in():
    """Handle student check-in with location verification"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        lecture_id = data.get('lecture_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not all([lecture_id, latitude, longitude]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Verify lecture exists and is active
        lecture = Lecture.query.get(lecture_id)
        if not lecture or not lecture.is_active():
            return jsonify({'error': 'Lecture not found or not active'}), 404
            
        # Check if already checked in
        existing = Attendance.query.filter_by(
            student_id=user_id, 
            lecture_id=lecture_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Already checked in'}), 400
            
        # Verify location is within geofence
        if not lecture.is_within_geofence(latitude, longitude):
            return jsonify({'error': 'Location outside allowed area'}), 403
            
        # Create attendance record
        attendance = Attendance(
            student_id=user_id,
            lecture_id=lecture_id,
            marked_latitude=latitude,
            marked_longitude=longitude,
            status='present',
            marked_at=datetime.utcnow()
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'message': 'Check-in successful',
            'attendance_id': attendance.id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/lectures/active', methods=['GET'])
@jwt_required()
def get_active_lectures():
    """Get active lectures for current user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role == 'student':
            # Get lectures for enrolled courses
            lectures = db.session.query(Lecture).join(Course).join(
                'enrollments'
            ).filter_by(user_id=user_id).filter(
                Lecture.is_active == True
            ).all()
        else:
            # Teachers see their own lectures
            lectures = Lecture.query.filter_by(
                teacher_id=user_id,
                is_active=True
            ).all()
            
        return jsonify([{
            'id': lecture.id,
            'title': lecture.title,
            'course_name': lecture.course.name,
            'start_time': lecture.scheduled_start.isoformat(),
            'end_time': lecture.scheduled_end.isoformat(),
            'location': {
                'latitude': lecture.latitude,
                'longitude': lecture.longitude,
                'radius': lecture.geofence_radius
            }
        } for lecture in lectures]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            from flask_jwt_extended import create_access_token, create_refresh_token
            
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500