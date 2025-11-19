"""
Database migration script for adding rectangular boundary support
Adds new columns to Lecture and Attendance models for rectangular geofencing
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from extensions import db
from sqlalchemy import text

def upgrade():
    """
    Add new columns for rectangular boundary support
    """
    print("Starting migration: add_rectangular_boundaries")
    
    try:
        # Add columns to lectures table
        print("Adding columns to lectures table...")
        
        # Geofence type selector
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS geofence_type VARCHAR(20) DEFAULT 'circular'
        """))
        
        # Rectangular boundary coordinates (JSON)
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_coordinates TEXT
        """))
        
        # Boundary metadata
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_area_sqm REAL
        """))
        
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_perimeter_m REAL
        """))
        
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_center_lat REAL
        """))
        
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_center_lon REAL
        """))
        
        # GPS accuracy requirements
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS gps_accuracy_threshold INTEGER DEFAULT 20
        """))
        
        # Tolerance settings
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_tolerance_m REAL DEFAULT 2.0
        """))
        
        # Validation metadata
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_validation_method VARCHAR(50)
        """))
        
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_created_at DATETIME
        """))
        
        db.session.execute(text("""
            ALTER TABLE lectures 
            ADD COLUMN IF NOT EXISTS boundary_last_modified DATETIME
        """))
        
        print("✅ Added columns to lectures table")
        
        # Add columns to attendances table
        print("Adding columns to attendances table...")
        
        # Enhanced validation metadata
        db.session.execute(text("""
            ALTER TABLE attendances 
            ADD COLUMN IF NOT EXISTS validation_method VARCHAR(50)
        """))
        
        db.session.execute(text("""
            ALTER TABLE attendances 
            ADD COLUMN IF NOT EXISTS distance_to_boundary_edge REAL
        """))
        
        db.session.execute(text("""
            ALTER TABLE attendances 
            ADD COLUMN IF NOT EXISTS gps_accuracy_at_checkin REAL
        """))
        
        db.session.execute(text("""
            ALTER TABLE attendances 
            ADD COLUMN IF NOT EXISTS boundary_intersection_status VARCHAR(50)
        """))
        
        db.session.execute(text("""
            ALTER TABLE attendances 
            ADD COLUMN IF NOT EXISTS location_uncertainty_radius REAL
        """))
        
        print("✅ Added columns to attendances table")
        
        # Create indexes for better query performance
        print("Creating indexes...")
        
        try:
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_lectures_geofence_type 
                ON lectures(geofence_type)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_lectures_geofence_composite 
                ON lectures(id, geofence_type)
            """))
            
            print("✅ Created indexes")
        except Exception as e:
            print(f"⚠️ Index creation warning (may already exist): {e}")
        
        # Set default values for existing lectures
        print("Setting default values for existing lectures...")
        db.session.execute(text("""
            UPDATE lectures 
            SET geofence_type = 'circular' 
            WHERE geofence_type IS NULL
        """))
        
        db.session.execute(text("""
            UPDATE lectures 
            SET gps_accuracy_threshold = 20 
            WHERE gps_accuracy_threshold IS NULL
        """))
        
        db.session.execute(text("""
            UPDATE lectures 
            SET boundary_tolerance_m = 2.0 
            WHERE boundary_tolerance_m IS NULL
        """))
        
        print("✅ Set default values for existing lectures")
        
        # Commit all changes
        db.session.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.session.rollback()
        raise


def downgrade():
    """
    Remove rectangular boundary columns (rollback migration)
    """
    print("Starting rollback: remove_rectangular_boundaries")
    
    try:
        # Drop indexes
        print("Dropping indexes...")
        try:
            db.session.execute(text("DROP INDEX IF EXISTS idx_lectures_geofence_type"))
            db.session.execute(text("DROP INDEX IF EXISTS idx_lectures_geofence_composite"))
            print("✅ Dropped indexes")
        except Exception as e:
            print(f"⚠️ Index drop warning: {e}")
        
        # Remove columns from lectures table
        print("Removing columns from lectures table...")
        
        columns_to_remove_lectures = [
            'geofence_type',
            'boundary_coordinates',
            'boundary_area_sqm',
            'boundary_perimeter_m',
            'boundary_center_lat',
            'boundary_center_lon',
            'gps_accuracy_threshold',
            'boundary_tolerance_m',
            'boundary_validation_method',
            'boundary_created_at',
            'boundary_last_modified'
        ]
        
        for column in columns_to_remove_lectures:
            try:
                db.session.execute(text(f"ALTER TABLE lectures DROP COLUMN IF EXISTS {column}"))
            except Exception as e:
                print(f"⚠️ Could not drop column {column}: {e}")
        
        print("✅ Removed columns from lectures table")
        
        # Remove columns from attendances table
        print("Removing columns from attendances table...")
        
        columns_to_remove_attendances = [
            'validation_method',
            'distance_to_boundary_edge',
            'gps_accuracy_at_checkin',
            'boundary_intersection_status',
            'location_uncertainty_radius'
        ]
        
        for column in columns_to_remove_attendances:
            try:
                db.session.execute(text(f"ALTER TABLE attendances DROP COLUMN IF EXISTS {column}"))
            except Exception as e:
                print(f"⚠️ Could not drop column {column}: {e}")
        
        print("✅ Removed columns from attendances table")
        
        # Commit all changes
        db.session.commit()
        print("✅ Rollback completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        db.session.rollback()
        raise


def run_migration():
    """
    Run the migration with proper Flask app context
    """
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("RECTANGULAR BOUNDARIES MIGRATION")
        print("="*60 + "\n")
        
        try:
            upgrade()
            print("\n" + "="*60)
            print("MIGRATION SUCCESSFUL")
            print("="*60 + "\n")
        except Exception as e:
            print("\n" + "="*60)
            print("MIGRATION FAILED")
            print("="*60)
            print(f"Error: {e}\n")
            raise


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        from app import create_app
        app = create_app()
        with app.app_context():
            print("\n" + "="*60)
            print("ROLLING BACK RECTANGULAR BOUNDARIES MIGRATION")
            print("="*60 + "\n")
            try:
                downgrade()
                print("\n" + "="*60)
                print("ROLLBACK SUCCESSFUL")
                print("="*60 + "\n")
            except Exception as e:
                print("\n" + "="*60)
                print("ROLLBACK FAILED")
                print("="*60)
                print(f"Error: {e}\n")
                raise
    else:
        run_migration()
