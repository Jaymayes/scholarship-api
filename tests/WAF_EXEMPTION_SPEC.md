# WAF Authentication Exemption Specification
**For:** Security Lead + Backend Lead  
**SLA:** T+3h (4-hour deadline)  
**Priority:** P0 BLOCKER  
**Executive Directive:** CEO 24-hour conditional launch plan

---

## Problem Statement

The Web Application Firewall (WAF) SQL injection detection is blocking legitimate authentication JSON payloads, resulting in 100% authentication failure rate. All login attempts and API key creation requests return `WAF_SQLI_001` (403 Forbidden).

**Impact:**
- No user can log in
- No API keys can be created
- All auth-dependent features untestable (13 tests blocked)
- Total system failure for user-facing operations

---

## Root Cause Analysis

**WAF Rule:** `middleware/waf_protection.py` - SQL injection pattern detection  
**Trigger:** JSON authentication payloads containing `username`, `password`, and similar fields trigger overly broad regex patterns

**Evidence:**
```bash
$ curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

Response:
{
  "error": "Request blocked by Web Application Firewall",
  "code": "WAF_SQLI_001",
  "status": 403,
  "timestamp": 1759583192
}
```

---

## Endpoints Requiring Exemption

### Authentication Endpoints (All POST methods)
1. `/api/v1/auth/login` - OAuth2 password flow
2. `/api/v1/auth/login-simple` - JSON login
3. `/api/v1/auth/logout` - Session termination
4. `/api/v1/auth/check` - Auth status check (GET)

### API Key Management
5. `/api/v1/launch/commercialization/api-keys` - API key creation

### Pattern for Exemption
Recommend exempting the entire auth prefix:
- `/api/v1/auth/*` (all methods)
- `/api/v1/launch/commercialization/api-keys` (POST only)

---

## Implementation Approach (Least-Privilege)

### Option 1: Endpoint-Specific Exemption (RECOMMENDED)

**File:** `middleware/waf_protection.py`  
**Location:** Line ~313 in `_detect_sql_injection()` method

**Current Code:**
```python
# SQL injection exempt endpoints (legitimate content may contain SQL keywords)
sql_exempt_paths = {
    "/partner/register",  # Partner registration may contain text like "select scholarships"
    "/api/v1/launch/simulate/traffic"
}

# Add orchestration bypass paths (legitimate JSON from Command Center)
sql_exempt_paths.update(self._waf_bypass_paths)

if request.url.path in sql_exempt_paths:
    logger.debug(f"WAF: Allowing SQL-exempt endpoint - {request.method} {request.url.path}")
    return False
```

**Recommended Change:**
```python
# SQL injection exempt endpoints (legitimate content may contain SQL keywords)
sql_exempt_paths = {
    "/partner/register",
    "/api/v1/launch/simulate/traffic",
    # CEO DIRECTIVE: Auth endpoints exempt from SQL injection checks (T+3h gate)
    # Authentication JSON payloads contain "password", "username" which trigger false positives
    "/api/v1/auth/login",
    "/api/v1/auth/login-simple",
    "/api/v1/auth/logout",
    "/api/v1/auth/check",
    "/api/v1/launch/commercialization/api-keys"
}

# Add orchestration bypass paths
sql_exempt_paths.update(self._waf_bypass_paths)

if request.url.path in sql_exempt_paths:
    logger.info(f"WAF: Auth endpoint bypassed - {request.method} {request.url.path}")
    return False
```

### Option 2: Prefix-Based Exemption (ALTERNATIVE)

**If auth endpoints expand frequently:**
```python
# Check for auth prefix exemption
auth_prefixes = {"/api/v1/auth/"}
if any(request.url.path.startswith(prefix) for prefix in auth_prefixes):
    logger.info(f"WAF: Auth endpoint bypassed - {request.method} {request.url.path}")
    return False
```

---

## Security Considerations

### What's Preserved:
- ✅ SQL injection protection on all non-auth endpoints
- ✅ XSS protection (unchanged)
- ✅ Path traversal protection (unchanged)
- ✅ Command injection protection (unchanged)
- ✅ IP reputation checks (if implemented)
- ✅ Rate limiting on auth endpoints (via separate middleware)

### Compensating Controls:
1. **Rate Limiting:** Auth endpoints already protected by rate limiting middleware
2. **JWT Validation:** Subsequent requests validated via JWT tokens
3. **Database Parameterization:** SQLAlchemy ORM prevents SQL injection at data layer
4. **Input Validation:** Pydantic models validate auth request structure
5. **Logging:** Auth failures logged for monitoring and forensics

### Risk Assessment:
**Risk Level:** LOW  
**Justification:**
- Auth endpoints use parameterized queries (SQLAlchemy ORM)
- Credentials hashed with bcrypt before database interaction
- Rate limiting prevents brute force attempts
- No raw SQL execution in authentication code paths
- Attack surface limited to specific exempted endpoints only

---

## Testing Requirements (Acceptance Criteria)

### 1. Positive Tests (Must Pass)
```bash
# Test 1: Login with valid credentials
curl -X POST http://localhost:5000/api/v1/auth/login-simple \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
# Expected: 200 OK with JWT token

# Test 2: Login with invalid credentials
curl -X POST http://localhost:5000/api/v1/auth/login-simple \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrong"}'
# Expected: 401 Unauthorized (not 403 WAF block)

# Test 3: API key creation
curl -X POST http://localhost:5000/api/v1/launch/commercialization/api-keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "developer", "label": "test-key"}'
# Expected: 200 OK with API key (or appropriate auth error, NOT WAF block)
```

### 2. Negative Tests (Must Still Block)
```bash
# Test 4: SQL injection on search endpoint (should still block)
curl "http://localhost:5000/api/v1/search?query=' OR '1'='1" \
  -H "X-API-Key: test"
# Expected: 403 WAF_SQLI_001 (blocking still active)

# Test 5: XSS on non-auth endpoint (should still block)
curl "http://localhost:5000/api/v1/search?query=<script>alert('xss')</script>" \
  -H "X-API-Key: test"
# Expected: 403 WAF_XSS_001 (blocking still active)
```

### 3. Soak Test (30 minutes)
```bash
# Simulate 1000 login attempts over 30 minutes
for i in {1..1000}; do
  curl -s -X POST http://localhost:5000/api/v1/auth/login-simple \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}' > /dev/null
  sleep 1.8
done

# Acceptance: ≥99.5% success rate, 0 WAF_SQLI_001 errors on auth endpoints
```

---

## Deployment Plan

### Step 1: Code Change (15 minutes)
- Update `middleware/waf_protection.py` per Option 1 recommendation
- Add comment referencing CEO directive and T+3h gate

### Step 2: Local Testing (30 minutes)
- Run positive tests (login, API key creation)
- Run negative tests (SQLi, XSS on non-auth endpoints)
- Verify logs show "Auth endpoint bypassed" messages

### Step 3: Staging Deployment (30 minutes)
- Deploy to staging environment
- Run full test suite (positive + negative)
- Monitor for any unexpected WAF triggers

### Step 4: Production Deployment (15 minutes)
- Deploy to production via workflow restart
- Monitor first 100 login attempts in real-time
- Watch for any anomalies in error rates

### Step 5: Soak Test (30 minutes)
- Run 30-minute authentication soak test
- Target: ≥99.5% success rate, 0 WAF false positives
- Monitor application logs and metrics dashboards

**Total Time Estimate:** 2 hours (within 4-hour SLA)

---

## Rollback Plan

**If auth success rate < 99.5% or other issues arise:**

1. Revert code change in `middleware/waf_protection.py`
2. Restart workflow
3. Escalate to CEO for launch delay decision
4. Alternative: Temporarily set `enable_block_mode=False` in WAF middleware (NOT RECOMMENDED - loses all protections)

**Rollback RTO:** < 10 minutes

---

## Monitoring and Alerting

### New Metrics to Add:
1. `auth_waf_bypasses_total` - Counter for auth endpoint WAF bypasses
2. `auth_success_rate` - Gauge for login success percentage
3. `auth_waf_false_positives` - Counter for any remaining false positives

### Alert Thresholds:
- **Critical:** Auth success rate < 99.5% for 5 minutes
- **Warning:** Auth WAF false positives > 0 in 15 minutes
- **Info:** Auth endpoint WAF bypass rate change > 50%

---

## Post-Implementation Validation

### ✅ Checklist:
- [ ] Positive tests: 100% pass (login, API key creation successful)
- [ ] Negative tests: 100% pass (SQLi/XSS still blocked on non-auth endpoints)
- [ ] 30-minute soak test: ≥99.5% auth success rate
- [ ] Logs confirm "Auth endpoint bypassed" messages
- [ ] Zero WAF_SQLI_001 errors on auth endpoints
- [ ] Non-auth endpoints still show WAF protection active
- [ ] Monitoring dashboards updated with new metrics
- [ ] Alert rules configured and tested

---

## Owner and Timeline

**Primary Owner:** Security Lead  
**Supporting Owner:** Backend Lead  
**SLA:** T+3h (4 hours from directive issuance)  
**Checkpoint:** T+2h status update required  
**Executive Review:** T+3h Go/No-Go gate

**Escalation Path:**
- If blocked: Escalate to CEO immediately
- If delayed: Notify CEO with revised ETA
- If alternative approach needed: Consult with CEO before proceeding

---

**Document Status:** READY FOR IMPLEMENTATION  
**Last Updated:** 2025-10-04 - Pre-Launch Sprint  
**Approval:** Awaiting Security Lead acceptance
