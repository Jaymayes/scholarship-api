"""
Token Blocklist Service - JWT Revocation Support
SEC-05 REMEDIATION: Enable token revocation for compromised/logout tokens

Provides centralized token revocation checking via:
1. Redis SET (preferred for horizontal scaling)
2. PostgreSQL fallback (if Redis unavailable)

Usage:
    from services.token_blocklist import is_token_revoked, revoke_token
    
    if await is_token_revoked(jti):
        raise HTTPException(status_code=401, detail="Token revoked")
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

_redis_client = None
_redis_available = False

def _init_redis():
    """Initialize Redis client for token blocklist"""
    global _redis_client, _redis_available
    
    redis_url = os.getenv("REDIS_URL") or os.getenv("RATE_LIMIT_BACKEND_URL")
    
    if not redis_url:
        logger.info("Token blocklist: Redis not configured, using database fallback")
        return
    
    try:
        import redis
        _redis_client = redis.Redis.from_url(redis_url, socket_timeout=2)
        _redis_client.ping()
        _redis_available = True
        logger.info("✅ Token blocklist: Redis connected successfully")
    except Exception as e:
        logger.warning(f"Token blocklist: Redis unavailable ({e}), using database fallback")
        _redis_available = False

_init_redis()

BLOCKLIST_KEY = "token_blocklist"
BLOCKLIST_TTL_SECONDS = 86400 * 7  # 7 days (tokens typically expire in 30 min, but keep for audit)


async def is_token_revoked(jti: str) -> bool:
    """
    Check if a token (by JTI) has been revoked.
    
    Args:
        jti: JWT ID claim (unique token identifier)
        
    Returns:
        True if token is revoked, False otherwise
    """
    if not jti:
        return False
    
    # Try Redis first (faster, distributed)
    if _redis_available and _redis_client:
        try:
            result = _redis_client.sismember(BLOCKLIST_KEY, jti)
            if result:
                logger.debug(f"Token {jti[:8]}... found in Redis blocklist")
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis blocklist check failed: {e}, falling back to DB")
    
    # Fallback to PostgreSQL
    try:
        from sqlalchemy import text
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            result = db.execute(
                text("SELECT 1 FROM revoked_tokens WHERE jti = :jti AND expires_at > NOW()"),
                {"jti": jti}
            ).fetchone()
            
            if result:
                logger.debug(f"Token {jti[:8]}... found in DB blocklist")
                return True
            return False
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Token blocklist DB check failed: {e}")
        return False


async def revoke_token(jti: str, expires_at: Optional[datetime] = None, reason: str = "logout") -> bool:
    """
    Revoke a token by adding its JTI to the blocklist.
    
    Args:
        jti: JWT ID claim (unique token identifier)
        expires_at: When the token naturally expires (for cleanup)
        reason: Reason for revocation (logout, compromise, admin_action)
        
    Returns:
        True if successfully revoked, False on error
    """
    if not jti:
        return False
    
    if expires_at is None:
        expires_at = datetime.utcnow() + timedelta(seconds=BLOCKLIST_TTL_SECONDS)
    
    success = False
    
    # Add to Redis (with TTL for auto-cleanup)
    if _redis_available and _redis_client:
        try:
            ttl_seconds = max(1, int((expires_at - datetime.utcnow()).total_seconds()))
            _redis_client.sadd(BLOCKLIST_KEY, jti)
            _redis_client.expire(BLOCKLIST_KEY, ttl_seconds)
            logger.info(f"Token {jti[:8]}... revoked in Redis (reason: {reason})")
            success = True
        except Exception as e:
            logger.warning(f"Redis token revocation failed: {e}")
    
    # Also persist to PostgreSQL for durability
    try:
        from sqlalchemy import text
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            db.execute(
                text("""
                    INSERT INTO revoked_tokens (jti, revoked_at, expires_at, reason)
                    VALUES (:jti, NOW(), :expires_at, :reason)
                    ON CONFLICT (jti) DO NOTHING
                """),
                {"jti": jti, "expires_at": expires_at, "reason": reason}
            )
            db.commit()
            logger.info(f"Token {jti[:8]}... revoked in DB (reason: {reason})")
            success = True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB token revocation failed: {e}")
    
    return success


async def revoke_all_user_tokens(user_id: str, reason: str = "logout_all") -> int:
    """
    Revoke all tokens for a specific user.
    
    Note: This requires tracking user_id -> jti mapping, which isn't 
    currently implemented. For now, this is a placeholder that logs a warning.
    
    Full implementation would require:
    1. Redis SET per user: user_tokens:{user_id} -> [jti1, jti2, ...]
    2. Or scanning JWT claims in DB if tokens are stored server-side
    
    Args:
        user_id: User ID to revoke all tokens for
        reason: Reason for revocation
        
    Returns:
        Number of tokens revoked (0 if not implemented)
    """
    logger.warning(
        f"revoke_all_user_tokens called for user {user_id} (reason: {reason}). "
        "Full implementation requires user->jti mapping. Consider forcing re-auth via version bump."
    )
    return 0


async def cleanup_expired_tokens() -> int:
    """
    Clean up expired tokens from the blocklist.
    Called periodically to prevent unbounded growth.
    
    Returns:
        Number of tokens cleaned up
    """
    try:
        from sqlalchemy import text
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            result = db.execute(
                text("DELETE FROM revoked_tokens WHERE expires_at < NOW() RETURNING jti")
            )
            db.commit()
            deleted_rows = result.fetchall()
            count = len(deleted_rows)
            if count > 0:
                logger.info(f"Cleaned up {count} expired tokens from blocklist")
            return count
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Token blocklist cleanup failed: {e}")
        return 0


def get_blocklist_stats() -> dict:
    """
    Get blocklist statistics for health checks.
    
    Returns:
        Dict with redis_available, redis_count, db_count
    """
    stats = {
        "redis_available": _redis_available,
        "redis_count": 0,
        "db_count": 0
    }
    
    if _redis_available and _redis_client:
        try:
            stats["redis_count"] = _redis_client.scard(BLOCKLIST_KEY)
        except Exception:
            pass
    
    try:
        from sqlalchemy import text
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM revoked_tokens WHERE expires_at > NOW()")
            ).fetchone()
            stats["db_count"] = result[0] if result else 0
        finally:
            db.close()
    except Exception:
        pass
    
    return stats
