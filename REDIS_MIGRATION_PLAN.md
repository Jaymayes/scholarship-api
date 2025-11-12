# Redis Migration Plan: Replay Protection & Idempotency Storage

**CEO Directive**: Gate B - Production-ready callback integration  
**Priority**: P0 Follow-up (Week 1 Post-Launch)  
**Owner**: Agent3  
**Status**: PLANNED  

---

## Executive Summary

The provider_register → scholarship_api callback integration currently uses in-memory storage for replay protection and idempotency tracking. While functional for initial launch, this approach has critical limitations that must be addressed before high-volume production use.

**Timeline**: Week 1 post-launch (Nov 18-22, 2025)  
**Effort**: ~4 hours implementation + 2 hours testing  
**Risk**: LOW (additive change, backward compatible)

---

## Current Implementation

### Replay Protection (In-Memory)
**Location**: `middleware/service_auth.py`

```python
# Global in-memory store for replay protection
_used_request_ids: Set[str] = set()

# No TTL, no cleanup, unbounded growth
if request_id in _used_request_ids:
    return {"valid": False, "reason": "Replay attack detected"}
_used_request_ids.add(request_id)
```

**Issues**:
- ❌ Unbounded memory growth (accumulates forever)
- ❌ Lost on process restart (replay protection breaks)
- ❌ Not shared across horizontal scaling (each instance has own set)
- ❌ No automatic expiry (5-minute drift window not enforced)

### Idempotency Storage (In-Memory)
**Location**: `routers/b2b_partner.py`

```python
# Global in-memory cache for idempotency
_idempotency_store: Dict[str, IdempotencyRecord] = {}

# No TTL, no cleanup
if idempotency_key in _idempotency_store:
    return OnboardingCallbackResponse(**cached_record.response)
_idempotency_store[idempotency_key] = record
```

**Issues**:
- ❌ Unbounded memory growth
- ❌ Lost on restart (retries after restart may duplicate processing)
- ❌ Not shared across instances
- ❌ No automatic cleanup

---

## Target Architecture

### Redis-Backed Storage

**Benefits**:
- ✅ Automatic expiry (TTL-based cleanup)
- ✅ Shared across all instances (horizontal scaling support)
- ✅ Persistent across restarts
- ✅ Bounded memory (Redis eviction policies)
- ✅ Production-grade reliability

### Redis Schema

```
# Replay Protection Keys
Key: replay:request_id:{request_id}
Value: timestamp
TTL: 5 minutes (300 seconds)

# Idempotency Keys
Key: idempotency:{sha256_hash}
Value: JSON-serialized OnboardingCallbackResponse
TTL: 24 hours (86400 seconds)
```

---

## Implementation Plan

### Phase 1: Redis Setup (Day 1)

**Tasks**:
1. Install redis package: `pip install redis`
2. Configure Redis connection in `config/settings.py`:
   ```python
   REDIS_URL: str = "redis://localhost:6379/0"
   REDIS_PASSWORD: Optional[str] = None
   REDIS_DB: int = 0
   ```
3. Create Redis client wrapper in `infrastructure/redis_client.py`:
   ```python
   class RedisClient:
       def __init__(self, url: str):
           self.client = redis.from_url(url, decode_responses=True)
       
       def set_with_ttl(self, key: str, value: str, ttl_seconds: int):
           return self.client.setex(key, ttl_seconds, value)
       
       def get(self, key: str) -> Optional[str]:
           return self.client.get(key)
       
       def exists(self, key: str) -> bool:
           return self.client.exists(key) > 0
   ```

### Phase 2: Migrate Replay Protection (Day 2)

**Location**: `middleware/service_auth.py`

**Changes**:
```python
from infrastructure.redis_client import RedisClient

class ServiceAuthMiddleware:
    def __init__(self, ...):
        self.redis = RedisClient(settings.REDIS_URL)
        self.replay_ttl = 300  # 5 minutes (matches drift window)
    
    async def _validate_service_auth(self, request: Request) -> dict:
        # Check replay protection in Redis
        replay_key = f"replay:request_id:{request_id}"
        
        if self.redis.exists(replay_key):
            logger.warning(f"Replay attack detected: {request_id}")
            return {"valid": False, "reason": "Replay attack detected"}
        
        # Store in Redis with TTL
        self.redis.set_with_ttl(replay_key, timestamp, self.replay_ttl)
        
        # Signature validation...
        return {"valid": True}
```

**Testing**:
- Unit test: Verify Redis key creation with correct TTL
- Integration test: Verify replay rejection across multiple requests
- Load test: Verify performance impact (<5ms overhead)

### Phase 3: Migrate Idempotency (Day 3)

**Location**: `routers/b2b_partner.py`

**Changes**:
```python
from infrastructure.redis_client import RedisClient

redis_client = RedisClient(settings.REDIS_URL)

@router.post("/{partner_id}/onboarding/{step_id}/complete")
async def complete_onboarding_step(...):
    # Generate idempotency key
    idempotency_key = IdempotencyRecord.generate_key(...)
    redis_key = f"idempotency:{idempotency_key}"
    
    # Check Redis cache
    cached_response = redis_client.get(redis_key)
    if cached_response:
        logger.info(f"Idempotent callback replay detected: {request_id}")
        return OnboardingCallbackResponse(**json.loads(cached_response))
    
    # Process callback...
    response = OnboardingCallbackResponse(...)
    
    # Store in Redis with 24-hour TTL
    redis_client.set_with_ttl(
        redis_key,
        json.dumps(response.model_dump()),
        ttl_seconds=86400
    )
    
    return response
```

**Testing**:
- Unit test: Verify cache hit/miss logic
- Integration test: Verify idempotency across multiple retries
- E2E test: Update existing test to verify Redis integration

### Phase 4: Deployment & Monitoring (Day 4)

**Infrastructure**:
1. Provision Redis instance (Replit Redis integration or external service)
2. Configure REDIS_URL environment variable
3. Deploy updated code with Redis support
4. Monitor Redis metrics:
   - Key count (replay + idempotency)
   - Memory usage
   - Hit/miss ratio
   - Expiry rate

**Monitoring Alerts**:
- Redis connection failures → Page on-call
- Memory usage >80% → Warning
- Cache hit ratio <50% → Investigation

**Rollback Plan**:
- If Redis fails, gracefully degrade to in-memory (log errors)
- Feature flag: `ENABLE_REDIS_CACHE=true/false`
- Automatic fallback on Redis connection errors

---

## Production Readiness Checklist

### Pre-Migration
- [ ] Provision Redis instance
- [ ] Configure REDIS_URL secret
- [ ] Test Redis connectivity from app
- [ ] Review Redis eviction policy (allkeys-lru recommended)

### Migration
- [ ] Install redis package
- [ ] Implement RedisClient wrapper
- [ ] Migrate replay protection
- [ ] Migrate idempotency storage
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Run E2E test suite

### Post-Migration
- [ ] Monitor Redis metrics (first 24 hours)
- [ ] Verify TTL cleanup working
- [ ] Confirm no memory leaks
- [ ] Load test with 1000 concurrent callbacks
- [ ] Document Redis schema in architecture docs

---

## Risk Mitigation

### Risk 1: Redis Downtime
**Impact**: Replay protection and idempotency broken  
**Mitigation**: Graceful degradation to in-memory with logging  
**Detection**: Redis connection health checks every 60s

### Risk 2: Performance Regression
**Impact**: Callback latency >120ms (SLO violation)  
**Mitigation**: Redis pipelining for batch operations  
**Detection**: P95 latency monitoring with alerts

### Risk 3: Memory Pressure on Redis
**Impact**: Eviction of valid idempotency keys  
**Mitigation**: Allocate 2GB Redis memory, monitor usage  
**Detection**: Memory usage alerts at 80%

---

## Success Metrics

**Functional**:
- ✅ Replay attacks blocked across process restarts
- ✅ Idempotency maintained across retries (24-hour window)
- ✅ Automatic TTL cleanup (no manual intervention)
- ✅ Horizontal scaling support (shared state)

**Performance**:
- ✅ Callback latency <120ms (P95)
- ✅ Redis overhead <5ms per request
- ✅ 99.9% cache hit ratio for replays

**Operational**:
- ✅ Zero manual cleanup required
- ✅ Graceful degradation on Redis failures
- ✅ Clear monitoring dashboards

---

## Timeline

**Week 1 Post-Launch** (Nov 18-22, 2025):

| Day | Task | Owner | Duration |
|-----|------|-------|----------|
| Mon | Provision Redis + configure connection | Agent3 | 2h |
| Tue | Migrate replay protection | Agent3 | 3h |
| Wed | Migrate idempotency storage | Agent3 | 3h |
| Thu | Testing + monitoring setup | Agent3 | 4h |
| Fri | Deployment + validation | Agent3 | 2h |

**Total Effort**: ~14 hours  
**Deployment Window**: Thu evening (low traffic)

---

## Alternative Considered: PostgreSQL

**Pros**:
- Already have PostgreSQL database
- No new infrastructure
- Strong consistency

**Cons**:
- No automatic TTL (need cleanup job)
- Higher latency vs Redis (10-20ms vs <1ms)
- Adds load to primary database
- Requires additional tables/indexes

**Decision**: Redis is preferred for TTL support and performance

---

## Appendix: Redis Configuration

### Recommended Settings

```yaml
# Redis Configuration (redis.conf)
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60

# Persistence (optional, replay data is ephemeral)
save ""
appendonly no
```

### Replit Integration

```bash
# Enable Replit Redis integration
replit redis enable

# Access via environment variable
REDIS_URL=$REPLIT_REDIS_URL
```

---

**Approval Required**: Engineering Lead + CEO  
**Status**: READY FOR WEEK 1 EXECUTION
