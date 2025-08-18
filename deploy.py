#!/usr/bin/env python3
"""
Production Deployment Script
Optimized configuration for deployment environments
"""

import os
import uvicorn
from config.settings import settings, Environment

def main():
    """Run the application with production-optimized settings"""
    
    # Override settings for deployment
    deployment_settings = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 5000)),
        "reload": False,
        "workers": 1,  # Single worker for deployment simplicity
        "access_log": True,
        "log_level": "info",
    }
    
    print(f"🚀 Starting Scholarship Discovery API in {settings.environment.value} mode")
    print(f"📡 Server binding to {deployment_settings['host']}:{deployment_settings['port']}")
    
    uvicorn.run(
        "main:app",
        **deployment_settings
    )

if __name__ == "__main__":
    main()