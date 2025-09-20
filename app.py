from flask import Flask
from flask_cors import CORS
import os
from config import Config
from extensions import db, login_manager, jwt

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
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.teacher import teacher_bp
    from routes.student import student_bp
    from routes.attendance import attendance_bp
    from routes.api import api_bp
    from debug_routes import debug_bp
    from test_routes import test_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(debug_bp)
    app.register_blueprint(test_bp)
    
    # Register simple active lectures blueprint
    try:
        from simple_active_lectures import simple_bp
        app.register_blueprint(simple_bp)
        print("✅ Simple active lectures registered")
    except Exception as e:
        print(f"⚠️ Could not register simple active lectures: {e}")
    
    # Add location test route
    @app.route('/test/location')
    def location_test():
        from flask import render_template
        return render_template('test/location_test.html')
    
    # Main route
    from routes.main import main_bp
    app.register_blueprint(main_bp)
    
    # Initialize database tables and sample data
    with app.app_context():
        try:
            # Check if we're using Supabase
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'postgresql://' in database_url:
                print("🔄 Using Supabase PostgreSQL database")
                # Try Supabase initialization
                try:
                    from init_supabase import create_supabase_tables, init_supabase_data
                    create_supabase_tables()
                    init_supabase_data()
                    print("✅ Supabase database initialized")
                except Exception as supabase_error:
                    print(f"⚠️ Supabase initialization error: {supabase_error}")
                    # Fallback to SQLAlchemy table creation
                    db.create_all()
                    print("✅ Database tables created via SQLAlchemy")
            else:
                print("🔄 Using SQLite database")
                # Use original sample data initialization for SQLite
                from init_sample_data import init_sample_data
                init_sample_data()
                print("✅ SQLite database initialized with sample data")
                
        except Exception as e:
            print(f"⚠️ Database initialization error: {e}")
            # Last resort: create basic tables
            try:
                db.create_all()
                print("✅ Basic database tables created")
            except Exception as table_error:
                print(f"❌ Could not create tables: {table_error}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)