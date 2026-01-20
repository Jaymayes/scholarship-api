"""
Phase 4: Concurrency Limiter Middleware
Limits in-flight requests on hot paths to prevent resource exhaustion
SEV-2 CIR-20260119-001: Performance Decompression
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

HOT_PATHS = {
    "/api/v1/auth/login": 50,
    "/api/v1/auth/login-simple": 50,
    "/api/v1/scholarships/search": 100,
    "/api/v1/search": 100,
    "/api/v1/eligibility/check": 75,
}

DEFAULT_CONCURRENCY_LIMIT = 200


@dataclass
class ConcurrencyStats:
    current: int = 0
    rejected: int = 0
    peak: int = 0
    total_requests: int = 0


class ConcurrencyLimiterMiddleware(BaseHTTPMiddleware):
    """
    Limits concurrent in-flight requests per path pattern.
    
    Target metrics:
    - /api/login p95 ≤200ms
    - Prevents thread pool exhaustion under load
    """
    
    def __init__(
        self,
        app,
        hot_paths: dict[str, int] | None = None,
        default_limit: int = DEFAULT_CONCURRENCY_LIMIT,
        enabled: bool = True
    ):
        super().__init__(app)
        self.hot_paths = hot_paths or HOT_PATHS
        self.default_limit = default_limit
        self.enabled = enabled
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._stats: dict[str, ConcurrencyStats] = defaultdict(ConcurrencyStats)
        self._lock = asyncio.Lock()
    
    async def _get_semaphore(self, path: str) -> tuple[asyncio.Semaphore, int]:
        """Get or create semaphore for path with appropriate limit."""
        limit = self.default_limit
        for pattern, path_limit in self.hot_paths.items():
            if path.startswith(pattern):
                limit = path_limit
                break
        
        if path not in self._semaphores:
            async with self._lock:
                if path not in self._semaphores:
                    self._semaphores[path] = asyncio.Semaphore(limit)
        
        return self._semaphores[path], limit
    
    def _get_path_key(self, path: str) -> str:
        """Normalize path for semaphore lookup."""
        for pattern in self.hot_paths:
            if path.startswith(pattern):
                return pattern
        return "__default__"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)
        
        path = request.url.path
        path_key = self._get_path_key(path)
        semaphore, limit = await self._get_semaphore(path_key)
        stats = self._stats[path_key]
        
        if semaphore.locked() and stats.current >= limit:
            stats.rejected += 1
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily at capacity",
                    "detail": f"Too many concurrent requests to {path_key}",
                    "retry_after": 1
                },
                headers={
                    "Retry-After": "1",
                    "X-Concurrency-Limit": str(limit),
                    "X-Concurrency-Current": str(stats.current)
                }
            )
        
        start_time = time.monotonic()
        try:
            async with semaphore:
                stats.current += 1
                stats.total_requests += 1
                if stats.current > stats.peak:
                    stats.peak = stats.current
                
                response = await call_next(request)
                
                elapsed_ms = (time.monotonic() - start_time) * 1000
                response.headers["X-Concurrency-Current"] = str(stats.current)
                response.headers["X-Concurrency-Limit"] = str(limit)
                response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
                
                return response
        finally:
            stats.current -= 1
    
    def get_stats(self) -> dict:
        """Get current concurrency statistics for monitoring."""
        return {
            path: {
                "current": stats.current,
                "peak": stats.peak,
                "rejected": stats.rejected,
                "total": stats.total_requests,
                "limit": self.hot_paths.get(path, self.default_limit)
            }
            for path, stats in self._stats.items()
        }
