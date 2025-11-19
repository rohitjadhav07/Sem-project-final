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
    
    # Google Maps API Key (for WiFi positioning)
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or ''
    
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
    
    # Use Supabase PostgreSQL database with fallback options
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DATABASE_URL')
    
    # If no URL provided, use direct connection (more reliable than pooler)
    if not database_url:
        supabase_project = 'kkdnmzfcjckukxszfbgc'
        supabase_password = 'Finalproject1234'
        # Use direct connection instead of pooler for better reliability
        database_url = f'postgresql://postgres:{supabase_password}@db.{supabase_project}.supabase.co:5432/postgres'
    
    # Handle Vercel's postgres:// URL format (convert to postgresql://)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Add connection parameters for reliability
    if database_url:
        database_url = database_url.strip()
        if '?' not in database_url:
            database_url += '?sslmode=require&connect_timeout=10'
        else:
            if 'sslmode' not in database_url:
                database_url += '&sslmode=require'
            if 'connect_timeout' not in database_url:
                database_url += '&connect_timeout=10'
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = False  # Set to True only if using HTTPS
    WTF_CSRF_ENABLED = True
    
    # Database settings for better connection handling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
        'max_overflow': 5,
        'pool_size': 10,
        'connect_args': {
            'connect_timeout': 30,
            'application_name': 'geo_attendance_pro',
            'target_session_attrs': 'read-write',
            'keepalives_idle': 600,
            'keepalives_interval': 30,
            'keepalives_count': 3
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

class VercelConfig(ProductionConfig):
    """Vercel-specific configuration"""
    
    # Optimized database settings for Vercel serverless
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 60,        # Shorter recycle time for serverless
        'pool_timeout': 30,        # Shorter timeout
        'max_overflow': 0,         # No overflow for serverless
        'pool_size': 1,            # Single connection for serverless
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'geo_attendance_vercel',
            'target_session_attrs': 'read-write'
        }
    }
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Vercel-specific logging
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
    'vercel': VercelConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}