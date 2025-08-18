"""
Simple database session manager for health checks
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings

def get_session():
    """Get a database session for health checks"""
    if not settings.database_url:
        raise Exception("No database URL configured")
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()