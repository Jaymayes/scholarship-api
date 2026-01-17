# Security Headers Report
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-032
**Timestamp**: 2026-01-17T20:45:47Z

## Headers Verified (A2 Core Data)

| Header | Required | Actual | Status |
|--------|----------|--------|--------|
| Strict-Transport-Security | max-age>=15552000 | max-age=15552000; includeSubDomains | PASS |
| Content-Security-Policy | Present | default-src 'none'; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none' | PASS |
| X-Frame-Options | DENY | DENY | PASS |
| X-Content-Type-Options | nosniff | nosniff | PASS |
| Referrer-Policy | no-referrer | no-referrer | PASS |
| Permissions-Policy | Present | camera=(), microphone=(), geolocation=(), payment=() | PASS |
| X-Trace-Id | Echo back | CEOSPRINT-20260113-VERIFY-ZT3G-032.headers | PASS |
| X-Waf-Status | passed | passed | PASS |

## Verdict: PASS
