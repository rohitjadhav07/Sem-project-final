# 🚀 Supabase Setup Guide for Geo Attendance Pro

This guide will help you set up Supabase as the database for your Geo Attendance Pro application.

## 📋 Prerequisites

1. A Supabase account (free at [supabase.com](https://supabase.com))
2. Your Vercel deployment ready

## 🔧 Step 1: Create Supabase Project

1. **Go to [supabase.com](https://supabase.com)** and sign in
2. **Click "New Project"**
3. **Choose your organization**
4. **Fill in project details:**
   - Name: `geo-attendance-pro`
   - Database Password: Generate a strong password (save this!)
   - Region: Choose closest to your users
5. **Click "Create new project"**
6. **Wait for setup to complete** (2-3 minutes)

## 🔑 Step 2: Get Your Credentials

Once your project is ready:

1. **Go to Settings → API**
2. **Copy these values:**
   - **Project URL**: `https://your-project.supabase.co`
   - **Anon (public) key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **Service role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

3. **Go to Settings → Database**
4. **Copy the Connection String:**
   - Look for "Connection string" → "URI"
   - Copy the PostgreSQL URI: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`
   - Replace `[password]` with your database password from Step 1

## ⚙️ Step 3: Configure Vercel Environment Variables

1. **Go to your Vercel project dashboard**
2. **Navigate to Settings → Environment Variables**
3. **Add these variables:**

```
SUPABASE_URL = https://your-project.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DATABASE_URL = postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
SECRET_KEY = your-secret-key-here
JWT_SECRET_KEY = your-jwt-secret-key-here
FLASK_CONFIG = production
```

4. **Click "Save"** for each variable

## 🚀 Step 4: Deploy and Test

1. **Redeploy your Vercel app** (it will automatically redeploy when you save environment variables)
2. **Visit your app URL**
3. **Check if it works:**
   - Login with: `admin` / `admin123`
   - Or: `teacher1` / `teacher123`
   - Or: `student1` / `student123`

## 📊 Step 5: Verify Database

1. **Go to your Supabase dashboard**
2. **Click "Table Editor"**
3. **You should see these tables:**
   - `users`
   - `courses`
   - `lectures`
   - `enrollments`
   - `attendances`
   - `audit_logs`

## 🎯 Benefits You'll Get

✅ **Persistent Data** - No more data resets!
✅ **Real-time Updates** - Live attendance tracking
✅ **Scalable** - Handles thousands of users
✅ **Backup & Recovery** - Automatic backups
✅ **Analytics** - Built-in database insights
✅ **Security** - Row-level security policies

## 🔍 Troubleshooting

### Issue: "Supabase not configured"
- **Solution**: Double-check all environment variables are set correctly in Vercel
- **Check**: Make sure there are no extra spaces in the values

### Issue: "Connection failed"
- **Solution**: Verify the database URL has the correct password
- **Check**: Ensure your Supabase project is active (not paused)

### Issue: "Tables not found"
- **Solution**: The app will create tables automatically on first run
- **Check**: Look at Vercel function logs for any errors

## 📞 Support

If you encounter issues:
1. Check Vercel function logs
2. Check Supabase logs in your dashboard
3. Verify all environment variables are correct

## 🎉 Success!

Once set up, your Geo Attendance Pro will have:
- **Permanent data storage**
- **Better performance**
- **Real-time capabilities**
- **Professional database features**

Your app is now production-ready! 🚀