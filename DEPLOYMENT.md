# 🚀 Geo Attendance Pro - Deployment Guide

This guide covers multiple deployment options for the Geo Attendance Pro application.

## 📋 Prerequisites

- Python 3.11+
- Git
- Database (SQLite for development, PostgreSQL/MySQL for production)

## 🔧 Environment Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd geo_attendance_pro
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🌐 Deployment Options

### Option 1: Heroku Deployment (Recommended for beginners)

1. **Install Heroku CLI**
   - Download from: https://devcenter.heroku.com/articles/heroku-cli

2. **Deploy using script**
   ```bash
   ./deploy.sh heroku
   ```

3. **Manual Heroku deployment**
   ```bash
   # Login to Heroku
   heroku login
   
   # Create app
   heroku create your-app-name
   
   # Set environment variables
   heroku config:set FLASK_CONFIG=heroku
   heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   
   # Add PostgreSQL
   heroku addons:create heroku-postgresql:mini
   
   # Deploy
   git push heroku main
   
   # Initialize database
   heroku run python init_db.py
   ```

4. **Access your app**
   ```
   https://your-app-name.herokuapp.com
   ```

### Option 2: Docker Deployment (Recommended for production)

1. **Install Docker and Docker Compose**
   - Docker: https://docs.docker.com/get-docker/
   - Docker Compose: https://docs.docker.com/compose/install/

2. **Deploy using script**
   ```bash
   ./deploy.sh docker
   ```

3. **Manual Docker deployment**
   ```bash
   # Build and run
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   ```

4. **Access your app**
   ```
   http://localhost (with Nginx)
   http://localhost:5000 (direct access)
   ```

### Option 3: VPS/Server Deployment

1. **Prepare server**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3 python3-pip python3-venv nginx postgresql -y
   ```

2. **Deploy using script**
   ```bash
   ./deploy.sh vps
   ```

3. **Manual VPS deployment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export FLASK_CONFIG=production
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   
   # Initialize database
   python init_db.py
   
   # Run with Gunicorn
   gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
   ```

### Option 4: Railway Deployment

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy to Railway**
   ```bash
   railway login
   railway init
   railway up
   ```

### Option 5: DigitalOcean App Platform

1. **Create app.yaml**
   ```yaml
   name: geo-attendance-pro
   services:
   - name: web
     source_dir: /
     github:
       repo: your-username/geo-attendance-pro
       branch: main
     run_command: gunicorn --worker-tmp-dir /dev/shm --config gunicorn.conf.py wsgi:app
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: FLASK_CONFIG
       value: production
   databases:
   - name: geo-attendance-db
     engine: PG
     version: "13"
   ```

## 🔒 Security Configuration

### SSL/HTTPS Setup

1. **For Nginx (VPS deployment)**
   ```bash
   # Install Certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d yourdomain.com
   ```

2. **For Heroku**
   - SSL is automatically provided for *.herokuapp.com domains
   - For custom domains: Add SSL certificate in Heroku dashboard

### Environment Variables

**Required for production:**
```bash
FLASK_CONFIG=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=your-database-url
```

**Optional but recommended:**
```bash
JWT_SECRET_KEY=your-jwt-secret
MAIL_SERVER=your-mail-server
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

## 📊 Monitoring and Maintenance

### Health Checks

The application includes a health check endpoint:
```
GET /health
```

### Logging

- **Development**: Logs to console
- **Production**: Logs to files in `/logs` directory
- **Docker**: Logs to stdout (viewable with `docker-compose logs`)

### Database Backups

1. **PostgreSQL backup**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Restore from backup**
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

### Updates and Maintenance

1. **Update application**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   # Restart application
   ```

2. **Database migrations**
   ```bash
   python migrate_enhanced_location.py
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL environment variable
   - Ensure database server is running
   - Verify credentials

2. **Location services not working**
   - Ensure HTTPS is enabled (required for geolocation)
   - Check browser permissions
   - Verify GPS accuracy settings

3. **Static files not loading**
   - Check Nginx configuration
   - Verify static file paths
   - Ensure proper permissions

### Debug Mode

**Never enable debug mode in production!**

For development debugging:
```bash
export FLASK_CONFIG=development
python app.py
```

## 📞 Support

For deployment issues:
1. Check the logs first
2. Verify environment variables
3. Test database connectivity
4. Check firewall settings
5. Verify SSL certificate status

## 🎯 Performance Optimization

### Production Recommendations

1. **Use a production WSGI server** (Gunicorn, uWSGI)
2. **Enable caching** (Redis, Memcached)
3. **Use a reverse proxy** (Nginx, Apache)
4. **Enable compression** (gzip)
5. **Optimize database** (indexes, connection pooling)
6. **Monitor performance** (New Relic, DataDog)

### Scaling

- **Horizontal scaling**: Multiple app instances behind load balancer
- **Database scaling**: Read replicas, connection pooling
- **CDN**: For static assets
- **Caching**: Redis for session storage and caching

## 🔄 CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-app-name"
        heroku_email: "your-email@example.com"
```

---

**🎉 Your Geo Attendance Pro application is now ready for deployment!**

Choose the deployment option that best fits your needs and infrastructure requirements.