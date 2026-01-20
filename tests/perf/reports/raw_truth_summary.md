# Raw Truth Summary

**Incident:** CIR-20260119-001  
**Verification Time:** 2026-01-20T07:54:26Z  
**Status:** SEV-1 ACTIVE

## Endpoint Status Summary

| Endpoint | Status | Response Time |
|----------|--------|---------------|
| GET /health | ✅ 200 OK | <50ms |
| GET /ready | ✅ 200 OK | <50ms |
| GET /metrics/p95 | ✅ 200 OK | <50ms |
| GET /api/probe/ | ✅ 200 OK | <100ms |
| POST /api/telemetry/ingest | ✅ 200 OK | <100ms |
| POST /api/internal/pilot/synthetic-login | ✅ PASSED | <500ms |

## Service Status

- **API:** healthy
- **Database:** ready
- **Stripe:** configured
- **All Probes:** PASS

## TLS Verification

- **Protocol:** TLSv1.3
- **Cipher:** TLS_AES_128_GCM_SHA256
- **Certificate:** Valid (Let's Encrypt)
- **Expiry:** Mar 30 17:19:48 2026 GMT

## Containment Active

- **Traffic Cap:** 0%
- **Fleet SEO:** Paused
- **Scheduler Cap:** 0
- **Background Ops:** Blocked

## Performance Metrics (10-min window)

- **P50:** 26.57ms
- **P95:** 35.93ms
- **Sample Count:** 5
- **Error Rate:** 0.0%

## Attestation

All external health checks PASS. System is stable under containment.
Awaiting CEO/HITL override for staged traffic reopen.
