# Performance Summary - All Canary Stages

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE4-033  
**Protocol**: AGENT3_CANARY_ROLLOUT v1.0  
**Last Updated**: 2026-01-22T06:15:46Z

---

## Stage Progression

| Stage | Traffic | Probes | Server P95 | Success | 5xx | Status |
|-------|---------|--------|------------|---------|-----|--------|
| 1 | 5% | 60 | 139ms | 100% | 0% | ✅ PASS |
| 2 | 25% | 200 | 130ms | 100% | 0% | ✅ PASS |
| 3 | 50% | 400 | 133ms | 100% | 0% | ✅ PASS |
| 4 | 100% | 800+ | 134ms | 100% | 0% | ⏳ IN PROGRESS |

---

## Cumulative Statistics

| Metric | Value |
|--------|-------|
| Total Probes | 1,460+ |
| Total Failures | 0 |
| Overall Success Rate | 100% |
| P95 Range | 130-139ms |

---

## Error Budget (Stage 4 - 24h)

| Metric | Budget | Spent | Remaining |
|--------|--------|-------|-----------|
| SLO Violation | 7.2 min | 0 min | 100% |

---

## Notes

- Server P95 consistently ~130-140ms due to /health DB queries
- Core API endpoints (/) respond in 3-6ms
- /pricing and /browse require authentication (expected behavior)
