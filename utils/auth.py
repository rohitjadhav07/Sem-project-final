from functools import wraps
from flask import redirect, url_for, flash, request, jsonify
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity
from models.audit_log import AuditLog
from app import db
from datetime import datetime

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """Decorator to require teacher role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['teacher', 'admin']:
            if request.is_json:
                return jsonify({'error': 'Teacher access required'}), 403
            flash('Access denied. Teacher privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['student', 'admin']:
            if request.is_json:
                return jsonify({'error': 'Student access required'}), 403
            flash('Access denied. Student privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def jwt_student_required(f):
    """Decorator to require student role for JWT authenticated requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            from models.user import User
            user = User.query.get(user_id)
            if not user or user.role not in ['student', 'admin']:
                return jsonify({'error': 'Student access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def jwt_teacher_required(f):
    """Decorator to require teacher role for JWT authenticated requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            from models.user import User
            user = User.query.get(user_id)
            if not user or user.role not in ['teacher', 'admin']:
                return jsonify({'error': 'Teacher access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def log_user_activity(action, entity_type, entity_id, details=None):
    """Log user activity for audit purposes"""
    try:
        audit_log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        # Don't let audit logging break the main functionality
        print(f"Audit logging failed: {e}")
        db.session.rollback()