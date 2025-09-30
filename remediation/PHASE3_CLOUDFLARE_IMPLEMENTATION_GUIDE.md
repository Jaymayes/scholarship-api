# Phase 3 Edge Containment - Cloudflare Implementation Guide

**Incident**: DEF-002 P0 Security Containment  
**Approved By**: CEO  
**Target Completion**: T+4 hours from approval  
**DRI**: Security Lead, Infra Lead, SRE  

---

## Pre-Cutover Checklist

### Cloudflare Account Setup
- [ ] Provision Cloudflare Business account
- [ ] Add domain: `api.scholarshipai.com`
- [ ] Configure NS records or CNAME setup
- [ ] Set DNS TTL to 5 minutes for fast rollback

### Origin Configuration
**Current Replit Origin**: `scholarship-api-jamarrlmayes.replit.app`  
**Port**: 5000 (HTTPS via Replit proxy)  
**Origin Protocol**: HTTPS

---

## Cloudflare Configuration (T+0 to T+1h)

### 1. DNS Records
```
Type: CNAME
Name: api.scholarshipai.com
Target: scholarship-api-jamarrlmayes.replit.app
Proxy: ✅ Enabled (orange cloud)
TTL: 300 seconds (5 minutes)
```

### 2. SSL/TLS Settings
```
Mode: Full (Strict)
Minimum TLS Version: 1.2
Authenticated Origin Pulls: Enabled (if Replit supports)
Always Use HTTPS: Enabled
HSTS: Enabled
  - Max Age: 31536000 (12 months)
  - Include Subdomains: Yes
  - Preload: Yes
```

### 3. WAF Rules (Block Mode)

#### Rule 1: Primary Debug Path Block
```
Expression: (http.request.uri.path contains "/_debug")
Action: Block
Log: Yes
Priority: 1
```

#### Rule 2: Debug Variants Block
```
Expression: (
  starts_with(http.request.uri.path, "/debug") or
  http.request.uri.path matches "(?i)/+debug(/|$)" or
  http.request.uri.path contains "%5F%5F?debug" or
  http.request.uri.path contains "%2f_debug" or
  http.request.uri.path matches "(?i).*//.*debug"
)
Action: Block
Log: Yes
Priority: 2
```

#### Rule 3: Path Normalization Prevention
```
Expression: (http.request.uri.path contains "%2e%2e" or http.request.uri.path contains "../")
Action: Block
Log: Yes
Priority: 3
```

### 4. Transform Rules (Apply BEFORE WAF)
```
Rule: Normalize Request Path
Expression: true
Transformation: 
  - Lowercase URI path
  - URL decode once
  - Remove duplicate slashes
Priority: 1 (executes before WAF)
```

### 5. Cache Configuration
```
Cache Level: Bypass (during containment window)
Browser Cache TTL: Respect Existing Headers
Cache Everything: Disabled for API paths

Cache Rule:
  If: http.request.uri.path starts_with "/"
  Then: Bypass cache
  
Response Header Modification:
  Set: Cache-Control: no-store, no-cache, must-revalidate
```

### 6. Security Headers (Edge Injection)
```javascript
// Response Header Modification Rule
{
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "SAMEORIGIN",
  "Referrer-Policy": "no-referrer",
  "X-XSS-Protection": "1; mode=block",
  "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

### 7. Rate Limiting (Edge Layer)
```
Rule: Underscore Path Rate Limit
Expression: starts_with(http.request.uri.path, "/_")
Rate: 50 requests per 10 seconds
Action: Block
Duration: 60 seconds
```

### 8. Bot Management
```
OWASP ModSecurity Core Rule Set: Enabled
Bot Fight Mode: Enabled
JavaScript Challenge: Enabled for non-API paths only
Verified Bots: Allowed (Google, Bing)
```

---

## Staged Rollout (T+1 to T+2h)

### Phase 1: Dry Run (15 minutes)
1. Set all WAF rules to "Log" mode
2. Monitor for false positives
3. Review CloudFlare Analytics for blocked patterns
4. Adjust rules if needed

### Phase 2: Block Mode (30 minutes)
1. Switch rules from "Log" to "Block"
2. DNS cutover (update TTL, wait for propagation)
3. Run verification matrix immediately

### Phase 3: Validation (15 minutes)
1. Verify all debug paths return 403
2. Verify legitimate API traffic works
3. Check latency metrics (target: P95 < 200ms)

---

## Verification Matrix Tests

Run from 5 geographic regions (US-East, US-West, EU, Asia, South America):

```bash
#!/bin/bash
DOMAIN="https://api.scholarshipai.com"

echo "=== Debug Path Blocking Tests ==="

# Test 1: Basic debug path
curl -I "$DOMAIN/_debug/config"
# Expected: HTTP/2 403

# Test 2: Percent-encoded
curl -I "$DOMAIN/_debug%2fconfig"
# Expected: HTTP/2 403

# Test 3: Double-slash
curl -I "$DOMAIN/_debug//config"
# Expected: HTTP/2 403

# Test 4: Case variation
curl -I "$DOMAIN/_Debug/config"
# Expected: HTTP/2 403

# Test 5: Plain /debug
curl -I "$DOMAIN/debug"
# Expected: HTTP/2 403

# Test 6: Mixed encoding
curl -I "$DOMAIN/%5F%64%65%62%75%67/config"
# Expected: HTTP/2 403

# Test 7: Double-encoded
curl -I "$DOMAIN/%255F%2564%2565%2562%2575%2567/config"
# Expected: HTTP/2 403

echo ""
echo "=== Legitimate API Tests ==="

# Test 8: Root endpoint
curl -I "$DOMAIN/"
# Expected: HTTP/2 200

# Test 9: Health check
curl -I "$DOMAIN/healthz"
# Expected: HTTP/2 200

# Test 10: API search
curl -I "$DOMAIN/api/v1/search?q=engineering"
# Expected: HTTP/2 403 or 200 (depends on auth)

echo ""
echo "=== Latency Baseline ==="
time curl -o /dev/null -s -w "Time: %{time_total}s\n" "$DOMAIN/"
```

---

## Monitoring Setup

### CloudFlare Analytics Dashboards
- **Firewall Events**: Filter for "Block" actions on debug paths
- **Performance**: Track P50, P95, P99 latency
- **Traffic**: Monitor origin requests vs edge-cached
- **Security**: Track bot scores, WAF blocks, rate limit hits

### Alert Thresholds
```yaml
Alerts:
  - Name: "Debug Path 2xx Response"
    Condition: "http.response.status_code in [200, 201, 202, 203] AND http.request.uri.path contains 'debug'"
    Severity: P0
    Notify: security-team@company.com
    
  - Name: "API Error Rate Spike"
    Condition: "5xx_rate > 0.5% for 5 minutes"
    Severity: P1
    Notify: on-call-engineer@company.com
    
  - Name: "Latency Degradation"
    Condition: "p95_latency > baseline + 50ms for 10 minutes"
    Severity: P2
    Notify: sre-team@company.com
```

### Synthetic Monitoring
```javascript
// Cloudflare Workers script for continuous monitoring
addEventListener('scheduled', event => {
  event.waitUntil(runHealthChecks())
})

async function runHealthChecks() {
  const tests = [
    { path: '/_debug/config', expect: 403 },
    { path: '/', expect: 200 },
    { path: '/healthz', expect: 200 }
  ]
  
  for (const test of tests) {
    const response = await fetch(`https://api.scholarshipai.com${test.path}`)
    if (response.status !== test.expect) {
      await alertP0(`Unexpected status: ${test.path} returned ${response.status}`)
    }
  }
}
```

---

## Rollback Plan

### Trigger Conditions
- Error rate > 1% for 5 consecutive minutes
- Latency P95 > 500ms for 5 consecutive minutes
- False positive rate > 0.1% on legitimate traffic

### Rollback Steps
1. Pause all WAF rules (switch to Log mode)
2. Revert DNS to direct Replit origin
3. Wait 5 minutes for DNS propagation
4. Verify traffic restored to baseline
5. Investigate root cause, adjust rules
6. Retry with corrected configuration

---

## Success Criteria

### Phase 3 Complete When:
- [x] 100% block rate across verification matrix (all regions, all encodings)
- [x] API error rate remains < 0.1%
- [x] P95 latency impact < +50ms vs baseline
- [x] Zero false positives on legitimate API traffic
- [x] 24-hour sustained block with no 2xx on debug paths

---

## Post-Cutover Tasks (T+4h to End of Day)

1. **JWT Rotation #2** (Dual-Key Rollout)
   - Generate new key (96+ chars)
   - Add to Replit Secrets as `JWT_SECRET_KEY_NEW`
   - Deploy with kid rotation logic
   - Monitor auth success rate
   - Retire old key after 60 minutes
   - Force logout high-risk sessions

2. **Origin Security**
   - Remove public reference to `scholarship-api-jamarrlmayes.replit.app`
   - Configure Cloudflare IP allowlist at origin (if possible)
   - Consider Cloudflare Tunnel for complete origin obfuscation

3. **Compliance Documentation**
   - Log all test results with timestamps
   - Document containment timeline
   - Prepare 72-hour post-incident review
   - FERPA/COPPA data exposure assessment (currently: no confirmed access)

---

## Infrastructure Artifacts

All application-layer hardening is complete and logged:
- Pre-router middleware: `middleware/debug_block_prefilter.py`
- Enhanced WAF: `middleware/waf_protection.py` (lines 145-183)
- Route inventory: Startup hook at `main.py` lines 147-193
- Containment reports: `remediation/DEF-002_*.md`

**Application Status**: ✅ Production-ready, fail-closed guards active  
**Next Layer**: Edge containment via Cloudflare (this guide)
