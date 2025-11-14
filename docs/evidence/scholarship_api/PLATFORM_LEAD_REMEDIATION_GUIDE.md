# Platform Lead Remediation Guide - scholarship_api Gate 0

**Owner**: Platform Lead  
**Deadline**: Nov 15, 10:00 AM MST  
**Duration**: 2-4 hours (infrastructure) + 15 min (validation)

## Current State

❌ **Load Test FAILED**: 92.1% error rate, P95 1,700ms  
❌ **Single instance deployment** (no autoscaling)  
❌ **No Redis** (in-memory rate limiting)  
❌ **No connection pooling**  
✅ **Code is production-ready** (JWT, JWKS, /readyz working)

## Required Infrastructure Changes

### 1. Deployment Configuration (30-60 min)

**Option A: Replit Autoscale** (Preferred)
```yaml
# .replit deployment config
[deployment]
deploymentTarget = "autoscale"

[deployment.autoscale]
minInstances = 2
maxInstances = 10

[deployment.autoscale.triggers]
cpu = { threshold = 70 }
memory = { threshold = 80 }
latency_p95 = { threshold = 100 }
error_rate = { threshold = 1 }

[deployment.health]
liveness = "/health"
readiness = "/readyz"
initialDelaySeconds = 10
periodSeconds = 5
timeoutSeconds = 3
```

**Option B: Reserved VM** (Fallback)
```yaml
[deployment]
deploymentTarget = "vm"

[deployment.vm]
reservedInstances = 3  # Fixed capacity
```

**Option C: Secondary Platform** (If Replit insufficient)
- AWS ECS/Fargate with Application Load Balancer
- Google Cloud Run (autoscaling)
- Fly.io (global edge deployment)

### 2. Connection Pooling (30 min)

**SQLAlchemy Pool Configuration** (already in code, verify settings)

File: `config/settings.py`
```python
# Verify these settings exist:
DATABASE_POOL_SIZE = 20  # connections per instance
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

**Alternative: PgBouncer** (if needed)
```ini
# pgbouncer.ini
[databases]
scholarship_api = host=<PGHOST> port=<PGPORT> dbname=<PGDATABASE>

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
reserve_pool_size = 5
reserve_pool_timeout = 3
```

### 3. Redis Provisioning (30-60 min)

**Required for**:
- Distributed rate limiting
- JWKS cache (optional optimization)
- Session storage (future)

**Provisioning**:
```bash
# Option 1: Replit Redis addon
replit-cli addons create redis --plan standard

# Option 2: External Redis (Upstash, Redis Labs)
# Set environment variable:
RATE_LIMIT_REDIS_URL=redis://user:pass@host:port/db
```

**Verification**:
```bash
curl https://scholarship-api.replit.app/readyz
# Should show redis: "healthy"
```

### 4. Uvicorn/FastAPI Tuning (15 min)

File: `main.py` (verify configuration)
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        workers=4,  # CPU cores * 2
        timeout_keep_alive=75,
        limit_concurrency=1000,
        backlog=2048,
        access_log=False,  # Use structured logging instead
    )
```

### 5. Circuit Breakers & Timeouts (30 min)

**Add Request Timeouts** (prevent queue buildup)

File: `middleware/timeout.py` (create if not exists)
```python
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=5.0  # 5s max per request
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"error": "Request timeout"}
            )
```

### 6. HTTP/2 & Keep-Alive (15 min)

**Enable in uvicorn**:
```python
uvicorn.run(
    # ... existing config ...
    http="h2",  # Enable HTTP/2
    timeout_keep_alive=75,  # Keep connections alive
)
```

**Verify**:
```bash
curl -I --http2 https://scholarship-api.replit.app/health
# Should see: HTTP/2 200
```

---

## Validation Checklist

### Pre-Flight Checks
- [ ] Autoscale config deployed (min 2, max 10 instances)
- [ ] Connection pool configured (20+ connections)
- [ ] Redis provisioned and healthy
- [ ] Uvicorn workers configured (4-8)
- [ ] Circuit breakers enabled
- [ ] Request timeouts set (5s)
- [ ] HTTP/2 enabled
- [ ] Health checks working (/health, /readyz)

### Load Test Execution

**Run k6 Gate 0 Test**:
```bash
# Install k6 (if not already)
wget https://github.com/grafana/k6/releases/download/v0.48.0/k6-v0.48.0-linux-amd64.tar.gz
tar -xzf k6-v0.48.0-linux-amd64.tar.gz

# Run test
./k6-v0.48.0-linux-amd64/k6 run \
  load-tests/gate0_canary.js \
  --summary-export=gate0_results_PASS.json \
  --out json=gate0_metrics.json

# Upload to k6 Cloud (optional)
k6 cloud load-tests/gate0_canary.js
```

**Success Criteria**:
- ✅ Error rate: <0.5% (target: <0.1%)
- ✅ P95 latency: ≤120ms (target: <100ms)
- ✅ P99 latency: ≤200ms
- ✅ Throughput: 250 RPS sustained for 10 minutes
- ✅ No dropped iterations
- ✅ No server restarts during test

### Post-Test Validation
- [ ] Check /readyz output:
  ```bash
  curl https://scholarship-api.replit.app/readyz | jq
  ```
  Expected:
  ```json
  {
    "status": "ready",
    "checks": {
      "database": {"status": "healthy"},
      "redis": {"status": "healthy"},
      "auth_jwks": {"status": "degraded"},  # OK until scholar_auth ready
      "configuration": {"status": "healthy"}
    }
  }
  ```

- [ ] Check metrics endpoint:
  ```bash
  curl https://scholarship-api.replit.app/metrics
  ```

- [ ] Verify autoscaling behavior:
  ```bash
  # Check instance count during load
  replit-cli deployments list
  # Should show 2-10 instances active during test
  ```

---

## Evidence Package

Collect and deliver to `docs/evidence/scholarship_api/`:

1. **Infrastructure Config**
   - `autoscale_config.yaml` (deployment settings)
   - `connection_pool_config.txt` (SQLAlchemy settings)
   - `redis_provision_confirmation.txt` (provisioning receipt)

2. **Load Test Results**
   - `gate0_results_PASS.json` (k6 summary)
   - `gate0_metrics.json` (full metrics)
   - `k6_cloud_run_url.txt` (if using k6 Cloud)

3. **Before/After Comparison**
   ```
   BEFORE (Nov 14):
   - Error rate: 92.1%
   - P95 latency: 1,700ms
   - Throughput: 63 RPS
   
   AFTER (Nov 15):
   - Error rate: <0.5%
   - P95 latency: <120ms
   - Throughput: 250+ RPS
   ```

4. **Health Check Output**
   - `readyz_output.json` (post-test snapshot)
   - `metrics_sample.txt` (Prometheus metrics)

5. **Autoscaling Evidence**
   - Instance count chart (min/max/current)
   - CPU/memory utilization graphs
   - Request queue depth

---

## Troubleshooting

### High Latency (P95 >120ms)
- Check database query performance (add indexes)
- Verify connection pool not exhausted
- Check for n+1 queries (use eager loading)
- Enable query logging temporarily

### High Error Rate (>0.5%)
- Check server logs for exceptions
- Verify database connectivity
- Check Redis connectivity
- Verify rate limiting not blocking legitimate requests

### Autoscaling Not Triggering
- Verify trigger thresholds (CPU, latency, errors)
- Check health check endpoints responding
- Verify metrics collection working

### Connection Pool Exhaustion
- Increase pool size (20 → 50)
- Check for connection leaks (ensure proper close)
- Add connection monitoring

---

## Timeline

| Time | Task | Duration |
|------|------|----------|
| Now | Start infrastructure migration | - |
| +1hr | Autoscale config deployed | 30-60 min |
| +2hr | Connection pool + Redis configured | 60 min |
| +3hr | Uvicorn tuning + timeouts | 45 min |
| +3.5hr | Pre-flight validation | 30 min |
| +4hr | Run k6 load test | 15 min |
| +4.5hr | Evidence collection | 30 min |
| **Nov 15, 10:00 AM MST** | **Deliver evidence package** | - |

---

## Contact

**Questions/Blockers**: Escalate to CEO immediately  
**Hourly Updates**: Required during remediation  
**Final Delivery**: Nov 15, 10:00 AM MST

**Current Status**: WAITING FOR PLATFORM LEAD TO START

---

**Prepared By**: Agent3 (Program Integrator)  
**Date**: Nov 14, 2025, 15:40 UTC
