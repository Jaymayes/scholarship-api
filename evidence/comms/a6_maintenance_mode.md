# A6 Maintenance Mode Communications Package

**Incident ID**: A6-PRV-2026-01-15  
**Status**: STAGED (Ready to auto-send)  
**Trigger**: A6 not green by 09:21:13Z or fails during 30-min stabilization window

---

## Channels

### 1. In-Product Banner (Provider UI)

```
Provider onboarding is temporarily unavailable while we complete reliability 
maintenance. Student services remain fully available.

Incident ID: A6-PRV-2026-01-15
Next update: [time +30m]
```

**Placement**: Top of Provider Dashboard, dismissible after acknowledgment  
**Priority**: High (yellow banner)

---

### 2. Status Page Incident

**Title**: A6 Provider onboarding degraded

**Impact**:
- Provider sign-ups and credential verification unavailable
- Existing provider dashboards unaffected
- Student services fully operational

**Metrics**:
- Uptime target: 99.9%
- Current error_rate: [dynamic]
- Current P95: [dynamic]
- Rollback build ID: [dynamic]

**ETA**: Restoration targeted within current gate; next checkpoint 10:11:13Z

---

### 3. Email to Institutional Partners

**Subject**: Action required: temporary pause on provider onboarding (A6)

**Body**:
```
Dear Partner,

We are pausing new provider onboarding while we complete a reliability rollback 
on the A6 Provider App.

KEY POINTS:
- Student services are unaffected
- Our standard is 99.9% availability
- Today's regression tripped our automatic safeguards

RESTORATION CRITERIA:
We will reopen onboarding after 30 minutes of clean health:
- P95 < 1.25s
- Error rate < 0.5%

NEXT UPDATE:
You will receive an all-clear or next ETA at 10:11:13Z.

Incident ID: A6-PRV-2026-01-15

If you have pilot timelines, please reply and we will prioritize a 
white-glove onboarding path.

Best regards,
ScholarshipAI Platform Operations
```

---

### 4. CS/Sales Talk Track

```
SITUATION: Safety interlock engaged on A6 Provider onboarding.

KEY MESSAGES:
- No data loss occurred
- Automatic safeguards triggered as designed
- Onboarding resumes after sustained green metrics

OFFER:
"We can provision sandboxes without production writes if you need 
immediate access for demos or testing."

ESCALATION:
For urgent pilot needs, escalate to Partnerships lead.
```

---

## Ownership & SLA

| Role | Responsibility |
|------|----------------|
| Partnerships Lead | Email to institutional partners |
| CS Lead | In-product banner + talk track distribution |
| Platform Ops | Status page updates |

**SLA**:
- Send within 5 minutes of trigger
- Post updates every 30 minutes until resolved
- All-clear notification within 15 minutes of resolution

---

## Auto-Send Logic

```python
# Trigger conditions
TRIGGER_CONDITIONS = {
    "deadline": "2026-01-15T09:21:13Z",
    "health_check_failed": True,
    "stabilization_window_breach": True
}

# If any condition met, auto-send all channels
if current_time > deadline and not a6_green:
    send_banner()
    create_status_incident()
    send_partner_email()
    distribute_talk_track()
```

---

## Resolution Communications

### All-Clear Template

**Subject**: RESOLVED: Provider onboarding restored (A6-PRV-2026-01-15)

**Body**:
```
The A6 Provider onboarding service has been restored.

RESOLUTION TIME: [timestamp]
TOTAL DOWNTIME: [duration]

All provider sign-ups and credential verification are now operational.
Thank you for your patience.

Incident ID: A6-PRV-2026-01-15

Best regards,
ScholarshipAI Platform Operations
```

---

## Staged Status

- [x] In-product banner copy approved
- [x] Status page incident template ready
- [x] Partner email draft approved
- [x] CS/Sales talk track distributed
- [x] Auto-send armed — triggers at 09:21:13Z if A6 not green

## Auto-Send Implementation

The following conditions arm automatic dispatch:

```python
AUTO_SEND_TRIGGER = {
    "deadline": "2026-01-15T09:21:13Z",
    "condition": "A6 not green by deadline OR stabilization window breach",
    "armed": True,
    "armed_at": "2026-01-15T08:XX:XXZ"
}
```

**Polling Interval**: 60 seconds  
**Check Endpoint**: `/api/v1/telemetry/a3-a6-breaker/guardrails`  
**Send Criteria**: `kill_active=True` OR `current_time > deadline AND a6_health != 200`
