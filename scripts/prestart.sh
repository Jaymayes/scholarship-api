#!/bin/bash
# Pre-startup script: database and dependency checks

set -e

echo "🚀 Starting pre-deployment checks..."

# Wait for database to be ready
echo "📊 Checking database connectivity..."
python -c "
import sys
import time
import os
from sqlalchemy import create_engine, text
from config.settings import settings

max_tries = 30
for i in range(max_tries):
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print(f'✅ Database connected successfully')
        break
    except Exception as e:
        if i == max_tries - 1:
            print(f'❌ Database connection failed after {max_tries} attempts: {e}')
            sys.exit(1)
        print(f'⏳ Database not ready, retrying... ({i+1}/{max_tries})')
        time.sleep(2)
"

# Wait for Redis (if configured for production)
if [ "$RATE_LIMIT_BACKEND_URL" != "" ] && [ "$ENVIRONMENT" = "production" ]; then
    echo "🔄 Checking Redis connectivity..."
    python -c "
import sys
import time
import redis
import os

redis_url = os.getenv('RATE_LIMIT_BACKEND_URL')
if redis_url:
    max_tries = 30
    for i in range(max_tries):
        try:
            r = redis.from_url(redis_url)
            r.ping()
            print(f'✅ Redis connected successfully')
            break
        except Exception as e:
            if i == max_tries - 1:
                print(f'❌ Redis connection failed after {max_tries} attempts: {e}')
                sys.exit(1)
            print(f'⏳ Redis not ready, retrying... ({i+1}/{max_tries})')
            time.sleep(2)
"
fi

# Run database migrations
echo "🔧 Running database migrations..."
python -c "
import sys
from alembic.config import Config
from alembic import command
import os

try:
    # Check if alembic.ini exists, if not create minimal config
    if not os.path.exists('alembic.ini'):
        print('⚠️  No alembic.ini found, skipping migrations')
    else:
        alembic_cfg = Config('alembic.ini')
        command.upgrade(alembic_cfg, 'head')
        print('✅ Database migrations completed')
except Exception as e:
    print(f'⚠️  Migration warning: {e}')
    # Don't fail startup for migration issues in development
    if os.getenv('ENVIRONMENT') == 'production':
        sys.exit(1)
"

# Quick smoke test
echo "🔍 Running application smoke test..."
python -c "
import sys
from main import app
from config.settings import settings

try:
    # Basic application initialization test
    print(f'✅ Application initialized successfully')
    print(f'📋 Environment: {settings.environment.value}')
    print(f'🔒 Security mode: {\"production\" if not settings.is_development else \"development\"}')
    print(f'🗄️  Database: {settings.get_database_info}')
except Exception as e:
    print(f'❌ Application smoke test failed: {e}')
    sys.exit(1)
"

echo "✅ Pre-deployment checks completed successfully!"