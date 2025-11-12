"""
Service-to-Service Authentication Middleware
CEO Directive: Gate B - Secure provider_register callbacks

HMAC-based authentication for inter-service communication
Prevents unauthorized callbacks from spoofed sources
"""

import hashlib
import hmac
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from config.settings import settings

logger = logging.getLogger(__name__)

# Service authentication secret (shared between provider_register and scholarship_api)
# TODO: Store in Replit secrets as SERVICE_AUTH_SECRET
SERVICE_AUTH_SECRET = settings.jwt_secret_key or "INSECURE_DEFAULT_SECRET_REPLACE_IN_PRODUCTION"  # Temporary: Use JWT secret until SERVICE_AUTH_SECRET is provisioned

if not settings.jwt_secret_key:
    logger.warning("⚠️ SERVICE_AUTH_SECRET not configured - using insecure default. Configure JWT_SECRET_KEY in production!")


class ServiceAuthMiddleware:
    """
    Service-to-service authentication middleware
    
    Validates HMAC signature on incoming service callbacks
    Enforces timestamp drift limits to prevent replay attacks
    """
    
    def __init__(self, max_timestamp_drift_seconds: int = 300):
        """
        Initialize service auth middleware
        
        Args:
            max_timestamp_drift_seconds: Maximum allowed timestamp drift (default: 5 minutes)
        """
        self.max_drift = max_timestamp_drift_seconds
    
    async def __call__(self, request: Request, call_next):
        """
        Middleware handler
        
        Validates service authentication for protected endpoints
        """
        # Only apply to service callback endpoints
        if self._should_authenticate(request.url.path):
            auth_result = await self._validate_service_auth(request)
            
            if not auth_result["valid"]:
                logger.warning(
                    f"⚠️ Service auth failed: {auth_result['reason']} | "
                    f"path={request.url.path} | "
                    f"client_ip={request.client.host if request.client else 'unknown'}"
                )
                
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Service authentication failed",
                        "reason": auth_result["reason"],
                        "hint": "Include valid X-Service-Auth and X-Service-Timestamp headers"
                    }
                )
        
        response = await call_next(request)
        return response
    
    def _should_authenticate(self, path: str) -> bool:
        """
        Determine if path requires service authentication
        
        Args:
            path: Request path
            
        Returns:
            True if path requires service auth
        """
        # Protect provider onboarding callback endpoints
        protected_patterns = [
            "/api/v1/partners/",  # Partner callbacks
            "/api/v1/internal/",  # Internal service endpoints
        ]
        
        # Exclude health checks and public endpoints
        excluded_patterns = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json"
        ]
        
        for excluded in excluded_patterns:
            if path.startswith(excluded):
                return False
        
        for pattern in protected_patterns:
            if pattern in path and "/onboarding/" in path and "/complete" in path:
                return True
        
        return False
    
    async def _validate_service_auth(self, request: Request) -> dict:
        """
        Validate service authentication headers
        
        Args:
            request: FastAPI request
            
        Returns:
            Dict with validation result and reason
        """
        # Extract auth headers
        service_signature = request.headers.get("X-Service-Auth")
        service_timestamp = request.headers.get("X-Service-Timestamp")
        request_id = request.headers.get("X-Request-ID")
        
        if not service_signature:
            return {"valid": False, "reason": "Missing X-Service-Auth header"}
        
        if not service_timestamp:
            return {"valid": False, "reason": "Missing X-Service-Timestamp header"}
        
        # Validate timestamp drift (prevent replay attacks)
        try:
            timestamp = float(service_timestamp)
            current_time = time.time()
            drift = abs(current_time - timestamp)
            
            if drift > self.max_drift:
                return {
                    "valid": False,
                    "reason": f"Timestamp drift too large: {drift:.2f}s (max {self.max_drift}s)"
                }
        except ValueError:
            return {"valid": False, "reason": "Invalid timestamp format"}
        
        # Read request body for signature validation
        body = await request.body()
        
        # Compute expected HMAC signature
        expected_signature = self._compute_signature(
            method=request.method,
            path=request.url.path,
            body=body,
            timestamp=service_timestamp,
            request_id=request_id or ""
        )
        
        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(service_signature, expected_signature):
            return {"valid": False, "reason": "Invalid signature"}
        
        logger.info(
            f"✅ Service auth validated | "
            f"path={request.url.path} | "
            f"request_id={request_id} | "
            f"drift={drift:.2f}s"
        )
        
        return {"valid": True, "reason": "Signature valid"}
    
    def _compute_signature(
        self,
        method: str,
        path: str,
        body: bytes,
        timestamp: str,
        request_id: str
    ) -> str:
        """
        Compute HMAC-SHA256 signature for request
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Request timestamp
            request_id: Request ID for tracing
            
        Returns:
            Hex-encoded HMAC signature
        """
        # Construct signature payload
        payload = f"{method}:{path}:{timestamp}:{request_id}:{body.decode('utf-8')}"
        
        # Compute HMAC-SHA256
        signature = hmac.new(
            key=SERVICE_AUTH_SECRET.encode('utf-8'),
            msg=payload.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return signature


def generate_service_auth_signature(
    method: str,
    path: str,
    body: str,
    timestamp: Optional[float] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    Generate service auth headers for outgoing requests
    
    Used by provider_register to sign callbacks to scholarship_api
    
    Args:
        method: HTTP method (e.g., "POST")
        path: Request path (e.g., "/api/v1/partners/{id}/onboarding/{step}/complete")
        body: JSON body as string
        timestamp: Unix timestamp (default: current time)
        request_id: Request ID for tracing (default: None)
        
    Returns:
        Dict with X-Service-Auth, X-Service-Timestamp, X-Request-ID headers
    """
    if timestamp is None:
        timestamp = time.time()
    
    if request_id is None:
        from uuid import uuid4
        request_id = str(uuid4())
    
    timestamp_str = str(timestamp)
    
    # Compute signature
    payload = f"{method}:{path}:{timestamp_str}:{request_id}:{body}"
    signature = hmac.new(
        key=SERVICE_AUTH_SECRET.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return {
        "X-Service-Auth": signature,
        "X-Service-Timestamp": timestamp_str,
        "X-Request-ID": request_id
    }


async def require_service_auth(request: Request):
    """
    Dependency for requiring service authentication on specific routes
    
    Usage:
        @router.post("/endpoint", dependencies=[Depends(require_service_auth)])
        async def protected_endpoint():
            ...
    """
    middleware = ServiceAuthMiddleware()
    
    auth_result = await middleware._validate_service_auth(request)
    
    if not auth_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Service authentication failed: {auth_result['reason']}"
        )
    
    return auth_result
