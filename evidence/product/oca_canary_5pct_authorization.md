# OCA 5% Canary Authorization

**Status**: AUTO-GO (conditional)  
**Decision Date**: 2026-01-14  
**Traffic**: 5% of eligible users

---

## Approval Scope

| Parameter | Value |
|-----------|-------|
| Channel | Production |
| Traffic | 5% of eligible users |
| Randomization | Locked |
| Window | 24 hours OR 1,000 exposures (whichever first) |
| Comms | Student + provider sequences for canary cohort only |

---

## Pre-Launch Gates (Must All Be Green)

### A6 Provider Service
- 60-minute health window ≥ 99.9% uptime
- P95 < 200ms
- Error < 0.5%
- `provider_register` smoke test returns 200 with OCA header present
- **Owner**: Engineering Lead
- **Target**: Within 12 hours

### Legal
- Signed approval of copy deck and consent language
- Record stored in repo and linked in A8
- **Owner**: General Counsel
- **Due**: 4 hours

### Freeze
- Code freeze across OCA-touching repos during 24-hour canary

---

## Launch Checklist (Execute in Order)

1. Flip feature flag `one_click_apply.status = CANARY_5` and `cap = 5%`
2. Set `rate_limit = 5/day`
3. Configure experiment window
4. Enable provider dashboard banner and "Report Issue" auto-disable workflow
5. Send canary student emails (A/B split 50/50) to eligible cohort
6. Suppress under-13 and no-consent users
7. Emit A8 event `oca_canary_started` with:
   - cohort_id
   - variant allocations
   - SLO snapshot

---

## Real-Time Watch (A8)

### SLO
| Metric | Threshold |
|--------|-----------|
| P95 latency | ≤ 1.5s |
| Error rate | < 1.0% |
| Queue depth | ≤ 30 |

### Integrity
| Metric | Threshold |
|--------|-----------|
| Ghostwriting refusals | 100% |
| Provider complaints | 0 |

### Refunds
| Metric | Threshold |
|--------|-----------|
| 24h refunds | < 2.0% |
| Delta vs baseline | ≤ +0.25pp |

### Funnel
| Metric | Target |
|--------|--------|
| Open rate | ≥ 35% |
| CTR | ≥ 8% |
| Modal completion | ≥ 70% |
| Submit success | ≥ 50% |

---

## Kill/Rollback Runbook

**Response Time**: Act within 60 seconds

### Triggers
- Provider complaint ≥ 1
- Integrity violation ≥ 1
- P95 breach for 5 consecutive minutes
- Error ≥ 1.0% for 5 minutes
- Refund > 2.0% 24h

### Actions
1. Set `one_click_apply.status = DISABLED`
2. Publish `oca_feature_killed` with trigger
3. Pause canary emails
4. Notify providers via banner
5. Root-cause and produce fix/verify plan before any re-enable

---

## Promotion Criteria (to 10% after 24h)

| Category | Requirement |
|----------|-------------|
| Integrity | 0 provider complaints; 0 confirmed violations |
| Performance | P95 ≤ 1.5s; error < 1.0%; queue depth ≤ 30 |
| Finance | Refunds ≤ baseline +0.25pp and < 2.0% 24h |
| Provider | Acceptance rate no negative delta vs baseline |
| Growth | Completion rate lift ≥ +10% vs control with stable refund/complaint rates |

---

## Reporting Cadence

| Checkpoint | Content |
|------------|---------|
| T+2h | Initial health ping with SLO and early funnel read |
| T+6h | Executive midpoint snapshot |
| T+24h | Canary readout and 10% recommendation |

---

## Budget

| Item | Amount |
|------|--------|
| T-1 spend | ~$45 |
| 24-hour window cap | $500 total |
| Red-team/load testing | Existing budgets |

---

## Outstanding Gates

| Gate | Owner | Deadline |
|------|-------|----------|
| A6 green | Engineering Lead | Within 12 hours |
| Legal sign-off | General Counsel | 4 hours |

---

## Escalation

If either gate misses deadline:
- Escalate to CEO with revised timeline
- Include risk assessment

---

## Auto-GO Trigger

Once both gates are green:
1. Proceed automatically
2. Post `oca_canary_started` event in A8
