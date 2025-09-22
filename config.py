import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security Headers
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Email Configuration (for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Location Security Settings
    MIN_GPS_ACCURACY = int(os.environ.get('MIN_GPS_ACCURACY') or 15)  # meters
    DEFAULT_GEOFENCE_RADIUS = int(os.environ.get('DEFAULT_GEOFENCE_RADIUS') or 50)  # meters
    LOCATION_CONFIRMATIONS_REQUIRED = int(os.environ.get('LOCATION_CONFIRMATIONS_REQUIRED') or 3)
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'geo_attendance.db')
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use Supabase PostgreSQL database with fallback to SQLite
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DATABASE_URL')
    
    # Handle Vercel's postgres:// URL format (convert to postgresql://)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:////tmp/geo_attendance.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = False  # Set to True only if using HTTPS
    WTF_CSRF_ENABLED = True
    
    # Database settings for better connection handling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'geo_attendance_pro',
            'sslmode': 'require'
        }
    }
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class HerokuConfig(ProductionConfig):
    """Heroku-specific configuration"""
    SSL_REDIRECT = True
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Handle proxy server headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        
        # Log to stdout on Heroku
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class DockerConfig(ProductionConfig):
    """Docker-specific configuration"""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Log to stdout in Docker
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}