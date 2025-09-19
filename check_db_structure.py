#!/usr/bin/env python3
"""
Check database structure
"""

import sqlite3
import os

def check_database():
    """Check the current database structure"""
    
    db_path = 'geo_attendance.db'
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Database tables:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check each table structure
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name} table structure:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()