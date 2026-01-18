# Manual Intervention Manifest
**FIX Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-043
**VERIFY Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-044
**Timestamp**: 2026-01-18T03:25:09Z
**Protocol**: AGENT3_HANDSHAKE v30

---

## A6 — provider-register (PRIMARY BLOCKER)

### Issue: `/api/providers` returns 404

### Option 1: Node.js/Express
**File**: `server/index.js` or `routes/index.js`

```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Health endpoint
app.get("/health", (req, res) => {
  res.json({service: "provider-register", status: "healthy", timestamp: new Date().toISOString()});
});

// REQUIRED: /api/providers (empty array acceptable)
// NOTE: Place before any catch-all or :id routes
app.get("/api/providers", (req, res) => {
  res.json([]);
});

app.listen(PORT, "0.0.0.0", () => console.log(`A6 up on ${PORT}`));
```

### Option 2: FastAPI
**File**: `main.py`

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"service": "provider-register", "status": "healthy"}

@app.get("/api/providers")
def providers():
    return []
```

**Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 3: Flask
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

### Notes
- Exempt GET `/api/providers` from CSRF if enforced
- Keep CORS tight (GET only)
- Ensure route ordering: `/api/providers` before any `:id` catch-all

### Steps
1. Apply code above
2. Click **Deploy** → **Production**
3. Verify:
```bash
curl -sSL "https://<A6_HOST>/health?t=$(date +%s)"
curl -sSL "https://<A6_HOST>/api/providers?t=$(date +%s)"
```

---

## A8 — auto-com-center (/healthz alias)

### Issue: `/healthz` returns 404 (compatibility gap)

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

### Verify
```bash
curl -sSL "https://<A8_HOST>/healthz?t=$(date +%s)"
```

---

## A3 — scholarship-agent

```javascript
app.get("/health", (req, res) => {
  res.json({service: "scholarship-agent", status: "healthy", timestamp: new Date().toISOString()});
});
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A5 — student-pilot (Stripe markers)

**In `/pricing` page:**
```html
<script src="https://js.stripe.com/v3"></script>
<script>const stripe = Stripe('pk_live_...');</script>
<button id="checkout" data-role="checkout">Start</button>
```

**Cookie config:**
```javascript
app.set('trust proxy', 1);
res.cookie('session', value, {secure: true, httpOnly: true, sameSite: 'None'});
```

---

## A7 — auto-page-maker

```javascript
app.get("/sitemap.xml", (req, res) => {
  res.set('Content-Type', 'application/xml');
  res.send(`<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.scholaraiadvisor.com/</loc></url></urlset>`);
});
app.get("/health", (req, res) => res.json({service: "auto-page-maker", status: "healthy"}));
```

---

## Summary

| App | Status | Fix |
|-----|--------|-----|
| A2 | VERIFIED | None |
| A3 | BLOCKED | /health |
| A5 | BLOCKED | Stripe markers |
| A6 | BLOCKED | /api/providers |
| A7 | BLOCKED | /sitemap.xml |
| A8 | BLOCKED | /healthz alias |
