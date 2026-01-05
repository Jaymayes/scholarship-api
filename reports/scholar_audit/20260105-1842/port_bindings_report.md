# Port Bindings Report
**Audit Date**: 2026-01-05T19:45:00Z

## Configured Ports (A2 Scholarship API)

| Service | Configured Port | Binding Address | Status |
|---------|-----------------|-----------------|--------|
| FastAPI Server | 5000 | 0.0.0.0 | ✅ Active |
| PostgreSQL | 5432 | localhost | ✅ Active (Neon-backed) |

## Port Assignment Rules (Replit)

| Port | Purpose | Notes |
|------|---------|-------|
| 5000 | Webview (primary) | Only port exposed to public |
| 3000-3003 | Alternative dev ports | Internal only |
| 5173 | Vite dev server | Internal only |
| 8000, 8080 | Alternative backends | Internal only |

## Workflow Configuration

```yaml
Workflow: FastAPI Server
Command: PORT=5000 python main.py
Output Type: webview
Wait For Port: 5000
```

## Prior Port Conflict Analysis

**Symptom**: "Port 5000 already in use" error during workflow restart

**Root Causes** (ordered by likelihood):
1. **Previous process not terminated**: Orphan uvicorn process holding port
2. **Rapid restart**: New process starts before old one releases socket
3. **SO_REUSEADDR not set**: Server doesn't allow port reuse

**Evidence**: Current state shows single uvicorn process on port 5000 - no conflict detected.

## Remediation Recommendations

### 1. Graceful Shutdown (Already Implemented)
```python
# main.py uses uvicorn with proper signal handling
uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
```

### 2. Add Startup Delay in Workflow
```yaml
# If conflicts persist, add delay before start
command: sleep 2 && PORT=5000 python main.py
```

### 3. Kill Orphan Processes (Manual Fix)
```bash
# If port conflict occurs, kill orphan:
pkill -f "uvicorn.*5000" && sleep 2 && python main.py
```

## Fleet Port Inventory

| App | Public Port | Protocol | Conflict Risk |
|-----|-------------|----------|---------------|
| A1 scholar_auth | 443 (HTTPS) | HTTP/1.1 | Low |
| A2 scholarship_api | 5000 → 443 | HTTP/1.1 | **Observed** |
| A3-A8 | 443 (HTTPS) | HTTP/1.1 | Low |

## Current Status

**Status**: ✅ NO ACTIVE CONFLICTS

- Port 5000 bound to single uvicorn process
- No orphan processes detected
- Workflow running normally

## Conclusion

Port conflicts in A2 are **transient** issues caused by rapid restarts, not misconfiguration. The current workflow setup is correct. If conflicts recur:
1. Wait 5 seconds before restarting
2. Use `pkill -f uvicorn` if orphan processes exist
3. Consider adding startup delay to workflow
