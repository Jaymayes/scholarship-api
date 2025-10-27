# Daily Operations - Quick Start Guide
**For:** Operations Team, DevOps, Platform Engineers  
**Purpose:** Fast reference for daily monitoring and incident response  

---

## 🚀 Three Commands You Need Daily

### 1. Morning Health Check (9am)
```bash
curl https://your-api.replit.app/api/v1/observability/health-summary | jq
```
✅ Expected: `"status": "healthy"`, `"p95_compliance": true`

---

### 2. Latency Dashboard (Check 3x daily)
```bash
curl https://your-api.replit.app/api/v1/observability/latency-dashboard | jq
```
📊 Shows: P50/P95/P99 by endpoint group, error rate, slow queries

---

### 3. Daily KPI Report (End of day)
```bash
curl https://your-api.replit.app/api/v1/observability/kpi-report?period_hours=24 | jq
```
💰 Shows: Usage, conversions, revenue impact, business metrics

---

## 🔥 Incident Response

### Quick Stress Test (Before releases)
```bash
pytest tests/stress_test_hot_paths.py -m stress -v
```
**Pass Criteria:** Error rate <5%, zero auth regressions, stable P95

---

### Execute Optimization Plan (When P95 >120ms)
```bash
./scripts/execute_optimization_plan.sh
```
**Generates:** Baseline comparison, performance tests, stress tests, KPI report

---

## 📊 New Endpoints to Monitor

| Endpoint | Expected P95 | Business Impact |
|----------|--------------|-----------------|
| `POST /api/v1/matching/predict` | <5000ms | Core revenue driver |
| `POST /api/v1/matching/quick-wins` | <5000ms | 30% conversion rate |
| `POST /api/v1/matching/stretch-opportunities` | <5000ms | 15% conversion rate |
| `POST /api/v1/documents/bulk-analyze` | <10000ms | Document processing |
| `GET /api/v1/documents/user/me` | <150ms | User dashboard |

---

## 🎯 Performance Targets

- **Health Endpoint:** P95 ≤120ms ⏱️
- **Search:** P95 <200ms
- **AI Endpoints:** P95 <5000ms
- **Error Rate:** <1% 🎯
- **Uptime:** >99.9%

---

## 📈 Weekly Reports

**Every Monday 10am:**
```python
from observability.kpi_reporting import print_kpi_report
print_kpi_report(period_hours=168)  # Last 7 days
```

**Key Metrics for CEO:**
- New endpoint adoption (calls, users)
- Estimated MRR
- Application starts (conversion funnel)
- Revenue impact from credits consumed

---

## 🚨 Alert Triggers

| Alert | Threshold | Action |
|-------|-----------|--------|
| **P0** | Error rate >5% for >5min | Immediate - Check logs, rollback if needed |
| **P1** | P95 >300ms for >15min | 15min - Review latency dashboard |
| **P2** | Slow query detected | 1hour - Investigate query plan |

---

## 📚 Full Documentation

- **Complete Runbook:** `OPERATIONS_RUNBOOK.md`
- **Optimization Plan:** `POST_LAUNCH_OPTIMIZATION_PLAN.md`
- **Performance Report:** `EXECUTIVE_PERFORMANCE_REPORT.md`

---

**Need Help?** Escalate to Platform Engineering via #alerts Slack channel
