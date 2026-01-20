# SEV-1 Incident Declaration

**Incident ID:** CIR-20260119-001  
**Declared:** 2026-01-20T07:15:00Z  
**Status:** ACTIVE  
**Severity:** SEV-1 (Critical)

## Decision Block

- **INCIDENT_MODE:** SEV1
- **TRAFFIC_CAP:** 0% (pilot killed)
- **LEDGER_FREEZE:** true
- **PROVIDER_INVOICING_PAUSED:** true
- **FEE_POSTINGS_PAUSED:** true

## Root Cause

Self-inflicted WAF regression that stripped the `x-forwarded-host` header, breaking:
1. Auth (OIDC) callback validation
2. Internal health checks (410 Gone responses)

## Global Controls Active

| Control | Value | Purpose |
|---------|-------|---------|
| INCIDENT_MODE | SEV1 | Maximum containment |
| TRAFFIC_CAP | 0% | No user traffic until cleared |
| LEDGER_FREEZE | true | Prevent financial mutations |
| PROVIDER_INVOICING_PAUSED | true | Suspend invoicing |
| FEE_POSTINGS_PAUSED | true | Suspend fee postings |

## Anti-False-Positive Rules

1. External public URLs only for all checks
2. Add `Cache-Control: no-cache` and `?t=<epoch_ms>` to all requests
3. Ignore all prior `.md` reports (scorched earth)
4. Second Confirmation: any PASS requires 2-of-3 (HTTP+Trace, Logs, A8 round-trip); prefer 3-of-3

## Recovery Phases

- [x] Phase 0: Scorched Earth + State sanity
- [x] Phase 1: WAF emergency rollback + allowlist
- [x] Phase 2: Auth/OIDC repair
- [x] Phase 3: Health/synthetic monitors repair
- [x] Phase 4: Performance decompression
- [x] Phase 5: Telemetry 500 fix + BYPASS rules
- [x] Phase 6: SEO schema ZodError hotfix
- [x] Phase 7: 10-minute green gate
- [x] Phase 8: Second confirmation
- [x] Phase 9: Finance freeze validation

## Attestation

**Status:** STABLE (SEV-1 Cleared to SEV-2 Monitoring)  
**Cleared:** 2026-01-20T07:56:45Z  
**Traffic Cap:** 0% pending CEO/HITL reopen  
**All Acceptance Criteria:** PASS  
**Go/No-Go Report:** tests/perf/reports/go_no_go_report.md
