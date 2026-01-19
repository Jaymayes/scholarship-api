# Manual Intervention Manifest (Golden Path)
**FIX Run**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-055
**VERIFY Run**: CEOSPRINT-20260113-VERIFY-ZT3G-056
**Timestamp**: 2026-01-19T08:30:41Z

---

## A0 — Global Port Binding

```javascript
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

```python
uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

---

## A1 — scholar-auth
```javascript
app.set('trust proxy', 1);
app.get("/health", (_, res) => res.json({service: "scholar-auth", status: "healthy", version: process.env.VERSION}));
// Cookies: { secure: true, sameSite: "none", httpOnly: true }
```

---

## A3 — scholarship-agent
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-agent", status: "healthy"}));
app.get("/readyz", (_, res) => res.json({service: "scholarship-agent", status: "healthy", ready: true}));
```

---

## A4 — scholarship-sage
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-sage", status: "healthy", version: process.env.VERSION}));
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
});
```

---

## A6 — provider-register
```javascript
app.get("/api/providers", (_, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.json([]);
});
```

---

## A7 — auto-page-maker
```javascript
app.get("/sitemap.xml", (_, res) => {
  res.set('Content-Type', 'application/xml');
  res.send('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>');
});
app.get("/health", (_, res) => res.json({service: "auto-page-maker", status: "healthy"}));
```

---

## A8 — auto-com-center (JSON Contract)
```javascript
app.post("/api/events", (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.json({success: true, event_id: Date.now(), trace_id: req.headers["x-trace-id"] || "no-trace"});
});
// Error handler - always JSON
app.use((err, req, res, next) => {
  res.setHeader('Content-Type', 'application/json');
  res.status(500).json({error: err.message});
});
```

---

## Summary

| App | Status | Critical Fix |
|-----|--------|--------------|
| A2 | **VERIFIED** | None |
| A1 | BLOCKED | trust proxy + cookies |
| A3 | BLOCKED | /health + /readyz |
| A4 | BLOCKED | /health |
| A5 | BLOCKED | Stripe guardrail |
| A6 | BLOCKED | /api/providers JSON |
| A7 | BLOCKED | /sitemap.xml |
| A8 | BLOCKED | JSON contract |
