"""
Secure Cookie Middleware
Phase 2 Auth/OIDC Repair: Enforce secure cookie policy on all Set-Cookie headers

Implements:
- SameSite=None (required for cross-origin auth flows)
- Secure flag (HTTPS only)
- HttpOnly flag (no JS access)
- Path=/ (accessible across all paths)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SecureCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce secure cookie policy on all Set-Cookie headers.
    
    CEO Directive Phase 2: All cookies MUST have:
    - SameSite=None (for OIDC cross-origin flows)
    - Secure (HTTPS only)
    - HttpOnly (prevent XSS attacks)
    - Path=/ (consistent access)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        set_cookie_headers = response.headers.getlist("set-cookie")
        
        if set_cookie_headers:
            response.headers._list = [
                (k, v) for k, v in response.headers._list 
                if k.lower() != b"set-cookie"
            ]
            
            for cookie in set_cookie_headers:
                secured_cookie = self._secure_cookie(cookie)
                response.headers.append("set-cookie", secured_cookie)
                logger.debug(f"Secured cookie: {secured_cookie[:50]}...")
        
        return response
    
    def _secure_cookie(self, cookie: str) -> str:
        """
        Apply secure attributes to a cookie string.
        
        Adds:
        - SameSite=None (if not present)
        - Secure (if not present)
        - HttpOnly (if not present)
        - Path=/ (if not present)
        """
        cookie_lower = cookie.lower()
        parts = [cookie]
        
        if "samesite" not in cookie_lower:
            parts.append("SameSite=None")
        elif "samesite=lax" in cookie_lower or "samesite=strict" in cookie_lower:
            cookie = self._replace_samesite(cookie, "None")
            parts = [cookie]
        
        if "secure" not in cookie_lower:
            parts.append("Secure")
        
        if "httponly" not in cookie_lower:
            parts.append("HttpOnly")
        
        if "path=" not in cookie_lower:
            parts.append("Path=/")
        
        return "; ".join(parts)
    
    def _replace_samesite(self, cookie: str, new_value: str) -> str:
        """Replace SameSite value in cookie string"""
        import re
        pattern = re.compile(r'samesite\s*=\s*\w+', re.IGNORECASE)
        return pattern.sub(f"SameSite={new_value}", cookie)
