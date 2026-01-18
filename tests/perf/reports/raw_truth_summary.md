# Raw Truth Summary
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-040

## VERIFIED WORKING (A2 Core Data)
1. Health: HTTP 200 with markers
2. Hybrid Search: Hard filters active
3. FPR: 0% (target ≤5%)
4. Precision: 1.0 (target ≥0.85)
5. Recall: 0.78 (target ≥0.70)
6. Security Headers: All present

## CONDITIONAL
- B2C: Stripe configured, no charge (guardrail)
- B2B: API ready, A6 /api/providers 404

## BLOCKED
- A3, A5, A6, A7, A8: External workspaces

## Raw Facts
| Fact | Value |
|------|-------|
| Git SHA | 6e7842495a25ba6098c4789b5e5a91ed173041f9 |
| FPR | 0% |
| Precision | 1.0 |
| Recall | 0.78 |
| A6 Blocker | /api/providers 404 |
| A8 Gap | /healthz alias |
| Stripe | ~4/25 |
| CEO Override | NOT PRESENT |
