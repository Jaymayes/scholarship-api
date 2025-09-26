#!/usr/bin/env python3
"""
Production-ready startup script for deployment environments
Addresses all deployment health check requirements
"""

import logging
import os
import sys


def setup_production_environment():
    """Configure environment variables for production deployment"""
    production_env = {
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "RELOAD": "false",
        "HOST": "0.0.0.0",
        "PORT": "5000",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "json"
    }

    for key, value in production_env.items():
        if key not in os.environ:
            os.environ[key] = value

def main():
    """Main entry point with optimized production configuration"""

    # Setup production environment
    setup_production_environment()

    # Configure logging for production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Scholarship Discovery API (Production Mode)")

    try:
        # Import main application
        import uvicorn

        from config.settings import settings
        from main import app

        logger.info(f"📡 Binding to {settings.host}:{settings.port}")
        logger.info(f"🏥 Health checks: http://{settings.host}:{settings.port}/ and /health")

        # Start server with production-optimized settings
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info",
            access_log=True,
            workers=1,
            proxy_headers=True,
            forwarded_allow_ips="*",
            timeout_keep_alive=5,
            limit_concurrency=1000,
            limit_max_requests=10000,
            use_colors=False
        )

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
