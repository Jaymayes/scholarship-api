# SEV-1 Execution Block

**RUN_ID:** CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001  
**Protocol:** AGENT3_HANDSHAKE v30 (Prod-First + Scorched Earth + 2-of-3)  
**Declared:** 2026-01-20T08:34:17Z  
**Status:** ACTIVE

## CEO Directive

1. HOTFIX WAF (`_meta` allowlist + XFH preserve)
2. OIDC Phase 2 (trust proxy + cookies + validation)
3. Unified PRODUCTION Deploy
4. Traffic = 0%
5. Finance Freeze ACTIVE

## Hard Safety Controls

| Control | Value | Enforced |
|---------|-------|----------|
| TRAFFIC_CAP | 0 | ✅ DO NOT RAISE |
| LEDGER_FREEZE | true | ✅ ACTIVE |
| PROVIDER_INVOICING_PAUSED | true | ✅ ACTIVE |
| FEE_POSTINGS_PAUSED | true | ✅ ACTIVE |
| LIVE STRIPE CHARGES | ABSOLUTELY NO | ✅ BLOCKED |

## Probe Requirements

- All probes use PUBLIC URLs only (no localhost)
- Add `Cache-Control: no-cache` and `?t=<epoch_ms>`
- Add `X-Trace-Id: RUN_ID.<component>`
- Add `X-Idempotency-Key: <UUIDv4>` on mutable requests
- 2-of-3 confirmation required (prefer 3-of-3)

## Recovery Phases

- [ ] Phase 0: Scorched Earth + Incident stamp
- [ ] Phase 1: WAF Hotfix (XFH preserve + _meta allowlist)
- [ ] Phase 2: Auth/OIDC Phase 2 repairs
- [ ] Phase 3: Unified PRODUCTION deployment
- [ ] Phase 4: Production verification (no localhost)
- [ ] Phase 5: Telemetry acceptance (A8)
- [ ] Phase 6: 10-minute Green Gate (Prod-only)
- [ ] Phase 7: Second confirmation per app
- [ ] Phase 8: Finance Freeze posture validation

## Stop/Abort Rules

If public verification fails for WAF/metrics/auth or Command Center still shows "Skipping … in progress" storms after patch:
- Print: "Attestation: UNSTABLE (SEV-1) — Prod verification failed; Traffic=0; Finance Freeze ACTIVE"
- STOP (no further changes)

## Attestation Target

STABLE (SEV-1 → SEV-2 Monitoring) with Traffic remaining 0% pending CEO/HITL staged reopen.
