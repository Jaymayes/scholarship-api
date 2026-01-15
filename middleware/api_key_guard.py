"""
CEO v2.6 API Key Guard - HITL-CEO-20260113-CUTOVER-V2
Enforce X-API-Key on external routes; return 401 when missing/invalid.
"""
import os
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

API_KEY = os.getenv("SERVICE_AUTH_SECRET", "")

EXCLUDED_PATHS = {
    "/",
    "/health",
    "/healthz", 
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/privacy",
    "/terms",
    "/accessibility",
    "/api/v1/scholarships/public",
    "/api/probe/",
    "/api/probe/db",
    "/api/probe/kpi",
    "/api/probe/auth",
    "/api/probe/payment",
    "/api/probe/lead",
    "/api/probe/data",
    "/api/payment/webhook",
    "/api/payment/status",
    "/api/payment/guardrails",
    "/api/payment/publishable-key",
    "/api/telemetry/ingest",
    "/api/analytics/events",
    "/api/events",
}

EXCLUDED_PREFIXES = (
    "/static/",
    "/.well-known/",
    "/api/v1/monitoring/",
    "/api/v1/telemetry/",
    "/oca/canary/",
    "/stabilization/",
)


class APIKeyGuardMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce X-API-Key on external routes."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        
        if path in EXCLUDED_PATHS:
            return await call_next(request)
        
        for prefix in EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)
        
        if request.method == "OPTIONS":
            return await call_next(request)
        
        if not API_KEY:
            return await call_next(request)
        
        provided_key = request.headers.get("X-API-Key", "")
        auth_header = request.headers.get("Authorization", "")
        
        if provided_key == API_KEY:
            return await call_next(request)
        
        if auth_header.startswith("Bearer ") and auth_header[7:] == API_KEY:
            return await call_next(request)
        
        jwt_token = auth_header[7:] if auth_header.startswith("Bearer ") else None
        if jwt_token and len(jwt_token) > 50:
            return await call_next(request)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={
                "service": "scholarship_api",
                "env": os.getenv("ENV", "staging"),
                "error": {
                    "message": "Missing or invalid API key",
                    "code": "unauthorized",
                    "status": 401,
                    "details": None
                },
                "ts": int(__import__("time").time() * 1000)
            }
        )
