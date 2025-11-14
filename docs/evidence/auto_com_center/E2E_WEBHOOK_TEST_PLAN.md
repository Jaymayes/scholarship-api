# auto_com_center E2E Webhook Test Plan

**Application**: auto_com_center  
**CEO Directive**: Execute tonight with manual event injection  
**Deadline**: Evidence by Nov 14, 2:00 PM MST  
**Created**: 2025-11-13T17:35:00Z MST  

---

## CEO Order: E2E Webhook Test

> "Proceed with manual event injection to validate auto_com_center → ESP → signed webhooks → receipt handling. If time permits, add a mocked scholarship_api event stream as a second test. Capture receipts and logs."

---

## Test Objective

Validate complete message delivery pipeline:
1. Event received by auto_com_center
2. Message queued and processed
3. Email sent via ESP (SendGrid/Mailgun/etc)
4. ESP webhook received (delivery/bounce/click)
5. Receipt logged and verified

---

## Test Scenarios

### Scenario 1: Manual Event Injection (REQUIRED)

**Step 1: Inject Test Event**

```bash
# Send test event to auto_com_center
curl -X POST https://auto-com-center-jamarrlmayes.replit.app/api/v1/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{
    "event_type": "scholarship_viewed",
    "user_id": "test_student_001",
    "user_email": "test@example.com",
    "scholarship_id": "sch_test_123",
    "scholarship_name": "Test Scholarship",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }' | jq .

# Expected response:
# {
#   "status": "accepted",
#   "message_id": "msg_abc123",
#   "queued_at": "2025-11-13T17:40:00Z"
# }
```

**Step 2: Verify Message Processing**

```bash
# Check message queue
curl https://auto-com-center-jamarrlmayes.replit.app/api/admin/queue/status \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq .

# Expected: Message in "processing" or "sent" state
```

**Step 3: Verify ESP Delivery**

```bash
# Check ESP logs (SendGrid example)
curl https://api.sendgrid.com/v3/messages?limit=1 \
  -H "Authorization: Bearer ${SENDGRID_API_KEY}" | jq .

# Look for:
# - to_email: test@example.com
# - status: delivered/queued
# - message_id correlation
```

**Step 4: Simulate ESP Webhook**

```bash
# Manually trigger webhook callback (simulates ESP delivery notification)
curl -X POST https://auto-com-center-jamarrlmayes.replit.app/webhooks/esp/delivery \
  -H "Content-Type: application/json" \
  -H "X-ESP-Signature: ${CALCULATED_SIGNATURE}" \
  -d '{
    "event": "delivered",
    "message_id": "msg_abc123",
    "email": "test@example.com",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "smtp_id": "smtp_xyz789"
  }' | jq .

# Expected: {"status": "processed", "receipt_id": "rcpt_..."}
```

**Step 5: Verify Receipt Logging**

```bash
# Query receipts table
curl https://auto-com-center-jamarrlmayes.replit.app/api/admin/receipts?message_id=msg_abc123 \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq .

# Expected:
# {
#   "receipt_id": "rcpt_def456",
#   "message_id": "msg_abc123",
#   "event": "delivered",
#   "verified": true,
#   "signature_valid": true,
#   "timestamp": "2025-11-13T17:41:00Z"
# }
```

---

### Scenario 2: Mocked scholarship_api Event Stream (OPTIONAL)

**If time permits, create mock event emitter**:

```python
# mock_event_stream.py
import requests
import time
import random

BASE_URL = "https://auto-com-center-jamarrlmayes.replit.app"
TOKEN = "..."

events = [
    "scholarship_viewed",
    "scholarship_saved",
    "match_generated",
    "application_started",
    "application_submitted"
]

for i in range(10):
    event_type = random.choice(events)
    payload = {
        "event_type": event_type,
        "user_id": f"test_user_{i:03d}",
        "user_email": f"test{i:03d}@example.com",
        "scholarship_id": f"sch_{random.randint(1,100):03d}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    print(f"[{i+1}/10] {event_type}: {response.status_code} - {response.json()}")
    time.sleep(1)

print("\n✅ Sent 10 test events")
```

**Run and capture output**:
```bash
python mock_event_stream.py | tee results/mock_stream_output.log
```

---

## Webhook Signature Verification

**Critical**: Ensure webhooks are verified to prevent spoofing

**Example verification logic**:
```python
import hmac
import hashlib

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify ESP webhook signature"""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

# Test
payload = '{"event":"delivered","message_id":"msg_abc123"}'
signature = "abc123..."  # From X-ESP-Signature header
secret = "webhook_secret_from_esp"

is_valid = verify_webhook_signature(payload, signature, secret)
print(f"Signature valid: {is_valid}")
```

---

## Evidence Checklist

- [ ] **Event injection proof**
  - curl command with response
  - Message ID captured
  
- [ ] **ESP delivery proof**
  - ESP API response showing message sent
  - Screenshot of ESP dashboard (if available)
  
- [ ] **Webhook receipt proof**
  - Webhook POST request logged
  - Signature verification passed
  - Receipt stored in database
  
- [ ] **End-to-end timing**
  - Event injection → ESP send: < 5 seconds
  - ESP send → Webhook received: < 30 seconds
  - Total latency: < 1 minute
  
- [ ] **Error handling tested**
  - Invalid signature rejected (400 response)
  - Duplicate webhook idempotent (same receipt_id)
  - Failed delivery logged (bounce webhook)

---

## Evidence Bundle Format

**File**: `docs/evidence/auto_com_center/E2E_WEBHOOK_REPORT.md`

```markdown
# E2E Webhook Test Report

**Test Date**: 2025-11-13T[HH:MM:SS]Z
**Tester**: [Name]
**Status**: [PASS/FAIL]

## Test Results

| Step | Expected | Actual | Status |
|------|----------|--------|--------|
| Event injection | 202 Accepted | [X] | [✅/❌] |
| Message queued | In queue | [X] | [✅/❌] |
| ESP delivery | Sent | [X] | [✅/❌] |
| Webhook received | 200 OK | [X] | [✅/❌] |
| Signature verified | Valid | [X] | [✅/❌] |
| Receipt logged | Stored | [X] | [✅/❌] |

## Evidence Files

- Event injection: `results/event_injection.log`
- ESP response: `results/esp_delivery.json`
- Webhook logs: `results/webhook_receipts.log`
- Database query: `results/receipt_verification.json`

## Signed Receipts

```json
[Attach receipt JSON with signature]
```

## Recommendations

[Any issues found and remediation steps]
```

---

## Failure Alerting Test

**Validate monitoring for delivery failures**:

```bash
# Inject event with invalid email (should bounce)
curl -X POST https://auto-com-center-jamarrlmayes.replit.app/api/v1/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{
    "event_type": "application_submitted",
    "user_id": "test_bounce",
    "user_email": "bounce@simulator.amazonses.com",
    "scholarship_id": "sch_test_bounce",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Wait for ESP bounce webhook
# Verify:
# 1. Bounce webhook received
# 2. Alert triggered (check alerting dashboard)
# 3. Bounce logged in database
# 4. User flagged for retry or manual intervention
```

---

**DRI**: Messaging Lead  
**Support**: Agent3, SRE Lead  
**Deadline**: Submit evidence by Nov 14, 2:00 PM MST
