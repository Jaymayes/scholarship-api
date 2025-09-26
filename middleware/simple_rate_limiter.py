"""
Simple Rate Limiter Implementation
Direct rate limiting implementation for FastAPI endpoints
"""

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request


class SimpleRateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if request is allowed
        Returns (allowed, remaining_requests)
        """
        current_time = time.time()

        with self.lock:
            # Clean old requests outside the window
            cutoff = current_time - window_seconds
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]

            # Check if under limit
            if len(self.requests[identifier]) < limit:
                self.requests[identifier].append(current_time)
                remaining = limit - len(self.requests[identifier])
                return True, remaining
            remaining = 0
            return False, remaining

# Global rate limiter instance
rate_limiter = SimpleRateLimiter()

def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Check if user is authenticated
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.user_id}"

    # Use IP address
    client_host = getattr(request.client, 'host', '127.0.0.1')
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_host = forwarded_for.split(",")[0].strip()

    return f"ip:{client_host}"

async def check_rate_limit(request: Request, limit_per_minute: int = 10):
    """
    Dependency to check rate limiting with Replit-specific handling
    """
    # Skip rate limiting for health checks and OPTIONS requests (Replit requirement)
    if request.method == "OPTIONS" or request.url.path in ["/health", "/healthz", "/readiness", "/metrics"]:
        return True

    identifier = get_client_identifier(request)
    allowed, remaining = rate_limiter.is_allowed(identifier, limit_per_minute, 60)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "trace_id": getattr(request.state, 'trace_id', 'unknown'),
                "code": "RATE_LIMITED",
                "message": f"Rate limit exceeded: {limit_per_minute} requests per minute",
                "status": 429,
                "timestamp": int(time.time()),
                "retry_after_seconds": 60
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(limit_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + 60))
            }
        )

    return True

# Rate limiting dependencies for different endpoints
async def search_rate_limit(request: Request):
    """Rate limit for search endpoints - 5 per minute for testing"""
    return await check_rate_limit(request, 5)

async def eligibility_rate_limit(request: Request):
    """Rate limit for eligibility endpoints - 10 per minute"""
    return await check_rate_limit(request, 10)

async def scholarships_rate_limit(request: Request):
    """Rate limit for scholarship endpoints - 20 per minute"""
    return await check_rate_limit(request, 20)

async def analytics_rate_limit(request: Request):
    """Rate limit for analytics endpoints - 5 per minute"""
    return await check_rate_limit(request, 5)
