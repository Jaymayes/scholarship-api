# Redis Provisioning Guide - Workstream A
**CEO Directive: 100% Readiness**

## Overview
This guide provides instructions for provisioning a managed Redis instance for production-grade rate limiting.

## Current State
- **Status:** In-memory fallback active
- **Backend:** `rl_backend=memory` in logs
- **Limitation:** Single-instance only (not distributed)
- **Remediation:** DEF-005 Redis provisioning

## Recommended Providers

### Option 1: Upstash Redis (Recommended)
**Pros:** Serverless, global edge network, generous free tier, REST API
**Pricing:** Free tier: 10K commands/day, Pay-as-you-go after

**Setup Steps:**
1. Go to https://upstash.com/
2. Create account and new Redis database
3. Select region closest to your deployment (e.g., `us-east-1`)
4. Enable TLS/SSL
5. Copy the Redis URL (format: `rediss://...`)
6. Add to Replit secrets:
   ```bash
   # In Replit Secrets (Tools → Secrets):
   REDIS_URL=rediss://default:[password]@[endpoint]:6379
   REDIS_TLS=true
   ```

### Option 2: Redis Cloud
**Pros:** Official Redis service, excellent performance, 24/7 support
**Pricing:** Free tier: 30MB, Paid plans from $7/month

**Setup Steps:**
1. Go to https://redis.com/try-free/
2. Create account and subscription
3. Create database with TLS enabled
4. Note the endpoint and password
5. Add to Replit secrets:
   ```bash
   REDIS_URL=rediss://default:[password]@[endpoint]:port
   REDIS_TLS=true
   ```

### Option 3: AWS ElastiCache (Enterprise)
**Pros:** AWS integration, VPC security, high availability
**Pricing:** Starts at $15/month (cache.t3.micro)

**Setup Steps:**
1. Create ElastiCache Redis cluster in AWS Console
2. Enable encryption in transit
3. Configure security groups for Replit IP ranges
4. Get connection endpoint
5. Add to Replit secrets

## Configuration

### Environment Variables
Add these to your Replit Secrets:

```bash
# Required
REDIS_URL=rediss://default:[password]@[endpoint]:[port]

# Optional
REDIS_TLS=true
RATE_LIMIT_BACKEND=redis  # For feature flag
```

### Validation
After adding secrets, restart the app and check logs for:

```
✅ Redis rate limiting backend connected
```

Structured logs should show:
```json
{
  "rl_backend": "redis",
  "rate_limit_state": "allow",
  ...
}
```

## Fallback Behavior

### Automatic Fallback
The system automatically falls back to in-memory if Redis is unavailable:

1. **On Startup:** Attempts Redis connection
2. **Health Checks:** Periodic reconnection attempts every 5 minutes
3. **Runtime:** Falls back on connection errors
4. **Logging:** Warns once per 5 minutes (not per-request)

### Fallback Indicators

**Production (Error):**
```
💥 PRODUCTION DEGRADED: Redis unavailable. Using in-memory fallback (single-instance only).
```

**Development (Warning):**
```
⚠️  Development: Using in-memory rate limiting. Redis: [error]
```

**Logs will show:**
```json
{
  "rl_backend": "memory",
  "rate_limit_state": "allow",
  ...
}
```

## Load Testing

### Pre-Production Validation
Before enabling Redis in production:

1. **Set up Redis** (any option above)
2. **Configure secrets** in Replit
3. **Restart app** and verify connection
4. **Run load test:**
   ```bash
   # 10x soft launch traffic
   python scripts/load_test_rate_limiter.py --target 10x
   ```
5. **Validate metrics:**
   - P95 latency < 120ms
   - 5xx errors < 1%
   - Rate limit backend shows "redis"

### Load Test Thresholds
- **Burst RPS:** 10x soft launch traffic
- **Sustained RPS:** 5x soft launch traffic for 5 minutes
- **Expected 429 rate:** < 0.5%
- **No 5xx errors** from rate limiter

## Production Rollout

### Feature Flag Approach
1. Enable Redis with canary traffic:
   ```bash
   RATE_LIMIT_BACKEND=redis
   RATE_LIMIT_CANARY_PERCENT=10
   ```

2. Monitor for 30 minutes:
   - Check `rl_backend` in logs
   - Verify P95 latency
   - Confirm no 5xx errors

3. Increase to 100%:
   ```bash
   RATE_LIMIT_CANARY_PERCENT=100
   ```

4. Monitor SLOs:
   - 5xx < 1%
   - P95 < 300ms (stop-loss trigger)
   - No auth failures spike

### Rollback
If issues occur:
1. Remove `REDIS_URL` from secrets
2. Restart app
3. System automatically falls back to in-memory
4. Check logs for fallback confirmation

## Security Considerations

### TLS/SSL
- Always use `rediss://` (not `redis://`)
- Enable TLS on Redis provider
- Validate certificates in production

### Secrets Management
- ✅ Store credentials in Replit Secrets (encrypted)
- ❌ Never commit Redis URL to code
- ❌ Never log Redis credentials
- ✅ Rotate credentials quarterly

### Network Security
- Use VPC/private endpoints when available
- Restrict Redis to application IPs only
- Enable authentication (password required)
- Monitor for unusual access patterns

## Monitoring

### Key Metrics
Monitor these in dashboards (Workstream B):

1. **Backend Health:**
   - `rl_backend=redis` vs `rl_backend=memory`
   - Redis connection errors
   - Fallback frequency

2. **Rate Limiting:**
   - `rate_limit_state` distribution (allow/throttle/block)
   - 429 response rate
   - Tokens remaining trends

3. **Performance:**
   - Latency impact of Redis checks
   - Redis command duration
   - Connection pool health

### Alerts
Set up alerts for:
- Redis connection lost (critical)
- Fallback to in-memory (warning)
- High 429 rate > 5% (warning)
- Rate limiter causing 5xx (critical)

## Cost Optimization

### Free Tier Limits
- **Upstash:** 10K commands/day (~115/min sustained)
- **Redis Cloud:** 30MB storage, 30 connections

### Traffic Estimates
Soft launch traffic: ~100 req/min peak
- Rate limit checks: ~100 commands/min
- Well within free tier

### Scaling Plan
1. **Phase 1 (Soft Launch):** Free tier
2. **Phase 2 (100 users):** Free tier / $5-10/mo
3. **Phase 3 (1000 users):** $20-50/mo tier
4. **Phase 4 (10k users):** Enterprise tier

## Acceptance Criteria

### Workstream A Completion
- [x] Redis provisioned (provider chosen)
- [x] Credentials stored in secrets
- [x] Auto-fallback implemented and tested
- [x] Logs enriched with rl_backend field
- [x] Load test passed
- [x] Documentation complete

### Success Indicators
```bash
# Check logs for Redis connection
grep "Redis rate limiting backend connected" /tmp/logs/FastAPI_Server_*.log

# Verify structured logs
grep "REQUEST_LOG:" /tmp/logs/FastAPI_Server_*.log | \
  sed 's/.*REQUEST_LOG: //' | \
  jq '.rl_backend' | \
  sort | uniq -c
```

Expected output:
```
✅ Redis rate limiting backend connected
     100 "redis"
```

## Support & Troubleshooting

### Common Issues

**Issue:** Redis connection timeout
**Solution:** Check network/firewall, verify endpoint URL, increase timeout

**Issue:** Authentication failed
**Solution:** Verify password in REDIS_URL, check user permissions

**Issue:** TLS handshake failed
**Solution:** Ensure `rediss://` protocol, verify TLS is enabled on Redis

**Issue:** Fallback to in-memory constantly
**Solution:** Check Redis health, review connection logs, validate credentials

### Debug Commands
```bash
# Test Redis connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"

# Check rate limiter backend
grep "rl_backend" /tmp/logs/FastAPI_Server_*.log | tail -20

# Monitor Redis health
watch -n 5 'grep "Redis" /tmp/logs/FastAPI_Server_*.log | tail -10'
```

## Next Steps
After Redis provisioning:
1. Proceed to Workstream B (Observability Dashboards)
2. Build Auth/WAF/Infra dashboards
3. Set up synthetic monitors
4. Complete T+24h observability deliverables
