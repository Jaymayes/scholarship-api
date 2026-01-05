# ROLLBACK PROCEDURES - A2 Protocol v3.5.1 Changes
**Date**: 2026-01-05
**Risk Level**: LOW

## Quick Rollback Commands

### Option 1: Git Revert (Recommended)

```bash
# Revert to before SRE Fix Pack changes
git checkout 4748d5c0 -- main.py routers/payments.py

# Restart the server
pkill -f "python main.py" && PORT=5000 python main.py
```

### Option 2: Selective Rollback

**Revert /events to /ingest**:
```bash
# In main.py, change all occurrences:
sed -i 's|/events|/ingest|g' main.py

# In routers/payments.py:
sed -i 's|A8_EVENTS_URL|A8_INGEST_URL|g' routers/payments.py
```

**Remove Authorization header support**:
```bash
# Delete lines 306-322 in main.py (get_a8_headers function)
# Remove a8_key variable and auth header logic from payments.py
```

**Remove /ready endpoint**:
```bash
# Delete lines 942-969 in main.py
```

### Option 3: Full Checkpoint Rollback

```bash
# Rollback to checkpoint before changes
git log --oneline -10
# Pick commit before 6a067676
git reset --hard <commit-before-changes>
```

## Verification After Rollback

```bash
# Test health endpoints
curl -s http://localhost:5000/health | jq '.'
curl -s http://localhost:5000/ready  # Should 404 if removed

# Test A8 connectivity (will use /ingest if reverted)
curl -s http://localhost:5000/api/probe/ | jq '.'
```

## Risk Assessment

| Change | Rollback Risk | Notes |
|--------|---------------|-------|
| /events endpoint | LOW | A8 may still accept /ingest |
| Authorization header | NONE | Optional feature |
| /ready endpoint | LOW | Only affects deploy checks |

## Emergency Contacts

- DevOps: Notify if rolling back in production
- A8 Team: Notify if reverting to /ingest endpoint

## Notes

- Rolling back does NOT affect stored events in A8
- Rolling back does NOT affect stored events in A2 database
- Authorization header rollback has no data impact
