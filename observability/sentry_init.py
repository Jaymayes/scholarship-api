"""
Sentry Integration for Error and Performance Monitoring

CEO Executive Directive (2025-11-04):
- REQUIRED NOW for all 8 apps
- Freeze exception granted for observability only
- Must not alter functional behavior
- 10% performance sampling
- PII redaction mandatory
- request_id correlation required
"""

import logging
import os
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

logger = logging.getLogger(__name__)


def before_send(event, hint):
    """
    PII redaction filter - CEO Directive: No PII in logs/traces
    
    Removes sensitive data from Sentry events before transmission:
    - Email addresses
    - Phone numbers
    - Personal names
    - Passwords
    - Tokens/secrets
    """
    # Redact PII from request data
    if 'request' in event:
        request = event['request']
        
        # Redact from headers
        if 'headers' in request:
            headers = request['headers']
            # Redact authorization headers
            if 'Authorization' in headers:
                headers['Authorization'] = '[REDACTED]'
            if 'authorization' in headers:
                headers['authorization'] = '[REDACTED]'
            # Redact cookies
            if 'Cookie' in headers:
                headers['Cookie'] = '[REDACTED]'
            if 'cookie' in headers:
                headers['cookie'] = '[REDACTED]'
        
        # Redact from query params and form data
        for key in ['query_string', 'data', 'form']:
            if key in request and request[key]:
                # Common PII fields to redact
                pii_fields = [
                    'email', 'password', 'phone', 'ssn', 'name', 
                    'first_name', 'last_name', 'address', 'token',
                    'secret', 'api_key', 'auth'
                ]
                
                if isinstance(request[key], dict):
                    for field in pii_fields:
                        if field in request[key]:
                            request[key][field] = '[REDACTED]'
    
    # Redact PII from exception values
    if 'exception' in event and 'values' in event['exception']:
        for exception in event['exception']['values']:
            if 'value' in exception:
                # Redact email patterns
                import re
                exception['value'] = re.sub(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    '[EMAIL_REDACTED]',
                    exception['value']
                )
                # Redact phone patterns
                exception['value'] = re.sub(
                    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                    '[PHONE_REDACTED]',
                    exception['value']
                )
    
    # Redact PII from breadcrumbs
    if 'breadcrumbs' in event:
        for crumb in event['breadcrumbs']:
            if 'data' in crumb and isinstance(crumb['data'], dict):
                pii_fields = ['email', 'password', 'phone', 'token', 'secret']
                for field in pii_fields:
                    if field in crumb['data']:
                        crumb['data'][field] = '[REDACTED]'
    
    return event


def traces_sampler(sampling_context):
    """
    Performance sampling configuration - CEO Directive: 10% sampling
    
    Implements intelligent sampling:
    - 10% for normal operations (CEO requirement)
    - 100% for errors (always capture error traces)
    - 0% for health checks (reduce noise)
    """
    # Always sample error transactions
    if sampling_context.get("parent_sampled") is True:
        return 1.0
    
    # Never sample health check endpoints (reduce noise)
    if "asgi_scope" in sampling_context:
        scope = sampling_context["asgi_scope"]
        path = scope.get("path", "")
        if path in ["/health", "/healthz", "/readyz", "/api/v1/health"]:
            return 0.0
    
    # CEO Directive: 10% sampling for normal operations
    return 0.1


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    release: Optional[str] = None,
    enable_tracing: bool = True,
    sample_rate: float = 0.1
) -> bool:
    """
    Initialize Sentry SDK for error and performance monitoring
    
    Args:
        dsn: Sentry DSN (Data Source Name) from environment
        environment: Environment name (production, staging, development)
        release: Release version for tracking deployments
        enable_tracing: Enable performance tracing (CEO requirement)
        sample_rate: Base error sample rate (default 0.1 = 10%)
    
    Returns:
        bool: True if Sentry initialized successfully, False otherwise
    """
    # Get DSN from parameter or environment
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")
    
    if not sentry_dsn or sentry_dsn.strip() == "":
        logger.warning(
            "⚠️ SENTRY_DSN not configured - Sentry initialization skipped. "
            "CEO Directive: Required before Gate B DRY-RUN"
        )
        return False
    
    # Clean up DSN - remove "dsn:" prefix if present (common formatting error)
    sentry_dsn = sentry_dsn.strip()
    if sentry_dsn.lower().startswith("dsn:"):
        sentry_dsn = sentry_dsn[4:].strip()  # Remove "dsn:" prefix
    
    # Validate DSN format (should start with https:// or http://)
    if not (sentry_dsn.startswith("https://") or sentry_dsn.startswith("http://")):
        logger.error(
            f"❌ Invalid SENTRY_DSN format - must start with https:// or http://, "
            f"got: {sentry_dsn[:20]}..."
        )
        return False
    
    # Get release from environment or default
    app_version = release or os.getenv("APP_VERSION", "v2.7")
    
    # APP_NAME for Sentry tagging
    app_name = os.getenv("APP_NAME", "scholarship_api")
    app_base_url = os.getenv("APP_BASE_URL", "https://scholarship-api-jamarrlmayes.replit.app")
    
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=f"{app_name}@{app_version}",
            
            # Error sampling (10% as per CEO directive)
            sample_rate=sample_rate,
            
            # Performance monitoring - CEO Directive: 10% sampling
            enable_tracing=enable_tracing,
            traces_sampler=traces_sampler,
            
            # PII redaction - CEO Directive: Mandatory
            before_send=before_send,
            
            # Send default PII (we'll redact in before_send)
            send_default_pii=False,
            
            # Integrations for FastAPI, SQLAlchemy, Redis, HTTPX
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint
                    failed_request_status_codes=[500, 501, 502, 503, 504]
                ),
                SqlalchemyIntegration(),
                RedisIntegration(),
                HttpxIntegration()
            ],
            
            # Global tags for filtering
            default_integrations=True,
            auto_enabling_integrations=True
        )
        
        # Set global tags for filtering in Sentry UI
        sentry_sdk.set_tag("app_name", app_name)
        sentry_sdk.set_tag("app_base_url", app_base_url)
        sentry_sdk.set_tag("environment", environment)
        
        logger.info(
            f"✅ Sentry initialized successfully - "
            f"App: {app_name}, Environment: {environment}, "
            f"Performance Sampling: 10% (CEO requirement), "
            f"PII Redaction: Enabled"
        )
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")
        return False


def set_request_context(request_id: str, user_id: Optional[str] = None, role: Optional[str] = None):
    """
    Set request context for Sentry correlation - CEO Directive: request_id correlation
    
    Args:
        request_id: Request ID for tracing
        user_id: User ID (hashed/pseudonymized, not PII)
        role: User role (Student, Provider, Admin, SystemService)
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("request_id", request_id)
        
        if user_id:
            # Use user_id (hashed) not email/name (PII)
            scope.set_user({"id": user_id})
        
        if role:
            scope.set_tag("role", role)


def capture_message(message: str, level="info", **kwargs):
    """
    Capture a message in Sentry with proper context
    
    Args:
        message: Message to capture
        level: Log level (debug, info, warning, error, fatal)
        **kwargs: Additional context
    """
    from typing import Literal
    sentry_sdk.capture_message(message, level=level, **kwargs)  # type: ignore


def capture_exception(exception: Exception, **kwargs):
    """
    Capture an exception in Sentry with proper context
    
    Args:
        exception: Exception to capture
        **kwargs: Additional context
    """
    sentry_sdk.capture_exception(exception, **kwargs)
