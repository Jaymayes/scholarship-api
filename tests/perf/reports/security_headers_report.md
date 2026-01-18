# Security Headers Report
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030
**Timestamp**: 2026-01-18T18:40:19Z

## A2 Core Data Headers

| Header | Required | Actual | Status |
|--------|----------|--------|--------|
| Strict-Transport-Security | max-age>=15552000 | max-age=15552000; includeSubDomains | PASS |
| Content-Security-Policy | Present | default-src 'none'; connect-src 'self' | PASS |
| X-Frame-Options | DENY | DENY | PASS |
| X-Content-Type-Options | nosniff | nosniff | PASS |

## External Apps
- A1-A8 (except A2): BLOCKED - See manual_intervention_manifest.md

## Verdict: A2 PASS, Others BLOCKED
