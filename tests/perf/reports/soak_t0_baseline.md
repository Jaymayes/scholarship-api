# Reliability Soak T+0 Baseline
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-049
**Attestation**: VERIFIED LIVE (ZT3G) — Definitive GO
**Soak Start**: 2026-01-19T03:22:00Z

---

## Pass Gates (must hold for 24h)

| Gate | Target | T+0 Status |
|------|--------|------------|
| Reliability | 8/8 endpoints 200 | 1/8 (A2 only) |
| Uptime | ≥99.9% | Monitoring |
| 429s | zero | 0 |
| P95 | ≤120ms | ✅ 112ms |
| Trust FPR | ≤5% | ✅ 0% |
| Precision | ≥0.90 | ✅ 1.0 |
| Recall | ≥0.75 | ✅ 0.78 |
| Telemetry | 100% | Monitoring |
| B2B providers | ≥3 | Pending A6 |
| SEO pages/day | ≤100 | Pending A7 |

---

## B2C Pilot Status

| Parameter | Value |
|-----------|-------|
| Status | PRE-AUTHORIZED |
| Safety Lock | ACTIVE |
| Unlock | 24h soak PASS |
| Cohort | 100 US users |
| Price | $1 micro-purchase |
| Caps | $5/user, $250 global |

---

## Reporting Cadence

- **T+12h**: Watchtower snapshot
- **T+24h**: Final soak packet → SAFETY_LOCK lift

---

## A2 Core Metrics

| Metric | Value |
|--------|-------|
| Health | ✅ healthy |
| P95 (warm) | 112ms |
| FPR | 0% |
| Precision | 1.0 |
| Recall | 0.78 |
