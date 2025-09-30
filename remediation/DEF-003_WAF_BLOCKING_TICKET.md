# DEF-003: WAF Over-Blocking Authenticated Requests

**Severity:** 🔴 HIGH  
**Component:** WAF / Middleware Order  
**Owner:** Security Lead + Infra/DevOps  
**Target:** Day 1-2  
**Status:** 🟡 IN PROGRESS

---

## 📋 PROBLEM STATEMENT

Web Application Firewall (WAF) is blocking 100% of legitimate authenticated API requests with 403 errors (WAF_AUTH_001, WAF_SQLI_001). This makes the API completely unusable for authenticated users while properly blocking malicious traffic. Root cause: middleware execution order places WAF before authentication validation.

## 🔬 EVIDENCE

**Failed Authenticated Requests:**
```bash
# All return 403 WAF block despite valid JWT token
GET /api/v1/search?q=engineering
→ {"error":"Request blocked by Web Application Firewall","code":"WAF_AUTH_001","status":403}

GET /api/v1/scholarships
→ {"error":"Request blocked by Web Application Firewall","code":"WAF_AUTH_001","status":403}

POST /api/v1/eligibility/check
→ {"error":"Request blocked by Web Application Firewall","code":"WAF_SQLI_001","status":403}
```

**Test Results:**
- 0/10 authenticated search requests successful
- 429/403 errors on all protected endpoints
- Valid JWT tokens ignored by WAF

**Trace IDs:**
```
waf-1759239520, waf-1759239531, waf-1759239533
de9cb3cd-00a3-43c9-a104-65d64603b054
```

## 🎯 ACCEPTANCE CRITERIA (Launch Gate - Security)

**WAF Tuning Gate:**
- [ ] **0 false positives** on authenticated test suite (100% success rate)
- [ ] **Retain OWASP Top 10 protections** (SQL injection, XSS, etc.)
- [ ] **Explicit allow rules** for authenticated routes
- [ ] **Common JSON payloads pass** without blocking
- [ ] **Auth middleware executes before WAF**
- [ ] **Quick pen-test validates** attack protection maintained

## 🛠️ FIX PLAN

### Phase 1: Middleware Order Fix (30 min)

**Current (Broken) Order:**
```python
# main.py - BEFORE (WAF blocks before auth check)
app.add_middleware(WAFProtectionMiddleware)       # ❌ Executes FIRST
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TraceIDMiddleware)
app.add_middleware(AuthenticationMiddleware)      # ❌ Executes LAST
```

**Corrected Order:**
```python
# main.py - AFTER (Auth validates before WAF)
app.add_middleware(TraceIDMiddleware)             # 1. Trace ID first
app.add_middleware(AuthenticationMiddleware)      # 2. Auth second
app.add_middleware(RateLimitMiddleware)           # 3. Rate limit third
app.add_middleware(WAFProtectionMiddleware)       # 4. WAF last (with auth context)
```

**Rationale:**
1. **Trace ID**: Generate correlation ID for all requests
2. **Authentication**: Validate JWT and set user context
3. **Rate Limiting**: Apply limits based on authenticated user
4. **WAF**: Check for attacks with full auth context available

### Phase 2: WAF Allowlist for Authenticated Routes (1 hour)

```python
# middleware/waf_protection.py

class WAFProtectionMiddleware:
    def __init__(self):
        self.authenticated_routes = [
            r'^/api/v1/search',
            r'^/api/v1/scholarships',
            r'^/api/v1/eligibility',
            r'^/api/v1/recommendations',
            r'^/api/v1/interactions'
        ]
    
    async def __call__(self, request: Request, call_next):
        # Check if user is authenticated (set by AuthenticationMiddleware)
        user = request.state.user if hasattr(request.state, "user") else None
        
        # If authenticated, skip certain WAF checks for allowlisted routes
        if user and self._is_authenticated_route(request.path):
            # Authenticated users get relaxed WAF rules
            return await self._check_authenticated_request(request, call_next)
        else:
            # Unauthenticated: full WAF protection
            return await self._check_unauthenticated_request(request, call_next)
    
    def _is_authenticated_route(self, path: str) -> bool:
        import re
        return any(re.match(pattern, path) for pattern in self.authenticated_routes)
    
    async def _check_authenticated_request(self, request: Request, call_next):
        """Relaxed WAF for authenticated requests"""
        # Only check for severe attacks, allow common patterns
        severe_patterns = [
            r'(\bUNION\b.*\bSELECT\b)',  # SQL Union attacks
            r'(<script[^>]*>.*?</script>)',  # Direct script injection
            r'(eval\s*\()',  # JavaScript eval
            r'(document\.cookie)',  # Cookie theft attempts
        ]
        
        # Check query params and body
        query_string = str(request.url.query)
        
        for pattern in severe_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                logger.warning(f"WAF blocked authenticated request: {pattern}")
                return self._block_request("WAF_SEVERE_001")
        
        # Allow request to proceed
        return await call_next(request)
    
    async def _check_unauthenticated_request(self, request: Request, call_next):
        """Full WAF protection for unauthenticated requests"""
        # Existing strict WAF logic
        return await self._full_waf_check(request, call_next)
```

### Phase 3: JSON Payload Allowlist (30 min)

```python
# middleware/waf_protection.py

class WAFProtectionMiddleware:
    
    def __init__(self):
        # Allowlist common API patterns that might trigger false positives
        self.safe_json_patterns = [
            r'"gpa":\s*\d+\.\d+',              # GPA values
            r'"major":\s*"[^"]*"',             # Major field
            r'"scholarship_id":\s*"sch_\d+"',  # Scholarship IDs
            r'"user_profile":\s*\{',           # User profile objects
            r'"eligibility":\s*\{',            # Eligibility objects
        ]
    
    async def _check_json_body(self, request: Request) -> bool:
        """Check if JSON body is safe"""
        if request.headers.get("content-type") == "application/json":
            body = await request.body()
            body_str = body.decode()
            
            # Check if body matches safe patterns
            for pattern in self.safe_json_patterns:
                if re.search(pattern, body_str):
                    return True  # Safe pattern found
        
        return False  # Unknown pattern, proceed with caution
```

### Phase 4: Query Parameter Allowlist (1 hour)

```python
# middleware/waf_protection.py

class WAFProtectionMiddleware:
    
    def __init__(self):
        # Allowlist legitimate query patterns
        self.safe_query_patterns = {
            'q': r'^[a-zA-Z0-9\s\-_]+$',           # Search queries (alphanumeric + spaces)
            'page': r'^\d+$',                       # Page numbers
            'page_size': r'^\d+$',                  # Page size
            'sort': r'^[a-zA-Z_]+$',                # Sort fields
            'filter': r'^[a-zA-Z0-9,]+$',           # Filter values
        }
    
    def _check_query_params(self, request: Request) -> Tuple[bool, str]:
        """Validate query parameters against allowlist"""
        for param, value in request.query_params.items():
            # Check if param has allowlist pattern
            if param in self.safe_query_patterns:
                pattern = self.safe_query_patterns[param]
                if not re.match(pattern, value):
                    return False, f"Invalid {param} format"
            else:
                # Unknown param: apply strict validation
                if self._contains_attack_pattern(value):
                    return False, f"Attack pattern in {param}"
        
        return True, ""
```

### Phase 5: Attack Pattern Preservation (1 hour)

**OWASP Top 10 Protection (MUST MAINTAIN):**
```python
# middleware/waf_protection.py

class WAFProtectionMiddleware:
    
    def __init__(self):
        # Critical attack patterns (NEVER allowlist these)
        self.critical_patterns = {
            'sql_injection': [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bINSERT\b.*\bINTO\b)",
                r"(\bDELETE\b.*\bFROM\b)",
                r"(\bDROP\b.*\bTABLE\b)",
                r"(--\s*$)",  # SQL comments
                r"(;\s*DROP\s+)",
                r"(\bOR\b\s+['\"]?1['\"]?\s*=\s*['\"]?1)",
            ],
            'xss': [
                r'(<script[^>]*>.*?</script>)',
                r'(<iframe[^>]*>)',
                r'(javascript:)',
                r'(onerror\s*=)',
                r'(onload\s*=)',
            ],
            'path_traversal': [
                r'(\.\.\/)',
                r'(\.\.\\)',
                r'(%2e%2e%2f)',
            ],
            'command_injection': [
                r'(;\s*rm\s+-rf)',
                r'(\|\s*cat\s+)',
                r'(`.*`)',
                r'(\$\(.*\))',
            ]
        }
    
    def _contains_attack_pattern(self, value: str) -> bool:
        """Check if value contains attack patterns"""
        for category, patterns in self.critical_patterns.items():
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"WAF detected {category}: {pattern}")
                    return True
        return False
```

## 🧪 TESTING & VALIDATION

### Test Suite: Authenticated Requests (Must Pass)
```python
# tests/test_waf_authenticated.py
import pytest

class TestWAFAuthenticated:
    
    @pytest.fixture
    def auth_headers(self):
        # Login and get token
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_search_engineering(self, auth_headers):
        """Basic search should work"""
        response = requests.get(
            f"{BASE_URL}/api/v1/search?q=engineering",
            headers=auth_headers
        )
        assert response.status_code == 200, f"WAF blocked: {response.text}"
    
    def test_search_stem_pagination(self, auth_headers):
        """Search with pagination should work"""
        response = requests.get(
            f"{BASE_URL}/api/v1/search?q=stem&page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"WAF blocked: {response.text}"
    
    def test_eligibility_check_json(self, auth_headers):
        """JSON POST with GPA/major should work"""
        response = requests.post(
            f"{BASE_URL}/api/v1/eligibility/check",
            headers=auth_headers,
            json={
                "user_profile": {
                    "gpa": 3.5,
                    "major": "Computer Science",
                    "year": "Junior"
                },
                "scholarship_id": "sch_001"
            }
        )
        assert response.status_code == 200, f"WAF blocked: {response.text}"
    
    def test_list_scholarships(self, auth_headers):
        """List all scholarships should work"""
        response = requests.get(
            f"{BASE_URL}/api/v1/scholarships",
            headers=auth_headers
        )
        assert response.status_code == 200, f"WAF blocked: {response.text}"

# Run: pytest tests/test_waf_authenticated.py -v
# Expected: 100% pass rate (0 false positives)
```

### Test Suite: Attack Protection (Must Block)
```python
# tests/test_waf_attacks.py
import pytest

class TestWAFAttackProtection:
    
    def test_sql_injection_blocked(self):
        """SQL injection should be blocked"""
        payloads = [
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT NULL--"
        ]
        for payload in payloads:
            response = requests.get(f"{BASE_URL}/api/v1/search?q={payload}")
            assert response.status_code == 403, f"SQL injection not blocked: {payload}"
            assert "WAF" in response.text
    
    def test_xss_blocked(self):
        """XSS attempts should be blocked"""
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>"
        ]
        for payload in payloads:
            response = requests.get(f"{BASE_URL}/api/v1/search?q={payload}")
            assert response.status_code == 403, f"XSS not blocked: {payload}"
    
    def test_path_traversal_blocked(self):
        """Path traversal should be blocked"""
        response = requests.get(f"{BASE_URL}/api/v1/search?q=../../etc/passwd")
        assert response.status_code == 403

# Run: pytest tests/test_waf_attacks.py -v
# Expected: 100% block rate (attacks prevented)
```

## ✅ VERIFICATION CHECKLIST

**Day 1:**
- [ ] Middleware order corrected (Auth before WAF)
- [ ] Authenticated route allowlist implemented
- [ ] JSON payload patterns allowlisted
- [ ] Query parameter validation updated
- [ ] Test suite: 100% authenticated requests pass
- [ ] Test suite: 100% attack attempts blocked

**Day 2:**
- [ ] Penetration test on auth flows
- [ ] OWASP Top 10 validation
- [ ] Performance impact assessment
- [ ] WAF bypass attempts tested
- [ ] Security lead sign-off

## 📊 MONITORING

**WAF Metrics:**
```python
# Prometheus metrics
waf_requests_total = Counter('waf_requests_total', 'WAF requests', ['action', 'rule'])
waf_false_positives = Counter('waf_false_positives', 'WAF false positives', ['endpoint'])
waf_blocks = Counter('waf_blocks', 'WAF blocks', ['attack_type'])
```

**Alerts:**
```yaml
# alerts/waf.yml
- alert: WAFHighFalsePositiveRate
  expr: rate(waf_false_positives[5m]) > 0.01
  labels:
    severity: warning
  annotations:
    summary: "WAF blocking legitimate traffic"

- alert: WAFAttackSpike
  expr: rate(waf_blocks[5m]) > 10
  labels:
    severity: critical
  annotations:
    summary: "WAF detected attack spike"
```

## 🔄 ROLLBACK PLAN

If issues arise:
1. Revert middleware order to previous (document why)
2. Disable WAF temporarily (maintenance mode)
3. Re-enable with stricter allowlist
4. Gradual rollout of relaxed rules

## 📁 ARTIFACTS

- [ ] Middleware configuration diff
- [ ] Test suite results (100% pass proof)
- [ ] Penetration test report
- [ ] OWASP Top 10 validation report
- [ ] Security lead sign-off

---

**ETA:** Day 1-2 (4 hours total)  
**Risk:** Medium (requires careful tuning)  
**Dependencies:** None (can start immediately)
