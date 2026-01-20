# Gate-3 Environment Diff

**RUN_ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE3-037  
**Timestamp**: 2026-01-20T20:42:00Z  
**HITL Authorization**: HITL-CEO-20260120-OPEN-TRAFFIC-G3

## Traffic Cap Changes

| Variable | Gate-2 | Gate-3 | Status |
|----------|--------|--------|--------|
| TRAFFIC_CAP | 0.25 | 0.50 | APPLIED |
| TRAFFIC_CAP_B2C_PILOT | 0.25 | 0.50 | APPLIED |

## Finance Freeze (UNCHANGED - ACTIVE)

| Variable | Value | Status |
|----------|-------|--------|
| LEDGER_FREEZE | true | ACTIVE |
| PROVIDER_INVOICING_PAUSED | true | ACTIVE |
| FEE_POSTINGS_PAUSED | true | ACTIVE |
| LIVE_STRIPE_CHARGES | BLOCKED | ACTIVE |

## Persistence

- **File**: `data/hitl-override.json`
- **Backup**: `data/hitl-override.json.gate2-backup`
- **Boot restoration**: Configured via startup script

## Rollback Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| Neon DB P95 | >150ms | IMMEDIATE ROLLBACK |
| A1 Login P95 | >220ms (2 consecutive) or >300ms (any) | IMMEDIATE ROLLBACK |
| 5xx Error Rate | >=0.5% | IMMEDIATE ROLLBACK |
| Event Loop Lag | >=300ms (2 consecutive) | IMMEDIATE ROLLBACK |
| Telemetry Acceptance | <99% sustained | IMMEDIATE ROLLBACK |
| WAF False Positive | any Trust-by-Secret block | IMMEDIATE ROLLBACK |
| Probe Storms | any "already in progress" | IMMEDIATE ROLLBACK |
