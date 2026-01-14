# Step-Up Token Consumption

**Token**: `CEO-20260114-PAID-PILOT-STEPUP`  
**Consumed**: 2026-01-14  
**Status**: ACTIVE

---

## Budget Change

| Parameter | Before | After |
|-----------|--------|-------|
| Daily Budget | $150 | **$300** |
| Pacing | Even | 30/30/40 AM/PM/evening |

---

## Success Gates Verified

| Gate | Threshold | Status |
|------|-----------|--------|
| CAC | ≤$8 for 24h | ✓ Met |
| ARPU | ≥1.8× CAC | ✓ Met |
| Refunds | ≤4% | ✓ Met |
| Stripe Success | ≥98.5% | ✓ Met |

---

## Day 2 Operating Orders

### Auto-Downshift Triggers (to $150/day)
Any 6h moving average breach:
- CAC > $10
- Stripe success < 98.5% for 30 min
- Fraud ≥ 0.5%
- Refund rate ≥ 4%

### Targeting Segments
1. First-upload abandoners
2. Checkout/credit cart abandoners
3. High-intent essay/transcript viewers

### Frequency Caps
- ≤3 impressions/user/day
- ≤7/week
- Suppress converters for 14 days

### Creative Budget Mix
- 70% current winner
- 20% challenger
- 10% exploratory

### Kill Criteria
After ≥500 impressions, drop any creative with:
- CTR −30% vs control
- CAC +25% vs cohort for 6h

---

## Landing Flows

Drive to First Upload and credit-gate with A8 events:
- `upload_started`
- `upload_completed`
- `credit_purchase`

---

## Compliance Guardrails

- Minors DoNotSell=true
- 0 PII in logs
- X-API-Key enforcement confirmed daily
- Refund p50 ≤ 30s
- Disputes = 0
- Fraud < 0.5%

---

## Performance Controls

- P95 ≤ 110ms
- Error ≤ 0.5%
- Search/match caching (60s TTL) through Week 1
- Auto-throttle if LLM/API projection > $300 or queue_depth ≥ 30

---

## Provider Operations

- Payout caps: $250/provider, $5,000 global
- 10% holdback, Net-14 (simulation)
- CFO go-live review: Day 7
- Weekly target: +20 providers, +60 listings

---

## Forecast (Directional)

At CAC ≤ $8 and ARPU ≈ $25:
- ~37-40 new purchases/day
- ~$930-$1,000 gross B2C/day
- ~$28k-$30k B2C net/month (if sustained)

---

## Reporting

- Day 2 T+12h/T+24h pilot reports
- Friday KPI 1-pager
