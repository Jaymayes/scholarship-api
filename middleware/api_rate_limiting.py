"""
API Rate Limiting Middleware
CRITICAL SECURITY: Global rate limiting enforcement with proper headers
"""
import logging
from collections.abc import Callable
from typing import Any

from fastapi import Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from production.api_commercialization import commercialization_service

logger = logging.getLogger(__name__)

class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    CRITICAL SECURITY MIDDLEWARE: Global API rate limiting enforcement

    This middleware enforces rate limits on ALL API endpoints and adds
    proper X-RateLimit-* headers to every response for transparency.

    Security features:
    - Enforces rate limits globally across all API endpoints
    - Adds standardized rate limit headers to ALL responses
    - Handles both per-minute and monthly quotas
    - Provides clear error messages for rate limit violations
    - Logs all rate limiting decisions for security monitoring
    """

    def __init__(self, app):
        super().__init__(app)
        self.protected_paths = [
            "/api/v1/scholarships",
            "/api/v1/search",
            "/api/v1/eligibility",
            "/api/v1/recommendations",
            "/api/v1/ai",
            "/api/v1/billing"
        ]

        # Endpoints that don't require API key authentication
        self.public_endpoints = [
            "/api/v1/billing/api-key",  # Key creation endpoint (public)
            "/api/v1/billing/tiers",    # Pricing info (public)
            "/status",                  # Status page (public)
            "/status/json",             # Status API (public)
            "/release-notes",           # Release notes (public)
            "/changelog"                # Changelog (public)
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Global rate limiting enforcement for all API endpoints
        """
        # Check if this endpoint requires API key authentication
        path = request.url.path

        # Check if this is a public endpoint
        is_public_endpoint = any(path == public_path or path.startswith(public_path)
                               for public_path in self.public_endpoints)

        needs_rate_limiting = (any(path.startswith(protected) for protected in self.protected_paths)
                              and not is_public_endpoint)

        if not needs_rate_limiting:
            # Non-protected endpoint, proceed without rate limiting
            return await call_next(request)

        # Extract API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix

        if not api_key:
            # No API key provided for protected endpoint
            return JSONResponse(
                status_code=401,
                content={
                    "error": "api_key_required",
                    "message": "X-API-Key header is required for this endpoint",
                    "documentation": "https://docs.scholarship-api.com/authentication"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check rate limits using the commercialization service
        endpoint = path.split("/")[-1] or "root"
        rate_limit_result = commercialization_service.check_rate_limits(api_key, endpoint)

        if not rate_limit_result["allowed"]:
            # Rate limit exceeded or invalid key
            status_code = rate_limit_result.get("status_code", 429)
            reason = rate_limit_result.get("reason", "rate_limit_exceeded")

            # Prepare error response
            error_content = {
                "error": reason,
                "message": self._get_error_message(reason),
                "documentation": "https://docs.scholarship-api.com/rate-limits"
            }

            # Add rate limit headers if available
            response_headers = rate_limit_result.get("headers", {})

            if reason == "rate_limit_exceeded":
                error_content["retry_after"] = response_headers.get("Retry-After", "60")
                error_content["rate_limits"] = {
                    "limit": response_headers.get("X-RateLimit-Limit"),
                    "remaining": response_headers.get("X-RateLimit-Remaining"),
                    "reset": response_headers.get("X-RateLimit-Reset")
                }

                # Log rate limit violation for security monitoring
                logger.warning(f"🚨 Rate limit exceeded: {api_key[:12]}*** on {endpoint}")
            else:
                # Log authentication failure
                logger.warning(f"🚨 Invalid API key attempt: {api_key[:12] if len(api_key) > 12 else '***'}*** on {endpoint}")

            return JSONResponse(
                status_code=status_code,
                content=error_content,
                headers=response_headers
            )

        # Rate limit check passed, proceed with request
        try:
            response = await call_next(request)

            # Add rate limit headers to successful responses
            rate_limit_headers = rate_limit_result.get("headers", {})
            for header_name, header_value in rate_limit_headers.items():
                response.headers[header_name] = header_value

            # Add billing information headers (for transparency)
            billing_info = rate_limit_result.get("billing_impact", {})
            if billing_info:
                response.headers["X-Billing-Overage"] = str(billing_info.get("monthly_overage", 0))
                response.headers["X-Billing-Charges"] = f"${billing_info.get('overage_charges', 0.0):.2f}"

            # Log successful API access
            tier = rate_limit_result.get("tier", "unknown")
            logger.info(f"✅ API access: {api_key[:12]}*** ({tier}) on {endpoint}")

            return response

        except Exception as e:
            logger.error(f"❌ Middleware error processing {endpoint}: {e}")
            raise

    def _get_error_message(self, reason: str) -> str:
        """Get user-friendly error messages for different failure reasons"""
        messages = {
            "invalid_api_key": "Invalid API key. Please check your X-API-Key header and ensure it's active.",
            "rate_limit_exceeded": "Rate limit exceeded. Please wait before making more requests.",
            "quota_exceeded": "Monthly quota exceeded. Please upgrade your plan or wait for next billing cycle.",
            "key_suspended": "API key has been suspended. Please contact support.",
            "key_cancelled": "API key has been cancelled. Please contact support for reactivation."
        }
        return messages.get(reason, f"Request denied: {reason}")


# FastAPI Dependency for manual rate limiting in specific endpoints
async def require_api_key_with_rate_limit(
    x_api_key: str | None = Header(None, alias="X-API-Key")
) -> dict[str, Any]:
    """
    FastAPI dependency for endpoints that need explicit rate limiting control

    Usage:
        @app.get("/api/v1/premium")
        async def premium_endpoint(
            rate_limit_info: Dict = Depends(require_api_key_with_rate_limit)
        ):
            # Endpoint logic here
            return {"data": "premium content"}
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check rate limits
    rate_limit_result = commercialization_service.check_rate_limits(x_api_key, "manual_check")

    if not rate_limit_result["allowed"]:
        status_code = rate_limit_result.get("status_code", 429)
        reason = rate_limit_result.get("reason", "rate_limit_exceeded")

        raise HTTPException(
            status_code=status_code,
            detail=f"Rate limit check failed: {reason}",
            headers=rate_limit_result.get("headers", {})
        )

    return {
        "api_key_info": rate_limit_result,
        "tier": rate_limit_result.get("tier"),
        "headers": rate_limit_result.get("headers", {}),
        "billing_impact": rate_limit_result.get("billing_impact", {})
    }
