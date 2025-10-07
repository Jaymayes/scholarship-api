"""
Database Configuration - P0-4 Executive Authorization
Centralized database engine configuration with connection pooling, SSL/TLS, and failover support
"""

# Import engine from models/database where it's configured with all production settings
from models.database import engine, SessionLocal, Base, DATABASE_URL

# Re-export for health checks and other services
__all__ = ['engine', 'SessionLocal', 'Base', 'DATABASE_URL']

# Database configuration is in models/database.py with:
# - Connection pooling (pool_size, max_overflow)
# - SSL/TLS hardening (verify-full in production)
# - Pool pre-ping and recycle for connection health
# - Timeout and retry settings
# - Application name for monitoring
