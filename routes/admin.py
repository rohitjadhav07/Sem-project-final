from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.course import Course
from models.lecture import Lecture
from app import db
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with system overview"""
    stats = {
        'total_users': User.query.count(),
        'total_courses': Course.query.count(),
        'total_lectures': Lecture.query.count(),
        'active_lectures': Lecture.query.filter_by(is_active=True).count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
def manage_users():
    """Manage system users"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/courses')
def manage_courses():
    """Manage courses"""
    courses = Course.query.all()
    users = User.query.all()  # For teacher selection
    return render_template('admin/courses.html', courses=courses, users=users)

@admin_bp.route('/reports')
def reports():
    """System reports"""
    return render_template('admin/reports.html')

@admin_bp.route('/settings')
def settings():
    """System settings"""
    return render_template('admin/settings.html')

@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/course/<int:course_id>/toggle-status', methods=['POST'])
def toggle_course_status(course_id):
    """Toggle course active status"""
    course = Course.query.get_or_404(course_id)
    course.is_active = not course.is_active
    db.session.commit()
    
    status = 'activated' if course.is_active else 'deactivated'
    flash(f'Course {course.code} has been {status}.', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/add-user', methods=['POST'])
def add_user():
    """Add new user"""
    try:
        data = request.form
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('admin.manage_users'))
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            phone=data.get('phone'),
            student_id=data.get('student_id') if data['role'] == 'student' else None,
            employee_id=data.get('employee_id') if data['role'] in ['teacher', 'admin'] else None
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating user: {str(e)}', 'error')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>')
def get_user(user_id):
    """Get user data for editing"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@admin_bp.route('/user/<int:user_id>/edit', methods=['POST'])
def edit_user(user_id):
    """Edit user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.form
        
        # Update user fields
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.username = data['username']
        user.email = data['email']
        user.phone = data.get('phone')
        
        # Update password if provided
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting current user
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'})
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User {username} deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/add-course', methods=['POST'])
def add_course():
    """Add new course"""
    try:
        data = request.form
        
        # Check if course code already exists
        existing_course = Course.query.filter_by(code=data['code']).first()
        if existing_course:
            flash('Course code already exists', 'error')
            return redirect(url_for('admin.manage_courses'))
        
        # Create new course
        course = Course(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            teacher_id=data['teacher_id'],
            credits=int(data.get('credits', 3)),
            semester=data.get('semester'),
            academic_year=data.get('academic_year')
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash(f'Course {course.code} created successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating course: {str(e)}', 'error')
        return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/course/<int:course_id>')
def get_course(course_id):
    """Get course data for editing"""
    course = Course.query.get_or_404(course_id)
    return jsonify(course.to_dict())

@admin_bp.route('/course/<int:course_id>/edit', methods=['POST'])
def edit_course(course_id):
    """Edit course"""
    try:
        course = Course.query.get_or_404(course_id)
        data = request.form
        
        # Update course fields
        course.code = data['code']
        course.name = data['name']
        course.description = data.get('description')
        course.teacher_id = data['teacher_id']
        course.credits = int(data.get('credits', 3))
        course.semester = data.get('semester')
        course.academic_year = data.get('academic_year')
        
        db.session.commit()
        flash(f'Course {course.code} updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating course: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/course/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    """Delete course"""
    try:
        course = Course.query.get_or_404(course_id)
        course_code = course.code
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Course {course_code} deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/course/<int:course_id>/detail')
def course_detail(course_id):
    """Course detail page"""
    course = Course.query.get_or_404(course_id)
    return render_template('admin/course_detail.html', course=course)

@admin_bp.route('/course/<int:course_id>/toggle-status', methods=['POST'])
def course_toggle_status(course_id):
    """Toggle course active status"""
    try:
        course = Course.query.get_or_404(course_id)
        course.is_active = not course.is_active
        db.session.commit()
        
        status = 'activated' if course.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'Course {status} successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})