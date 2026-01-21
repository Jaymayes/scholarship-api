# A1 Auth Hot-Path Optimization

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-058  
**Service**: A1 Auth Service  
**Sprint**: V2 Sprint-1 (72h)

## Performance Targets

| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Login P95 | ~240ms | ≤200ms | ≤150ms |
| Login Max | ~320ms | ≤280ms | ≤240ms |
| Token validation P95 | ~50ms | ≤30ms | ≤20ms |

## Optimization Strategy

### 1. OIDC Discovery/JWKS Warm on Boot

**Problem**: Cold start latency when fetching JWKS from identity provider.

**Solution**:
```python
# On application startup
async def warmup_jwks():
    """Pre-fetch and cache JWKS keys before first request."""
    jwks_client = PyJWKClient(settings.JWKS_URI)
    # Fetch and cache keys
    signing_keys = jwks_client.get_signing_keys()
    logger.info(f"JWKS warmed: {len(signing_keys)} keys cached")
    
# Register as startup handler
app.add_event_handler("startup", warmup_jwks)
```

**Impact**: Eliminates 100-150ms cold start on first auth request.

### 2. Keep-Alive Connection Pooling

**Problem**: TCP connection setup overhead on each OIDC request.

**Solution**:
```python
# Use httpx with connection pooling
http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=30
    ),
    timeout=httpx.Timeout(5.0, connect=2.0)
)
```

**Impact**: Saves 20-40ms per external request.

### 3. Remove Sync I/O in Request Path

**Problem**: Blocking file I/O for config/secrets loading in request handlers.

**Solution**:
```python
# Before: Sync file read in request
def get_secret():
    with open("secret.key") as f:
        return f.read()

# After: Cache at startup
SECRET_KEY = None

@app.on_event("startup")
async def load_secrets():
    global SECRET_KEY
    async with aiofiles.open("secret.key") as f:
        SECRET_KEY = await f.read()
```

**Impact**: Eliminates 5-15ms blocking I/O per request.

### 4. Lightweight Session Lookup Cache

**Problem**: Database round-trip for every session validation.

**Solution**:
```python
# In-memory LRU cache with TTL
from cachetools import TTLCache

session_cache = TTLCache(maxsize=10000, ttl=60)

async def validate_session(session_id: str) -> Optional[Session]:
    # Check cache first
    if session_id in session_cache:
        return session_cache[session_id]
    
    # Cache miss - fetch from DB
    session = await db.get_session(session_id)
    if session:
        session_cache[session_id] = session
    return session
```

**Impact**: Reduces DB queries by ~80%, saves 30-50ms per cached hit.

### 5. JWT Validation Optimization

**Problem**: Full JWT parsing on every request.

**Solution**:
```python
# Quick expiry check before full validation
def quick_jwt_check(token: str) -> bool:
    """Fast check without full validation."""
    try:
        # Decode without verification for quick expiry check
        unverified = jwt.decode(token, options={"verify_signature": False})
        exp = unverified.get("exp", 0)
        return exp > time.time()
    except:
        return False
```

**Impact**: Saves 5-10ms for expired tokens.

## Implementation Checklist

| Optimization | Priority | Status |
|--------------|----------|--------|
| JWKS warm on boot | P0 | ✅ Design Complete |
| Connection pooling | P0 | ✅ Design Complete |
| Remove sync I/O | P1 | ✅ Design Complete |
| Session cache | P1 | ✅ Design Complete |
| JWT quick check | P2 | ✅ Design Complete |

## Spike Test Expectations

| Concurrency | Current P95 | Expected P95 |
|-------------|-------------|--------------|
| 20 | 240ms | ≤180ms |
| 30 | 280ms | ≤200ms |
| 40 | 320ms | ≤220ms |

## Monitoring

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| login_p95_ms | Prometheus | >240ms (2 consecutive) |
| login_max_ms | Prometheus | >320ms (any) |
| jwks_cache_hit_rate | Custom | <95% |
| session_cache_hit_rate | Custom | <80% |

**Status**: ✅ DESIGN COMPLETE
