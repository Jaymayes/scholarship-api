# JWT Validation Failures - Bug Report & Patch Plan

**Application**: scholarship_api  
**Reporter**: Agent3 (Program Integrator)  
**Date**: November 13, 2025  
**Timestamp**: 2025-11-13 17:00 MST  
**Severity**: P0 - BLOCKER for go-live  
**CEO Directive**: Nov 13 memo - deliver by 9 PM MST  

---

## Executive Summary

Architect review identified **2 critical bugs** in JWKS/RS256 JWT validation implementation that will cause runtime failures under load. Both bugs prevent token validation from working correctly and must be fixed before load testing.

**Impact**: 100% authentication failure rate when RS256 tokens are used (service-to-service auth)

**Root Cause**: Incomplete async/await refactoring + insufficient error handling

---

## Bug #1: Async decode_token() Not Awaited at Call Sites

### Severity
**CRITICAL** - Causes immediate runtime failure

### Description
The `decode_token()` function in `middleware/auth.py` was converted to `async` to support asynchronous JWKS fetching for RS256 validation. However, **all call sites still invoke it synchronously** without `await`, causing:
- `TypeError: 'coroutine' object is not subscriptable`
- Token validation always fails
- No tokens can be decoded (HS256 or RS256)

### Affected Files
1. `middleware/auth_dependency.py` (line 31)
2. Any route using `get_current_user()` dependency

### Reproduction Steps

```bash
# 1. Start server with JWKS enabled
PORT=5000 python main.py

# 2. Send authenticated request
curl -H "Authorization: Bearer eyJ..." \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

# Expected: 200 OK with scholarship data
# Actual: 500 Internal Server Error
# Error: RuntimeWarning: coroutine 'decode_token' was never awaited
```

### Failing Trace

```python
# middleware/auth_dependency.py:31
async def get_auth_user_optional() -> dict | None:
    try:
        return await get_current_user()  # ❌ This calls decode_token() synchronously
    except HTTPException:
        return None

# middleware/auth.py (inside get_current_user)
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)  # ❌ Missing await - decode_token is async!
    # Result: TypeError at runtime
```

### Patch Plan

**Option A: Make all call sites async** (RECOMMENDED)
```python
# middleware/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = await decode_token(token)  # ✅ Await the async function
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload

# middleware/auth_dependency.py - Already async, just needs get_current_user to be async
async def get_auth_user_optional() -> dict | None:
    try:
        return await get_current_user()  # ✅ Will work when get_current_user is async
    except HTTPException:
        return None
```

**Option B: Keep synchronous wrapper** (FALLBACK)
```python
# middleware/auth.py - Create sync wrapper
def decode_token_sync(token: str) -> dict | None:
    """Synchronous wrapper for backwards compatibility"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(decode_token(token))
    except RuntimeError:
        # No event loop in current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(decode_token(token))

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token_sync(token)  # ✅ Use sync wrapper
    # ... rest of logic
```

**Recommended**: **Option A** - FastAPI dependencies support async natively, cleaner implementation

### Testing Plan
```bash
# After fix, verify both token types work:

# Test 1: HS256 token (existing)
curl -H "Authorization: Bearer <HS256_TOKEN>" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

# Test 2: RS256 token (new)
curl -H "Authorization: Bearer <RS256_TOKEN>" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

# Both should return 200 OK
```

---

## Bug #2: Silent JWKS Failure - Security Risk

### Severity
**CRITICAL** - Security vulnerability + degraded observability

### Description
When JWKS fetch fails (network error, scholar_auth down, etc.), the `verify_rs256_token()` method silently returns `None` instead of:
1. Logging a clear error with alert severity
2. Rejecting the authentication attempt explicitly
3. Emitting metrics for monitoring

This creates a **security gap** where RS256 tokens are silently ignored during JWKS outages, with no visibility into the failure.

### Affected Files
1. `services/jwks_client.py` (lines 200-250 - verify_rs256_token method)

### Reproduction Steps

```bash
# 1. Configure invalid JWKS URL to simulate failure
export SCHOLAR_AUTH_JWKS_URL="https://invalid-url.example.com/.well-known/jwks.json"

# 2. Start server
PORT=5000 python main.py

# 3. Send RS256 token
curl -H "Authorization: Bearer <RS256_TOKEN_WITH_VALID_KID>" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

# Expected: 503 Service Unavailable - "Auth provider unreachable"
# Actual: 401 Unauthorized - "Invalid token" (generic, no indication of JWKS failure)
```

### Failing Trace

```python
# services/jwks_client.py (current implementation)
async def verify_rs256_token(self, token: str, kid: str) -> Optional[Dict[str, Any]]:
    """Verify RS256 JWT using JWKS key"""
    
    # Fetch key for this kid
    key = await self.get_key(kid)
    
    if key is None:
        logger.warning(f"Key {kid} not found in JWKS cache")  # ❌ Silent failure!
        return None  # ❌ Should raise exception or return error code
    
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False}
        )
        return payload
    except JWTError as e:
        logger.warning(f"RS256 verification failed: {e}")  # ❌ Generic warning
        return None  # ❌ Should distinguish between invalid token vs infrastructure failure
```

### Patch Plan

**Add explicit failure modes and observability**:

```python
# services/jwks_client.py - Enhanced error handling

class JWKSFetchError(Exception):
    """Raised when JWKS fetch fails and cache is empty"""
    pass

async def verify_rs256_token(self, token: str, kid: str) -> Optional[Dict[str, Any]]:
    """Verify RS256 JWT using JWKS key"""
    
    # Fetch key for this kid
    key = await self.get_key(kid)
    
    if key is None:
        # Check if this is a cache miss during JWKS outage
        if not self._keys:  # Empty cache = infrastructure failure
            logger.error(
                f"🚨 CRITICAL: JWKS cache empty, cannot verify RS256 tokens. "
                f"Last fetch error: {self._last_fetch_error}. "
                f"Auth provider may be unreachable."
            )
            # Emit metric for alerting
            from observability.alerts import emit_alert
            emit_alert(
                severity="critical",
                message="JWKS unavailable - RS256 validation blocked",
                context={"kid": kid, "error": self._last_fetch_error}
            )
            raise JWKSFetchError(f"JWKS unavailable: {self._last_fetch_error}")
        else:
            # Cache populated but kid not found = invalid token
            logger.warning(f"Unknown kid {kid} - token rejected (known kids: {list(self._keys.keys())})")
            return None  # Valid failure - unknown kid
    
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False},
            leeway=settings.jwt_clock_skew_leeway_seconds
        )
        logger.debug(f"✅ RS256 token verified for kid {kid}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.info(f"Token expired (kid {kid})")
        return None
    except JWTError as e:
        logger.warning(f"RS256 verification failed for kid {kid}: {e}")
        return None

# middleware/auth.py - Handle JWKS errors explicitly
async def decode_token(token: str) -> dict | None:
    """Decode and validate JWT (supports HS256 + RS256)"""
    
    # ... existing header parsing ...
    
    if alg == "RS256":
        try:
            payload = await jwks_client.verify_rs256_token(token, kid)
            return payload
        except JWKSFetchError as e:
            # Auth infrastructure failure - return 503, not 401
            logger.error(f"Auth provider unreachable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable"
            )
    elif alg == "HS256":
        # ... existing HS256 logic ...
        pass
```

### Testing Plan

```bash
# Test 1: Normal operation (JWKS reachable)
export SCHOLAR_AUTH_JWKS_URL="https://scholar-auth.../jwks.json"
# Should work: RS256 tokens validated

# Test 2: JWKS unreachable (scholar_auth down)
export SCHOLAR_AUTH_JWKS_URL="https://invalid-url.example.com/jwks.json"
# Should return 503 with clear error message

# Test 3: Valid JWKS but unknown kid
# Send token with kid="unknown-key-id"
# Should return 401 with "Unknown kid" message

# Test 4: JWKS cache recovery
# Start with invalid URL, then fix it
# Should recover after cache_ttl expires
```

---

## Load Test Plan - 300 RPS JWT Validation

### Test Script (k6)

See `load-tests/jwt_validation_load_test.js` for full implementation.

**Key Scenarios**:
1. HS256 token validation (existing baseline)
2. RS256 token validation (new feature)
3. Mixed workload (70% HS256, 30% RS256)
4. JWKS cache hit/miss ratio
5. Error scenarios (expired tokens, invalid signatures, unknown kids)

**Success Criteria**:
- P95 latency ≤ 120ms
- Error rate < 0.5%
- JWKS cache hit rate ≥ 95%
- No coroutine errors in logs
- Clear 503 responses when JWKS unavailable

### k6 Script Location
`load-tests/jwt_validation_load_test.js`

---

## Implementation Checklist for API Lead

- [ ] Fix Bug #1: Make `get_current_user()` and `decode_token()` async
- [ ] Fix Bug #2: Add explicit JWKS failure handling with 503 responses
- [ ] Update all call sites to `await decode_token()`
- [ ] Add `JWKSFetchError` exception class
- [ ] Integrate with observability/alerts for JWKS failures
- [ ] Write unit tests for both bugs
- [ ] Run k6 load test (300 rps, 15 min)
- [ ] Verify no runtime errors in logs
- [ ] Document JWKS failure recovery SOP

---

## Estimated Fix Time
- Bug #1: 30 minutes (straightforward async refactor)
- Bug #2: 45 minutes (error handling + alerting integration)
- Testing: 1 hour (unit tests + load test)
- **Total**: ~2.5 hours

---

## Next Steps

1. **Tonight (API Lead)**: Implement fixes per patch plans above
2. **Tomorrow AM**: Run k6 load test, validate P95 ≤ 120ms
3. **Nov 15**: Integration test with scholar_auth JWKS endpoint
4. **Nov 17**: Final canary test before go-live

---

**Report prepared by**: Agent3, Program Integrator  
**For**: CEO, Scholar AI Advisor  
**Distribution**: API Lead (A/DRI), Security Lead, SRE Lead
