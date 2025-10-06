"""
Rate Limit Middleware - CEO 100% Readiness Workstream A
Checks rate limits and enriches request state for structured logging
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from middleware.production_rate_limiter import check_rate_limit, token_bucket
from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check rate limits and enrich request state
    
    Sets the following fields in request.state for structured logging:
    - rate_limit_state: allow|throttle|block
    - rate_limit_key: user:xxx or ip:xxx
    - tokens_remaining: int
    - rl_backend: redis|memory
    """
    
    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/metrics",
        "/robots.txt",
        "/sitemap.xml",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    async def dispatch(self, request: Request, call_next):
        # Check if path is exempt
        if request.url.path in self.EXEMPT_PATHS:
            # Still set default values for logging
            request.state.rate_limit_state = "allow"
            request.state.rate_limit_key = None
            request.state.tokens_remaining = None
            request.state.rl_backend = "exempt"
            return await call_next(request)
        
        # Determine rate limit based on endpoint type
        limit, window = self._get_rate_limit(request)
        
        # Check rate limit
        rl_info = check_rate_limit(request, limit=limit, window=window)
        
        # Enrich request state for structured logging
        request.state.rate_limit_state = rl_info["rate_limit_state"]
        request.state.rate_limit_key = rl_info["rate_limit_key"]
        request.state.tokens_remaining = rl_info["tokens_remaining"]
        request.state.rl_backend = rl_info["rl_backend"]
        
        # Block request if rate limit exceeded
        if not rl_info["allowed"]:
            from fastapi.responses import JSONResponse
            
            retry_after = 60
            error_data = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Retry after {retry_after} seconds.",
                "retry_after": retry_after,
                "code": "RATE_LIMIT_EXCEEDED"
            }
            
            headers = {
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(__import__('time').time() + retry_after))
            }
            
            return JSONResponse(
                content=error_data,
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers=headers
            )
        
        # Continue with request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(rl_info["tokens_remaining"])
        response.headers["X-RateLimit-Backend"] = rl_info["rl_backend"]
        
        return response
    
    def _get_rate_limit(self, request: Request) -> tuple[int, int]:
        """
        Determine rate limit based on endpoint and auth status
        
        Returns:
            (limit, window_seconds)
        """
        path = request.url.path
        
        # Check if user is authenticated
        is_authenticated = hasattr(request.state, 'user') and request.state.user
        
        # Search endpoints - moderate limit
        if "/search" in path:
            return (60, 60) if is_authenticated else (30, 60)
        
        # Write operations - strict limit
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if "/auth/" in path:
                return (10, 60)  # Auth endpoints - very strict
            return (30, 60) if is_authenticated else (10, 60)
        
        # Read operations - generous limit
        if request.method == "GET":
            return (100, 60) if is_authenticated else (60, 60)
        
        # Default limit
        return (100, 60) if is_authenticated else (60, 60)
