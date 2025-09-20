"""
Database persistence manager for Vercel deployment
"""
import os
import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    """Manage database persistence across serverless function calls"""
    
    def __init__(self):
        self.db_path = '/tmp/geo_attendance_persistent.db'
        self.backup_data_file = '/tmp/app_data_backup.json'
    
    def backup_database_to_json(self, db_session):
        """Backup database to JSON for persistence"""
        try:
            from models.user import User
            from models.course import Course
            from models.lecture import Lecture
            from models.enrollment import Enrollment
            from models.attendance import Attendance
            
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'users': [],
                'courses': [],
                'lectures': [],
                'enrollments': [],
                'attendances': []
            }
            
            # Backup users
            for user in User.query.all():
                backup_data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'phone': user.phone,
                    'student_id': user.student_id,
                    'employee_id': user.employee_id,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })
            
            # Backup courses
            for course in Course.query.all():
                backup_data['courses'].append({
                    'id': course.id,
                    'name': course.name,
                    'code': course.code,
                    'description': course.description,
                    'teacher_id': course.teacher_id,
                    'location_name': course.location_name,
                    'latitude': course.latitude,
                    'longitude': course.longitude,
                    'geofence_radius': course.geofence_radius,
                    'is_active': course.is_active,
                    'created_at': course.created_at.isoformat() if course.created_at else None
                })
            
            # Backup lectures
            for lecture in Lecture.query.all():
                backup_data['lectures'].append({
                    'id': lecture.id,
                    'course_id': lecture.course_id,
                    'teacher_id': lecture.teacher_id,
                    'title': lecture.title,
                    'description': lecture.description,
                    'latitude': lecture.latitude,
                    'longitude': lecture.longitude,
                    'location_name': lecture.location_name,
                    'geofence_radius': lecture.geofence_radius,
                    'scheduled_start': lecture.scheduled_start.isoformat() if lecture.scheduled_start else None,
                    'scheduled_end': lecture.scheduled_end.isoformat() if lecture.scheduled_end else None,
                    'status': lecture.status,
                    'is_active': lecture.is_active,
                    'attendance_window_start': lecture.attendance_window_start,
                    'attendance_window_end': lecture.attendance_window_end,
                    'location_locked': lecture.location_locked,
                    'location_accuracy': lecture.location_accuracy,
                    'location_set_at': lecture.location_set_at.isoformat() if lecture.location_set_at else None
                })
            
            # Backup enrollments
            for enrollment in Enrollment.query.all():
                backup_data['enrollments'].append({
                    'id': enrollment.id,
                    'student_id': enrollment.student_id,
                    'course_id': enrollment.course_id,
                    'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
                    'is_active': enrollment.is_active
                })
            
            # Backup attendances
            for attendance in Attendance.query.all():
                backup_data['attendances'].append({
                    'id': attendance.id,
                    'student_id': attendance.student_id,
                    'lecture_id': attendance.lecture_id,
                    'status': attendance.status,
                    'marked_at': attendance.marked_at.isoformat() if attendance.marked_at else None,
                    'student_latitude': attendance.student_latitude,
                    'student_longitude': attendance.student_longitude,
                    'distance_from_lecture': attendance.distance_from_lecture
                })
            
            # Write to file
            with open(self.backup_data_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Database backed up to {self.backup_data_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return False
    
    def restore_database_from_json(self, db_session):
        """Restore database from JSON backup"""
        try:
            if not os.path.exists(self.backup_data_file):
                print("No backup file found, skipping restore")
                return False
            
            from models.user import User
            from models.course import Course
            from models.lecture import Lecture
            from models.enrollment import Enrollment
            from models.attendance import Attendance
            from datetime import datetime, timezone, timedelta
            
            # IST timezone
            IST = timezone(timedelta(hours=5, minutes=30))
            
            with open(self.backup_data_file, 'r') as f:
                backup_data = json.load(f)
            
            # Check if data is recent (within last hour)
            backup_time = datetime.fromisoformat(backup_data['timestamp'])
            if (datetime.utcnow() - backup_time).total_seconds() > 3600:  # 1 hour
                print("Backup data is too old, skipping restore")
                return False
            
            # Restore users
            for user_data in backup_data['users']:
                if not User.query.get(user_data['id']):
                    user = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        role=user_data['role'],
                        is_active=user_data['is_active'],
                        phone=user_data['phone'],
                        student_id=user_data['student_id'],
                        employee_id=user_data['employee_id']
                    )
                    if user_data['created_at']:
                        user.created_at = datetime.fromisoformat(user_data['created_at'])
                    db_session.add(user)
            
            # Restore courses
            for course_data in backup_data['courses']:
                if not Course.query.get(course_data['id']):
                    course = Course(
                        id=course_data['id'],
                        name=course_data['name'],
                        code=course_data['code'],
                        description=course_data['description'],
                        teacher_id=course_data['teacher_id'],
                        location_name=course_data['location_name'],
                        latitude=course_data['latitude'],
                        longitude=course_data['longitude'],
                        geofence_radius=course_data['geofence_radius'],
                        is_active=course_data['is_active']
                    )
                    if course_data['created_at']:
                        course.created_at = datetime.fromisoformat(course_data['created_at'])
                    db_session.add(course)
            
            # Restore lectures
            for lecture_data in backup_data['lectures']:
                if not Lecture.query.get(lecture_data['id']):
                    lecture = Lecture(
                        id=lecture_data['id'],
                        course_id=lecture_data['course_id'],
                        teacher_id=lecture_data['teacher_id'],
                        title=lecture_data['title'],
                        description=lecture_data['description'],
                        latitude=lecture_data['latitude'],
                        longitude=lecture_data['longitude'],
                        location_name=lecture_data['location_name'],
                        geofence_radius=lecture_data['geofence_radius'],
                        status=lecture_data['status'],
                        is_active=lecture_data['is_active'],
                        attendance_window_start=lecture_data['attendance_window_start'],
                        attendance_window_end=lecture_data['attendance_window_end'],
                        location_locked=lecture_data['location_locked'],
                        location_accuracy=lecture_data['location_accuracy']
                    )
                    if lecture_data['scheduled_start']:
                        lecture.scheduled_start = datetime.fromisoformat(lecture_data['scheduled_start'])
                    if lecture_data['scheduled_end']:
                        lecture.scheduled_end = datetime.fromisoformat(lecture_data['scheduled_end'])
                    if lecture_data['location_set_at']:
                        lecture.location_set_at = datetime.fromisoformat(lecture_data['location_set_at'])
                    db_session.add(lecture)
            
            # Restore enrollments
            for enrollment_data in backup_data['enrollments']:
                if not Enrollment.query.get(enrollment_data['id']):
                    enrollment = Enrollment(
                        id=enrollment_data['id'],
                        student_id=enrollment_data['student_id'],
                        course_id=enrollment_data['course_id'],
                        is_active=enrollment_data['is_active']
                    )
                    if enrollment_data['enrollment_date']:
                        enrollment.enrollment_date = datetime.fromisoformat(enrollment_data['enrollment_date'])
                    db_session.add(enrollment)
            
            # Restore attendances
            for attendance_data in backup_data['attendances']:
                if not Attendance.query.get(attendance_data['id']):
                    attendance = Attendance(
                        id=attendance_data['id'],
                        student_id=attendance_data['student_id'],
                        lecture_id=attendance_data['lecture_id'],
                        status=attendance_data['status'],
                        student_latitude=attendance_data['student_latitude'],
                        student_longitude=attendance_data['student_longitude'],
                        distance_from_lecture=attendance_data['distance_from_lecture']
                    )
                    if attendance_data['marked_at']:
                        attendance.marked_at = datetime.fromisoformat(attendance_data['marked_at'])
                    db_session.add(attendance)
            
            db_session.commit()
            print("✅ Database restored from backup")
            return True
            
        except Exception as e:
            print(f"❌ Error restoring database: {e}")
            db_session.rollback()
            return False

# Global instance
db_manager = DatabaseManager()