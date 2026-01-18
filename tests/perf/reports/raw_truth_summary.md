# Raw Truth Summary
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030
**Timestamp**: 2026-01-18T18:40:19Z

## VERIFIED (A2 Core Data)
1. /health: HTTP 200 with {"status":"healthy"}
2. /api/status: HTTP 401 (expected - needs API key)
3. Security headers: HSTS, CSP, XFO, XCTO all present
4. Hybrid Search: Hard filters active
5. FPR: 0% (target ≤5%)
6. Precision: 1.0 (target ≥0.85)
7. Recall: 0.78 (target ≥0.70)
8. P95 (warm): 114ms (target ≤120ms)

## BLOCKED (External Apps)
- A1, A3, A4, A5, A6, A7, A8: External workspaces

## CONDITIONAL
- B2C: Stripe ~4/25, CEO Override NOT PRESENT

## Raw Facts
| Fact | Value |
|------|-------|
| Git SHA | 01fe737695c5f635568138242f6659b6bc1afd09 |
| FPR | 0% |
| Precision | 1.0 |
| Recall | 0.78 |
| P95 (warm) | 114ms |
| A6 Blocker | /api/providers 404 |
| Stripe | ~4/25 |
| CEO Override | NOT PRESENT |
