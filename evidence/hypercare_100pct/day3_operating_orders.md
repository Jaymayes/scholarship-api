# Day 3 Operating Orders

**Date**: 2026-01-14  
**Status**: ACTIVE  
**Budget**: $300/day (hold)

---

## Executive Decisions

### Budget and Pacing
- Daily budget: $300 rolling 24h
- Pacing: 30/30/40 AM/PM/evening
- No budget change until 72h pilot complete

### Segment Mix (Next 24h)
| Segment | Allocation | Notes |
|---------|------------|-------|
| Checkout Abandoners | 60% | Priority |
| Upload Abandoners | 30% | Secondary |
| Essay/Transcript Viewers | 10% | Auto-pause if CAC >$8 for 6h |

---

## Creative Plan

| Variant | Allocation | Type |
|---------|------------|------|
| "Complete your app" | 70% | Winner |
| "Last Chance Match" | 20% | Challenger |
| "Resume your upload in 2 clicks" | 10% | New benefit-led |

### Kill Criteria
After ≥500 impressions, drop if:
- CTR −30% vs control
- CAC +25% vs cohort for 6h

---

## Funnel & Pricing Experiments

### First-Upload UX (10% traffic)
- Sticky "Resume upload" CTA
- Prefilled step state
- Success metric: upload completion rate + credit conversion

### Credit Pack Framing (10% traffic)
- 1-pack baseline vs value-pack nudge (3-pack anchor)
- Report ARPU lift
- Auto-disable on refund spike (+1% in 24h)
- 4x markup maintained

---

## Cost & SLO Guardrails

| Parameter | Threshold | Action |
|-----------|-----------|--------|
| Analyze queue_depth | < 30 | Auto-throttle 50% if breached 15 min |
| P95 latency | ≤ 1.5s | Auto-throttle 50% if breached 15 min |
| Platform spend | ≤ $300 | Cut exploratory creative to 0% if exceeded 1h |

---

## Provider Ops (Week-1 Gap Close)

- Target: +7 providers, +12 listings in 48h
- Priority outreach: checkout-abandoning providers
- 3% fee instrumentation verified

---

## Compliance

- Retargeting only (no prospecting)
- Minors DoNotSell=true
- 0 PII in logs
- Daily API-key spot checks

---

## Reporting Required

### Day 3 T+12h and T+24h Pilot Reports
- Spend, CAC, ARPU7, ARPU:CAC ratio
- Refunds/fraud, Stripe success
- Auto-pauses triggered
- Segment/creative table with actions
- Funnel: visitor→signup→upload→paid
- SEO share
- Pricing/funnel experiment outcomes

### Friday KPI 1-Pager
- SLOs
- Revenue split (B2C/B2B)
- ARPU and margin
- SEO net pages + CTR
- Funnel deltas
- Cost drivers
- Provider progress
- Next week's ROI-ranked experiments

---

## Scale Criteria

**Do not change budget until 72h pilot complete**

Consider $300→$400 only if last 24h:
- CAC ≤ $7
- ARPU7 ≥ 2.0× CAC
- Refunds ≤ 3%
- Stripe ≥ 98.5%
- No incidents

Requires explicit CEO authorization with evidence.

---

## Trajectory

- CAC ≤ $8
- Margin ≥ 60%
- Organic sessions ≥ 85%
