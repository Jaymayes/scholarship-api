# HITL Micro-Charge Runbook

**Document ID**: HITL-MICROCHARGE-001
**Version**: 1.0
**Status**: PREPARED (Not Executed)
**Created**: 2026-01-12T07:52:00Z

---

## Purpose

Validate end-to-end Stripe payment flow with a controlled micro-charge and immediate refund, capturing 3-of-3 evidence for B2C funnel verification.

---

## Preconditions (All Must Be True)

| # | Condition | Current | Required |
|---|-----------|---------|----------|
| 1 | Stripe capacity | 4 remaining | ≥5 OR HITL approval |
| 2 | A3 /health | 404 ❌ | 200 |
| 3 | A6 /health | 200 ✅ | 200 |
| 4 | A8 /health | 404 ❌ | 200 |
| 5 | A1 warm P95 | ~109ms | ≤120ms |
| 6 | 24h stability window | Pending | Complete |
| 7 | HITL explicit approval | ❌ | ✅ |

**Current Status**: NOT READY (A3/A8 = 404, HITL approval pending)

---

## Procedure

### Step 1: Pre-Flight Check (5 min)

```bash
# Verify fleet health
for app in A3 A6 A8; do
  curl -sS -o /dev/null -w "%{http_code}" "https://${app,,}-jamarrlmayes.replit.app/health"
done
# All must return 200

# Verify Stripe capacity
# Check Stripe dashboard for remaining test charges
```

### Step 2: Generate Trace ID

```bash
TRACE_ID="HITL-MICROCHARGE-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
echo "Trace ID: $TRACE_ID"
```

### Step 3: Create Charge ($0.50)

```bash
# Via A2 payment endpoint
curl -X POST "https://scholarship-api-jamarrlmayes.replit.app/api/payment/create-checkout-session" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "X-Idempotency-Key: $TRACE_ID" \
  -d '{
    "amount": 50,
    "currency": "usd",
    "description": "HITL Micro-Charge Test",
    "metadata": {"trace_id": "'$TRACE_ID'", "purpose": "B2C validation"}
  }'
```

**Expected**: Checkout session URL or payment intent ID

### Step 4: Capture Evidence #1 (HTTP Receipt)

Save full response including:
- HTTP status code
- Response body (session_id, payment_intent)
- X-Trace-Id header echo
- Timestamp

```bash
# Save to evidence file
cat > tests/perf/evidence/microcharge_http_receipt.json << RECEIPT
{
  "trace_id": "$TRACE_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "http_status": "<status>",
  "session_id": "<session_id>",
  "payment_intent": "<pi_xxx>"
}
RECEIPT
```

### Step 5: Immediate Refund (<60s)

```bash
# Via Stripe Dashboard or API
# Refund the payment intent immediately
```

### Step 6: Capture Evidence #2 (Logs)

```bash
# Check A2 logs for trace
grep "$TRACE_ID" /var/log/a2/*.log

# Save matching log entries
cat > tests/perf/evidence/microcharge_logs.txt << LOGS
Trace ID: $TRACE_ID
Matching entries:
<log entries>
LOGS
```

### Step 7: Capture Evidence #3 (Stripe Ledger + A8)

```bash
# Stripe ledger verification
# - Charge visible in dashboard
# - Refund visible in dashboard
# - Net: $0.00

# A8 round-trip (if A8 available)
curl -X POST "https://a8-command-center-jamarrlmayes.replit.app/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: $TRACE_ID" \
  -d '{
    "event_type": "payment_test",
    "trace_id": "'$TRACE_ID'",
    "status": "refunded",
    "amount_cents": 50
  }'

# Verify GET
curl "https://a8-command-center-jamarrlmayes.replit.app/api/events?trace_id=$TRACE_ID"
```

### Step 8: Generate 3-of-3 Evidence Summary

```bash
cat > tests/perf/evidence/microcharge_3of3_summary.json << SUMMARY
{
  "trace_id": "$TRACE_ID",
  "executed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "evidence": {
    "http_receipt": {
      "present": true/false,
      "file": "tests/perf/evidence/microcharge_http_receipt.json",
      "checksum": "<sha256>"
    },
    "logs": {
      "present": true/false,
      "file": "tests/perf/evidence/microcharge_logs.txt",
      "matching_entries": <count>
    },
    "stripe_ledger": {
      "charge_id": "<ch_xxx>",
      "refund_id": "<re_xxx>",
      "net_amount": 0,
      "a8_roundtrip": true/false
    }
  },
  "verdict": "PASS/FAIL"
}
SUMMARY
```

---

## Safety Stops

Abort immediately if:

1. **Stripe capacity <5** - Do not proceed
2. **Any core app non-200** - A3/A6/A8 must all be healthy
3. **Refund failure** - Escalate to Stripe support
4. **Charge amount ≠$0.50** - Verify before confirming
5. **No HITL approval** - Wait for explicit CEO sign-off

---

## Rollback

If charge succeeds but refund fails:

1. Log to Stripe dashboard immediately
2. Initiate manual refund via dashboard
3. Contact Stripe support if >5 min delay
4. Document incident in HITL log

---

## Post-Execution

1. Update `hitl_approvals.log` with result
2. Generate checksums for all evidence files
3. Post summary to A8 (if available)
4. Update go_no_go_report.md with B2C verdict

---

## Approval Chain

| Role | Name | Approval | Date |
|------|------|----------|------|
| CEO | Pending | ☐ | - |
| Agent | A2 | ☐ Prepared | 2026-01-12 |

---

**EXECUTE ONLY WITH EXPLICIT HITL APPROVAL**
