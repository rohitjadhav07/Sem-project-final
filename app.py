from flask import Flask
from flask_cors import CORS
import os
from config import Config
from extensions import db, login_manager, jwt

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, environment variables not loaded from .env file")

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints with error handling
    blueprints = [
        ('routes.auth', 'auth_bp', '/auth'),
        ('routes.admin', 'admin_bp', '/admin'),
        ('routes.teacher', 'teacher_bp', '/teacher'),
        ('routes.student', 'student_bp', '/student'),
        ('routes.attendance', 'attendance_bp', '/attendance'),
        ('routes.api', 'api_bp', '/api'),
        ('routes.main', 'main_bp', ''),
    ]
    
    for module_name, blueprint_name, url_prefix in blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
            print(f"✅ Registered {blueprint_name}")
        except Exception as e:
            print(f"⚠️ Could not register {blueprint_name}: {e}")
    
    # Register optional blueprints
    optional_blueprints = [
        ('debug_routes', 'debug_bp'),
        ('test_routes', 'test_bp'),
        ('simple_active_lectures', 'simple_bp'),
    ]
    
    for module_name, blueprint_name in optional_blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint)
            print(f"✅ Registered optional {blueprint_name}")
        except Exception as e:
            print(f"⚠️ Optional blueprint {blueprint_name} not available: {e}")
    
    # Add location test route
    @app.route('/test/location')
    def location_test():
        try:
            from flask import render_template
            return render_template('test/location_test.html')
        except Exception as e:
            return f"Location test page not available: {e}"
    
    # Initialize database tables and sample data
    with app.app_context():
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Test database connection first
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("✅ Database connection successful")
                
                # Use original sample data initialization
                from init_sample_data import init_sample_data
                init_sample_data()
                print("✅ Database initialized with sample data")
                break  # Success, exit retry loop
                
            except Exception as e:
                retry_count += 1
                print(f"⚠️ Database connection attempt {retry_count}/{max_retries} failed: {e}")
                
                if retry_count >= max_retries:
                    print("❌ Max retries reached. Running without database initialization.")
                    # In production, continue without database initialization
                    if not app.config.get('DEBUG', False):
                        print("⚠️ Running in production mode without database initialization")
                        break
                    else:
                        print("❌ Development mode: Database connection required")
                else:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)