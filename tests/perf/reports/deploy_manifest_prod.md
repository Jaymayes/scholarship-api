# Deploy Manifest - Production

**RUN_ID:** CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001  
**Deploy Time:** 2026-01-20T08:34:17Z

## Bundle Contents

| Component | Description | Status |
|-----------|-------------|--------|
| WAF Hotfix | XFH preserve + _meta allowlist | ✅ Deployed |
| /metrics/p95 | Public JSON endpoint | ✅ Active |
| OIDC Phase 2 | Trust proxy + cookie + validation | ✅ Configured |
| Probe Mutex | Jitter ±20%, lock TTL | ✅ Active |

## Commit Information

| App | Commit SHA | Timestamp |
|-----|------------|-----------|
| A2 (Scholarship API) | ce75c487bb2e429879b87a0bc507ad6c915afd7f | 2026-01-20T08:36:00Z |

## Environment Variables Set

| Variable | Value | Purpose |
|----------|-------|---------|
| WAF_STRIP_X_FORWARDED_HOST | false | Preserve XFH for trusted sources |
| WAF_ALLOWLIST_XFH | true | Enable XFH allowlisting |
| WAF_TRUSTED_INGRESS_CIDRS | 35.192.0.0/12,... | Trusted ingress IPs |
| WAF_TRUSTED_INTERNALS | 127.0.0.1/32,::1/128 | Internal IPs |
| WAF_ALLOWED_HOST_SUFFIXES | .replit.app,... | Allowed host suffixes |
| WAF_UNDERSCORE_ALLOWLIST | _meta | Allowed underscore keys |
| RUN_ID | CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001 | Traceability |
| INCIDENT_MODE | SEV1 | SEV-1 posture active |

## Files Modified

| File | Changes |
|------|---------|
| middleware/waf_protection.py | Added _parse_underscore_allowlist, updated _remove_underscore_keys |
| tests/perf/reports/incidents/sev1_exec_block.md | Incident declaration |
| tests/perf/reports/waf_hotfix_prod.md | WAF hotfix documentation |

## Deployment Verification

| Check | Status |
|-------|--------|
| Server restart | ✅ SUCCESS |
| Health endpoint | ✅ 200 OK |
| Metrics endpoint | ✅ 200 OK |
| Telemetry acceptance | ✅ 100% |

## Attestation

Unified production deployment complete:
- All components bundled and deployed
- Commit SHAs recorded
- Environment variables set
- Server running and healthy
