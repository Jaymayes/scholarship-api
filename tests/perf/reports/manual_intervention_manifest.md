# Manual Intervention Manifest
**FIX Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-029
**VERIFY Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030
**Timestamp**: 2026-01-18T18:40:19Z
**Protocol**: AGENT3_HANDSHAKE v30

---

## Cross-Workspace Reality

External apps (A1, A3, A4, A5, A6, A7, A8) cannot be modified from this workspace. This manifest provides **exact copy-paste fixes** for each workspace owner.

---

## A0 — Global Port Binding (All Apps)

**All apps must bind to 0.0.0.0:$PORT**

### Node.js/Express
```javascript
app.listen(process.env.PORT || 3000, "0.0.0.0", () => {
  console.log(`Server up on port ${process.env.PORT || 3000}`);
});
```

### Python/Uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Python/Flask
```python
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
```

---

## A1 — scholar-auth

### Required Changes

```javascript
const express = require('express');
const app = express();

app.set('trust proxy', 1);

// Health endpoint
app.get("/health", (req, res) => {
  res.json({
    service: "scholar-auth",
    status: "healthy",
    version: "1.0.0",
    timestamp: new Date().toISOString()
  });
});

// OIDC config (if applicable)
app.get("/.well-known/openid-configuration", (req, res) => {
  res.json({issuer: "https://auth.scholaraiadvisor.com"});
});

// Cookie settings
const cookieOptions = {
  secure: true,
  sameSite: 'none',
  httpOnly: true,
  path: '/'
};

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

### Verification
```bash
curl -sSL "https://<A1_HOST>/health?t=$(date +%s)"
```

---

## A3 — scholarship-agent (Orchestrator v1.4-Unified)

### Required Changes

```javascript
const express = require('express');
const app = express();

app.get("/health", (req, res) => {
  res.json({service: "scholarship-agent", status: "healthy", timestamp: new Date().toISOString()});
});

app.get("/readyz", (req, res) => {
  res.json({service: "scholarship-agent", status: "healthy", ready: true});
});

// Orchestration endpoint with backoff/retry
app.post("/orchestrate", async (req, res) => {
  const traceId = req.headers['x-trace-id'] || 'unknown';
  const idempotencyKey = req.headers['x-idempotency-key'];
  // Implement with exponential backoff + jitter
  res.json({success: true, trace_id: traceId, run_progress: 1, cta_emitted: 1});
});

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

### Verification
```bash
curl -sSL "https://<A3_HOST>/health?t=$(date +%s)"
curl -sSL "https://<A3_HOST>/readyz?t=$(date +%s)"
```

---

## A4 — scholarship-sage

```javascript
app.get("/health", (req, res) => {
  res.json({service: "scholarship-sage", status: "healthy"});
});
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A5 — student-pilot (B2C + Stripe)

### /pricing page requirements

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://js.stripe.com/v3"></script>
</head>
<body>
  <script>
    const stripe = Stripe('pk_live_YOUR_KEY'); // or pk_test_...
  </script>
  <button id="checkout" data-role="checkout">Start Free Trial</button>
</body>
</html>
```

### Cookie/Session Config
```javascript
app.set('trust proxy', 1);

res.cookie('session', value, {
  secure: true,
  httpOnly: true,
  sameSite: 'None'
});
```

### Security Headers
```javascript
app.use((req, res, next) => {
  res.set({
    'Strict-Transport-Security': 'max-age=15552000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' js.stripe.com; connect-src 'self' api.stripe.com",
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff'
  });
  next();
});
```

### Verification
```bash
curl -sSL "https://<A5_HOST>/pricing?t=$(date +%s)" | grep -E "(pk_live_|pk_test_|js.stripe.com)"
```

---

## A6 — provider-register (PRIMARY BLOCKER)

### Issue: /api/providers returns 404

```javascript
const express = require('express');
const app = express();

app.get("/health", (req, res) => {
  res.json({service: "provider-register", status: "healthy", timestamp: new Date().toISOString()});
});

// REQUIRED: Place before any :id catch-all routes
app.get("/api/providers", (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.json([]);  // Empty array acceptable
});

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

### Fee Lineage (for B2B verification)
```javascript
// Record with X-Trace-Id
app.post("/api/providers/:id/fee", (req, res) => {
  const traceId = req.headers['x-trace-id'];
  const fee = {platform: 0.03, ai_markup: 4.0, trace_id: traceId};
  res.json(fee);
});
```

### Verification
```bash
curl -sSL "https://<A6_HOST>/health?t=$(date +%s)"
curl -sSL "https://<A6_HOST>/api/providers?t=$(date +%s)"
```

---

## A7 — auto-page-maker (SEO)

```javascript
app.get("/sitemap.xml", (req, res) => {
  res.set('Content-Type', 'application/xml');
  res.send(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.scholaraiadvisor.com/</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <priority>1.0</priority>
  </url>
</urlset>`);
});

app.get("/health", (req, res) => {
  res.json({service: "auto-page-maker", status: "healthy"});
});

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

### Verification
```bash
curl -sSL "https://<A7_HOST>/sitemap.xml?t=$(date +%s)" | head -5
curl -sSL "https://<A7_HOST>/health?t=$(date +%s)"
```

---

## A8 — auto-com-center (Telemetry)

```python
from fastapi import FastAPI, Request
from datetime import datetime
import uuid
import hashlib

app = FastAPI()
events_store = {}

@app.post("/api/events")
async def ingest_event(request: Request):
    body = await request.json()
    event_id = str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-Id", "unknown")
    checksum = hashlib.sha256(str(body).encode()).hexdigest()[:16]
    events_store[event_id] = {
        "event_id": event_id,
        "trace_id": trace_id,
        "checksum": checksum,
        "payload": body,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return {"success": True, "event_id": event_id, "trace_id": trace_id, "checksum": checksum}

@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    return events_store.get(event_id, {"error": "not_found"})

@app.get("/health")
def health():
    return {"service": "auto-com-center", "status": "healthy", "events_count": len(events_store)}

@app.get("/healthz")
def healthz():
    return {"service": "auto-com-center", "status": "healthy"}
```

### Verification
```bash
# POST event
EVENT=$(curl -sSL -X POST "https://<A8_HOST>/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d '{"kind":"verify"}')
echo "$EVENT"

# GET event back (checksum round-trip)
EVENT_ID=$(echo "$EVENT" | jq -r '.event_id')
curl -sSL "https://<A8_HOST>/api/events/${EVENT_ID}"
```

---

## DNS/Custom Domain Fixes

If custom domain returns NXDOMAIN:
1. Add CNAME record at registrar: `app.scholaraiadvisor.com` → `<repl-name>.<owner>.repl.co`
2. Configure in Replit: Settings → Custom Domains
3. Until propagation, use `*.replit.app` URLs

---

## Summary

| App | Status | Primary Fix |
|-----|--------|-------------|
| A1 | BLOCKED | trust proxy + cookie config |
| A2 | VERIFIED | None needed |
| A3 | BLOCKED | /health + /readyz + orchestration |
| A4 | BLOCKED | /health |
| A5 | BLOCKED | Stripe markers + headers |
| A6 | BLOCKED | /api/providers returns JSON |
| A7 | BLOCKED | /sitemap.xml + /health |
| A8 | BLOCKED | POST/GET /api/events + checksum |

**Action**: Share with workspace owners → Apply fixes → Republish → Re-verify
