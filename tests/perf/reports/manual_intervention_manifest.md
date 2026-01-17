# Manual Intervention Manifest
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**Timestamp**: 2026-01-17T18:37:00Z

## Overview
This manifest documents external apps that could not be verified from this workspace and require manual intervention.

## Apps Requiring Manual Verification

### A1 (Auth Service)
- **Status**: UNVERIFIED - external workspace
- **Expected URL**: Check Replit dashboard for saa-auth
- **Required Checks**:
  1. GET / and /health → service markers
  2. Set-Cookie includes SameSite=None; Secure; HttpOnly
  3. app.set('trust proxy', 1) enabled
- **Code Changes Required**:
  ```javascript
  // Ensure host binding
  app.listen(process.env.PORT || 5000, '0.0.0.0');
  
  // Health endpoint
  app.get('/health', (req, res) => {
    res.json({service: 'saa-auth', version: '1.0.0', uptime_s: process.uptime(), timestamp: new Date().toISOString(), status: 'healthy'});
  });
  ```
- **Curl Check**:
  ```bash
  curl -I https://<auth-domain>/health -H "Cache-Control: no-cache"
  ```

### A3 (Scholarship Agent)
- **Status**: UNVERIFIED - external workspace
- **Expected Markers**: {service: "scholarship-agent", status: "healthy"}
- **Required Endpoints**: /health or /readyz
- **Curl Check**:
  ```bash
  curl https://<agent-domain>/health -H "Cache-Control: no-cache"
  ```

### A5 (B2C Landing)
- **Status**: UNVERIFIED - external workspace
- **Required Checks**:
  1. GET /pricing → HTML contains pk_live_ or pk_test_
  2. stripe.js tag present
  3. checkout CTA element present (id="checkout" or data-role="checkout")
- **Curl Check**:
  ```bash
  curl https://<b2c-domain>/pricing -H "Cache-Control: no-cache" | grep -E "(pk_live_|pk_test_|stripe.js)"
  ```

### A6 (B2B Portal)
- **Status**: UNVERIFIED - external workspace
- **Required Checks**:
  1. GET /api/providers → JSON array (not HTML error)
- **Curl Check**:
  ```bash
  curl https://<b2b-domain>/api/providers -H "Accept: application/json" -H "Cache-Control: no-cache"
  ```

### A7 (SEO Landing)
- **Status**: UNVERIFIED - external workspace
- **Required Checks**:
  1. GET /sitemap.xml → valid XML
  2. GET /health → service markers
- **Curl Check**:
  ```bash
  curl https://<seo-domain>/sitemap.xml -H "Cache-Control: no-cache" | head -20
  curl https://<seo-domain>/health -H "Cache-Control: no-cache"
  ```

### A8 (Telemetry)
- **Status**: UNVERIFIED - external workspace
- **Required Checks**:
  1. POST /api/events with X-Trace-Id → {"success":true,"event_id":...}
  2. GET by event_id confirms checksum
- **Curl Check**:
  ```bash
  curl -X POST https://<telemetry-domain>/api/events \
    -H "Content-Type: application/json" \
    -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
    -d '{"event":"test","payload":{}}' | jq .
  ```

## Action Required
1. Access each external workspace in Replit
2. Verify host binding is 0.0.0.0:$PORT
3. Add shallow /health endpoint if missing
4. Redeploy and run curl checks
5. Document results in respective health JSON files

## Verified in This Workspace
- A2 (Core Data): ✅ VERIFIED - scholarship_api running with all security headers and hybrid search
