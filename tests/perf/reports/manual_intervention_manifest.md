# Manual Intervention Manifest (Golden Path)
**Order ID**: SAA-EO-2026-01-19-01
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-056
**Timestamp**: 2026-01-19T15:18:53Z
**Deadline**: 8 hours (2026-01-19T23:18:53Z)

---

## DaaS Hard Rules (ALL APPS)

```
NO LOCAL STATE
ALL READS/WRITES VIA CORE API
DATABASE_URL NEVER EMBEDDED IN A5/A7
```

---

## A5 — student-pilot (Golden Path)

### Required Changes:
```javascript
// 1. Remove any local DB connections
// FORBIDDEN: const db = new Database(process.env.DATABASE_URL);
// REQUIRED: All data via Core API

// 2. Health endpoint
app.get("/health", (_, res) => res.json({
  service: "student-pilot",
  status: "healthy",
  version: process.env.VERSION
}));

// 3. Readyz endpoint
app.get("/readyz", (_, res) => res.json({
  service: "student-pilot",
  ready: true
}));

// 4. Security headers middleware
app.use((req, res, next) => {
  res.set('Strict-Transport-Security', 'max-age=15552000; includeSubDomains');
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  next();
});

// 5. B2C Pilot Checkout (with safety lock)
app.post("/create-checkout-session", async (req, res) => {
  const cohort_id = "B2C-PILOT-001";
  const run_id = "CEOSPRINT-20260113-VERIFY-ZT3G-056";
  
  // Safety check
  if (process.env.SAFETY_LOCK === "active" && !process.env.CEO_OVERRIDE) {
    return res.status(403).json({error: "SAFETY_LOCK_ACTIVE"});
  }
  
  // Log to A8
  await fetch(A8_URL + "/api/events", {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-Trace-Id": `${run_id}.checkout`},
    body: JSON.stringify({run_id, cohort_id, event_type: "charge", status: "pending"})
  });
});
```

### Release Gate Checklist:
- [ ] Manifest digest matches `golden_path.yaml`
- [ ] `/health` returns 200 + functional markers
- [ ] `/readyz` returns green
- [ ] Security headers present
- [ ] 3-of-3 confirmation logged in A8

---

## A7 — auto-page-maker (Golden Path)

### Required Changes:
```javascript
// 1. Remove any local DB connections
// FORBIDDEN: Any DATABASE_URL usage
// REQUIRED: All scholarship data via A2 Core API

// 2. Health endpoint
app.get("/health", (_, res) => res.json({
  service: "auto-page-maker",
  status: "healthy"
}));

// 3. Sitemap endpoint
app.get("/sitemap.xml", async (_, res) => {
  res.set('Content-Type', 'application/xml');
  // Fetch pages from Core API, not local DB
  res.send('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">...</urlset>');
});

// 4. Security headers middleware
app.use((req, res, next) => {
  res.set('Strict-Transport-Security', 'max-age=15552000; includeSubDomains');
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  next();
});
```

### Release Gate Checklist:
- [ ] Manifest digest matches `golden_path.yaml`
- [ ] `/health` returns 200 + functional markers
- [ ] `/sitemap.xml` returns valid XML
- [ ] Security headers present
- [ ] 3-of-3 confirmation logged in A8

---

## A8 Attestation Template

After A5/A7 redeploy, post to shiproom:

```
Subject: CEO-OVERRIDE B2C PILOT ZT3G-056

A5_commit: <sha>
A7_commit: <sha>
manifest_digest: <hash>
build_artifact_sha: <hash>
a8_attestation_id: <evt_xxx>
60-min snapshot window (UTC): <start>–<end>
P95 core: <ms> / aux: <ms>
3-of-3 confirmations: A5 ✓ A7 ✓
checksum parity: ✓
```

---

## Success Criteria for Ramp Request

Two consecutive 60-minute snapshots with:
- A5/A7: 200 OK + functional markers
- P95 ≤120ms on A1-A4
- P95 ≤200ms on A6/A8
