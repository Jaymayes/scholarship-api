# Step-by-Step Merge Instructions
**For**: Maintainers of A2, A7, A8 repositories
**Date**: 2026-01-05T22:20:00Z

## Overview

This document provides instructions for applying the PR patches generated in Phase 2.
All changes are feature-flagged with DEFAULT OFF for safe rollout.

---

## Issue A: A2 /ready Enhancement

**Repository**: scholarship-api (A2)
**Complexity**: Low
**Risk**: Low

### Steps

1. **Review patch file**: `pr_docs/issue_a_a2_ready/ready_enhancement.patch`

2. **Apply the changes** to main.py readiness_check function

3. **Add tests**: Copy `test_ready_contract.py` to tests/ directory

4. **Set feature flag** (Replit Secrets):
   - `READY_EXTENDED_CHECKS=false` (keep off initially)

5. **Deploy to Staging** and verify `/ready` returns expected response

6. **Enable flag** when ready: `READY_EXTENDED_CHECKS=true`

---

## Issue B: A7 Async Ingestion

**Repository**: auto-page-maker (A7)
**Complexity**: Medium
**Risk**: Medium

### Steps

1. **Create new files**:
   - Copy `async_ingestion.py` to `app/routes/ingest.py`

2. **Register router** in main.py:
   ```python
   from app.routes.ingest import router as ingest_router
   app.include_router(ingest_router)
   ```

3. **Add tests**: Copy `test_async_ingestion.py` to tests/

4. **Set feature flag**: `ASYNC_INGESTION_ENABLED=false`

5. **Deploy and test sync mode** (should return 200)

6. **Enable async mode**: `ASYNC_INGESTION_ENABLED=true` (should return 202)

7. **Profile latency** with 200 samples to verify improvement

---

## Issue C: A8 Banner Auto-Clear

**Repository**: auto-com-center (A8)
**Complexity**: Medium
**Risk**: Low

### Steps

1. **Database migration** (add columns to incidents table):
   - `last_healthy_at TIMESTAMP NULL`
   - `auto_cleared BOOLEAN DEFAULT FALSE`
   - `cleared_at TIMESTAMP NULL`
   - `cleared_by VARCHAR(50) NULL`

2. **Add service file**: Copy `banner_auto_clear.py` to services/

3. **Register scheduled task** (run every minute)

4. **Set feature flags**:
   - `BANNER_AUTO_CLEAR_ENABLED=false`
   - `BANNER_TTL_MINUTES=15`
   - `ADMIN_CLEAR_TOKEN=<secure-token>`

5. **Test admin endpoint**: POST to `/api/admin/clear-stale-incidents`

6. **Enable auto-clear**: `BANNER_AUTO_CLEAR_ENABLED=true`

---

## Issue D: A8 Demo Mode

**Repository**: auto-com-center (A8)
**Complexity**: Low
**Risk**: Low

### Steps

1. **Add route file**: Copy `demo_mode.py` to routes/tiles.py (or merge)

2. **Add Vue component**: Copy `DemoModeBadge.vue` to components/

3. **Import component** in dashboard view

4. **Add tests**: Copy `test_demo_mode.py` to tests/

5. **Set feature flag**: `DEMO_MODE_ENABLED=false`

6. **Test mode switching**:
   - GET `/api/tiles/revenue` (live mode default)
   - GET `/api/tiles/revenue?mode=demo` (demo mode)

---

## Post-Merge Checklist

- [ ] All tests pass
- [ ] Feature flags default to OFF
- [ ] Staging deployment successful
- [ ] Latency profile shows improvement (Issue B)
- [ ] Documentation updated
- [ ] Monitoring rules applied

---

**Status**: READY FOR MAINTAINER REVIEW
