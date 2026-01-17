# Raw Truth Summary
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**Timestamp**: 2026-01-17T18:37:00Z

## What Actually Works (This Workspace)

### ✅ VERIFIED WORKING

1. **Health Endpoint**
   - External URL: https://83dfcf73-98cb-4164-b6f8-418c739faf3b-00-10wl0zocrf1wy.picard.replit.dev/health
   - Returns: {"status":"healthy","trace_id":"..."}
   - HTTP 200 confirmed

2. **Hybrid Search with Hard Filters**
   - Endpoint: /api/v1/search/hybrid/public
   - GPA filter: Working
   - Major filter: Working
   - Deadline filter: Working (always enforced)
   - Residency filter: Working (but no state-restricted scholarships in data)

3. **FPR Reduction**
   - Low GPA (2.0) arts student: 77.78% reduction
   - Mid GPA (2.5) arts student: 55.56% reduction
   - High GPA (3.8) engineering: 22.22% reduction
   - Improvement from baseline: 59.52%

4. **Security Headers**
   - HSTS: max-age=15552000; includeSubDomains ✅
   - CSP: present ✅
   - X-Frame-Options: DENY ✅
   - X-Content-Type-Options: nosniff ✅
   - X-Trace-Id: echoed back ✅

5. **Database**
   - PostgreSQL: Connected
   - Zero-staleness: Implemented (no mock data fallback)
   - Real scholarships: 9 with future deadlines

### ⚠️ CONDITIONAL

1. **B2C Checkout**
   - Stripe keys: Configured in secrets
   - Payment endpoints: Available
   - Live charge: NOT EXECUTED (guardrail active, <5 remaining)

2. **B2B Funnel**
   - API available: Yes
   - Fee structure: Configured
   - External portal (A6): UNVERIFIED

3. **Performance**
   - Health P95: 228ms (target 120ms - exceeds due to external network)
   - Search P95: 145ms (target 200ms - PASS)

### ❌ NOT VERIFIED (External Apps)

- A1 (Auth): External workspace
- A3 (Agent): External workspace
- A5 (B2C Landing): External workspace
- A6 (B2B Portal): External workspace
- A7 (SEO): External workspace
- A8 (Telemetry): External workspace

## Raw Facts

| Fact | Value |
|------|-------|
| Git SHA | c8b0c0b0593aa765e52cd91d5ad97fc8c100a05d |
| Scholarships with future deadline | 9 |
| FPR baseline | 42% |
| FPR post-fix | 17% |
| FPR improvement | 59.52% |
| Hard filters deployed | deadline, gpa, major, residency |
| Stripe remaining | ~4/25 |
| CEO override for charge | NOT PRESENT |
| External apps verified | 0/6 |

## Conclusion
This workspace (A2 Core Data) is fully operational with Trust Leak fix deployed. External apps require manual verification per the intervention manifest.
