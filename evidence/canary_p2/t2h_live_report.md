# Canary Phase 2 - T+2h LIVE Report

**Run ID**: `CANARY-P2-20260113-LIVE-T2H`  
**Generated**: 2026-01-13T22:05:00Z  
**Stripe Mode**: **LIVE**  
**Traffic Weight**: 25%  
**Status**: GREEN

---

## CFO Token Consumed

**Token**: `CFO-20260114-STRIPE-LIVE-25`  
**Consumed**: 2026-01-13T21:44:00Z  
**Evidence**: evidence/canary_p2/cfo_token_consumption.md

---

## 1. SLO Snapshot (10-min rolling)

| Metric | A2 | Target | Status |
|--------|-----|--------|--------|
| P95 Latency | **96ms** | ≤120ms | ✓ PASS |
| Error Rate | **0%** | ≤0.5% | ✓ PASS |
| Samples | 30 | - | - |

Latency: Avg 65ms, P95 96ms

---

## 2. First Upload Parity

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Parity | **100%** | ≥99.5% | ✓ PASS |
| Journeys | 5/5 | - | - |

---

## 3. Stripe LIVE Status

| Metric | Value | Status |
|--------|-------|--------|
| Mode | **LIVE** | ✓ ACTIVE |
| Configured | true | ✓ |
| Webhook Secret | true | ✓ |
| Guardrails | Active | ✓ |

---

## 4. Revenue Guardrails

| Guardrail | Limit | Used | Remaining | Status |
|-----------|-------|------|-----------|--------|
| Per-user daily | $50 | $0 | $50 | ✓ OK |
| Global daily | $1,500 | $0 | $1,500 | ✓ OK |
| Max single | $49 | - | - | ✓ OK |

Provider payouts: Simulation only (until Phase 3)

---

## 5. Stripe Metrics (LIVE)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Auth Success Rate | - | ≥98% | Pending |
| Settlement Success | - | ≥98% | Pending |
| Refund Latency | - | <10min | Pending |
| Chargebacks | 0 | 0 | ✓ PASS |
| Disputes | 0 | 0 | ✓ PASS |

Note: Fresh LIVE mode - no transactions processed yet. Monitoring active.

---

## 6. Executive KPIs

### B2C Metrics

| Metric | Value | Baseline | Status |
|--------|-------|----------|--------|
| ARPU from Credits | $0 | - | Fresh |
| Visitor→Signup | TBD | 7-day SEO | - |
| Signup→First Upload | TBD | 7-day SEO | - |
| First Upload→Paid | TBD | 7-day SEO | - |
| Refund Rate | 0% | <5% | ✓ PASS |

### B2B Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Provider Fee | 3% | ✓ Configured |
| Active Providers | TBD | - |

### Unit Economics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| AI Markup | 4x | 4x | ✓ PASS |
| Gross Margin | - | ≥60% | Pending |
| CAC | Near $0 | Organic | ✓ PASS |

---

## 7. Verifier KPIs

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Pass Rate | 100% | ≥99% | ✓ PASS |
| FP Rate | 0% | <1% | ✓ PASS |

---

## 8. Incidents

| Severity | Count | MTTR | Status |
|----------|-------|------|--------|
| Sev-1 | 0 | N/A | ✓ PASS |
| Sev-2 | 0 | N/A | ✓ PASS |

---

## 9. Cost Velocity

| Category | Current | Projected 24h | Cap | Status |
|----------|---------|---------------|-----|--------|
| Compute | ~$0 | <$10 | $300 | ✓ OK |
| Stripe Fees | $0 | TBD | - | ✓ OK |
| Total | ~$0 | <$10 | $300 | ✓ OK |

Alert threshold ($240): Not triggered

---

## 10. Auto-Rollback Triggers

| Trigger | Current | Threshold | Status |
|---------|---------|-----------|--------|
| Sev-1 Incidents | 0 | Any | ✓ SAFE |
| P95 > 120ms | 96ms | 30+ min | ✓ SAFE |
| Stripe Success | - | <98% 30min | ✓ SAFE |
| Fraud Signals | 0% | >1% | ✓ SAFE |

---

## Phase 2 Status

All gates GREEN. Monitoring continues for 12h window.

| Gate | Status |
|------|--------|
| SLO P95 ≤ 120ms | ✓ PASS (96ms) |
| Error ≤ 0.5% | ✓ PASS (0%) |
| 0 Sev-1 | ✓ PASS |
| Stripe LIVE | ✓ ACTIVE |
| Guardrails | ✓ ACTIVE |

---

## Next Checkpoints

- T+6h: Phase 2 mid-point report
- T+12h: Phase 2 completion packet
- Phase 3 (50%): Requires `HITL-CEO-20260114-CANARY-PH3` with P95 ≤ 110ms
