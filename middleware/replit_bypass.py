"""
EMERGENCY BYPASS: Replit Infrastructure WAF Workaround
Incident: WAF-BLOCK-20251008
Status: STANDBY (Deploy only if Option A fails by T+6:20)

This middleware provides a temporary workaround for Replit infrastructure WAF
blocking public GET endpoints. This is NOT a permanent solution - remove once
Replit configures proper WAF rules at infrastructure level.

Security Guardrails:
- Read-only access only (GET requests)
- Strict path matching (no wildcards)
- Token validation required
- Audit logging for all bypass usage
- Rate limiting preserved
- Feature flag gated for instant removal
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ReplitInfrastructureBypass(BaseHTTPMiddleware):
    """
    Emergency bypass for Replit infrastructure WAF blocking public endpoints.
    
    TEMPORARY WORKAROUND:
    - Replit's Google Frontend WAF blocks GET requests to public endpoints
    - Application code is correct (verified via localhost testing)
    - This bypass allows Replit proxy to inject auth token for public paths
    - Remove immediately once Replit configures proper WAF rules
    
    Security:
    - Token scoped to specific read-only paths only
    - Daily rotation via Replit Secrets
    - Audit logging for compliance
    - Feature flag for instant disable
    """
    
    # Scoped public endpoints (read-only only)
    ALLOWED_BYPASS_PATHS = {
        "/api/v1/scholarships": {
            "methods": ["GET"],
            "scope": "public_discovery",
            "description": "Public scholarship listing for student browsing"
        },
        "/api/v1/search": {
            "methods": ["GET"],
            "scope": "public_search",
            "description": "Public scholarship search for discovery"
        }
    }
    
    def __init__(self, app, enabled: bool = False):
        """
        Initialize bypass middleware.
        
        Args:
            app: FastAPI application
            enabled: Feature flag (default False - must explicitly enable)
        """
        super().__init__(app)
        self.enabled = enabled
        self.bypass_count = 0
        self.last_bypass_time = None
        
        if self.enabled:
            logger.warning(
                "🚨 REPLIT BYPASS ENABLED: This is a temporary workaround. "
                "Remove once Replit WAF configured properly. "
                f"Paths: {list(self.ALLOWED_BYPASS_PATHS.keys())}"
            )
        else:
            logger.info("Replit bypass middleware loaded but DISABLED (standby mode)")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with optional Replit infrastructure bypass."""
        
        # Feature flag check - bypass disabled by default
        if not self.enabled:
            return await call_next(request)
        
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # Check if this path is eligible for bypass
        if path in self.ALLOWED_BYPASS_PATHS:
            config = self.ALLOWED_BYPASS_PATHS[path]
            
            # Verify method is allowed (GET only)
            if method in config["methods"]:
                # Validate Replit infrastructure token
                replit_token = request.headers.get("X-Replit-Internal-Auth")
                
                if replit_token and self._validate_token(replit_token):
                    # Infrastructure pre-authorized - mark request
                    request.state.replit_bypass = True
                    request.state.bypass_reason = "replit_waf_workaround"
                    
                    # Audit logging
                    self.bypass_count += 1
                    self.last_bypass_time = time.time()
                    
                    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
                    
                    logger.info(
                        f"🔓 REPLIT BYPASS: {method} {path} | "
                        f"IP: {client_ip} | "
                        f"Scope: {config['scope']} | "
                        f"Count: {self.bypass_count} | "
                        f"Description: {config['description']}"
                    )
                    
                    # Continue to application
                    response = await call_next(request)
                    
                    # Add bypass header for monitoring
                    response.headers["X-Replit-Bypass"] = "active"
                    response.headers["X-Bypass-Reason"] = "infrastructure_waf_workaround"
                    
                    elapsed = (time.time() - start_time) * 1000
                    logger.info(f"✅ REPLIT BYPASS SUCCESS: {path} | {elapsed:.2f}ms")
                    
                    return response
                else:
                    # Token missing or invalid - reject
                    logger.warning(
                        f"⚠️ REPLIT BYPASS REJECTED: {method} {path} | "
                        f"Reason: Invalid or missing X-Replit-Internal-Auth token"
                    )
            else:
                # Method not allowed for bypass (e.g., POST/PUT/DELETE)
                logger.warning(
                    f"⚠️ REPLIT BYPASS REJECTED: {method} {path} | "
                    f"Reason: Method {method} not in allowed list {config['methods']}"
                )
        
        # Not a bypass path or validation failed - continue normally
        return await call_next(request)
    
    def _validate_token(self, token: str) -> bool:
        """
        Validate Replit infrastructure token.
        
        Security requirements:
        - Constant-time comparison (prevent timing attacks)
        - Token stored in Replit Secrets
        - Daily rotation recommended
        - Scoped to public read paths only
        
        Args:
            token: X-Replit-Internal-Auth header value
            
        Returns:
            True if token valid, False otherwise
        """
        import secrets
        
        expected_token = settings.REPLIT_BYPASS_TOKEN
        
        if not expected_token:
            logger.error("REPLIT_BYPASS_TOKEN not configured in secrets")
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(token, expected_token)
    
    def get_stats(self) -> dict:
        """Get bypass usage statistics for monitoring."""
        return {
            "enabled": self.enabled,
            "total_bypasses": self.bypass_count,
            "last_bypass_time": self.last_bypass_time,
            "allowed_paths": list(self.ALLOWED_BYPASS_PATHS.keys()),
            "incident_id": "WAF-BLOCK-20251008"
        }
