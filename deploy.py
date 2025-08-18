#!/usr/bin/env python3
"""
Production deployment script for Scholarship Discovery API
Addresses deployment health check requirements and proper configuration
"""

import os
import sys
import uvicorn
from config.settings import settings, Environment

def main():
    """Main deployment entry point with production-ready configuration"""
    
    # Force production settings for deployment
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("RELOAD", "false")
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "5000")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Import app after environment variables are set
    from main import app
    
    print(f"🚀 Starting Scholarship Discovery API in {settings.environment.value} mode")
    print(f"📡 Server will bind to {settings.host}:{settings.port}")
    print(f"📊 Health checks available at: http://{settings.host}:{settings.port}/")
    print(f"📚 API documentation: http://{settings.host}:{settings.port}/docs")
    
    # Production-optimized uvicorn configuration
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,  # Never reload in production
        log_level=settings.log_level.lower(),
        access_log=True,
        workers=1,  # Single worker for deployment
        proxy_headers=True,  # For reverse proxy compatibility
        forwarded_allow_ips="*",  # Allow forwarded headers
        timeout_keep_alive=5,  # Quick timeout for health checks
        limit_concurrency=1000,  # Reasonable concurrency limit
        limit_max_requests=10000,  # Request limit before worker restart
        use_colors=False  # No colors in production logs
    )

if __name__ == "__main__":
    main()