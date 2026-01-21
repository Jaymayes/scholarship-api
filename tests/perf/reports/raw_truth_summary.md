# Raw Truth Summary

**Run ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2S2-FIX-027  
**Protocol**: AGENT3_HANDSHAKE v30  
**Generated**: 2026-01-21T22:52:00Z

---

## Truth Table

| App | Expected | Actual | Delta |
|-----|----------|--------|-------|
| A0 | 200 + markers | 200 + markers | ✅ Match |
| A1 | 200 + OIDC | 000 timeout | ❌ Blocked |
| A2 | 200 + status | 000 timeout | ❌ Blocked |
| A3 | 200 + agent | 000 timeout | ❌ Blocked |
| A4 | 200 + sage | 000 timeout | ❌ Blocked |
| A5 | 200 + Stripe | 200, no Stripe | ⚠ Missing markers |
| A6 | 200 + JSON | 000 timeout | ❌ Blocked |
| A7 | 200 + sitemap | 000 timeout | ❌ Blocked |
| A8 | 200 + events | 200 + rate limit error | ⚠ Degraded |

---

## Root Causes

1. **A1-A4, A6-A7**: Apps in sleeping state or DNS misconfigured
2. **A5**: Landing page missing Stripe integration
3. **A8**: Upstash Redis rate limited

---

## No Fabrication Confirmation

All results above are from actual curl probes. No PASS was fabricated.
See tests/perf/evidence/raw_curl_evidence.txt for full probe output.
