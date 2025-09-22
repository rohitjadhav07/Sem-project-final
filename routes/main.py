from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main landing page"""
    try:
        if current_user.is_authenticated:
            # Redirect to appropriate dashboard based on role
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif current_user.role == 'student':
                return redirect(url_for('student.dashboard'))
        
        return render_template('index.html')
    except Exception as e:
        # Return a simple error page for debugging
        return f"""
        <h1>Geo Attendance Pro</h1>
        <p>Application is starting up...</p>
        <p>Error: {str(e)}</p>
        <p><a href="/health">Check Health Status</a></p>
        """, 500

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    try:
        from extensions import db
        from sqlalchemy import text
        from flask import current_app
        
        # Test database connection
        result = db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        # Get database URL for debugging (hide password)
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        if db_url and '@' in db_url:
            # Hide password in URL for security
            parts = db_url.split('@')
            if len(parts) > 1:
                user_pass = parts[0].split('//')[-1]
                if ':' in user_pass:
                    user = user_pass.split(':')[0]
                    db_url_safe = f"postgresql://{user}:***@{parts[1]}"
                else:
                    db_url_safe = db_url
            else:
                db_url_safe = db_url
        else:
            db_url_safe = db_url
            
        return {
            'status': 'healthy',
            'database': 'connected',
            'database_url': db_url_safe,
            'message': 'Geo Attendance Pro is running'
        }, 200
    except Exception as e:
        from flask import current_app
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        if db_url and '@' in db_url:
            parts = db_url.split('@')
            if len(parts) > 1:
                user_pass = parts[0].split('//')[-1]
                if ':' in user_pass:
                    user = user_pass.split(':')[0]
                    db_url_safe = f"postgresql://{user}:***@{parts[1]}"
                else:
                    db_url_safe = db_url
            else:
                db_url_safe = db_url
        else:
            db_url_safe = db_url
            
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'database_url': db_url_safe,
            'error': str(e)
        }, 500