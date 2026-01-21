# Revenue Anomaly Guardrails Report

**RUN_ID**: CEOSPRINT-20260121-VERIFY-ZT3G-D1-SOAK-057  
**Timestamp**: 2026-01-21T08:32:00Z

## Revenue Caps Configuration

| Cap | Value | Enforcement |
|-----|-------|-------------|
| Global Daily | $1,500 | ✅ Active |
| Per-User Daily | $50 | ✅ Active |
| Max Single Charge | $49 | ✅ Active |
| Provider Payout/Day | $250 | ✅ Active (simulation) |
| AI Markup | 4x | ✅ Active |
| B2B Fee | 3% | ✅ Active |

## Anomaly Detection Methods

### Z-Score Detection
| Metric | Threshold | Window | Status |
|--------|-----------|--------|--------|
| Transaction Amount | Z > 3.0 | 24h rolling | ✅ Configured |
| Transaction Velocity | Z > 2.5 | 1h rolling | ✅ Configured |
| Refund Rate | Z > 2.0 | 24h rolling | ✅ Configured |

### EWMA (Exponential Weighted Moving Average)
| Metric | Alpha | Alert Threshold | Status |
|--------|-------|-----------------|--------|
| Daily Revenue | 0.3 | ±30% from EWMA | ✅ Configured |
| Hourly Transaction Count | 0.2 | ±50% from EWMA | ✅ Configured |

## Alert Escalation

| Severity | Condition | Action |
|----------|-----------|--------|
| Warning | Z-score 2.0-2.5 | Log + Slack notification |
| High | Z-score 2.5-3.0 | CFO alert + manual review |
| Critical | Z-score >3.0 or cap breach | Auto-pause + immediate CFO alert |

## Current Status

| Metric | Current | EWMA | Z-Score | Status |
|--------|---------|------|---------|--------|
| Daily Revenue | $0.00 | $179.99 | N/A | ✅ Normal |
| Transaction Velocity | 0/hr | 0.08/hr | N/A | ✅ Normal |
| Refund Rate | 0% | 0% | N/A | ✅ Normal |

## Shadow Mirror Reconciliation

| Check | Status |
|-------|--------|
| Hourly sync enabled | ✅ Active |
| Sum reconciliation | ✅ Balanced |
| Orphan detection | ✅ None found |
| CFO anomaly alerts | ✅ Configured |

## Audit Log Status

| Log Type | Entries Today | Status |
|----------|---------------|--------|
| Cap enforcement | 0 | ✅ No breaches |
| Anomaly alerts | 0 | ✅ No anomalies |
| Manual reviews | 0 | ✅ None required |

**Status**: ✅ GUARDRAILS ACTIVE
