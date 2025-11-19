#!/usr/bin/env python3
"""
Simple migration script to add rectangular boundary columns
This script adds new columns to existing database without dropping tables
"""

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
from sqlalchemy import text, inspect

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_rectangular_boundary_columns():
    """Add new columns for rectangular boundary support"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("ADDING RECTANGULAR BOUNDARY SUPPORT")
        print("="*60 + "\n")
        
        try:
            # Check database type
            db_url = str(db.engine.url)
            is_sqlite = 'sqlite' in db_url.lower()
            
            print(f"Database: {db_url}")
            print(f"Database type: {'SQLite' if is_sqlite else 'Other'}\n")
            
            # Columns to add to lectures table
            lectures_columns = {
                'geofence_type': "VARCHAR(20) DEFAULT 'circular'",
                'boundary_coordinates': "TEXT",
                'boundary_area_sqm': "REAL",
                'boundary_perimeter_m': "REAL",
                'boundary_center_lat': "REAL",
                'boundary_center_lon': "REAL",
                'gps_accuracy_threshold': "INTEGER DEFAULT 20",
                'boundary_tolerance_m': "REAL DEFAULT 2.0",
                'boundary_validation_method': "VARCHAR(50)",
                'boundary_created_at': "DATETIME",
                'boundary_last_modified': "DATETIME"
            }
            
            # Columns to add to attendances table
            attendances_columns = {
                'validation_method': "VARCHAR(50)",
                'distance_to_boundary_edge': "REAL",
                'gps_accuracy_at_checkin': "REAL",
                'boundary_intersection_status': "VARCHAR(50)",
                'location_uncertainty_radius': "REAL"
            }
            
            # Add columns to lectures table
            print("Checking lectures table...")
            for column_name, column_type in lectures_columns.items():
                if not check_column_exists('lectures', column_name):
                    print(f"  Adding column: {column_name}")
                    try:
                        db.session.execute(text(f"ALTER TABLE lectures ADD COLUMN {column_name} {column_type}"))
                        db.session.commit()
                        print(f"  ✅ Added {column_name}")
                    except Exception as e:
                        print(f"  ⚠️ Could not add {column_name}: {e}")
                        db.session.rollback()
                else:
                    print(f"  ✓ Column {column_name} already exists")
            
            # Add columns to attendances table
            print("\nChecking attendances table...")
            for column_name, column_type in attendances_columns.items():
                if not check_column_exists('attendances', column_name):
                    print(f"  Adding column: {column_name}")
                    try:
                        db.session.execute(text(f"ALTER TABLE attendances ADD COLUMN {column_name} {column_type}"))
                        db.session.commit()
                        print(f"  ✅ Added {column_name}")
                    except Exception as e:
                        print(f"  ⚠️ Could not add {column_name}: {e}")
                        db.session.rollback()
                else:
                    print(f"  ✓ Column {column_name} already exists")
            
            # Update existing lectures with default values
            print("\nUpdating existing lectures with default values...")
            try:
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
            except Exception as e:
                print(f"⚠️ Could not update defaults: {e}")
                db.session.rollback()
            
            # Create indexes for better performance
            print("\nCreating indexes...")
            try:
                # Check if indexes exist first
                inspector = inspect(db.engine)
                existing_indexes = [idx['name'] for idx in inspector.get_indexes('lectures')]
                
                if 'idx_lectures_geofence_type' not in existing_indexes:
                    db.session.execute(text("""
                        CREATE INDEX idx_lectures_geofence_type 
                        ON lectures(geofence_type)
                    """))
                    print("✅ Created idx_lectures_geofence_type")
                else:
                    print("✓ Index idx_lectures_geofence_type already exists")
                
                if 'idx_lectures_geofence_composite' not in existing_indexes:
                    db.session.execute(text("""
                        CREATE INDEX idx_lectures_geofence_composite 
                        ON lectures(id, geofence_type)
                    """))
                    print("✅ Created idx_lectures_geofence_composite")
                else:
                    print("✓ Index idx_lectures_geofence_composite already exists")
                
                db.session.commit()
            except Exception as e:
                print(f"⚠️ Index creation warning: {e}")
                db.session.rollback()
            
            print("\n" + "="*60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60 + "\n")
            print("New features available:")
            print("  - Rectangular boundary geofencing")
            print("  - Configurable GPS accuracy thresholds (10m, 15m, 20m)")
            print("  - Edge tolerance for boundary validation")
            print("  - Enhanced validation metadata")
            print("\nYour existing data has been preserved.")
            print("All existing lectures default to 'circular' geofence type.\n")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_rectangular_boundary_columns()
