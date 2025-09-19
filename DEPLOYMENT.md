# Deployment Guide

## Vercel Deployment

### Required Environment Variables in Vercel:

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add these variables:

```
SECRET_KEY = generate-a-secure-random-key-here
JWT_SECRET_KEY = generate-another-secure-random-key-here  
FLASK_CONFIG = production
```

### Generate Secure Keys:

You can generate secure keys using Python:

```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(32))
```

### Database:

- The app uses SQLite in production (perfect for Vercel)
- Database tables are created automatically on first run
- No external database setup required

### After Setting Environment Variables:

1. Redeploy your Vercel app (it will redeploy automatically)
2. Your app should now work at: `https://your-app-name.vercel.app`

## Features Available:

- ✅ User Authentication (Admin, Teacher, Student roles)
- ✅ Course Management
- ✅ Lecture Scheduling
- ✅ GPS-based Attendance Tracking
- ✅ Real-time Location Verification
- ✅ Attendance Reports and Analytics