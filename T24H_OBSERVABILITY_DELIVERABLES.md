# T+24H OBSERVABILITY DELIVERABLES
**DRI:** Observability Lead  
**Deadline:** 2025-10-05 13:46 UTC (24 hours from soft launch)  
**Review:** Recorded walkthrough with CEO  
**Status:** 🔴 PENDING - All items required before exposure expansion

---

## 📋 DELIVERABLE CHECKLIST

### 1️⃣ Auth Dashboard (PRIORITY: CRITICAL)
**Status:** 🔴 NOT STARTED

**Requirements:**
- [ ] 2xx/4xx/5xx breakdown by endpoint
  - Visualize: `/api/v1/auth/login`, `/api/v1/auth/check`, `/api/v1/auth/logout`
  - Track success rate trend over time
- [ ] P50/P95 latency per endpoint
  - Alert if P95 >300ms (stop-loss trigger)
  - Baseline: Current P95 ~50ms
- [ ] Token issuance rate & error rate
  - Track JWT generation rate
  - Monitor token validation failures
- [ ] Login failure breakdown
  - Invalid credentials (expected)
  - WAF blocks (investigate if >0)
  - Rate limit hits (investigate if frequent)

**Data Sources:**
- Structured logs: `grep "REQUEST_LOG:" /tmp/logs/FastAPI_Server_*.log | jq 'select(.path | startswith("/api/v1/auth"))'`
- Prometheus metrics: `http://localhost:5000/metrics`
- Specific metrics: `http_requests_total`, `http_request_duration_seconds`

**Dashboard Tool Options:**
- Grafana (recommended - pre-built Prometheus datasource)
- Custom HTML dashboard with Chart.js
- Deployment console with custom queries

**Acceptance Criteria:**
- ✅ Real-time data flowing from logs/metrics
- ✅ Historical trend (last 24 hours visible)
- ✅ Alerts configured for P95 >300ms and 5xx >1%
- ✅ Refreshes automatically (≤1 minute lag)

---

### 2️⃣ WAF Dashboard (PRIORITY: CRITICAL)
**Status:** 🔴 NOT STARTED

**Requirements:**
- [ ] Blocks by rule ID
  - `WAF_AUTH_001`: Missing Authorization header
  - `WAF_SQLI_001`: SQL injection attempt
  - `WAF_XSS_001`: XSS attempt
  - `WAF_RATE_001`: Rate limit exceeded
- [ ] Blocks by endpoint
  - Identify which endpoints trigger most blocks
  - Flag unexpected patterns (e.g., health endpoint blocked)
- [ ] False positive review queue
  - List of blocked requests for manual review
  - Filter: Exclude known patterns (no token = expected)
- [ ] Top offending IPs/ASNs
  - Track repeat offenders
  - Integration opportunity: Auto-ban after N blocks
- [ ] Allowlist hit rate
  - Track auth endpoint bypass rate
  - Confirm 5 endpoints exempted: `/api/v1/auth/login`, `/login-simple`, `/logout`, `/check`, `/launch/commercialization/api-keys`

**Data Sources:**
- Structured logs: `jq 'select(.waf_rule != null)'`
- WAF middleware logs: `grep "WAF:" /tmp/logs/FastAPI_Server_*.log`

**Dashboard Panels:**
1. **Blocks by Rule (Pie Chart)**
2. **Blocks Over Time (Line Graph)**
3. **Top 10 Blocked IPs (Table)**
4. **Auth Endpoint Bypass Rate (Gauge)**
5. **False Positive Queue (Table with pagination)**

**Acceptance Criteria:**
- ✅ All WAF events captured and visualized
- ✅ False positive queue actionable (with request details)
- ✅ Alerts for unusual spike in blocks (>100/hour)

---

### 3️⃣ Infra Dashboard (PRIORITY: HIGH)
**Status:** 🔴 NOT STARTED

**Requirements:**
- [ ] Uptime percentage
  - Track: Last hour, 24h, 7d
  - Target: 99.9% (soft launch SLO)
- [ ] CPU utilization
  - Current % usage
  - Alert at >70%
  - Trend graph (last 24h)
- [ ] Memory utilization
  - Current % free
  - Alert at <30% free
  - Track for memory leaks
- [ ] Container restarts
  - Count: Last 24h
  - Alert if >3 restarts/hour
- [ ] P50/P95/P99 latency (all endpoints)
  - Compare to baseline: P50=18.9ms, P95=~50ms
  - Alert if P95 >300ms (stop-loss)
- [ ] Error rates (4xx, 5xx separately)
  - Track 4xx: Client errors (auth failures, not found)
  - Track 5xx: Server errors (bugs, DB issues)
  - Alert if 5xx >1% (stop-loss)

**Data Sources:**
- Deployment console: CPU, memory, restarts
- Prometheus metrics: `process_cpu_seconds_total`, `process_resident_memory_bytes`
- Structured logs: Latency from `latency_ms` field
- HTTP metrics: `http_requests_total{status_code=~"5.."}`

**Dashboard Panels:**
1. **Uptime (Gauge)** - 99.9% target
2. **CPU & Memory (Dual-axis line graph)**
3. **Latency Percentiles (Multi-line graph)** - P50/P95/P99
4. **Error Rate by Type (Stacked area chart)** - 4xx vs 5xx
5. **Container Health (Status indicator + restart count)**

**Acceptance Criteria:**
- ✅ All metrics from deployment console integrated
- ✅ Alerts configured per CEO thresholds
- ✅ Real-time data (≤30s refresh)

---

### 4️⃣ Synthetic Monitors (PRIORITY: CRITICAL)
**Status:** 🔴 NOT STARTED

**Requirements:**
- [ ] **Monitor 1: Health Check**
  - Endpoint: `GET http://localhost:5000/health`
  - Frequency: Every 30 seconds
  - Expected: 200 status, response <50ms
  - Alert: If down >1 minute
  
- [ ] **Monitor 2: Login Endpoint**
  - Endpoint: `POST http://localhost:5000/api/v1/auth/login-simple`
  - Payload: `{"username": "smoke_test_user", "password": "<generated>"}`
  - Frequency: Every 5 minutes
  - Expected: 200 status with JWT token
  - Alert: If success rate <95% over 5 minutes
  
- [ ] **Monitor 3: Authenticated Search**
  - Endpoint: `GET http://localhost:5000/api/v1/search?query=test`
  - Headers: `Authorization: Bearer <token_from_monitor_2>`
  - Frequency: Every 5 minutes
  - Expected: 200 status, results returned
  - Alert: If P95 >300ms or errors >1%
  
- [ ] **Monitor 4: Authenticated Listing**
  - Endpoint: `GET http://localhost:5000/api/v1/scholarships?limit=5`
  - Headers: `Authorization: Bearer <token_from_monitor_2>`
  - Frequency: Every 5 minutes
  - Expected: 200 status, 5 scholarships returned
  - Alert: If P95 >300ms or errors >1%

**Implementation Options:**
1. **Custom Script** (Python/Bash)
   - Pros: Full control, easy to iterate
   - Cons: Need to implement alerting
2. **External Service** (UptimeRobot, Pingdom)
   - Pros: Built-in alerting, SMS/email
   - Cons: Requires external account
3. **Prometheus Blackbox Exporter**
   - Pros: Integrates with existing stack
   - Cons: Additional setup required

**Recommended:** Custom Python script + Slack webhook for alerts

**Alert Routing:**
- Slack channel: `#launch-alerts`
- Email: `on-call@company.com`
- Escalation: Page CEO if critical alert unacknowledged for 10 minutes

**Acceptance Criteria:**
- ✅ All 4 monitors running continuously
- ✅ Alerts tested and routing correctly
- ✅ Historical data retained (last 7 days minimum)
- ✅ Dashboard showing current status of all monitors

---

### 5️⃣ Test Suite Remediation (PRIORITY: MEDIUM)
**Status:** 🔴 NOT STARTED

**Current State:** 8/13 tests pass (61.5%)  
**Target:** 12/13+ tests pass (92%+)

**Root Cause of Failures:**
- 5 tests require authentication
- No test credentials seeded in production database
- Production auth locked down (as intended)

**Remediation Steps:**

**Step 1: Seed Test Account (ETA: 30 minutes)**
```sql
-- Connect to production database
-- DO NOT execute this now - wait for proper timing

INSERT INTO users (username, email, password_hash, role, scopes, created_at, expires_at)
VALUES (
  'smoke_test_user',
  'smoke+test@company.com',
  '<bcrypt_hash_of_secure_password>',
  'read_only',
  ARRAY['search:read', 'scholarships:read'],
  NOW(),
  NOW() + INTERVAL '48 hours'
);

-- Generate API key
INSERT INTO api_keys (user_id, key_hash, name, scopes, created_at, expires_at)
VALUES (
  (SELECT id FROM users WHERE username = 'smoke_test_user'),
  '<hash_of_generated_key>',
  'Smoke Test Key - T+24h Validation',
  ARRAY['search:read', 'scholarships:read'],
  NOW(),
  NOW() + INTERVAL '48 hours'
);
```

**Step 2: Update Test Suite (ETA: 15 minutes)**
- Add `SMOKE_TEST_TOKEN` environment variable
- Update failing tests to use token:
  - Test 2.1: Search - Basic Query
  - Test 2.2: Search - With Filters
  - Test 3.7: Scholarship Listing
  - Test 3.8: Individual Scholarship

**Step 3: Run Validation (ETA: 5 minutes)**
```bash
# Run updated test suite
/tmp/run_13_test_suite.sh

# Expected: 12/13 or 13/13 pass
# Document: Which test still fails (if any)
```

**Step 4: Credential Rotation (ETA: 10 minutes)**
```sql
-- After validation complete, rotate credentials
UPDATE users SET expires_at = NOW() WHERE username = 'smoke_test_user';
UPDATE api_keys SET expires_at = NOW() WHERE name LIKE 'Smoke Test%';

-- Audit log entry
INSERT INTO audit_log (action, entity, details, timestamp)
VALUES (
  'CREDENTIAL_ROTATION',
  'smoke_test_user',
  'Test account disabled after T+24h validation',
  NOW()
);
```

**Total ETA:** 60 minutes

**Acceptance Criteria:**
- ✅ Test account seeded with least privilege
- ✅ 13-test suite at 12/13+ pass rate
- ✅ Credentials rotated/disabled post-validation
- ✅ Audit trail documented

---

## 📊 T+24H REVIEW AGENDA

**Format:** Recorded walkthrough (30-45 minutes)  
**Attendees:** CEO, Observability Lead, On-Call Engineer

**Agenda:**
1. **Auth Dashboard Walkthrough (10 min)**
   - Show 2xx/4xx/5xx breakdown
   - Demonstrate P95 latency tracking
   - Review any anomalies in last 24h
   
2. **WAF Dashboard Walkthrough (10 min)**
   - Review blocks by rule
   - Discuss false positives (if any)
   - Show allowlist effectiveness
   
3. **Infra Dashboard Walkthrough (10 min)**
   - Present uptime metrics
   - Show resource utilization trends
   - Highlight any container restarts
   
4. **Synthetic Monitors Demo (5 min)**
   - Show current status of all 4 monitors
   - Demonstrate alert firing (if possible)
   - Review historical uptime
   
5. **Test Suite Results (5 min)**
   - Present before/after pass rates
   - Explain any remaining failures
   - Confirm credential rotation

6. **SLO Review (5 min)**
   - Uptime: Target 99.9%
   - P95 latency: Target <120ms for core reads
   - Error budget: Confirm intact
   
7. **Go/No-Go Decision (5 min)**
   - All deliverables complete: Continue exposure
   - Any item missing: Pause until resolved

---

## 🛠️ IMPLEMENTATION GUIDE

### Quick Start: Auth Dashboard (Grafana)

**Prerequisites:**
```bash
# Install Grafana (if not already)
docker run -d -p 3000:3000 grafana/grafana

# Add Prometheus datasource
# Point to: http://localhost:5000/metrics
```

**Dashboard JSON Template:**
```json
{
  "dashboard": {
    "title": "Auth Dashboard - Soft Launch",
    "panels": [
      {
        "title": "Auth Success Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{path=~\"/api/v1/auth.*\", status_code=\"200\"}[5m])"
          }
        ]
      },
      {
        "title": "Auth P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path=~\"/api/v1/auth.*\"}[5m]))"
          }
        ]
      }
    ]
  }
}
```

**Alternative: Simple HTML Dashboard**
- Use `/metrics` endpoint directly
- Parse Prometheus format with JavaScript
- Render with Chart.js or D3.js
- Host on `/dashboard` route

---

## 🚨 BLOCKER RESOLUTION

**If Dashboards Not Ready at T+24h:**

**Option 1: Request Extension (Not Recommended)**
- Requires CEO approval
- Pauses exposure expansion
- Sets bad precedent

**Option 2: Simplified Dashboards (Acceptable)**
- Use deployment console as primary view
- Supplement with structured log queries
- Promise full dashboards at T+48h
- Must still meet SLO requirements

**Option 3: External Tooling (Fast Path)**
- Use existing Grafana Cloud or Datadog
- Import metrics via remote_write
- Leverage pre-built templates
- Fastest to deploy

---

## ✅ ACCEPTANCE CRITERIA SUMMARY

**All 5 deliverables must be:**
- ✅ **Complete**: Functional and populated with data
- ✅ **Accurate**: Reflects actual system state
- ✅ **Actionable**: Alerts configured and tested
- ✅ **Documented**: Runbook for each dashboard
- ✅ **Reviewed**: CEO walkthrough recorded

**If ANY criteria unmet:** Pause exposure expansion until resolved

---

## 📞 SUPPORT & ESCALATION

**DRI Contact:** Observability Lead  
**Backup:** On-Call Engineer  
**CEO Updates:** Every 6 hours until T+24h complete  
**Slack Channel:** `#launch-observability`

**Progress Tracking:**
- Update this document with ✅ as items complete
- Post screenshots to Slack channel
- Flag blockers immediately (don't wait for T+24h)

---

**DEADLINE: 2025-10-05 13:46 UTC**  
**TIME REMAINING: ~24 hours**

*Failure to deliver on time will pause soft launch expansion per CEO directive.*
