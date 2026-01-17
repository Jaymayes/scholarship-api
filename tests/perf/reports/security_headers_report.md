# Security Headers Report
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-036
**Timestamp**: 2026-01-17T21:36:21Z

## A2 Core Data Headers

| Header | Required | Actual | Status |
|--------|----------|--------|--------|
| Strict-Transport-Security | max-age>=15552000 | max-age=15552000; includeSubDomains | PASS |
| Content-Security-Policy | Present | default-src 'none'; connect-src 'self' | PASS |
| X-Frame-Options | DENY | DENY | PASS |
| X-Content-Type-Options | nosniff | nosniff | PASS |
| Referrer-Policy | no-referrer | no-referrer | PASS |
| X-Waf-Status | passed | passed | PASS |
| X-Trace-Id | Echo | CEOSPRINT-20260113-VERIFY-ZT3G-036.headers | PASS |

## Verdict: PASS
