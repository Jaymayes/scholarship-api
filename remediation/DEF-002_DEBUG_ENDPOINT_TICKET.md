# DEF-002: Debug Configuration Endpoint Exposed

**Severity:** 🔴 CRITICAL (Security)  
**Component:** Security / API Endpoints  
**Owner:** Backend Lead + Security Lead (verification)  
**Target:** Day 0 (TODAY - Immediate)  
**Status:** 🔴 URGENT

---

## 📋 PROBLEM STATEMENT

Debug endpoint `/_debug/config` is publicly accessible in production, leaking sensitive internal configuration including JWT secrets, database details, and internal architecture. This is a **critical information disclosure vulnerability** that enables reconnaissance for targeted attacks.

## 🔬 EVIDENCE

**Exposed Endpoint:** `/_debug/config`

**Information Leaked:**
```json
{
  "environment": "development",
  "debug_mode": true,
  "jwt": {
    "algorithm": "HS256",
    "secret_configured": true,
    "secret_length": 86  // ⚠️ LEAKED
  },
  "database": {
    "type": "PostgreSQL",
    "configured": true
  },
  "replit_env": {
    "repl_id": "13ce5ef8-ca85-4a91-a0cc-9618b979781c",  // ⚠️ LEAKED
    "repl_owner": "jamarrlmayes"  // ⚠️ LEAKED
  },
  "rate_limiting": {
    "backend_type": "in-memory fallback (Redis unavailable)",  // ⚠️ LEAKED
    "per_minute_limit": 200
  }
}
```

**cURL Reproduction:**
```bash
curl -s https://scholarship-api-jamarrlmayes.replit.app/_debug/config | jq
```

## 🎯 ACCEPTANCE CRITERIA (Launch Gate - Security)

- [x] **No public debug endpoints** in any environment
- [ ] `/_debug/config` returns 401/403 without admin authentication
- [ ] Comprehensive audit confirms no other debug/admin endpoints exposed
- [ ] Security lead sign-off with penetration test verification
- [ ] All environments (dev, staging, prod) validated

## 🛠️ FIX PLAN

### Option 1: Remove Endpoint Entirely (RECOMMENDED - 15 min)

```python
# routers/debug.py - DELETE THIS FILE
# OR comment out the entire router

# main.py - Remove debug router registration
# BEFORE:
# app.include_router(debug.router)

# AFTER:
# app.include_router(debug.router)  # REMOVED FOR SECURITY
```

### Option 2: Require Admin Authentication (30 min)

```python
# routers/debug.py
from fastapi import APIRouter, Depends
from middleware.auth import require_auth, User

router = APIRouter(prefix="/_debug", tags=["Debug"])

# Add admin role check
def require_admin(current_user: User = Depends(require_auth)) -> User:
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

@router.get("/config")
async def debug_config(current_user: User = Depends(require_admin)):
    """Debug configuration (admin only)"""
    # ... existing code with audit logging
    logger.warning(
        f"DEBUG_CONFIG_ACCESS",
        extra={
            "user_id": current_user.user_id,
            "ip": request.client.host,
            "timestamp": datetime.utcnow()
        }
    )
    return config_data
```

### Option 3: Environment-Based (Best Practice - 45 min)

```python
# routers/debug.py
from config.settings import settings

# Only register in development
if settings.environment == "development":
    @router.get("/config")
    async def debug_config(current_user: User = Depends(require_admin)):
        # ... existing code
else:
    # Production: endpoint doesn't exist
    pass

# OR use conditional router registration
# main.py
if settings.environment == "development":
    app.include_router(debug.router)
```

## 🔍 COMPREHENSIVE DEBUG ENDPOINT AUDIT

**Scan for Other Debug/Admin Endpoints:**
```bash
# Search for debug endpoints
grep -r "/_debug\|/debug\|/_admin\|/admin" routers/ --include="*.py"

# Search for sensitive config endpoints
grep -r "config\|settings\|env" routers/ --include="*.py" | grep -E "@router\.(get|post)"

# Check for environment leaks
grep -r "os.environ\|settings\|\.env" routers/ --include="*.py"
```

**Expected Debug Endpoints to Audit:**
- `/_debug/config` ← **FIX THIS**
- `/_debug/metrics` ← Check if exposed
- `/_debug/health` ← Check if exposed
- `/admin/*` ← Check all admin routes
- `/internal/*` ← Check all internal routes

**Security Checklist:**
```python
# Create comprehensive scan
import requests

BASE_URL = "https://scholarship-api-jamarrlmayes.replit.app"

# Common debug/admin paths
debug_paths = [
    "/_debug/config",
    "/_debug/metrics", 
    "/_debug/health",
    "/_debug/logs",
    "/debug",
    "/admin",
    "/admin/config",
    "/.env",
    "/config",
    "/settings",
    "/internal/config",
    "/system/info"
]

for path in debug_paths:
    response = requests.get(f"{BASE_URL}{path}")
    if response.status_code == 200:
        print(f"🚨 EXPOSED: {path} - Status: {response.status_code}")
    elif response.status_code in [401, 403]:
        print(f"✅ PROTECTED: {path} - Status: {response.status_code}")
    else:
        print(f"ℹ️  {path} - Status: {response.status_code}")
```

## 🔐 ADDITIONAL SECURITY HARDENING

**1. Response Header Sanitization:**
```python
# middleware/security_headers.py
@app.middleware("http")
async def sanitize_debug_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Remove debug headers in production
    if settings.environment == "production":
        response.headers.pop("X-Debug-Mode", None)
        response.headers.pop("X-Repl-ID", None)
        response.headers.pop("X-Environment", None)
    
    return response
```

**2. Error Response Sanitization:**
```python
# middleware/error_handling.py
def sanitize_error_response(exc: Exception) -> dict:
    if settings.environment == "production":
        # Generic error message
        return {
            "error": "An error occurred",
            "trace_id": generate_trace_id(),
            "timestamp": datetime.utcnow()
        }
    else:
        # Detailed error in development
        return {
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
```

**3. Audit Logging for Sensitive Access:**
```python
# Log all access to sensitive endpoints
@router.get("/config")
async def debug_config(request: Request, current_user: User = Depends(require_admin)):
    # Security audit log
    security_logger.warning(
        "SENSITIVE_ENDPOINT_ACCESS",
        extra={
            "endpoint": "/_debug/config",
            "user_id": current_user.user_id,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
            "timestamp": datetime.utcnow().isoformat(),
            "action": "config_access"
        }
    )
    
    return config_data
```

## ✅ VERIFICATION CHECKLIST

**Immediate (Day 0 - Today):**
- [ ] Remove or protect `/_debug/config` endpoint
- [ ] Verify endpoint returns 401/403 without auth
- [ ] Test with curl: `curl -I https://.../_debug/config`
- [ ] Search codebase for other debug endpoints
- [ ] Review all `/admin`, `/internal`, `/_*` routes
- [ ] Security lead verification and sign-off

**Before Launch (Day 3):**
- [ ] Penetration test on all endpoints
- [ ] Verify no config leaks in error responses
- [ ] Check response headers for debug info
- [ ] Audit all sensitive route access patterns
- [ ] Document secure access procedures
- [ ] Update security runbook

## 📊 MONITORING

**Security Alerts:**
```yaml
# alerts/security.yml
- alert: DebugEndpointAccess
  expr: rate(debug_endpoint_access_total[5m]) > 0
  labels:
    severity: critical
  annotations:
    summary: "Debug endpoint accessed in production"
    description: "Endpoint {{ $labels.endpoint }} accessed by {{ $labels.user_id }}"
    runbook: "https://runbooks.scholarshipai.com/security-debug-access"
```

**Audit Log Query:**
```python
# Query for suspicious access
SELECT 
    timestamp,
    endpoint,
    user_id,
    ip_address,
    user_agent
FROM security_audit_log
WHERE endpoint LIKE '%debug%' 
   OR endpoint LIKE '%admin%'
   OR endpoint LIKE '%config%'
ORDER BY timestamp DESC
LIMIT 100;
```

## 🔄 ROLLBACK PLAN

If issues arise:
1. Can re-enable debug endpoint with admin auth
2. Ensure proper audit logging before re-enabling
3. Document business justification for access

## 📁 ARTIFACTS

- [ ] Security audit scan results
- [ ] Before/after endpoint exposure report
- [ ] Penetration test results
- [ ] Security lead sign-off document

---

**ETA:** Day 0 (TODAY - 30 minutes)  
**Risk:** Low (straightforward removal/protection)  
**Dependencies:** None (highest priority, start immediately)

## 🚨 IMMEDIATE ACTION REQUIRED

**Execute NOW:**
```bash
# 1. Backup current code
git checkout -b hotfix/remove-debug-endpoint

# 2. Remove debug endpoint
# Edit routers/debug.py or main.py

# 3. Test locally
curl -I http://localhost:5000/_debug/config
# Should return 404 or 403

# 4. Deploy immediately
git commit -m "SECURITY: Remove public debug endpoint (DEF-002)"
git push origin hotfix/remove-debug-endpoint

# 5. Verify in production
curl -I https://scholarship-api-jamarrlmayes.replit.app/_debug/config
# Should return 404 or 403
```

**Notify Security Lead:** Immediate verification required after deployment
