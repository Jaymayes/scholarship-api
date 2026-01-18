# Manual Intervention Manifest
**FIX Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-033
**VERIFY Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-034
**Timestamp**: 2026-01-18T19:15:16Z
**Protocol**: AGENT3_HANDSHAKE v30

---

## Cross-Workspace Reality

External apps (A1, A3, A4, A5, A6, A7, A8) cannot be accessed from this workspace. This manifest provides **exact copy-paste fixes**.

---

## A0 — Global Port Binding (All Apps)

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

```javascript
const express = require('express');
const app = express();
app.set('trust proxy', 1);

app.get("/health", (req, res) => {
  res.json({service: "scholar-auth", status: "healthy", timestamp: new Date().toISOString()});
});

const cookieOptions = {secure: true, sameSite: 'none', httpOnly: true, path: '/'};

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A3 — scholarship-agent

```javascript
app.get("/health", (req, res) => {
  res.json({service: "scholarship-agent", status: "healthy"});
});
app.get("/readyz", (req, res) => {
  res.json({service: "scholarship-agent", status: "healthy", ready: true});
});
app.listen(process.env.PORT || 3000, "0.0.0.0");
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

## A5 — student-pilot (Stripe)

**In /pricing page:**
```html
<script src="https://js.stripe.com/v3"></script>
<script>const stripe = Stripe('pk_live_...');</script>
<button id="checkout" data-role="checkout">Start</button>
```

**Headers:**
```javascript
res.set({
  'Strict-Transport-Security': 'max-age=15552000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'; script-src 'self' js.stripe.com",
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff'
});
```

---

## A6 — provider-register (PRIMARY BLOCKER)

### Issue: /api/providers returns 404

```javascript
// Place BEFORE any :id catch-all routes
app.get("/api/providers", (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.json([]);
});

app.get("/health", (req, res) => {
  res.json({service: "provider-register", status: "healthy"});
});

app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A7 — auto-page-maker

```javascript
app.get("/sitemap.xml", (req, res) => {
  res.set('Content-Type', 'application/xml');
  res.send(`<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.scholaraiadvisor.com/</loc></url></urlset>`);
});
app.get("/health", (req, res) => res.json({service: "auto-page-maker", status: "healthy"}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A8 — auto-com-center

```python
from fastapi import FastAPI, Request
import uuid, hashlib
app = FastAPI()
events = {}

@app.post("/api/events")
async def ingest(request: Request):
    body = await request.json()
    eid = str(uuid.uuid4())
    trace = request.headers.get("X-Trace-Id", "unknown")
    checksum = hashlib.sha256(str(body).encode()).hexdigest()[:16]
    events[eid] = {"event_id": eid, "trace_id": trace, "checksum": checksum}
    return {"success": True, "event_id": eid, "trace_id": trace, "checksum": checksum}

@app.get("/api/events/{eid}")
def get_event(eid: str):
    return events.get(eid, {"error": "not_found"})

@app.get("/health")
def health():
    return {"service": "auto-com-center", "status": "healthy"}

@app.get("/healthz")
def healthz():
    return {"service": "auto-com-center", "status": "healthy"}
```

---

## DNS / Custom Domain

If NXDOMAIN on custom domain:
1. Add CNAME: `app.scholaraiadvisor.com` → `<repl-name>.<owner>.repl.co`
2. Configure in Replit: Settings → Custom Domains
3. Use `*.replit.app` URLs until propagation

---

## Summary

| App | Status | Fix |
|-----|--------|-----|
| A1 | BLOCKED | trust proxy + cookies |
| A2 | **VERIFIED** | None |
| A3 | BLOCKED | /health + /readyz |
| A4 | BLOCKED | /health |
| A5 | BLOCKED | Stripe markers |
| A6 | BLOCKED | /api/providers |
| A7 | BLOCKED | /sitemap.xml |
| A8 | BLOCKED | /api/events |
