# OCA Executive Decision Block

**Status**: GO (Conditional) — ARMED_AWAITING_GATES  
**Authorization Token**: `CEO-20260119-OCA-PROMOTE-10PCT-PREAUTH`  
**Date**: 2026-01-19  
**Strategy**: B2B-led growth; lift First Document Uploads ≥10% without harming trust or unit economics  
**Positioning**: Editor/Coach — No AI essays; students write, we only assist  
**Guardrails**: $500 cap; LTV:CAC ≥4:1 check at T+24h

---

## Owner Assignments and Deadlines

| Owner | Deadline | Deliverable |
|-------|----------|-------------|
| Legal | T+4h | `legal_copy_signed` to A8 with SHA256, approver_id=GC_7721, repo_path, commit_sha, signed_at |
| Engineering A6 | T+12h | `a6_health_window_ok` with p95<200ms, error<0.5%, uptime=1.0, provider_register=200, oca_header=true |
| Ops/SRE | Immediate | Kill runbook drill (1-min), A/B template verification, schema flags live |
| Marketing/Comms | Immediate | Suppression rules active, UTM/A8 attribution verified |

### Schema Flags Required
- `holdout_control=true` for 10% control
- Cost telemetry: `cost_per_notified`, `cost_per_started`, `cost_per_completed`

### Compliance Line (All Surfaces)
> "No AI essays. Students write; we only assist."

---

## Launch Gates and Automation

### Auto-GO Trigger (THREE Gates Required)
All three events must arrive in A8:

#### 1. legal_copy_signed (T+4h)
- Approver: GC_7721
- SHA256 doc_hash, repo_path, commit_sha, signed_at
- **Failover**: Provider-Only banner + page CEO

#### 2. a6_health_window_ok (T+12h)
- p95 < 200ms
- error < 0.5%
- uptime = 1.0
- oca_header_present = true
- provider_register_status = 200

#### 3. a8_preflight_verifications_ok (Immediate)
- Kill drill proof attached
- A/B compliance screenshots with exact "No AI essays" text
- Holdout integrity: 10% control cohort with zero notification events
- Allocation drift ≤ 0.5pp; randomization locked
- Cost telemetry fields non-null in dry run:
  - cost_per_notified
  - cost_per_started
  - cost_per_completed
  - compute_per_completion
- Variant safeguard test: simulated acceptance dip → variant paused + CEO page captured
- Log hygiene sample: OCA header present; no PII in audit

### Post-Launch Sequence (Automatic)
1. Flag → `CANARY_5`
2. Provider banner ON
3. Canary emails A/B 50/50
4. 5-provider seed validation
5. Emit `oca_canary_started`

---

## SLOs, Guardrails, and Kill Logic

### SLO Thresholds
| Metric | Threshold |
|--------|-----------|
| P95 latency | ≤ 1.5s |
| Error rate | < 1.0% |
| Queue depth | ≤ 30 |
| Refunds | < 2.0% AND ≤ baseline +0.25pp |
| Complaints | = 0 |
| Violations | = 0 |

### Kill Response
- Within 60 seconds on breach
- Auto-rollback
- File A8 incident with root-cause placeholder and rollback proof

### Throttle Policy
- If P95 ≥ 1.3s (10-min avg) → reduce to 4/user/day
- Restore when P95 < 1.0s (30-min avg)

---

## Measurement Directives (Data-First)

### Core Activation Metric
**First Document Upload**

### Control Group
10% holdout (no notifications) to measure true lift

### T+2h Packet
- SLO by variant; queue depth
- Funnel: open → click → start → complete (by variant and control)
- Suppression match rate
- 0 complaints/violations confirmation
- Cost telemetry: cost per notified, per start, per completion
- Compute-per-completion

### T+6h Packet
- Trend vs. T+2h
- Refunds/chargebacks
- Provider acceptance vs. baseline
- Top failure signatures from Report Issue
- Interim A/B lift and control lift

### T+24h Packet
- Full readout + evidence pack
- 5 seed validations: OCA header, banner, report issue, audit entries, A8 IDs
- ROI view: ARPU lift, payback, unit-economics vs. $500 cap

---

## Promotion Rules

### 5% → 10% (Auto with Token)

**Condition**: All Success Criteria green at T+24h (including ROI/LTV:CAC ≥4:1 trajectory)

**Action**: Auto-emit `oca_canary_promoted` to 10% traffic

**Token**: `CEO-20260119-OCA-PROMOTE-10PCT-PREAUTH`

### 10% → 25% (Requires Brief)

**Condition**: T+36h brief required with:
- P95 ≤ 1.2s (last 6h)
- Error < 0.7%
- Completion lift ≥ +12% vs control
- Provider acceptance ≥ baseline
- Cost-per-completion within target margin

---

## Risk Controls (Playbook V2.0 Aligned)

### Academic Integrity
- Non-negotiable messaging on all surfaces
- No AI-written essays
- Strict COPPA/FERPA posture
- No PII in logs
- OCA header required in submissions and audits

### Legal Latency
- Provider-Only fallback if copy slips
- Page CEO at T+4h miss

### Autonomy Tax
- Accept up to 1.5s P95 during canary
- $500 hard budget cap

---

## Success Target (5% Canary)

| Metric | Target |
|--------|--------|
| Completion lift vs. control | ≥ +10% |
| Provider acceptance | Neutral-to-positive |
| Refunds | < 2.0% |
| Cost-per-completed | Validates scale economics |

---

## Variant Quality Safeguards

If provider acceptance dips below baseline for any variant:
1. Immediately pause that variant
2. Notify CEO with rapid QA plan

---

## Escalation Triggers

Page CEO on:
- `oca_canary_started` event
- Any gate miss
- Any provider complaint
- Any kill trigger

---

## Configuration Status

**LOCKED** — Guardrails set, execute per plan
