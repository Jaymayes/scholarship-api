# Manual Intervention Manifest
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-007
**Protocol**: AGENT3_HANDSHAKE v27
**Generated**: 2026-01-12T04:35:06Z
**Status**: RAW TRUTH PROBE FAILED

---

## Raw Evidence Summary

| App | Observed Status | Evidence File |
|-----|-----------------|---------------|
| A3 | `HTTP/2 404` | raw_curl_evidence.txt |
| A8 | `HTTP/2 404` | raw_curl_evidence.txt |
| A6 | `HTTP/2 200` ✅ | raw_curl_evidence.txt |

---

## A3: scholarai-agent (FAILED)

### Observed Status Line (verbatim)
```
< HTTP/2 404
```

### Probable Root Cause
- App is not binding to `0.0.0.0:$PORT`
- Startup command may use `127.0.0.1` or hardcoded port
- App may not be starting at all

### Fix Steps (CEO must perform in A3 workspace)

1. **Open A3 Workspace**
   - Go to: https://replit.com/@jamarrlmayes/scholarai-agent

2. **Check/Fix Startup Command**
   - For **Python/FastAPI/Uvicorn**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - For **Flask**:
     ```python
     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
     ```
   - For **Node/Express**:
     ```javascript
     server.listen(process.env.PORT || 5000, "0.0.0.0")
     ```

3. **Verify PORT Environment Variable**
   - Ensure `PORT` is defined in Secrets/Environment
   - Do NOT hardcode port numbers

4. **Republish/Deploy**
   - Click Deploy/Publish button after saving changes

5. **Verify Fix**
   ```bash
   curl -I https://scholarai-agent-jamarrlmayes.replit.app/health
   # Expected: HTTP/2 200
   ```

---

## A8: a8-command-center (FAILED)

### Observed Status Line (verbatim)
```
< HTTP/2 404
```

### Probable Root Cause
- App is not binding to `0.0.0.0:$PORT`
- Startup command may use `127.0.0.1` or hardcoded port
- App may not be starting at all

### Fix Steps (CEO must perform in A8 workspace)

1. **Open A8 Workspace**
   - Go to: https://replit.com/@jamarrlmayes/a8-command-center

2. **Check/Fix Startup Command**
   - For **Python/FastAPI/Uvicorn**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - For **Flask**:
     ```python
     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
     ```
   - For **Node/Express**:
     ```javascript
     server.listen(process.env.PORT || 5000, "0.0.0.0")
     ```

3. **Verify PORT Environment Variable**
   - Ensure `PORT` is defined in Secrets/Environment
   - Do NOT hardcode port numbers

4. **Republish/Deploy**
   - Click Deploy/Publish button after saving changes

5. **Verify Fix**
   ```bash
   curl -I https://a8-command-center-jamarrlmayes.replit.app/health
   # Expected: HTTP/2 200
   ```

---

## A6: scholarship-sage (PASSED)

### Observed Status Line (verbatim)
```
< HTTP/2 200
```

### Status: No intervention required ✅

---

## Acceptance Tests (Post-Fix)

After fixing A3 and A8, run these verification commands:

```bash
# A3 Health Check
curl -I https://scholarai-agent-jamarrlmayes.replit.app/health
# Expected: HTTP/2 200

# A8 Health Check  
curl -I https://a8-command-center-jamarrlmayes.replit.app/health
# Expected: HTTP/2 200

# Full Fleet Probe
for app in scholar-auth scholarship-api scholarai-agent auto-page-maker student-pilot scholarship-sage scholaraiadvisor.com a8-command-center; do
  echo "$app: $(curl -s -o /dev/null -w '%{http_code}' https://${app}-jamarrlmayes.replit.app/health 2>/dev/null || curl -s -o /dev/null -w '%{http_code}' https://${app}/health)"
done
# Expected: All return 200
```

---

## Risk Notes

| Risk | Mitigation |
|------|------------|
| Incomplete fix | Re-verify with curl after each change |
| Wrong framework command | Check app's main file for framework type |
| Missing PORT env var | Add to Secrets tab in Replit |

---

## Rollback

If fix causes regression:
1. Revert to last known good commit in that workspace
2. Or restore from Replit checkpoint

---

## Agent Limitation

This agent operates in the **A2 workspace only**. It cannot:
- Access A3 or A8 filesystem
- Edit A3 or A8 startup commands
- Republish A3 or A8 deployments
- View A3 or A8 logs

**CEO manual intervention is required.**
