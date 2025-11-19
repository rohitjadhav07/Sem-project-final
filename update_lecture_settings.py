#!/usr/bin/env python3
"""
Update existing lectures with better GPS accuracy settings
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
from models.lecture import Lecture
from sqlalchemy import text


def update_lecture_settings():
    """Update all lectures with stricter GPS accuracy requirements"""
    
    app = create_app('production')
    
    with app.app_context():
        print("\n" + "="*60)
        print("UPDATING LECTURE GPS ACCURACY SETTINGS")
        print("="*60 + "\n")
        
        try:
            # Get all lectures
            lectures = Lecture.query.all()
            print(f"Found {len(lectures)} lectures\n")
            
            updated_count = 0
            
            for lecture in lectures:
                print(f"Updating: {lecture.title} (ID: {lecture.id})")
                
                # Set GPS accuracy threshold to 20m (was probably not set)
                if not lecture.gps_accuracy_threshold or lecture.gps_accuracy_threshold > 20:
                    lecture.gps_accuracy_threshold = 20
                    print(f"  ✅ Set GPS accuracy threshold to 20m")
                
                # Reduce geofence radius if it's too large
                if lecture.geofence_radius and lecture.geofence_radius > 50:
                    old_radius = lecture.geofence_radius
                    lecture.geofence_radius = 50
                    print(f"  ✅ Reduced radius from {old_radius}m to 50m")
                
                # Set boundary tolerance
                if not lecture.boundary_tolerance_m:
                    lecture.boundary_tolerance_m = 2.0
                    print(f"  ✅ Set boundary tolerance to 2.0m")
                
                updated_count += 1
                print()
            
            # Commit changes
            db.session.commit()
            
            print("="*60)
            print(f"UPDATED {updated_count} LECTURES")
            print("="*60)
            print("\nNew settings:")
            print("  ✓ GPS accuracy threshold: 20m (rejects GPS > 20m)")
            print("  ✓ Maximum geofence radius: 50m")
            print("  ✓ Boundary tolerance: 2.0m")
            print("\nStudents will now need GPS accuracy ≤20m to check in.\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Update failed: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = update_lecture_settings()
    sys.exit(0 if success else 1)
