# JWT Validation Load Tests

**Application**: scholarship_api  
**Target**: 300 RPS, 15 minutes sustained  
**SLO**: P95 ≤ 120ms, Error rate < 0.5%  
**Created**: November 13, 2025  

---

## Prerequisites

1. **Install k6**:
   ```bash
   # MacOS
   brew install k6
   
   # Linux
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   
   # Windows (Chocolatey)
   choco install k6
   ```

2. **Get Test Tokens**:
   ```bash
   # HS256 token (from scholarship_api auth)
   export HS256_TEST_TOKEN="<your_hs256_token>"
   
   # RS256 token (from scholar_auth)
   export RS256_TEST_TOKEN="<your_rs256_token>"
   ```

3. **Verify Service is Running**:
   ```bash
   curl https://scholarship-api-jamarrlmayes.replit.app/health
   # Should return: {"status": "healthy"}
   ```

---

## Running the Load Test

### Basic Run (300 RPS, 15 min)
```bash
cd load-tests

k6 run \
  --env BASE_URL=https://scholarship-api-jamarrlmayes.replit.app \
  --env HS256_TEST_TOKEN="${HS256_TEST_TOKEN}" \
  --env RS256_TEST_TOKEN="${RS256_TEST_TOKEN}" \
  jwt_validation_load_test.js
```

### Quick Smoke Test (10 RPS, 1 min)
```bash
k6 run \
  --duration 1m \
  --vus 10 \
  --env BASE_URL=https://scholarship-api-jamarrlmayes.replit.app \
  --env HS256_TEST_TOKEN="${HS256_TEST_TOKEN}" \
  jwt_validation_load_test.js
```

### Save Results to JSON
```bash
k6 run \
  --out json=results/jwt_validation_$(date +%Y%m%d_%H%M%S).json \
  --env BASE_URL=https://scholarship-api-jamarrlmayes.replit.app \
  --env HS256_TEST_TOKEN="${HS256_TEST_TOKEN}" \
  --env RS256_TEST_TOKEN="${RS256_TEST_TOKEN}" \
  jwt_validation_load_test.js
```

---

## Interpreting Results

### Success Criteria (CEO SLO)
```
✅ PASS: http_req_duration.p95 ≤ 120ms
✅ PASS: jwt_validation_errors.rate < 0.5%
✅ PASS: hs256_token_success.rate > 99.5%
✅ PASS: rs256_token_success.rate > 99.5%
```

### Sample Passing Output
```
     ✓ HS256: status is 200
     ✓ HS256: has valid JSON
     ✓ HS256: response time < 120ms
     ✓ RS256: status is 200 or 503
     ✓ RS256: not 500 (no coroutine errors)

     checks.........................: 100.00% ✓ 270000 ✗ 0
     http_req_duration..............: avg=45ms  min=12ms med=38ms max=115ms p(95)=89ms p(99)=105ms
     http_req_failed................: 0.00%   ✓ 0      ✗ 270000
     jwt_validation_errors..........: 0.00%   ✓ 0      ✗ 270000
     hs256_token_success............: 100.00% ✓ 189000 ✗ 0
     rs256_token_success............: 100.00% ✓ 81000  ✗ 0
     iterations.....................: 270000  300/s
```

### Sample Failing Output (Bug Present)
```
     ✗ HS256: status is 200
     ✗ RS256: not 500 (no coroutine errors)  <-- CRITICAL BUG

     checks.........................: 0.00%   ✓ 0      ✗ 270000
     http_req_duration..............: avg=250ms (FAIL - exceeds 120ms P95 SLO)
     http_req_failed................: 100.00% (FAIL - all requests failing)
     jwt_validation_errors..........: 100.00% (FAIL - exceeds 0.5% SLO)
```

---

## Monitoring During Load Test

### Watch Logs in Real-Time
```bash
# Terminal 1: Run load test
k6 run jwt_validation_load_test.js

# Terminal 2: Watch server logs
tail -f /tmp/logs/FastAPI_Server_*.log | grep -E "ERROR|CRITICAL|coroutine"
```

### Watch Metrics
```bash
# Monitor Prometheus metrics
curl https://scholarship-api-jamarrlmayes.replit.app/metrics | grep jwt

# Watch JWKS cache stats
curl https://scholarship-api-jamarrlmayes.replit.app/readyz | jq '.jwks'
```

---

## Common Issues

### Issue 1: "coroutine not awaited" errors
**Symptom**: 500 errors, logs show `RuntimeWarning: coroutine 'decode_token' was never awaited`  
**Root Cause**: Bug #1 - async decode_token not awaited  
**Fix**: Apply patch from `docs/evidence/scholarship_api/JWT_VALIDATION_BUG_REPORT.md`

### Issue 2: Silent 401 errors (no JWKS logs)
**Symptom**: RS256 tokens return 401, but no JWKS fetch errors in logs  
**Root Cause**: Bug #2 - Silent JWKS failure  
**Fix**: Apply patch from bug report (add explicit error handling)

### Issue 3: High latency spikes
**Symptom**: P95 > 120ms, especially on first RS256 request  
**Root Cause**: JWKS cache not prewarmed  
**Fix**: Verify startup logs show "JWKS cache prewarmed"

---

## Post-Test Checklist

After running load test, verify:

- [ ] No "coroutine" errors in logs
- [ ] P95 latency ≤ 120ms
- [ ] Error rate < 0.5%
- [ ] JWKS cache hit rate ≥ 95% (check `/readyz`)
- [ ] 503 errors (if any) have clear messages (not silent failures)
- [ ] Prometheus metrics show realistic data
- [ ] No memory leaks (check `psutil` metrics)

---

## Next Steps

1. **Fix bugs** per patch plan in `JWT_VALIDATION_BUG_REPORT.md`
2. **Re-run load test** after fixes applied
3. **Document results** in `results/` directory
4. **Schedule canary test** for Nov 17 before go-live

---

**Maintained by**: Agent3, Program Integrator  
**For questions**: See CEO memo (Nov 13, 2025)
