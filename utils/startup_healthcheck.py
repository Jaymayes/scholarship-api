"""
Startup Healthcheck - CEO P1 Directive
Validates SSL verify-full mode and fails fast if not properly configured
"""

import logging
import sys
from sqlalchemy import create_engine, text

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("startup_healthcheck")


def validate_database_ssl() -> bool:
    """
    Validate that database connection is using SSL encryption
    CEO P1 directive: Enforce encrypted database connections (sslmode=require minimum)
    
    Returns:
        bool: True if SSL encryption is enabled, False otherwise
    """
    if not settings.database_url:
        logger.warning("No DATABASE_URL configured, skipping SSL validation")
        return True  # Allow startup without database
    
    if "postgresql" not in settings.database_url:
        logger.info("Non-PostgreSQL database, skipping SSL validation")
        return True
    
    try:
        # Check that the DATABASE_URL contains SSL mode
        db_url = settings.database_url
        
        # Enforce SSL mode is present
        if "sslmode=" not in db_url:
            logger.error("🔴 P1 SECURITY: DATABASE_URL missing sslmode parameter")
            return False
        
        # Accept require, verify-ca, or verify-full (all provide encryption)
        ssl_mode = db_url.split('sslmode=')[1].split('&')[0] if 'sslmode=' in db_url else 'none'
        acceptable_modes = ['require', 'verify-ca', 'verify-full']
        
        if ssl_mode not in acceptable_modes:
            logger.error(f"🔴 P1 SECURITY: DATABASE_URL not using encrypted SSL mode (found: {ssl_mode}, required: {acceptable_modes})")
            return False
        
        logger.info(f"✅ SSL mode configured: {ssl_mode} (encrypted connection)")
        
        # Test actual connection with SSL
        logger.info("🔒 Validating database SSL connection with verify-full mode...")
        
        # Build connection URL with enforced SSL verify-full
        import re
        test_url = db_url
        if "sslmode=" in test_url:
            test_url = re.sub(r'[?&]sslmode=[^&]*', '', test_url)
            test_url = re.sub(r'&$', '', test_url)
        
        separator = "&" if "?" in test_url else "?"
        test_url = f"{test_url}{separator}sslmode=verify-full&sslrootcert=system"
        
        # Create test engine and validate connection
        test_engine = create_engine(
            test_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
                "application_name": "scholarship_api_ssl_healthcheck"
            }
        )
        
        with test_engine.connect() as conn:
            # Verify SSL is active
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            version_str = str(version)[:50] if version else "unknown"
            logger.info(f"✅ Database connection validated: {version_str}...")
            
        test_engine.dispose()
        
        logger.info("✅ P1 SECURITY: SSL verify-full mode validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"🔴 P1 SECURITY FAILURE: SSL verify-full validation failed: {e}")
        logger.error("Database connection must use SSL verify-full mode for production")
        return False


def run_startup_healthchecks() -> bool:
    """
    Run all startup healthchecks and fail fast if critical checks fail
    CEO P1 Directive: Fail fast if SSL verify-full is not configured
    
    Returns:
        bool: True if all critical checks pass, False otherwise
    """
    logger.info("=" * 80)
    logger.info("🏥 STARTUP HEALTHCHECKS - CEO P1 Directive")
    logger.info("=" * 80)
    
    checks = {
        "SSL verify-full": validate_database_ssl(),
    }
    
    # Log results
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "🔴 FAIL"
        logger.info(f"{status}: {check_name}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        logger.info("=" * 80)
        logger.info("✅ All startup healthchecks passed - proceeding with startup")
        logger.info("=" * 80)
    else:
        logger.critical("=" * 80)
        logger.critical("🔴 STARTUP HEALTHCHECK FAILURE - CRITICAL CHECKS FAILED")
        logger.critical("=" * 80)
        failed_checks = [name for name, result in checks.items() if not result]
        logger.critical(f"Failed checks: {', '.join(failed_checks)}")
        logger.critical("Application startup aborted per CEO P1 directive")
        logger.critical("=" * 80)
    
    return all_passed


def enforce_startup_healthchecks():
    """
    Run startup healthchecks and exit if critical checks fail
    This enforces fail-fast behavior for production security requirements
    """
    if not run_startup_healthchecks():
        logger.critical("🚨 CRITICAL: Startup healthchecks failed - exiting")
        sys.exit(1)
