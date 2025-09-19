import csv
import io
from datetime import datetime, timedelta
from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd

def generate_attendance_report(course_id=None, student_id=None, start_date=None, end_date=None, format='dict'):
    """
    Generate attendance report with various filters
    """
    from models.attendance import Attendance
    from models.lecture import Lecture
    from models.course import Course
    from models.user import User
    
    query = Attendance.query.join(Lecture).join(Course).join(User)
    
    # Apply filters
    if course_id:
        query = query.filter(Course.id == course_id)
    
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    
    if start_date:
        query = query.filter(Lecture.scheduled_start >= start_date)
    
    if end_date:
        query = query.filter(Lecture.scheduled_start <= end_date)
    
    attendances = query.order_by(Lecture.scheduled_start.desc()).all()
    
    if format == 'dict':
        return [attendance.to_dict() for attendance in attendances]
    elif format == 'dataframe':
        data = []
        for attendance in attendances:
            data.append({
                'Student Name': attendance.student.full_name,
                'Student ID': attendance.student.student_id,
                'Course Code': attendance.lecture.course.code,
                'Course Name': attendance.lecture.course.name,
                'Lecture Title': attendance.lecture.title,
                'Scheduled Date': attendance.lecture.scheduled_start.strftime('%Y-%m-%d'),
                'Scheduled Time': attendance.lecture.scheduled_start.strftime('%H:%M'),
                'Status': attendance.status.title(),
                'Marked At': attendance.marked_at.strftime('%Y-%m-%d %H:%M:%S') if attendance.marked_at else '',
                'Distance (m)': attendance.distance_from_lecture,
                'Auto Marked': 'Yes' if attendance.auto_marked else 'No'
            })
        return pd.DataFrame(data)
    
    return attendances

def export_to_csv(data, filename=None):
    """
    Export attendance data to CSV format
    """
    if filename is None:
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    output = io.StringIO()
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(output, index=False)
    else:
        # Assume it's a list of dictionaries
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    output.seek(0)
    return output.getvalue(), filename

def export_to_pdf(data, title="Attendance Report", filename=None):
    """
    Export attendance data to PDF format
    """
    if filename is None:
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Generation info
    info_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    if isinstance(data, pd.DataFrame):
        # Convert DataFrame to list of lists for table
        table_data = [data.columns.tolist()] + data.values.tolist()
    else:
        # Convert list of dicts to table format
        if data:
            headers = ['Student Name', 'Course', 'Lecture', 'Date', 'Status', 'Marked At']
            table_data = [headers]
            
            for item in data:
                row = [
                    item.get('student_name', ''),
                    f"{item.get('course_code', '')} - {item.get('course_name', '')}",
                    item.get('lecture_title', ''),
                    item.get('marked_at', '').split('T')[0] if item.get('marked_at') else '',
                    item.get('status', '').title(),
                    item.get('marked_at', '').split('T')[1][:8] if item.get('marked_at') else ''
                ]
                table_data.append(row)
        else:
            table_data = [['No data available']]
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue(), filename

def generate_course_summary(course_id, start_date=None, end_date=None):
    """
    Generate course attendance summary
    """
    from models.course import Course
    from models.enrollment import Enrollment
    from models.lecture import Lecture
    from models.attendance import Attendance
    
    course = Course.query.get(course_id)
    if not course:
        return None
    
    # Get enrollments
    enrollments = Enrollment.query.filter_by(course_id=course_id, is_active=True).all()
    
    # Get lectures in date range
    lecture_query = Lecture.query.filter_by(course_id=course_id, is_active=True)
    if start_date:
        lecture_query = lecture_query.filter(Lecture.scheduled_start >= start_date)
    if end_date:
        lecture_query = lecture_query.filter(Lecture.scheduled_start <= end_date)
    
    lectures = lecture_query.order_by(Lecture.scheduled_start).all()
    
    summary = {
        'course': course.to_dict(),
        'total_students': len(enrollments),
        'total_lectures': len(lectures),
        'students': [],
        'lectures': []
    }
    
    # Student summaries
    for enrollment in enrollments:
        student_attendances = Attendance.query.join(Lecture).filter(
            Attendance.student_id == enrollment.student_id,
            Lecture.course_id == course_id
        ).all()
        
        present_count = sum(1 for a in student_attendances if a.status == 'present')
        late_count = sum(1 for a in student_attendances if a.status == 'late')
        absent_count = sum(1 for a in student_attendances if a.status == 'absent')
        
        attendance_rate = (present_count + late_count) / len(lectures) * 100 if lectures else 0
        
        summary['students'].append({
            'student': enrollment.student.to_dict(),
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'attendance_rate': round(attendance_rate, 2)
        })
    
    # Lecture summaries
    for lecture in lectures:
        stats = lecture.get_attendance_stats()
        summary['lectures'].append({
            'lecture': lecture.to_dict(),
            'stats': stats
        })
    
    return summary