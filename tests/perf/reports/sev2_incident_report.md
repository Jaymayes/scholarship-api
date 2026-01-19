# SEV-2 Incident Report
**Incident ID**: CIR-20260119-001
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-056
**A8 Attestation ID**: evt_a26b5c759a49
**Opened**: 2026-01-19T15:44:54Z
**Status**: ACTIVE

---

## Kill Switch Activated

| Action | Status |
|--------|--------|
| TRAFFIC_CAP_B2C_PILOT | 0% ✅ |
| B2C_CAPTURE | paused ✅ |
| CHANGE_FREEZE | active ✅ |
| Refunds | enabled ✅ |

---

## Error Codes Mapped

| Code | Description |
|------|-------------|
| AUTH_DB_UNREACHABLE | A1 database connection failure |
| RETRY_STORM_SUPPRESSED | Circuit breaker activated |

---

## War Room Roles

| Role | Owner |
|------|-------|
| Incident Commander | Head of Platform (A1/A8) |
| Ops/Comms Lead | Head of Sales/Ops |
| Scribe | Watchtower owner (A8) |
| Eng Lead A1 | Platform team |
| Eng Lead A3 | Agent team |
| Eng Lead A5/A7 | Golden Path compliance |

---

## 60-Minute Path-to-Green

### T+0-10 min: Containment
- [ ] A3 worker concurrency → 0
- [ ] Pause crons/queues hitting A1
- [ ] Circuit-breaker "open" for A1 dependency
- [ ] Secrets audit: confirm A3 has no DATABASE_URL
- [ ] Snapshot logs/metrics for RCA

### T+10-25 min: A1 Stabilization
- [ ] Verify DATABASE_URL + SELECT 1
- [ ] Enforce pooling: max=10, min=2, idleTimeout=10s
- [ ] acquireTimeout=3s, statement_timeout=5s
- [ ] Reduce HTTP worker concurrency
- [ ] Add health markers: db_connected, pool_in_use, pool_idle

### T+25-40 min: Canary
- [ ] Single A3→A1 request via gateway
- [ ] Confirm 200 + db_connected=true
- [ ] Re-enable A3 at concurrency=1, breaker half-open
- [ ] Test single job, verify backoff metrics

### T+40-60 min: Stabilize
- [ ] Raise A3 concurrency to 2-3
- [ ] Enable global rate limiter (50 rps, burst 20)
- [ ] Begin 60-min green snapshot clock

---

## Exit Criteria

| Metric | Target | Status |
|--------|--------|--------|
| A1 uptime | 60 min green | PENDING |
| db_connected | true | PENDING |
| Pool utilization | <80% | PENDING |
| Auth 5xx | 0 | PENDING |
| RETRY_STORM events | 0 | PENDING |
| P95 core (A1-A4) | ≤120ms | PENDING |
| P95 aux (A6/A8) | ≤200ms | PENDING |
| A3 secrets audit | clean | PENDING |
| A5/A7 Golden Path | compliant | PENDING |
| 3-of-3 confirmations | verified | PENDING |
