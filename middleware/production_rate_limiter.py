"""
Production-Grade Rate Limiting with Redis and Auto-Fallback
CEO Directive: 100% Readiness - Workstream A

Features:
- Redis-backed token bucket with automatic fallback to in-memory
- Health check with periodic retry
- Enriched structured logging (rate_limit_state, rate_limit_key, tokens_remaining, rl_backend)
- User-ID based limits when authenticated, IP-based otherwise
"""

import asyncio
import time
from collections import defaultdict
from typing import Optional

import redis
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class TokenBucketLimiter:
    """Token bucket rate limiter with Redis and in-memory backends"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_available = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        self.last_warn_time = 0
        self.warn_interval = 300  # Warn once per 5 minutes
        
        # In-memory fallback storage
        self.memory_tokens = defaultdict(lambda: {"tokens": 0, "last_refill": time.time()})
        
        # Try to connect to Redis on init
        self._check_redis_health()
    
    def _check_redis_health(self) -> bool:
        """Check Redis connectivity with timeout"""
        current_time = time.time()
        
        # Only check periodically to avoid overhead
        if current_time - self.last_health_check < self.health_check_interval:
            return self.redis_available
        
        self.last_health_check = current_time
        
        # Check if Redis is configured
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url or redis_url == "memory://":
            return False
        
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    decode_responses=True
                )
            
            self.redis_client.ping()
            
            if not self.redis_available:
                logger.info("✅ Redis rate limiting backend connected")
            
            self.redis_available = True
            return True
            
        except Exception as e:
            if self.redis_available:
                logger.error(f"❌ Redis connection lost: {e}")
            
            # Warn periodically, not on every request
            if current_time - self.last_warn_time > self.warn_interval:
                if settings.environment.value == "production":
                    logger.error(
                        f"💥 PRODUCTION DEGRADED: Redis unavailable. "
                        f"Using in-memory fallback (single-instance only). "
                        f"Error: {e}"
                    )
                else:
                    logger.warning(f"⚠️  Development: Using in-memory rate limiting. Redis: {e}")
                self.last_warn_time = current_time
            
            self.redis_available = False
            return False
    
    def _get_tokens_redis(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Get tokens from Redis backend"""
        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            
            # Token bucket algorithm with Redis
            # Key format: ratelimit:{key}
            redis_key = f"ratelimit:{key}"
            
            # Get current state
            pipe.get(f"{redis_key}:tokens")
            pipe.get(f"{redis_key}:last_refill")
            result = pipe.execute()
            
            tokens = float(result[0]) if result[0] else limit
            last_refill = float(result[1]) if result[1] else now
            
            # Calculate token refill
            time_passed = now - last_refill
            refill_rate = limit / window
            tokens = min(limit, tokens + (time_passed * refill_rate))
            
            # Check if request can proceed
            if tokens >= 1:
                tokens -= 1
                allowed = True
            else:
                allowed = False
            
            # Update Redis state with TTL
            pipe = self.redis_client.pipeline()
            pipe.set(f"{redis_key}:tokens", tokens, ex=window * 2)
            pipe.set(f"{redis_key}:last_refill", now, ex=window * 2)
            pipe.execute()
            
            return allowed, int(tokens)
            
        except Exception as e:
            logger.warning(f"Redis token check failed: {e}, falling back to memory")
            self.redis_available = False
            return self._get_tokens_memory(key, limit, window)
    
    def _get_tokens_memory(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Get tokens from in-memory backend"""
        now = time.time()
        bucket = self.memory_tokens[key]
        
        # Calculate token refill
        time_passed = now - bucket["last_refill"]
        refill_rate = limit / window
        bucket["tokens"] = min(limit, bucket["tokens"] + (time_passed * refill_rate))
        bucket["last_refill"] = now
        
        # Check if request can proceed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            allowed = True
        else:
            allowed = False
        
        return allowed, int(bucket["tokens"])
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int, str]:
        """
        Check rate limit for a key
        
        Returns:
            (allowed, tokens_remaining, backend)
        """
        # Periodic health check
        self._check_redis_health()
        
        if self.redis_available:
            allowed, tokens = self._get_tokens_redis(key, limit, window)
            return allowed, tokens, "redis"
        else:
            allowed, tokens = self._get_tokens_memory(key, limit, window)
            return allowed, tokens, "memory"


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key from request
    Priority: user_id > authenticated token > IP address
    """
    # Check if user is authenticated (set by auth middleware)
    if hasattr(request.state, 'user') and request.state.user:
        user_id = getattr(request.state.user, 'user_id', None) or getattr(request.state.user, 'sub', None)
        if user_id:
            return f"user:{user_id}"
    
    # Extract from JWT token if available
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if len(token) > 20:
            return f"token:{token[-20:]}"
    
    # Fall back to IP with X-Forwarded-For support
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        return f"ip:{ip}"
    
    # Direct IP
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


# Global limiter instance
token_bucket = TokenBucketLimiter()


def check_rate_limit(request: Request, limit: int = 100, window: int = 60) -> dict:
    """
    Check rate limit and return enriched data for logging
    
    Returns dict with:
        - allowed: bool
        - rate_limit_state: str (allow|throttle|block)
        - rate_limit_key: str
        - tokens_remaining: int
        - rl_backend: str (redis|memory)
    """
    key = get_rate_limit_key(request)
    allowed, tokens_remaining, backend = token_bucket.check_rate_limit(key, limit, window)
    
    # Determine state based on tokens
    if allowed:
        if tokens_remaining > limit * 0.5:
            state = "allow"
        else:
            state = "throttle"  # Getting close to limit
    else:
        state = "block"
    
    return {
        "allowed": allowed,
        "rate_limit_state": state,
        "rate_limit_key": key,
        "tokens_remaining": tokens_remaining,
        "rl_backend": backend
    }


# Legacy slowapi limiter for backward compatibility
def get_user_identifier(request: Request) -> str:
    """Get client identifier for slowapi limiter"""
    return get_rate_limit_key(request)


def create_slowapi_limiter():
    """Create slowapi limiter with Redis or memory backend"""
    redis_url = getattr(settings, 'redis_url', None)
    
    if redis_url and redis_url != "memory://":
        try:
            redis_client = redis.Redis.from_url(redis_url, socket_timeout=2)
            redis_client.ping()
            logger.info("✅ Slowapi Redis limiter connected")
            return Limiter(key_func=get_user_identifier, storage_uri=redis_url)
        except Exception as e:
            logger.warning(f"Slowapi falling back to memory: {e}")
    
    return Limiter(key_func=get_user_identifier, storage_uri="memory://")


# Create slowapi limiter for decorator usage
slowapi_limiter = create_slowapi_limiter()


# Decorator functions for different endpoint types
def api_rate_limit(limit: str = "100/minute"):
    """General API rate limit"""
    if slowapi_limiter:
        return slowapi_limiter.limit(limit)
    return lambda f: f


def search_rate_limit(limit: str = "60/minute"):
    """Search endpoint rate limit"""
    if slowapi_limiter:
        return slowapi_limiter.limit(limit)
    return lambda f: f


def write_rate_limit(limit: str = "30/minute"):
    """Write operation rate limit"""
    if slowapi_limiter:
        return slowapi_limiter.limit(limit)
    return lambda f: f


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Handle rate limit exceeded errors"""
    retry_after = 60
    
    # Try to extract retry_after from exception
    if hasattr(exc, 'retry_after'):
        retry_after = int(exc.retry_after)
    
    from fastapi.responses import JSONResponse
    
    error_data = {
        "error": "Rate limit exceeded",
        "message": f"Too many requests. Retry after {retry_after} seconds.",
        "retry_after": retry_after,
        "code": "RATE_LIMIT_EXCEEDED"
    }
    
    headers = {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(getattr(exc, 'limit', 'unknown')),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time() + retry_after))
    }
    
    return JSONResponse(content=error_data, status_code=429, headers=headers)
