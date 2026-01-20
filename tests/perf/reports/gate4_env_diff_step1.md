# Gate-4 Environment Diff - Step 1

**RUN_ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE4-042  
**Timestamp**: 2026-01-20T22:44:00Z  
**HITL Authorization**: HITL-CEO-20260120-OPEN-TRAFFIC-G4-STEP1

## Configuration Changes

| Setting | Previous (Gate-3) | New (Gate-4 Step 1) |
|---------|-------------------|---------------------|
| gate | 3 | 4 |
| step | - | 1 |
| traffic_cap | 0.50 | 0.75 |
| traffic_cap_b2c_pilot | 0.50 | 0.75 |
| finance_freeze | true | true |
| ledger_freeze | true | true |
| provider_invoicing_paused | true | true |
| fee_postings_paused | true | true |
| live_stripe_charges | BLOCKED | BLOCKED |

## Rollback Triggers

| Trigger | Threshold |
|---------|-----------|
| Neon P95 | >150ms |
| A1 Login P95 | >240ms (2 consecutive) OR >320ms (any) |
| Error Rate 5xx | ≥0.5% |
| Event Loop Lag | ≥300ms (2 consecutive) |
| A8 Acceptance | <99% |

## Rollback Plan

If any trigger breaches:
1. Set TRAFFIC_CAP=0.50 immediately
2. Restore data/hitl-override.json.gate3-backup
3. Generate gate4_abort.md
