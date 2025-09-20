# 🚀 Complete Supabase Setup for Geo Attendance Pro

This guide will walk you through setting up Supabase as your database backend.

## 📋 Step 1: Create Supabase Project

1. **Go to [supabase.com](https://supabase.com)** and sign up/login
2. **Click "New Project"**
3. **Fill in details:**
   - **Organization**: Choose or create one
   - **Name**: `geo-attendance-pro`
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your users (e.g., Asia Pacific for India)
4. **Click "Create new project"**
5. **Wait 2-3 minutes** for project creation

## 🔑 Step 2: Get Your Credentials

### From Supabase Dashboard:

#### A. Get API Credentials
1. **Go to Settings → API**
2. **Copy these values:**
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (long string)
   - **service_role secret key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (different long string)

#### B. Get Database URL
1. **Go to Settings → Database**
2. **Scroll to "Connection info"**
3. **Click "Connection string" → "URI"**
4. **Copy the PostgreSQL URL**: `postgresql://postgres.your-ref:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres`
5. **Replace `PASSWORD` with your actual database password from Step 1**

## ⚙️ Step 3: Configure Vercel Environment Variables

1. **Go to [vercel.com](https://vercel.com)** → Your project → Settings → Environment Variables
2. **Add these 6 variables:**

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdXItcHJvamVjdC1yZWYiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY5OTk5OTk5OSwiZXhwIjoyMDE1NTc1OTk5fQ.your-signature
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdXItcHJvamVjdC1yZWYiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjk5OTk5OTk5LCJleHAiOjIwMTU1NzU5OTl9.your-signature
SUPABASE_DATABASE_URL=postgresql://postgres.your-project-ref:your-actual-password@aws-0-region.pooler.supabase.com:6543/postgres
SECRET_KEY=your-super-secret-key-for-flask-sessions
JWT_SECRET_KEY=your-jwt-secret-key-for-authentication
```

3. **Click "Save" for each variable**

## 🗄️ Step 4: Set Up Database Tables

### Option A: Automatic Setup (Recommended)
Your app will automatically create tables when it starts. Just redeploy after setting environment variables.

### Option B: Manual Setup (If needed)
1. **Go to Supabase Dashboard → SQL Editor**
2. **Run this SQL:**

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'teacher', 'student')) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    phone VARCHAR(20),
    student_id VARCHAR(20) UNIQUE,
    employee_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Courses table
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    teacher_id INTEGER REFERENCES users(id),
    location_name VARCHAR(200),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    geofence_radius INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lectures table
CREATE TABLE lectures (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) NOT NULL,
    teacher_id INTEGER REFERENCES users(id) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    location_name VARCHAR(200),
    geofence_radius INTEGER DEFAULT 50,
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')) DEFAULT 'scheduled',
    is_active BOOLEAN DEFAULT TRUE,
    attendance_window_start INTEGER DEFAULT -15,
    attendance_window_end INTEGER DEFAULT 15,
    location_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enrollments table
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) NOT NULL,
    course_id INTEGER REFERENCES courses(id) NOT NULL,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, course_id)
);

-- Attendances table
CREATE TABLE attendances (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) NOT NULL,
    lecture_id INTEGER REFERENCES lectures(id) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('present', 'absent', 'late', 'excused')) DEFAULT 'absent',
    student_latitude DECIMAL(10,8),
    student_longitude DECIMAL(11,8),
    distance_from_lecture DECIMAL,
    marked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, lecture_id)
);
```

## 🚀 Step 5: Deploy and Test

1. **Redeploy your Vercel app** (happens automatically when you save environment variables)
2. **Wait for deployment** (2-3 minutes)
3. **Visit your app**: https://sem-project-final.vercel.app
4. **Test login with:**
   - Admin: `admin` / `admin123`
   - Teacher: `teacher1` / `teacher123`
   - Student: `student1` / `student123`

## ✅ Step 6: Verify Setup

### Check Database Tables:
1. **Go to Supabase Dashboard → Table Editor**
2. **You should see these tables:**
   - `users` (with sample users)
   - `courses` (with sample courses)
   - `lectures` (with active lectures)
   - `enrollments` (student enrollments)
   - `attendances` (attendance records)

### Test Features:
1. **Login as student** → Should see active lectures
2. **Try GPS check-in** → Should work with location verification
3. **Login as teacher** → Should see lecture management
4. **Login as admin** → Should see system overview

## 🎯 Benefits You'll Get

✅ **Persistent Data** - No more resets every 10 minutes!
✅ **Real-time Updates** - Live attendance tracking
✅ **Scalable Database** - Handles thousands of users
✅ **Automatic Backups** - Your data is safe
✅ **Better Performance** - PostgreSQL is much faster than SQLite
✅ **Professional Features** - Row-level security, triggers, functions

## 🔍 Troubleshooting

### "Internal Server Error"
- **Check**: All environment variables are set correctly
- **Verify**: Database password in SUPABASE_DATABASE_URL is correct
- **Test**: Visit `/test/supabase` to check connection

### "Connection Failed"
- **Check**: Supabase project is active (not paused)
- **Verify**: All credentials are copied correctly (no extra spaces)
- **Test**: Try regenerating API keys if needed

### "Tables Not Found"
- **Solution**: App will create tables automatically on first run
- **Manual**: Use the SQL commands in Step 4 if needed

## 📞 Support

If you need help:
1. **Check Vercel function logs** for detailed errors
2. **Check Supabase logs** in your dashboard
3. **Test connection** at `/test/supabase`
4. **Verify credentials** are exactly as shown in Supabase dashboard

## 🎉 Success!

Once everything is set up, your Geo Attendance Pro will have:
- **Permanent data storage** that never resets
- **Professional PostgreSQL database**
- **Real-time capabilities**
- **Scalable architecture**
- **Production-ready performance**

Your app is now enterprise-ready! 🚀