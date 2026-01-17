# Manual Intervention Manifest
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**Timestamp**: 2026-01-17T19:47:00Z

## Apps Requiring Manual Verification

### A1 (Auth)
```bash
curl -I https://<auth-domain>/health -H "Cache-Control: no-cache"
# Verify: Set-Cookie SameSite=None; Secure; HttpOnly
```

### A3 (Agent)
```bash
curl https://<agent-domain>/health -H "Cache-Control: no-cache"
# Verify: {service:"scholarship-agent",status:"healthy"}
```

### A5 (B2C)
```bash
curl https://<b2c-domain>/pricing | grep -E "(pk_live_|pk_test_|stripe.js)"
# Verify: Stripe publishable key + stripe.js tag
```

### A6 (B2B)
```bash
curl https://<b2b-domain>/api/providers -H "Accept: application/json"
# Verify: JSON array (even [] is acceptable)
```

### A7 (SEO)
```bash
curl https://<seo-domain>/sitemap.xml | head -20
curl https://<seo-domain>/health
# Verify: Valid XML + health markers
```

### A8 (Telemetry)
```bash
curl -X POST https://<telemetry-domain>/api/events \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d '{"event":"test"}'
# Verify: {"success":true,"event_id":...}
```

## Verified
- A2 (Core Data): VERIFIED - scholarship_api running
