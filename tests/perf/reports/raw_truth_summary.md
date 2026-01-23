# Raw Truth Summary - ZT3G Auth Repair Sprint
**RUN_ID**: CEOSPRINT-20260123-EXEC-ZT3G-FIX-AUTH-009  
**Timestamp**: 2026-01-23T12:37:49Z

## Probe Results

| Probe | Target | Result | Evidence |
|-------|--------|--------|----------|
| A1 Discovery | /.well-known/openid-configuration | ✅ 200 | S256 listed |
| A1 Health | /health | ✅ 200 | {"status":"alive"} |
| A1 Readyz | /readyz | ✅ 200 | DB healthy, pool healthy |
| A5 /api/auth/login | /api/auth/login | ❌ 404 | Endpoint missing |
| A5 Alt Auth | /auth/start, /login | ✅ 200 | Pages render, no PKCE |
| A6 /api/auth/login | /api/auth/login | ⚠️ 302 | Redirects, no PKCE |
| A6 /api/providers | /api/providers | ✅ 200 | JSON array |
| A8 Health | /health | ✅ 200 | {"status":"ok"} |
| A8 Events | POST /api/events | ✅ 200 | Event persisted |

## PKCE Compliance

| Client | Endpoint Exists | Redirects to A1 | code_challenge | code_challenge_method=S256 |
|--------|-----------------|-----------------|----------------|---------------------------|
| A5 student-pilot | ❌ 404 | N/A | ❌ | ❌ |
| A6 provider-register | ✅ 302 | ✅ | ❌ | ❌ |

## Cross-Workspace Reality
- A1, A5, A6 are **separate Replit workspaces**
- Cannot edit from this workspace (A2)
- Manual intervention manifest generated
