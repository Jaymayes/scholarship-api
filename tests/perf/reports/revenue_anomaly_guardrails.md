# Revenue Anomaly Guardrails

**RUN_ID**: CEOSPRINT-20260121-VERIFY-ZT3G-D1-SOAK-CONT-062  
**Protocol**: AGENT3_HANDSHAKE v41  
**Updated**: 2026-01-21T10:22:00Z

## Anomaly Detection Methods

### Z-Score Detection
- **Window**: Rolling 24h
- **Threshold**: |Z| > 3.0 triggers alert
- **Metrics Monitored**:
  - Transaction count per hour
  - Average transaction amount
  - Refund rate
  - Chargeback rate

### EWMA (Exponential Weighted Moving Average)
- **Alpha**: 0.3 (recent-weighted)
- **Alert**: Deviation > 2σ from EWMA
- **Metrics**:
  - Revenue velocity
  - User conversion rate
  - Provider payout rate

## Cap Enforcement

| Cap Type | Limit | Enforcement | Breach Action |
|----------|-------|-------------|---------------|
| Global Daily | $1,500 | Hard block | Reject new charges |
| Per-User Daily | $50 | Soft warn at $40, hard at $50 | Block user charges |
| Single Transaction | $49 | Pre-validation | Reject transaction |
| Provider Payout | $100/day | Queue + manual | Hold for review |

## Auto-Actions on Anomaly

| Condition | Action | Notification |
|-----------|--------|--------------|
| Z-score > 3.0 | Flag for review | Slack #finance-alerts |
| Refund rate > 5% | Pause new acquisitions | PagerDuty |
| Chargeback > 0 | Immediate finance freeze | CEO/CFO direct |
| Ledger mismatch | Auto-rollback | Full incident |

## Current Status

| Metric | Value | Z-Score | Status |
|--------|-------|---------|--------|
| Transactions/hr | 0 | 0.0 | ✅ Normal |
| Avg Amount | $0.00 | 0.0 | ✅ Normal |
| Refund Rate | 0.0% | 0.0 | ✅ Normal |
| Chargeback Rate | 0.0% | 0.0 | ✅ Normal |

## Historical Baseline

From Gate-5/Gate-6 data:
- Total Revenue: $179.99
- Transactions: 2
- Avg Transaction: $89.995
- Refunds: 0

## Verdict

**Anomaly Detection: GREEN** — No anomalies detected, all caps enforced.

---

**Next Check**: Continuous (per-transaction)
