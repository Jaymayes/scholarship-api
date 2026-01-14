# OCA Auto-GO Armed

**Status**: ARMED  
**Trigger**: Automatic at 5% once A8 receives BOTH gate events  
**Date**: 2026-01-14

---

## Approval

| Parameter | Value |
|-----------|-------|
| Go-live | Automatic at 5% |
| Trigger | `a6_health_window_ok` AND `legal_copy_signed` in A8 |
| Budget cap | $500 for 24h window |
| Randomization | Locked |
| Rate limit | 5/user/day |
| Kill-switches | Active |

---

## Gate Event Payloads (Required in A8)

### a6_health_window_ok
```json
{
  "p95": "<200ms",
  "error_rate": "<0.005",
  "uptime": "1.0",
  "provider_register": 200,
  "oca_header_present": true,
  "window_start": "<timestamp>",
  "window_end": "<timestamp>"
}
```

### legal_copy_signed
```json
{
  "doc_hash": "SHA256",
  "approver_id": "GC_7721",
  "repo_path": "<path>",
  "commit_sha": "<sha>",
  "signed_at": "<timestamp>"
}
```

---

## Pre-Trigger Requirements

1. Gate event payloads persisted to A8
2. Code freeze confirmed for OCA-touching repos (record `freeze_start` in A8)
3. Seed validation: 5 provider-seeded packets immediately after launch
   - Confirm OCA header present
   - Confirm dashboard banner behavior

---

## Auto-Launch Sequence

1. Flag flip → `one_click_apply.status = CANARY_5`
2. Enable provider dashboard banner
3. Send canary emails (A/B 50/50)
4. Emit `oca_canary_started` with SLO snapshot

---

## Real-Time Operations

### Monitoring
- SLO, integrity, refunds, funnel
- Alerting configured for SLA breach
- On-call path hot

### Kill Response
- Within 60 seconds on any trigger
- Post `oca_feature_killed` with trigger and remediation owner

---

## Reporting Cadence

| Checkpoint | Content |
|------------|---------|
| T+2h | Health ping (SLO + early funnel by variant) |
| T+6h | Midpoint (SLO, A/B, incidents, refunds, provider complaints) |
| T+24h | Readout with 10% recommendation + evidence pack |

### T+24h Evidence Pack
- Allure links
- Sample provider packet
- COPPA/FERPA log excerpts
- Revenue events A2→A8

---

## 10% Promotion Pre-Approval

**Condition**: All 5% criteria green at T+24h

| Criterion | Threshold |
|-----------|-----------|
| Complaints/violations | 0 |
| P95 latency | ≤ 1.5s |
| Error rate | < 1.0% |
| Refunds | < 2.0% AND ≤ baseline +0.25pp |
| Completion lift | ≥ +10% |
| Provider acceptance | No negative delta |

**Action**: Pre-authorized to advance to 10% without additional CEO approval  
**Event**: Emit `oca_canary_promoted`  
**Maintain**: Same kill triggers

---

## Escalation

If gates miss deadline:
- Legal T+4h
- A6 T+12h

Page CEO with:
- Revised ETA
- Risk assessment
- Rollback/hold cost
- Dependency issues

---

## Confirmations to Post in A8 Now

### canary_config_staged
```json
{
  "canary_id": "<id>",
  "cohort_id": "<id>",
  "variants": ["A", "B"],
  "freeze_window": "<start>-<end>"
}
```

### notification_plan_loaded
```json
{
  "suppression_logic_hash": "<SHA256>"
}
```

---

## Awaiting

Either:
1. `oca_canary_started` + T+2h health readout
2. SLA-breach alert with revised plan
