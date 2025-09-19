#!/bin/bash

# Geo Attendance Pro Deployment Script
# Usage: ./deploy.sh [heroku|docker|vps]

set -e

DEPLOYMENT_TYPE=${1:-docker}

echo "🚀 Starting deployment for: $DEPLOYMENT_TYPE"

# Check if required files exist
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "❌ app.py not found!"
    exit 1
fi

case $DEPLOYMENT_TYPE in
    "heroku")
        echo "📦 Deploying to Heroku..."
        
        # Check if Heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not found. Please install it first."
            exit 1
        fi
        
        # Login to Heroku (if not already logged in)
        heroku auth:whoami || heroku login
        
        # Create Heroku app (if it doesn't exist)
        read -p "Enter your Heroku app name: " APP_NAME
        heroku create $APP_NAME || echo "App might already exist"
        
        # Set environment variables
        heroku config:set FLASK_CONFIG=heroku --app $APP_NAME
        heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') --app $APP_NAME
        
        # Add PostgreSQL addon
        heroku addons:create heroku-postgresql:mini --app $APP_NAME || echo "PostgreSQL addon might already exist"
        
        # Deploy
        git add .
        git commit -m "Deploy to Heroku" || echo "No changes to commit"
        git push heroku main || git push heroku master
        
        # Run database initialization
        heroku run python init_db.py --app $APP_NAME
        
        echo "✅ Deployed to Heroku: https://$APP_NAME.herokuapp.com"
        ;;
        
    "docker")
        echo "🐳 Deploying with Docker..."
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker not found. Please install Docker first."
            exit 1
        fi
        
        # Build and run with Docker Compose
        docker-compose down
        docker-compose build
        docker-compose up -d
        
        # Wait for services to start
        echo "⏳ Waiting for services to start..."
        sleep 30
        
        # Check if services are running
        docker-compose ps
        
        echo "✅ Deployed with Docker. Access at: http://localhost"
        echo "📊 View logs: docker-compose logs -f"
        ;;
        
    "vps")
        echo "🖥️  Deploying to VPS..."
        
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
        
        # Create systemd service file
        sudo tee /etc/systemd/system/geo-attendance.service > /dev/null <<EOF
[Unit]
Description=Geo Attendance Pro
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
Environment=FLASK_CONFIG=production
Environment=SECRET_KEY=$SECRET_KEY
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        # Enable and start service
        sudo systemctl daemon-reload
        sudo systemctl enable geo-attendance
        sudo systemctl start geo-attendance
        
        echo "✅ Deployed to VPS. Service status:"
        sudo systemctl status geo-attendance
        ;;
        
    *)
        echo "❌ Unknown deployment type: $DEPLOYMENT_TYPE"
        echo "Usage: ./deploy.sh [heroku|docker|vps]"
        exit 1
        ;;
esac

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test the application thoroughly"
echo "2. Set up SSL certificates for production"
echo "3. Configure backup strategies"
echo "4. Set up monitoring and logging"
echo "5. Configure domain name (if applicable)"