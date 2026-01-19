# Reliability Soak T+2h Snapshot
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-052
**Timestamp**: 2026-01-19T06:02:00Z

---

## Trust Metrics ✅

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| FPR | ≤5% | **2.8%** | ✅ |
| Precision | ≥90% | **96.4%** | ✅ |
| Recall | ≥75% | **76.0%** | ✅ |

---

## Calibration Parameters

| Parameter | Value |
|-----------|-------|
| τc (threshold) | 0.72 |
| HITL band | 0.60–0.72 |
| Borderline cases | 142 → HITL |

---

## Controls Active

- **Freeze**: τc=0.72 locked through T+12h
- **A7 SEO**: 100 pages/day cap
- **429 tolerance**: zero
- **Alerting**: FPR ≥4.5% or Recall <0.75 for 15min → page ops

---

## Taper Plan (T+12h if stable)

| Condition | Action |
|-----------|--------|
| FPR ≤3.5% + Recall ≥0.76 for 2h | Reduce HITL 0.66–0.72 to 50% |
| Any breach | Revert to 100% HITL |

---

## Shadow Scoring

- Legacy τ=0.60 running in SHADOW ONLY
- No user-facing decisions
