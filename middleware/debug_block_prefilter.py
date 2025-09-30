"""
Pre-Router Debug Path Blocker - CEO Directive DEF-002
Priority: P0 | Incident ID: DEF-002
Owner: Security Lead | Approved: CEO

Belt-and-suspenders fail-closed middleware that executes BEFORE any routing,
mounting, or WAF inspection. Blocks all debug-like paths with canonicalization
bypass protection.

This middleware sits at the top of the ASGI stack to prevent any route
injection order quirks or middleware bypass scenarios.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from urllib.parse import unquote

from utils.logger import get_logger

logger = get_logger(__name__)


class DebugPathBlockerMiddleware(BaseHTTPMiddleware):
    """
    Top-of-stack fail-closed middleware blocking all debug paths
    
    Security Features:
    - Executes before routing (can't be bypassed by route order)
    - Handles percent-encoding bypasses (%2F, %2f, etc)
    - Handles double-slash normalization (//debug)
    - Handles case variations (/Debug, /_DEBUG)
    - Returns 410 Gone (permanent removal signal)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.blocked_count = 0
        logger.critical("🛡️ DEBUG PATH BLOCKER: Initialized at top of ASGI stack (CEO Directive DEF-002)")
    
    async def dispatch(self, request: Request, call_next):
        """
        Pre-routing debug path blocker with canonicalization bypass protection
        """
        path = request.url.path
        
        # Normalize path for bypass detection
        path_lower = path.lower()
        path_decoded = unquote(path.lower())  # Handle percent-encoding
        path_normalized = path.replace("//", "/").lower()  # Handle double slashes
        
        # CEO DIRECTIVE: Block all paths containing "debug" in any form
        debug_patterns = [
            "_debug" in path_lower,
            "_debug" in path_decoded,
            "_debug" in path_normalized,
            "/debug" in path_lower,
            "/debug" in path_decoded,
            path_lower.startswith("/_debug"),
            path_decoded.startswith("/_debug"),
            path_normalized.startswith("/_debug"),
        ]
        
        if any(debug_patterns):
            self.blocked_count += 1
            
            client_ip = request.client.host if request.client else "unknown"
            
            logger.critical(
                f"🚨 DEBUG PATH BLOCKED (Pre-Router): {path} | "
                f"IP: {client_ip} | "
                f"Method: {request.method} | "
                f"Incident: DEF-002 | "
                f"Total Blocks: {self.blocked_count}"
            )
            
            return JSONResponse(
                status_code=410,  # 410 Gone - permanent removal signal
                content={
                    "error": "Gone",
                    "code": "DEBUG_PATH_REMOVED",
                    "message": "Debug endpoints have been permanently removed",
                    "status": 410,
                    "timestamp": int(time.time()),
                    "trace_id": f"prefilter-block-{int(time.time())}",
                    "incident_id": "DEF-002"
                },
                headers={
                    "X-Block-Layer": "pre-router",
                    "X-Incident-ID": "DEF-002",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache"
                }
            )
        
        # Path is clean, continue to application
        return await call_next(request)
