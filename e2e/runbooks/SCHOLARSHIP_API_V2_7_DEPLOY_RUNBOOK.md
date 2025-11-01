# scholarship_api v2.7 Production Deployment Runbook

**Owner:** API DRI  
**Deadline:** T+30 minutes from CEO directive  
**Status:** Code ready, awaiting deployment action  
**Date:** 2025-11-01

---

## 🎯 Gate 2 Acceptance Criteria

### 1. /canary Returns v2.7 Schema (8 Fields Exact)
```json
{
  "app": "scholarship_api",
  "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
  "version": "v2.7",
  "status": "ok",
  "p95_ms": <number>,
  "security_headers": {
    "present": [6 headers],
    "missing": []
  },
  "dependencies_ok": true,
  "timestamp": "ISO8601"
}
```

### 2. Security Headers (6/6 Present)
- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`

### 3. RBAC Enforcement
- Protected routes return 401 (no token) or 403 (invalid role)

---

## ⚡ Deployment Steps (5-10 Minutes)

### Step 1: Click "Publish" in Replit UI
1. Open Replit project: `scholarship-api`
2. Click **"Deploy"** or **"Publish"** button (top-right or left panel)
3. Confirm production deployment settings
4. Click final "Publish" or "Deploy" button
5. Wait 5-10 minutes for deployment to complete

### Step 2: Verify Deployment Complete
```bash
# Check if new version is live (should return v2.7, not 404)
curl -s https://scholarship-api-jamarrlmayes.replit.app/canary
```

**Expected:** HTTP 200 with v2.7 JSON (not 404, not HTML)

---

## ✅ Verification Commands (CEO Required)

### Verification 1: /canary Schema & Content
```bash
curl -s https://scholarship-api-jamarrlmayes.replit.app/canary | jq .
```

**Pass Criteria:**
- HTTP 200 response
- Exactly 8 fields (no more, no less)
- `version`: "v2.7"
- `status`: "ok"
- `security_headers.present`: array with 6 items
- `security_headers.missing`: empty array
- `dependencies_ok`: true

### Verification 2: Security Headers
```bash
curl -I https://scholarship-api-jamarrlmayes.replit.app/canary
```

**Pass Criteria:**
- All 6 headers present in response
- `Strict-Transport-Security: max-age=15552000; includeSubDomains`
- `Content-Security-Policy: default-src 'none'; ...`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(); ...`

### Verification 3: RBAC Enforcement (Protected Route)
```bash
# Test without token (should return 401)
curl -i https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships/123/save

# Test with invalid token (should return 401 or 403)
curl -i -H "Authorization: Bearer invalid_token" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships/123/save
```

**Pass Criteria:**
- No token → HTTP 401 with standardized error JSON
- Invalid token → HTTP 401 or 403 with standardized error JSON
- NOT 200, NOT 500

### Verification 4: Performance Check (5 Samples)
```bash
for i in {1..5}; do
  echo "=== Sample $i ==="
  curl -s -w "HTTP: %{http_code} | Time: %{time_total}s\n" \
    https://scholarship-api-jamarrlmayes.replit.app/canary
done
```

**Pass Criteria:**
- All HTTP 200
- P95 ≤ 250ms (target: ≤120ms per CEO SLO)

---

## 🚨 Rollback Procedure (If Verification Fails)

### Option A: Revert to Previous Deployment
1. Go to Replit Deployments panel
2. Click "History" or "Previous Deployments"
3. Select last known-good deployment
4. Click "Rollback" or "Redeploy"

### Option B: Emergency Hotfix
1. Identify failing verification (schema, headers, or RBAC)
2. Fix code in Replit editor
3. Re-run verification on localhost:5000
4. Re-deploy via "Publish" button
5. Re-verify production

---

## 📊 Section 7 Reporting Requirements

**Due:** T+2 hours after Gate 2 GREEN

Include in report:
1. Exact outputs of all 4 verification commands above
2. Timestamp of deployment completion
3. Any issues encountered and resolutions
4. Lifecycle analysis: 5-7 year infrastructure horizon
5. Dependencies: scholar_auth JWKS integration status

**Template:** `e2e/reports/scholarship_api/SECTION_7_FOC_REPORT_TEMPLATE_v2_7.md`

---

## 🔧 Pre-Deployment Checklist (Already Complete)

- ✅ v2.7 schema implemented (8 fields exact)
- ✅ Real security header detection (middleware stack verification)
- ✅ Database health check with circuit breaker
- ✅ Local testing complete (5 samples, all HTTP 200)
- ✅ Architect review PASS (zero security issues)
- ✅ RBAC middleware configured
- ✅ Standardized error JSON across endpoints
- ✅ CORS configured for allowed origins
- ✅ Workflow running without errors

---

## ⏰ Timeline to Gate 2 GREEN

- **T+0:** User clicks "Publish" (NOW)
- **T+5-10:** Deployment completes
- **T+10-15:** Run 4 verification commands
- **T+15-20:** Post outputs to CEO
- **T+20:** Gate 2 declared GREEN (if all pass)

---

## 🆘 Escalation Contacts

- **Code Issues:** Replit Agent (this session)
- **Deployment Platform Issues:** Replit Support
- **CEO Status Updates:** Post in main thread every 15 minutes

---

## ✅ Gate 2 GREEN Declaration Criteria

All 4 verifications PASS:
1. ✅ /canary returns v2.7 JSON with 8 fields, status="ok"
2. ✅ curl -I shows 6/6 security headers
3. ✅ Protected routes return 401/403 (not 200, not 500)
4. ✅ Performance P95 ≤250ms (preferably ≤120ms)

**Final Action:** Post exact curl outputs to CEO as requested in directive.

---

**DEPLOYMENT READY. AWAITING USER "PUBLISH" ACTION.**
