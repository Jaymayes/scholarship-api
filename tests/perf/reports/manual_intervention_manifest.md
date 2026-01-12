# Manual Intervention Manifest

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-017
**Protocol**: AGENT3_HANDSHAKE v28 (Strict Mode)
**Generated**: 2026-01-12T19:06:43Z
**Status**: BLOCKED - CEO ACTION REQUIRED

---

## Agent Workspace Limitation

This agent operates exclusively in the **A2 (scholarship-api)** workspace. It cannot access, edit, or republish other workspaces.

---

## BLOCKED: A3 (scholarai-agent)

### Current State
- **URL**: https://scholarai-agent-jamarrlmayes.replit.app
- **Health**: HTTP 404
- **Content**: No valid service marker

### Root Cause
Server not binding to `0.0.0.0:$PORT` or missing `/health` endpoint.

### Required Fixes

#### 1. Open Workspace
```
https://replit.com/@jamarrlmayes/scholarai-agent
```

#### 2. Check/Fix Startup Command

**Option A: Uvicorn (FastAPI)**
```bash
# In .replit or workflow
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Option B: In Python code (main.py)**
```python
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

#### 3. Add /health Endpoint

**FastAPI:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "scholarship-agent"}
```

**Flask:**
```python
@app.route("/health")
def health():
    return {"status": "ok", "service": "scholarship-agent"}
```

#### 4. Prevent EADDRINUSE
- Ensure only ONE start command in `.replit` or workflow
- Remove any duplicate process managers
- Use `pkill -f uvicorn` before starting if needed

#### 5. Republish
- Save all changes
- Click Deploy/Publish button
- Wait for deployment to complete

#### 6. Verify
```bash
curl -vL "https://scholarai-agent-jamarrlmayes.replit.app/health?t=$(date +%s)"
# Expected: HTTP 200 with {"status": "ok", "service": "scholarship-agent"}
```

---

## BLOCKED: A8 (a8-command-center)

### Current State
- **URL**: https://a8-command-center-jamarrlmayes.replit.app
- **Health**: HTTP 404
- **Content**: No valid service marker

### Root Cause
Server not binding to `0.0.0.0:$PORT` or missing `/health` endpoint.

### Required Fixes

#### 1. Open Workspace
```
https://replit.com/@jamarrlmayes/a8-command-center
```

#### 2. Check/Fix Startup Command

**Node.js/Express:**
```javascript
const port = process.env.PORT || 5000;
app.listen(port, "0.0.0.0", () => {
  console.log(`A8 Command Center running on port ${port}`);
});
```

**Python/Uvicorn:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 3. Add /health Endpoint

**Express:**
```javascript
app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "command-center" });
});
```

**FastAPI:**
```python
@app.get("/health")
async def health():
    return {"status": "ok", "service": "command-center"}
```

#### 4. Republish
- Save all changes
- Click Deploy/Publish button
- Wait for deployment to complete

#### 5. Verify
```bash
curl -vL "https://a8-command-center-jamarrlmayes.replit.app/health?t=$(date +%s)"
# Expected: HTTP 200 with {"status": "ok", "service": "command-center"}
```

---

## Verification After Fixes

Run this command to verify both apps:

```bash
for app in scholarai-agent a8-command-center; do
  resp=$(curl -sS "https://${app}-jamarrlmayes.replit.app/health?t=$(date +%s)" 2>/dev/null)
  code=$(curl -sS -o /dev/null -w "%{http_code}" "https://${app}-jamarrlmayes.replit.app/health" 2>/dev/null)
  echo "$app: HTTP $code"
  echo "  Body: $resp"
done
```

**Expected:**
```
scholarai-agent: HTTP 200
  Body: {"status":"ok","service":"scholarship-agent"}
a8-command-center: HTTP 200
  Body: {"status":"ok","service":"command-center"}
```

---

## Timeline

| Step | Action | Owner | ETA |
|------|--------|-------|-----|
| 1 | Open A3 workspace | CEO | Immediate |
| 2 | Apply A3 fixes | CEO | +10 min |
| 3 | Republish A3 | CEO | +15 min |
| 4 | Verify A3 = 200 | CEO | +20 min |
| 5 | Open A8 workspace | CEO | +20 min |
| 6 | Apply A8 fixes | CEO | +30 min |
| 7 | Republish A8 | CEO | +35 min |
| 8 | Verify A8 = 200 | CEO | +40 min |
| 9 | Notify Agent | CEO | +40 min |
| 10 | Full verification | Agent | +55 min |

---

## Post-Fix Command

Once A3 and A8 are fixed, send to agent:

> "A3 and A8 are fixed and returning 200. Run verification CEOSPRINT-20260113-VERIFY-ZT3G-018"
