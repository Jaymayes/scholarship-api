"""
Rate Limiting Middleware
Implements rate limiting using slowapi with Redis backend
"""

import os

import redis
from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize Redis client (fallback to memory if Redis not available)
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()  # Test connection
    print("✅ Connected to Redis for rate limiting")
    use_redis = True
except (redis.ConnectionError, redis.TimeoutError, Exception):
    print("⚠️  Redis not available, using in-memory rate limiting")
    redis_client = None
    use_redis = False

def get_limiter_key(request: Request) -> str:
    """
    Generate rate limiting key based on user authentication or IP
    Authenticated users get higher limits with user-based keys
    """
    # Check if user is authenticated (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP-based limiting for unauthenticated requests
    return f"ip:{get_remote_address(request)}"

def get_user_from_request(request: Request) -> str | None:
    """Extract user ID from request state (set by auth middleware)"""
    return getattr(request.state, "user_id", None)

# Initialize limiter
limiter = Limiter(
    key_func=get_limiter_key,
    storage_uri=REDIS_URL if use_redis else "memory://",
    default_limits=["1000 per hour"]  # Global default limit
)

# Rate limiting decorators for different access levels
def public_rate_limit():
    """Rate limit for public/unauthenticated endpoints"""
    return limiter.limit("60/minute")

def authenticated_rate_limit():
    """Rate limit for authenticated users (higher limits)"""
    return limiter.limit("300/minute")

def admin_rate_limit():
    """Rate limit for admin users (highest limits)"""
    return limiter.limit("1000/minute")

def bulk_operation_rate_limit():
    """Rate limit for expensive bulk operations"""
    return limiter.limit("10/minute")

def search_rate_limit():
    """Rate limit for search operations"""
    return limiter.limit("120/minute")

# Custom rate limit exceeded handler
def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    response = HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after,
            "type": "rate_limit_error"
        }
    )

    # Add headers for rate limiting info
    response.headers = {
        "Retry-After": str(exc.retry_after),
        "X-RateLimit-Limit": str(exc.detail.split("/")[0]),
        "X-RateLimit-Reset": str(exc.retry_after)
    }

    return response

# Middleware to set user context for rate limiting
async def set_rate_limit_context(request: Request, call_next):
    """Middleware to set user context for rate limiting"""
    # This would extract user info from JWT token if present
    # For now, we'll use a simple approach

    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        # In a real implementation, decode JWT here
        # For now, just extract a mock user ID for demonstration
        authorization.split(" ")[1]
        # This would be replaced with actual JWT decoding
        request.state.user_id = "mock_user_from_token"

    return await call_next(request)

# Rate limiting policies by endpoint type
RATE_LIMIT_POLICIES = {
    "public_search": "60/minute",           # Public scholarship search
    "public_detail": "120/minute",          # Public scholarship details
    "authenticated_search": "300/minute",   # Authenticated search
    "authenticated_write": "100/minute",    # Create/update operations
    "bulk_operations": "10/minute",         # Bulk eligibility checks
    "analytics": "60/minute",               # Analytics endpoints
    "admin_operations": "1000/minute",      # Admin operations
}

def get_rate_limit_for_endpoint(endpoint_type: str, user_roles: list | None = None) -> str:
    """Get rate limit policy for specific endpoint type and user role"""
    if user_roles and "admin" in user_roles:
        return RATE_LIMIT_POLICIES.get("admin_operations", "1000/minute")

    return RATE_LIMIT_POLICIES.get(endpoint_type, "60/minute")
