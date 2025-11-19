#!/usr/bin/env python3
"""
Direct SQLite migration to add rectangular boundary columns
Works without Flask dependencies
"""
import sqlite3
import os

def add_columns():
    """Add rectangular boundary columns directly to SQLite database"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'geo_attendance.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print("\n" + "="*60)
    print("ADDING RECTANGULAR BOUNDARY COLUMNS")
    print("="*60 + "\n")
    print(f"Database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing columns in lectures table
        cursor.execute("PRAGMA table_info(lectures)")
        existing_lectures_cols = [row[1] for row in cursor.fetchall()]
        
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
        
        print("Adding columns to lectures table...")
        for col_name, col_type in lectures_columns.items():
            if col_name not in existing_lectures_cols:
                try:
                    cursor.execute(f"ALTER TABLE lectures ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Added {col_name}")
                except Exception as e:
                    print(f"  ⚠️ Could not add {col_name}: {e}")
            else:
                print(f"  ✓ Column {col_name} already exists")
        
        # Get existing columns in attendances table
        cursor.execute("PRAGMA table_info(attendances)")
        existing_attendances_cols = [row[1] for row in cursor.fetchall()]
        
        # Columns to add to attendances table
        attendances_columns = {
            'validation_method': "VARCHAR(50)",
            'distance_to_boundary_edge': "REAL",
            'gps_accuracy_at_checkin': "REAL",
            'boundary_intersection_status': "VARCHAR(50)",
            'location_uncertainty_radius': "REAL"
        }
        
        print("\nAdding columns to attendances table...")
        for col_name, col_type in attendances_columns.items():
            if col_name not in existing_attendances_cols:
                try:
                    cursor.execute(f"ALTER TABLE attendances ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Added {col_name}")
                except Exception as e:
                    print(f"  ⚠️ Could not add {col_name}: {e}")
            else:
                print(f"  ✓ Column {col_name} already exists")
        
        # Update existing lectures with default values
        print("\nUpdating existing lectures with default values...")
        cursor.execute("""
            UPDATE lectures 
            SET geofence_type = 'circular' 
            WHERE geofence_type IS NULL
        """)
        cursor.execute("""
            UPDATE lectures 
            SET gps_accuracy_threshold = 20 
            WHERE gps_accuracy_threshold IS NULL
        """)
        cursor.execute("""
            UPDATE lectures 
            SET boundary_tolerance_m = 2.0 
            WHERE boundary_tolerance_m IS NULL
        """)
        print("✅ Updated default values")
        
        # Create indexes
        print("\nCreating indexes...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lectures_geofence_type 
                ON lectures(geofence_type)
            """)
            print("✅ Created idx_lectures_geofence_type")
        except Exception as e:
            print(f"⚠️ Index warning: {e}")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lectures_geofence_composite 
                ON lectures(id, geofence_type)
            """)
            print("✅ Created idx_lectures_geofence_composite")
        except Exception as e:
            print(f"⚠️ Index warning: {e}")
        
        # Commit changes
        conn.commit()
        
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
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = add_columns()
    exit(0 if success else 1)
