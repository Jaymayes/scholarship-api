# Risk Register
**Scholar Ecosystem Audit**
**Date**: 2026-01-06

---

## Active Risks

| ID | Risk | Severity | Likelihood | Impact | Mitigation | Owner | Status |
|----|------|----------|------------|--------|------------|-------|--------|
| R1 | Auth Token Leakage | HIGH | LOW | Token theft, unauthorized access | Enforce SameSite=Strict, Secure on cookies; short token TTL; JTI revocation | A1 Team | MITIGATED |
| R2 | Revenue Blindness | HIGH | MEDIUM | Finance tile shows $0, CFO concern | Fix A6 to restore B2B flow; clear stale banners; verify A8 data lineage | A6/A8 | ACTIVE |
| R3 | A6 Service Outage | CRITICAL | CURRENT | No new provider onboarding | Check A6 console logs, verify secrets, redeploy | A6 Maintainer | ACTIVE |
| R4 | OIDC Client Misconfiguration | MEDIUM | MEDIUM | Users see "Session Expired" | Audit client_id, redirect_uri allowlist across apps | App Teams | OPEN |
| R5 | A2 /ready SLO Breach | MEDIUM | HIGH | Deploy health checks fail | Optimize DB queries in readiness check | A2 Team | OPEN |
| R6 | Stale Alert Fatigue | LOW | MEDIUM | Ops ignores real alerts | Clear stale banners; tune alert thresholds | A8 Admin | OPEN |

---

## Closed Risks

| ID | Risk | Resolution | Closed Date |
|----|------|------------|-------------|
| R-HIST-1 | SERVICE_AUTH_SECRET reuse | Dedicated secret deployed | 2025-12-17 |
| R-HIST-2 | CORS blocking custom domains | Added scholaraiadvisor.com | 2025-12-22 |
| R-HIST-3 | Redis connection spam | Set DISABLE_RATE_LIMIT_BACKEND=true | 2025-12-28 |

---

## Risk Mitigation Details

### R1: Auth Token Leakage
- **Current Controls**: 
  - RS256 JWKS for token signing
  - JTI-based revocation list in PostgreSQL
  - SameSite/Secure cookie attributes
- **Residual Risk**: Low - requires active session hijacking

### R2: Revenue Blindness
- **Root Cause**: A6 DOWN prevents new B2B events
- **Evidence**: $179.99 revenue exists in A2 (not $0)
- **Fix**: Restore A6 → events flow → A8 updates

### R3: A6 Service Outage
- **Symptoms**: HTTP 500 on all endpoints
- **Probable Cause**: Missing secrets or DB connection failure
- **Evidence**: TLS connects, app crashes before response
- **Fix Steps**:
  1. Access A6 Replit console
  2. Check startup logs for error
  3. Verify DATABASE_URL, STRIPE_* secrets
  4. Redeploy

### R4: OIDC Client Misconfiguration
- **Symptoms**: "invalid_request", "Session Expired"
- **A1 Status**: HEALTHY (OIDC infrastructure working)
- **Probable Cause**: Client apps using wrong client_id or redirect_uri
- **Fix**: Audit OAuth configs in A5, A6, A7

### R5: A2 /ready SLO Breach
- **Current**: P95 = 265ms
- **Target**: ≤150ms
- **Impact**: Deploy health checks may timeout
- **Fix**: Optimize DB/Stripe checks, consider caching

---

## Risk Heat Map

```
                    IMPACT
              Low    Medium   High
          ┌────────┬────────┬────────┐
    High  │        │   R5   │        │
LIKELIHOOD├────────┼────────┼────────┤
   Medium │   R6   │   R4   │   R2   │
          ├────────┼────────┼────────┤
    Low   │        │        │   R1   │
          └────────┴────────┴────────┘
    
    CRITICAL (Current): R3 (A6 DOWN)
```
