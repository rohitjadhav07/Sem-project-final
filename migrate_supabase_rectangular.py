#!/usr/bin/env python3
"""
Supabase/PostgreSQL Migration for Rectangular Boundaries
Run this to add rectangular boundary columns to your Supabase database
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from sqlalchemy import text


def migrate_supabase():
    """Add rectangular boundary columns to Supabase PostgreSQL database"""
    
    app = create_app('production')  # Use production config for Supabase
    
    with app.app_context():
        print("\n" + "="*60)
        print("SUPABASE RECTANGULAR BOUNDARIES MIGRATION")
        print("="*60 + "\n")
        
        try:
            # Test connection
            db.session.execute(text('SELECT 1'))
            print("✅ Connected to Supabase database\n")
            
            # Add columns to lectures table
            print("Adding columns to lectures table...")
            
            lectures_columns = [
                ("geofence_type", "VARCHAR(20) DEFAULT 'circular'"),
                ("boundary_coordinates", "TEXT"),
                ("boundary_area_sqm", "REAL"),
                ("boundary_perimeter_m", "REAL"),
                ("boundary_center_lat", "REAL"),
                ("boundary_center_lon", "REAL"),
                ("gps_accuracy_threshold", "INTEGER DEFAULT 20"),
                ("boundary_tolerance_m", "REAL DEFAULT 2.0"),
                ("boundary_validation_method", "VARCHAR(50)"),
                ("boundary_created_at", "TIMESTAMP"),
                ("boundary_last_modified", "TIMESTAMP")
            ]
            
            for col_name, col_type in lectures_columns:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE lectures 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    print(f"  ✅ Added {col_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"  ✓ Column {col_name} already exists")
                    else:
                        print(f"  ⚠️ Could not add {col_name}: {e}")
            
            db.session.commit()
            
            # Add columns to attendances table
            print("\nAdding columns to attendances table...")
            
            attendances_columns = [
                ("validation_method", "VARCHAR(50)"),
                ("distance_to_boundary_edge", "REAL"),
                ("gps_accuracy_at_checkin", "REAL"),
                ("boundary_intersection_status", "VARCHAR(50)"),
                ("location_uncertainty_radius", "REAL")
            ]
            
            for col_name, col_type in attendances_columns:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE attendances 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    print(f"  ✅ Added {col_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"  ✓ Column {col_name} already exists")
                    else:
                        print(f"  ⚠️ Could not add {col_name}: {e}")
            
            db.session.commit()
            
            # Update existing lectures with default values
            print("\nUpdating existing lectures with default values...")
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
            db.session.commit()
            print("✅ Updated default values")
            
            # Create indexes
            print("\nCreating indexes...")
            try:
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_lectures_geofence_type 
                    ON lectures(geofence_type)
                """))
                print("✅ Created idx_lectures_geofence_type")
            except Exception as e:
                print(f"⚠️ Index warning: {e}")
            
            try:
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_lectures_geofence_composite 
                    ON lectures(id, geofence_type)
                """))
                print("✅ Created idx_lectures_geofence_composite")
            except Exception as e:
                print(f"⚠️ Index warning: {e}")
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60 + "\n")
            print("New features available:")
            print("  ✓ Rectangular boundary geofencing")
            print("  ✓ Configurable GPS accuracy thresholds (10m, 15m, 20m)")
            print("  ✓ Edge tolerance for boundary validation (2m default)")
            print("  ✓ Enhanced validation metadata")
            print("\nYour existing data has been preserved.")
            print("All existing lectures default to 'circular' geofence type.\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = migrate_supabase()
    sys.exit(0 if success else 1)
