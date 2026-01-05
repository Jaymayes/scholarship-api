# Rollback Readiness Document
**Phase**: 2 (Implementation)
**Date**: 2026-01-05T22:20:00Z

## Feature Flag Summary

All changes are behind feature flags with **DEFAULT OFF** for instant rollback.

| Issue | Feature Flag | Default | Rollback Command |
|-------|--------------|---------|------------------|
| A | `READY_EXTENDED_CHECKS` | `false` | Set to `false` |
| B | `ASYNC_INGESTION_ENABLED` | `false` | Set to `false` |
| C | `BANNER_AUTO_CLEAR_ENABLED` | `false` | Set to `false` |
| D | `DEMO_MODE_ENABLED` | `false` | Set to `false` |

## Rollback Procedures

### Immediate Rollback (< 1 minute)
1. Set feature flag to `false` in environment
2. Restart service (automatic on Replit)
3. Verify behavior reverts to baseline

### Full Rollback (< 5 minutes)
1. Revert PR/commit
2. Redeploy previous version
3. Verify health endpoints return 200

## Rollback Commands

### Issue A (A2 /ready)
```
# Disable extended checks
Set READY_EXTENDED_CHECKS=false in Replit Secrets
Restart workflow
```

### Issue B (A7 async)
```
# Disable async ingestion - falls back to sync
Set ASYNC_INGESTION_ENABLED=false in Replit Secrets
Verify response returns 200 (sync) not 202 (async)
```

### Issue C (A8 banners)
```
# Disable auto-clear
Set BANNER_AUTO_CLEAR_ENABLED=false in Replit Secrets
Banners will persist (original behavior)
```

### Issue D (A8 demo mode)
```
# Disable demo mode
Set DEMO_MODE_ENABLED=false in Replit Secrets
All queries default to live mode
```

## Verification Commands

```bash
# Verify A2 /ready
curl https://scholarship-api-.../ready | jq '.services'

# Verify A7 returns correct status code
curl -w "%{http_code}" https://auto-page-maker-.../api/v1/ingest

# Verify A8 no auto-clear
curl https://auto-com-center-.../api/admin/incidents

# Verify A8 live mode
curl https://auto-com-center-.../api/tiles/revenue?mode=live
```

## Rollback Evidence Requirements

After rollback, document:
1. Timestamp of rollback
2. Feature flag values before/after
3. Endpoint response verification
4. Any data cleanup needed

---

**Status**: READY FOR GATE 1 APPROVAL
