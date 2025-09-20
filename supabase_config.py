"""
Supabase configuration and setup
"""
import os
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        if self.supabase_url and self.supabase_key:
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
    
    def get_database_url(self):
        """Get the PostgreSQL database URL for SQLAlchemy"""
        if self.database_url:
            return self.database_url
        
        # Fallback to SQLite if Supabase not configured
        return 'sqlite:////tmp/geo_attendance.db'
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client for direct operations"""
        return self.supabase_client
    
    def is_configured(self):
        """Check if Supabase is properly configured"""
        return bool(self.supabase_url and self.supabase_key and self.database_url)

# Global instance
supabase_config = SupabaseConfig()