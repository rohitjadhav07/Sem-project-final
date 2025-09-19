#!/usr/bin/env python3
"""
Script to activate lectures for testing
"""

from app import create_app
from models.lecture import Lecture
from app import db
from datetime import datetime, timedelta

def activate_lectures():
    app = create_app()
    with app.app_context():
        # Get all lectures
        lectures = Lecture.query.all()
        
        print(f"Found {len(lectures)} lectures")
        
        # Set some lectures to be active today
        now = datetime.now()
        
        for i, lecture in enumerate(lectures):
            if i < 2:  # Make first 2 lectures active
                # Set to start 30 minutes ago and end in 30 minutes
                lecture.scheduled_start = now - timedelta(minutes=30)
                lecture.scheduled_end = now + timedelta(minutes=30)
                lecture.status = 'active'
                lecture.is_active = True
                print(f"Activated lecture: {lecture.title} (ID: {lecture.id})")
            elif i < 4:  # Make next 2 lectures scheduled for later today
                # Set to start in 2 hours
                lecture.scheduled_start = now + timedelta(hours=2)
                lecture.scheduled_end = now + timedelta(hours=3)
                lecture.status = 'scheduled'
                lecture.is_active = True
                print(f"Scheduled lecture: {lecture.title} (ID: {lecture.id}) for {lecture.scheduled_start.strftime('%H:%M')}")
        
        db.session.commit()
        print("\nLectures updated successfully!")
        
        # Show current status
        print("\nCurrent Lecture Status:")
        for lecture in Lecture.query.all():
            print(f"  {lecture.id}: {lecture.title} - {lecture.status} - {lecture.scheduled_start.strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    activate_lectures()