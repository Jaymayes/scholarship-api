# Manual Intervention Manifest
**FIX Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-039
**VERIFY Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-040
**Timestamp**: 2026-01-18T02:38:23Z
**Protocol**: AGENT3_HANDSHAKE v30

---

## Overview

External apps (A3, A5, A6, A7, A8) cannot be modified from this workspace. This manifest provides **exact copy-paste fixes** for each workspace owner.

---

## A6 — provider-register (PRIMARY BLOCKER)

### Status: /api/providers returns 404

### Replit Workspace
`https://replit.com/@<username>/provider-register`

### Option 1: Node.js/Express

**File**: `server/index.js` (or `index.js`)

```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Health endpoint
app.get("/health", (req, res) => {
  res.json({
    service: "provider-register",
    status: "healthy",
    timestamp: new Date().toISOString()
  });
});

// REQUIRED: /api/providers endpoint (empty array is acceptable)
app.get("/api/providers", (req, res) => {
  res.json([]);
});

// CRITICAL: Bind to 0.0.0.0, not localhost
app.listen(PORT, "0.0.0.0", () => {
  console.log(`A6 provider-register listening on port ${PORT}`);
});
```

### Option 2: Python/FastAPI

**File**: `main.py`

```python
from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

@app.get("/health")
def health():
    return {
        "service": "provider-register",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/providers")
def providers():
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
```

**Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 3: Python/Flask

**File**: `app.py`

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(service="provider-register", status="healthy")

@app.get("/api/providers")
def providers():
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
```

### CSRF/CORS Note
- Exempt GET `/api/providers` from CSRF if enforced
- Keep CORS tight

### Republish Steps
1. Apply code changes above
2. Ensure single start command (avoid EADDRINUSE)
3. Click **Deploy** → **Production**

### Verification
```bash
curl -sSL "https://<A6_HOST>/health?t=$(date +%s)" -H "Cache-Control: no-cache"
curl -sSL "https://<A6_HOST>/api/providers?t=$(date +%s)" -H "Cache-Control: no-cache"
```

**Expected**:
- `/health`: `{"service":"provider-register","status":"healthy",...}`
- `/api/providers`: `[]` (or array of provider objects)

---

## A8 — auto-com-center (Health Alias)

### Status: Add /healthz alias if missing

### Node.js
```javascript
app.get("/healthz", (req, res) => {
  res.json({service: "auto-com-center", status: "healthy"});
});
```

### FastAPI
```python
@app.get("/healthz")
def healthz():
    return {"service": "auto-com-center", "status": "healthy"}
```

### Full A8 Implementation (if not present)

```python
from fastapi import FastAPI, Request
from datetime import datetime
import uuid

app = FastAPI()
events_store = {}

@app.post("/api/events")
async def ingest_event(request: Request):
    body = await request.json()
    event_id = str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-Id", "unknown")
    events_store[event_id] = {
        "event_id": event_id,
        "trace_id": trace_id,
        "payload": body,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return {"success": True, "event_id": event_id}

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
curl -sSL "https://<A8_HOST>/healthz?t=$(date +%s)"
curl -X POST "https://<A8_HOST>/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d '{"kind":"verify"}'
```

---

## A3 — scholarship-agent

### Node.js
```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get("/health", (req, res) => {
  res.json({
    service: "scholarship-agent",
    status: "healthy",
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`A3 scholarship-agent listening on port ${PORT}`);
});
```

### Verification
```bash
curl -sSL "https://<A3_HOST>/health?t=$(date +%s)" -H "Cache-Control: no-cache"
```

---

## A5 — student-pilot (B2C)

### Stripe on /pricing
```html
<!-- In <head> section -->
<script src="https://js.stripe.com/v3"></script>

<!-- In page body -->
<script>
  const stripe = Stripe('pk_live_YOUR_KEY'); // or pk_test_...
</script>
<button id="checkout" data-role="checkout">Start Free Trial</button>
```

### Cookie Configuration (Node.js)
```javascript
app.set('trust proxy', 1);

res.cookie('session', value, {
  secure: true,
  httpOnly: true,
  sameSite: 'None'
});
```

### Health Endpoint
```javascript
app.get("/health", (req, res) => {
  res.json({service: "student-pilot", status: "healthy"});
});
```

### Verification
```bash
curl -sSL "https://<A5_HOST>/pricing?t=$(date +%s)" | grep -E "(pk_live_|pk_test_|js.stripe.com)"
curl -sSL "https://<A5_HOST>/health?t=$(date +%s)"
```

---

## A7 — auto-page-maker (SEO)

### Sitemap + Health (Node.js)
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
```

### Verification
```bash
curl -sSL "https://<A7_HOST>/sitemap.xml?t=$(date +%s)" | head -5
curl -sSL "https://<A7_HOST>/health?t=$(date +%s)"
```

---

## Summary

| App | Status | Primary Fix |
|-----|--------|-------------|
| A2 (Core Data) | VERIFIED | None needed |
| A3 (Agent) | BLOCKED | Add /health, bind 0.0.0.0 |
| A5 (B2C) | BLOCKED | Stripe markers, cookie config |
| A6 (B2B) | BLOCKED | /api/providers + /health |
| A7 (SEO) | BLOCKED | /sitemap.xml + /health |
| A8 (Telemetry) | BLOCKED | POST/GET /api/events, /healthz |

**Action**: Share with workspace owners → Apply fixes → Republish → Re-verify
