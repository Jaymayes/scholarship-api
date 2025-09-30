# DEF-005: Redis Rate Limiting Unavailable

**Severity:** 🟡 MEDIUM (Infrastructure)  
**Component:** Rate Limiting / Redis  
**Owner:** Infra/DevOps + App Team  
**Target:** Day 1-2  
**Status:** 🟡 IN PROGRESS

---

## 📋 PROBLEM STATEMENT

Redis is unavailable, causing fallback to in-memory rate limiting. This is not production-ready as rate limits reset on every deployment, there's no distributed limiting across pods, and memory exhaustion risk exists under attack. Production requires persistent, distributed rate limiting with Redis.

## 🔬 EVIDENCE

**Current State:**
```json
{
  "rate_limiting": {
    "backend_type": "in-memory fallback (Redis unavailable)",
    "per_minute_limit": 200,
    "enabled": true
  }
}
```

**Error Logs:**
```
WARNING:scholarship_api.middleware.rate_limiting:⚠️ Development mode: Redis rate limiting unavailable, using in-memory fallback. Error: Error 99 connecting to localhost:6379. Cannot assign requested address.
```

**Impact:**
- Rate limits reset on redeploy (users can bypass by waiting)
- No cross-pod limit enforcement (each instance independent)
- Memory leaks possible under sustained attack
- Cannot implement global API quotas

## 🎯 ACCEPTANCE CRITERIA (Launch Gate - Distributed Rate Limiting)

**Redis Rate Limiting Gate:**
- [ ] **Managed Redis provisioned** and accessible from API
- [ ] **Distributed rate limiting verified** across multiple app instances
- [ ] **Consistent counters across pods** (user hitting limit on pod-1 blocked on pod-2)
- [ ] **Limiter survives redeployments** (counters persist in Redis)
- [ ] **No user-facing throttling regressions** (same limits as before)
- [ ] **Graceful fallback tested** (in-memory if Redis temporarily down)
- [ ] **Safe limits configured** (per-user, per-IP, global quotas)

## 🛠️ FIX PLAN

### Phase 1: Provision Managed Redis (1 hour)

**Option A: Upstash Redis (RECOMMENDED)**
- Serverless Redis with generous free tier
- Global distribution
- Low latency
- REST API support

```bash
# 1. Sign up: https://upstash.com
# 2. Create Redis database
#    - Name: scholarshipai-rate-limiting-prod
#    - Region: us-east-1 (match API region)
#    - Type: Regional (for low latency)
# 3. Get connection details:
export REDIS_URL="rediss://default:<password>@<host>:6379"
export REDIS_HOST="<host>"
export REDIS_PORT="6379"
export REDIS_PASSWORD="<password>"
export REDIS_TLS="true"
```

**Option B: Redis Cloud (Managed)**
```bash
# Alternative: Redis Enterprise Cloud
# Free tier: 30MB, perfect for rate limiting
# Sign up: https://redis.com/try-free/
```

**Option C: Self-Hosted (Not Recommended for Production)**
```yaml
# docker-compose.redis.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
volumes:
  redis_data:
```

### Phase 2: Update Rate Limiting Configuration (30 min)

```python
# config/settings.py

class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str | None = Field(None, alias="REDIS_URL")
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_password: str | None = Field(None, alias="REDIS_PASSWORD")
    redis_tls: bool = Field(False, alias="REDIS_TLS")
    redis_db: int = Field(0, alias="REDIS_DB")
    
    # Rate Limiting
    rate_limit_backend: str = Field("redis", alias="RATE_LIMIT_BACKEND")  # "redis" or "memory"
    rate_limit_per_minute: int = Field(200, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(10000, alias="RATE_LIMIT_PER_HOUR")
    
    @property
    def redis_connection_string(self) -> str:
        """Get Redis connection string"""
        if self.redis_url:
            return self.redis_url
        
        protocol = "rediss" if self.redis_tls else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
```

### Phase 3: Implement Distributed Rate Limiting (2 hours)

```python
# middleware/enhanced_rate_limiting.py
import redis.asyncio as redis
from slowapi import Limiter
from slowapi.util import get_remote_address

class RedisRateLimiter:
    def __init__(self):
        self.redis_client = None
        self.fallback_to_memory = False
        
    async def connect(self):
        """Connect to Redis with fallback"""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_connection_string,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("✅ Redis rate limiting connected successfully")
            self.fallback_to_memory = False
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️ Falling back to in-memory rate limiting")
            self.fallback_to_memory = True
    
    async def increment_counter(
        self, 
        key: str, 
        window_seconds: int,
        limit: int
    ) -> Tuple[int, bool]:
        """
        Increment rate limit counter
        Returns: (current_count, is_allowed)
        """
        if self.fallback_to_memory or not self.redis_client:
            # Fallback to in-memory (not production-safe)
            return await self._memory_increment(key, window_seconds, limit)
        
        try:
            # Use Redis INCR with expiry (atomic operation)
            pipe = self.redis_client.pipeline()
            
            # Increment counter
            pipe.incr(key)
            # Set expiry if this is first increment
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            current_count = results[0]
            
            is_allowed = current_count <= limit
            
            return current_count, is_allowed
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Graceful degradation: allow request if Redis fails
            return 0, True
    
    async def get_ttl(self, key: str) -> int:
        """Get time-to-live for rate limit key"""
        if self.redis_client:
            return await self.redis_client.ttl(key)
        return 60  # Default for memory fallback

# Initialize rate limiter
redis_limiter = RedisRateLimiter()

@app.on_event("startup")
async def connect_redis():
    await redis_limiter.connect()

# SlowAPI configuration with Redis storage
def rate_limit_key_func(request: Request) -> str:
    """Generate rate limit key from user or IP"""
    # Try to get authenticated user
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.user_id}"
    
    # Fallback to IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP (client)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host
    
    return f"ip:{client_ip}"

limiter = Limiter(
    key_func=rate_limit_key_func,
    storage_uri=settings.redis_connection_string,
    strategy="fixed-window"
)

# Apply to app
app.state.limiter = limiter
```

### Phase 4: Multi-Tier Rate Limits (1 hour)

```python
# middleware/tiered_rate_limiting.py

class TieredRateLimiter:
    """Multi-tier rate limiting: per-user, per-IP, global"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_all_limits(self, request: Request) -> Tuple[bool, dict]:
        """Check all rate limit tiers"""
        
        # Tier 1: Per-User limit (if authenticated)
        if hasattr(request.state, "user") and request.state.user:
            user_allowed, user_limit_info = await self._check_user_limit(
                request.state.user.user_id
            )
            if not user_allowed:
                return False, user_limit_info
        
        # Tier 2: Per-IP limit
        ip = get_client_ip(request)
        ip_allowed, ip_limit_info = await self._check_ip_limit(ip)
        if not ip_allowed:
            return False, ip_limit_info
        
        # Tier 3: Global API limit (anti-DDoS)
        global_allowed, global_limit_info = await self._check_global_limit()
        if not global_allowed:
            return False, global_limit_info
        
        return True, {"status": "allowed"}
    
    async def _check_user_limit(self, user_id: str) -> Tuple[bool, dict]:
        """Per-user rate limit"""
        key = f"ratelimit:user:{user_id}:minute"
        count, allowed = await redis_limiter.increment_counter(
            key, 
            window_seconds=60, 
            limit=100  # 100 req/min per user
        )
        
        if not allowed:
            ttl = await redis_limiter.get_ttl(key)
            return False, {
                "error": "User rate limit exceeded",
                "limit": 100,
                "window": "minute",
                "retry_after": ttl
            }
        
        return True, {}
    
    async def _check_ip_limit(self, ip: str) -> Tuple[bool, dict]:
        """Per-IP rate limit (anti-abuse)"""
        key = f"ratelimit:ip:{ip}:minute"
        count, allowed = await redis_limiter.increment_counter(
            key,
            window_seconds=60,
            limit=200  # 200 req/min per IP
        )
        
        if not allowed:
            ttl = await redis_limiter.get_ttl(key)
            return False, {
                "error": "IP rate limit exceeded",
                "limit": 200,
                "window": "minute",
                "retry_after": ttl
            }
        
        return True, {}
    
    async def _check_global_limit(self) -> Tuple[bool, dict]:
        """Global API rate limit (DDoS protection)"""
        key = "ratelimit:global:second"
        count, allowed = await redis_limiter.increment_counter(
            key,
            window_seconds=1,
            limit=1000  # 1000 req/sec globally
        )
        
        if not allowed:
            return False, {
                "error": "Global rate limit exceeded (DDoS protection)",
                "retry_after": 1
            }
        
        return True, {}

# Middleware
@app.middleware("http")
async def tiered_rate_limit_middleware(request: Request, call_next):
    tiered_limiter = TieredRateLimiter(redis_limiter.redis_client)
    
    allowed, limit_info = await tiered_limiter.check_all_limits(request)
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content=limit_info,
            headers={
                "Retry-After": str(limit_info.get("retry_after", 60)),
                "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                "X-RateLimit-Window": limit_info.get("window", "minute")
            }
        )
    
    response = await call_next(request)
    return response
```

### Phase 5: Testing & Validation (1 hour)

```python
# tests/test_redis_rate_limiting.py
import pytest
import asyncio

class TestRedisRateLimiting:
    
    @pytest.mark.asyncio
    async def test_distributed_rate_limiting(self):
        """Test that limits are enforced across multiple pods"""
        
        # Simulate 2 API instances
        client1 = httpx.AsyncClient(base_url=BASE_URL)
        client2 = httpx.AsyncClient(base_url=BASE_URL)
        
        # User makes 50 requests on pod 1
        for i in range(50):
            response = await client1.get("/api/v1/search?q=test", headers=auth_headers)
            assert response.status_code == 200
        
        # User makes 51st request on pod 2 (should hit limit)
        for i in range(51):
            response = await client2.get("/api/v1/search?q=test", headers=auth_headers)
        
        # 51st request should be rate limited
        assert response.status_code == 429
        assert "retry_after" in response.json()
    
    @pytest.mark.asyncio
    async def test_rate_limit_persistence(self):
        """Test that limits persist across redeployments"""
        
        # Hit rate limit
        for i in range(100):
            await client.get("/api/v1/search?q=test", headers=auth_headers)
        
        # Simulate redeployment (restart app)
        await restart_application()
        
        # Rate limit should still be enforced
        response = await client.get("/api/v1/search?q=test", headers=auth_headers)
        assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_graceful_fallback(self):
        """Test fallback to memory if Redis unavailable"""
        
        # Stop Redis
        await stop_redis()
        
        # Requests should still work (with warning)
        response = await client.get("/api/v1/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        
        # Check logs for fallback warning
        assert "Falling back to in-memory rate limiting" in logs
```

## ✅ VERIFICATION CHECKLIST

- [ ] Managed Redis provisioned (Upstash or Redis Cloud)
- [ ] REDIS_URL environment variable configured
- [ ] Redis connection successful on app startup
- [ ] Distributed rate limiting tested (2+ pods)
- [ ] Rate limits persist across redeployments
- [ ] Multi-tier limits working (user, IP, global)
- [ ] Graceful fallback to memory tested
- [ ] Headers include rate limit info (X-RateLimit-*)
- [ ] Monitoring dashboards updated

## 📊 MONITORING

```python
# metrics/rate_limiting.py
from prometheus_client import Counter, Gauge

rate_limit_hits = Counter(
    'rate_limit_hits_total',
    'Rate limit hits',
    ['tier', 'user_id']
)

rate_limit_allowed = Counter(
    'rate_limit_allowed_total',
    'Rate limit allowed requests',
    ['tier']
)

redis_connection_status = Gauge(
    'redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)'
)
```

## 🔄 ROLLBACK PLAN

If Redis issues occur:
1. Graceful fallback to in-memory (already implemented)
2. Log warning but continue serving traffic
3. Fix Redis connection in background
4. No user-facing disruption

## 📁 ARTIFACTS

- [ ] Redis provisioning documentation
- [ ] Connection test results
- [ ] Multi-pod distributed test results
- [ ] Fallback behavior validation

---

**ETA:** Day 1-2 (5.5 hours total)  
**Risk:** Low (has graceful fallback)  
**Dependencies:** Budget approval (Redis ~$10-50/month)
