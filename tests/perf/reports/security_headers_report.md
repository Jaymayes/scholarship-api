# Security Headers Report

**Generated**: 2026-01-22T19:21:00Z  
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027

---

## Recommended Headers

| Header | Recommended Value | Status |
|--------|-------------------|--------|
| Strict-Transport-Security | max-age=15552000 | ⏳ Check in prod |
| Content-Security-Policy | strict allowlist | ⏳ Configure |
| X-Frame-Options | DENY | ⏳ Configure |
| X-Content-Type-Options | nosniff | ⏳ Configure |

---

## Current Headers (A2 /)

Headers captured from local service:

```
HTTP/1.1 200 OK
content-type: application/json
```

---

## CSP Allowlist (Recommended)

```
default-src 'self';
script-src 'self' js.stripe.com;
connect-src 'self' api.stripe.com;
frame-src 'self' js.stripe.com;
style-src 'self' 'unsafe-inline';
```

---

## Notes

Security headers are typically configured at the CDN/proxy layer (Cloudflare, nginx) rather than application level. Verify in production deployment.
