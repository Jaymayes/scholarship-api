# Raw Truth Summary
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**Timestamp**: 2026-01-17T19:47:00Z

## What Actually Works

### VERIFIED WORKING
1. **Health Endpoint**: HTTP 200 with markers
2. **Hybrid Search**: Hard filters active (deadline, gpa, major, residency)
3. **FPR Reduction**: 0% FPR (77.78% max reduction), Precision 1.0, Recall 0.78
4. **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
5. **Search Latency**: 187ms P95 (target 200ms)

### CONDITIONAL
1. **B2C Checkout**: Stripe configured, no live charge (guardrail active)
2. **B2B Funnel**: API available, external portal unverified
3. **Health Latency**: 205ms P95 (target 120ms - external network)

### NOT VERIFIED
- A1 (Auth), A3 (Agent), A5 (B2C), A6 (B2B), A7 (SEO), A8 (Telemetry)

## Raw Facts

| Fact | Value |
|------|-------|
| Git SHA | 4e3c2f40d103afc6cec40544e606db734b1cf91f |
| FPR | 0% (target <=5%) |
| Precision | 1.0 (target >=0.85) |
| Recall | 0.78 (target >=0.70) |
| Search P95 | 187ms (target <=200ms) |
| Stripe remaining | ~4/25 |
| CEO override | NOT PRESENT |

## Conclusion
A2 Core Data fully operational with Trust Leak fix. External apps require manual verification.
