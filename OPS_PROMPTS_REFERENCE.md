# Operations Prompts - Quick Reference

This document maps your operational prompts to executable scripts and API endpoints.

---

## Daily Ops

**Prompt:**
> "Run observability endpoints: health-summary, latency-dashboard, kpi-report(24h). Flag any endpoint group with P95 >200ms. Success = baseline captured and slow endpoints identified. Artifact: /ops/scholarship-api/daily_ops_snapshot.json"

**Execute:**
```bash
python scripts/daily_ops.py
```

**API Endpoints:**
```bash
curl https://your-api.replit.app/api/v1/observability/health-summary
curl https://your-api.replit.app/api/v1/observability/latency-dashboard
curl https://your-api.replit.app/api/v1/observability/kpi-report?period_hours=24
```

**Artifact:** `ops/scholarship-api/daily_ops_snapshot.json`

**Success Criteria:**
- ✅ Baseline captured: Yes
- ✅ Slow endpoints identified: Count provided
- ✅ Health status: Documented

---

## Release/Validation

**Prompt:**
> "Execute 48-hour optimization plan: enable Redis caching, reorder middleware, add prepared statements, run stress tests, compare baselines. Goal: -80 to -120ms P95. Success = documented before/after with sustained improvement. Artifact: /ops/scholarship-api/optimization_before_after.md"

**Execute:**
```bash
python scripts/release_validation.py
```

**Alternative (Full Shell Script):**
```bash
./scripts/execute_optimization_plan.sh
```

**Artifact:** `ops/scholarship-api/optimization_before_after.md`

**Success Criteria:**
- ✅ Before/after documented: Yes
- ✅ P95 reduction: Measured (goal: ≥80ms)
- ✅ Sustained improvement: Error rate <1%
- ✅ Stress tests: Passed

---

## KPI/Reporting

**Prompt:**
> "Report quick-wins and stretch-opportunities usage, conversion to applications, credit spend, and MRR estimates. Success = tie feature usage to revenue impact. Artifact: /ops/scholarship-api/kpi_24h.txt"

**Execute:**
```bash
python scripts/kpi_reporting.py
```

**API Endpoint:**
```bash
curl https://your-api.replit.app/api/v1/observability/kpi-report?period_hours=24
```

**Artifact:** `ops/scholarship-api/kpi_24h.txt`

**Success Criteria:**
- ✅ Feature usage tracked: Quick-wins + Stretch
- ✅ Conversion measured: Applications from predictive calls
- ✅ Credit spend documented: Total credits consumed
- ✅ Revenue impact calculated: Tied to MRR

---

## Incident Response

**Prompt:**
> "Run hot-path stress tests and enforce rollback if error rate >5% or auth failures >0.5%. Produce latency distribution and fix list. Artifact: /ops/scholarship-api/stress_test_results.md"

**Execute:**
```bash
python scripts/incident_response.py
```

**Direct Pytest:**
```bash
pytest tests/stress_test_hot_paths.py -m stress -v
```

**Artifact:** `ops/scholarship-api/stress_test_results.md`

**Success Criteria:**
- ✅ Stress tests executed: Yes
- ✅ Latency distribution captured: P50/P90/P95/P99
- ✅ Error rate measured: Value provided
- ✅ Auth regressions checked: Count provided
- ✅ Fix list generated: Issues identified
- ✅ Rollback decision: Made based on thresholds

**Rollback Triggers:**
- 🔴 Error rate >5%
- 🔴 Auth failures >0.5%

---

## Script Locations

All operational scripts are in `scripts/`:

- `scripts/daily_ops.py` - Daily operations snapshot
- `scripts/release_validation.py` - Release validation with optimization
- `scripts/kpi_reporting.py` - KPI and revenue reporting
- `scripts/incident_response.py` - Incident response with rollback logic
- `scripts/execute_optimization_plan.sh` - Full 48-hour optimization workflow

---

## Artifact Directory

All artifacts are saved to: `ops/scholarship-api/`

- `daily_ops_snapshot.json` - Daily ops baseline
- `optimization_before_after.md` - Optimization comparison
- `kpi_24h.txt` - KPI report
- `stress_test_results.md` - Stress test results with rollback decision

---

## Quick Start

**Morning Routine:**
```bash
python scripts/daily_ops.py
```

**Before Release:**
```bash
python scripts/release_validation.py
python scripts/incident_response.py
```

**End of Day:**
```bash
python scripts/kpi_reporting.py
```

**Incident Response:**
```bash
python scripts/incident_response.py
# Exit code 1 = rollback required
# Exit code 0 = system healthy
```

---

## Integration with CI/CD

Add to your deployment pipeline:

```yaml
# Example GitHub Actions
- name: Daily Ops Check
  run: python scripts/daily_ops.py

- name: Pre-Deploy Validation
  run: |
    python scripts/release_validation.py
    python scripts/incident_response.py
    if [ $? -eq 1 ]; then
      echo "Rollback required - deployment blocked"
      exit 1
    fi

- name: Post-Deploy KPI
  run: python scripts/kpi_reporting.py
```

---

**Documentation:**
- Full Runbook: `OPERATIONS_RUNBOOK.md`
- Quick Start: `DAILY_OPS_QUICKSTART.md`
- This Reference: `OPS_PROMPTS_REFERENCE.md`
