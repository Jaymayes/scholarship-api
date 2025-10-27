"""
Database Connection Pool Warm-up Utility
Eliminates cold-start latency by pre-establishing connections
"""
import asyncio
from typing import Optional

from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger(__name__)


async def warmup_connection_pool(db_session_factory, pool_size: int = 5) -> bool:
    """
    Warm up the database connection pool by pre-establishing connections
    
    Args:
        db_session_factory: Database session factory (dependency)
        pool_size: Number of connections to establish (default: 5)
        
    Returns:
        bool: True if warmup successful, False otherwise
    """
    logger.info(f"🔥 Warming up database connection pool ({pool_size} connections)...")
    
    try:
        connections_established = 0
        
        # Establish connections by executing simple queries
        for i in range(pool_size):
            try:
                db = next(db_session_factory())
                
                # Execute lightweight query to establish connection
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                
                # Connection established successfully
                connections_established += 1
                logger.debug(f"  Connection {i+1}/{pool_size} established")
                
                # Close the session (returns connection to pool)
                db.close()
                
                # Small delay to avoid overwhelming database
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.warning(f"  Failed to establish connection {i+1}: {e}")
                continue
        
        success_rate = (connections_established / pool_size) * 100
        
        if connections_established >= pool_size * 0.8:  # 80% threshold
            logger.info(f"✅ Connection pool warmed up: {connections_established}/{pool_size} connections ({success_rate:.0f}%)")
            return True
        else:
            logger.warning(f"⚠️ Partial warmup: {connections_established}/{pool_size} connections ({success_rate:.0f}%)")
            return False
            
    except Exception as e:
        logger.error(f"🔴 Connection pool warmup failed: {e}")
        return False


def warmup_connection_pool_sync(db_session_factory, pool_size: int = 5) -> bool:
    """
    Synchronous version of connection pool warm-up
    
    Args:
        db_session_factory: Database session factory (dependency)
        pool_size: Number of connections to establish (default: 5)
        
    Returns:
        bool: True if warmup successful, False otherwise
    """
    logger.info(f"🔥 Warming up database connection pool ({pool_size} connections)...")
    
    try:
        connections_established = 0
        
        # Establish connections by executing simple queries
        for i in range(pool_size):
            try:
                db = next(db_session_factory())
                
                # Execute lightweight query to establish connection
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                
                # Connection established successfully
                connections_established += 1
                logger.debug(f"  Connection {i+1}/{pool_size} established")
                
                # Close the session (returns connection to pool)
                db.close()
                
            except Exception as e:
                logger.warning(f"  Failed to establish connection {i+1}: {e}")
                continue
        
        success_rate = (connections_established / pool_size) * 100
        
        if connections_established >= pool_size * 0.8:  # 80% threshold
            logger.info(f"✅ Connection pool warmed up: {connections_established}/{pool_size} connections ({success_rate:.0f}%)")
            return True
        else:
            logger.warning(f"⚠️ Partial warmup: {connections_established}/{pool_size} connections ({success_rate:.0f}%)")
            return False
            
    except Exception as e:
        logger.error(f"🔴 Connection pool warmup failed: {e}")
        return False
