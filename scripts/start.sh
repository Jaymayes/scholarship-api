#!/bin/bash
# Production startup script with graceful handling

set -e

echo "🚀 Starting Scholarship Discovery API..."

# Run pre-startup checks
./prestart.sh

# Determine if we should use Gunicorn (production) or Uvicorn (development)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting in PRODUCTION mode with Gunicorn..."
    exec gunicorn main:app -c gunicorn_conf.py
else
    echo "🔧 Starting in DEVELOPMENT mode with Uvicorn..."
    exec uvicorn main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --reload \
        --access-log \
        --forwarded-allow-ips="*"
fi