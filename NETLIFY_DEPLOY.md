# 🌐 Netlify Deployment Guide

## Prerequisites
- Netlify account
- Git repository

## Step 1: Install Netlify CLI
```bash
npm install -g netlify-cli
```

## Step 2: Login to Netlify
```bash
netlify login
```

## Step 3: Initialize and Deploy
```bash
# In your project directory
netlify init

# Follow the prompts:
# - Create & configure a new site? Y
# - Team: (select your team)
# - Site name: geo-attendance-pro (or your preferred name)
# - Build command: pip install -r requirements.txt && python netlify_init.py
# - Directory to deploy: static
# - Functions directory: netlify/functions
```

## Step 4: Set Environment Variables
```bash
netlify env:set SECRET_KEY "your-secret-key-here"
netlify env:set JWT_SECRET_KEY "your-jwt-secret-here"
netlify env:set FLASK_CONFIG "production"
netlify env:set DATABASE_URL "sqlite:///geo_attendance_netlify.db"
```

## Step 5: Deploy
```bash
netlify deploy --prod
```

## ✅ Your app will be live at the provided Netlify URL!

## 🔧 Troubleshooting
- Check build logs in Netlify dashboard
- Check function logs: `netlify functions:log`
- Redeploy: `netlify deploy --prod`

## ⚠️ Important Notes
- Netlify Functions have execution time limits
- Database will reset on each deployment (use external DB for production)
- Consider using Netlify's database add-ons for persistence

## 📱 Test Your App
Login with:
- Admin: admin / admin123
- Teacher: teacher1 / teacher123
- Student: student1 / student123