#!/usr/bin/env python3
"""
Migration script to add enhanced location security fields to existing database
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new location security fields to the database"""
    
    db_path = 'geo_attendance.db'
    
    if not os.path.exists(db_path):
        print("Database not found. Please run init_db.py first.")
        return
    
    print("Starting database migration for enhanced location security...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(lectures)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = [
            'location_hash',
            'location_device_info',
            'location_ip_address',
            'location_verification_status',
            'location_confirmation_count',
            'location_last_verified',
            'min_accuracy_required',
            'allow_location_updates',
            'location_verification_required',
            'require_location_confirmation'
        ]
        
        # Add missing columns
        for column in new_columns:
            if column not in columns:
                print(f"Adding column: {column}")
                
                if column == 'location_hash':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_hash VARCHAR(64)")
                elif column == 'location_device_info':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_device_info TEXT")
                elif column == 'location_ip_address':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_ip_address VARCHAR(45)")
                elif column == 'location_verification_status':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_verification_status VARCHAR(20) DEFAULT 'pending'")
                elif column == 'location_confirmation_count':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_confirmation_count INTEGER DEFAULT 0")
                elif column == 'location_last_verified':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_last_verified DATETIME")
                elif column == 'min_accuracy_required':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN min_accuracy_required INTEGER DEFAULT 10")
                elif column == 'allow_location_updates':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN allow_location_updates BOOLEAN DEFAULT 0")
                elif column == 'location_verification_required':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN location_verification_required BOOLEAN DEFAULT 1")
                elif column == 'require_location_confirmation':
                    cursor.execute("ALTER TABLE lectures ADD COLUMN require_location_confirmation BOOLEAN DEFAULT 1")
        
        # Check attendances table for enhanced fields
        cursor.execute("PRAGMA table_info(attendances)")
        attendance_columns = [column[1] for column in cursor.fetchall()]
        
        attendance_new_columns = [
            'metadata'  # Only add metadata if missing, others already exist
        ]
        
        for column in attendance_new_columns:
            if column not in attendance_columns:
                print(f"Adding attendance column: {column}")
                
                if column == 'metadata':
                    cursor.execute("ALTER TABLE attendances ADD COLUMN metadata TEXT")
        
        # Update existing lectures with default security settings
        cursor.execute("""
            UPDATE lectures 
            SET location_verification_status = 'pending',
                location_confirmation_count = 0,
                min_accuracy_required = 10,
                allow_location_updates = 0,
                location_verification_required = 1,
                require_location_confirmation = 1
            WHERE location_verification_status IS NULL
        """)
        
        # For lectures that already have location set, mark them as verified
        cursor.execute("""
            UPDATE lectures 
            SET location_verification_status = 'verified',
                location_confirmation_count = 1,
                location_last_verified = datetime('now')
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND location_verification_status = 'pending'
        """)
        
        conn.commit()
        print("Database migration completed successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM lectures WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        lectures_with_location = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lectures")
        total_lectures = cursor.fetchone()[0]
        
        print(f"\nSummary:")
        print(f"- Total lectures: {total_lectures}")
        print(f"- Lectures with location: {lectures_with_location}")
        print(f"- Enhanced security features added")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()