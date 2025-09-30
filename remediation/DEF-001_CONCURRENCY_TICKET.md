# DEF-001: Concurrent Request Handling Failure

**Severity:** 🔴 CRITICAL  
**Component:** Application Core / Database Connection Pool  
**Owner:** Platform Lead (App + DB) + SRE Support  
**Target:** Day 1-2  
**Status:** 🟡 IN PROGRESS

---

## 📋 PROBLEM STATEMENT

API exhibits 100% failure rate (0/10 successful) under light concurrency (5 concurrent users). Production system will fail immediately under any real user load, violating our 24/7 availability and <0.1% error rate SLO.

## 🔬 EVIDENCE

**Test Results:**
- Single requests: ✅ P95 44ms (excellent)
- 5 concurrent users: ❌ 0/10 successful (100% failure)
- Error symptoms: Connection pool exhaustion, timeout errors

**Trace IDs for Investigation:**
```
waf-1759239520, waf-1759239531, waf-1759239533
```

## 🎯 ACCEPTANCE CRITERIA (Launch Gate)

**Performance & Scale Gate:**
- [ ] **Sustain 50 RPS for 15 minutes** with:
  - Error rate: **<0.1%** (target: 0%)
  - P95 latency: **≤120ms** (current: 44ms single request)
  - P99 latency: **≤200ms**
- [ ] **Zero connection pool exhaustion events**
- [ ] **Autoscaling rules verified and tested**
- [ ] **Load shedding guardrails in place** (graceful degradation >80% capacity)

## 🛠️ FIX PLAN

### Phase 1: Diagnosis (2 hours)
```bash
# 1. Check current pool configuration
grep -r "pool_size\|max_overflow\|pool_timeout" config/

# 2. Monitor during load test
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
psql -c "SELECT max_conn, used FROM pg_stat_database WHERE datname = current_database();"

# 3. Check SQLAlchemy pool stats
# Add to middleware:
from sqlalchemy import event
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.info(f"Pool size: {engine.pool.size()}, Overflow: {engine.pool.overflow()}")
```

### Phase 2: Database Pool Tuning (4 hours)

**Current Config (Suspected):**
```python
# Default SQLAlchemy settings (likely too conservative)
pool_size = 5          # Too low for production
max_overflow = 10      # Too low for concurrent load
pool_timeout = 30      # May need adjustment
pool_recycle = 3600    # May cause connection staleness
```

**Recommended Production Config:**
```python
# config/settings.py
DATABASE_CONFIG = {
    "pool_size": 20,              # Base pool (20 connections)
    "max_overflow": 30,           # Up to 50 total connections
    "pool_timeout": 10,           # Fail fast, don't queue
    "pool_recycle": 1800,         # Recycle every 30 min
    "pool_pre_ping": True,        # Verify connection health
    "echo_pool": True,            # Log pool events (debug mode)
}

# Apply to engine
from sqlalchemy import create_engine
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_CONFIG["pool_size"],
    max_overflow=DATABASE_CONFIG["max_overflow"],
    pool_timeout=DATABASE_CONFIG["pool_timeout"],
    pool_recycle=DATABASE_CONFIG["pool_recycle"],
    pool_pre_ping=DATABASE_CONFIG["pool_pre_ping"],
    echo_pool=DATABASE_CONFIG["echo_pool"]
)
```

**PostgreSQL Server Limits:**
```sql
-- Check and increase max_connections if needed
SHOW max_connections;  -- Should be >= 100 for production
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
```

### Phase 3: Load Shedding Guardrails (2 hours)

**Circuit Breaker Pattern:**
```python
# middleware/load_shedding.py
from fastapi import Request, HTTPException
import asyncio

class LoadSheddingMiddleware:
    def __init__(self, max_concurrent_requests: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.active_requests = 0
    
    async def __call__(self, request: Request, call_next):
        if not await self.semaphore.acquire(timeout=1.0):
            # Load shedding: reject at 80% capacity
            raise HTTPException(
                status_code=503,
                detail="Service at capacity, please retry",
                headers={"Retry-After": "5"}
            )
        
        try:
            self.active_requests += 1
            response = await call_next(request)
            return response
        finally:
            self.active_requests -= 1
            self.semaphore.release()

# Add to main.py
app.add_middleware(LoadSheddingMiddleware, max_concurrent_requests=100)
```

**Connection Pool Health Check:**
```python
# Add to health endpoint
@router.get("/health")
async def health_check():
    pool_status = {
        "size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "total": engine.pool.size() + engine.pool.overflow()
    }
    
    # Red flag if >80% utilization
    utilization = (pool_status["total"] - pool_status["checked_in"]) / pool_status["total"]
    
    return {
        "status": "healthy" if utilization < 0.8 else "degraded",
        "pool": pool_status,
        "utilization_pct": utilization * 100
    }
```

### Phase 4: Testing & Validation (3 hours)

**Load Test Profile:**
```bash
# Install load testing tool
pip install locust

# locustfile.py
from locust import HttpUser, task, between

class ScholarshipUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Authenticate
        response = self.client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        self.token = response.json()["access_token"]
        self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def search_scholarships(self):
        self.client.get("/api/v1/search?q=engineering")
    
    @task(2)
    def list_scholarships(self):
        self.client.get("/api/v1/scholarships")
    
    @task(1)
    def check_eligibility(self):
        self.client.post("/api/v1/eligibility/check", json={
            "user_profile": {"gpa": 3.5, "major": "CS"},
            "scholarship_id": "sch_001"
        })

# Run load test: 50 RPS for 15 minutes
locust -f locustfile.py --headless -u 50 -r 10 --run-time 15m --host https://scholarship-api-jamarrlmayes.replit.app
```

**Success Criteria Validation:**
```python
# Automated validation script
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

def load_test_validation():
    results = []
    start_time = time.time()
    
    # 50 RPS for 15 minutes = 45,000 requests
    def make_request(i):
        try:
            response = requests.get(
                "https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=test",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            return {
                "success": response.status_code == 200,
                "latency": response.elapsed.total_seconds() * 1000,
                "status": response.status_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        for _ in range(900):  # 15 minutes worth
            batch = list(executor.map(make_request, range(50)))
            results.extend(batch)
            time.sleep(1)  # 1 second between batches = 50 RPS
    
    # Calculate metrics
    successes = [r for r in results if r.get("success")]
    latencies = [r["latency"] for r in successes if "latency" in r]
    
    error_rate = (1 - len(successes) / len(results)) * 100
    p95 = statistics.quantiles(latencies, n=20)[18] if latencies else 0
    p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies) if latencies else 0
    
    print(f"Error Rate: {error_rate:.3f}% (Target: <0.1%)")
    print(f"P95 Latency: {p95:.0f}ms (Target: ≤120ms)")
    print(f"P99 Latency: {p99:.0f}ms (Target: ≤200ms)")
    
    # Launch gate validation
    assert error_rate < 0.1, f"FAIL: Error rate {error_rate}% exceeds 0.1%"
    assert p95 <= 120, f"FAIL: P95 {p95}ms exceeds 120ms"
    assert p99 <= 200, f"FAIL: P99 {p99}ms exceeds 200ms"
    
    print("✅ ALL LAUNCH GATES PASSED")
```

## 📊 MONITORING & VALIDATION

**Metrics to Track:**
- `database_pool_size` (gauge)
- `database_pool_overflow` (gauge)
- `database_pool_checkedin` (gauge)
- `database_connection_errors` (counter)
- `request_concurrency` (histogram)
- `load_shedding_rejections` (counter)

**Alerts:**
```yaml
# alerts/connection_pool.yml
- alert: DatabasePoolExhaustion
  expr: (database_pool_size + database_pool_overflow - database_pool_checkedin) / (database_pool_size + database_pool_overflow) > 0.8
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool >80% utilized"
    runbook: "https://runbooks.scholarshipai.com/database-pool-exhaustion"
```

## 🔄 ROLLBACK PLAN

If performance degrades:
1. Revert pool size changes: `pool_size=5, max_overflow=10`
2. Disable load shedding middleware
3. Enable maintenance mode (503 responses)
4. Investigate with increased logging

## ✅ VERIFICATION CHECKLIST

- [ ] Database pool configuration updated and tested
- [ ] PostgreSQL max_connections increased to 200
- [ ] Load shedding middleware implemented
- [ ] Circuit breaker patterns in place
- [ ] 50 RPS load test successful (15 min, <0.1% error)
- [ ] P95 latency ≤120ms under load
- [ ] Zero pool exhaustion events
- [ ] Autoscaling rules verified
- [ ] Monitoring dashboards updated
- [ ] Alerts configured and tested
- [ ] Runbook documented

## 📁 ARTIFACTS

- [ ] Load test results (Locust HTML report)
- [ ] Pool metrics dashboard screenshot
- [ ] Before/after performance comparison
- [ ] Runbook: Database Pool Exhaustion

---

**ETA:** Day 1-2 (11 hours total)  
**Risk:** Medium (requires careful tuning, testing)  
**Dependencies:** None (can start immediately)
