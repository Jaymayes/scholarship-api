"""
Enhanced Rate Limiting Middleware - QA FIX Implementation
Implements production-ready rate limiting with Redis backend and proper client IP detection
"""

import json
import logging
import time

import redis
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config.settings import settings

logger = logging.getLogger(__name__)

class EnhancedRateLimiter:
    """Enhanced rate limiter with production-ready features"""

    def __init__(self):
        self.limiter = self._create_limiter()

    def _get_client_identifier(self, request: Request) -> str:
        """
        QA FIX: Enhanced client identification with proxy support
        Priority: JWT subject > Client IP (with proxy headers)
        """
        # Priority 1: Use authenticated user ID for per-user limits
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get('sub', 'anonymous')
            return f"user:{user_id}"

        # Priority 2: IP-based with proper proxy support
        client_ip = get_remote_address(request)

        # QA FIX: Handle X-Forwarded-For header for load balancers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client) from chain
            client_ip = forwarded_for.split(",")[0].strip()

        # Handle X-Real-IP header (NGINX)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip.strip()

        return f"ip:{client_ip}"

    def _create_limiter(self) -> Limiter | None:
        """
        QA FIX: Create Redis-backed rate limiter with production requirements
        DEF-005 FIX: Respect DISABLE_RATE_LIMIT_BACKEND setting
        """
        if settings.disable_rate_limit_backend:
            logger.info("📦 Using in-memory rate limiting (DISABLE_RATE_LIMIT_BACKEND=true)")
            return Limiter(
                key_func=self._get_client_identifier,
                default_limits=["100/minute"]
            )
        
        redis_url = settings.redis_url
        if redis_url.startswith("redis://localhost"):
            logger.info("📦 Using in-memory rate limiting (no external Redis configured)")
            return Limiter(
                key_func=self._get_client_identifier,
                default_limits=["100/minute"]
            )
        
        try:
            redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            redis_client.ping()

            logger.info("✅ Enhanced Redis rate limiting backend connected")
            return Limiter(
                key_func=self._get_client_identifier,
                storage_uri=redis_url,
                default_limits=["100/minute"]
            )

        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using in-memory fallback: {e}")
            return Limiter(
                key_func=self._get_client_identifier,
                default_limits=["100/minute"]
            )

    def create_rate_limit_response(self, exc: RateLimitExceeded) -> Response:
        """
        QA FIX: Create proper 429 response with required headers
        """
        retry_after = 60  # Default

        # Extract retry_after from exception if available
        if hasattr(exc, 'retry_after'):
            retry_val = getattr(exc, 'retry_after', None)
            if retry_val:
                retry_after = int(retry_val)

        response_data = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Retry after {retry_after} seconds.",
            "retry_after": retry_after,
            "limit": getattr(exc, 'limit', 'unknown'),
            "remaining": 0
        }

        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(getattr(exc, 'limit', 'unknown')),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time() + retry_after)),
            "Content-Type": "application/json"
        }

        return Response(
            content=json.dumps(response_data),
            status_code=429,
            headers=headers
        )

# Create global enhanced rate limiter instance
enhanced_limiter = EnhancedRateLimiter()
limiter = enhanced_limiter.limiter

# CEO v2.3 Section 3.2: Rate limit decorators per specification
def general_rate_limit():
    """General rate limit for most endpoints"""
    limit = "300/minute"  # CEO spec: baseline 300 rpm
    return limiter.limit(limit) if limiter else lambda f: f

def search_rate_limit():
    """CEO v2.5 A2: Read endpoints 300 rpm per origin"""
    limit = "300/minute"  # CEO spec A2: reads 300 rpm
    return limiter.limit(limit) if limiter else lambda f: f

def write_rate_limit():
    """CEO v2.5 A2: Provider writes 120 rpm per provider_id"""
    limit = "120/minute"  # CEO spec A2: writes 120 rpm
    return limiter.limit(limit) if limiter else lambda f: f

def eligibility_rate_limit():
    """Rate limit for eligibility checking (moderate)"""
    limit = "300/minute"  # General baseline
    return limiter.limit(limit) if limiter else lambda f: f

def provider_write_rate_limit():
    """CEO v2.5 A2: Strict 120 rpm for provider write operations"""
    limit = "120/minute"  # CEO spec A2: 120 rpm
    return limiter.limit(limit) if limiter else lambda f: f

# QA FIX: Enhanced exception handler
async def enhanced_rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Enhanced rate limit exception handler with proper headers"""
    return enhanced_limiter.create_rate_limit_response(exc)
