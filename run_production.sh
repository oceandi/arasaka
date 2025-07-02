#!/bin/bash

# Production deployment script for maintenancesp.com

echo "🚀 Starting Maintenance Solution Partner Application..."

# Load environment variables
export FLASK_ENV=production
export FLASK_APP=app.py

# SSL Certificate paths (adjust for your system)
export SSL_CERT_PATH="/etc/letsencrypt/live/maintencesp.com/fullchain.pem"
export SSL_KEY_PATH="/etc/letsencrypt/live/maintencesp.com/privkey.pem"

# Server configuration
export PORT=443
export HOST=0.0.0.0

# Security (CHANGE THIS SECRET KEY!)
export SECRET_KEY="MSP-Karel-Production-Secret-Key-2024-Change-This"

echo "📋 Configuration:"
echo "   Domain: maintencesp.com"
echo "   Port: $PORT (HTTPS)"
echo "   SSL: Enabled"
echo "   Environment: $FLASK_ENV"

# Check SSL certificates
if [ ! -f "$SSL_CERT_PATH" ]; then
    echo "❌ SSL Certificate not found at: $SSL_CERT_PATH"
    echo "💡 Run: sudo certbot certonly --standalone -d maintencesp.com"
    exit 1
fi

if [ ! -f "$SSL_KEY_PATH" ]; then
    echo "❌ SSL Private Key not found at: $SSL_KEY_PATH"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install production dependencies
pip install gunicorn

# Run database migrations
flask db upgrade

# Start the application with Gunicorn (recommended for production)
echo "🔥 Starting with Gunicorn (Production WSGI Server)..."
gunicorn --bind 0.0.0.0:443 \
         --workers 4 \
         --worker-class sync \
         --timeout 30 \
         --keep-alive 2 \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --certfile=$SSL_CERT_PATH \
         --keyfile=$SSL_KEY_PATH \
         --ssl-version TLSv1_2 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         --log-level info \
         app:app

echo "✅ Maintenance Solution Partner is running at https://maintencesp.com"