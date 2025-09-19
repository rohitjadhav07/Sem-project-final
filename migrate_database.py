#!/usr/bin/env python3
"""
Database migration script to add enhanced location security fields
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate existing database to include new location security fields"""
    
    db_path = 'geo_attendance.db'
    
    if not os.path.exists(db_path):
        print("Database not found. Please run init_db.py first.")
        return False
    
    print("Starting database migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(lectures)")
        lecture_columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(attendances)")
        attendance_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current lecture columns: {lecture_columns}")
        print(f"Current attendance columns: {attendance_columns}")
        
        # Add new columns to lectures table
        lecture_migrations = [
            ("location_accuracy", "REAL"),
            ("location_metadata", "TEXT"),
            ("location_set_at", "DATETIME"),
            ("location_locked", "BOOLEAN DEFAULT 0"),
            ("location_hash", "VARCHAR(64)"),
            ("location_device_info", "TEXT"),
            ("min_accuracy_required", "INTEGER DEFAULT 20"),
            ("allow_location_updates", "BOOLEAN DEFAULT 1"),
            ("location_verification_required", "BOOLEAN DEFAULT 1")
        ]
        
        for column_name, column_type in lecture_migrations:
            if column_name not in lecture_columns:
                try:
                    cursor.execute(f"ALTER TABLE lectures ADD COLUMN {column_name} {column_type}")
                    print(f"✓ Added column {column_name} to lectures table")
                except sqlite3.Error as e:
                    print(f"✗ Error adding {column_name}: {e}")
        
        # Add new columns to attendances table
        attendance_migrations = [
            ("student_latitude", "REAL"),
            ("student_longitude", "REAL"),
            ("location_accuracy", "VARCHAR(50)"),
            ("security_score", "INTEGER"),
            ("location_metadata", "TEXT")
        ]
        
        for column_name, column_type in attendance_migrations:
            if column_name not in attendance_columns:
                try:
                    cursor.execute(f"ALTER TABLE attendances ADD COLUMN {column_name} {column_type}")
                    print(f"✓ Added column {column_name} to attendances table")
                except sqlite3.Error as e:
                    print(f"✗ Error adding {column_name}: {e}")
        
        # Update existing lectures to have location_locked = True if they have coordinates
        cursor.execute("""
            UPDATE lectures 
            SET location_locked = 1, location_set_at = created_at 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        
        # Copy marked_latitude/longitude to student_latitude/longitude in attendances
        cursor.execute("""
            UPDATE attendances 
            SET student_latitude = marked_latitude, student_longitude = marked_longitude 
            WHERE marked_latitude IS NOT NULL AND marked_longitude IS NOT NULL
        """)
        
        conn.commit()
        print("✓ Database migration completed successfully!")
        
        # Verify migration
        cursor.execute("PRAGMA table_info(lectures)")
        new_lecture_columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(attendances)")
        new_attendance_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"New lecture columns: {len(new_lecture_columns)} total")
        print(f"New attendance columns: {len(new_attendance_columns)} total")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

def create_location_hashes():
    """Create location hashes for existing lectures"""
    import hashlib
    
    db_path = 'geo_attendance.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get lectures with coordinates but no hash
        cursor.execute("""
            SELECT id, latitude, longitude, location_set_at 
            FROM lectures 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND (location_hash IS NULL OR location_hash = '')
        """)
        
        lectures = cursor.fetchall()
        
        for lecture_id, lat, lng, set_at in lectures:
            if set_at:
                location_string = f"{lat}:{lng}:{set_at}"
            else:
                location_string = f"{lat}:{lng}:{datetime.now().isoformat()}"
            
            location_hash = hashlib.sha256(location_string.encode()).hexdigest()
            
            cursor.execute("""
                UPDATE lectures 
                SET location_hash = ? 
                WHERE id = ?
            """, (location_hash, lecture_id))
        
        conn.commit()
        print(f"✓ Created location hashes for {len(lectures)} lectures")
        
    except Exception as e:
        print(f"Error creating location hashes: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Enhanced Location Security Database Migration")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("\nCreating location hashes...")
        create_location_hashes()
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("\nNew features added:")
        print("• Enhanced location precision (8 decimal places)")
        print("• Location locking and integrity verification")
        print("• GPS accuracy requirements and validation")
        print("• Security scoring for location data")
        print("• Device fingerprinting for anti-spoofing")
        print("• Comprehensive location metadata storage")
        
        print("\nYou can now:")
        print("1. Create lectures with high-precision location capture")
        print("2. Set GPS accuracy requirements")
        print("3. Lock locations to prevent tampering")
        print("4. View detailed location security information")
        print("5. Detect potential location spoofing attempts")
    else:
        print("\nMigration failed. Please check the errors above.")