# Manual Intervention Manifest

**Generated**: 2026-01-22T19:18:00Z  
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027  
**Protocol**: AGENT3_HANDSHAKE v30

---

## Blocked Services

The following external services are not accessible from this workspace (A2 scholarship-api):

| App | Service | URL | Status | Action Required |
|-----|---------|-----|--------|-----------------|
| A1 | scholar-auth | https://scholar-auth.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |
| A3 | scholarship-agent | https://scholarship-agent.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |
| A4 | scholarship-sage | https://scholarship-sage.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |
| A5 | student-pilot | https://student-pilot.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |
| A6 | provider-register | https://provider-register.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |
| A7 | auto-page-maker | https://auto-page-maker.scholaraiadvisor.com | BLOCKED (HTTP 000) | Deploy and verify in separate workspace |

---

## Accessible Services (This Workspace)

| App | Service | Status | Notes |
|-----|---------|--------|-------|
| A2 | scholarship-api | ✅ PASS | Local service - fully accessible |
| A8 | auto-com-center (Watchtower) | ✅ PARTIAL | POST events works; GET returns 405 |

---

## Required Manual Actions Per Blocked Service

### A1 (scholar-auth)

1. **Replit URL**: Navigate to scholar-auth Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://scholar-auth.scholaraiadvisor.com/health"
   curl -I "https://scholar-auth.scholaraiadvisor.com/" | grep Set-Cookie
   ```
3. **Expected**: JSON with `{service:"scholar-auth"}`, Set-Cookie with `SameSite=None; Secure; HttpOnly`
4. **Code Changes** (if needed):
   - Ensure `app.set("trust proxy", 1)` in Express
   - Cookie options: `{ sameSite:"none", secure:true, httpOnly:true }`

### A3 (scholarship-agent)

1. **Replit URL**: Navigate to scholarship-agent Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://scholarship-agent.scholaraiadvisor.com/health"
   ```
3. **Expected**: JSON `{service:"scholarship-agent", status:"healthy"}`

### A4 (scholarship-sage)

1. **Replit URL**: Navigate to scholarship-sage Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://scholarship-sage.scholaraiadvisor.com/health"
   ```
3. **Expected**: JSON containing `{service:"scholarship-sage"}`

### A5 (student-pilot)

1. **Replit URL**: Navigate to student-pilot Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://student-pilot.scholaraiadvisor.com/pricing"
   # Check for pk_live_ or pk_test_ and stripe.js
   ```
3. **Expected**: HTML with Stripe publishable key and checkout CTA

### A6 (provider-register)

1. **Replit URL**: Navigate to provider-register Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://provider-register.scholaraiadvisor.com/api/providers"
   ```
3. **Expected**: JSON array (even `[]`), not HTML

### A7 (auto-page-maker)

1. **Replit URL**: Navigate to auto-page-maker Replit project
2. **Verification Steps**:
   ```bash
   curl -vL "https://auto-page-maker.scholaraiadvisor.com/sitemap.xml"
   curl -vL "https://auto-page-maker.scholaraiadvisor.com/health"
   ```
3. **Expected**: Valid sitemap.xml; JSON `{service:"auto-page-maker", status:"healthy"}`

---

## Cross-Workspace Reality Check

Per ZT3G protocol: These apps exist in separate Replit workspaces. This workspace (A2/A8) cannot directly access or modify them. Manual verification in each respective workspace is required.

---

## Attestation Impact

Due to blocked services A1, A3-A7:
- **Full ZT3G Attestation**: BLOCKED pending manual intervention
- **A2/A8 Local Attestation**: CAN PROCEED with available services

---

## Recommended Next Steps

1. Complete all A2/A8 verification in this workspace
2. Open each blocked service's Replit workspace
3. Execute the verification steps above
4. If services pass, update this manifest with PASS status
5. Once all 8 apps are verified, proceed to final ZT3G attestation
