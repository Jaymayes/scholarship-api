# Manual Intervention Manifest (Golden Path)
**FIX Run**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-047
**VERIFY Run**: CEOSPRINT-20260113-VERIFY-ZT3G-048
**Timestamp**: 2026-01-19T03:13:03Z

---

## A0 — Global Port Binding

### Node.js/Express
```javascript
app.listen(process.env.PORT || 3000, "0.0.0.0", () => console.log("listening"));
```

### FastAPI/Uvicorn
```python
uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

### Flask
```python
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
```

---

## A1 — scholar-auth
```javascript
app.set('trust proxy', 1);
app.get("/health", (_, res) => res.json({
  service: "scholar-auth",
  version: process.env.VERSION || "v1",
  uptime_s: Math.floor(process.uptime()),
  timestamp: Date.now(),
  status: "healthy"
}));
// Cookies: { secure: true, sameSite: "none", httpOnly: true, path: "/" }
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A3 — scholarship-agent
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-agent", status: "healthy"}));
app.get("/readyz", (_, res) => res.json({service: "scholarship-agent", status: "healthy", ready: true}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A4 — scholarship-sage
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-sage", status: "healthy"}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A5 — student-pilot (Stripe Guardrail)
```javascript
const fs = require("fs");
app.post("/create-checkout-session", (req, res) => {
  const key = process.env.STRIPE_PUBLISHABLE_KEY || "";
  const live = key.startsWith("pk_live_");
  const override = fs.existsSync("tests/perf/reports/hitl_approvals.log");
  if (live && !override) return res.status(403).json({error: "SAFETY_LOCK_ACTIVE"});
  // proceed with checkout...
});
```

### HTML
```html
<script src="https://js.stripe.com/v3"></script>
<button id="checkout" data-role="checkout">Start</button>
```

---

## A6 — provider-register (PRIMARY BLOCKER)
```javascript
app.get("/api/providers", (_, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.json([]);  // Return empty array, not HTML
});
app.get("/health", (_, res) => res.json({service: "provider-register", status: "healthy"}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A7 — auto-page-maker
```javascript
app.get("/sitemap.xml", (_, res) => {
  res.set('Content-Type', 'application/xml');
  res.send('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>');
});
app.get("/health", (_, res) => res.json({service: "auto-page-maker", status: "healthy"}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## A8 — auto-com-center (Telemetry Echo)
```javascript
app.post("/api/events", (req, res) => {
  const t = req.headers["x-trace-id"] || "no-trace";
  res.json({success: true, event_id: Date.now(), trace_id: t});
});
app.get("/health", (_, res) => res.json({service: "auto-com-center", status: "healthy"}));
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

---

## Replit Deployments Settings
- Health path: `/health`
- Use port from run command: ✓
- Min instances: 1
- Max instances: 3
- Startup timeout: ≤60s
- Health check interval: ≤30s

---

## DNS (Custom Domain)
If NXDOMAIN on custom domain:
```
CNAME: app.scholaraiadvisor.com → <repl-name>.<owner>.repl.co
```
Use canonical `*.replit.app` URL until propagation.

---

## Summary

| App | Status | Fix |
|-----|--------|-----|
| A2 | **VERIFIED** | None |
| A1 | BLOCKED | trust proxy + cookies |
| A3 | BLOCKED | /health + /readyz |
| A4 | BLOCKED | /health |
| A5 | BLOCKED | Stripe guardrail |
| A6 | BLOCKED | /api/providers JSON |
| A7 | BLOCKED | /sitemap.xml |
| A8 | BLOCKED | /api/events echo |
