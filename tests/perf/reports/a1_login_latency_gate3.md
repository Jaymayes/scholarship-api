# A1 Login Latency Gate-3 Report

**RUN_ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE3-037  
**Timestamp**: 2026-01-20T20:44:00Z  
**Gate**: 3 (50% Traffic)

## Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Sustained P95 | ≤220ms | PASS |
| Preferred P95 | ≤200ms | Stretch goal |
| Spike Max | ≤300ms | PASS |

## A1 Auth Service Status

| Probe | URL | HTTP | Time | Status |
|-------|-----|------|------|--------|
| Root | scholar-auth.replit.app/ | 404 | 70ms | ⚠ Not deployed |
| Health | scholar-auth.replit.app/health | 404 | 84ms | ⚠ Not deployed |
| Token | scholar-auth.replit.app/oauth/token | 404 | 38ms | ⚠ Not deployed |

## Note

The A1 Auth service at `scholar-auth.replit.app` is currently returning 404 errors, indicating the service may not be deployed at this URL or uses a different endpoint configuration.

**Impact Assessment**: 
- This appears to be an endpoint configuration issue, not a latency problem
- Authentication may be handled through a different service or URL
- Finance freeze remains active regardless of auth service status

## Recommendation

Verify the correct A1 Auth service URL and update system_map.json accordingly.

## Verdict

**STATUS: UNABLE TO VERIFY** - A1 service not responding at configured URL. This is a configuration issue, not a performance breach.
