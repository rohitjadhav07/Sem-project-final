"""
Comprehensive Test Suite for Geo Attendance Pro
Tests all major components and generates detailed report
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test results storage
test_results = {
    'timestamp': datetime.now().isoformat(),
    'tests': [],
    'summary': {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }
}

def log_test(name, status, message, details=None):
    """Log test result"""
    test_results['tests'].append({
        'name': name,
        'status': status,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    test_results['summary']['total'] += 1
    test_results['summary'][status] += 1
    
    icon = '✅' if status == 'passed' else '❌' if status == 'failed' else '⏭️'
    print(f"{icon} {name}: {message}")
    if details:
        print(f"   Details: {details}")

print("=" * 80)
print("GEO ATTENDANCE PRO - COMPREHENSIVE TEST SUITE")
print("=" * 80)
print()

# Test 1: Environment Configuration
print("📋 Test Category: Environment Configuration")
print("-" * 80)

try:
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and secret_key != 'your-secret-key-here':
        log_test('Environment: SECRET_KEY', 'passed', 'Secret key configured')
    else:
        log_test('Environment: SECRET_KEY', 'failed', 'Secret key not configured or using default')
except Exception as e:
    log_test('Environment: SECRET_KEY', 'failed', str(e))

try:
    db_url = os.getenv('DATABASE_URL')
    if db_url and 'supabase' in db_url:
        log_test('Environment: DATABASE_URL', 'passed', 'Supabase database configured')
    elif db_url:
        log_test('Environment: DATABASE_URL', 'passed', 'Database configured')
    else:
        log_test('Environment: DATABASE_URL', 'failed', 'Database URL not configured')
except Exception as e:
    log_test('Environment: DATABASE_URL', 'failed', str(e))

try:
    google_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if google_key and google_key != 'your-google-maps-api-key':
        log_test('Environment: GOOGLE_MAPS_API_KEY', 'passed', f'API key configured ({google_key[:20]}...)')
    else:
        log_test('Environment: GOOGLE_MAPS_API_KEY', 'failed', 'Google Maps API key not configured')
except Exception as e:
    log_test('Environment: GOOGLE_MAPS_API_KEY', 'failed', str(e))

print()

# Test 2: File Structure
print("📁 Test Category: File Structure")
print("-" * 80)

required_files = [
    ('static/js/enhanced_gps.js', 'Enhanced GPS module'),
    ('static/js/hybrid_location.js', 'Hybrid location system'),
    ('templates/teacher/create_lecture_enhanced.html', 'Teacher create lecture template'),
    ('templates/student/dashboard.html', 'Student dashboard template'),
    ('utils/rectangular_geofence.py', 'Rectangular geofence utilities'),
    ('models/lecture.py', 'Lecture model'),
    ('models/attendance.py', 'Attendance model'),
    ('routes/teacher.py', 'Teacher routes'),
    ('routes/student.py', 'Student routes'),
    ('config.py', 'Configuration file'),
    ('.env', 'Environment variables'),
]

for file_path, description in required_files:
    if os.path.exists(file_path):
        log_test(f'File: {description}', 'passed', f'{file_path} exists')
    else:
        log_test(f'File: {description}', 'failed', f'{file_path} not found')

print()

# Test 3: Python Imports
print("🐍 Test Category: Python Imports")
print("-" * 80)

try:
    import flask
    log_test('Import: Flask', 'passed', f'Flask {flask.__version__}')
except ImportError as e:
    log_test('Import: Flask', 'failed', str(e))

try:
    import sqlalchemy
    log_test('Import: SQLAlchemy', 'passed', f'SQLAlchemy {sqlalchemy.__version__}')
except ImportError as e:
    log_test('Import: SQLAlchemy', 'failed', str(e))

try:
    from flask_login import LoginManager
    log_test('Import: Flask-Login', 'passed', 'Flask-Login available')
except ImportError as e:
    log_test('Import: Flask-Login', 'failed', str(e))

try:
    import requests
    log_test('Import: Requests', 'passed', f'Requests {requests.__version__}')
except ImportError as e:
    log_test('Import: Requests', 'failed', str(e))

print()

# Test 4: Google Geolocation API
print("🌐 Test Category: Google Geolocation API")
print("-" * 80)

try:
    import requests
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not api_key or api_key == 'your-google-maps-api-key':
        log_test('Google API: Configuration', 'skipped', 'API key not configured')
    else:
        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
        response = requests.post(
            url,
            json={"considerIp": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test('Google API: Connection', 'passed', 
                    f"API working, Location: {data['location']['lat']:.4f}, {data['location']['lng']:.4f}, Accuracy: ±{data['accuracy']}m")
        elif response.status_code == 403:
            log_test('Google API: Connection', 'failed', 
                    'API key invalid or restricted. Enable Geolocation API in Google Cloud Console')
        elif response.status_code == 429:
            log_test('Google API: Connection', 'failed', 'Quota exceeded')
        else:
            log_test('Google API: Connection', 'failed', f'HTTP {response.status_code}: {response.text}')
            
except Exception as e:
    log_test('Google API: Connection', 'failed', str(e))

print()

# Test 5: Database Connection
print("🗄️  Test Category: Database Connection")
print("-" * 80)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        log_test('Database: Connection', 'skipped', 'DATABASE_URL not configured')
    else:
        # Handle postgres:// vs postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(db_url, poolclass=NullPool, connect_args={'connect_timeout': 10})
        connection = engine.connect()
        connection.close()
        log_test('Database: Connection', 'passed', 'Successfully connected to database')
        
        # Test tables exist
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = ['users', 'courses', 'lectures', 'attendances', 'enrollments']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if not missing_tables:
                log_test('Database: Tables', 'passed', f'All required tables exist ({len(tables)} total)')
            else:
                log_test('Database: Tables', 'failed', f'Missing tables: {missing_tables}')
                
        except Exception as e:
            log_test('Database: Tables', 'failed', str(e))
            
except Exception as e:
    log_test('Database: Connection', 'failed', str(e))

print()

# Test 6: Rectangular Geofence Module
print("📐 Test Category: Rectangular Geofence")
print("-" * 80)

try:
    sys.path.insert(0, os.path.dirname(__file__))
    from utils.rectangular_geofence import RectangularBoundary, point_in_rectangular_boundary
    
    # Test boundary creation
    boundary = RectangularBoundary.from_center_and_dimensions(
        40.7128, -74.0060,  # NYC coordinates
        30, 30  # 30m x 30m
    )
    log_test('Geofence: Boundary Creation', 'passed', 
            f'Created 30m×30m boundary, Area: {boundary.calculate_area():.1f}m²')
    
    # Test point inside
    center = boundary.get_center()
    result = point_in_rectangular_boundary(center[0], center[1], boundary)
    if result['inside']:
        log_test('Geofence: Point Inside', 'passed', 'Center point correctly identified as inside')
    else:
        log_test('Geofence: Point Inside', 'failed', 'Center point incorrectly identified as outside')
    
    # Test point outside
    result = point_in_rectangular_boundary(center[0] + 0.001, center[1] + 0.001, boundary)
    if not result['inside']:
        log_test('Geofence: Point Outside', 'passed', 'Far point correctly identified as outside')
    else:
        log_test('Geofence: Point Outside', 'failed', 'Far point incorrectly identified as inside')
        
except Exception as e:
    log_test('Geofence: Module', 'failed', str(e))

print()

# Test 7: Application Startup
print("🚀 Test Category: Application Startup")
print("-" * 80)

try:
    from app import create_app
    app = create_app()
    log_test('App: Creation', 'passed', 'Flask app created successfully')
    
    # Test routes registered
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    required_routes = ['/teacher/lectures/create', '/student/dashboard', '/student/api/checkin']
    
    missing_routes = [r for r in required_routes if not any(r in route for route in routes)]
    if not missing_routes:
        log_test('App: Routes', 'passed', f'{len(routes)} routes registered')
    else:
        log_test('App: Routes', 'failed', f'Missing routes: {missing_routes}')
        
except Exception as e:
    log_test('App: Creation', 'failed', str(e))

print()

# Test 8: JavaScript Files
print("📜 Test Category: JavaScript Files")
print("-" * 80)

try:
    with open('static/js/hybrid_location.js', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'HybridLocationSystem' in content:
            log_test('JavaScript: HybridLocationSystem', 'passed', 'Class defined')
        else:
            log_test('JavaScript: HybridLocationSystem', 'failed', 'Class not found')
            
        if 'tryGoogleGeolocation' in content:
            log_test('JavaScript: Google API Integration', 'passed', 'Method defined')
        else:
            log_test('JavaScript: Google API Integration', 'failed', 'Method not found')
            
except Exception as e:
    log_test('JavaScript: Files', 'failed', str(e))

try:
    with open('static/js/enhanced_gps.js', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'EnhancedGPS' in content:
            log_test('JavaScript: EnhancedGPS', 'passed', 'Class defined')
        else:
            log_test('JavaScript: EnhancedGPS', 'failed', 'Class not found')
            
        if 'GPSKalmanFilter' in content:
            log_test('JavaScript: Kalman Filter', 'passed', 'Class defined')
        else:
            log_test('JavaScript: Kalman Filter', 'failed', 'Class not found')
            
except Exception as e:
    log_test('JavaScript: Enhanced GPS', 'failed', str(e))

print()

# Generate Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total Tests: {test_results['summary']['total']}")
print(f"✅ Passed: {test_results['summary']['passed']}")
print(f"❌ Failed: {test_results['summary']['failed']}")
print(f"⏭️  Skipped: {test_results['summary']['skipped']}")
print()

success_rate = (test_results['summary']['passed'] / test_results['summary']['total'] * 100) if test_results['summary']['total'] > 0 else 0
print(f"Success Rate: {success_rate:.1f}%")
print()

# Save results to JSON
with open('test_results.json', 'w') as f:
    json.dump(test_results, f, indent=2)
print("📄 Detailed results saved to: test_results.json")

# Generate HTML report
html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Geo Attendance Pro - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat.total {{ background: #2196F3; color: white; }}
        .stat.passed {{ background: #4CAF50; color: white; }}
        .stat.failed {{ background: #f44336; color: white; }}
        .stat.skipped {{ background: #FF9800; color: white; }}
        .stat h2 {{ margin: 0; font-size: 36px; }}
        .stat p {{ margin: 5px 0 0 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .passed {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        .skipped {{ color: #FF9800; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Geo Attendance Pro - Test Report</h1>
        <p class="timestamp">Generated: {test_results['timestamp']}</p>
        
        <div class="summary">
            <div class="stat total">
                <h2>{test_results['summary']['total']}</h2>
                <p>Total Tests</p>
            </div>
            <div class="stat passed">
                <h2>{test_results['summary']['passed']}</h2>
                <p>Passed</p>
            </div>
            <div class="stat failed">
                <h2>{test_results['summary']['failed']}</h2>
                <p>Failed</p>
            </div>
            <div class="stat skipped">
                <h2>{test_results['summary']['skipped']}</h2>
                <p>Skipped</p>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Message</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""

for test in test_results['tests']:
    status_class = test['status']
    status_icon = '✅' if test['status'] == 'passed' else '❌' if test['status'] == 'failed' else '⏭️'
    details = test['details'] if test['details'] else '-'
    html_report += f"""
                <tr>
                    <td>{test['name']}</td>
                    <td class="{status_class}">{status_icon} {test['status'].upper()}</td>
                    <td>{test['message']}</td>
                    <td>{details}</td>
                </tr>
"""

html_report += """
            </tbody>
        </table>
        
        <h2>Recommendations</h2>
        <ul>
"""

if test_results['summary']['failed'] > 0:
    html_report += "<li>⚠️ Review failed tests and fix issues before deployment</li>"
if test_results['summary']['skipped'] > 0:
    html_report += "<li>💡 Complete skipped tests by configuring missing components</li>"
if test_results['summary']['passed'] == test_results['summary']['total']:
    html_report += "<li>✅ All tests passed! System is ready for deployment</li>"

html_report += """
        </ul>
    </div>
</body>
</html>
"""

with open('test_report.html', 'w', encoding='utf-8') as f:
    f.write(html_report)
print("📊 HTML report saved to: test_report.html")

print()
print("=" * 80)
if test_results['summary']['failed'] == 0:
    print("✅ ALL TESTS PASSED! System is ready.")
else:
    print("⚠️  Some tests failed. Please review and fix issues.")
print("=" * 80)
