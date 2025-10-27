# Scholarship API - Operations Runbook
**Last Updated:** October 27, 2025  
**Purpose:** Daily operations, performance monitoring, KPI tracking, incident response  

---

## Quick Reference

| Task | Command/Endpoint | Frequency |
|------|-----------------|-----------|
| **Latency Dashboard** | `GET /api/v1/observability/latency-dashboard` | Every 4 hours |
| **KPI Report** | `GET /api/v1/observability/kpi-report` | Daily |
| **Health Summary** | `GET /api/v1/observability/health-summary` | Every hour |
| **Stress Test** | `pytest tests/stress_test_hot_paths.py -m stress` | Before releases |
| **Optimization Plan** | `./scripts/execute_optimization_plan.sh` | As needed |

---

## 1. Daily Operations

### Morning Routine (Every Day - 9am)

**1. Check Health Summary**
```bash
curl -s https://your-api.replit.app/api/v1/observability/health-summary | jq
```

**Expected Response:**
```json
{
  "status": "healthy",
  "error_rate": 0.0,
  "p95_overall": 120.0,
  "p95_compliance": true,
  "slow_queries_count": 0
}
```

**Action Items:**
- ✅ `status: "healthy"` → All good
- ⚠️ `status: "degraded"` → Check latency dashboard
- 🔴 `error_rate > 1.0` → Immediate investigation required

---

**2. Review Latency Dashboard**
```bash
curl -s https://your-api.replit.app/api/v1/observability/latency-dashboard | jq
```

or using Python:
```python
from observability.latency_dashboard import print_daily_ops_snapshot
print_daily_ops_snapshot()
```

**Expected Output:**
```
================================================================================
📊 LATENCY DASHBOARD SNAPSHOT
================================================================================

OVERALL PERFORMANCE:
  P50: 85.0ms
  P95: 120.0ms
  P99: 180.0ms
  Error Rate: 0.05% ✅

ENDPOINT GROUPS:
  health               ✅
    P50:   50.0ms  P95:   90.0ms  P99:  120.0ms
  search               ✅
    P50:   80.0ms  P95:  150.0ms  P99:  200.0ms
  predictive_matching  ✅
    P50:  2000.0ms  P95: 3500.0ms  P99: 4500.0ms
  ...

✅ NO SLOW QUERIES DETECTED
```

**Action Items:**
- P95 >120ms for health endpoints → Run optimization plan
- Slow queries detected → Review database query plans
- Predictive matching P95 >5000ms → Investigate AI service

---

### Afternoon Check (Every Day - 2pm)

**3. Generate KPI Report**
```bash
curl -s https://your-api.replit.app/api/v1/observability/kpi-report?period_hours=24 | jq
```

or using Python:
```python
from observability.kpi_reporting import print_kpi_report
print_kpi_report(period_hours=24)
```

**Expected Output:**
```
================================================================================
📈 KPI REPORT: Usage & Conversion
Period: last_24_hours
================================================================================

🎯 NEW ENDPOINT USAGE:
  quick_wins               
    Calls:    450  Success:    445  Error:   1.1%
    Latency P95: 2800.0ms

  stretch_opportunities    
    Calls:    320  Success:    318  Error:   0.6%
    Latency P95: 3200.0ms

💼 CONVERSIONS:
  Estimated Application Starts: 165

💰 MONETIZATION:
  Credits Consumed: 2840
  Revenue Impact: $227.20

📊 BUSINESS IMPACT:
  New Endpoint Calls: 850
  Estimated Active Users: 170
  Est. MRR: $6,816.00
  Avg Revenue/User: $1.34
```

**Action Items:**
- New endpoint adoption growing → Document success
- Conversion rate <10% → Review UX funnel
- Revenue impact tracking → Report to CEO weekly

---

### Evening Validation (Every Day - 6pm)

**4. Check Metrics Endpoint**
```bash
curl -s https://your-api.replit.app/metrics | grep "active_scholarships_total"
```

**Expected:** Should show current scholarship count (e.g., 15)

**5. Review Error Logs**
```bash
# Check for 5xx errors in last 4 hours
curl -s https://your-api.replit.app/metrics | grep "http_requests_total.*5.."
```

**Action:** If >10 errors, investigate root cause

---

## 2. Release & Validation

### Pre-Release Checklist

**Before Every Release:**

1. ✅ Run Performance Tests
```bash
pytest tests/test_performance.py -m performance -v
```

**Pass Criteria:**
- Health endpoint P95 ≤120ms
- Search endpoint P95 <200ms
- Metrics endpoint P95 ≤150ms
- Zero auth regressions

---

2. ✅ Run Stress Tests
```bash
pytest tests/stress_test_hot_paths.py -m stress -v
```

**Pass Criteria:**
- Predictive matching: Error rate <5%, P95 <5000ms
- Document bulk analyze: Error rate <10%
- Quick wins / Stretch: Error rate <5%
- **Zero auth regressions** (auth_failure_rate = 0.0%)

---

3. ✅ Execute 48-Hour Optimization Plan (if needed)
```bash
./scripts/execute_optimization_plan.sh
```

**Generated Files:**
- `baseline_before.txt` - Pre-optimization latency
- `baseline_after.txt` - Post-optimization latency
- `performance_test_results.txt` - Test results
- `stress_test_results.txt` - Stress test results
- `kpi_report.txt` - Business impact

**Validation:**
- Compare P95 in before/after baselines
- Target: ≥10% improvement
- No auth regressions in stress tests
- Error rate remains <1%

---

4. ✅ Verify Deployment Config
```bash
# Check deployment config
cat .replit | grep -A 10 "deployment"
```

**Expected:**
```toml
deployment_target = "autoscale"
run = ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000}"]
```

---

### Post-Release Validation

**Immediately After Release:**

1. **Health Check** (within 2 minutes)
```bash
curl https://your-api.replit.app/api/v1/health
```
Expected: `200 OK` with `{"status": "healthy"}`

---

2. **Smoke Tests** (within 5 minutes)
```bash
# Test public endpoints
curl https://your-api.replit.app/
curl https://your-api.replit.app/metrics
curl https://your-api.replit.app/api/v1/health/deep

# Test authenticated endpoint (requires JWT)
curl -H "Authorization: Bearer <token>" \
  https://your-api.replit.app/api/v1/matching/quick-wins \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_profile": {...}, "limit": 5}'
```

---

3. **Monitor Error Rate** (first 30 minutes)
```bash
# Check every 5 minutes
watch -n 300 'curl -s https://your-api.replit.app/api/v1/observability/health-summary | jq ".error_rate"'
```

**Rollback Trigger:** Error rate >3% for >5 minutes

---

## 3. KPI Reporting & Business Metrics

### Weekly KPI Report (Every Monday - 10am)

**Generate Weekly Report:**
```python
from observability.kpi_reporting import get_kpi_report

# Last 7 days
report = get_kpi_report(period_hours=168)

# Key metrics to extract
total_endpoint_calls = sum(ep["total_calls"] for ep in report["new_endpoints"].values())
estimated_mrr = report["business_impact"]["revenue_metrics"]["estimated_monthly_recurring_revenue"]
active_users = report["business_impact"]["user_engagement"]["estimated_active_users"]

print(f"Weekly Summary:")
print(f"- New Endpoint Calls: {total_endpoint_calls}")
print(f"- Active Users: {active_users}")
print(f"- Est. MRR: ${estimated_mrr:.2f}")
```

---

### Monthly CEO Report (First Monday of Month)

**Metrics to Include:**

1. **Performance:**
   - P50/P95/P99 trend (month-over-month)
   - Uptime percentage
   - Error rate

2. **Usage:**
   - Total API calls
   - Active users (estimated)
   - Top endpoints by volume

3. **Monetization:**
   - Total credits consumed
   - Revenue impact
   - MRR growth rate
   - Avg revenue per user

4. **Conversions:**
   - Quick-wins usage → Application starts
   - Stretch opportunities usage
   - Document uploads → Profile completions

**Report Template:**
```markdown
# Scholarship API - Monthly Performance Report
**Month:** [Month Year]

## Executive Summary
- Uptime: 99.95%
- P95 Latency: 118ms (target: ≤120ms) ✅
- Error Rate: 0.08% (target: <1%) ✅
- Active Users: 2,450
- MRR: $32,680 (+18% MoM)

## Key Highlights
- Quick-wins endpoint: 12,500 calls (+25% MoM)
- Application starts: 3,750 (30% conversion)
- Revenue impact: $2,614/month

## Action Items
- [ ] Provision managed Redis (horizontal scaling)
- [ ] Optimize AI endpoints (P95 currently 3.8s, target <3.5s)
```

---

## 4. Incident Response

### Hot-Path Stress Testing (Before Major Releases)

**Run Canary Tests:**
```bash
pytest tests/stress_test_hot_paths.py -m stress -v -s
```

**Critical Tests:**

1. **POST /api/v1/matching/predict** (100 concurrent requests)
   - Expected: P95 <5000ms, error rate <5%
   - Auth regression check: 0 failures

2. **POST /api/v1/documents/bulk-analyze** (50 concurrent requests)
   - Expected: P95 <10000ms, error rate <10%
   - Auth regression check: 0 failures

3. **POST /api/v1/matching/quick-wins** (100 concurrent requests)
   - Expected: P95 <5000ms, error rate <5%

4. **POST /api/v1/matching/stretch-opportunities** (100 concurrent requests)
   - Expected: P95 <5000ms, error rate <5%

---

### Incident Escalation Matrix

| Severity | Trigger | Response Time | Actions |
|----------|---------|---------------|---------|
| **P0** | Error rate >5% for >5min | Immediate | 1. Check logs<br>2. Rollback if needed<br>3. Page on-call |
| **P1** | P95 >300ms for >15min | 15 minutes | 1. Review latency dashboard<br>2. Check DB slow queries<br>3. Review recent deployments |
| **P2** | Slow query detected | 1 hour | 1. Investigate query plan<br>2. Add index if needed<br>3. Optimize query |
| **P3** | Auth failures >10/hour | 4 hours | 1. Check JWT config<br>2. Review auth middleware logs<br>3. Verify secret rotation |

---

### Rollback Procedure

**When to Rollback:**
- Error rate >3% sustained for >5 minutes
- P95 >300ms (2x baseline) sustained for >15 minutes
- Auth regression detected (auth failures >1%)
- Database connection failures

**Rollback Steps:**
```bash
# 1. Revert to previous deployment
git log --oneline -10  # Find last stable commit
git checkout <commit-hash>

# 2. Redeploy
# (Use Replit UI to trigger deployment)

# 3. Verify health
curl https://your-api.replit.app/api/v1/health

# 4. Monitor for 15 minutes
watch -n 60 'curl -s https://your-api.replit.app/api/v1/observability/health-summary | jq'

# 5. Document incident
echo "Incident: [Date] - [Description]" >> INCIDENT_LOG.md
```

---

## 5. Performance Optimization Workflow

### When to Optimize

**Triggers:**
- P95 >120ms for health endpoints (sustained >24 hours)
- P95 >200ms for search endpoints
- Slow queries detected in dashboard
- Error rate >0.5% (sustained)

---

### Optimization Sprint (48 Hours)

**See:** `POST_LAUNCH_OPTIMIZATION_PLAN.md` for full details

**Quick Steps:**
1. Capture baseline (`baseline_before.txt`)
2. Enable result caching (Redis)
3. Reorder middleware (rate limit first)
4. Add prepared statements (frequent queries)
5. Create composite indexes
6. Capture post-optimization baseline
7. Compare results
8. Run stress tests
9. Deploy if successful

**Expected Improvements:**
- Result caching: 15-20ms reduction
- Middleware reordering: 5-10ms reduction
- Prepared statements: 5-15ms reduction
- **Total:** 25-45ms reduction (17-31%)

---

## 6. Alerting & Monitoring

### Prometheus Alerts

**Configured Alerts:** (See `observability/alerting-rules.yml`)

1. **PerformanceRegression** (Warning)
   - Trigger: P95 >150ms for >5 minutes
   - Action: Review latency dashboard

2. **TailLatencyDegradation** (Warning)
   - Trigger: P99 >250ms for >5 minutes
   - Action: Check slow queries

3. **HighErrorRate** (Critical)
   - Trigger: Error rate >1% for >2 minutes
   - Action: Immediate investigation

---

### Dashboard URLs

- **Latency Dashboard:** `/api/v1/observability/latency-dashboard`
- **KPI Report:** `/api/v1/observability/kpi-report`
- **Health Summary:** `/api/v1/observability/health-summary`
- **Prometheus Metrics:** `/metrics`
- **Infrastructure Dashboard:** `/api/v1/observability/dashboards/infrastructure`

---

## 7. Contacts & Escalation

**On-Call Rotation:** (Update this section)
- Week 1: [Name] - [Contact]
- Week 2: [Name] - [Contact]

**Escalation:**
- P0/P1 Incidents → Page on-call immediately
- P2 Incidents → Slack #alerts channel
- P3 Incidents → Create GitHub issue

---

## Appendix A: Common Issues & Solutions

### Issue: P95 Latency Spike

**Symptoms:** P95 >150ms sustained

**Diagnosis:**
1. Check latency dashboard for endpoint group causing spike
2. Review slow queries
3. Check database connection pool

**Solutions:**
- Add database index for slow queries
- Enable result caching
- Increase connection pool size

---

### Issue: Auth Failures

**Symptoms:** 401 errors on authenticated endpoints

**Diagnosis:**
1. Check JWT secret configuration
2. Verify token expiration settings
3. Review middleware order

**Solutions:**
- Rotate JWT secrets if compromised
- Increase token expiration time
- Ensure auth middleware before WAF

---

### Issue: Slow AI Endpoints

**Symptoms:** Predictive matching P95 >5000ms

**Diagnosis:**
1. Check OpenAI API latency
2. Review analysis depth (quick vs deep)
3. Check scholarship dataset size

**Solutions:**
- Use "quick" analysis for hot paths
- Implement result caching for AI responses
- Reduce max_results for faster responses

---

**End of Operations Runbook**  
**For questions or updates, contact Platform Engineering**
