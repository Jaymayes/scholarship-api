"""
Enhanced Rate Limiting Middleware
Using slowapi with Redis backend and proper environment-aware configuration
"""

import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response, HTTPException
import time
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

def get_user_identifier(request: Request) -> str:
    """Get client identifier prioritizing authenticated user over IP"""
    # Check if user is set in request state by auth middleware
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.user_id}"
    
    # Extract from JWT token if available
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Use token suffix as identifier
        token = auth_header[7:]  # Remove "Bearer "
        if len(token) > 20:
            return f"token:{token[-20:]}"
    
    # Fall back to IP with X-Forwarded-For support
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        return f"ip:{ip}"
    
    return f"ip:{get_remote_address(request)}"

# Initialize limiter with Redis fallback to memory
def create_rate_limiter():
    """Create rate limiter with Redis or in-memory storage"""
    try:
        # Test Redis connection
        redis_client = redis.Redis.from_url(settings.get_backend_url, socket_timeout=2)
        redis_client.ping()
        logger.info("✅ Redis connected for rate limiting")
        
        return Limiter(
            key_func=get_user_identifier,
            storage_uri=settings.get_backend_url
        )
        
    except Exception as e:
        logger.warning(f"⚠️  Redis not available, using in-memory rate limiting: {e}")
        
        return Limiter(
            key_func=get_user_identifier,
            storage_uri="memory://"
        )

# Create the limiter instance
limiter = create_rate_limiter()

def get_rate_limit_for_environment(base_limit: str) -> str:
    """Adjust rate limits based on environment"""
    if settings.environment.value in ["local", "development"]:
        # Double the limits for dev environments
        parts = base_limit.split("/")
        if len(parts) == 2:
            count = int(parts[0])
            return f"{count * 2}/{parts[1]}"
    return base_limit

# Environment-aware rate limit decorators
def search_rate_limit():
    """Rate limit for search endpoints"""
    limit = get_rate_limit_for_environment(settings.rate_limit_search)
    return limiter.limit(limit)

def eligibility_rate_limit():
    """Rate limit for eligibility check endpoints"""
    limit = get_rate_limit_for_environment(settings.rate_limit_eligibility)
    return limiter.limit(limit)

def scholarships_rate_limit():
    """Rate limit for scholarship endpoints"""
    limit = get_rate_limit_for_environment(settings.rate_limit_scholarships)
    return limiter.limit(limit)

def analytics_rate_limit():
    """Rate limit for analytics endpoints"""
    limit = get_rate_limit_for_environment(settings.rate_limit_analytics)
    return limiter.limit(limit)

# Generic rate limiters
def public_rate_limit(limit: str = "60/minute"):
    """Rate limit for public endpoints"""
    return limiter.limit(get_rate_limit_for_environment(limit))

def authenticated_rate_limit(limit: str = "300/minute"):
    """Rate limit for authenticated endpoints"""
    return limiter.limit(get_rate_limit_for_environment(limit))

def admin_rate_limit(limit: str = "1000/minute"):
    """Rate limit for admin endpoints"""
    return limiter.limit(get_rate_limit_for_environment(limit))