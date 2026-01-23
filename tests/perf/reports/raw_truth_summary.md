# Raw Truth Summary - ZT3G Auth Fix
**RUN_ID**: CEOSPRINT-20260123-EXEC-ZT3G-FIX-AUTH-005  
**Timestamp**: 2026-01-23T11:03:35Z

## Probe Results

| Probe | Endpoint | Result | Evidence |
|-------|----------|--------|----------|
| A1 Discovery | /.well-known/openid-configuration | ✅ 200 | S256 in code_challenge_methods_supported |
| A1 Health | /health | ✅ 200 | {"status":"alive"} |
| A1 Readyz | /readyz | ✅ 200 | DB healthy, pool healthy |
| A5 Pricing | /pricing | ✅ 200 | 4509 bytes, Stripe.js not in static HTML |
| A5 Auth | /api/auth/login | ❌ 404 | Endpoint missing |
| A6 Auth | /api/auth/login | ⚠️ 302 | Redirects but no PKCE params |
| A6 Providers | /api/providers | ✅ 200 | JSON array returned |
| A8 Health | /health | ✅ 200 | {"status":"ok"} |
| A8 Events | POST /api/events | ✅ 200 | Event accepted |

## PKCE Status

| Client | Has /api/auth/login | Redirects to A1 | Includes code_challenge |
|--------|---------------------|-----------------|------------------------|
| A5 student-pilot | ❌ No (404) | N/A | ❌ No |
| A6 provider-register | ✅ Yes (302) | ✅ Yes | ❌ No |

## Cross-Workspace Reality
- A1, A5, A6 are **separate Replit workspaces**
- Cannot edit from this workspace (A2)
- Manual intervention manifest generated
