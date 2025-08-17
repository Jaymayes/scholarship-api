#!/usr/bin/env python3
"""
Database Migration Script
Creates tables and migrates mock data to PostgreSQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models.database import engine, SessionLocal, create_tables, drop_tables
from services.database_service import DatabaseService
from utils.logger import get_logger

logger = get_logger("migration")

def run_migration():
    """Run database migration"""
    try:
        logger.info("Starting database migration...")
        
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Migrate mock data
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            count = db_service.migrate_mock_data()
            logger.info(f"✅ Migrated {count} scholarships to database")
        finally:
            db.close()
        
        logger.info("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False

def reset_database():
    """Reset database (drop and recreate)"""
    try:
        logger.warning("Resetting database - dropping all tables...")
        drop_tables()
        logger.info("All tables dropped")
        
        return run_migration()
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop and recreate)")
    
    args = parser.parse_args()
    
    if args.reset:
        success = reset_database()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)