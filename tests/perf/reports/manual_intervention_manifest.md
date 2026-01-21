# Manual Intervention Manifest

**Run ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2S2-FIX-027  
**Protocol**: AGENT3_HANDSHAKE v30  
**Generated**: 2026-01-21T22:49:00Z  
**Status**: BLOCKED (External Apps Inaccessible)

---

## Summary

All external ecosystem apps (A1-A8) returned HTTP 000 (connection failed) or 301 redirects that could not be followed. This indicates:
1. Apps are in sleeping/waking state
2. DNS resolution issues
3. Different URL patterns than expected

## Apps Requiring Manual Intervention

### A1: Scholar Auth
- **Expected URL**: https://scholar-auth.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**:
  1. Access A1 Replit workspace
  2. Ensure startup command binds to `0.0.0.0:$PORT`
  3. Add shallow `/health` endpoint:
     ```javascript
     app.get('/health', (req, res) => {
       res.json({
         service: 'scholar-auth',
         version: '1.0.0',
         uptime_s: process.uptime(),
         status: 'healthy'
       });
     });
     ```
  4. Ensure `app.set('trust proxy', 1)`
  5. Verify Set-Cookie includes: `SameSite=None; Secure; HttpOnly`
  6. Redeploy and verify: `curl -I https://scholar-auth.scholaraiadvisor.com/health`

### A2: API Status
- **Expected URL**: https://api.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**: Same as A1 with service name "api-status"

### A3: Scholarship Agent
- **Expected URL**: https://scholarship-agent.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**: Same as A1 with service name "scholarship-agent"

### A4: Scholarship Sage
- **Expected URL**: https://scholarship-sage.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**: Same as A1 with service name "scholarship-sage"

### A5: Landing/Pricing
- **Expected URL**: https://www.scholaraiadvisor.com
- **Result**: HTTP 301 (redirect, body too small)
- **Required Actions**:
  1. Verify redirect target is accessible
  2. Ensure homepage contains `pk_live_` or `pk_test_` (Stripe key)
  3. Verify checkout CTA with id="checkout" or data-role="checkout"
  4. Verify stripe.js is loaded

### A6: Providers API
- **Expected URL**: https://providers.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**:
  1. Add `/api/providers` endpoint returning JSON array
  2. Ensure no HTML is returned

### A7: SEO/Sitemap
- **Expected URL**: https://seo.scholaraiadvisor.com
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**:
  1. Add `/health` endpoint
  2. Verify `/sitemap.xml` is accessible

### A8: Event Bus
- **Expected URL**: https://event-bus.scholaraiadvisor.com (or via EVENT_BUS_URL env)
- **Result**: HTTP 000 (connection timeout)
- **Required Actions**:
  1. Add `/health` endpoint
  2. Verify `/api/events` POST + GET with X-Trace-Id
  3. Implement telemetry fallback to A2
  4. Implement local spool to `business_events` table

---

## A0 (This Workspace) Status

**Scholarship API**: ✅ PASS
- `/ready`: 200 OK with markers
- `/health`: 200 OK with database status
- All V2 endpoints accessible

---

## Recommended Next Steps

1. **Wake all sleeping Replits** manually by visiting each workspace
2. **Apply standard health endpoint** to each app
3. **Re-run verification** after all apps are awake and deployed
4. **Do NOT fabricate PASS** for inaccessible apps

---

**Attestation**: BLOCKED (ZT3G) — See Manual Intervention Required Above
