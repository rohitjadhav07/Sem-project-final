# 🚀 Heroku Deployment Commands

Run these commands in your terminal (in the geo_attendance_pro directory):

## 1. Login to Heroku
```bash
heroku login
```

## 2. Create Heroku App
```bash
heroku create your-app-name-here
```
*Replace "your-app-name-here" with your desired app name (must be unique)*

## 3. Set Environment Variables
```bash
heroku config:set FLASK_CONFIG=heroku
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set MIN_GPS_ACCURACY=15
heroku config:set DEFAULT_GEOFENCE_RADIUS=50
heroku config:set LOCATION_CONFIRMATIONS_REQUIRED=3
```

## 4. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:mini
```

## 5. Deploy to Heroku
```bash
git push heroku master
```
*If you're on main branch, use: `git push heroku main`*

## 6. Open Your App
```bash
heroku open
```

## 7. View Logs (if needed)
```bash
heroku logs --tail
```

## 8. Test Your App
Visit your app URL and login with:
- **Admin:** admin / admin123
- **Teacher:** teacher1 / teacher123  
- **Student:** student1 / student123

---

## 🔧 Troubleshooting Commands

If you encounter issues:

```bash
# Check app status
heroku ps

# Restart app
heroku restart

# Check config vars
heroku config

# Run database initialization manually (if needed)
heroku run python heroku_init.py

# Check database
heroku pg:info
```

---

## 🎉 Success!
Your Geo Attendance Pro will be live at: https://your-app-name.herokuapp.com