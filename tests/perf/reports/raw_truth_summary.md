# Raw Truth Summary
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-032
**Timestamp**: 2026-01-17T20:45:00Z

## What Actually Works

### VERIFIED WORKING (A2 Core Data)
1. **Health Endpoint**: HTTP 200 with markers
2. **Hybrid Search**: Hard filters active (deadline, gpa, major, residency)
3. **FPR Reduction**: 0% FPR (77.78% max reduction), Precision 1.0, Recall 0.78
4. **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
5. **Search Latency (warm)**: 117ms P95 (target 200ms)

### CONDITIONAL
1. **B2C Checkout**: Stripe configured, no live charge (guardrail active, remaining ~4/25)
2. **B2B Funnel**: API available, external portal unverified
3. **Health Latency**: 230ms P95 via external network (internal is faster)

### NOT VERIFIED (External Apps)
- A3 (Agent): Requires /health endpoint
- A5 (B2C): Requires Stripe markers on /pricing
- A6 (B2B): Requires /api/providers endpoint
- A7 (SEO): Requires /sitemap.xml + /health
- A8 (Telemetry): Requires POST/GET /api/events

## Raw Facts

| Fact | Value |
|------|-------|
| Git SHA | 287dafca80655296733f1870d7924c78ff7f37ee |
| FPR | 0% (target ≤5%) |
| Precision | 1.0 (target ≥0.85) |
| Recall | 0.78 (target ≥0.70) |
| Search P95 (warm) | 117ms (target ≤200ms) |
| Stripe remaining | ~4/25 |
| CEO override | NOT PRESENT |
| External apps verified | 0/5 |

## Conclusion
A2 Core Data fully operational with Trust Leak fix deployed.
External apps require manual intervention per manifest.
B2C charge CONDITIONAL pending CEO override.
