# Risk Log
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-052

---

## Entry 1: FPR Spike (Resolved)

| Field | Value |
|-------|-------|
| Timestamp | 2026-01-19T04:00:00Z |
| Metric | FPR |
| Peak Value | 12% |
| Target | ≤5% |
| Duration | ~30 min |

### Root Cause
- Threshold drift from τ=0.60 to unmonitored range
- Insufficient HITL coverage on 0.60–0.72 band

### Corrective Actions
1. Calibrated τc to 0.72
2. Enabled 100% HITL on 0.60–0.72 band
3. Routed 142 borderline cases to human review
4. Deployed calibration with temperature adjustment

### Owner
- Trust Engineering

### Status
- **RESOLVED** at T+2h
- FPR now 2.8%

---

## Active Monitoring

| Risk | Threshold | Action |
|------|-----------|--------|
| FPR drift | ≥4.5% for 15min | Page ops |
| Recall drop | <0.75 for 15min | Page ops |
| P95 latency | >140ms for 10min | Add reviewer + cache |
