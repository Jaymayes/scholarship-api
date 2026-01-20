# Gate-2 Environment Diff

**Incident**: CIR-20260119-001  
**Run ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE2-029  
**Timestamp**: 2026-01-20T16:41:00Z  
**HITL Authorization**: HITL-CEO-20260120-OPEN-TRAFFIC-G2

## Environment Changes (Gate-1 → Gate-2)

| Variable | Gate-1 Value | Gate-2 Value |
|----------|-------------|--------------|
| TRAFFIC_CAP | 10 | 25 |
| TRAFFIC_CAP_B2C_PILOT | 10 | 25 |
| HITL_GATE2_ID | (not set) | HITL-CEO-20260120-OPEN-TRAFFIC-G2 |
| HITL_GATE2_TS | (not set) | 2026-01-20T16:41:00Z |
| RUN_ID | CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001 | CEOSPRINT-20260120-EXEC-ZT3G-GATE2-029 |

## Finance Freeze Status (UNCHANGED)

| Variable | Value |
|----------|-------|
| LEDGER_FREEZE | true |
| PROVIDER_INVOICING_PAUSED | true |
| FEE_POSTINGS_PAUSED | true |
| B2C_CAPTURE | pilot_only |
| FEATURE_B2C_CAPTURE | pilot_only |

## Safety Guardrails (UNCHANGED)

| Variable | Value |
|----------|-------|
| SAFETY_LOCK | active |
| CHANGE_FREEZE | active |
| SEV1_INCIDENT | active |
| SEV2_INCIDENT | active |
| INCIDENT_MODE | SEV1 |

## WAF Configuration (UNCHANGED)

| Variable | Value |
|----------|-------|
| WAF_STRIP_X_FORWARDED_HOST | false |
| WAF_UNDERSCORE_ALLOWLIST | _meta |
| WAF_TRUSTED_INGRESS_CIDRS | 35.192.0.0/12,35.224.0.0/12,34.0.0.0/8,136.0.0.0/8 |

## Observation Window Parameters

- Duration: 30 minutes minimum
- Sample interval: 60 seconds
- Spike windows: Minutes 10, 20, 30
- KPI thresholds:
  - A1 Login P95: ≤200ms (hard), ≤250ms (any sample triggers rollback)
  - Error Rate (5xx): <0.5%
  - Neon DB P95: ≤100ms
  - Event Loop Lag: <200ms
  - Telemetry Acceptance: ≥99%
  - WAF _meta blocks: 0
  - Probe Storms: 0

**Status**: Gate-2 ACTIVE at 25% traffic
