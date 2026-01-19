"""
Simple database session manager for health checks
SEV-2 hardened: pooling, timeouts, keepalive per CIR-20260119-001
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from config.settings import settings

_engine = None

def get_engine():
    """Get or create the database engine with SEV-2 hardened pooling"""
    global _engine
    if _engine is None and settings.database_url:
        _engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=3,
            connect_args={
                "options": "-c statement_timeout=5000",
                "connect_timeout": 3
            }
        )
    return _engine

def get_pool_status():
    """Get pool status for health endpoint"""
    engine = get_engine()
    if engine is None:
        return {"db_connected": False, "pool_in_use": 0, "pool_idle": 0, "pool_size": 0}
    
    try:
        pool = engine.pool
        return {
            "db_connected": True,
            "pool_in_use": getattr(pool, 'checkedout', lambda: 0)(),
            "pool_idle": getattr(pool, 'checkedin', lambda: 0)(),
            "pool_size": getattr(pool, 'size', lambda: 0)()
        }
    except Exception:
        return {"db_connected": True, "pool_in_use": 0, "pool_idle": 0, "pool_size": 0}

def get_session():
    """Get a database session for health checks"""
    engine = get_engine()
    if engine is None:
        raise Exception("No database URL configured")

    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
