#!/usr/bin/env python3
"""
Migration to add interactions table for analytics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models.database import engine, SessionLocal
from models.interaction import InteractionDB
from utils.logger import get_logger

logger = get_logger("migration_interactions")

def create_interactions_table():
    """Create interactions table if it doesn't exist"""
    try:
        # Import and create the table
        from models.database import Base
        InteractionDB.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("✅ Interactions table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create interactions table: {str(e)}")
        return False

def verify_interactions_table():
    """Verify interactions table exists and has correct structure"""
    try:
        db = SessionLocal()
        
        # Test table exists by running a simple query
        result = db.execute(text("SELECT COUNT(*) FROM interactions"))
        count = result.scalar()
        
        logger.info(f"✅ Interactions table verified - contains {count} records")
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to verify interactions table: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_interactions_table()
    if success:
        success = verify_interactions_table()
    
    sys.exit(0 if success else 1)