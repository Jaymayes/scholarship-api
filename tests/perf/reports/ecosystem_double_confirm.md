# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260109-1940-AUTO  
**Generated**: 2026-01-09T19:51:54Z  
**Protocol**: v3.5.1

## Fresh Fleet Health (Dual-Confirmed)

| App | Name | Probe 1 | Probe 2 | Latency | Status |
|-----|------|---------|---------|---------|--------|
| A1 | scholar-auth | ✅ 200 | ✅ OIDC valid | 189ms | PASS |
| A2 | scholarship-api | ✅ 200 (prod) | ✅ 200 (local) | 165/63ms | PASS |
| A3 | scholarai-agent | ❌ 404 | ❌ 404 | 101ms | FAIL |
| A4 | auto-page-maker | ✅ 200 | N/A | 166ms | SINGLE |
| A5 | student-pilot | ✅ 200 | N/A | 288ms | SINGLE |
| A6 | scholarship-sage | ✅ 200 | N/A | 175ms | SINGLE |
| A7 | scholaraiadvisor | ✅ 200 | ✅ sitemap | 294ms | PASS |
| A8 | a8-command-center | ❌ 404 | ❌ 404 | 111ms | FAIL |

## Conflicts (Ambiguity Rule)
1. **A3**: Context claims 64% readiness, probes show 404 → **NO-GO**
2. **A8**: Context claims 100%, probes show 404 → **NO-GO**

## Checksums
See tests/perf/evidence/checksums.json
