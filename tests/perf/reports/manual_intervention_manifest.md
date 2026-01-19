# Manual Intervention Manifest (Golden Path)
**FIX Run**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027
**VERIFY Run**: CEOSPRINT-20260113-VERIFY-ZT3G-028
**Timestamp**: 2026-01-19T08:04:16Z

---

## A0 — Global Port Binding

```javascript
// Node.js/Express
app.listen(process.env.PORT || 3000, "0.0.0.0");
```

```python
# FastAPI/Uvicorn
uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

---

## A1 — scholar-auth
```javascript
app.set('trust proxy', 1);
app.get("/health", (_, res) => res.json({service: "scholar-auth", status: "healthy"}));
// Cookies: { secure: true, sameSite: "none", httpOnly: true }
```

---

## A3 — scholarship-agent
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-agent", status: "healthy"}));
app.get("/readyz", (_, res) => res.json({service: "scholarship-agent", ready: true}));
```

---

## A4 — scholarship-sage
```javascript
app.get("/health", (_, res) => res.json({service: "scholarship-sage", status: "healthy"}));
```

---

## A5 — student-pilot (Stripe Guardrail)
```javascript
app.post("/create-checkout-session", (req, res) => {
  const key = process.env.STRIPE_PUBLISHABLE_KEY || "";
  if (key.startsWith("pk_live_") && !fs.existsSync("tests/perf/reports/hitl_approvals.log")) 
    return res.status(403).json({error: "SAFETY_LOCK_ACTIVE"});
});
```

---

## A6 — provider-register
```javascript
app.get("/api/providers", (_, res) => res.json([]));
```

---

## A7 — auto-page-maker
```javascript
app.get("/sitemap.xml", (_, res) => {
  res.set('Content-Type', 'application/xml');
  res.send('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>');
});
```

---

## A8 — auto-com-center
```javascript
app.post("/api/events", (req, res) => {
  res.json({success: true, event_id: Date.now(), trace_id: req.headers["x-trace-id"] || "no-trace"});
});
```

---

| App | Status |
|-----|--------|
| A2 | **VERIFIED** |
| A1, A3-A8 | BLOCKED |
