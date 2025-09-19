# 🚀 Vercel Deployment Guide

## Prerequisites
- Node.js installed
- Git repository

## Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

## Step 2: Login to Vercel
```bash
vercel login
```

## Step 3: Deploy
```bash
# In your project directory
vercel

# Follow the prompts:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - What's your project's name? geo-attendance-pro
# - In which directory is your code located? ./
```

## Step 4: Set Environment Variables
```bash
vercel env add SECRET_KEY
# Enter a secure secret key when prompted

vercel env add JWT_SECRET_KEY  
# Enter a JWT secret key when prompted

vercel env add FLASK_CONFIG
# Enter: production

vercel env add DATABASE_URL
# For SQLite: sqlite:///geo_attendance_vercel.db
# For PostgreSQL: your-postgres-connection-string
```

## Step 5: Deploy Again (to apply env vars)
```bash
vercel --prod
```

## ✅ Your app will be live at the provided Vercel URL!

## 🔧 Troubleshooting
- Check logs: `vercel logs`
- Redeploy: `vercel --prod`
- Check functions: Visit Vercel dashboard

## 📱 Test Your App
Login with:
- Admin: admin / admin123
- Teacher: teacher1 / teacher123
- Student: student1 / student123