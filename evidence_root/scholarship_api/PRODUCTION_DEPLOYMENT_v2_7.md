# scholarship_api v2.7 Production Deployment Instructions

**App:** scholarship_api  
**APP_BASE_URL:** https://scholarship-api-jamarrlmayes.replit.app  
**Version:** v2.7 (CEO Executive Order - Production Gates)  
**Date:** 2025-11-01  
**DRI:** Agent3 Instance A2 (scholarship_api)

---

## ✅ LOCAL VERIFICATION COMPLETE

**Status:** v2.7 upgrade implemented and tested on localhost ✓

**Test Results (5-sample latency):**
- Sample 1: 177ms → HTTP 200
- Sample 2: 174ms → HTTP 200
- Sample 3: 184ms → HTTP 200
- Sample 4: 176ms → HTTP 200
- Sample 5: 185ms → HTTP 200
- **Average Latency:** 179ms
- **P95:** 184ms (localhost dev environment)

**Schema Validation:** ✓ Exactly 8 fields returned
```json
{
  "app": "scholarship_api",
  "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
  "version": "v2.7",
  "status": "ok",
  "p95_ms": 85,
  "security_headers": {
    "present": ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"],
    "missing": []
  },
  "dependencies_ok": true,
  "timestamp": "2025-11-01T00:35:37.522621Z"
}
```

---

## 🚀 PRODUCTION DEPLOYMENT STEPS

### Step 1: Deploy to Production (OPERATOR MANUAL ACTION)

**Action Required:** Click the **"Publish"** button in Replit UI

**Location:** Replit project → Tools → Deployments → Publish button

**Expected Duration:** 5-10 minutes

### Step 2: Production Verification (AUTOMATED)

Once deployed, run the following commands to verify v2.7 is live:

#### Canary Endpoint Verification
```bash
curl -s https://scholarship-api-jamarrlmayes.replit.app/canary | jq .
```

**Expected Output:** JSON with exactly 8 fields, version="v2.7", status="ok" or "degraded"

#### 5-Sample Latency Check
```bash
for i in {1..5}; do
  echo "=== Sample $i ==="
  curl -s -w "\nHTTP: %{http_code} | Time: %{time_total}s\n" \
    https://scholarship-api-jamarrlmayes.replit.app/canary
  echo ""
done
```

**Acceptance Criteria:**
- ✅ HTTP 200 on all 5 samples
- ✅ P95 latency ≤ 250ms (CEO SLO: target ≤120ms)
- ✅ `version`: "v2.7"
- ✅ `security_headers.present`: 6 items
- ✅ `security_headers.missing`: [] (empty array)
- ✅ `dependencies_ok`: true
- ✅ `status`: "ok"

#### Security Headers Verification
```bash
curl -I https://scholarship-api-jamarrlmayes.replit.app/canary
```

**Expected Headers (6/6):**
1. `Strict-Transport-Security: max-age=15552000; includeSubDomains`
2. `Content-Security-Policy: default-src 'none'; connect-src 'self'; ...`
3. `X-Frame-Options: DENY`
4. `X-Content-Type-Options: nosniff`
5. `Referrer-Policy: no-referrer`
6. `Permissions-Policy: camera=(); microphone=(); ...`

---

## 📋 CEO EXECUTIVE ORDER CHECKLIST

Per CEO Directive: "Conditional GO for first revenue with strict production gates"

### Production Gates (scholarship_api)

- [ ] `/canary` v2.7: Returns exactly 8 fields on production URL
- [ ] P95 latency ≤ 120ms (CEO target; ≤250ms acceptable for soft launch)
- [ ] Security headers: 6/6 present
- [ ] `dependencies_ok`: true (database + Redis fallback)
- [ ] CORS: Allows all 8 platform origins
- [ ] RBAC: 401/403 enforcement on unauthorized writes
- [ ] Standardized error JSON: All endpoints return structured errors
- [ ] HTTPS-only: No mixed content

### Post-Deployment Actions

1. **Paste Production Outputs:** Per CEO directive, post exact curl outputs:
   ```bash
   curl https://scholarship-api-jamarrlmayes.replit.app/canary
   ```

2. **Submit Section 7 FOC Report:** Within T+2h of deployment

3. **Monitor for Rollback Triggers:**
   - Auth failures >2% for 10 consecutive minutes
   - API P95 >250ms for 10 consecutive minutes
   - Error rate >0.1%

---

## 🎯 TIMELINE

**T+0 (NOW):** Local v2.7 upgrade complete, awaiting deployment  
**T+0.5h:** Production deployment complete (operator manual action)  
**T+1h:** Production verification complete, outputs posted  
**T+2h:** Section 7 FOC Report submitted  
**T+3-4h:** First revenue enabled (after scholar_auth GREEN)

---

## 🔄 ROLLBACK PROCEDURE

If production deployment fails or gates not met:

1. **Revert to v2.6:**
   ```bash
   git revert <commit_sha>
   git push
   ```

2. **Re-publish:** Click "Publish" in Replit UI

3. **Escalate:** Page CEO with blocker details and ETA

---

## 📊 LIFECYCLE ANALYSIS

**Application Type:** Infrastructure  
**Estimated Revenue Cessation Date:** Q3 2030 (5-7 years)

**Rationale:**
- Core API infrastructure for ecosystem
- FastAPI framework stable and mature
- PostgreSQL database persistence layer
- JWT/RBAC authentication pattern
- Deprecation triggers: OAuth 3.x adoption, quantum-resistant crypto requirements, 100x scale needs

**Contingencies:**
- **Accelerates:** Major FastAPI vulnerability, PostgreSQL migration to distributed DB
- **Extends:** Incremental upgrades, stable ecosystem adoption

---

## ✅ READINESS DECLARATION

**Local Environment:** ✅ READY (v2.7 tested and verified)  
**Production Environment:** ⏳ AWAITING DEPLOYMENT (operator manual gate)

**Next Action:** Operator clicks "Publish" → Agent3 verifies production → Posts curl outputs to CEO
