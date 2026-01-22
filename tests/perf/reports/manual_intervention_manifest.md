# Manual Intervention Manifest

**Run ID**: CEOSPRINT-20260121-VERIFY-ZT3G-V2S2-028  
**Protocol**: AGENT3_HANDSHAKE v30 (Scorched Earth)  
**Generated**: 2026-01-22T01:53:00Z

---

## BLOCKED Apps Requiring Manual Fixes

### A7: SEO/Sitemap
**URL**: https://seo-jamarrlmayes.replit.app  
**Status**: 404 Not Found  
**Endpoints Tested**: /health, /sitemap.xml

#### Required Fixes:
1. **Add shallow /health endpoint**:
```javascript
app.get('/health', (req, res) => {
  res.json({
    service: 'seo-sitemap',
    version: '1.0.0',
    status: 'healthy',
    uptime_s: process.uptime()
  });
});
```

2. **Bind to correct port**:
```javascript
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`SEO service listening on 0.0.0.0:${PORT}`);
});
```

3. **Deploy and verify**:
```bash
curl -s https://seo-jamarrlmayes.replit.app/health
```

---

### A8: Event Bus
**URL**: https://event-bus-jamarrlmayes.replit.app  
**Status**: 404 Not Found  
**Endpoints Tested**: /health

#### Required Fixes:
1. **Add shallow /health endpoint**:
```javascript
app.get('/health', (req, res) => {
  res.json({
    service: 'event-bus',
    version: '1.0.0',
    status: 'healthy',
    uptime_s: process.uptime()
  });
});
```

2. **Check Upstash rate limit configuration**:
   - Verify Upstash Redis connection
   - Check rate limit thresholds
   - Ensure proper error handling

3. **Deploy and verify**:
```bash
curl -s https://event-bus-jamarrlmayes.replit.app/health
```

---

## Impact Assessment

| App | Impact | Severity |
|-----|--------|----------|
| A7 | SEO/sitemap unavailable | Medium |
| A8 | Telemetry round-trip blocked | High |

---

## Attestation Impact

With A7 and A8 returning 404:
- **Cannot achieve 8/8 PASS** for Definitive GO
- **A8 checksum round-trip** cannot be verified
- **Telemetry fallback** must use local spool

---

## Recommended Action

1. Deploy /health endpoints to A7 and A8
2. Re-run ZT3G verification after deployment
3. Verify A8 POST+GET checksum round-trip
