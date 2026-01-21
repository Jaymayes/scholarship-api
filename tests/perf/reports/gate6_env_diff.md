# Gate-6 Environment Configuration Diff

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-GATE6-GO-LIVE-052  
**Timestamp**: 2026-01-21T07:47:00Z

## Configuration Changes (Gate-5 → Gate-6)

| Setting | Gate-5 (Before) | Gate-6 (After) | Impact |
|---------|-----------------|----------------|--------|
| `gate` | 5 | 6 | GO-LIVE phase |
| `phase` | penny_test_complete | go_live | Active revenue |
| `finance_freeze` | true | **false** | Ledger writes enabled |
| `ledger_freeze` | true | **false** | Transaction recording |
| `provider_invoicing_paused` | true | **false** | B2B invoicing active |
| `fee_postings_paused` | true | **false** | Fee collection active |
| `live_stripe_charges` | LIMITED | **ENABLED** | Full capture |
| `capture_percent` | 0 | **1.00 (100%)** | All transactions captured |
| `shadow_ledger` | true | **false** | Live ledger only |
| `b2c_capture` | PENNY_TEST_COMPLETE | **LIVE** | B2C payments live |
| `b2b_capture` | N/A | **LIVE** | B2B payments live |
| `status` | awaiting_cfo_signoff | **go_live_active** | Operational |

## New Authorizations

| Authority | Token | Scope |
|-----------|-------|-------|
| CEO | HITL-CEO-20260121-GATE6-GO-LIVE | Full GO-LIVE |
| CFO | HITL-CFO-20260121-UNFREEZE-G6-GO-LIVE | 100% capture |

## Revenue Guardrails (Unchanged)

| Guardrail | Value |
|-----------|-------|
| Per-user daily cap | $50.00 |
| Global daily cap | $1,500.00 |
| Max single charge | $49.00 |
| Provider payout/day | $250.00 |
| AI markup | 4x |
| B2B fee | 3% |
| Holdback | 10% |

## Rollback Triggers (Unchanged)

| Trigger | Threshold |
|---------|-----------|
| Neon DB P95 | >150ms |
| Error rate | ≥0.5% |
| Event loop lag | ≥300ms (2 consecutive) |
| A8 acceptance | <99% |
| Reconciliation mismatch | Any |

## Verification Status

- [x] hitl-override.json updated
- [ ] Environment variables synced
- [ ] /metrics/config verified
