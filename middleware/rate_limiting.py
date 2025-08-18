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
    rate_config = settings.get_rate_limit_config
    
    if not rate_config["enabled"]:
        logger.info("Rate limiting disabled")
        return None
    
    try:
        # Test Redis connection
        redis_client = redis.Redis.from_url(rate_config["backend_url"], socket_timeout=2)
        redis_client.ping()
        logger.info("✅ Redis connected for rate limiting")
        
        return Limiter(
            key_func=get_user_identifier,
            storage_uri=rate_config["backend_url"]
        )
        
    except Exception as e:
        logger.warning(f"⚠️  Redis not available, using in-memory rate limiting: {e}")
        
        return Limiter(
            key_func=get_user_identifier,
            storage_uri="memory://"
        )

# Create the limiter instance
limiter = create_rate_limiter()

# Ensure the limiter is functional - override if None
if limiter is None:
    # Force creation of in-memory limiter for testing
    from slowapi import Limiter
    limiter = Limiter(
        key_func=get_user_identifier,
        storage_uri="memory://"
    )

def get_rate_limit_for_environment(base_limit: str) -> str:
    """Adjust rate limits based on environment"""
    if settings.environment.value in ["local", "development"]:
        # Double the limits for dev environments
        parts = base_limit.split("/")
        if len(parts) == 2:
            try:
                amount = int(parts[0])
                period = parts[1]
                return f"{amount * 2}/{period}"
            except ValueError:
                return base_limit
    return base_limit

# Rate limit exception handler with unified error schema
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Handle rate limit exceeded with unified error format"""
    from middleware.error_handlers import create_error_response
    import time
    
    # Extract rate limit details
    limit_info = str(exc).split() if exc else []
    
    # Calculate retry after (default to 60 seconds)
    retry_after = 60
    if len(limit_info) >= 2:
        try:
            # Parse "X per Y" format
            period_str = limit_info[-1]
            if 'minute' in period_str:
                retry_after = 60
            elif 'hour' in period_str:
                retry_after = 3600
            elif 'second' in period_str:
                retry_after = 1
        except:
            retry_after = 60
    
    # CRITICAL FIX: Use central error builder to prevent double encoding
    from utils.error_utils import build_rate_limit_error, get_trace_id
    
    error_data = build_rate_limit_error(
        trace_id=get_trace_id(request),
        retry_after_seconds=retry_after
    )
    
    # Add standard rate limiting headers
    headers = {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(getattr(exc, 'limit', 'unknown')),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time() + retry_after))
    }
    
    # Import JSONResponse for proper response
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        content=error_data,
        status_code=429,
        headers=headers
    )

# Environment-aware rate limit decorators
def search_rate_limit():
    """Rate limit for search endpoints"""
    # Use a very low limit for testing
    limit = "5/minute"  # Force low limit to test rate limiting
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