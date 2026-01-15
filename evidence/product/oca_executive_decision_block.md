# OCA Executive Decision Block

**Status**: FAILOVER ACTIVATED — DEGRADED (Provider-Only Mode)  
**Authorization Token**: `CEO-20260119-OCA-PROMOTE-10PCT-PREAUTH`  
**Lock Event**: `evt_1768428673887_yfharrqcg`  
**T0**: 2026-01-14T22:11:13Z  
**Current Clock**: T+07:44 (05:55Z)  
**Strategy**: B2B-led growth via First Document Upload lift  
**Positioning**: Editor/Coach — No AI essays; students write, we only assist  
**Guardrails**: $500 cap; LTV:CAC ≥4:1 at T+24h  
**Code Freeze**: Active and absolute

---

## Current Gate Status

| Gate | Event | Status | Deadline (UTC) |
|------|-------|--------|----------------|
| 1 | `a8_preflight_verifications_ok` | **PASSED** ✓ | Complete |
| 2 | `legal_copy_signed` | **MISSED** ✗ | 2026-01-15T02:11:13Z |
| 3 | `a6_health_window_ok` | Pending | 2026-01-15T10:11:13Z |

### Gate 2 Miss — Failover Details
- **Missed Deadline**: 2026-01-15T02:11:13Z
- **Mode**: Provider-Only (student notifications suppressed)
- **Events Required**:
  - `oca_failover_activated` with lock_event_id, missed_deadline_ts
  - `provider_only_banner_active = true` (screenshot_id)
  - `student_notifications_suppressed = true` (queue_count=0, suppression_rule_hash)

### Gate 3: a6_health_window_ok
- **Hard stop**: 2026-01-15T10:11:13Z (~4h16m remaining)
- Provider-only canary still requires this gate

---

## Immediate Orders (Failover Mode)

### Ops/SRE
- Flip to Provider-Only mode (if not already)
- Post to A8:
  - `oca_failover_activated` with lock_event_id, missed_deadline_ts
  - `provider_only_banner_active = true` (screenshot_id)
  - `student_notifications_suppressed = true` (queue_count=0, suppression_rule_hash)
- Correct dashboards: status → Gate 2 Missed / Failover Active
- Purge or hard-hold any queued student emails/modals
- Confirm zero sends after 02:11:13Z
- Budget/SLO guardrails unchanged; maintain kill ≤60s and throttle policies

### General Counsel
- Page CEO with RCA/ETA
- Post `legal_incident_created` with doc_hash placeholder and remediation plan
- No hot-fixing copy during freeze

### Engineering A6 (Gate 3)
- Continue toward Gate 3 by 10:11:13Z (~4h16m remaining)
- Pre-warm capacity sized for provider-only traffic (~10% of original expectation)
- Keep proactive throttle on
- Ensure: p95<200ms, error<0.5%, uptime=1.0, oca_header_present=true, provider_register=200

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

### Launch Condition (Provider-Only)

Auto-launch on receipt of `a6_health_window_ok`. Emit `oca_canary_started` with `mode = provider_only`.

### Post-Launch Sequence (Provider-Only)
1. Flag → `CANARY_5` with mode=provider_only
2. Provider banner ON
3. Student notifications SUPPRESSED
4. 5-provider seed validation
5. Emit `oca_canary_started` with mode=provider_only

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

### T+2h Packet — Provider-Only Version (Page CEO on Delivery)
- **SLOs**: P95, error, queue
- **Provider Funnel**: banner impressions → clicks → onboard start → verification task created → acceptance
- **Safety**: 0 complaints/violations
- **Integrity**: OCA header present; no PII in logs
- **Cost Telemetry**: cost_per_notified, cost_per_started, cost_per_completed (provider flow), compute_per_completion
- **Provider Metrics**: acceptance vs baseline, time-to-first-review, decline reasons (top 5)
- **Evidence**: kill-drill proof attached; screenshots of provider banner; confirmation of student suppression (post-02:11Z)

### T+6h Packet
- Trend vs. T+2h
- Refunds/chargebacks
- Provider acceptance vs. baseline
- Top failure signatures from Report Issue
- Interim A/B lift and control lift

### T+24h Decision (Provider-Only)

**No student promotion.** Success measured on B2B:
- Provider acceptance ≥ baseline
- Incidents/complaints = 0
- SLOs within thresholds; refunds/chargebacks = 0
- Unit economics: compute_per_completion within margin; LTV:CAC trajectory ≥4:1 (provider-side)

### T+24h Packet
- Full readout + evidence pack
- 5 seed validations: OCA header, banner, report issue, audit entries, A8 IDs
- ROI view: ARPU lift, payback, unit-economics vs. $500 cap

---

## Promotion Rules

### 5% → 10% (Auto with Token)

**Condition**: All green at T+24h:
- Completion lift ≥ +10% vs control
- Provider acceptance ≥ baseline
- Refunds < 2.0% AND ≤ baseline +0.25pp
- LTV:CAC trajectory ≥ 4:1 with LTV basis, CAC components, and compute_per_completion reported

**If any red/yellow**: Hold at 5% and include corrective plan

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

## Postmortem Requirement (Legal Miss)

GC to deliver 5-point brief:
1. Root cause
2. Why detection failed before T+3h45
3. Containment
4. Corrective actions
5. New sign-off path with auto-reminders

---

## Configuration Status

**FAILOVER ACTIVE** — Provider-Only Mode, Code Freeze Absolute
