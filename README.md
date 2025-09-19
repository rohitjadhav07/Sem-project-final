# Geo Attendance Pro

A comprehensive location-based attendance management system for educational institutions. Students can mark attendance only when physically present at the lecture location using GPS verification.

## Features

### 🎯 Core Features
- **Location-Based Attendance**: GPS geofencing ensures students are physically present
- **Multi-Role Support**: Separate interfaces for administrators, teachers, and students
- **Real-Time Tracking**: Live attendance monitoring and updates
- **Comprehensive Reports**: Detailed analytics and attendance reports
- **Mobile Responsive**: Works perfectly on smartphones, tablets, and desktops

### 👨‍💼 Admin Features
- User management (students, teachers, admins)
- Course management and assignment
- System-wide attendance reports
- Audit logs and security monitoring
- System configuration and settings

### 👨‍🏫 Teacher Features
- Create and manage lectures with GPS coordinates
- Set geofence radius for attendance areas
- Start/stop lectures and manage attendance windows
- Manual attendance marking and corrections
- Course-specific attendance reports
- Student performance analytics

### 👨‍🎓 Student Features
- View enrolled courses and upcoming lectures
- Location-based check-in for active lectures
- Attendance history and statistics
- Course enrollment with course codes
- Real-time lecture availability

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5 with responsive design
- **Authentication**: Flask-Login + JWT for API access
- **Location Services**: HTML5 Geolocation API
- **Security**: CSRF protection, password hashing, audit logging

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd geo_attendance_pro
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env with your settings
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///geo_attendance.db
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://127.0.0.1:5000`

## Default Login Credentials

After running `init_db.py`, you can use these default accounts:

- **Admin**: `admin` / `admin123`
- **Teacher**: `teacher1` / `teacher123`
- **Students**: `student1` to `student5` / `student123`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite:///geo_attendance.db` |
| `JWT_SECRET_KEY` | JWT token secret | `jwt-secret-change-in-production` |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key (optional) | None |
| `GEOFENCE_RADIUS` | Default geofence radius in meters | `50` |
| `LOCATION_UPDATE_INTERVAL` | Location update interval in seconds | `5` |

### Geofencing Settings

- **Default Radius**: 50 meters (configurable per lecture)
- **Attendance Window**: 15 minutes before to 15 minutes after lecture start
- **Location Accuracy**: Uses high-accuracy GPS when available

## API Endpoints

### Authentication
- `POST /api/auth/login` - API login with JWT tokens
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/me` - Get current user info

### Student API
- `GET /api/student/dashboard` - Dashboard data
- `POST /api/student/checkin` - Mark attendance
- `GET /api/student/lectures/active` - Get active lectures

### Attendance API
- `POST /api/attendance/mark` - Mark attendance
- `POST /api/attendance/check-location` - Verify location
- `GET /api/attendance/student/<id>` - Student attendance records
- `GET /api/attendance/lecture/<id>` - Lecture attendance records

## Usage Guide

### For Students

1. **Enroll in Courses**
   - Go to "My Courses" → "Enroll in Course"
   - Enter the course code provided by your teacher
   - Click "Enroll"

2. **Mark Attendance**
   - Check "Active Lectures" on your dashboard
   - Click "Check In" for available lectures
   - Allow location access when prompted
   - Confirm check-in if within the geofence area

3. **View History**
   - Go to "Attendance History" to see all records
   - Filter by course, status, or date range
   - View detailed statistics and trends

### For Teachers

1. **Create Lectures**
   - Go to "Lectures" → "Create New Lecture"
   - Fill in lecture details and location
   - Set geofence radius (recommended: 50-100m)
   - Use "Get Current Location" for easy setup

2. **Manage Attendance**
   - Start lectures when ready
   - Monitor real-time attendance
   - Make manual corrections if needed
   - End lectures when complete

3. **View Reports**
   - Access "Attendance Reports" for analytics
   - Generate custom reports by date/course
   - Export data in multiple formats

### For Administrators

1. **User Management**
   - Add/edit users and assign roles
   - Monitor user activity and login history
   - Manage account status and permissions

2. **System Configuration**
   - Adjust geofencing settings
   - Configure attendance windows
   - Set up notification preferences
   - Monitor system health

## Security Features

- **Password Hashing**: Secure password storage with Werkzeug
- **CSRF Protection**: Cross-site request forgery prevention
- **Audit Logging**: Complete activity tracking
- **Location Verification**: GPS-based attendance validation
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive data validation

## Troubleshooting

### Common Issues

1. **Location Not Working**
   - Ensure HTTPS is used (required for geolocation)
   - Check browser location permissions
   - Verify GPS is enabled on mobile devices

2. **Database Errors**
   - Run `python init_db.py` to reset database
   - Check database file permissions
   - Verify SQLite installation

3. **Import Errors**
   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Development Tips

- Use `FLASK_DEBUG=True` for development
- Check browser console for JavaScript errors
- Monitor Flask logs for backend issues
- Use browser developer tools for location debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the code documentation
- Create an issue on the repository

## Roadmap

### Planned Features
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced analytics dashboard
- [ ] Integration with LMS systems
- [ ] Facial recognition for additional verification
- [ ] Offline attendance support
- [ ] Multi-language support
- [ ] Advanced reporting with charts
- [ ] Email/SMS notifications
- [ ] Calendar integration
- [ ] Bulk operations for administrators

### Technical Improvements
- [ ] Redis caching for better performance
- [ ] Celery for background tasks
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing suite
- [ ] Performance monitoring
- [ ] Load balancing support