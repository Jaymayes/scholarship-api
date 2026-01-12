# Manual Intervention Manifest: A3/A8 Fix Package

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-011
**Generated**: 2026-01-12T17:30:00Z
**Priority**: CRITICAL (Blocking Fleet Verification)

---

## Agent Limitation Notice

The Replit Agent operates **exclusively in the A2 workspace**. It cannot:
- Access A3 or A8 filesystems
- Edit A3 or A8 startup commands
- View A3 or A8 logs
- Republish A3 or A8

**CEO must fix A3 and A8 manually.**

---

## A3: scholarai-agent (CRITICAL)

### Current Status
- **Health**: HTTP 404
- **Root Cause**: Server not binding to `0.0.0.0:$PORT`

### Fix Steps

1. **Open Workspace**
   ```
   https://replit.com/@jamarrlmayes/scholarai-agent
   ```

2. **Check Current Startup**
   - Look in `.replit` file for `run` command
   - Or check Workflows panel for the run command

3. **Identify Framework and Fix**

   **If Python/FastAPI/Uvicorn:**
   ```python
   # main.py - ensure this pattern at bottom
   if __name__ == "__main__":
       import uvicorn
       import os
       port = int(os.environ.get("PORT", 5000))
       uvicorn.run(app, host="0.0.0.0", port=port)
   ```
   
   **Or in run command:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

   **If Python/Flask:**
   ```python
   if __name__ == "__main__":
       import os
       port = int(os.environ.get("PORT", 5000))
       app.run(host="0.0.0.0", port=port)
   ```

   **If Node.js/Express:**
   ```javascript
   const port = process.env.PORT || 5000;
   app.listen(port, "0.0.0.0", () => {
     console.log(`Server running on port ${port}`);
   });
   ```

4. **Add /health Endpoint (if missing)**
   
   **FastAPI:**
   ```python
   @app.get("/health")
   async def health():
       return {"status": "ok"}
   ```
   
   **Flask:**
   ```python
   @app.route("/health")
   def health():
       return {"status": "ok"}
   ```
   
   **Express:**
   ```javascript
   app.get("/health", (req, res) => {
     res.json({ status: "ok" });
   });
   ```

5. **Republish**
   - Click the Deploy/Publish button
   - Wait for deployment to complete

6. **Verify**
   ```bash
   curl -I https://scholarai-agent-jamarrlmayes.replit.app/health
   # Expected: HTTP/2 200
   ```

### Common Issues
- `--host 127.0.0.1` instead of `0.0.0.0`
- Missing `PORT` environment variable usage
- No `/health` endpoint defined
- EADDRINUSE (another process on same port)

---

## A8: a8-command-center (CRITICAL)

### Current Status
- **Health**: HTTP 404
- **Root Cause**: Server not binding to `0.0.0.0:$PORT`

### Fix Steps

1. **Open Workspace**
   ```
   https://replit.com/@jamarrlmayes/a8-command-center
   ```

2. **Check Current Startup**
   - Look in `.replit` file for `run` command
   - Or check Workflows panel for the run command

3. **Apply Same Fix Pattern as A3**
   - Ensure `host="0.0.0.0"` or `--host 0.0.0.0`
   - Ensure using `$PORT` or `process.env.PORT`
   - Add `/health` endpoint if missing

4. **Republish**
   - Click the Deploy/Publish button
   - Wait for deployment to complete

5. **Verify**
   ```bash
   curl -I https://a8-command-center-jamarrlmayes.replit.app/health
   # Expected: HTTP/2 200
   ```

---

## Quick Reference: Framework Patterns

| Framework | Host Binding |
|-----------|--------------|
| Uvicorn | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Gunicorn | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Flask | `app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))` |
| Express | `app.listen(process.env.PORT, "0.0.0.0")` |
| Fastify | `server.listen({ port: process.env.PORT, host: "0.0.0.0" })` |

---

## Verification After Fix

Once both A3 and A8 are fixed, run this command:

```bash
for app in scholarai-agent a8-command-center; do
  echo "$app: $(curl -s -o /dev/null -w '%{http_code}' https://${app}-jamarrlmayes.replit.app/health)"
done
```

**Expected Output:**
```
scholarai-agent: 200
a8-command-center: 200
```

---

## Timeline

| Phase | Action | Owner | ETA |
|-------|--------|-------|-----|
| T+0 | Open A3 workspace | CEO | Immediate |
| T+5 | Identify root cause | CEO | 5 min |
| T+15 | Apply fix | CEO | 15 min |
| T+20 | Republish A3 | CEO | 20 min |
| T+25 | Verify A3 = 200 | CEO | 25 min |
| T+30 | Repeat for A8 | CEO | 30 min |
| T+40 | Both verified | CEO | 40 min |
| T+45 | Re-run verification | Agent | 45 min |

---

## Post-Fix: Agent Verification

Once A3 and A8 return 200, notify the agent with:

> "A3 and A8 are fixed. Run verification CEOSPRINT-20260113-VERIFY-ZT3G-012"

The agent will then execute the full verification suite.
