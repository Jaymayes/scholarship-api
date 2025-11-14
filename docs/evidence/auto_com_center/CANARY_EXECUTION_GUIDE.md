# auto_com_center Canary Execution Guide

**Application**: auto_com_center  
**APP_BASE_URL**: https://auto-com-center-jamarrlmayes.replit.app  
**CEO Directive**: Run NOW, re-run tomorrow 12 PM MST  
**Deadline**: Submit evidence by Nov 14, 2:00 PM MST  
**Created**: 2025-11-13T17:30:00Z MST  

---

## CEO Order: RUN CANARY NOW

> "Run it now. Start the 30‑minute/250 rps canary immediately. If it fails, you'll have tonight to remediate and a second verification window tomorrow before the 2:00 PM MST deadline."

---

## Execution Steps

### Step 1: Pre-Flight Checks (2 minutes)

```bash
# Verify service is running
curl https://auto-com-center-jamarrlmayes.replit.app/health
# Expected: {"status": "healthy"}

# Verify readiness (includes dependencies)
curl https://auto-com-center-jamarrlmayes.replit.app/readyz
# Expected: All checks pass

# Check current load (should be minimal)
curl https://auto-com-center-jamarrlmayes.replit.app/metrics | grep http_requests_total
```

### Step 2: Prepare k6 Canary Script (5 minutes)

**File**: `load-tests/canary_250rps_30min.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const p95Duration = new Trend('p95_duration');

export const options = {
  scenarios: {
    canary: {
      executor: 'constant-arrival-rate',
      rate: 250,
      timeUnit: '1s',
      duration: '30m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<120'], // CEO SLO: P95 ≤ 120ms
    'errors': ['rate<0.005'],            // CEO SLO: Error rate < 0.5%
    'http_req_failed': ['rate<0.005'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://auto-com-center-jamarrlmayes.replit.app';

export function setup() {
  console.log('🚀 Starting canary: 250 RPS for 30 minutes');
  console.log(`   Target: ${BASE_URL}`);
  console.log(`   SLOs: P95 ≤120ms, Error rate <0.5%`);
  return { startTime: Date.now() };
}

export default function () {
  // Simulate realistic message sending
  const payload = JSON.stringify({
    event_type: 'scholarship_viewed',
    user_id: `test_user_${__VU}_${__ITER}`,
    scholarship_id: `sch_${Math.floor(Math.random() * 100)}`,
    timestamp: new Date().toISOString(),
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.TEST_TOKEN}`,
    },
  };
  
  const response = http.post(`${BASE_URL}/api/v1/events`, payload, params);
  
  const success = check(response, {
    'status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'response time < 120ms': (r) => r.timings.duration < 120,
  });
  
  errorRate.add(!success);
  p95Duration.add(response.timings.duration);
  
  sleep(0.1);
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000 / 60;
  console.log(`\n✅ Canary completed: ${duration.toFixed(1)} minutes`);
}
```

### Step 3: Run Canary (30 minutes)

```bash
# Terminal 1: Run canary
cd auto-com-center
k6 run \
  --out json=results/canary_$(date +%Y%m%d_%H%M%S).json \
  --env BASE_URL=https://auto-com-center-jamarrlmayes.replit.app \
  --env TEST_TOKEN="${TEST_TOKEN}" \
  load-tests/canary_250rps_30min.js | tee results/canary_live_output.log

# Terminal 2: Watch logs for errors
tail -f /tmp/logs/auto_com_center_*.log | grep -E "ERROR|CRITICAL|WARN"

# Terminal 3: Monitor metrics
watch -n 5 'curl -s https://auto-com-center-jamarrlmayes.replit.app/metrics | grep -E "http_request_duration|error_rate"'
```

### Step 4: Capture Evidence (During canary)

**A) Take screenshots at T+5min, T+15min, T+25min**:
- Replit console (showing uptime, no restarts)
- Metrics dashboard (if available)
- Error logs (should be minimal)

**B) Record key metrics**:
```bash
# At T+30min (end of canary)
curl https://auto-com-center-jamarrlmayes.replit.app/metrics > results/canary_final_metrics.txt
curl https://auto-com-center-jamarrlmayes.replit.app/health > results/canary_final_health.json
```

### Step 5: Analyze Results (5 minutes)

```bash
# Parse k6 JSON output for CEO metrics
cat results/canary_*.json | jq '
  select(.type == "Point" and .metric == "http_req_duration") |
  .data.value
' | sort -n | awk '
  BEGIN { count = 0; sum = 0 }
  { values[count++] = $1; sum += $1 }
  END {
    p95_index = int(count * 0.95)
    p99_index = int(count * 0.99)
    print "P50:", values[int(count * 0.5)]
    print "P95:", values[p95_index]
    print "P99:", values[p99_index]
    print "Avg:", sum / count
  }
'

# Calculate error rate
cat results/canary_*.json | jq '
  select(.type == "Point" and .metric == "errors") |
  .data.value
' | awk '{ sum += $1; count++ } END { print "Error rate:", (sum/count)*100"%" }'
```

---

## Success Criteria (CEO SLOs)

**PASS Requirements**:
- ✅ P95 latency ≤ 120ms
- ✅ Error rate < 0.5%
- ✅ No service restarts during 30-minute window
- ✅ No CRITICAL errors in logs
- ✅ Health check remains green throughout

**FAIL Triggers**:
- ❌ P95 > 120ms sustained for >5 minutes
- ❌ Error rate ≥ 0.5%
- ❌ Service crashes or restarts
- ❌ Database connection pool exhaustion
- ❌ Memory leak (heap growth >50MB during test)

---

## Evidence Bundle Format

**File**: `docs/evidence/auto_com_center/CANARY_REPORT_[TIMESTAMP].md`

```markdown
# auto_com_center Canary Report

**Run Date**: 2025-11-13T[HH:MM:SS]Z
**Duration**: 30 minutes
**Load**: 250 RPS constant
**Status**: [PASS/FAIL]

## Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P95 Latency | ≤120ms | [X]ms | [✅/❌] |
| Error Rate | <0.5% | [X]% | [✅/❌] |
| Uptime | 100% | [X]% | [✅/❌] |
| Total Requests | 450,000 | [X] | [✅/❌] |

## Evidence

- k6 JSON output: `results/canary_[timestamp].json`
- Live output log: `results/canary_live_output.log`
- Screenshots: `results/screenshots/`
- Final metrics: `results/canary_final_metrics.txt`

## Recommendations

[If PASS]: Ready for production go-live
[If FAIL]: [Specific remediation steps]
```

---

## If Canary FAILS

1. **Immediately notify CEO** with failure summary
2. **Identify root cause** from logs/metrics
3. **Implement fix** tonight
4. **Re-run canary** tomorrow 12 PM MST

**Common Failure Modes**:
- Database connection pool exhaustion → Increase pool size
- Rate limiting too aggressive → Adjust limits
- Memory leak → Profile and fix
- External API timeout → Add circuit breaker

---

## Tomorrow's Re-Run (12 PM MST)

```bash
# Same command, fresh evidence
k6 run \
  --out json=results/canary_formal_$(date +%Y%m%d_%H%M%S).json \
  --env BASE_URL=https://auto-com-center-jamarrlmayes.replit.app \
  --env TEST_TOKEN="${TEST_TOKEN}" \
  load-tests/canary_250rps_30min.js
```

---

**DRI**: Messaging Lead  
**Support**: Agent3 (Program Integrator), SRE Lead  
**Escalation**: CEO if canary fails twice
