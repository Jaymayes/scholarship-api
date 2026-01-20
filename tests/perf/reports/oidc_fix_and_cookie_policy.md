# Phase 2 Auth/OIDC Repair: Cookie Policy and Set-Cookie Capture

**Date**: 2026-01-20  
**Component**: scholarship_api (A2)  
**Phase**: Auth/OIDC Repair - Phase 2  
**Status**: ✅ IMPLEMENTED

## Summary

This document captures the implementation of secure cookie policy as part of Phase 2 Auth/OIDC repair.

## Cookie Policy Requirements

Per CEO directive, all cookies MUST have the following attributes:

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| SameSite | None | Required for cross-origin OIDC flows between apps |
| Secure | true | HTTPS-only access (mandatory for SameSite=None) |
| HttpOnly | true | Prevent XSS attacks from accessing cookies |
| Path | / | Consistent access across all routes |

## Implementation

### Middleware: `middleware/secure_cookies.py`

A new middleware class `SecureCookieMiddleware` has been added that:

1. Intercepts all responses with `Set-Cookie` headers
2. Applies security attributes to each cookie:
   - Adds `SameSite=None` if not present
   - Replaces `SameSite=Lax` or `SameSite=Strict` with `SameSite=None`
   - Adds `Secure` flag if not present
   - Adds `HttpOnly` flag if not present
   - Adds `Path=/` if not present

### Middleware Registration

The middleware is registered in `main.py` in the security middleware stack:

```python
app.add_middleware(SecureCookieMiddleware)     # Phase 2 Auth/OIDC: Secure cookies
app.add_middleware(SecurityHeadersMiddleware)  # Security headers
```

## Expected Set-Cookie Headers

After this implementation, all Set-Cookie headers will be transformed:

**Before:**
```
Set-Cookie: session=abc123; Path=/api
```

**After:**
```
Set-Cookie: session=abc123; Path=/api; SameSite=None; Secure; HttpOnly
```

## Verification

### Manual Test

```bash
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/auth/login-simple \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' 2>&1 | grep -i "set-cookie"
```

### Automated Test

A test can verify cookie attributes:

```python
def test_secure_cookie_attributes():
    response = client.post("/api/v1/auth/login-simple", json={"username": "admin", "password": "admin123"})
    cookies = response.headers.get_list("set-cookie")
    for cookie in cookies:
        assert "Secure" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=None" in cookie
```

## OIDC Base URL Resolution Logic

The canonical base URL for OIDC operations is resolved using the following priority:

### Resolution Priority

1. **Environment Variable (Preferred)**: `OIDC_PUBLIC_BASE_URL` or `PUBLIC_BASE_URL`
   - If set, use this value as the canonical base URL
   - No fallback to headers, ensuring consistent OIDC issuer matching

2. **Forwarded Headers (Conditional Fallback)**: `X-Forwarded-Proto` + `X-Forwarded-Host`
   - Only used when environment variable is NOT set
   - Only trusted if request originates from allowlisted proxy IP

### Trusted Proxy IP Allowlist

```python
trusted_proxy_ips = [
    "127.0.0.1",           # localhost
    "::1",                 # IPv6 localhost
    "10.0.0.0/8",          # Private network (Replit internal)
    "172.16.0.0/12",       # Private network (Replit internal)
    "192.168.0.0/16",      # Private network
]
```

### Resolution Code (Python)

```python
def get_oidc_base_url(request: Request, settings: Settings) -> str:
    """Resolve canonical OIDC base URL with security checks."""
    # Priority 1: Environment variable
    if settings.oidc_public_base_url:
        return settings.oidc_public_base_url.rstrip("/")
    
    # Priority 2: X-Forwarded headers (only from trusted proxies)
    if settings.trust_proxy and is_trusted_proxy(request.client.host):
        proto = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host")
        if host:
            return f"{proto}://{host}".rstrip("/")
    
    # Fallback: Default configured URL
    return "https://scholarship-api-jamarrlmayes.replit.app"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OIDC_PUBLIC_BASE_URL | https://scholarship-api-jamarrlmayes.replit.app | Canonical base URL for OIDC redirect URIs |
| PUBLIC_BASE_URL | (alias for above) | Alternative env var name for OIDC base URL |
| TRUST_PROXY | true | Trust X-Forwarded-* headers from Replit proxy |

## Security Considerations

1. **SameSite=None + Secure**: These must be used together (browser requirement)
2. **HttpOnly**: Prevents JavaScript access to sensitive cookies
3. **OIDC Flows**: Cross-origin authentication requires SameSite=None

## Audit Trail

| Date | Action | Author |
|------|--------|--------|
| 2026-01-20 | Created secure cookie middleware | Agent3 |
| 2026-01-20 | Added OIDC_PUBLIC_BASE_URL config | Agent3 |
| 2026-01-20 | Updated main.py middleware stack | Agent3 |

---

**Artifact**: `tests/perf/reports/oidc_fix_and_cookie_policy.md`  
**Phase**: 2 - Auth/OIDC Repair  
**Protocol**: v3.5.1
