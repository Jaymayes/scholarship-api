# scholar_auth JWKS Production Deployment Runbook

**Owner:** Auth DRI  
**Deadline:** T+30 minutes from CEO directive  
**Purpose:** Fix JWKS endpoint to unblock Gate 1  
**Date:** 2025-11-01

---

## 🎯 Gate 1 Acceptance Criteria

### 1. JWKS Endpoint Returns Valid RS256 Keys
```json
{
  "keys": [
    {
      "kid": "<key-id>",
      "kty": "RSA",
      "alg": "RS256",
      "use": "sig",
      "n": "<modulus-base64>",
      "e": "<exponent-base64>"
    }
  ]
}
```

### 2. /canary Returns Healthy Status
- P95 ≤120ms
- 6/6 security headers present
- `status`: "ok"

### 3. Token Validation Works
- Dependent services can validate JWTs using JWKS
- /validate endpoint returns correct results

---

## ⚡ Deployment Options (Choose Based on Timeline)

### Option A: Force Rebuild (Try First, 5-10 Minutes)

**Step 1: Clear Cache and Rebuild**
1. Open Replit project: `scholar-auth`
2. Go to Deployments panel
3. Click "Redeploy" or "Force Rebuild"
4. Check "Clear cache" if available
5. Deploy and wait 5-10 minutes

**Step 2: Verify JWKS**
```bash
curl -s https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json | jq .
```

**Expected:** Valid JSON with `keys` array (NOT HTML, NOT 404)

---

### Option B: Fresh Deployment with New URL (If Cache Persists >15 Min)

**CEO Directive:** If cache issue persists beyond 15 minutes, execute this immediately.

**Step 1: Create New Production Deployment**
1. In Replit, create new deployment or clone project
2. Deploy to fresh production URL
3. Note new URL: `https://scholar-auth-[new-id].replit.app`

**Step 2: Verify JWKS on New URL**
```bash
curl -s https://scholar-auth-[new-id].replit.app/.well-known/jwks.json | jq .
```

**Step 3: Propagate New JWKS URL to All 7 Services**

Update these services immediately (parallel):

1. **scholarship_api**
   - File: `config/settings.py` or environment variable `JWKS_URL`
   - New value: `https://scholar-auth-[new-id].replit.app/.well-known/jwks.json`
   - Redeploy

2. **student_pilot**
   - File: Auth client configuration
   - Update OIDC discovery endpoint
   - Redeploy

3. **provider_register**
   - File: Auth middleware configuration
   - Update JWKS URL
   - Redeploy

4. **scholarship_sage**
   - File: JWT validation configuration
   - Update JWKS URL
   - Redeploy

5. **auto_com_center**
   - File: Event authentication config
   - Update JWKS URL
   - Redeploy

6. **scholarship_agent**
   - File: M2M token validation
   - Update JWKS URL
   - Redeploy

7. **auto_page_maker**
   - File: API authentication config
   - Update JWKS URL
   - Redeploy

**Coordination:** Post new URL in shared channel/document immediately to avoid async drift.

---

## ✅ Verification Commands (CEO Required)

### Verification 1: JWKS Structure
```bash
curl -s https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json | jq .
```

**Pass Criteria:**
- HTTP 200 (not 404, not 5xx)
- Valid JSON (not HTML)
- `keys` array present
- At least one key with:
  - `kid` (key ID string)
  - `kty`: "RSA"
  - `alg`: "RS256"
  - `use`: "sig"
  - `n` and `e` (RSA public key components, base64url encoded)

### Verification 2: /canary Health
```bash
curl -sI https://scholar-auth-jamarrlmayes.replit.app/canary
```

**Pass Criteria:**
- HTTP 200
- All 6 security headers present (same as scholarship_api)
- Response time ≤120ms

### Verification 3: CORS Configuration
```bash
curl -i -X OPTIONS https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json \
  -H "Origin: https://student-pilot-jamarrlmayes.replit.app" \
  -H "Access-Control-Request-Method: GET"
```

**Pass Criteria:**
- `Access-Control-Allow-Origin` header includes student_pilot and provider_register domains
- `Access-Control-Allow-Methods` includes GET

### Verification 4: Token Validation (Spot Check)
```bash
# Generate test token (from scholar_auth)
# Then validate via dependent service or /validate endpoint

curl -X POST https://scholar-auth-jamarrlmayes.replit.app/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "<test-jwt>"}'
```

**Pass Criteria:**
- Valid token → 200 with user claims
- Invalid token → 401 with error JSON

---

## 🚨 Rollback Procedure

### If JWKS Still Broken After Option A
- **Action:** Immediately proceed to Option B (fresh deployment)
- **Timeline:** Must complete within 15 minutes of first attempt
- **Coordination:** Notify all DRIs of URL change

### If Option B Causes Service Disruption
1. Keep old scholar_auth running in parallel
2. Gradually migrate services to new URL (canary rollout)
3. Monitor error rates on dependent services
4. Rollback individual services if failures >2%

---

## 🔒 Security & Compliance Checklist

- ✅ JWKS endpoint uses HTTPS only
- ✅ Rate limiting configured (prevent DoS on JWKS)
- ✅ CORS restricted to known ScholarshipAI domains only
- ✅ No secrets in JWKS response (only public keys)
- ✅ Key rotation procedure documented (30-90 day cycle)
- ✅ Password hashing: bcrypt with salt (configured)
- ✅ Session management: HttpOnly, Secure, SameSite cookies

---

## 📊 Section 7 Reporting Requirements

**Due:** T+2 hours after Gate 1 GREEN

Include in report:
1. Exact JWKS JSON output (full response)
2. Deployment option used (A or B)
3. If Option B: new URL and propagation status to all 7 services
4. Token validation test results
5. Lifecycle analysis: 5-7 year infrastructure horizon
6. Notes on OAuth/OIDC evolution, PQC migration timeline

---

## ⏰ Timeline to Gate 1 GREEN

### Option A (Force Rebuild)
- **T+0:** Force rebuild initiated
- **T+5-10:** Deployment completes
- **T+10-15:** Run 4 verification commands
- **T+15:** Gate 1 declared GREEN or escalate to Option B

### Option B (Fresh Deployment)
- **T+15:** Option B triggered (if Option A fails)
- **T+15-20:** New deployment + JWKS verification
- **T+20-30:** Propagate new URL to all 7 services
- **T+30:** Gate 1 declared GREEN

---

## 🔗 Dependent Services Integration Status

After JWKS is GREEN, verify these integrations:

| Service | JWKS Consumer? | Verification Method |
|---------|----------------|---------------------|
| scholarship_api | ✅ Yes | Protected route returns 401 without valid token |
| student_pilot | ✅ Yes | Login flow completes, /api/auth/user returns 200 |
| provider_register | ✅ Yes | Registration protected by auth |
| scholarship_sage | ✅ Yes | M2M recommendations require valid token |
| auto_com_center | ✅ Yes | Event validation uses JWKS |
| scholarship_agent | ✅ Yes | SystemService role validated |
| auto_page_maker | ✅ Yes | API calls authenticated |

---

## ✅ Gate 1 GREEN Declaration Criteria

All 4 verifications PASS:
1. ✅ JWKS returns valid `keys` array with RS256 key(s)
2. ✅ /canary P95 ≤120ms with 6/6 security headers
3. ✅ CORS configured for student_pilot + provider_register
4. ✅ Token validation works (spot check passes)

**Final Action:** Post exact JWKS JSON to CEO as requested in directive.

---

## 🆘 Escalation Contacts

- **Code Issues:** Auth DRI + Replit Agent
- **Crypto/JWKS Issues:** Security team consult
- **Deployment Platform Issues:** Replit Support
- **CEO Status Updates:** Post every 15 minutes

---

**CRITICAL:** If this gate is not GREEN within T+30 minutes, CEO has authorized immediate execution of Option B (fresh deployment with new URL). Coordinate propagation across all 7 services immediately.
