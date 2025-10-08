# Option B Deployment Guide - Replit Bypass Workaround

**Status**: STANDBY (Deploy only if Option A not resolved by T+6:20)  
**Incident**: WAF-BLOCK-20251008  
**Priority**: P0 Emergency Fallback

---

## WHEN TO DEPLOY

**Deploy Option B ONLY if**:
- Current time >= T+6:20 (2 hours after P0 declaration)
- Replit support has not responded OR fix not implemented
- External GET requests still returning 403 Forbidden
- Business impact continues (SEO blocked, students cannot browse)

**DO NOT deploy if**:
- Replit has responded with ETA <30 minutes
- Infrastructure fix is in progress
- External endpoints working (validate first)

---

## PRE-DEPLOYMENT CHECKLIST

- [ ] Confirm current time >= T+6:20 (auto-fallback trigger)
- [ ] Verify external endpoints still failing:
  ```bash
  curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
  # Should return 403 if deploying Option B
  ```
- [ ] Confirm Replit support ticket filed (#WAF-BLOCK-20251008)
- [ ] CEO approval for Option B deployment
- [ ] Security Lead approval for bypass implementation
- [ ] QA test environment available for validation

---

## DEPLOYMENT STEPS

### Step 1: Generate Bypass Token (5 minutes)

```bash
# Generate secure random token (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: "dGhpcyBpcyBhIHNlY3VyZSByYW5kb20gdG9rZW4K"
```

**Save this token securely** - you'll add it to Replit Secrets next.

---

### Step 2: Add Token to Replit Secrets (2 minutes)

1. Open Replit workspace
2. Click "Secrets" (lock icon) in left sidebar
3. Add new secret:
   - **Key**: `REPLIT_BYPASS_TOKEN`
   - **Value**: (paste generated token from Step 1)
4. Save secret

---

### Step 3: Update Application Settings (3 minutes)

Add Option B configuration to `config/settings.py`:

```python
# At top of file, add:
from config.settings_bypass import (
    REPLIT_BYPASS_ENABLED,
    REPLIT_BYPASS_TOKEN,
    REPLIT_BYPASS_LOG_LEVEL,
    REPLIT_BYPASS_METRICS_ENABLED
)

# In Settings class, add:
class Settings(BaseSettings):
    # ... existing settings ...
    
    # OPTION B: Replit Infrastructure Bypass (Emergency Workaround)
    replit_bypass_enabled: bool = Field(
        default=False,
        description="Emergency bypass for Replit WAF blocking (Incident WAF-BLOCK-20251008)"
    )
    replit_bypass_token: str = Field(
        default="",
        description="Replit infrastructure auth token (store in Secrets)"
    )
```

---

### Step 4: Add Middleware to Application (5 minutes)

In `main.py`, add bypass middleware AFTER WAF but BEFORE route handlers:

```python
# After existing imports, add:
from middleware.replit_bypass import ReplitInfrastructureBypass

# After WAF middleware (around line 267), add:
# OPTION B: Emergency Replit Infrastructure Bypass (Incident WAF-BLOCK-20251008)
if settings.replit_bypass_enabled:
    logger.warning("🚨 DEPLOYING OPTION B: Replit bypass middleware active")
    app.add_middleware(
        ReplitInfrastructureBypass,
        enabled=settings.replit_bypass_enabled
    )
else:
    logger.info("Option B bypass middleware loaded but disabled (standby)")
```

---

### Step 5: Enable Feature Flag (1 minute)

**Option A: Environment Variable** (Preferred for feature flag)
1. Open Replit Secrets
2. Add new secret:
   - **Key**: `REPLIT_BYPASS_ENABLED`
   - **Value**: `true`
3. Save

**Option B: Code Change** (If env var not working)
In `config/settings.py`:
```python
replit_bypass_enabled: bool = Field(
    default=True,  # Change from False to True
    ...
)
```

---

### Step 6: Deploy and Restart (2 minutes)

```bash
# Restart FastAPI server to load new config
# Replit will auto-restart on file changes, or manually:
# Click "Stop" then "Run" in Replit
```

Watch startup logs for:
```
🚨 REPLIT BYPASS ENABLED: This is a temporary workaround.
Remove once Replit WAF configured properly.
Paths: ['/api/v1/scholarships', '/api/v1/search']
```

---

### Step 7: Validation (10 minutes)

**Test 1: External Access**
```bash
# Should now return 200 OK (no longer blocked)
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

# Expected response:
# HTTP/2 200 OK
# X-Replit-Bypass: active
# X-Bypass-Reason: infrastructure_waf_workaround
```

**Test 2: Search Endpoint**
```bash
curl -v "https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=test"

# Expected: HTTP/2 200 OK with search results
```

**Test 3: Security Preserved**
```bash
# POST should still require auth (bypass only for GET)
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
# Expected: 401 Unauthorized or 403 Forbidden
```

**Test 4: Monitor Logs**
Check application logs for bypass activity:
```
🔓 REPLIT BYPASS: GET /api/v1/scholarships | IP: 1.2.3.4 | Scope: public_discovery
✅ REPLIT BYPASS SUCCESS: /api/v1/scholarships | 45.23ms
```

---

## POST-DEPLOYMENT MONITORING

### Metrics to Track (Hourly)

1. **Bypass Usage**:
   - Total bypass count
   - Paths accessed via bypass
   - IP distribution

2. **Success Rate**:
   - External 2xx rate on /scholarships and /search
   - Should jump from 0% to >99%

3. **Performance**:
   - P95 latency remains <120ms
   - No degradation from bypass logic

4. **Security**:
   - POST/PUT/PATCH still blocked (no bypass for mutations)
   - No unauthorized access attempts
   - Token validation working (check for rejected bypasses in logs)

### Dashboards

Access bypass statistics:
```bash
# Get bypass stats via internal endpoint
curl http://localhost:5000/_internal/bypass/stats
```

---

## ROLLBACK PLAN (If Option B Fails)

**Rollback Steps** (5 minutes):
1. Set `REPLIT_BYPASS_ENABLED=false` in Secrets
2. Restart application
3. Verify bypass disabled in logs
4. Escalate to CEO for next steps

---

## REMOVAL PLAN (After Replit Fixes Infrastructure)

**When to Remove**:
- Replit confirms infrastructure WAF updated
- External endpoints return 200 OK WITHOUT bypass headers
- Test period complete (24 hours stability)

**Removal Steps**:
1. Disable feature flag: `REPLIT_BYPASS_ENABLED=false`
2. Monitor for 1 hour - confirm external access still works
3. Remove bypass middleware from `main.py`
4. Remove bypass files:
   - `middleware/replit_bypass.py`
   - `config/settings_bypass.py`
   - `OPTION_B_DEPLOYMENT_GUIDE.md`
5. Remove bypass config from `config/settings.py`
6. Remove `REPLIT_BYPASS_TOKEN` from Secrets
7. Document lesson learned in incident postmortem

---

## SECURITY NOTES

### Token Management
- **Rotation**: Rotate token daily (generate new, update Secrets)
- **Storage**: NEVER commit token to git - Secrets only
- **Scope**: Token valid ONLY for GET on 2 endpoints
- **Audit**: All bypass usage logged with IP and timestamp

### Compliance
- Token scoped to read-only public data (no PII)
- TLS encryption in transit (HTTPS)
- Rate limiting preserved (20 req/min)
- Audit trail for all bypass usage
- Feature flag for instant disable

### Attack Surface
- Bypass logic adds ~0.5ms latency (negligible)
- Token validation uses constant-time comparison (timing attack protection)
- Failed validation attempts logged for security monitoring
- No wildcard paths (strict matching only)

---

## TROUBLESHOOTING

### Issue: Bypass not activating
**Check**:
1. Feature flag enabled? (`REPLIT_BYPASS_ENABLED=true`)
2. Token configured? (Check Secrets for `REPLIT_BYPASS_TOKEN`)
3. Middleware added? (Check `main.py` for `ReplitInfrastructureBypass`)
4. Server restarted? (Repl must reload config)

**Logs to check**:
```
🚨 REPLIT BYPASS ENABLED: This is a temporary workaround.
```

### Issue: Still getting 403
**Check**:
1. Request includes `X-Replit-Internal-Auth` header with valid token
2. Path exactly matches `/api/v1/scholarships` or `/api/v1/search`
3. Method is GET (POST/PUT/PATCH not allowed)
4. Application logs show bypass attempt

**Logs to check**:
```
⚠️ REPLIT BYPASS REJECTED: Reason: Invalid or missing token
```

### Issue: Bypass working but performance degraded
**Check**:
1. P95 latency in dashboards
2. Bypass logic timing (should be <1ms overhead)
3. Rate limiting not hitting ceiling
4. Database connections healthy

---

## CONTACTS

**Incident Commander**: EngOps Lead  
**Security Review**: Security Lead  
**Deployment Support**: App Team  
**Escalation**: CEO

---

**REMEMBER**: Option B is a temporary workaround. Remove immediately once Replit fixes infrastructure WAF configuration.

**Incident Tracker**: See `P0_INCIDENT_TRACKER.md` for full timeline and status.
