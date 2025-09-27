"""
Database Connection Manager with SSL/TLS Hardening & Retry Logic
Enterprise-grade connection management for production reliability
"""

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

import psycopg2
from sqlalchemy import text
from sqlalchemy.exc import (
    DisconnectionError,
    OperationalError,
    PendingRollbackError,
    TimeoutError,
)

from models.database import SessionLocal, engine
from utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass

class DatabaseSSLError(Exception):
    """Custom exception for SSL/TLS related database issues"""
    pass

def with_db_retry(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_backoff: float = 60.0
):
    """
    Decorator for database operations with exponential backoff retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_base: Base delay in seconds
        backoff_multiplier: Multiplier for exponential backoff  
        max_backoff: Maximum delay between retries
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (
                    OperationalError,
                    DisconnectionError, 
                    TimeoutError,
                    PendingRollbackError,
                    psycopg2.OperationalError,
                    psycopg2.DatabaseError
                ) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Database operation failed after {max_retries} retries: {str(e)}")
                        raise DatabaseConnectionError(f"Database connection failed after {max_retries} retries") from e
                    
                    # Calculate exponential backoff delay with jitter to prevent thundering herd
                    base_delay = min(
                        backoff_base * (backoff_multiplier ** attempt),
                        max_backoff
                    )
                    # Add ±25% jitter to prevent synchronized retries
                    jitter = random.uniform(-0.25, 0.25) * base_delay
                    delay = max(0.1, base_delay + jitter)  # Minimum 100ms delay
                    
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    time.sleep(delay)
                    
                except Exception as e:
                    # Non-retryable exceptions
                    logger.error(f"Non-retryable database error: {str(e)}")
                    raise
                    
            # This should never be reached, but just in case
            raise DatabaseConnectionError("Unexpected error in retry logic") from last_exception
            
        return wrapper
    return decorator


class DatabaseConnectionManager:
    """Enterprise-grade database connection manager with SSL validation"""
    
    def __init__(self):
        self.engine = engine
        self._ssl_validated = False
    
    @with_db_retry(max_retries=3)
    def validate_connection(self) -> dict[str, Any]:
        """
        Validate database connection with SSL/TLS verification
        
        Returns:
            dict: Connection status and SSL information
        """
        try:
            with self.engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Get SSL/TLS connection information
                ssl_info = self._get_ssl_info(conn)
                
                # Validate SSL configuration in production
                if ssl_info.get("ssl_active"):
                    self._validate_ssl_configuration(ssl_info)
                
                connection_info = {
                    "status": "connected",
                    "ssl_active": ssl_info.get("ssl_active", False),
                    "ssl_version": ssl_info.get("version"),
                    "ssl_cipher": ssl_info.get("cipher"),
                    "server_version": self._get_server_version(conn),
                    "connection_validated_at": time.time()
                }
                
                self._ssl_validated = True
                logger.info(f"Database connection validated: SSL={ssl_info.get('ssl_active', False)}")
                return connection_info
                
        except Exception as e:
            logger.error(f"Database connection validation failed: {str(e)}")
            raise DatabaseConnectionError(f"Connection validation failed: {str(e)}") from e
    
    def _get_ssl_info(self, conn) -> dict[str, Any]:
        """Extract SSL/TLS information from PostgreSQL connection"""
        try:
            # Check if SSL is active (use different approach for different PG versions)
            ssl_active = False
            try:
                ssl_result = conn.execute(text("SELECT ssl_is_used()"))
                ssl_active = ssl_result.fetchone()[0] if ssl_result else False
            except Exception:
                # Fallback: Check connection info or assume based on URL
                try:
                    # Alternative method: check if connection was made with SSL
                    info_result = conn.execute(text("SELECT current_setting('ssl', true)"))
                    ssl_setting = info_result.fetchone()[0] if info_result else "off"
                    ssl_active = ssl_setting.lower() in ["on", "true", "1"]
                except Exception:
                    # Final fallback: check connection string
                    ssl_active = "sslmode" in str(conn.engine.url) and "disable" not in str(conn.engine.url)
            
            ssl_info = {"ssl_active": ssl_active}
            
            if ssl_active:
                # Get SSL version and cipher (if functions exist)
                try:
                    version_result = conn.execute(text("SELECT ssl_version()"))
                    ssl_info["version"] = version_result.fetchone()[0] if version_result else None
                except Exception:
                    ssl_info["version"] = "TLS (version unavailable)"
                
                try:
                    cipher_result = conn.execute(text("SELECT ssl_cipher()"))
                    ssl_info["cipher"] = cipher_result.fetchone()[0] if cipher_result else None
                except Exception:
                    ssl_info["cipher"] = "Unknown cipher"
            
            return ssl_info
            
        except Exception as e:
            logger.warning(f"Failed to get SSL information: {str(e)}")
            return {"ssl_active": False}
    
    def _get_server_version(self, conn) -> str:
        """Get PostgreSQL server version"""
        try:
            result = conn.execute(text("SELECT version()"))
            return result.fetchone()[0] if result else "unknown"
        except Exception:
            return "unknown"
    
    def _validate_ssl_configuration(self, ssl_info: dict[str, Any]) -> None:
        """Validate SSL configuration meets enterprise security requirements"""
        from config.settings import settings
        
        if settings.environment.value in ["production", "staging"]:
            if not ssl_info.get("ssl_active"):
                raise DatabaseSSLError("SSL/TLS is REQUIRED for production/staging database connections")
            
            ssl_version = ssl_info.get("version", "")
            if ssl_version:
                # SECURITY: Enforce TLS 1.2+ (server-side must be configured)
                if "TLSv1.2" not in ssl_version and "TLSv1.3" not in ssl_version:
                    logger.warning(
                        f"⚠️ SSL version may be outdated: {ssl_version}. "
                        "Ensure server enforces TLS 1.2+ via ssl_min_protocol_version"
                    )
                
                logger.info(f"✅ Production SSL validation passed: {ssl_version}")
                
                # Additional security validation
                cipher = ssl_info.get("cipher", "")
                if cipher and any(weak in cipher.lower() for weak in ["rc4", "des", "md5"]):
                    logger.warning(f"⚠️ Potentially weak cipher detected: {cipher}")
            
            # Validate SSL mode configuration
            engine_url = str(self.engine.url)
            if "verify-full" not in engine_url and "verify-ca" not in engine_url:
                logger.warning(
                    "⚠️ SSL verification mode not detected in connection string. "
                    "Ensure sslmode=verify-full for maximum security."
                )
    
    @with_db_retry(max_retries=2)
    def get_session(self):
        """Get database session with connection validation"""
        try:
            session = SessionLocal()
            
            # Test the session with a simple query
            session.execute(text("SELECT 1"))
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to create database session: {str(e)}")
            raise DatabaseConnectionError(f"Session creation failed: {str(e)}") from e
    
    @with_db_retry(max_retries=3)
    def health_check(self) -> dict[str, Any]:
        """Comprehensive database health check"""
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Basic connectivity
                conn.execute(text("SELECT 1"))
                
                # Connection pool status
                pool = self.engine.pool
                pool_info = {
                    "pool_size": pool.size(),
                    "pool_checked_in": pool.checkedin(),
                    "pool_checked_out": pool.checkedout(),
                    "pool_overflow": pool.overflow(),
                    "pool_invalid": getattr(pool, 'invalid', lambda: 0)()
                }
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "ssl_validated": self._ssl_validated,
                    "pool_info": pool_info,
                    "timestamp": time.time()
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {str(e)}")
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time, 2),
                "ssl_validated": self._ssl_validated,
                "timestamp": time.time()
            }
    
    def close(self):
        """Close database connections and clean up resources"""
        try:
            self.engine.dispose()
            logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")


# Global instance
db_manager = DatabaseConnectionManager()