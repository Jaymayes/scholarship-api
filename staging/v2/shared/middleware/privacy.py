"""
Privacy Middleware (Age-Gate, DoNotSell, CSP)
Protocol: AGENT3_HANDSHAKE v30
Non-negotiable privacy & security hardening.
"""
import os
import time
import httpx
from typing import Callable, Optional
from functools import wraps

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

A8_EVENTS_URL = os.environ.get("A8_EVENTS_URL", "")


class PrivacyMiddleware(BaseHTTPMiddleware):
    """
    Age-gate middleware for under-18 users.
    If age < 18:
    - Sets DoNotSell=true
    - Disables third-party pixels (Meta, TikTok)
    - Serves CSP that excludes tracking
    - Logs compliance event to A8
    """
    
    BLOCKED_SCRIPTS = [
        "connect.facebook.net",
        "facebook.com",
        "analytics.tiktok.com",
        "tiktok.com",
        "googletagmanager.com",
        "google-analytics.com",
        "doubleclick.net",
        "facebook.net"
    ]
    
    CSP_MINOR = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    
    CSP_ADULT = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://*.stripe.com; "
        "frame-src https://js.stripe.com https://hooks.stripe.com; "
        "frame-ancestors 'self';"
    )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        user_age = request.state.__dict__.get("user_age")
        user_id = request.state.__dict__.get("user_id")
        
        if user_age is not None and user_age < 18:
            response.headers["Content-Security-Policy"] = self.CSP_MINOR
            response.headers["X-Privacy-Mode"] = "minor"
            response.set_cookie(
                key="do_not_sell",
                value="true",
                httponly=True,
                secure=True,
                samesite="none",
                max_age=31536000
            )
            
            await self._log_privacy_event(user_id, "privacy_enforced", {
                "reason": "under_18",
                "do_not_sell": True,
                "third_party_blocked": True
            })
        else:
            response.headers["Content-Security-Policy"] = self.CSP_ADULT
            response.headers["X-Privacy-Mode"] = "standard"
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    async def _log_privacy_event(self, user_id: Optional[str], event_type: str, payload: dict):
        """Emit privacy compliance event to A8."""
        if not A8_EVENTS_URL:
            return
        
        event = {
            "event_type": event_type,
            "source_app_id": "privacy_middleware_v2",
            "user_id": user_id,
            "payload": payload,
            "ts": int(time.time() * 1000)
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(A8_EVENTS_URL, json=event)
        except Exception:
            pass


def age_gate_dependency(min_age: int = 13):
    """
    FastAPI dependency for age-gating routes.
    Raises 403 if user is below minimum age.
    """
    from fastapi import HTTPException, Depends, Header
    
    async def check_age(
        request: Request,
        x_user_age: Optional[str] = Header(None)
    ):
        if x_user_age is not None:
            try:
                age = int(x_user_age)
                request.state.user_age = age
                
                if age < min_age:
                    raise HTTPException(
                        status_code=403,
                        detail=f"This feature requires users to be at least {min_age} years old"
                    )
                
                return age
            except ValueError:
                pass
        
        return None
    
    return Depends(check_age)


def set_user_context(user_id: str, age: Optional[int] = None):
    """
    Decorator to set user context on request state.
    Use in conjunction with PrivacyMiddleware.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            request.state.user_id = user_id
            if age is not None:
                request.state.user_age = age
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


CSP_MINOR_TEMPLATE = """
<!-- CSP for minors (under 18) - No third-party tracking -->
<meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self';
    frame-ancestors 'self';
">
"""

CSP_ADULT_TEMPLATE = """
<!-- Standard CSP (18+) - Stripe allowed -->
<meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://js.stripe.com;
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    connect-src 'self' https://*.stripe.com;
    frame-src https://js.stripe.com https://hooks.stripe.com;
    frame-ancestors 'self';
">
"""

DISCLAIMER_FOOTER = """
<footer style="margin-top: 40px; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; text-align: center;">
    <p>AI tools are for editing and discovery only; users are responsible for academic integrity.</p>
    <p>&copy; Scholar AI Advisor by Referral Service LLC. <a href="/privacy">Privacy</a> | <a href="/terms">Terms</a> | <a href="/accessibility">Accessibility</a></p>
</footer>
"""
