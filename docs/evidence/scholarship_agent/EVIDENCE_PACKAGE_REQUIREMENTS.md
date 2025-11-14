# scholarship_agent Evidence Package Requirements

**Application**: scholarship_agent  
**APP_BASE_URL**: https://scholarship-agent-jamarrlmayes.replit.app  
**DRI**: Agent3 (Program Integrator)  
**Deadline**: November 13, 2025, 9:00 PM MST  
**Status**: ⚠️ BLOCKED - Awaiting workspace access  

---

## CEO Requirements (Nov 13 Memo)

> "Submit evidence package confirming S2S integration ready, scheduled jobs dry-run logs, admin monitoring dashboards, audit logs, and 100% env-driven config."

---

## Required Artifacts Checklist

### 1. S2S Integration Readiness ✅

**File**: `docs/evidence/scholarship_agent/s2s_integration_proof.md`

**Must Include**:
- [ ] OAuth2 Client Credentials configuration
  - Client ID registered with scholar_auth
  - Client secret stored in Replit Secrets (screenshot of secret name only, NOT value)
  - Token endpoint URL (env-driven, not hardcoded)
  - Scopes requested (e.g., `scholarships.read`, `scholarships.write`, `students.read`)

- [ ] Token fetch test results
  ```bash
  # Command
  curl -X POST https://scholar-auth.../oauth/token \
    -d "grant_type=client_credentials" \
    -d "client_id=${CLIENT_ID}" \
    -d "client_secret=${CLIENT_SECRET}" \
    -d "scope=scholarships.read students.read"
  
  # Expected output (token redacted)
  {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 300,
    "scope": "scholarships.read students.read"
  }
  ```

- [ ] Decoded JWT claims (use https://jwt.io, redact sensitive fields)
  ```json
  {
    "sub": "scholarship_agent",
    "iat": 1699999999,
    "exp": 1699999999,
    "scope": "scholarships.read students.read",
    "role": "service",
    "client_id": "scholarship_agent_prod"
  }
  ```

- [ ] S2S auth integration code location
  - Path to auth client: `services/auth_client.py` (or equivalent)
  - Middleware/decorator for outbound requests
  - Token refresh logic (handle 401, retry with new token)

---

### 2. Scheduled Jobs Dry-Run Logs ✅

**File**: `docs/evidence/scholarship_agent/scheduled_jobs_dry_run.log`

**Required Jobs** (based on typical scholarship automation):
1. **Scholarship Sync Job** - Fetch new scholarships from providers
2. **Deadline Reminder Job** - Send upcoming deadline notifications
3. **Match Regeneration Job** - Re-run matching for updated profiles
4. **Analytics Aggregation Job** - Daily metrics rollup
5. **Data Cleanup Job** - Archive old records

**For Each Job, Provide**:
```
========================================
Job: Scholarship Sync Job
Schedule: 0 */6 * * * (every 6 hours)
Dry-Run Timestamp: 2025-11-13T17:00:00Z
Status: DRY-RUN SUCCESSFUL
Duration: 1.2 seconds
========================================

[2025-11-13 17:00:00] INFO: Starting scholarship sync job (DRY-RUN mode)
[2025-11-13 17:00:00] INFO: Fetching scholarships from scholarship_api
[2025-11-13 17:00:01] INFO: Retrieved 110 scholarships
[2025-11-13 17:00:01] INFO: DRY-RUN: Would sync 15 new scholarships
[2025-11-13 17:00:01] INFO: DRY-RUN: Would update 8 existing scholarships
[2025-11-13 17:00:01] INFO: DRY-RUN: Would emit 23 events to auto_com_center
[2025-11-13 17:00:01] INFO: Job completed successfully (DRY-RUN)

Events that would be emitted (DRY-RUN):
- scholarship_added: 15
- scholarship_updated: 8
- match_generated: 45 (for 15 new scholarships)
========================================
```

**Verification Commands**:
```bash
# List all scheduled jobs
python manage.py list_jobs

# Run single job in dry-run mode
python manage.py run_job scholarship_sync --dry-run

# Check job configuration
cat config/jobs.yaml
```

---

### 3. Admin Monitoring Dashboards ✅

**File**: `docs/evidence/scholarship_agent/monitoring_dashboard_screenshots.md`

**Required Dashboard Components**:

**A) Job Execution Dashboard**
- Screenshot of job status page
- Shows: Last run time, next run time, success/failure counts
- Example metrics:
  ```
  Job Name               | Last Run          | Status  | Duration | Next Run
  -----------------------|-------------------|---------|----------|-----------------
  Scholarship Sync       | 2025-11-13 17:00  | Success | 1.2s     | 2025-11-13 23:00
  Deadline Reminders     | 2025-11-13 16:00  | Success | 0.8s     | 2025-11-13 22:00
  Match Regeneration     | 2025-11-13 15:00  | Success | 3.4s     | 2025-11-14 03:00
  ```

**B) Health Metrics Dashboard**
- `/health` endpoint JSON output
- Shows: DB connectivity, Redis status, external API reachability
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-11-13T17:00:00Z",
    "checks": {
      "database": {"status": "up", "latency_ms": 12},
      "redis": {"status": "up", "latency_ms": 3},
      "scholarship_api": {"status": "up", "latency_ms": 45},
      "scholar_auth": {"status": "up", "latency_ms": 38},
      "auto_com_center": {"status": "up", "latency_ms": 52}
    }
  }
  ```

**C) Prometheus Metrics Endpoint**
```bash
# Command
curl https://scholarship-agent-jamarrlmayes.replit.app/metrics

# Sample output (first 20 lines)
# HELP job_executions_total Total number of job executions
# TYPE job_executions_total counter
job_executions_total{job="scholarship_sync",status="success"} 142
job_executions_total{job="scholarship_sync",status="failure"} 2
job_executions_total{job="deadline_reminders",status="success"} 89

# HELP job_duration_seconds Job execution duration
# TYPE job_duration_seconds histogram
job_duration_seconds_bucket{job="scholarship_sync",le="1.0"} 120
job_duration_seconds_bucket{job="scholarship_sync",le="5.0"} 142
```

**D) Error Rate Tracking**
- Last 24 hours error count: 0
- Alert thresholds: > 5 errors/hour triggers alert
- Recent errors: None (or list if any)

---

### 4. Audit Logs ✅

**File**: `docs/evidence/scholarship_agent/audit_logs_sample.jsonl`

**Required Log Entries** (JSONL format, 1 per line):

```jsonl
{"timestamp":"2025-11-13T17:00:00Z","event":"job_started","job":"scholarship_sync","trigger":"scheduled","user":"system","metadata":{"dry_run":false}}
{"timestamp":"2025-11-13T17:00:01Z","event":"api_call","service":"scholarship_api","endpoint":"/api/v1/scholarships","method":"GET","status":200,"duration_ms":245,"request_id":"req_abc123"}
{"timestamp":"2025-11-13T17:00:01Z","event":"data_sync","action":"create","entity":"scholarship","entity_id":"sch_789","source":"scholarship_api","user":"system"}
{"timestamp":"2025-11-13T17:00:01Z","event":"event_emitted","event_type":"scholarship_added","target":"auto_com_center","status":"queued","request_id":"req_abc124"}
{"timestamp":"2025-11-13T17:00:02Z","event":"job_completed","job":"scholarship_sync","status":"success","duration_ms":1200,"records_processed":23}
```

**Audit Log Requirements**:
- [ ] Immutable storage (append-only)
- [ ] Includes request_id for tracing
- [ ] No PII logged (student emails/phones redacted)
- [ ] 30-day hot retention confirmed
- [ ] Exportable via `/api/admin/audit_logs` endpoint

**Sample Query**:
```bash
# Last 100 audit entries
curl -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  https://scholarship-agent-jamarrlmayes.replit.app/api/admin/audit_logs?limit=100

# Filter by event type
curl -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  https://scholarship-agent-jamarrlmayes.replit.app/api/admin/audit_logs?event=job_started
```

---

### 5. 100% Env-Driven Configuration ✅

**File**: `docs/evidence/scholarship_agent/env_config_validation.md`

**Validation Steps**:

```bash
# Step 1: Scan codebase for hardcoded URLs
grep -r "https://" --include="*.py" --exclude-dir=venv --exclude-dir=.git .

# Expected: Only comments/documentation, no hardcoded URLs in code

# Step 2: Check environment variable usage
grep -r "os.getenv\|settings\." --include="*.py" | wc -l

# Expected: All URLs/secrets loaded from env

# Step 3: List all required env vars
cat .env.example

# Expected output:
SCHOLAR_AUTH_URL=https://scholar-auth-jamarrlmayes.replit.app
SCHOLAR_AUTH_CLIENT_ID=scholarship_agent_prod
SCHOLAR_AUTH_CLIENT_SECRET=<secret>
SCHOLARSHIP_API_URL=https://scholarship-api-jamarrlmayes.replit.app
AUTO_COM_CENTER_URL=https://auto-com-center-jamarrlmayes.replit.app
DATABASE_URL=<secret>
REDIS_URL=<secret>
JWT_SECRET_KEY=<secret>
```

**Configuration File Check**:
```bash
# config/settings.py validation
cat config/settings.py | grep -E "class Settings|scholar_auth_url|scholarship_api_url"

# Expected: All URLs from env vars, no defaults except localhost for dev
```

**Deployment Config**:
```bash
# .replit file check
cat .replit | grep -E "run =|hidden ="

# Expected: No secrets in .replit file
```

---

## Submission Format

**Directory Structure**:
```
docs/evidence/scholarship_agent/
├── EVIDENCE_PACKAGE_REQUIREMENTS.md (this file)
├── s2s_integration_proof.md
├── scheduled_jobs_dry_run.log
├── monitoring_dashboard_screenshots.md
├── audit_logs_sample.jsonl
└── env_config_validation.md
```

**Header Format** (all evidence files):
```markdown
# [Artifact Title]

**Application**: scholarship_agent
**Created**: 2025-11-13T[HH:MM:SS]Z
**Author**: [DRI Name]
**Purpose**: CEO go-live evidence (Nov 13 memo)

---

[Content]
```

---

## Blockers

⚠️ **CRITICAL**: Agent3 does not have access to scholarship_agent Replit workspace

**Resolution Options**:
1. Ops grants workspace access within 60-minute SLA
2. scholarship_agent DRI pushes evidence to shared repo
3. Agent3 escalates to CEO in 4 PM war-room

**Current Status**: Awaiting workspace access as of 5:00 PM MST

---

## Next Steps (Once Access Granted)

1. [ ] SSH into scholarship_agent workspace
2. [ ] Run all validation commands above
3. [ ] Capture screenshots/logs
4. [ ] Create evidence files per checklist
5. [ ] Push to `docs/evidence/scholarship_agent/`
6. [ ] Notify CEO in war-room: "scholarship_agent evidence package ready for review"

---

**Prepared by**: Agent3, Program Integrator  
**For**: CEO, Scholar AI Advisor  
**Escalation Path**: If access not granted by 6 PM MST, escalate to CEO
