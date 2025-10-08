# P0 INCIDENT TRACKER - Replit WAF Blocking Public Endpoints

**Incident ID**: WAF-BLOCK-20251008  
**Severity**: P0 - Customer Impacting  
**Declared**: 2025-10-08 T+4:20  
**Commander**: EngOps Lead  
**Status**: 🔴 **ACTIVE**

---

## TIMELINE & CHECKPOINTS

### T+4:20 - Incident Declared
- ✅ P0 incident declared
- ✅ Root cause identified: Replit infrastructure WAF blocking
- ✅ Documentation complete: `RCA_PHASE1_FINDINGS.md`
- ✅ WAF configuration check: No user access (infrastructure-managed)

### T+4:35 - Executive Decisions Approved (CEO)
- ✅ **P0 Support Ticket**: Approved to file immediately
- ✅ **Fallback Timer**: Approved - 2-hour countdown started
- ✅ **Paid Traffic**: Approved pause for affected endpoints
- ✅ **Option B**: Pre-approved to auto-deploy at T+6:20
- ✅ **Escalation Path**: Documented for Option B failure scenarios
- 🔄 **ACTION**: Filing P0 support ticket NOW

### T+4:35 - Initial Response (Target: 15min)
- **IF WAF Access Available**:
  - [ ] Add allow rules for GET /api/v1/scholarships
  - [ ] Add allow rules for GET /api/v1/search
  - [ ] Validate with curl reproducers
  - [ ] Confirm external 200 OK responses
  
- **IF No WAF Access**:
  - [ ] File P0 Replit support ticket (template below)
  - [ ] Attach RCA_PHASE1_FINDINGS.md
  - [ ] Include curl reproducers and header captures
  - [ ] Start 2-hour fallback timer

### T+6:20 - Auto-Fallback Checkpoint (Target: 2 hours)
- **IF Option A NOT Resolved**:
  - [ ] Execute Option B: Implement Replit-specific auth bypass
  - [ ] Scope to read-only for scholarships/search only
  - [ ] Store token in Replit Secrets
  - [ ] Add strict path matching + audit logging
  - [ ] Deploy behind feature flag
  - **ETA**: 1 hour implementation + testing

### T+8:20 - Option B Validation (Target: 4 hours)
- **IF Option B Deployed**:
  - [ ] Validate external 200 OK responses
  - [ ] Monitor KPIs (error rate, conversion, latency)
  - [ ] Keep P0 ticket open with Replit
  - [ ] Request WAF exception ETA from Replit
  - [ ] Plan Option B removal once Option A fixed

---

## IMPACT ASSESSMENT

### Affected Endpoints
- ❌ **GET /api/v1/scholarships** - 100% external failure rate
- ❌ **GET /api/v1/search** - 100% external failure rate
- ✅ **GET /api/v1/credits/packages** - Working (different WAF rule)
- ✅ **Localhost** - All endpoints working (127.0.0.1:5000)

### Business Impact
- 🔴 **SEO**: Googlebot/Bingbot blocked from indexing scholarships
- 🔴 **Conversion**: External users cannot browse scholarships
- 🔴 **CAC**: Paid traffic to blocked endpoints wasting spend
- ✅ **Internal**: Dashboard and admin tools functional (localhost)

### Metrics Tracking (Hourly)
- [ ] External 403 rate on /scholarships and /search
- [ ] Student acquisition funnel conversion rate
- [ ] Error budget burn vs 99.9% uptime SLO
- [ ] SEO landing page bounce rate
- [ ] Support ticket volume

---

## REMEDIATION OPTIONS

### **Option A: Replit Infrastructure WAF** (In Progress)
**Owner**: EngOps Lead + Replit Support  
**ETA**: 30min (if access) OR 2-4 hours (support ticket)  
**Status**: 🔄 Checking WAF dashboard access

**Required Changes**:
```yaml
# Replit WAF Configuration (Google Cloud Armor)
rules:
  - path: /api/v1/scholarships
    method: GET
    action: ALLOW
    description: Public scholarship discovery endpoint
  
  - path: /api/v1/search
    method: GET
    action: ALLOW
    description: Public search endpoint for students
```

**Validation**:
```bash
# Should return 200 OK after fix
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=test
```

---

### **Option B: Application Workaround** (Fallback - T+6:20)
**Owner**: API Lead  
**ETA**: 1 hour implementation + testing  
**Status**: ⏳ Standby (triggers if Option A not resolved by T+6:20)

**Implementation** (Only if Option A fails):
```python
# middleware/replit_bypass.py
class ReplitInfrastructureBypass:
    """
    Emergency bypass for Replit infrastructure WAF blocking.
    TEMPORARY: Remove once Replit configures proper WAF rules.
    """
    
    ALLOWED_PATHS = {
        "/api/v1/scholarships": {"methods": ["GET"], "scope": "public_discovery"},
        "/api/v1/search": {"methods": ["GET"], "scope": "public_search"}
    }
    
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Check if this is a public endpoint requiring bypass
        if path in self.ALLOWED_PATHS:
            config = self.ALLOWED_PATHS[path]
            
            if method in config["methods"]:
                # Validate Replit infrastructure token
                replit_token = request.headers.get("X-Replit-Internal-Auth")
                
                if replit_token == settings.REPLIT_INTERNAL_TOKEN:
                    # Infrastructure pre-authorized
                    logger.info(f"Replit bypass: {method} {path}")
                    request.state.replit_bypass = True
                    return await call_next(request)
        
        return await call_next(request)
```

**Security Requirements**:
- ✅ Token scoped to read-only endpoints only
- ✅ Strict path matching (no wildcards)
- ✅ Daily token rotation via Replit Secrets
- ✅ Audit logging for all bypass usage
- ✅ Rate limiting preserved
- ✅ No PII exposure (search results only)
- ✅ Feature flag for instant removal

---

## REPLIT SUPPORT TICKET (Use if no WAF access)

**Subject**: P0: Replit WAF (Google Frontend) incorrectly blocking public GET endpoints

**Priority**: P0 - Customer Impacting

**Project Details**:
- **Repl Name**: scholarship-api
- **Repl Owner**: jamarrlmayes
- **Production URL**: https://scholarship-api-jamarrlmayes.replit.app
- **Environment**: Production deployment

**Issue Description**:

External GET requests to our public scholarship discovery endpoints are being blocked by Replit's infrastructure WAF (Google Frontend) with 403 Forbidden responses. This breaks core student discovery functionality and SEO indexing.

**Affected Endpoints**:
- GET /api/v1/scholarships (scholarship listing)
- GET /api/v1/search (scholarship search)

**Evidence**:

1. **Response Headers** (External requests):
```
HTTP/2 403
server: Google Frontend
via: 1.1 google
x-waf-rule: WAF_AUTH_001
x-waf-status: blocked
```

2. **Application Behavior**:
- ✅ Localhost: All endpoints return 200 OK
- ✅ Localhost + proxy headers: 200 OK (headers not the issue)
- ❌ External requests: 403 Forbidden (blocked before reaching app)
- ✅ GET /api/v1/credits/packages: 200 OK (different WAF rule)

3. **Application Logs**: ZERO WAF block entries for external requests, proving blocks occur upstream at Google Frontend layer, not in application code.

**Root Cause**:

Replit infrastructure WAF is enforcing authentication requirements on endpoints that our application intends to be publicly accessible for student browsing and SEO indexing. Application-level WAF correctly allows all GET requests (verified via extensive testing).

**Reproduction**:

```bash
# FAILS (External - blocked by Replit WAF)
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
# Returns: HTTP/2 403 (Google Frontend)

# WORKS (Localhost - proves app code correct)
curl -v http://localhost:5000/api/v1/scholarships
# Returns: HTTP/1.1 200 OK
```

**Requested Fix**:

Please add WAF exceptions at the Replit infrastructure level for:
- **GET /api/v1/scholarships** (public scholarship discovery)
- **GET /api/v1/search** (public search for students)

POST/PUT/PATCH methods should continue to require authentication (security preserved).

**Attachments**:
- RCA_PHASE1_FINDINGS.md (full root cause analysis with sequence diagrams)
- Header captures and curl reproducers
- Middleware ordering verification + unit tests
- Application log evidence

**Business Impact**:
- SEO: Search engine crawlers cannot index scholarships
- Conversion: Students cannot browse available scholarships
- Urgency: P0 customer-facing issue blocking core user journey

**Request**: Please confirm receipt and provide ETA for WAF configuration update.

---

## ACCOUNTABILITY

| Role | Owner | Responsibilities |
|------|-------|------------------|
| Incident Commander | EngOps Lead | Overall incident coordination, timeline enforcement |
| Replit Liaison | Partnerships/Support | Support ticket filing, escalation, ETA tracking |
| QA Validation | App Team | Curl test execution, external validation |
| Communications | Marketing | User messaging, paid campaign pause/resume |
| Security Review | Security Lead | Option B security validation (if needed) |

---

## COMMUNICATIONS PLAN

### Internal Status Updates
- **Channel**: #incidents-p0
- **Frequency**: Every 30 minutes until resolved
- **Next Update**: T+4:50 (in 30 minutes)

### User-Facing Messaging
- **Status Page**: "Temporary access issue for scholarship browsing - investigating"
- **SEO Crawlers**: 503 with Retry-After header (if extended)
- **Paid Traffic**: Paused to broken endpoints until resolved

### Post-Incident
- **RCA Distribution**: Stakeholders, engineering team
- **Lessons Learned**: 30min session within 24 hours
- **Prevention**: Document Replit WAF configuration process

---

## SUCCESS CRITERIA

- ✅ External GET /api/v1/scholarships returns 200 OK
- ✅ External GET /api/v1/search returns 200 OK
- ✅ SEO crawlers can index scholarships (200/304 responses)
- ✅ Conversion funnel restored to baseline
- ✅ POST/PUT/PATCH still require authentication (security intact)
- ✅ P95 latency remains <120ms
- ✅ Error rate <0.1%

---

## NEXT ACTIONS (Immediate - T+4:20)

1. **🔄 IN PROGRESS**: Search Replit documentation for WAF configuration access
2. **PENDING**: File P0 support ticket if no WAF dashboard access
3. **PENDING**: Start 2-hour fallback timer (T+6:20 checkpoint)
4. **PENDING**: Post internal status update (#incidents-p0)
5. **PENDING**: Pause paid traffic to /scholarships and /search endpoints

---

## LONG-TERM PREVENTION

Per CEO directive:
- Define exit ramp for mission-critical public endpoints
- Consider reverse proxy under our control for SEO-critical paths
- Multi-provider front door to reduce vendor WAF lock-in risk
- Document Replit platform constraints in architecture decisions
