from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))
from app import db
from models.user import User
from utils.auth import log_user_activity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        if request.is_json:
            # API login
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            # Form login
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Username and password required'}), 400
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email with error handling
        try:
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
        except Exception as e:
            print(f"Database connection error during login: {e}")
            if request.is_json:
                return jsonify({'error': 'Database connection error. Please try again.'}), 500
            else:
                flash('Database connection error. Please try again in a moment.', 'error')
                return render_template('auth/login.html')
        
        if user and user.check_password(password) and user.is_active:
            if request.is_json:
                # API response with JWT tokens
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_user_activity('login', 'user', user.id)
                
                return jsonify({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user.to_dict()
                }), 200
            else:
                # Web login
                login_user(user, remember=request.form.get('remember_me'))
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_user_activity('login', 'user', user.id)
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.index')
                return redirect(next_page)
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid credentials'}), 401
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                error_msg = f'{field.replace("_", " ").title()} is required'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('auth/register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            error_msg = 'Username or email already exists'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        # Validate role
        if data['role'] not in ['student', 'teacher']:
            error_msg = 'Invalid role selected'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            phone=data.get('phone'),
            student_id=data.get('student_id') if data['role'] == 'student' else None,
            employee_id=data.get('employee_id') if data['role'] == 'teacher' else None
        )
        user.set_password(data['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            
            log_user_activity('register', 'user', user.id)
            
            if request.is_json:
                return jsonify({
                    'message': 'Registration successful',
                    'user': user.to_dict()
                }), 201
            else:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            error_msg = 'Registration failed. Please try again.'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            flash(error_msg, 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    log_user_activity('logout', 'user', current_user.id)
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Update allowed fields
    allowed_fields = ['first_name', 'last_name', 'phone', 'email']
    updated_fields = []
    
    for field in allowed_fields:
        if field in data and data[field] != getattr(current_user, field):
            setattr(current_user, field, data[field])
            updated_fields.append(field)
    
    # Handle password change
    if data.get('new_password'):
        if not data.get('current_password'):
            error_msg = 'Current password is required to change password'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/profile.html', user=current_user)
        
        if not current_user.check_password(data['current_password']):
            error_msg = 'Current password is incorrect'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/profile.html', user=current_user)
        
        current_user.set_password(data['new_password'])
        updated_fields.append('password')
    
    if updated_fields:
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_user_activity('update_profile', 'user', current_user.id, 
                         {'updated_fields': updated_fields})
        
        success_msg = 'Profile updated successfully'
        if request.is_json:
            return jsonify({
                'message': success_msg,
                'user': current_user.to_dict()
            }), 200
        flash(success_msg, 'success')
    
    return render_template('auth/profile.html', user=current_user)

# JWT API endpoints
@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token"""
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': new_token}), 200

@auth_bp.route('/api/me')
@jwt_required()
def get_current_user():
    """Get current user info from JWT"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200