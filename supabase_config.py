"""
Supabase configuration and setup
"""
import os

# Try to import Supabase, but handle gracefully if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

class SupabaseConfig:
    """Supabase configuration class"""
    
    def __init__(self):
        # Supabase credentials (will be set via environment variables)
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        self.database_url = os.environ.get('SUPABASE_DATABASE_URL')
        
        # Initialize Supabase client
        self.supabase_client = None
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                print(f"⚠️ Could not initialize Supabase client: {e}")
    
    def get_database_url(self):
        """Get the database URL for SQLAlchemy"""
        if self.database_url and self.database_url.startswith('postgresql://'):
            # Check if psycopg2 is available for PostgreSQL
            try:
                import psycopg2
                return self.database_url
            except ImportError:
                print("⚠️ PostgreSQL URL provided but psycopg2 not available, using SQLite")
                return 'sqlite:////tmp/geo_attendance.db'
        elif self.database_url:
            return self.database_url
        
        # Fallback to SQLite if Supabase not configured
        return 'sqlite:////tmp/geo_attendance.db'
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client for direct operations"""
        return self.supabase_client
    
    def is_configured(self):
        """Check if Supabase is properly configured"""
        return bool(SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key and self.database_url)

# Global instance
supabase_config = SupabaseConfig()